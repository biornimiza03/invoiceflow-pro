
"""InvoiceFlow Pro — Upload & Validation.

CSV/Excel imports live in the Streamlit session, independently of SQLite.
Business logic remains in the existing invoiceflow modules.
"""

from html import escape
from zipfile import BadZipFile

import altair as alt
import pandas as pd
import streamlit as st

from invoiceflow.analytics import build_currency_analytics
from invoiceflow.filters import filter_invoices
from invoiceflow.reader import read_invoice_file
from invoiceflow.reporter import build_csv_report, build_excel_report
from invoiceflow.validator import validate_invoices

st.set_page_config(
    page_title="InvoiceFlow | Upload & Validation",
    page_icon="📊",
    layout="wide",
)


# ==========================================================
# ONE CONSOLIDATED CSS BLOCK
# ==========================================================

UPLOAD_CSS = """
<style>
.if-up-hero {
    padding:30px 34px;
    margin:2px 0 28px;
    border-radius:19px;
    background:linear-gradient(115deg,#183543,#125447 60%,#098468);
    box-shadow:0 10px 28px rgba(13,60,59,.075);
}
.if-up-eyebrow {
    font-size:10px;
    font-weight:800;
    letter-spacing:1.6px;
    color:#b7eee0;
    margin-bottom:10px;
}
.if-up-hero h1 {
    font-size:clamp(24px,2.8vw,31px);
    letter-spacing:-.55px;
    margin:0 0 8px;
    color:#fff;
    font-weight:790;
}
.if-up-hero p {
    font-size:13px;
    line-height:1.65;
    color:#d5eae8;
    margin:0;
}

.if-up-heading {margin:28px 0 14px}
.if-up-heading small {
    display:block;
    color:#09836a;
    font-weight:800;
    font-size:10px;
    letter-spacing:1.3px;
    margin-bottom:7px;
}
.if-up-heading h3 {
    color:#193746;
    font-size:19px;
    font-weight:760;
    margin:0 0 7px;
}
.if-up-heading p {
    font-size:12px;
    color:#738894;
    line-height:1.6;
    margin:0;
}

.st-key-if_upload_zone {
    background:linear-gradient(130deg,#fff,#f8fcfa)!important;
    border:1px solid #d9e9e2!important;
    border-radius:17px!important;
    padding:20px 23px!important;
    box-shadow:0 5px 20px rgba(20,55,60,.035);
}
.st-key-if_upload_zone [data-testid="stFileUploader"] section {
    background:#fff!important;
    border:1px dashed #9bceb8!important;
    border-radius:13px!important;
    min-height:112px;
    transition:background-color .2s ease,border-color .2s ease;
}
.st-key-if_upload_zone [data-testid="stFileUploader"] section:hover {
    background:#f1faf5!important;
    border-color:#0a9874!important;
}
.st-key-if_upload_zone [data-testid="stFileUploader"] button {
    border-radius:9px!important;
    background:#fff!important;
    border:1px solid #badccf!important;
    color:#08775d!important;
}
.st-key-if_upload_zone [data-testid="stFileUploader"] button:hover {
    background:#e9f7f0!important;
    border-color:#91cbb2!important;
}
.if-up-tip {
    padding:11px 15px;
    margin:14px 0 2px;
    border-radius:10px;
    background:#f1f8f5;
    border:1px solid #deeee6;
    color:#527b6c;
    font-size:12px;
    line-height:1.65;
}
.if-up-file {
    display:flex;
    gap:12px;
    align-items:center;
    justify-content:space-between;
    background:#fff;
    border:1px solid #e0ebe7;
    border-radius:10px;
    padding:11px 14px;
    margin:8px 0;
    color:#254652;
    font-size:12px;
}
.if-up-file-name {font-weight:700;overflow-wrap:anywhere}
.if-up-file-meta {color:#80929b;white-space:nowrap;font-size:11px}

.if-up-stats {
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:13px;
    margin:16px 0 22px;
}
.if-up-stat {
    padding:19px 20px;
    background:#fff;
    border:1px solid #dfe9e9;
    border-radius:15px;
    min-width:0;
    box-shadow:0 5px 16px rgba(18,55,60,.035);
}
.if-up-stat.primary {
    background:linear-gradient(125deg,#155047,#09846a);
    border-color:transparent;
}
.if-up-stat small {
    display:block;
    font-size:11px;
    font-weight:650;
    color:#728794;
}
.if-up-stat strong {
    display:block;
    font-size:clamp(22px,2.1vw,28px);
    font-weight:800;
    color:#193746;
    margin:10px 0 6px;
    overflow-wrap:anywhere;
}
.if-up-stat span {
    font-size:11px;
    color:#90a0a9;
    line-height:1.5;
}
.if-up-stat.primary small,
.if-up-stat.primary span {color:#d1f1e6}
.if-up-stat.primary strong {color:#fff}

.if-up-message {
    display:flex;
    align-items:flex-start;
    gap:12px;
    padding:14px 17px;
    margin:16px 0;
    border-radius:12px;
    border:1px solid #d6eadd;
    background:#f0f9f3;
    color:#386e58;
    font-size:12px;
    line-height:1.7;
}
.if-up-message.warn {
    background:#fff9ee;
    border-color:#ecd6ac;
    color:#8b5915;
}
.if-up-message i {
    font-size:17px;
    font-style:normal;
    flex-shrink:0;
}
[data-testid="stMain"] [data-testid="stDataFrame"] {
    border-radius:12px;
    overflow:hidden;
}

.st-key-if_up_exports [data-testid="stDownloadButton"] button {
    border-radius:10px!important;
    background:#fff!important;
    border:1px solid #bcdccc!important;
    color:#0c765d!important;
    font-weight:650!important;
    min-height:42px;
    transition:background-color .2s ease,border-color .2s ease;
}
.st-key-if_up_exports [data-testid="stDownloadButton"] button:hover {
    background:#e9f7f0!important;
    border-color:#8dc8ac!important;
}
.st-key-if_up_next [data-testid="stButton"] button {
    border-radius:10px!important;
    min-height:42px;
    transition:background-color .2s ease,border-color .2s ease;
}
.st-key-if_up_next [data-testid="stButton"] button:not([kind="primary"]):hover {
    background:#e9f7f0!important;
    border-color:#95cdb7!important;
    color:#087b61!important;
}

@media(max-width:1050px){
    .if-up-stats {
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
}
@media(max-width:650px){
    .if-up-hero {padding:24px 20px}
    .if-up-stats {grid-template-columns:1fr}
    .st-key-if_upload_zone {padding:16px!important}
    .if-up-file {
        align-items:flex-start;
        flex-direction:column;
        gap:3px;
    }
}
@media(prefers-reduced-motion:reduce){
    .st-key-if_upload_zone [data-testid="stFileUploader"] section,
    .st-key-if_upload_zone button,
    .st-key-if_up_exports button,
    .st-key-if_up_next button {
        transition:none!important;
    }
}
</style>
"""


