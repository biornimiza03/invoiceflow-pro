
"""InvoiceFlow Pro — Financial Dashboard.

Business Overview uses saved SQLite invoices and payments.
Spreadsheet Analysis uses imported CSV/Excel session data.
"""

from decimal import Decimal
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from invoiceflow.analytics import build_currency_analytics
from invoiceflow.dashboard_financial import render_financial_overview
from invoiceflow.dashboard_skin import apply_dashboard_skin
from invoiceflow.hover_effects import apply_hover_effects
from invoiceflow.saved_analytics import (
    get_saved_dashboard_summary,
    list_active_currencies,
)
from invoiceflow.validator import validate_invoices


# ============================================================
# DASHBOARD PREMIUM STYLES
# ============================================================

DASHBOARD_CSS = """
<style>

.if-fin-hero {
    display: none !important;
}

.if-dash-intro {
    margin: 9px 0 16px;
}

.if-dash-kicker {
    color: #087e67;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}

.if-dash-title {
    color: #173747;
    font-weight: 780;
    font-size: 21px;
    letter-spacing: -.5px;
    line-height: 1.3;
}

.if-dash-desc {
    color: #718695;
    font-size: 12px;
    line-height: 1.6;
    margin-top: 6px;
}

.if-dash-section {
    margin: 22px 0 12px;
}

.if-dash-section h3 {
    font-size: 18px;
    font-weight: 750;
    color: #173747;
    margin: 0 0 6px;
}

.if-dash-section p {
    font-size: 12px;
    color: #718695;
    margin: 0;
}

/* STATISTIC CARDS */

.if-dash-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 13px;
    margin: 14px 0 20px;
}

.if-dash-card {
    border: 1px solid #dce8e9;
    background: #ffffff;
    border-radius: 16px;
    padding: 20px;
    min-width: 0;
    box-shadow: 0 5px 19px rgba(15,45,56,.04);
}

.if-dash-card.primary {
    background: linear-gradient(125deg,#175146,#078467);
    border-color: transparent;
}

.if-dash-card-label {
    color: #69818e;
    font-size: 12px;
    font-weight: 650;
}

.if-dash-card-value {
    color: #173747;
    font-size: clamp(20px,2vw,27px);
    margin: 12px 0 8px;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.if-dash-card-note {
    color: #889ba5;
    font-size: 11px;
    line-height: 1.5;
}

.if-dash-card.primary .if-dash-card-label,
.if-dash-card.primary .if-dash-card-note {
    color: #d2eee5;
}

.if-dash-card.primary .if-dash-card-value {
    color: #ffffff;
}

/* INFORMATION PANEL */

.if-dash-help {
    border-left: 3px solid #0b8b6b;
    background: #f0f9f5;
    padding: 12px 15px;
    border-radius: 0 11px 11px 0;
    color: #4a7566;
    font-size: 12px;
    line-height: 1.6;
    margin-top: 13px;
}

/* INVOICE VALUE BREAKDOWN */

.if-breakdown {
    background: linear-gradient(135deg,#fff,#f8fbfa);
    border: 1px solid #dce8e8;
    border-radius: 18px;
    padding: 25px;
    margin: 10px 0 18px;
    box-shadow: 0 7px 25px rgba(20,50,60,.035);
}

.if-breakdown-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 18px;
    margin-bottom: 24px;
}

.if-breakdown-eyebrow {
    font-size: 10px;
    letter-spacing: 1.4px;
    font-weight: 800;
    color: #0e8b70;
    margin-bottom: 8px;
}

.if-breakdown-total {
    color: #173747;
    font-size: clamp(25px,3vw,34px);
    font-weight: 800;
    letter-spacing: -.8px;
    line-height: 1.2;
}

.if-breakdown-subtitle {
    color: #8498a2;
    font-size: 12px;
    margin-top: 9px;
}

.if-breakdown-badge {
    background: #edf8f3;
    color: #087c61;
    border: 1px solid #d0e8dc;
    border-radius: 30px;
    padding: 7px 13px;
    font-size: 11px;
    font-weight: 700;
}

.if-breakdown-track {
    display: flex;
    width: 100%;
    height: 12px;
    border-radius: 20px;
    background: #e8eff0;
    overflow: hidden;
    margin: 0 0 22px;
}

.if-breakdown-sales {
    background: #0c9574;
    height: 100%;
}

.if-breakdown-purchases {
    background: #dda04d;
    height: 100%;
}

.if-breakdown-grid {
    display: grid;
    grid-template-columns: repeat(2,minmax(0,1fr));
    gap: 15px;
}

.if-breakdown-card {
    border: 1px solid #dfe9ea;
    border-radius: 15px;
    background: #ffffff;
    padding: 21px;
    min-width: 0;
}

.if-breakdown-card-header {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #54717d;
    font-size: 12px;
    font-weight: 700;
}

.if-breakdown-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.if-breakdown-dot.sales {
    background: #0c9574;
}

.if-breakdown-dot.purchases {
    background: #dda04d;
}

.if-breakdown-number {
    color: #173747;
    font-size: clamp(21px,2.3vw,28px);
    font-weight: 800;
    letter-spacing: -.5px;
    margin: 14px 0 7px;
    overflow-wrap: anywhere;
}

.if-breakdown-share {
    color: #8a9aa3;
    font-size: 11px;
}

.if-breakdown-footer {
    border-top: 1px solid #e5ecee;
    margin-top: 23px;
    padding-top: 15px;
    color: #758994;
    font-size: 12px;
    line-height: 1.6;
}

/* PREMIUM EXPANDERS */

[data-testid="stExpander"] {
    border: 1px solid #dce8e5 !important;
    border-radius: 13px !important;
    background: #ffffff !important;
    box-shadow: 0 4px 16px rgba(20,55,60,.04);
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    padding: 13px 17px !important;
    background: #ffffff !important;
    transition: background-color .2s ease;
}

[data-testid="stExpander"] summary:hover {
    background: #f3f9f6 !important;
}

[data-testid="stExpander"] summary p {
    color: #244b4a !important;
    font-weight: 650 !important;
    font-size: 13px !important;
}

/* SPREADSHEET START CARDS */

.st-key-dashboard_upload_card,
.st-key-dashboard_demo_card {
    border-radius: 18px !important;
    padding: 20px !important;
    min-height: 190px;
    box-shadow: 0 7px 22px rgba(16,50,60,.045);
}

.st-key-dashboard_upload_card {
    background: linear-gradient(135deg,#f0faf6,#fff) !important;
    border: 1px solid #b9dfd0 !important;
}

.st-key-dashboard_demo_card {
    background: #ffffff !important;
    border: 1px solid #dce8ea !important;
}

.st-key-dashboard_upload_card button,
.st-key-dashboard_demo_card button {
    min-height: 46px;
    font-weight: 700;
    border-radius: 11px;
}

/* OPEN SAVED INVOICES BUTTON */

.st-key-dashboard_saved_premium button {
    background: #ffffff !important;
    color: #08775c !important;
    border: 1px solid #b7dbc9 !important;
    border-radius: 11px !important;
    font-weight: 650 !important;
    min-height: 42px !important;

    transition:
        background-color .2s ease,
        border-color .2s ease !important;
}

.st-key-dashboard_saved_premium button:hover {
    background: #e9f7f0 !important;
    border-color: #91ccb1 !important;
    color: #08775c !important;
}

.st-key-dashboard_saved_premium button p {
    color: inherit !important;
}

/* RESPONSIVE */

@media (max-width:1050px) {
    .if-dash-grid {
        grid-template-columns: repeat(2,minmax(0,1fr));
    }
}

@media (max-width:650px) {
    .if-dash-grid,
    .if-breakdown-grid {
        grid-template-columns: 1fr;
    }

    .if-breakdown {
        padding: 17px;
    }
}

@media (prefers-reduced-motion:reduce) {
    .st-key-dashboard_saved_premium button,
    [data-testid="stExpander"] summary {
        transition: none !important;
    }
}

</style>
"""


