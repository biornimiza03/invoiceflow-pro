
"""InvoiceFlow Pro — premium financial overview.

Read-only financial dashboard backed by saved, active invoices in SQLite.
The spreadsheet-analysis dashboard is managed separately.
"""

from datetime import date
from decimal import Decimal
from html import escape
from invoiceflow.financial_visuals import render_financial_intelligence

import altair as alt
import pandas as pd
import streamlit as st

from invoiceflow.financial_insights import get_financial_insights
from invoiceflow.payments import list_invoice_balances


EMERALD = "#12866C"
AMBER = "#D49A48"


STYLES = """
<style>
.if-fin-hero { margin: 4px 0 22px; }
.if-fin-eyebrow { font-size: 11px; font-weight: 800; letter-spacing: 1.6px; color: #07886B; margin-bottom: 8px; }
.if-fin-hero h2 { margin: 0 0 8px; font-size: 27px; font-weight: 780; color: #173341; }
.if-fin-hero p { margin: 0; font-size: 13px; color: #6E8591; }
.if-fin-section { margin: 25px 0 12px; }
.if-fin-section h3 { margin: 0 0 5px; font-size: 19px; font-weight: 750; color: #173341; }
.if-fin-section p { margin: 0; font-size: 12px; color: #718593; }
.if-fin-kpis { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 14px; margin: 15px 0; }
.if-fin-card { background: #fff; border: 1px solid #DEE8EA; border-radius: 16px; padding: 20px; min-width: 0; box-shadow: 0 5px 19px rgba(20,45,56,.04); transition: transform .2s ease, box-shadow .2s ease; }
.if-fin-card:hover { transform: translateY(-2px); box-shadow: 0 9px 24px rgba(20,45,56,.08); }
.if-fin-card.primary { background: linear-gradient(125deg,#154F44,#078568); border-color: transparent; }
.if-fin-label { color: #607887; font-size: 12px; font-weight: 650; }
.if-fin-value { margin: 14px 0 9px; font-size: clamp(21px,2vw,29px); line-height: 1.15; font-weight: 800; color: #16323E; overflow-wrap: anywhere; }
.if-fin-hint { color: #879AA3; font-size: 11px; line-height: 1.5; }
.if-fin-card.primary .if-fin-label, .if-fin-card.primary .if-fin-hint { color: #D1F0E5; }
.if-fin-card.primary .if-fin-value { color: #fff; }
.if-fin-stats { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; margin: 14px 0 20px; }
.if-fin-stat { background: #fff; border: 1px solid #DEE8EA; border-radius: 14px; padding: 17px 20px; }
.if-fin-stat .if-fin-value { margin: 7px 0 0; font-size: 25px; }
.if-fin-stat.warning .if-fin-value { color: #B7772D; }
.if-fin-tip { font-size: 11px; color: #7D929D; margin-top: 13px; }
@media (max-width: 1050px) { .if-fin-kpis { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 650px) { .if-fin-stats { grid-template-columns: 1fr; } .if-fin-kpis { grid-template-columns: 1fr; } .if-fin-card { padding: 17px; } }
@media (prefers-reduced-motion: reduce) { .if-fin-card { transition: none; } .if-fin-card:hover { transform: none; } }
</style>
"""


def _money(cents, currency):
    return f"{Decimal(int(cents or 0)) / Decimal('100'):,.2f} {currency}"


def _section(title, description):
    st.html(
        '<div class="if-fin-section">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(description)}</p>'
        '</div>'
    )


def _card(label, value, description, primary=False):
    kind = " primary" if primary else ""
    return (
        f'<article class="if-fin-card{kind}">'
        f'<div class="if-fin-label">{escape(str(label))}</div>'
        f'<div class="if-fin-value">{escape(str(value))}</div>'
        f'<div class="if-fin-hint">{escape(str(description))}</div>'
        '</article>'
    )