# ==========================================================
# PRESENTATION / FILTER HELPERS
# ==========================================================

def section(step, name, description):
    st.html(
        '<div class="if-up-heading">'
        f'<small>{escape(step)}</small>'
        f'<h3>{escape(name)}</h3>'
        f'<p>{escape(description)}</p>'
        '</div>'
    )


def cards(items):
    blocks = []

    for index, (label, value, note) in enumerate(items):
        variant = " primary" if index == 0 else ""

        blocks.append(
            f'<div class="if-up-stat{variant}">'
            f'<small>{escape(str(label))}</small>'
            f'<strong>{escape(str(value))}</strong>'
            f'<span>{escape(str(note))}</span>'
            '</div>'
        )

    st.html(
        '<div class="if-up-stats">'
        + "".join(blocks)
        + '</div>'
    )


def reset_filters():
    for key, value in {
        "if_up_supplier": "All suppliers",
        "if_up_currency": "All currencies",
        "if_up_payment": "All payments",
        "if_up_validation": "All statuses",
    }.items():
        st.session_state[key] = value


def filter_options(frame, column, placeholder):
    values = sorted(
        {
            str(value).strip()
            for value in frame[column].dropna()
            if str(value).strip()
        },
        key=str.casefold,
    )
    return [placeholder] + values