# ============================================================
# REUSABLE HELPERS
# ============================================================

def money(cents, currency):
    amount = Decimal(str(cents or 0)) / Decimal("100")
    return f"{amount:,.2f} {currency}"


def render_intro(kicker, title, description):
    st.html(
        '<div class="if-dash-intro">'
        f'<div class="if-dash-kicker">{escape(kicker)}</div>'
        f'<div class="if-dash-title">{escape(title)}</div>'
        f'<div class="if-dash-desc">{escape(description)}</div>'
        '</div>'
    )


def render_section(title, description):
    st.html(
        '<div class="if-dash-section">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(description)}</p>'
        '</div>'
    )


def render_cards(items):
    blocks = []

    for index, (label, value, note) in enumerate(items):
        primary = " primary" if index == 0 else ""

        blocks.append(
            f'<div class="if-dash-card{primary}">'
            f'<div class="if-dash-card-label">{escape(str(label))}</div>'
            f'<div class="if-dash-card-value">{escape(str(value))}</div>'
            f'<div class="if-dash-card-note">{escape(str(note))}</div>'
            '</div>'
        )

    st.html(
        '<div class="if-dash-grid">'
        + "".join(blocks)
        + '</div>'
    )


# ============================================================
# PERSISTENT SQLITE INVOICE VALUE BREAKDOWN
# ============================================================

