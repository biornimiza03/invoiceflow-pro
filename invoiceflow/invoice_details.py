
"""InvoiceFlow Pro — invoice details and management UI."""

import sqlite3
from datetime import date
from decimal import Decimal
from html import escape

import pandas as pd
import streamlit as st

from invoiceflow.database import DB_PATH
from invoiceflow.invoice_store import archive_saved_invoice, update_saved_invoice
from invoiceflow.payments import PAYMENT_METHODS, register_payment
from invoiceflow.ui_polish import apply_ui_polish


# -----------------------------------------------------
# DATA & FORMATTING
# -----------------------------------------------------

def format_money(cents, currency):
    amount = Decimal(str(cents or 0)) / Decimal("100")
    return f"{amount:,.2f} {currency}"


def load_invoice_details_data():
    if not DB_PATH.exists():
        return [], {}, []

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "invoices" not in tables:
            return [], {}, []

        invoices = [
            dict(row) for row in conn.execute(
                "SELECT * FROM invoices ORDER BY id DESC"
            )
        ]
        contacts = (
            {
                row["id"]: row["name"]
                for row in conn.execute("SELECT id, name FROM contacts")
            }
            if "contacts" in tables else {}
        )
        payments = (
            [dict(row) for row in conn.execute(
                "SELECT * FROM payments ORDER BY id DESC"
            )]
            if "payments" in tables else []
        )
    return invoices, contacts, payments


