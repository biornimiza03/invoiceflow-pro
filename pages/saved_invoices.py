
"""InvoiceFlow Pro — Smart Invoice Directory and Archived Invoice Workspace."""

import hashlib
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import streamlit as st

from invoiceflow.database import list_contacts
from invoiceflow.hover_effects import apply_hover_effects
from invoiceflow.invoice_details import render_invoice_details
from invoiceflow.invoice_store import (
    create_saved_invoice,
    initialize_invoice_store,
    list_archived_invoices,
    list_saved_invoices,
    restore_saved_invoice,
)


def reset_invoice_filters():
    """Return search, filters and sorting to their default values."""
    st.session_state["directory_search"] = ""
    st.session_state["directory_type"] = "All"
    st.session_state["directory_status"] = "All"
    st.session_state["directory_currency"] = "All"
    st.session_state["directory_sort"] = "Newest issue date"


def as_decimal(value):
    """Convert a stored display amount to a number for sorting."""
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


# =====================================================
# SHARED PAGE STYLES
# =====================================================

PAGE_CSS = """
<style>

.if-stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin: 20px 0 30px;
}

.if-stat-card {
    background: #fff;
    border: 1px solid #dee7e9;
    border-radius: 16px;
    padding: 22px;
    min-height: 155px;
    box-shadow: 0 4px 18px rgba(20, 40, 50, .035);
    transition: transform .2s ease, box-shadow .2s ease;
}

.if-stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(20, 40, 50, .09);
}

.if-stat-primary {
    background: linear-gradient(125deg, #173f3b, #11745d);
    border-color: transparent;
}

.if-stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 17px;
}

.if-stat-label {
    font-size: 13px;
    font-weight: 600;
    color: #5e7180;
}

.if-stat-icon {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: #f0f4f6;
    font-size: 18px;
}

.if-stat-value {
    font-size: 34px;
    font-weight: 750;
    letter-spacing: -1px;
    color: #172c3a;
    margin-bottom: 9px;
}

.if-stat-description {
    font-size: 11px;
    color: #83919d;
}

.if-stat-primary .if-stat-label,
.if-stat-primary .if-stat-description {
    color: #d7f6ec;
}

.if-stat-primary .if-stat-value {
    color: #fff;
}

/* ============================================
   PREMIUM ARCHIVE SUMMARY
============================================ */

.if-archive-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 20px 23px;
    margin: 18px 0 22px;
    border-radius: 16px;
    background: linear-gradient(120deg, #fff, #f5fbf8);
    border: 1px solid #dbe9e4;
    box-shadow: 0 5px 18px rgba(17, 40, 52, .04);
}

.if-archive-summary-title {
    font-size: 16px;
    font-weight: 750;
    color: #193746;
    margin-bottom: 5px;
}

.if-archive-summary-text {
    font-size: 12px;
    color: #718894;
    line-height: 1.6;
}

.if-archive-counter {
    flex-shrink: 0;
    min-width: 64px;
    text-align: center;
    background: #e8f7f0;
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 27px;
    font-weight: 800;
    color: #087d64;
}

/* ============================================
   EMPTY ARCHIVE
============================================ */

.if-archive-empty {
    display: flex;
    align-items: center;
    gap: 17px;
    padding: 25px;
    border: 1px solid #dbe9e4;
    border-radius: 17px;
    background: linear-gradient(120deg, #fff, #f8fcfa);
    margin: 16px 0;
}

.if-archive-empty-icon {
    display: grid;
    place-items: center;
    width: 50px;
    height: 50px;
    flex-shrink: 0;
    border-radius: 14px;
    background: #e8f7f0;
    color: #0b8968;
    font-size: 24px;
}

.if-archive-empty-title {
    color: #193746;
    font-size: 18px;
    font-weight: 750;
    margin-bottom: 6px;
}

.if-archive-empty-text {
    color: #758b97;
    font-size: 13px;
    line-height: 1.6;
}

/* ============================================
   RESTORE PANEL
============================================ */

.st-key-archive_restore_panel {
    border: 1px solid #dbe9e4 !important;
    background: #fff !important;
    border-radius: 17px !important;
    padding: 21px 23px !important;
    margin-top: 22px;
    box-shadow: 0 5px 18px rgba(17, 40, 52, .04);
}

.if-restore-title {
    color: #193746;
    font-size: 18px;
    font-weight: 750;
    margin: 0 0 5px;
}

.if-restore-description {
    color: #748995;
    font-size: 12px;
    line-height: 1.6;
    margin-bottom: 8px;
}

/* ============================================
   RESPONSIVE
============================================ */

@media (max-width: 1000px) {
    .if-stat-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 600px) {
    .if-stat-grid {
        grid-template-columns: 1fr;
    }

    .if-archive-summary {
        padding: 17px;
    }

    .if-archive-empty {
        padding: 18px;
    }

    .st-key-archive_restore_panel {
        padding: 16px !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    .if-stat-card {
        transition: none;
    }

    .if-stat-card:hover {
        transform: none;
    }
}

</style>
"""