def ensure_choice(key, choices):
    if (
        key in st.session_state
        and st.session_state[key] not in choices
    ):
        st.session_state[key] = choices[0]


def uploaded_card(uploaded_file):
    st.html(
        '<div class="if-up-file">'
        f'<span class="if-up-file-name">'
        f'📄 {escape(uploaded_file.name)}'
        '</span>'
        f'<span class="if-up-file-meta">'
        f'{uploaded_file.size / 1024:,.1f} KB'
        '</span>'
        '</div>'
    )


# ==========================================================
# PAGE HEADER AND FILE UPLOAD
# ==========================================================

st.html(UPLOAD_CSS)

st.html("""
<section class="if-up-hero">
    <div class="if-up-eyebrow">
        INVOICE IMPORT WORKSPACE
    </div>
    <h1>Upload &amp; Validation</h1>
    <p>
        Import CSV or Excel spreadsheets,
        verify invoice data and export reliable reports.
    </p>
</section>
""")

section(
    "STEP 01 · IMPORT",
    "Upload invoice files",
    "Upload one or more CSV or XLSX files for automatic validation.",
)

with st.container(border=True, key="if_upload_zone"):

    files = st.file_uploader(
        "Choose your CSV or Excel files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="if_upload_files",
    )

    st.html(
        '<div class="if-up-tip">'
        'Supported formats: CSV and XLSX. '
        'Multiple files are supported. '
        'Imports are reviewed in the current session; '
        'saved SQLite invoices stay separate.'
        '</div>'
    )


if not files:

    st.html(
        '<div class="if-up-message">'
        '<i>📄</i>'
        '<span>'
        '<strong>Ready for your files.</strong> '
        'Select a CSV/Excel spreadsheet above '
        'to view validation results, financial summaries '
        'and export options.'
        '</span>'
        '</div>'
    )

    if st.session_state.get("validated_invoices") is not None:
        st.caption(
            "Previously imported session data may still "
            "be visible on Dashboard and Invoices. "
            "New uploads will replace that session dataset."
        )

    st.stop()


# ==========================================================
# READ AND VALIDATE
# ==========================================================

frames = []
failures = []

for uploaded_file in files:

    try:
        invoices = read_invoice_file(uploaded_file)

        invoices["source_file"] = uploaded_file.name

        frames.append(invoices)

        uploaded_card(uploaded_file)

    except (
        ValueError,
        UnicodeError,
        pd.errors.ParserError,
        BadZipFile,
        OSError,
    ) as error:

        failures.append(
            (uploaded_file.name, str(error))
        )


for name, error in failures:
    st.error(f"Unable to import {name}: {error}")


if not frames:

    st.error(
        "No files could be imported. "
        "Check the CSV/Excel format and try again."
    )

    st.stop()


try:

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    validated = validate_invoices(combined)

except (
    ValueError,
    KeyError,
    TypeError,
) as error:

    st.error(
        f"Unable to validate the uploaded data: {error}"
    )

    st.stop()


st.session_state["validated_invoices"] = validated.copy()

valid_count = int(
    validated["validation_status"].eq("Valid").sum()
)

review_count = len(validated) - valid_count

pass_rate = (
    100 * valid_count / len(validated)
    if len(validated)
    else 0
)

if failures:
    st.warning(
        f"Imported {len(frames)} file(s); "
        f"{len(failures)} failed."
    )
else:
    st.success(
        f"Successfully imported {len(frames)} file(s)."
    )


# ==========================================================
# STEP 02 — VALIDATION
# ==========================================================

section(
    "STEP 02 · VALIDATE",
    "Validation overview",
    "Quality check for imported invoice rows.",
)

cards([
    (
        "Imported rows",
        len(validated),
        "All processed invoice records",
    ),
    (
        "Valid invoices",
        valid_count,
        "Passed validation checks",
    ),
    (
        "Needs review",
        review_count,
        "Rows requiring attention",
    ),
    (
        "Pass rate",
        f"{pass_rate:.0f}%",
        "Valid rows / imported rows",
    ),
])