def _kpis(insights, currency):
    cards = [
        ("Cash Received", _money(insights["cash_received_cents"], currency), "Recorded payments on sales", True),
        ("Cash Paid", _money(insights["cash_paid_cents"], currency), "Recorded payments on purchases", False),
        ("Receivables", _money(insights["receivables_cents"], currency), "Still owed by customers", False),
        ("Payables", _money(insights["payables_cents"], currency), "Still owed to suppliers", False),
    ]
    st.html('<div class="if-fin-kpis">' + ''.join(_card(*c) for c in cards) + '</div>')

    stats = [
        ("Active invoices", insights["active_count"], False),
        ("Overdue invoices", insights["overdue_count"], insights["overdue_count"] > 0),
        ("Due within 7 days", insights["due_soon_count"], insights["due_soon_count"] > 0),
    ]
    html = []
    for label, value, warn in stats:
        warning_class = " warning" if warn else ""
        html.append(
            f'<div class="if-fin-stat{warning_class}">'
            f'<div class="if-fin-label">{escape(str(label))}</div>'
            f'<div class="if-fin-value">{escape(str(value))}</div>'
            '</div>'
        )
    st.html('<div class="if-fin-stats">' + ''.join(html) + '</div>')


def _first_month(period):
    """Return YYYY-MM cutoff, or None for the full available history."""
    count = {
        "Last 3 months": 3,
        "Last 6 months": 6,
        "Last 12 months": 12,
    }.get(period)
    if count is None:
        return None

    today = date.today()
    month_zero_based = today.year * 12 + today.month - 1 - (count - 1)
    year, month_index = divmod(month_zero_based, 12)
    return f"{year:04d}-{month_index + 1:02d}"