# =====================================================
# INVOICE DIRECTORY — STATISTICS
# =====================================================

def render_invoice_stats(invoices):

    paid_count = sum(
        str(row.get("Payment", "")).lower() == "paid"
        for row in invoices
    )

    partial_count = sum(
        str(row.get("Payment", "")).lower() == "partial"
        for row in invoices
    )

    unpaid_count = sum(
        str(row.get("Payment", "")).lower() == "unpaid"
        for row in invoices
    )

    items = [
        (
            "Active Invoices",
            len(invoices),
            "📄",
            "Total active invoice records",
        ),
        (
            "Fully Paid",
            paid_count,
            "✅",
            "Invoices with no remaining balance",
        ),
        (
            "Partially Paid",
            partial_count,
            "🕒",
            "Payments recorded, balance remaining",
        ),
        (
            "Unpaid",
            unpaid_count,
            "⚠️",
            "Invoices awaiting payment",
        ),
    ]

    blocks = []

    for index, (label, value, icon, description) in enumerate(items):

        primary = " if-stat-primary" if index == 0 else ""

        blocks.append(
            f'<div class="if-stat-card{primary}">'
            f'<div class="if-stat-header">'
            f'<span class="if-stat-label">{label}</span>'
            f'<span class="if-stat-icon" aria-hidden="true">{icon}</span>'
            '</div>'
            f'<div class="if-stat-value">{value}</div>'
            f'<div class="if-stat-description">{description}</div>'
            '</div>'
        )

    st.html(
        '<div class="if-stat-grid">'
        + "".join(blocks)
        + '</div>'
    )


# =====================================================
# TAB 1 — INVOICE DIRECTORY
# =====================================================