if review_count:

    st.html(
        '<div class="if-up-message warn">'
        '<i>⚠️</i>'
        '<span>'
        f'<strong>{review_count} invoice(s) need review.</strong> '
        'Check their validation status and issues '
        'before using them.'
        '</span>'
        '</div>'
    )

else:

    st.html(
        '<div class="if-up-message">'
        '<i>✓</i>'
        '<span>'
        '<strong>All imported invoices passed validation.</strong> '
        'Review records and export reports below.'
        '</span>'
        '</div>'
    )


# ==========================================================
# STEP 03 — FILTER AND REVIEW
# ==========================================================

section(
    "STEP 03 · REVIEW",
    "Invoice validation results",
    "Filter records and inspect issues without "
    "changing the saved session dataset.",
)

choices = {
    "if_up_supplier": filter_options(
        validated,
        "supplier",
        "All suppliers",
    ),
    "if_up_currency": filter_options(
        validated,
        "currency",
        "All currencies",
    ),
    "if_up_payment": filter_options(
        validated,
        "payment_status",
        "All payments",
    ),
    "if_up_validation": filter_options(
        validated,
        "validation_status",
        "All statuses",
    ),
}

for key, values in choices.items():
    ensure_choice(key, values)


c1, c2, c3, c4 = st.columns(4)

with c1:
    supplier = st.selectbox(
        "Supplier",
        choices["if_up_supplier"],
        key="if_up_supplier",
    )

with c2:
    currency = st.selectbox(
        "Currency",
        choices["if_up_currency"],
        key="if_up_currency",
    )

with c3:
    payment = st.selectbox(
        "Payment status",
        choices["if_up_payment"],
        key="if_up_payment",
    )

with c4:
    status = st.selectbox(
        "Validation status",
        choices["if_up_validation"],
        key="if_up_validation",
    )


filtered = filter_invoices(
    validated,
    supplier=supplier,
    currency=currency,
    payment_status=payment,
    validation_status=status,
)


left, right = st.columns(
    [4, 1],
    vertical_alignment="bottom",
)

with left:
    st.caption(
        f"Showing {len(filtered)} of {len(validated)} invoices. "
        "Filters affect the preview only."
    )

with right:
    st.button(
        "Reset filters",
        key="if_up_reset_filters",
        on_click=reset_filters,
        use_container_width=True,
    )


if filtered.empty:

    st.info(
        "No invoices match these filters. "
        "Try resetting the filters."
    )

else:

    # Automatic table height avoids unnecessary blank rows.
    rows_height = min(
        365,
        max(110, (len(filtered) + 1) * 36 + 5),
    )

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        row_height=36,
        height=rows_height,
    )


# ==========================================================
# STEP 04 — FINANCIAL ANALYTICS
# ==========================================================

section(
    "STEP 04 · ANALYZE",
    "Financial analytics",
    "Only valid invoice rows are included; "
    "different currencies are never combined.",
)

valid_rows = validated.loc[
    validated["validation_status"] == "Valid"
]

currencies = sorted({
    str(value).strip().upper()
    for value in valid_rows["currency"].dropna()
    if str(value).strip()
})


