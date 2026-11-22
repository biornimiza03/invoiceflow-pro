
"""InvoiceFlow Pro — imported spreadsheet invoice directory (session only)."""

from html import escape

import pandas as pd
import streamlit as st

from invoiceflow.hover_effects import apply_hover_effects
from invoiceflow.reporter import build_csv_report


CSS = """
<style>
.if-iv-section {margin:24px 0 16px}
.if-iv-section h3 {font-size:19px;font-weight:760;color:#193746;margin:0 0 6px}
.if-iv-section p {font-size:12px;color:#748895;margin:0;line-height:1.6}

.if-iv-empty {display:flex;align-items:center;gap:16px;padding:28px;margin:20px 0;border:1px solid #dce9e5;border-radius:17px;background:linear-gradient(120deg,#fff,#f7fcfa)}
.if-iv-icon {font-size:26px;display:grid;place-items:center;flex-shrink:0;width:54px;height:54px;background:#e8f7f0;border-radius:14px}
.if-iv-empty h3 {color:#193746;font-size:19px;margin:0 0 8px}
.if-iv-empty p {color:#718693;font-size:13px;line-height:1.7;margin:0}
.if-iv-guide {display:grid;grid-template-columns:repeat(3,1fr);gap:13px;margin-bottom:20px}
.if-iv-guide-card {padding:19px;background:#fff;border:1px solid #e0eae8;border-radius:14px}
.if-iv-guide-card small {display:block;color:#078465;font-weight:800;letter-spacing:.5px;margin-bottom:9px}
.if-iv-guide-card strong {display:block;color:#193746;font-size:13px;margin-bottom:7px}
.if-iv-guide-card p {font-size:12px;color:#718693;margin:0;line-height:1.6}

.if-iv-kpis {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:20px 0 25px}
.if-iv-kpi {background:#fff;border:1px solid #dfe9e9;border-radius:15px;padding:19px 20px;box-shadow:0 4px 16px rgba(18,55,60,.035)}
.if-iv-kpi.primary {background:linear-gradient(125deg,#155047,#09846a);border-color:transparent}
.if-iv-kpi label {display:block;color:#718693;font-size:12px;font-weight:650}
.if-iv-kpi strong {display:block;color:#193746;font-size:29px;font-weight:800;margin:9px 0 5px}
.if-iv-kpi small {font-size:11px;color:#8b9ca6}
.if-iv-kpi.primary label,.if-iv-kpi.primary small {color:#d0f1e5}
.if-iv-kpi.primary strong {color:#fff}

.if-iv-note {background:#f1f8f5;border:1px solid #dcece3;color:#527e70;padding:12px 16px;border-radius:12px;font-size:12px;margin:12px 0;line-height:1.6}

/* Compact records toolbar */
.if-iv-toolbar {display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:56px;padding:10px 16px;border:1px solid #e0eae8;border-radius:13px;background:#fff}
.if-iv-toolbar strong {font-size:13px;color:#254753}
.if-iv-toolbar small {display:block;color:#81939e;font-size:11px;margin-top:4px}
.if-iv-page-tag {padding:7px 11px;border-radius:9px;background:#eef7f2;color:#22735b;font-size:12px;font-weight:700}

/* Premium invoice table */
.if-iv-table-shell {border:1px solid #dce8e6;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 6px 22px rgba(20,52,59,.045);margin:14px 0 16px}
.if-iv-table-scroll {overflow-x:auto}
.if-iv-table {width:100%;min-width:1060px;border-collapse:collapse;font-size:12px}
.if-iv-table th {padding:16px 14px;text-align:left;background:#f4f9f7;color:#506e78;font-size:11px;font-weight:750;letter-spacing:.02em;white-space:nowrap}
.if-iv-table td {padding:15px 14px;border-top:1px solid #e8efee;color:#253e49;vertical-align:top}
.if-iv-table tbody tr:nth-child(even) {background:#fbfdfc}
.if-iv-table tbody tr:hover {background:#f1f9f5}
.if-iv-table td:first-child {font-weight:750;color:#175147}
.if-iv-table td:last-child {min-width:180px;max-width:310px;overflow-wrap:anywhere;line-height:1.55}

.if-iv-chip {display:inline-block;border-radius:20px;padding:5px 10px;font-size:11px;font-weight:700;white-space:nowrap}
.if-iv-chip.good {background:#e3f5e9;color:#08754d}
.if-iv-chip.warn {background:#fff0d8;color:#975007}
.if-iv-chip.neutral {background:#edf3f6;color:#526b7a}

/* Validation notice */
.if-iv-review-bar {display:flex;align-items:center;gap:12px;padding:13px 16px;margin:16px 0;border:1px solid #f0d9ad;border-radius:12px;background:#fff9ee;color:#835514;font-size:12px;line-height:1.6}
.if-iv-review-bar.good {background:#f1f8f5;border-color:#d6eade;color:#386f56}
.if-iv-review-dot {font-size:17px;flex-shrink:0}

/* Preview and action buttons */
.st-key-if_invoice_footer [data-testid="stExpander"] {border:1px solid #dce8e4!important;border-radius:13px!important;background:#fff!important;overflow:hidden}
.st-key-if_invoice_footer [data-testid="stExpander"] summary {padding:12px 16px!important;transition:background-color .2s ease}
.st-key-if_invoice_footer [data-testid="stExpander"] summary:hover {background:#f0f8f4!important}
.st-key-if_invoice_footer [data-testid="stDownloadButton"] button {background:#108367!important;border:1px solid #108367!important;color:white!important;border-radius:10px!important;font-weight:700!important}
.st-key-if_invoice_footer [data-testid="stDownloadButton"] button:hover {background:#086e56!important;border-color:#086e56!important}
.st-key-if_invoice_footer [data-testid="stButton"] button {border-radius:10px!important;transition:background-color .2s ease,border-color .2s ease}
.st-key-if_invoice_footer [data-testid="stButton"] button:hover {background:#e9f7f0!important;border-color:#b1dac6!important;color:#087b61!important}

@media (max-width:1000px) {.if-iv-kpis {grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:700px) {.if-iv-guide {grid-template-columns:1fr}.if-iv-empty {padding:19px}.if-iv-toolbar {align-items:flex-start}}
@media (max-width:500px) {.if-iv-kpis {grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce) {.st-key-if_invoice_footer button,.st-key-if_invoice_footer summary {transition:none!important}}
</style>
"""