def render_invoice_directory():

    invoices = list_saved_invoices()

    st.subheader("Invoice Directory")

    st.caption(
        "Search and filter active invoices, "
        "then open one for details and actions."
    )

    render_invoice_stats(invoices)

    if not invoices:

        st.info(
            "No active invoices yet. "
            "Use the Create Invoice tab to add one."
        )

        return

    # -----------------------------------------
    # SEARCH AND FILTERS
    # -----------------------------------------

    st.markdown("#### Find Invoices")

    search_col, type_col, status_col, currency_col = st.columns(
        [2.4, 1, 1, 1]
    )

    with search_col:

        search_term = st.text_input(
            "Search number or contact",
            placeholder="e.g. INV-1001 or Alpha Services",
            key="directory_search",
        ).strip().casefold()

    types = sorted({
        str(row["Type"])
        for row in invoices
    })

    statuses = sorted({
        str(row["Payment"])
        for row in invoices
    })

    currencies = sorted({
        str(row["Currency"])
        for row in invoices
    })

    with type_col:

        type_filter = st.selectbox(
            "Invoice type",
            ["All"] + types,
            key="directory_type",
        )

    with status_col:

        status_filter = st.selectbox(
            "Payment status",
            ["All"] + statuses,
            key="directory_status",
        )

    with currency_col:

        currency_filter = st.selectbox(
            "Currency",
            ["All"] + currencies,
            key="directory_currency",
        )

    # -----------------------------------------
    # SORTING
    # -----------------------------------------

    sort_col, reset_col = st.columns([3, 1])

    with sort_col:

        sort_option = st.selectbox(
            "Sort invoices by",
            [
                "Newest issue date",
                "Oldest issue date",
                "Due date (earliest)",
                "Highest total",
                "Lowest total",
                "Invoice number (A–Z)",
            ],
            key="directory_sort",
        )

    with reset_col:

        st.button(
            "Reset filters",
            on_click=reset_invoice_filters,
            key="directory_reset",
            use_container_width=True,
        )

    # -----------------------------------------
    # FILTER INVOICES
    # -----------------------------------------

    filtered = []

    for row in invoices:

        query_text = (
            f"{row['Invoice']} {row['Contact']}"
        ).casefold()

        if search_term and search_term not in query_text:
            continue

        if type_filter != "All" and row["Type"] != type_filter:
            continue

        if status_filter != "All" and row["Payment"] != status_filter:
            continue

        if currency_filter != "All" and row["Currency"] != currency_filter:
            continue

        filtered.append(row)

    # -----------------------------------------
    # SORT INVOICES
    # -----------------------------------------

    if sort_option == "Newest issue date":

        filtered.sort(
            key=lambda row: str(row["Issued"]),
            reverse=True,
        )

    elif sort_option == "Oldest issue date":

        filtered.sort(
            key=lambda row: str(row["Issued"]),
        )

    elif sort_option == "Due date (earliest)":

        filtered.sort(
            key=lambda row: str(row["Due"]),
        )

    elif sort_option == "Highest total":

        filtered.sort(
            key=lambda row: as_decimal(row["Total"]),
            reverse=True,
        )

    elif sort_option == "Lowest total":

        filtered.sort(
            key=lambda row: as_decimal(row["Total"]),
        )

    else:

        filtered.sort(
            key=lambda row: str(row["Invoice"]).casefold(),
        )

    # -----------------------------------------
    # RESULTS
    # -----------------------------------------

    st.caption(
        f"Showing {len(filtered)} of "
        f"{len(invoices)} active invoices"
    )

    if not filtered:

        st.info(
            "No invoices match your filters. "
            "Change or reset the filters above."
        )

        return

    st.markdown("#### Invoice Records")

    st.caption(
        "Click an invoice row to open its "
        "details, payments and actions."
    )

    status_labels = {
        "paid": "🟢 Fully Paid",
        "partial": "🟠 Partially Paid",
        "unpaid": "🔴 Unpaid",
    }

    display_rows = []

    for row in filtered:

        payment_status = str(
            row.get("Payment") or ""
        ).strip().lower()

        display_rows.append({
            "Invoice": row["Invoice"],
            "Contact": row["Contact"],
            "Type": row["Type"],
            "Issued": row["Issued"],
            "Due": row["Due"],
            "Currency": row["Currency"],
            "Total": float(as_decimal(row["Total"])),
            "Payment Status": status_labels.get(
                payment_status,
                str(row.get("Payment", "")),
            ),
        })

    # Preserve correct selection when sorting or filtering.

    signature = "|".join(
        str(row["ID"])
        for row in filtered
    )

    signature_hash = hashlib.sha256(
        signature.encode("utf-8")
    ).hexdigest()[:16]

    table_event = st.dataframe(
        display_rows,
        hide_index=True,
        width="stretch",
        row_height=38,
        on_select="rerun",
        selection_mode="single-row",
        key=f"invoice_table_{signature_hash}",
        column_config={
            "Invoice": st.column_config.TextColumn(
                "Invoice Number",
                width="medium",
            ),
            "Contact": st.column_config.TextColumn(
                "Customer / Supplier",
                width="large",
            ),
            "Total": st.column_config.NumberColumn(
                "Total",
                format="%.2f",
            ),
            "Payment Status": st.column_config.TextColumn(
                "Payment Status",
                width="medium",
            ),
        },
    )

    selected_rows = table_event.selection.rows

    if selected_rows:

        selected_index = selected_rows[0]

        if 0 <= selected_index < len(filtered):

            render_invoice_details(
                selected_invoice_id=filtered[selected_index]["ID"]
            )

    else:

        st.info(
            "Select an invoice in the table "
            "above to view its details."
        )


# =====================================================
# TAB 2 — CREATE INVOICE
# =====================================================