if currencies:

    ensure_choice(
        "if_up_reporting_currency",
        currencies,
    )

    selected_currency = st.selectbox(
        "Reporting currency",
        currencies,
        key="if_up_reporting_currency",
    )

    analytics = build_currency_analytics(
        validated,
        selected_currency,
    )

    if analytics is not None:

        cards([
            (
                "Valid invoice value",
                f"{analytics['total']:,.2f} {selected_currency}",
                "Validated total",
            ),
            (
                "Marked paid",
                f"{analytics['paid']:,.2f} {selected_currency}",
                "Imported spreadsheet status",
            ),
            (
                "Marked unpaid",
                f"{analytics['unpaid']:,.2f} {selected_currency}",
                "Imported spreadsheet status",
            ),
            (
                "Currency",
                selected_currency,
                "This currency only",
            ),
        ])

        chart_left, chart_right = st.columns(
            2,
            gap="medium",
        )

        # CHART 1 — INVOICE VALUE BY SUPPLIER

        with chart_left:

            with st.container(border=True):

                st.markdown(
                    "**Invoice value by supplier**"
                )

                suppliers_df = analytics["suppliers"]

                if suppliers_df.empty:

                    st.caption(
                        "No supplier values to chart."
                    )

                else:

                    suppliers_chart = (
                        alt.Chart(suppliers_df)
                        .mark_bar(
                            color="#138e72",
                            cornerRadiusTopLeft=5,
                            cornerRadiusTopRight=5,
                        )
                        .encode(
                            x=alt.X(
                                "supplier:N",
                                title="Supplier",
                                sort=None,
                            ),
                            y=alt.Y(
                                "total:Q",
                                title=f"Value ({selected_currency})",
                                scale=alt.Scale(
                                    zero=True,
                                    domainMin=0,
                                ),
                            ),
                            tooltip=[
                                alt.Tooltip(
                                    "supplier:N",
                                    title="Supplier",
                                ),
                                alt.Tooltip(
                                    "total:Q",
                                    title="Value",
                                    format=",.2f",
                                ),
                            ],
                        )
                        .properties(height=260)
                    )

                    st.altair_chart(
                        suppliers_chart,
                        use_container_width=True,
                    )

        # CHART 2 — MONTHLY INVOICE VALUE

        with chart_right:

            with st.container(border=True):

                st.markdown(
                    "**Monthly invoice value**"
                )

                monthly_df = analytics["months"]

                if monthly_df.empty:

                    st.caption(
                        "No monthly values to chart."
                    )

                else:

                    monthly_chart = (
                        alt.Chart(monthly_df)
                        .mark_bar(
                            color="#58bfa0",
                            cornerRadiusTopLeft=5,
                            cornerRadiusTopRight=5,
                        )
                        .encode(
                            x=alt.X(
                                "month:N",
                                title="Month",
                                sort=None,
                            ),
                            y=alt.Y(
                                "total:Q",
                                title=f"Value ({selected_currency})",
                                scale=alt.Scale(
                                    zero=True,
                                    domainMin=0,
                                ),
                            ),
                            tooltip=[
                                alt.Tooltip(
                                    "month:N",
                                    title="Month",
                                ),
                                alt.Tooltip(
                                    "total:Q",
                                    title="Value",
                                    format=",.2f",
                                ),
                            ],
                        )
                        .properties(height=260)
                    )

                    st.altair_chart(
                        monthly_chart,
                        use_container_width=True,
                    )

        st.caption(
            "Paid/unpaid labels come from the imported spreadsheet, "
            "not verified cash transactions. Saved invoice payments "
            "live separately in SQLite."
        )

else:

    st.info(
        "No valid invoice rows are available "
        "for financial analysis."
    )


# ==========================================================
# STEP 05 — EXPORT
# ==========================================================

section(
    "STEP 05 · EXPORT",
    "Export reports",
    "Download the complete validated import, "
    "including rows needing review.",
)

with st.container(key="if_up_exports"):

    excel_col, csv_col = st.columns(2)

    with excel_col:

        st.download_button(
            "Download Excel Report",
            data=build_excel_report(validated),
            file_name="InvoiceFlow_Report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="if_up_export_excel",
        )

    with csv_col:

        st.download_button(
            "Download CSV Report",
            data=build_csv_report(validated),
            file_name="InvoiceFlow_Report.csv",
            mime="text/csv",
            use_container_width=True,
            key="if_up_export_csv",
        )


# ==========================================================
# CONTINUE WORKING
# ==========================================================

section(
    "NEXT STEPS",
    "Continue working",
    "Review imported records or return to your business dashboard.",
)

with st.container(key="if_up_next"):

    invoice_col, dashboard_col = st.columns(2)

    with invoice_col:

        if st.button(
            "Open Invoice Management",
            icon=":material/receipt_long:",
            type="primary",
            use_container_width=True,
            key="if_up_open_invoices",
        ):

            st.switch_page("pages/invoices.py")

    with dashboard_col:

        if st.button(
            "Open Dashboard",
            icon=":material/dashboard:",
            use_container_width=True,
            key="if_up_open_dashboard",
        ):

            st.switch_page("pages/dashboard.py")