def _monthly_chart(records, series, currency, period):
    """
    Show compact comparisons for a single month,
    or a trend chart when multiple months exist.
    """

    if not records:
        st.info("No monthly activity has been recorded yet.")
        return

    frame = pd.DataFrame(records).copy()

    if "Month" not in frame.columns:
        st.info("Monthly reporting data is unavailable.")
        return

    frame["Month"] = frame["Month"].astype(str)

    for name in series:
        if name not in frame.columns:
            frame[name] = 0

        frame[name] = (
            pd.to_numeric(
                frame[name],
                errors="coerce",
            ).fillna(0) / 100
        )

    frame = (
        frame.groupby("Month", as_index=False)[series]
        .sum()
        .sort_values("Month")
    )

    cutoff = _first_month(period)

    if cutoff:
        frame = frame.loc[
            frame["Month"] >= cutoff
        ].copy()

    if frame.empty:
        st.info("No activity in the selected period.")
        return

    colors = ["#12866C", "#DE9E45"]

    # ------------------------------------------
    # STYLES
    # ------------------------------------------

    st.html("""
    <style>

    .if-month-comparison {
        display: grid;
        gap: 23px;
        padding: 15px 1px 17px;
    }

    .if-month-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .6px;
        color: #778d99;
        margin: 9px 0 5px;
    }

    .if-month-line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-bottom: 11px;
    }

    .if-month-name {
        font-size: 13px;
        font-weight: 700;
        color: #244455;
    }

    .if-month-amount {
        font-size: 21px;
        font-weight: 800;
        color: #173746;
        overflow-wrap: anywhere;
    }

    .if-month-track {
        height: 11px;
        border-radius: 20px;
        background: #edf2f3;
        overflow: hidden;
    }

    .if-month-fill {
        height: 100%;
        border-radius: 20px;
        transition: width .25s ease;
    }

    .if-month-summaries {
        display: grid;
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin: 10px 0 15px;
    }

    .if-month-summary {
        border: 1px solid #e0eaec;
        border-radius: 13px;
        padding: 14px;
        background: #ffffff;
    }

    .if-month-summary-label {
        font-size: 11px;
        color: #6f8794;
    }

    .if-month-summary-value {
        font-size: 21px;
        font-weight: 800;
        color: #173746;
        margin-top: 6px;
        overflow-wrap: anywhere;
    }

    @media (max-width: 600px) {

        .if-month-summaries {
            grid-template-columns: 1fr;
        }

        .if-month-line {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
        }
    }

    @media (prefers-reduced-motion: reduce) {

        .if-month-fill {
            transition: none;
        }
    }

    </style>
    """)

    # ==========================================
    # ONE MONTH — COMPACT COMPARISON
    # ==========================================

    if len(frame) == 1:

        month = str(frame.iloc[0]["Month"])

        try:
            month_label = pd.Period(
                month,
                freq="M",
            ).strftime("%B %Y")

        except (ValueError, TypeError):
            month_label = month

        values = [
            max(0.0, float(frame.iloc[0][name]))
            for name in series
        ]

        largest = max(values) if any(values) else 1.0

        rows = []

        for name, value, color in zip(
            series,
            values,
            colors,
        ):

            width_pct = value / largest * 100

            rows.append(
                '<div>'

                '<div class="if-month-line">'

                f'<span class="if-month-name">'
                f'{escape(str(name))}'
                '</span>'

                f'<strong class="if-month-amount">'
                f'{value:,.2f} {escape(str(currency))}'
                '</strong>'

                '</div>'

                '<div class="if-month-track">'

                f'<div class="if-month-fill" '
                f'style="width:{width_pct:.1f}%;'
                f'background:{color}">'
                '</div>'

                '</div>'
                '</div>'
            )

        st.html(
            '<div class="if-month-label">'
            f'{escape(month_label)} · Monthly comparison'
            '</div>'

            '<div class="if-month-comparison">'
            + "".join(rows)
            + '</div>'
        )

        return

    # ==========================================
    # MULTIPLE MONTHS — TREND CHART
    # ==========================================

    summaries = []

    for name in series:

        total = float(frame[name].sum())

        summaries.append(
            '<div class="if-month-summary">'

            '<div class="if-month-summary-label">'
            f'{escape(str(name))} · Period total'
            '</div>'

            '<div class="if-month-summary-value">'
            f'{total:,.2f} {escape(str(currency))}'
            '</div>'

            '</div>'
        )

    st.html(
        '<div class="if-month-summaries">'
        + "".join(summaries)
        + '</div>'
    )

    months = frame["Month"].tolist()

    long_data = frame.melt(
        id_vars="Month",
        value_vars=series,
        var_name="Category",
        value_name="Amount",
    )

    chart = (
        alt.Chart(long_data)
        .mark_line(
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=months,
                axis=alt.Axis(
                    title=None,
                    labelAngle=(
                        -25 if len(months) > 6 else 0
                    ),
                ),
            ),

            y=alt.Y(
                "Amount:Q",
                axis=alt.Axis(
                    title=f"Amount ({currency})",
                    grid=True,
                    gridColor="#e5edf0",
                ),
                scale=alt.Scale(zero=True),
            ),

            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=series,
                    range=colors,
                ),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                ),
            ),

            tooltip=[
                alt.Tooltip(
                    "Month:N",
                    title="Month",
                ),
                alt.Tooltip(
                    "Category:N",
                    title="Category",
                ),
                alt.Tooltip(
                    "Amount:Q",
                    title=f"Amount ({currency})",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=195)
        .configure_view(stroke=None)
    )

    st.altair_chart(
        chart,
        width="stretch",
    )



def _render_attention(insights, currency):
    _section("Invoices requiring attention", "Overdue invoices and obligations due soon.")
    rows = [
        {
            "Invoice": item["Invoice"],
            "Contact": item["Contact"],
            "Type": item["Type"],
            "Due date": item["Due Date"],
            "Balance due": _money(item["Remaining Cents"], currency),
            "Status": item["Status"],
            "Days overdue": item["Days Overdue"],
        }
        for item in insights["attention"]
    ]

    
    if not rows:

        st.html("""
        <div style="
            display:flex;
            align-items:center;
            gap:13px;
            padding:19px 22px;
            border:1px solid #d7e9df;
            border-radius:15px;
            background:#f7fcf9;
            margin:13px 0 20px;
        ">

            <div style="
                width:38px;
                height:38px;
                border-radius:50%;
                display:grid;
                place-items:center;
                background:#e2f5e9;
                color:#0a8763;
                font-size:22px;
                flex-shrink:0;
            ">
                ✓
            </div>

            <div>
                <div style="
                    font-size:14px;
                    font-weight:750;
                    color:#20493b;
                ">
                    All caught up
                </div>

                <div style="
                    color:#718c7e;
                    font-size:12px;
                    margin-top:4px;
                ">
                    No overdue or soon-due invoices
                    for the selected currency.
                </div>
            </div>

        </div>
        """)

        return


    st.dataframe(rows, hide_index=True, width="stretch", row_height=39)
    st.download_button(
        "Export attention list (CSV)",
        data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"invoice_attention_{currency}.csv",
        mime="text/csv",
        key=f"dashboard_attention_export_{currency}",
    )


