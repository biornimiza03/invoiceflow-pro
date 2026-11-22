
"""Financial Intelligence charts for InvoiceFlow Pro.

Uses currency-specific financial insights.
Does not modify SQLite or mix currencies.
"""

from datetime import date
from decimal import Decimal

import altair as alt
import pandas as pd
import streamlit as st


GREEN = "#0C9778"
AMBER = "#DA9944"
INK = "#20394A"


STYLES = """
<style>
.if-fi-title {
    margin: 12px 0 3px;
    font-size: 22px;
    font-weight: 800;
    color: #183544;
}

.if-fi-desc {
    margin: 0 0 18px;
    font-size: 12px;
    color: #6B8190;
}

.if-fi-kicker {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #0C886B;
}

.if-fi-note {
    font-size: 11px;
    color: #708593;
    line-height: 1.6;
    margin: 4px 0 12px;
}

.if-fi-metricrow {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 14px 0;
}

.if-fi-metric {
    padding: 14px;
    background: #F6FAF9;
    border: 1px solid #E0E9E7;
    border-radius: 12px;
    min-width: 0;
}

.if-fi-label {
    color: #6E8490;
    font-size: 11px;
    margin-bottom: 6px;
}

.if-fi-value {
    font-weight: 800;
    color: #183544;
    font-size: clamp(17px, 1.6vw, 23px);
    overflow-wrap: anywhere;
}

.if-fi-value.negative {
    color: #BC6B31;
}

@media (max-width: 730px) {
    .if-fi-metricrow {
        grid-template-columns: 1fr;
    }
}

@media (prefers-reduced-motion: reduce) {
    *[class^="if-fi-"] {
        transition: none !important;
        animation: none !important;
    }
}
</style>
"""


# =====================================================
# FORMATTING
# =====================================================

def _amount(cents, currency):

    amount = (
        Decimal(int(cents or 0))
        / Decimal("100")
    )

    return f"{amount:,.2f} {currency}"


# =====================================================
# PREPARE MONTHLY DATA
# =====================================================

def _monthly_frame(rows, series):

    columns = ["Month", *series]

    if not rows:
        return (
            pd.DataFrame(columns=columns)
            .set_index("Month")
        )

    frame = pd.DataFrame(rows)

    if "Month" not in frame.columns:
        return (
            pd.DataFrame(columns=columns)
            .set_index("Month")
        )

    frame["Month"] = frame["Month"].astype(str)

    valid_months = pd.to_datetime(
        frame["Month"],
        format="%Y-%m",
        errors="coerce",
    )

    frame = frame.loc[
        valid_months.notna()
    ].copy()

    if frame.empty:
        return (
            pd.DataFrame(columns=columns)
            .set_index("Month")
        )

    for name in series:

        if name not in frame.columns:
            frame[name] = 0

        frame[name] = (
            pd.to_numeric(
                frame[name],
                errors="coerce",
            )
            .fillna(0)
            / 100
        )

    return (
        frame.groupby("Month")[series]
        .sum()
        .sort_index()
    )


def _period_data(insights, period):

    invoiced = _monthly_frame(
        insights.get("monthly_invoiced", []),
        ["Sales", "Purchases"],
    )

    payments = _monthly_frame(
        insights.get("monthly_payments", []),
        ["Cash In", "Cash Out"],
    )

    recorded = sorted(
        set(invoiced.index).union(payments.index)
    )

    if not recorded:
        return None, None

    months_count = {
        "Last 3 months": 3,
        "Last 6 months": 6,
        "Last 12 months": 12,
    }.get(period)

    if months_count:

        end = pd.Period(
            date.today(),
            freq="M",
        )

        months = pd.period_range(
            start=end - (months_count - 1),
            end=end,
            freq="M",
        )

    else:

        months = pd.period_range(
            start=recorded[0],
            end=recorded[-1],
            freq="M",
        )

    month_strings = [
        str(month)
        for month in months
    ]

    invoiced = (
        invoiced.reindex(
            month_strings,
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"index": "Month"})
    )

    payments = (
        payments.reindex(
            month_strings,
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"index": "Month"})
    )

    payments["Net"] = (
        payments["Cash In"]
        - payments["Cash Out"]
    )

    return invoiced, payments


# =====================================================
# COMPACT FINANCIAL METRICS
# =====================================================

def _cards(values, currency):

    fragments = []

    for label, cents in values:

        number = _amount(
            cents,
            currency,
        )

        negative = (
            " negative"
            if cents < 0
            else ""
        )

        fragments.append(
            '<div class="if-fi-metric">'
            f'<div class="if-fi-label">{label}</div>'
            f'<div class="if-fi-value{negative}">'
            f'{number}'
            '</div>'
            '</div>'
        )

    st.html(
        '<div class="if-fi-metricrow">'
        + "".join(fragments)
        + '</div>'
    )


# =====================================================
# HORIZONTAL BAR CHART
# =====================================================