REQUIRED = (
    "invoice_number", "supplier", "invoice_date",
    "due_date", "total", "currency", "payment_status",
    "validation_status", "validation_issues",
)


# =====================================================
# HELPERS
# =====================================================

def safe(value):
    """Escape spreadsheet content before inserting it into HTML."""
    if value is None:
        return "—"

    try:
        if bool(pd.isna(value)):
            return "—"
    except (TypeError, ValueError):
        pass

    value = str(value).strip()
    return escape(value) if value else "—"


def heading(title, subtitle):
    st.html(
        '<div class="if-iv-section">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(subtitle)}</p></div>'
    )


def reset_filters():
    for key, value in {
        "if_invoice_search": "",
        "if_invoice_supplier": "All suppliers",
        "if_invoice_payment": "All payments",
        "if_invoice_validation": "All statuses",
        "if_invoice_currency": "All currencies",
        "if_invoice_sort": "Newest issue date",
        "if_invoice_page": 1,
    }.items():
        st.session_state[key] = value


def valid_state(key, options):
    if key in st.session_state and st.session_state[key] not in options:
        st.session_state[key] = options[0]


def chip(value, validation=False):
    status = str(value).strip().casefold()

    if validation:
        css = (
            "good" if status == "valid"
            else "warn" if status == "needs review"
            else "neutral"
        )
    else:
        css = (
            "good" if status == "paid"
            else "warn" if status in (
                "unpaid", "partial", "partially paid"
            )
            else "neutral"
        )

    return f'<span class="if-iv-chip {css}">{safe(value)}</span>'