def render_create_invoice():

    st.subheader("Create New Invoice")

    st.caption(
        "Purchase = invoice from a supplier. "
        "Sale = invoice issued to a customer."
    )

    invoice_type = st.selectbox(
        "Invoice Type",
        ["Purchase", "Sale"],
        key="create_invoice_type",
    )

    required_contact_type = (
        "Supplier"
        if invoice_type == "Purchase"
        else "Customer"
    )

    contacts = list_contacts()

    available_contacts = [
        contact
        for contact in contacts
        if contact["contact_type"] == required_contact_type
    ]

    if not available_contacts:

        st.warning(
            f"No active {required_contact_type.lower()}s found. "
            "Create one in Customers & Suppliers first."
        )

        st.page_link(
            "pages/contacts.py",
            label="Open Customers & Suppliers",
            icon=":material/groups:",
        )

        return

    contact_labels = {
        contact["id"]: contact["name"]
        for contact in available_contacts
    }

    with st.form(
        "create_invoice_form",
        clear_on_submit=True,
    ):

        contact_id = st.selectbox(
            required_contact_type,
            list(contact_labels),
            format_func=lambda value: contact_labels[value],
            key="create_invoice_contact",
        )

        invoice_number = st.text_input(
            "Invoice Number",
            placeholder="INV-1001",
            key="create_invoice_number",
        )

        issue_col, due_col = st.columns(2)

        with issue_col:

            invoice_date = st.date_input(
                "Invoice Date",
                value=date.today(),
                key="create_invoice_date",
            )

        with due_col:

            due_date = st.date_input(
                "Due Date",
                value=date.today() + timedelta(days=14),
                key="create_invoice_due_date",
            )

        currency = st.selectbox(
            "Currency",
            ["EUR", "USD", "ALL"],
            key="create_invoice_currency",
        )

        subtotal = st.text_input(
            "Subtotal",
            value="100.00",
            key="create_invoice_subtotal",
        )

        vat_rate = st.text_input(
            "VAT Rate (%)",
            value="20",
            key="create_invoice_vat",
        )

        submitted = st.form_submit_button(
            "Save Invoice",
            type="primary",
        )

    if submitted:

        try:

            new_id = create_saved_invoice(
                invoice_type=invoice_type,
                contact_id=contact_id,
                invoice_number=invoice_number,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=currency,
                subtotal=subtotal,
                vat_rate=vat_rate,
            )

        except ValueError as error:

            st.error(str(error))

        else:

            st.session_state["saved_invoice_notice"] = (
                f"Invoice #{new_id} saved successfully."
            )

            st.rerun()


# =====================================================
# TAB 3 — ARCHIVED INVOICES
# =====================================================

def render_archived_invoices():

    st.subheader("Archived Invoices")

    st.caption(
        "Archived records can be restored "
        "without losing their history."
    )

    archived = list_archived_invoices()

    # -----------------------------------------
    # EMPTY ARCHIVE
    # -----------------------------------------

    if not archived:

        st.html("""
        <div class="if-archive-empty">

            <div class="if-archive-empty-icon"
                 aria-hidden="true">
                ▤
            </div>

            <div>
                <div class="if-archive-empty-title">
                    Your archive is empty
                </div>

                <div class="if-archive-empty-text">
                    No invoices have been archived yet.
                    Archived invoices will appear here,
                    ready to be restored when needed.
                </div>
            </div>

        </div>
        """)

        return

    # -----------------------------------------
    # ARCHIVE SUMMARY CARD
    # -----------------------------------------

    count = len(archived)

    st.html(f"""
    <section class="if-archive-summary"
             aria-label="Archive summary">

        <div>
            <div class="if-archive-summary-title">
                Archived Invoice Records
            </div>

            <div class="if-archive-summary-text">
                Invoices stored in the archive
                and available for restoration.
            </div>
        </div>

        <div class="if-archive-counter"
             aria-label="{count} archived invoices">
            {count}
        </div>

    </section>
    """)

    # -----------------------------------------
    # ARCHIVED INVOICE TABLE
    # -----------------------------------------

    st.dataframe(
        archived,
        hide_index=True,
        width="stretch",
        row_height=39,
    )

    st.caption(
        "Archived invoices keep their "
        "recorded payment history."
    )

    archived_labels = {
        row["ID"]: f"{row['Invoice']} — {row['Contact']}"
        for row in archived
    }

    # -----------------------------------------
    # PREMIUM RESTORE PANEL
    # -----------------------------------------

    with st.container(
        border=True,
        key="archive_restore_panel",
    ):

        st.html("""
        <div class="if-restore-title">
            Restore an Invoice
        </div>

        <div class="if-restore-description">
            Choose an archived invoice to move it back
            to the active directory. Its information
            and payment history are preserved.
        </div>
        """)

        restore_id = st.selectbox(
            "Select Invoice to Restore",
            list(archived_labels),
            format_func=lambda value: archived_labels[value],
            key="restore_invoice_id",
        )

        if st.button(
            "Restore Invoice",
            type="primary",
            key="restore_invoice_btn",
        ):

            try:

                restore_saved_invoice(restore_id)

            except ValueError as error:

                st.error(str(error))

            else:

                st.session_state["saved_invoice_notice"] = (
                    "Invoice restored successfully."
                )

                st.rerun()