def render_invoice_value_breakdown():

    currencies = list_active_currencies()

    if not currencies:
        return

    selected = st.session_state.get(
        "dashboard_financial_reporting_currency"
    )

    currency = (
        selected if selected in currencies
        else currencies[0]
    )

    summary = get_saved_dashboard_summary(currency)

    sales = int(summary["sales_cents"])
    purchases = int(summary["purchases_cents"])

    total = sales + purchases

    sales_pct = (
        100 * sales / total
        if total > 0 else 0
    )

    purchases_pct = (
        100 * purchases / total
        if total > 0 else 0
    )

    with st.expander(
        "Invoice Value Breakdown",
        expanded=False,
    ):

        st.html(f"""
        <section class="if-breakdown">

            <div class="if-breakdown-header">
                <div>
                    <div class="if-breakdown-eyebrow">
                        GROSS INVOICED VOLUME
                    </div>

                    <div class="if-breakdown-total">
                        {escape(money(total, currency))}
                    </div>

                    <div class="if-breakdown-subtitle">
                        {int(summary["invoice_count"])}
                        active invoices · {escape(currency)}
                    </div>
                </div>

                <div class="if-breakdown-badge">
                    Invoice Values
                </div>
            </div>

            <div class="if-breakdown-track">
                <div class="if-breakdown-sales"
                     style="width:{sales_pct:.2f}%"></div>
                <div class="if-breakdown-purchases"
                     style="width:{purchases_pct:.2f}%"></div>
            </div>

            <div class="if-breakdown-grid">

                <div class="if-breakdown-card">
                    <div class="if-breakdown-card-header">
                        <span class="if-breakdown-dot sales"></span>
                        Sales Invoiced
                    </div>

                    <div class="if-breakdown-number">
                        {escape(money(sales, currency))}
                    </div>

                    <div class="if-breakdown-share">
                        {sales_pct:.1f}% of invoiced volume
                    </div>
                </div>

                <div class="if-breakdown-card">
                    <div class="if-breakdown-card-header">
                        <span class="if-breakdown-dot purchases"></span>
                        Purchases Invoiced
                    </div>

                    <div class="if-breakdown-number">
                        {escape(money(purchases, currency))}
                    </div>

                    <div class="if-breakdown-share">
                        {purchases_pct:.1f}% of invoiced volume
                    </div>
                </div>

            </div>

            <div class="if-breakdown-footer">
                These are invoice values from active records,
                not actual cash flow, revenue or accounting profit.
            </div>

        </section>
        """)


# ============================================================
# DEMO DATA
# ============================================================