def _horizontal_chart(
    values,
    categories,
    currency,
    colors,
    height=150,
):

    frame = pd.DataFrame({
        "Category": categories,
        "Amount": values,
    })

    chart = (
        alt.Chart(frame)
        .mark_bar(
            cornerRadiusEnd=6,
            size=24,
        )
        .encode(
            y=alt.Y(
                "Category:N",
                sort=categories,
                axis=alt.Axis(
                    title=None,
                    labelLimit=140,
                ),
            ),

            x=alt.X(
                "Amount:Q",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(
                    title=f"Amount ({currency})",
                    grid=True,
                    gridColor="#E5EEED",
                ),
            ),

            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=categories,
                    range=colors,
                ),
                legend=None,
            ),

            tooltip=[
                alt.Tooltip("Category:N"),
                alt.Tooltip(
                    "Amount:Q",
                    title=f"Amount ({currency})",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=height)
        .configure_view(stroke=None)
    )

    st.altair_chart(
        chart,
        theme=None,
        width="stretch",
    )


# =====================================================
# CHART 1 — CASH FLOW
# =====================================================

def _cashflow_chart(payments, currency):

    st.markdown("**Cash Flow Analysis**")

    st.caption(
        "Recorded cash movements for "
        "the selected chart period."
    )

    cash_in = int(
        round(float(payments["Cash In"].sum()) * 100)
    )

    cash_out = int(
        round(float(payments["Cash Out"].sum()) * 100)
    )

    net = cash_in - cash_out

    _cards(
        [
            ("Cash In", cash_in),
            ("Cash Out", cash_out),
            ("Net Cash Flow", net),
        ],
        currency,
    )

    # One month: compact but real bar chart.

    if len(payments) == 1:

        month = payments.iloc[0]["Month"]

        st.caption(
            f"{month} · Recorded payment comparison"
        )

        _horizontal_chart(
            values=[
                float(payments.iloc[0]["Cash In"]),
                float(payments.iloc[0]["Cash Out"]),
            ],
            categories=[
                "Cash In",
                "Cash Out",
            ],
            currency=currency,
            colors=[GREEN, AMBER],
            height=125,
        )

        st.caption(
            "Net Cash Flow = Cash In − Cash Out. "
            "This is not accounting profit."
        )

        return

    # Multiple months: grouped bars + net line.

    order = payments["Month"].tolist()

    bars_data = payments.melt(
        id_vars="Month",
        value_vars=["Cash In", "Cash Out"],
        var_name="Flow",
        value_name="Amount",
    )

    x_axis = alt.X(
        "Month:N",
        sort=order,
        axis=alt.Axis(
            title=None,
            labelAngle=(
                -25 if len(order) > 6 else 0
            ),
        ),
    )

    bars = (
        alt.Chart(bars_data)
        .mark_bar(
            size=22,
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
        )
        .encode(
            x=x_axis,

            xOffset=alt.XOffset(
                "Flow:N",
                sort=["Cash In", "Cash Out"],
            ),

            y=alt.Y(
                "Amount:Q",
                axis=alt.Axis(
                    title=f"Amount ({currency})",
                    grid=True,
                    gridColor="#E5EEED",
                ),
            ),

            color=alt.Color(
                "Flow:N",
                scale=alt.Scale(
                    domain=["Cash In", "Cash Out"],
                    range=[GREEN, AMBER],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                ),
            ),

            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip("Flow:N"),
                alt.Tooltip(
                    "Amount:Q",
                    format=",.2f",
                ),
            ],
        )
    )

    net_line = (
        alt.Chart(payments)
        .mark_line(
            color=INK,
            strokeWidth=3,
            point=True,
        )
        .encode(
            x=x_axis,
            y="Net:Q",
            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip(
                    "Net:Q",
                    title="Net Cash Flow",
                    format=",.2f",
                ),
            ],
        )
    )

    chart = (
        alt.layer(bars, net_line)
        .properties(height=285)
        .configure_view(stroke=None)
    )

    st.altair_chart(
        chart,
        theme=None,
        width="stretch",
    )

    st.caption(
        "Green: Cash In · Orange: Cash Out "
        "· Navy line: Net Cash Flow."
    )


# =====================================================
# CHART 2 — INVOICE SETTLEMENT
# =====================================================