# =====================================================
# EMPTY SESSION
# =====================================================

def empty_page():
    st.html("""
    <div class="if-iv-empty">
        <div class="if-iv-icon" aria-hidden="true">📄</div>
        <div>
            <h3>No spreadsheet invoices loaded</h3>
            <p>
                This directory reviews invoices imported for the
                current session. Upload CSV/Excel or try the demo
                dataset. Persistently saved invoices are available
                separately under Saved Invoices.
            </p>
        </div>
    </div>

    <div class="if-iv-guide">
        <div class="if-iv-guide-card">
            <small>01 · PREPARE</small>
            <strong>Upload or try a demo</strong>
            <p>Load your spreadsheet or the example dataset.</p>
        </div>

        <div class="if-iv-guide-card">
            <small>02 · VALIDATE</small>
            <strong>Check the records</strong>
            <p>Review valid invoices and data quality issues.</p>
        </div>

        <div class="if-iv-guide-card">
            <small>03 · EXPORT</small>
            <strong>Filter and download</strong>
            <p>Export the records you need as CSV.</p>
        </div>
    </div>
    """)

    a, b, c = st.columns(3)

    with a:
        if st.button(
            "Open Dashboard / Demo",
            type="primary",
            icon=":material/dashboard:",
            use_container_width=True,
        ):
            st.switch_page("pages/dashboard.py")

    with b:
        if st.button(
            "Upload CSV / Excel",
            icon=":material/upload_file:",
            use_container_width=True,
        ):
            st.switch_page("legacy_app.py")

    with c:
        if st.button(
            "Open Saved Invoices",
            icon=":material/receipt_long:",
            use_container_width=True,
        ):
            st.switch_page("pages/saved_invoices.py")


# =====================================================
# STATISTIC CARDS
# =====================================================