def demo_dataset_path():
    return (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "sample_invoices.csv"
    )


def load_demo_dataset():

    try:
        raw = pd.read_csv(
            demo_dataset_path(),
            dtype=str,
            keep_default_na=False,
        )

        validated = validate_invoices(raw)

    except (
        OSError,
        ValueError,
        pd.errors.ParserError,
    ) as error:

        st.error(
            f"Unable to load the demo dataset: {error}"
        )
        return

    st.session_state["validated_invoices"] = validated

    st.rerun()


# ============================================================
# UPLOAD NAVIGATION
# ============================================================

def render_upload_link():

    root = Path(__file__).resolve().parents[1]

    if (root / "legacy_app.py").is_file():

        if st.button(
            "Upload CSV / Excel",
            icon=":material/upload_file:",
            type="primary",
            use_container_width=True,
            key="dashboard_upload_primary",
        ):

            st.switch_page("legacy_app.py")

    else:

        st.warning(
            "Upload workspace unavailable."
        )


def render_empty_spreadsheet():

    st.markdown(
        "#### Choose how to get started"
    )

    st.caption(
        "Analyze your own invoice spreadsheet "
        "or explore the app with demonstration data."
    )

    left, right = st.columns(2, gap="medium")

    with left:

        with st.container(
            border=True,
            key="dashboard_upload_card",
        ):

            st.markdown(
                "### 📂 Upload your invoices"
            )

            st.caption(
                "Import a CSV or Excel file, "
                "validate records and explore analytics."
            )

            render_upload_link()

            st.caption(
                "Recommended for your business data"
            )

    with right:

        with st.container(
            border=True,
            key="dashboard_demo_card",
        ):

            st.markdown(
                "### 🧪 Explore with demo data"
            )

            st.caption(
                "Explore the app using sample invoices. "
                "No file required."
            )

            if st.button(
                "Try Demo Dataset",
                icon=":material/science:",
                type="secondary",
                use_container_width=True,
                key="dashboard_load_demo",
            ):

                load_demo_dataset()

            st.caption(
                "Sample data does not modify SQLite"
            )


def render_upload_navigation():

    render_section(
        "Continue working",
        "Import another file or manage saved invoices.",
    )

    left, right = st.columns(2)

    with left:
        render_upload_link()

    with right:

        if st.button(
            "Open Saved Invoices",
            icon=":material/receipt_long:",
            type="secondary",
            use_container_width=True,
            key="dashboard_saved_premium",
        ):

            st.switch_page(
                "pages/saved_invoices.py"
            )


# ============================================================
# SPREADSHEET ANALYSIS
# ============================================================