def show_styles():
    """Shared styles for the three redesigned sections."""
    st.html("""
    <style>
    .if-section-intro {
        display: flex;
        align-items: center;
        gap: 13px;
        margin: 8px 0 19px;
    }

    .if-section-icon {
        width: 45px;
        height: 45px;
        border-radius: 13px;
        background: #e7f5ef;
        color: #087b61;
        display: grid;
        place-items: center;
        font-size: 23px;
        flex-shrink: 0;
    }

    .if-section-title {
        font-size: 21px;
        font-weight: 750;
        color: #183444;
        line-height: 1.3;
    }

    .if-section-description {
        font-size: 13px;
        color: #728696;
        margin-top: 5px;
    }

    .if-cards {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 13px;
        margin: 14px 0 20px;
    }

    .if-card {
        background: #fff;
        border: 1px solid #dce7ea;
        border-radius: 15px;
        padding: 21px;
        min-width: 0;
        box-shadow: 0 3px 15px rgba(20, 53, 65, .035);
    }

    .if-card--green {
        background: linear-gradient(125deg, #164d43, #0b8469);
        border-color: #0b8469;
    }

    .if-card-label {
        font-size: 12px;
        color: #718494;
        margin-bottom: 10px;
    }

    .if-card-value {
        font-size: 25px;
        font-weight: 750;
        color: #183444;
        overflow-wrap: anywhere;
    }

    .if-card-foot {
        font-size: 11px;
        color: #8c9da7;
        margin-top: 9px;
    }

    .if-card--green .if-card-label,
    .if-card--green .if-card-foot {
        color: #c6f0e1;
    }

    .if-card--green .if-card-value {
        color: white;
    }

    .if-progress-panel {
        border: 1px solid #dce7ea;
        border-radius: 14px;
        background: #fff;
        padding: 17px 20px;
        margin: 7px 0 22px;
    }

    .if-progress-top {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        color: #718494;
        font-size: 12px;
        margin-bottom: 10px;
    }

    .if-progress-top strong {
        color: #0f8668;
    }

    .if-progress-track {
        background: #eaf1f1;
        border-radius: 20px;
        height: 9px;
        overflow: hidden;
    }

    .if-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #28bc91, #0b7b63);
        border-radius: 20px;
        transition: width .3s ease;
    }

    .if-panel {
        border: 1px solid #dce7ea;
        background: linear-gradient(130deg, #f9fbfc, #fff);
        border-radius: 16px;
        padding: 23px;
        margin: 12px 0 17px;
    }

    .if-panel-top {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 15px;
        flex-wrap: wrap;
    }

    .if-panel-title {
        font-size: 20px;
        font-weight: 750;
        color: #183444;
    }

    .if-panel-subtitle {
        font-size: 13px;
        color: #718494;
        margin-top: 5px;
    }

    .if-status-pill {
        display: inline-flex;
        background: #e7f7ef;
        border: 1px solid #bce5ce;
        color: #08714e;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 650;
    }

    .if-status-pill--warning {
        background: #fff5dd;
        border-color: #efd59e;
        color: #97640c;
    }

    .if-panel-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 15px;
        border-top: 1px solid #e3eaed;
        padding-top: 16px;
        margin-top: 20px;
    }

    .if-panel-grid-label {
        color: #738694;
        font-size: 12px;
        margin-bottom: 7px;
    }

    .if-panel-grid-value {
        font-weight: 750;
        font-size: 21px;
        color: #183444;
        overflow-wrap: anywhere;
    }

    .if-note {
        border: 1px solid #ccebdc;
        background: #f0faf5;
        border-radius: 12px;
        padding: 15px 18px;
        color: #326754;
        font-size: 13px;
        margin: 15px 0;
        line-height: 1.6;
    }

    .if-warning {
        border: 1px solid #f1dca6;
        background: #fff9eb;
        border-radius: 12px;
        padding: 15px 18px;
        color: #885b12;
        font-size: 13px;
        margin: 15px 0;
        line-height: 1.6;
    }

    .if-empty {
        border: 1px dashed #cbd9df;
        background: #f8fafb;
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        color: #6d8190;
        font-size: 13px;
    }

    .if-empty strong {
        display: block;
        color: #193544;
        font-size: 17px;
        margin-bottom: 8px;
    }

    @media (max-width: 760px) {
        .if-cards {
            grid-template-columns: 1fr 1fr;
        }

        .if-card--green {
            grid-column: 1 / -1;
        }

        .if-panel-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 490px) {
        .if-cards {
            grid-template-columns: 1fr;
        }

        .if-card--green {
            grid-column: auto;
        }

        .if-card-value {
            font-size: 22px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .if-progress-bar {
            transition: none;
        }
    }

/* PREMIUM CSV PREVIEW EXPANDER */

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] {
    border: 1px solid #dce8e5 !important;
    border-radius: 13px !important;
    background: #ffffff !important;
    box-shadow: 0 4px 16px rgba(20, 55, 60, 0.04);
    overflow: hidden;
    margin-top: 12px;
}

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] details {
    border: none !important;
    border-radius: 13px !important;
}

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] summary {
    padding: 13px 17px !important;
    background: #ffffff !important;
    transition: background 0.2s ease;
}

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] summary:hover {
    background: #f3f9f6 !important;
}

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] summary p {
    color: #244b4a !important;
    font-size: 13px !important;
    font-weight: 650 !important;
}

div[class*="st-key-if_motion_export_"]
[data-testid="stExpander"] details[open] summary {
    border-bottom: 1px solid #e6eeee;
}

@media (prefers-reduced-motion: reduce) {
    div[class*="st-key-if_motion_export_"]
    [data-testid="stExpander"] summary {
        transition: none !important;
    }
}

    </style>
    """)


def section_heading(icon, heading, description):
    st.html(f"""
    <div class="if-section-intro">
      <span class="if-section-icon" aria-hidden="true">{escape(icon)}</span>
      <div>
        <div class="if-section-title">{escape(heading)}</div>
        <div class="if-section-description">{escape(description)}</div>
      </div>
    </div>
    """)


def info_cards(cards):
    """cards: list of (label, value, short explanation)."""
    content = []

    for index, (label, value, foot) in enumerate(cards):
        variant = " if-card--green" if index == 0 else ""

        content.append(f"""
        <div class="if-card{variant}">
          <div class="if-card-label">{escape(str(label))}</div>
          <div class="if-card-value">{escape(str(value))}</div>
          <div class="if-card-foot">{escape(str(foot))}</div>
        </div>
        """)

    st.html('<div class="if-cards">' + "".join(content) + '</div>')


def open_payment_history(invoice_id):
    st.session_state[f"invoice_section_{invoice_id}"] = "Payment History"