def stats(frame):
    flags = (
        frame["validation_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    suppliers = (
        frame["supplier"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = [
        (
            "Matching invoices",
            len(frame),
            "Results after filtering",
        ),
        (
            "Valid",
            int(flags.eq("valid").sum()),
            "Records passing validation",
        ),
        (
            "Needs review",
            int(flags.eq("needs review").sum()),
            "Records flagged for review",
        ),
        (
            "Suppliers",
            int(suppliers[suppliers.ne("")].nunique()),
            "Distinct suppliers in results",
        ),
    ]

    parts = []

    for i, (name, value, desc) in enumerate(values):
        parts.append(
            f'<div class="if-iv-kpi{" primary" if i == 0 else ""}">'
            f'<label>{escape(name)}</label>'
            f'<strong>{value}</strong>'
            f'<small>{escape(desc)}</small>'
            '</div>'
        )

    st.html(
        '<div class="if-iv-kpis">'
        + "".join(parts)
        + '</div>'
    )


# =====================================================
# PREMIUM INVOICE TABLE
# =====================================================

def table(frame):
    rows = []

    for _, row in frame.iterrows():
        rows.append(
            '<tr>'
            f'<td>{safe(row["invoice_number"])}</td>'
            f'<td>{safe(row["supplier"])}</td>'
            f'<td>{safe(row["invoice_date"])}</td>'
            f'<td>{safe(row["due_date"])}</td>'
            f'<td>{safe(row["total"])} {safe(row["currency"])}</td>'
            f'<td>{chip(row["payment_status"])}</td>'
            f'<td>{chip(row["validation_status"], True)}</td>'
            f'<td>{safe(row["validation_issues"])}</td>'
            '</tr>'
        )

    st.html(
        '<div class="if-iv-table-shell">'
        '<div class="if-iv-table-scroll">'
        '<table class="if-iv-table">'
        '<thead><tr>'
        '<th>Invoice</th><th>Supplier</th>'
        '<th>Issued</th><th>Due Date</th>'
        '<th>Amount</th><th>Payment</th>'
        '<th>Validation</th><th>Notes</th>'
        '</tr></thead><tbody>'
        + "".join(rows)
        + '</tbody></table></div></div>'
    )


# =====================================================
# LOADED SPREADSHEET WORKSPACE
# =====================================================

def loaded_page(data):
    heading(
        "Invoice Directory",
        "Search, filter and review invoices imported into this session.",
    )

    st.html(
        '<div class="if-iv-note">'
        'Session invoices are separate from Saved Invoices in SQLite. '
        'Filtering and exporting here do not modify saved business records.'
        '</div>'
    )

    suppliers = ["All suppliers"] + sorted(
        {
            str(x).strip()
            for x in data["supplier"].dropna()
            if str(x).strip()
        },
        key=str.casefold,
    )

    payments = ["All payments"] + sorted({
        str(x).strip().casefold()
        for x in data["payment_status"].dropna()
        if str(x).strip()
    })

    validations = ["All statuses"] + sorted(
        {
            str(x).strip()
            for x in data["validation_status"].dropna()
            if str(x).strip()
        },
        key=str.casefold,
    )

    currencies = ["All currencies"] + sorted({
        str(x).strip()
        for x in data["currency"].dropna()
        if str(x).strip()
    })

    sorts = [
        "Newest issue date",
        "Oldest issue date",
        "Invoice number (A–Z)",
        "Supplier (A–Z)",
    ]

    for key, options in (
        ("if_invoice_supplier", suppliers),
        ("if_invoice_payment", payments),
        ("if_invoice_validation", validations),
        ("if_invoice_currency", currencies),
        ("if_invoice_sort", sorts),
    ):
        valid_state(key, options)

    # Search and filters

    a, b, c = st.columns([2.1, 1.3, 1.1])

    with a:
        search = st.text_input(
            "Search invoices",
            placeholder="Invoice number or supplier",
            key="if_invoice_search",
        ).strip().casefold()

    with b:
        supplier = st.selectbox(
            "Supplier", suppliers, key="if_invoice_supplier"
        )

    with c:
        payment = st.selectbox(
            "Payment status", payments, key="if_invoice_payment"
        )

    a, b, c, d = st.columns([1.2, 1, 1.5, .8])

    with a:
        validation = st.selectbox(
            "Validation status",
            validations,
            key="if_invoice_validation",
        )

    with b:
        currency = st.selectbox(
            "Currency",
            currencies,
            key="if_invoice_currency",
        )

    with c:
        order = st.selectbox(
            "Sort by",
            sorts,
            key="if_invoice_sort",
        )

    with d:
        st.button(
            "Reset filters",
            on_click=reset_filters,
            use_container_width=True,
            key="if_invoice_reset",
        )

    # Apply filters

    frame = data.copy()

    if search:
        mask = (
            frame["invoice_number"]
            .fillna("")
            .astype(str)
            .str.contains(search, case=False, regex=False)
            |
            frame["supplier"]
            .fillna("")
            .astype(str)
            .str.contains(search, case=False, regex=False)
        )
        frame = frame.loc[mask]

    if supplier != "All suppliers":
        frame = frame.loc[
            frame["supplier"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(supplier)
        ]

    if payment != "All payments":
        frame = frame.loc[
            frame["payment_status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(payment)
        ]

    if validation != "All statuses":
        frame = frame.loc[
            frame["validation_status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(validation)
        ]

    if currency != "All currencies":
        frame = frame.loc[
            frame["currency"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(currency)
        ]

    # Sorting

    if order in ("Newest issue date", "Oldest issue date"):
        dates = pd.to_datetime(
            frame["invoice_date"],
            errors="coerce",
        )
        frame = (
            frame.assign(_sort=dates)
            .sort_values(
                "_sort",
                ascending=order == "Oldest issue date",
                na_position="last",
                kind="stable",
            )
            .drop(columns="_sort")
        )
    else:
        col = (
            "invoice_number"
            if order == "Invoice number (A–Z)"
            else "supplier"
        )
        frame = frame.sort_values(
            col,
            key=lambda s: (
                s.fillna("").astype(str).str.casefold()
            ),
            kind="stable",
        )

    stats(frame)

    heading(
        "Invoice Records",
        "Review validation status and export the filtered records.",
    )

    if frame.empty:
        st.info(
            "No invoices match these filters. "
            "Change the filters or click Reset filters."
        )
        return

    # Compact toolbar and pagination

    page_count = max(1, (len(frame) + 49) // 50)
    valid_state(
        "if_invoice_page",
        list(range(1, page_count + 1)),
    )

    left, right = st.columns(
        [3.6, 1.1],
        vertical_alignment="bottom",
    )

    with left:
        st.html(
            '<div class="if-iv-toolbar">'
            f'<div><strong>{len(frame)} matching invoices</strong>'
            f'<small>{len(data)} total in the current session</small></div>'
            f'<span class="if-iv-page-tag">'
            f'{page_count} page{"s" if page_count != 1 else ""}'
            '</span></div>'
        )

    with right:
        if page_count > 1:
            page = st.selectbox(
                "Page",
                list(range(1, page_count + 1)),
                format_func=lambda x: (
                    f"Page {x} of {page_count}"
                ),
                key="if_invoice_page",
            )
        else:
            page = 1
            st.html(
                '<div class="if-iv-toolbar">'
                '<strong>Page 1 of 1</strong>'
                '</div>'
            )

    visible = frame.iloc[
        (page - 1) * 50:
        page * 50
    ]

    table(visible)

    st.caption(
        f"Showing {len(visible)} on this page "
        f"· {len(frame)} matching records"
    )

    # Validation status message

    review = (
        frame["validation_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("needs review")
        .sum()
    )

    if review:
        st.html(
            '<div class="if-iv-review-bar">'
            '<span class="if-iv-review-dot">⚠</span>'
            f'<span><strong>{review} invoice(s) need review.</strong> '
            'Check the Notes column before using these records.'
            '</span></div>'
        )
    else:
        st.html(
            '<div class="if-iv-review-bar good">'
            '<span class="if-iv-review-dot">✓</span>'
            '<span>All matching invoices passed validation.</span>'
            '</div>'
        )

    # Premium preview and actions

    with st.container(key="if_invoice_footer"):

        with st.expander(
            f"View complete invoice data — {len(frame)} rows"
        ):
            st.dataframe(
                frame,
                hide_index=True,
                width="stretch",
            )

        a, b, c = st.columns([1.5, 1, 1])

        with a:
            st.download_button(
                "Download Filtered CSV",
                data=build_csv_report(frame),
                file_name="InvoiceFlow_Filtered.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
                key="if_invoice_download",
            )

        with b:
            if st.button(
                "Upload another file",
                icon=":material/upload_file:",
                use_container_width=True,
            ):
                st.switch_page("legacy_app.py")

        with c:
            if st.button(
                "Saved Invoices",
                icon=":material/receipt_long:",
                use_container_width=True,
            ):
                st.switch_page(
                    "pages/saved_invoices.py"
                )


# =====================================================
# PAGE INITIALIZATION
# =====================================================

apply_hover_effects()
st.html(CSS)

st.html("""
<div class="if-hero">
    <div class="if-hero-title">
        Invoice Management
    </div>
    <div class="if-hero-description">
        Search, filter and review your imported spreadsheet invoices.
    </div>
</div>
""")

data = st.session_state.get("validated_invoices")

if not isinstance(data, pd.DataFrame) or data.empty:
    empty_page()

else:
    missing = [
        key for key in REQUIRED
        if key not in data.columns
    ]

    if missing:
        st.error(
            "Missing expected spreadsheet columns: "
            + ", ".join(missing)
        )

        if st.button("Open Dashboard / Demo"):
            st.switch_page("pages/dashboard.py")

    else:
        loaded_page(data)