def _render_recent_payments(insights, currency):
    _section("Recent payments", "Latest recorded transactions for active invoices.")
    rows = [
        {
            "Invoice": payment["invoice_number"],
            "Contact": payment["contact"],
            "Type": payment["invoice_type"],
            "Amount": _money(payment["amount_cents"], currency),
            "Date": payment["payment_date"],
            "Method": payment["method"],
        }
        for payment in insights["recent_payments"]
    ]

    if rows:
        st.dataframe(rows, hide_index=True, width="stretch", row_height=39)
        st.download_button(
            "Export recent payments (CSV)",
            data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"recent_payments_{currency}.csv",
            mime="text/csv",
            key=f"dashboard_recent_export_{currency}",
        )
    else:
        st.info("No recorded payments for this currency.")


def render_financial_overview():
    """Display saved-invoice analytics without modifying the database."""
    st.html(STYLES)
    st.html(
        '<header class="if-fin-hero">'
        '<div class="if-fin-eyebrow">BUSINESS ANALYTICS</div>'
        '<h2>Financial Performance</h2>'
        '<p>Monitor invoices, payments and upcoming obligations in one place.</p>'
        '</header>'
    )

    balances = list_invoice_balances()
    currencies = sorted({row["currency"] for row in balances})
    if not currencies:
        st.info("No active saved invoices yet. Create an invoice to activate financial reporting.")
        st.page_link("pages/saved_invoices.py", label="Open Saved Invoices", icon=":material/receipt_long:")
        return

    currency = st.selectbox(
        "Reporting currency",
        options=currencies,
        key="dashboard_financial_reporting_currency",
        help="Only figures from this currency are displayed. Different currencies are never combined.",
    )
    insights = get_financial_insights(currency)

    _section("Financial snapshot", "Based on active saved invoices and recorded payments.")
    _kpis(insights, currency)

    render_financial_intelligence(
        insights,
        currency,
    )
    _render_attention(insights, currency)
    _render_recent_payments(insights, currency)

    
    _section(
        "Quick navigation",
        "Continue managing invoices and payments.",
    )

    st.html("""
    <style>
    .st-key-dashboard_nav_saved,
    .st-key-dashboard_nav_payments {
        background: #ffffff !important;
        border: 1px solid #dce8e9 !important;
        border-radius: 17px !important;
        padding: 20px !important;
        min-height: 155px;
        box-shadow: 0 5px 19px rgba(16, 51, 60, .04);
    }

    .st-key-dashboard_nav_saved button,
    .st-key-dashboard_nav_payments button {
        min-height: 43px;
        border-radius: 11px;
        font-weight: 650;
    }
    </style>
    """)

    left, right = st.columns(2, gap="medium")

    with left:

        with st.container(
            border=True,
            key="dashboard_nav_saved",
        ):

            st.markdown("### 📄 Saved Invoices")

            st.caption(
                "Find, create, edit and manage "
                "your business invoices."
            )

            if st.button(
                "Open Saved Invoices",
                icon=":material/receipt_long:",
                use_container_width=True,
                key="dashboard_open_saved",
                type="secondary",
            ):

                st.switch_page("pages/saved_invoices.py")

    with right:

        with st.container(
            border=True,
            key="dashboard_nav_payments",
        ):

            st.markdown("### 💳 Payments")

            st.caption(
                "Register transactions and review "
                "payment balances."
            )

            if st.button(
                "Open Payments",
                icon=":material/payments:",
                use_container_width=True,
                key="dashboard_open_payments",
                type="secondary",
            ):

                st.switch_page("pages/payments.py")


    st.html(
        '<p class="if-fin-tip">Figures reflect active saved invoices only; archived records are excluded. '
        'Recorded cash activity is not a verified bank statement. '
        'Amounts from different currencies are never combined.</p>'
    )