def render_spreadsheet_analysis():

    render_intro(
        "SPREADSHEET WORKSPACE",
        "Spreadsheet Analysis",
        "Analyze uploaded CSV / Excel invoices "
        "without modifying SQLite records.",
    )

    data = st.session_state.get(
        "validated_invoices"
    )

    if data is None:
        render_empty_spreadsheet()
        return

    if not isinstance(data, pd.DataFrame):
        st.error(
            "The loaded spreadsheet has an invalid format."
        )
        return

    if "validation_status" not in data.columns:
        st.error(
            "The spreadsheet lacks validation status information."
        )
        return

    valid = data.loc[
        data["validation_status"] == "Valid"
    ]

    review = data.loc[
        data["validation_status"] == "Needs review"
    ]

    render_section(
        "Validation Results",
        "Quality checks for every imported row.",
    )

    pass_rate = (
        100 * len(valid) / len(data)
        if len(data) else 0
    )

    render_cards([
        ("Imported Rows", len(data), "All invoice rows"),
        ("Valid Invoices", len(valid), "Passed validation checks"),
        ("Needs Review", len(review), "Require correction"),
        ("Pass Rate", f"{pass_rate:.0f}%", "Valid rows / total rows"),
    ])

    currencies = []

    if "currency" in valid.columns:

        currencies = sorted({
            str(item).strip().upper()
            for item in valid["currency"].dropna()
            if str(item).strip()
        })

    if currencies:

        render_section(
            "Financial Summary",
            "Only valid invoices in the selected "
            "currency are included.",
        )

        currency = st.selectbox(
            "Spreadsheet Currency",
            options=currencies,
            key="dashboard_uploaded_currency",
        )

        analytics = build_currency_analytics(
            data,
            currency,
        )

        render_cards([
            (
                "Valid Invoice Value",
                f"{analytics['total']:,.2f} {currency}",
                "Validated invoice amount",
            ),
            (
                "Marked Paid",
                f"{analytics['paid']:,.2f} {currency}",
                "Status in spreadsheet",
            ),
            (
                "Marked Unpaid",
                f"{analytics['unpaid']:,.2f} {currency}",
                "Status in spreadsheet",
            ),
            (
                "Currency",
                currency,
                "Not combined with other currencies",
            ),
        ])

        render_section(
            "Invoice Value Breakdown",
            "Validated invoice amounts by supplier and month.",
        )

        left, right = st.columns(
            2,
            gap="medium",
        )

        with left:

            with st.container(border=True):

                st.markdown(
                    "**Invoice Value by Supplier**"
                )

                suppliers = analytics["suppliers"]

                if suppliers.empty:

                    st.info(
                        "No supplier data is available."
                    )

                else:

                    st.bar_chart(
                        suppliers,
                        x="supplier",
                        y="total",
                        color="#168D70",
                    )

        with right:

            with st.container(border=True):

                st.markdown(
                    "**Monthly Invoice Value**"
                )

                months = analytics["months"]

                if months.empty:

                    st.info(
                        "No monthly data is available."
                    )

                else:

                    st.bar_chart(
                        months,
                        x="month",
                        y="total",
                        color="#58BFA0",
                    )

        st.html(
            '<div class="if-dash-help">'
            'Imported paid/unpaid labels are spreadsheet '
            'statuses, not cash transactions. '
            'Actual recorded payments are shown '
            'in Business Overview.'
            '</div>'
        )

    else:

        st.warning(
            "No valid invoices with a currency "
            "are available for financial analysis."
        )

    render_section(
        "Imported Invoices",
        "The latest eight rows from this session.",
    )

    display_columns = [
        "invoice_number",
        "supplier",
        "invoice_date",
        "currency",
        "total",
        "payment_status",
        "validation_status",
    ]

    available = [
        column
        for column in display_columns
        if column in data.columns
    ]

    if available:

        st.dataframe(
            data[available].tail(8),
            hide_index=True,
            width="stretch",
            row_height=37,
        )

    else:

        st.info(
            "No recognized invoice columns are available."
        )

    if len(data):

        st.download_button(
            "Export Validated Session Data (CSV)",
            data=data.to_csv(index=False).encode("utf-8-sig"),
            file_name="invoiceflow_validated_session.csv",
            mime="text/csv",
            key="dashboard_session_export",
        )

    # Navigation appears ONLY at the bottom of Spreadsheet Analysis.
    render_upload_navigation()


# ============================================================
# MAIN DASHBOARD
# ============================================================

apply_dashboard_skin()
st.html(DASHBOARD_CSS)
apply_hover_effects()

st.html("""
<div class="if-hero">
    <div class="if-hero-title">
        Financial Dashboard
    </div>
    <div class="if-hero-description">
        Monitor invoices, payments and uploaded data
        from a centralized workspace.
    </div>
</div>
""")

workspace = st.segmented_control(
    "Dashboard workspace",
    options=[
        "Business Overview",
        "Spreadsheet Analysis",
    ],
    default="Business Overview",
    selection_mode="single",
    key="dashboard_active_workspace",
) or "Business Overview"


if workspace == "Business Overview":

    render_intro(
        "LIVE FINANCIAL DATA",
        "Your Business at a Glance",
        "Active invoices, actual payments and "
        "outstanding balances.",
    )

    render_financial_overview()

    render_invoice_value_breakdown()

else:

    render_spreadsheet_analysis()