def _settlement_chart(insights, currency):

    st.markdown("**Invoice Settlement**")

    st.caption(
        "How much of your active "
        "invoices has been paid?"
    )

    purchase_total = (
        int(insights.get("cash_paid_cents", 0))
        + int(insights.get("payables_cents", 0))
    )

    sale_total = (
        int(insights.get("cash_received_cents", 0))
        + int(insights.get("receivables_cents", 0))
    )

    default_choice = (
        "Purchases"
        if purchase_total
        else "Sales"
        if sale_total
        else "Purchases"
    )

    selected = st.segmented_control(
        "Invoice type",
        options=["Purchases", "Sales"],
        default=default_choice,
        selection_mode="single",
        key="fi_settlement_kind",
    ) or default_choice

    if selected == "Purchases":

        paid = int(
            insights.get("cash_paid_cents", 0)
        )

        outstanding = int(
            insights.get("payables_cents", 0)
        )

    else:

        paid = int(
            insights.get("cash_received_cents", 0)
        )

        outstanding = int(
            insights.get("receivables_cents", 0)
        )

    total = paid + outstanding

    if total <= 0:

        st.info(
            f"No active {selected.lower()} "
            "values to display."
        )

        return

    percent = min(
        100,
        max(0, paid / total * 100),
    )

    data = pd.DataFrame({
        "Status": [
            "Paid",
            "Outstanding",
        ],
        "Amount": [
            paid / 100,
            outstanding / 100,
        ],
    })

    donut = (
        alt.Chart(data)
        .mark_arc(
            innerRadius=65,
            outerRadius=108,
            cornerRadius=5,
        )
        .encode(
            theta=alt.Theta(
                "Amount:Q",
                stack=True,
            ),

            color=alt.Color(
                "Status:N",
                scale=alt.Scale(
                    domain=[
                        "Paid",
                        "Outstanding",
                    ],
                    range=[GREEN, AMBER],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                ),
            ),

            tooltip=[
                alt.Tooltip("Status:N"),
                alt.Tooltip(
                    "Amount:Q",
                    title=f"Amount ({currency})",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=245)
        .configure_view(stroke=None)
    )

    left, right = st.columns(
        [1.1, 1],
        gap="small",
        vertical_alignment="center",
    )

    with left:

        st.altair_chart(
            donut,
            theme=None,
            width="stretch",
        )

    with right:

        st.metric(
            "Settled",
            f"{percent:.1f}%",
        )

        st.caption(
            f"Paid: {_amount(paid, currency)}"
        )

        st.caption(
            "Remaining: "
            f"{_amount(outstanding, currency)}"
        )

    st.caption(
        "Settlement covers all active invoices "
        "in this currency, independently "
        "of the chart period."
    )


# =====================================================
# CHART 3 — INVOICE PERFORMANCE
# =====================================================

def _performance_chart(invoiced, currency):

    st.markdown("**Invoice Performance**")

    st.caption(
        "Sales and purchase invoice "
        "values by issue month."
    )

    # One month: horizontal bar chart.

    if len(invoiced) == 1:

        _horizontal_chart(
            values=[
                float(invoiced.iloc[0]["Sales"]),
                float(invoiced.iloc[0]["Purchases"]),
            ],
            categories=[
                "Sales",
                "Purchases",
            ],
            currency=currency,
            colors=[GREEN, AMBER],
            height=155,
        )

        return

    # Multiple months: grouped bar chart.

    order = invoiced["Month"].tolist()

    records = invoiced.melt(
        id_vars="Month",
        value_vars=["Sales", "Purchases"],
        var_name="Type",
        value_name="Amount",
    )

    chart = (
        alt.Chart(records)
        .mark_bar(
            size=16,
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=order,
                axis=alt.Axis(
                    title=None,
                    labelAngle=(
                        -25 if len(order) > 6 else 0
                    ),
                ),
            ),

            xOffset=alt.XOffset(
                "Type:N",
                sort=["Sales", "Purchases"],
            ),

            y=alt.Y(
                "Amount:Q",
                axis=alt.Axis(
                    title=f"Amount ({currency})",
                    grid=True,
                    gridColor="#E5EEED",
                ),
            ),

            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=["Sales", "Purchases"],
                    range=[GREEN, AMBER],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                ),
            ),

            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip("Type:N"),
                alt.Tooltip(
                    "Amount:Q",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=245)
        .configure_view(stroke=None)
    )

    st.altair_chart(
        chart,
        theme=None,
        width="stretch",
    )


# =====================================================
# MAIN FINANCIAL INTELLIGENCE SECTION
# =====================================================

def render_financial_intelligence(insights, currency):

    st.html(STYLES)

    st.html(
        '<div class="if-fi-kicker">'
        'FINANCIAL ANALYTICS'
        '</div>'

        '<div class="if-fi-title">'
        'Financial Intelligence'
        '</div>'

        '<p class="if-fi-desc">'
        'Cash flow, invoice settlement '
        'and monthly performance '
        'in one place.'
        '</p>'
    )

    period = st.segmented_control(
        "Chart period",
        options=[
            "All recorded",
            "Last 3 months",
            "Last 6 months",
            "Last 12 months",
        ],
        default="All recorded",
        selection_mode="single",
        key="dashboard_chart_period",
    ) or "All recorded"

    invoiced, payments = _period_data(
        insights,
        period,
    )

    if invoiced is None or payments is None:

        st.info(
            "No monthly invoice or payment "
            "activity has been recorded yet."
        )

        return

    st.html(
        '<div class="if-fi-note">'
        'The period filter affects Cash Flow and '
        'Invoice Performance. Settlement shows '
        'all active invoices.'
        '</div>'
    )

    # Main full-width cash-flow visualization.

    with st.container(border=True):

        _cashflow_chart(
            payments,
            currency,
        )

    # Two supporting charts.

    left, right = st.columns(
        2,
        gap="medium",
    )

    with left:

        with st.container(border=True):

            _settlement_chart(
                insights,
                currency,
            )

    with right:

        with st.container(border=True):

            _performance_chart(
                invoiced,
                currency,
            )