# =====================================================
# INITIALIZE PAGE
# =====================================================

initialize_invoice_store()
apply_hover_effects()
st.html(PAGE_CSS)

# =====================================================
# PREMIUM INVOICE DETAILS — FINAL UI POLISH
# =====================================================

st.html("""
<style>

/* Main invoice summary container */

div[class*="st-key-if_invoice_summary"] {
    background: linear-gradient(
        125deg,
        #ffffff 0%,
        #f7fcfa 100%
    ) !important;

    border: 1px solid #dbe8e2 !important;
    border-radius: 19px !important;

    padding: 25px 27px !important;
    margin: 20px 0 24px !important;

    box-shadow:
        0 7px 25px rgba(20, 60, 65, 0.045) !important;
}

/* Invoice number */

div[class*="st-key-if_invoice_summary"] h3 {
    color: #193746 !important;
    font-size: 25px !important;
    font-weight: 780 !important;
    letter-spacing: -0.4px !important;
}

/* Invoice subtitle */

div[class*="st-key-if_invoice_summary"]
[data-testid="stCaptionContainer"] {
    color: #738995 !important;
}

/* Premium individual financial cards */

div[class*="st-key-if_invoice_summary"]
[data-testid="stMetric"] {

    background: #ffffff !important;

    border: 1px solid #dce9e5 !important;
    border-radius: 14px !important;

    padding: 19px 21px !important;

    box-shadow:
        0 4px 15px rgba(20, 55, 60, 0.035) !important;
}

/* Metric labels */

div[class*="st-key-if_invoice_summary"]
[data-testid="stMetricLabel"] p {

    color: #6c8290 !important;
    font-size: 12px !important;
    font-weight: 650 !important;
}

/* Metric values */

div[class*="st-key-if_invoice_summary"]
[data-testid="stMetricValue"] {

    color: #193746 !important;
    font-weight: 750 !important;
}

/* Status box */

div[class*="st-key-if_invoice_summary"]
[data-testid="stAlert"] {

    border-radius: 11px !important;
    box-shadow: none !important;
}

/* The divider between header and financial cards */

div[class*="st-key-if_invoice_summary"] hr {

    border-color: #e0eae6 !important;
    margin: 21px 0 !important;
}

/* =========================================
   INVOICE INFORMATION
========================================= */

div[class*="st-key-if_motion_overview_"] {

    background: #ffffff !important;
    border: 1px solid #dce8e5 !important;

    border-radius: 17px !important;
    padding: 20px 23px !important;

    box-shadow:
        0 5px 18px rgba(18, 55, 60, 0.035) !important;
}

/* Invoice Information title */

div[class*="st-key-if_motion_overview_"] h4 {

    color: #193746 !important;
    font-size: 19px !important;
    font-weight: 750 !important;
}

/* Invoice information table */

div[class*="st-key-if_motion_overview_"]
[data-testid="stDataFrame"] {

    border: 1px solid #e0eae7 !important;
    border-radius: 12px !important;

    overflow: hidden !important;
}

/* Small screens */

@media (max-width: 700px) {

    div[class*="st-key-if_invoice_summary"] {
        padding: 17px !important;
    }

    div[class*="st-key-if_motion_overview_"] {
        padding: 15px !important;
    }
}

</style>
""")


st.html("""
<div class="if-hero">

    <div class="if-hero-title">
        Saved Invoices
    </div>

    <div class="if-hero-description">
        Find, review and manage your business
        invoices in one place.
    </div>

</div>
""")

# Show success messages after changes.

for notice_key in (
    "saved_invoice_notice",
    "invoice_details_notice",
):

    notice = st.session_state.pop(notice_key, None)

    if notice:
        st.success(notice)


# =====================================================
# PAGE NAVIGATION
# =====================================================

directory_tab, create_tab, archive_tab = st.tabs(
    [
        "Invoice Directory",
        "Create Invoice",
        "Archived Invoices",
    ]
)

with directory_tab:
    render_invoice_directory()

with create_tab:
    render_create_invoice()

with archive_tab:
    render_archived_invoices()