def open_register_payment(invoice_id):
    st.session_state[f"invoice_section_{invoice_id}"] = "Manage Invoice"
    st.session_state[f"invoice_action_{invoice_id}"] = "Register Payment"


# -----------------------------------------------------
# OVERVIEW
# -----------------------------------------------------

def render_overview(invoice, invoice_number, contact_name, currency):
    st.markdown("#### Invoice Information")

    vat = Decimal(str(invoice.get("vat_rate_bps") or 0)) / Decimal("100")

    values = [
        ("Invoice Number", invoice_number),
        ("Invoice Type", invoice.get("invoice_type", "")),
        ("Contact", contact_name),
        ("Invoice Date", invoice.get("invoice_date", "")),
        ("Due Date", invoice.get("due_date", "")),
        ("Currency", currency),
        ("Subtotal", format_money(invoice.get("subtotal_cents"), currency)),
        ("VAT Rate", f"{vat:.2f}%"),
        ("Invoice Total", format_money(invoice.get("total_cents"), currency)),
    ]

    st.dataframe(
        pd.DataFrame([{"Field": key, "Value": val} for key, val in values]),
        hide_index=True,
        width="stretch",
    )


# -----------------------------------------------------
# PAYMENT HISTORY — REDESIGN
# -----------------------------------------------------

def render_payment_history(payments, currency, invoice_total, selected_id):
    section_heading(
        "↗",
        "Payment History",
        "Review transactions and the payment progress of this invoice.",
    )

    paid = sum(int(row.get("amount_cents") or 0) for row in payments)
    remaining = max(0, invoice_total - paid)

    percent = (
        min(100, max(0, round(paid * 100 / invoice_total)))
        if invoice_total > 0 else 100
    )

    info_cards([
        (
            "Total recorded",
            format_money(paid, currency),
            "All recorded payments",
        ),
        (
            "Transactions",
            len(payments),
            "Individual payment records",
        ),
        (
            "Remaining balance",
            format_money(remaining, currency),
            "Outstanding amount",
        ),
    ])

    st.html(f"""
    <div class="if-progress-panel">
      <div class="if-progress-top">
        <span>Payment progress</span>
        <strong>{percent}% completed</strong>
      </div>

      <div class="if-progress-track"
           role="progressbar"
           aria-label="Payment progress"
           aria-valuemin="0"
           aria-valuemax="100"
           aria-valuenow="{percent}">
        <div class="if-progress-bar"
             style="width:{percent}%"></div>
      </div>
    </div>
    """)

    if not payments:
        st.html("""
        <div class="if-empty">
          <strong>No payments recorded</strong>
          The payment history will appear here once
          a transaction is saved.
        </div>
        """)

    else:
        st.markdown("##### Recorded Transactions")

        rows = [
            {
                "ID": row.get("id"),
                "Date": str(row.get("payment_date") or ""),
                "Method": str(row.get("method") or "—"),
                "Amount": float(
                    Decimal(str(row.get("amount_cents") or 0))
                    / Decimal("100")
                ),
                "Note": str(row.get("note") or "—"),
            }
            for row in payments
        ]

        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            width="stretch",
            row_height=40,
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    width="small",
                ),
                "Amount": st.column_config.NumberColumn(
                    f"Amount ({currency})",
                    format="%.2f",
                ),
                "Note": st.column_config.TextColumn(
                    "Reference / Note",
                    width="large",
                ),
            },
        )

    if paid > invoice_total:
        st.warning(
            "Recorded payments exceed the invoice total. "
            "Review this record."
        )

    elif remaining == 0:
        st.html("""
        <div class="if-note">
          <strong>✓ Invoice fully paid.</strong>
          There is no outstanding balance.
        </div>
        """)

    else:
        st.button(
            (
                "Register Payment"
                if not payments
                else "Record Another Payment"
            ),
            icon=":material/add_card:",
            key=f"history_register_{selected_id}",
            on_click=open_register_payment,
            args=(selected_id,),
        )


# -----------------------------------------------------
# EXPORT CSV — REDESIGN
# -----------------------------------------------------

def render_statement(
    invoice,
    selected_id,
    invoice_number,
    invoice_total,
    paid_amount,
    remaining,
    invoice_payments,
    currency,
):
    section_heading(
        "↓",
        "Invoice Statement Export",
        "Preview and download the financial statement in CSV format.",
    )

    # Keep the same CSV columns and summary structure as before.

    rows = [
        {
            "Record": "Invoice Total",
            "Date": invoice.get("invoice_date", ""),
            "Description": invoice_number,
            "Amount": f"{Decimal(invoice_total) / Decimal(100):.2f}",
            "Currency": currency,
        },
        {
            "Record": "Total Paid",
            "Date": "",
            "Description": "Recorded payments",
            "Amount": f"{Decimal(paid_amount) / Decimal(100):.2f}",
            "Currency": currency,
        },
        {
            "Record": "Remaining Balance",
            "Date": invoice.get("due_date", ""),
            "Description": "Outstanding balance",
            "Amount": f"{Decimal(remaining) / Decimal(100):.2f}",
            "Currency": currency,
        },
    ]

    for payment in invoice_payments:
        amount = int(payment.get("amount_cents") or 0)

        rows.append({
            "Record": "Payment",
            "Date": payment.get("payment_date", ""),
            "Description": (
                f"{payment.get('method', '')} - "
                f"{payment.get('note', '')}"
            ),
            "Amount": f"{Decimal(amount) / Decimal(100):.2f}",
            "Currency": currency,
        })

    frame = pd.DataFrame(rows)
    csv = frame.to_csv(index=False).encode("utf-8-sig")

    info_cards([
        (
            "Rows in export",
            len(frame),
            "3 summary rows + payments",
        ),
        (
            "Payment records",
            len(invoice_payments),
            "Transactions included",
        ),
        (
            "Remaining balance",
            format_money(remaining, currency),
            "Current balance",
        ),
    ])

    with st.container(border=True):
        st.markdown("##### Your Statement Is Ready")

        st.caption(
            f"Invoice {invoice_number} · "
            f"{len(frame)} rows · CSV / Excel-compatible"
        )

        st.download_button(
            "Download Invoice Statement (CSV)",
            data=csv,
            file_name=f"invoice_{selected_id}_statement.csv",
            mime="text/csv",
            key=f"statement_download_{selected_id}",
            type="primary",
            use_container_width=True,
        )

        st.caption(
            "Contains the invoice summary "
            "and each recorded payment."
        )

    with st.expander(f"Preview CSV — {len(frame)} rows"):
        st.dataframe(
            frame,
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "The first three rows summarize the invoice. "
            "Payment rows are details; do not add all rows "
            "together as one total."
        )


# -----------------------------------------------------
# EDIT INVOICE — KEEP EXISTING LOGIC
# -----------------------------------------------------

def render_edit_invoice(
    invoice,
    selected_id,
    invoice_number,
    currency,
    paid_amount,
):
    st.markdown("##### Edit Invoice")
    st.caption(f"Editing {invoice_number}")

    with st.form(key=f"quick_edit_invoice_{selected_id}"):

        edited_number = st.text_input(
            "Invoice Number",
            value=invoice_number,
        )

        col_date, col_due = st.columns(2)

        with col_date:
            edited_date = st.date_input(
                "Invoice Date",
                value=date.fromisoformat(
                    str(invoice["invoice_date"])
                ),
            )

        with col_due:
            edited_due = st.date_input(
                "Due Date",
                value=date.fromisoformat(
                    str(invoice["due_date"])
                ),
            )

        allowed_currencies = list(
            dict.fromkeys([currency, "EUR", "USD", "ALL"])
        )

        edited_currency = st.selectbox(
            "Currency",
            options=allowed_currencies,
            index=allowed_currencies.index(currency),
            disabled=paid_amount > 0,
            help=(
                "Currency cannot be changed after "
                "a payment has been recorded."
            ),
        )

        edited_subtotal = st.number_input(
            "Subtotal",
            min_value=0.0,
            value=float(
                Decimal(str(invoice["subtotal_cents"]))
                / Decimal("100")
            ),
            step=0.01,
            format="%.2f",
        )

        edited_vat = st.number_input(
            "VAT Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(
                Decimal(str(invoice["vat_rate_bps"]))
                / Decimal("100")
            ),
            step=0.5,
            format="%.2f",
        )

        estimated_total = Decimal(
            f"{edited_subtotal:.2f}"
        ) * (
            Decimal("1")
            + Decimal(f"{edited_vat:.2f}") / Decimal("100")
        )

        st.caption(
            f"Estimated Total: "
            f"{estimated_total:,.2f} {edited_currency}"
        )

        submitted = st.form_submit_button(
            "Save Changes",
            type="primary",
        )

    if not submitted:
        return

    if not edited_number.strip():
        st.error("Invoice number cannot be empty.")

    elif edited_due < edited_date:
        st.error(
            "Due date cannot be earlier than invoice date."
        )

    elif paid_amount > 0 and edited_currency != currency:
        st.error(
            "Currency cannot be changed after payments exist."
        )

    else:
        try:
            update_saved_invoice(
                invoice_id=selected_id,
                invoice_number=edited_number.strip(),
                invoice_date=edited_date.isoformat(),
                due_date=edited_due.isoformat(),
                currency=edited_currency,
                subtotal=f"{edited_subtotal:.2f}",
                vat_rate=f"{edited_vat:.2f}",
            )

        except (ValueError, sqlite3.Error) as error:
            st.error(str(error))

        else:
            st.session_state[
                "invoice_details_notice"
            ] = "Invoice updated successfully."

            st.rerun()


# -----------------------------------------------------
# REGISTER PAYMENT — KEEP EXISTING LOGIC
# -----------------------------------------------------

def render_register_payment(
    selected_id,
    invoice_number,
    invoice_date,
    remaining,
    currency,
):

    if remaining <= 0:
        st.html(f"""
        <section class="if-panel" aria-label="Fully paid invoice">

          <div class="if-panel-top">
            <div>
              <div class="if-panel-title">
                ✓ Invoice Fully Paid
              </div>
              <div class="if-panel-subtitle">
                All required payments are completed.
              </div>
            </div>

            <span class="if-status-pill">Settled</span>
          </div>

          <div class="if-panel-grid">
            <div>
              <div class="if-panel-grid-label">
                Invoice number
              </div>
              <div class="if-panel-grid-value">
                {escape(str(invoice_number))}
              </div>
            </div>

            <div>
              <div class="if-panel-grid-label">
                Outstanding balance
              </div>
              <div class="if-panel-grid-value">
                {escape(format_money(0, currency))}
              </div>
            </div>
          </div>

        </section>
        """)

        st.button(
            "View Payment History",
            icon=":material/history:",
            key=f"paid_history_{selected_id}",
            on_click=open_payment_history,
            args=(selected_id,),
        )

        return

    st.markdown("##### Register New Payment")
    st.caption("Record a payment directly against this invoice.")

    with st.container(border=True):
        left, right = st.columns(2)

        with left:
            st.caption("Selected Invoice")
            st.markdown(f"**{invoice_number}**")

        with right:
            st.caption("Outstanding Balance")
            st.markdown(
                f"**{format_money(remaining, currency)}**"
            )

    with st.form(
        key=f"inline_payment_form_{selected_id}",
        clear_on_submit=True,
    ):
        payment_amount = st.text_input(
            f"Payment Amount ({currency})",
            placeholder="e.g. 30.00",
            help=(
                "The amount must be greater than zero "
                "and cannot exceed the balance."
            ),
        )

        date_col, method_col = st.columns(2)

        with date_col:
            issue_date = date.fromisoformat(
                str(invoice_date)
            )

            payment_date = st.date_input(
                "Payment Date",
                value=max(date.today(), issue_date),
                min_value=issue_date,
            )

        with method_col:
            payment_method = st.selectbox(
                "Payment Method",
                options=PAYMENT_METHODS,
            )

        payment_note = st.text_area(
            "Payment Note (optional)",
            placeholder="Reference or description...",
            max_chars=300,
            height=90,
        )

        submitted = st.form_submit_button(
            "Register Payment",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not payment_amount.strip():
            st.error("Please enter a payment amount.")

        else:
            try:
                register_payment(
                    invoice_id=selected_id,
                    amount=payment_amount.strip(),
                    payment_date=payment_date.isoformat(),
                    method=payment_method,
                    note=payment_note.strip(),
                )

            except (ValueError, sqlite3.Error) as error:
                st.error(str(error))

            else:
                st.session_state[
                    "invoice_details_notice"
                ] = "Payment registered successfully."

                st.rerun()

    st.button(
        "View Existing Payments",
        icon=":material/history:",
        type="tertiary",
        key=f"pending_history_{selected_id}",
        on_click=open_payment_history,
        args=(selected_id,),
    )


# -----------------------------------------------------
# ARCHIVE INVOICE — REDESIGN
# -----------------------------------------------------

def render_archive_invoice(
    selected_id,
    remaining,
    currency,
    invoice_number,
    contact_name,
    invoice_total,
):
    section_heading(
        "▣",
        "Archive Invoice",
        "Remove an invoice from active views while keeping its history.",
    )

    settled = remaining == 0
    badge_class = (
        ""
        if settled
        else " if-status-pill--warning"
    )

    badge_text = (
        "Fully settled"
        if settled
        else "Outstanding balance"
    )

    st.html(f"""
    <section class="if-panel" aria-label="Archive invoice summary">
      <div class="if-panel-top">
        <div>
          <div class="if-panel-title">
            {escape(str(invoice_number))}
          </div>
          <div class="if-panel-subtitle">
            {escape(str(contact_name))}
          </div>
        </div>

        <span class="if-status-pill{badge_class}">
          {badge_text}
        </span>
      </div>

      <div class="if-panel-grid">
        <div>
          <div class="if-panel-grid-label">
            Invoice total
          </div>
          <div class="if-panel-grid-value">
            {escape(format_money(invoice_total, currency))}
          </div>
        </div>

        <div>
          <div class="if-panel-grid-label">
            Outstanding balance
          </div>
          <div class="if-panel-grid-value">
            {escape(format_money(remaining, currency))}
          </div>
        </div>
      </div>
    </section>
    """)

    if remaining > 0:
        st.html(f"""
        <div class="if-warning">
          <strong>Payment still due.</strong>
          Archiving this invoice will hide an outstanding
          balance of {escape(format_money(remaining, currency))}
          from active reports.
        </div>
        """)

    else:
        st.html("""
        <div class="if-note">
          <strong>✓ No outstanding balance.</strong>
          This invoice is fully paid.
        </div>
        """)

    with st.container(border=True):
        st.markdown("##### Confirm Archiving")

        st.caption(
            "The invoice and payment history remain in the database. "
            "You can restore it from Archived Invoices."
        )

        confirmed = st.checkbox(
            "I understand this invoice will move "
            "to Archived Invoices.",
            key=f"confirm_archive_{selected_id}",
        )

        if st.button(
            "Archive Invoice",
            type="primary",
            disabled=not confirmed,
            key=f"quick_archive_{selected_id}",
        ):
            try:
                archive_saved_invoice(selected_id)

            except (ValueError, sqlite3.Error) as error:
                st.error(str(error))

            else:
                st.session_state[
                    "invoice_details_notice"
                ] = "Invoice archived successfully."

                st.rerun()


# -----------------------------------------------------
# INVOICE DETAILS — MAIN VIEW
# -----------------------------------------------------

@st.fragment
def render_invoice_details(selected_invoice_id=None):

    st.subheader("Invoice Details")

    apply_ui_polish()
    show_styles()

    try:
        invoices, contacts, payments = (
            load_invoice_details_data()
        )

    except sqlite3.Error as error:
        st.error(
            f"Unable to read invoice data: {error}"
        )
        return

    active = [
        row for row in invoices
        if row.get("is_active", 1) == 1
    ]

    if not active:
        st.info("No active saved invoices available.")
        return

    labels = {
        row["id"]: (
            f"{row.get('invoice_number', 'Invoice')} — "
            f"{contacts.get(row.get('contact_id'), 'Unknown contact')}"
        )
        for row in active
    }

    if selected_invoice_id is None:
        selected_id = st.selectbox(
            "Select Invoice",
            options=list(labels),
            format_func=lambda row_id: labels[row_id],
            key="invoice_details_selected_id",
        )

    else:
        if selected_invoice_id not in labels:
            st.warning(
                "This invoice is no longer active or available."
            )
            return

        selected_id = selected_invoice_id

    invoice = next(
        row for row in active
        if row["id"] == selected_id
    )

    currency = invoice.get("currency", "EUR")
    invoice_number = invoice.get("invoice_number", "Unknown")

    contact_name = contacts.get(
        invoice.get("contact_id"),
        "Unknown contact",
    )

    invoice_total = int(invoice.get("total_cents") or 0)

    invoice_payments = [
        row for row in payments
        if row.get("invoice_id") == selected_id
    ]

    paid_amount = sum(
        int(row.get("amount_cents") or 0)
        for row in invoice_payments
    )

    remaining = max(0, invoice_total - paid_amount)

    status = (
        "Fully Paid"
        if remaining == 0
        else "Partially Paid"
        if paid_amount > 0
        else "Unpaid"
    )

    # Invoice summary

    with st.container(key="if_invoice_summary"):
        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"### {invoice_number}")

            st.caption(
                f"{contact_name} · "
                f"{invoice.get('invoice_type', 'Invoice')}"
            )

        with right:
            st.caption("Payment Status")

            if status == "Fully Paid":
                st.success(status)

            elif status == "Partially Paid":
                st.warning(status)

            else:
                st.info(status)

        st.divider()

        col_total, col_paid, col_remaining = (
            st.columns(3)
        )

        with col_total:
            st.metric(
                "Invoice Total",
                format_money(invoice_total, currency),
            )

        with col_paid:
            st.metric(
                "Already Paid",
                format_money(paid_amount, currency),
            )

        with col_remaining:
            st.metric(
                "Remaining Balance",
                format_money(remaining, currency),
            )

        if paid_amount > invoice_total:
            st.error(
                "Recorded payments exceed the invoice total. "
                "Please review it."
            )

    # Main navigation

    section = st.segmented_control(
        "Invoice Section",
        options=[
            "Overview",
            "Payment History",
            "Manage Invoice",
        ],
        default="Overview",
        selection_mode="single",
        key=f"invoice_section_{selected_id}",
    ) or "Overview"

    if section == "Overview":

        with st.container(
            key=f"if_motion_overview_{selected_id}"
        ):
            render_overview(
                invoice,
                invoice_number,
                contact_name,
                currency,
            )

    elif section == "Payment History":

        with st.container(
            key=f"if_motion_history_{selected_id}"
        ):
            render_payment_history(
                invoice_payments,
                currency,
                invoice_total,
                selected_id,
            )

    elif section == "Manage Invoice":

        st.markdown("#### Invoice Management")
        st.caption("Choose an action for the selected invoice.")

        action = st.segmented_control(
            "Choose Action",
            options=[
                "Edit Invoice",
                "Register Payment",
                "Archive Invoice",
                "Export CSV",
            ],
            default="Edit Invoice",
            selection_mode="single",
            key=f"invoice_action_{selected_id}",
        ) or "Edit Invoice"

        st.divider()

        if action == "Edit Invoice":

            with st.container(
                key=f"if_motion_edit_{selected_id}"
            ):
                render_edit_invoice(
                    invoice,
                    selected_id,
                    invoice_number,
                    currency,
                    paid_amount,
                )

        elif action == "Register Payment":

            with st.container(
                key=f"if_motion_payment_{selected_id}"
            ):
                render_register_payment(
                    selected_id,
                    invoice_number,
                    invoice["invoice_date"],
                    remaining,
                    currency,
                )

        elif action == "Archive Invoice":

            with st.container(
                key=f"if_motion_archive_{selected_id}"
            ):
                render_archive_invoice(
                    selected_id,
                    remaining,
                    currency,
                    invoice_number,
                    contact_name,
                    invoice_total,
                )

        elif action == "Export CSV":

            with st.container(
                key=f"if_motion_export_{selected_id}"
            ):
                render_statement(
                    invoice,
                    selected_id,
                    invoice_number,
                    invoice_total,
                    paid_amount,
                    remaining,
                    invoice_payments,
                    currency,
                )
