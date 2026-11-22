
"""InvoiceFlow Pro — Premium Payments Workspace.

UI improvements only: payment validation and storage remain in
invoiceflow.payments. Monetary values are never summed across currencies.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from html import escape

import pandas as pd
import streamlit as st

from invoiceflow.financial_insights import get_financial_insights
from invoiceflow.financial_visuals import render_financial_intelligence
from invoiceflow.hover_effects import apply_hover_effects
from invoiceflow.payment_status import summarize_invoice_balances
from invoiceflow.payments import (
    PAYMENT_METHODS,
    initialize_payment_store,
    list_invoice_balances,
    list_payment_history,
    register_payment,
)


# ============================================================
# ONE CONSOLIDATED CSS BLOCK — NO EXTRA CSS TO ADD
# ============================================================

PAYMENTS_CSS = """
<style>
/* Hero header */
.if-pay-hero {
    padding: 31px 34px;
    margin: 2px 0 22px;
    border-radius: 20px;
    background: linear-gradient(115deg, #152f3e, #125448 61%, #098468);
    border: 1px solid rgba(255,255,255,.1);
    box-shadow: 0 12px 30px rgba(13,60,59,.09);
}
.if-pay-eyebrow { color:#b7eee0; font-size:10px; font-weight:750; letter-spacing:1.6px; }
.if-pay-hero h1 { color:#fff; font-size:clamp(25px,3vw,33px); margin:8px 0; letter-spacing:-.6px; }
.if-pay-hero p { color:#d5eae8; font-size:13px; line-height:1.7; margin:0; }

/* Section headings */
.if-pay-section { margin:22px 0 16px; }
.if-pay-section h3 { color:#1d3b49; font-size:19px; font-weight:760; margin:0 0 7px; }
.if-pay-section p { color:#718694; font-size:12px; line-height:1.6; margin:0; }

/* KPI cards — one, two, three or four columns */
.if-pay-kpis {
    display:grid;
    grid-template-columns:repeat(var(--if-kpi-columns,4),minmax(0,1fr));
    gap:13px;
    margin:17px 0 25px;
}
.if-pay-kpi {
    min-width:0;
    padding:19px 20px;
    background:#fff;
    border:1px solid #dfe9e9;
    border-radius:16px;
    box-shadow:0 5px 18px rgba(18,55,60,.04);
    transition:border-color .2s ease,box-shadow .2s ease;
}
.if-pay-kpi:hover { border-color:#cee3d9; box-shadow:0 7px 20px rgba(18,55,60,.065); }
.if-pay-kpi.primary {
    background:linear-gradient(125deg,#155047,#09846a);
    border-color:transparent;
}
.if-pay-kpi.highlight-soft { background:#f3faf7; border-color:#c3e2d2; }
.if-pay-label { color:#728796; font-size:12px; font-weight:650; }
.if-pay-number { color:#183543; font-size:clamp(22px,2vw,29px); font-weight:800; margin:10px 0 5px; overflow-wrap:anywhere; }
.if-pay-detail { color:#90a1a9; font-size:11px; line-height:1.5; }
.if-pay-kpi.primary .if-pay-label,.if-pay-kpi.primary .if-pay-detail { color:#d1f1e6; }
.if-pay-kpi.primary .if-pay-number { color:#fff; }

/* Balance by currency */
.if-pay-currency-grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(185px,1fr));
    gap:12px;
    margin:14px 0 18px;
}
.if-pay-currency { background:#f9fcfb; border:1px solid #deebe5; border-radius:13px; padding:15px 18px; }
.if-pay-currency strong { display:block; color:#193e43; font-size:21px; margin-top:8px; overflow-wrap:anywhere; }

/* Informational note and empty states */
.if-pay-tip {
    background:#f1f8f5; border:1px solid #d7ebe1; border-radius:12px;
    padding:13px 17px; color:#4e7869; font-size:12px;
    line-height:1.7; margin:12px 0;
}
.if-pay-empty {
    display:flex; align-items:center; gap:13px; background:#fafcfb;
    border:1px solid #dfeae7; border-radius:15px; padding:21px; margin:15px 0;
}
.if-pay-empty-icon {
    display:grid; place-items:center; width:43px; height:43px;
    flex-shrink:0; background:#eaf8f1; border-radius:12px; color:#087b61; font-size:23px;
}
.if-pay-empty strong { display:block; color:#214149; font-size:15px; margin-bottom:5px; }
.if-pay-empty span { color:#758b98; font-size:12px; line-height:1.6; }

/* Premium tabs — compatible selectors for Streamlit tabs */
[data-testid="stTabs"] [role="tablist"],
.stTabs [role="tablist"],
.stTabs [data-baseweb="tab-list"] {
    display:flex !important; align-items:center !important; flex-wrap:wrap !important;
    gap:9px !important; padding:7px 0 13px !important;
    border-bottom:none !important; background:transparent !important;
}
[data-testid="stTabs"] [data-testid="stTab"],
[data-testid="stTabs"] [role="tab"],
.stTabs [role="tab"],
.stTabs [data-baseweb="tab"] {
    box-sizing:border-box !important; display:inline-flex !important;
    align-items:center !important; justify-content:center !important;
    min-height:42px !important; padding:10px 17px !important;
    background:#fff !important; border:1px solid #dce8e4 !important;
    border-radius:10px !important; color:#45636c !important;
    font-size:13px !important; font-weight:600 !important;
    text-decoration:none !important; box-shadow:0 2px 8px rgba(20,60,60,.025) !important;
    cursor:pointer !important;
    transition:background-color .2s ease,border-color .2s ease,color .2s ease,box-shadow .2s ease !important;
}
[data-testid="stTabs"] [role="tab"] p,
[data-testid="stTabs"] [data-testid="stTab"] p,
.stTabs [role="tab"] p { color:inherit !important; font-size:inherit !important; font-weight:inherit !important; }
[data-testid="stTabs"] [data-testid="stTab"]:hover,
[data-testid="stTabs"] [role="tab"]:hover,
.stTabs [role="tab"]:hover,
.stTabs [data-baseweb="tab"]:hover {
    background:#e9f7f0 !important; border-color:#b3dcc9 !important;
    color:#087b61 !important; box-shadow:0 4px 12px rgba(15,100,75,.06) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][data-selected],
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
[data-testid="stTabs"] [data-testid="stTab"][data-selected],
.stTabs [role="tab"][aria-selected="true"],
.stTabs [role="tab"][data-selected],
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background:#e5f5ec !important; border:1px solid #97cdb5 !important;
    border-radius:10px !important; color:#087b61 !important; font-weight:700 !important;
    box-shadow:inset 0 0 0 1px rgba(8,123,97,.035) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none !important; }
[data-testid="stTabs"] [role="tab"]:focus-visible,
.stTabs [role="tab"]:focus-visible { outline:2px solid #0c9270 !important; outline-offset:2px !important; }

/* Form and data grid */
[data-testid="stMain"] [data-testid="stForm"] {
    border:1px solid #dbe6e5 !important; border-radius:16px !important;
    padding:19px !important; background:#fff !important;
}
[data-testid="stMain"] [data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden; }

/* Download and Manage Invoices controls */
[data-testid="stMain"] [data-testid="stDownloadButton"] button,
[data-testid="stMain"] .st-key-payments_manage_invoices button {
    background:#fff !important; color:#146b59 !important;
    border:1px solid #bfded2 !important; border-radius:10px !important;
    font-size:12px !important; font-weight:650 !important;
    transition:background-color .2s ease,border-color .2s ease,color .2s ease,box-shadow .2s ease !important;
}
[data-testid="stMain"] [data-testid="stDownloadButton"] button:hover,
[data-testid="stMain"] .st-key-payments_manage_invoices button:hover {
    background:#e9f7f0 !important; border-color:#95cdb7 !important;
    color:#087b61 !important; box-shadow:0 4px 12px rgba(20,80,65,.055) !important;
}

/* Responsive layout */
@media (max-width:1080px) { .if-pay-kpis { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:600px) {
    .if-pay-hero { padding:23px 20px; }
    .if-pay-kpis { grid-template-columns:1fr; }
    [data-testid="stTabs"] [role="tab"],.stTabs [role="tab"] { padding:9px 12px !important; font-size:12px !important; }
    .if-pay-empty { padding:17px; }
}
@media (prefers-reduced-motion:reduce) {
    .if-pay-kpi,[data-testid="stTabs"] [role="tab"],.stTabs [role="tab"],
    [data-testid="stDownloadButton"] button,.st-key-payments_manage_invoices button {
        transition:none !important;
    }
}
</style>
"""


# ============================================================
# SHARED HELPERS
# ============================================================

def money(cents, currency):
    """Format integer cents without floating-point math."""
    amount = Decimal(int(cents or 0)) / Decimal("100")
    return f"{amount:,.2f} {currency}"


def section(title, description):
    st.html(
        '<div class="if-pay-section">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(description)}</p>'
        '</div>'
    )


def stat_cards(items, highlight_index=0):
    """Render up to four summary cards; optionally emphasize one card."""
    if not items:
        return

    blocks = []
    for index, (label, value, note) in enumerate(items):
        modifier = " primary" if index == highlight_index else ""
        blocks.append(
            f'<div class="if-pay-kpi{modifier}">'
            f'<div class="if-pay-label">{escape(str(label))}</div>'
            f'<div class="if-pay-number">{escape(str(value))}</div>'
            f'<div class="if-pay-detail">{escape(str(note))}</div>'
            '</div>'
        )

    st.html(
        f'<div class="if-pay-kpis" style="--if-kpi-columns:{min(len(items),4)}">'
        + "".join(blocks)
        + '</div>'
    )


def empty_state(title, description, icon="✓"):
    st.html(
        '<div class="if-pay-empty">'
        '<div class="if-pay-empty-icon" aria-hidden="true">'
        f'{escape(icon)}</div>'
        '<div>'
        f'<strong>{escape(title)}</strong>'
        f'<span>{escape(description)}</span>'
        '</div></div>'
    )


def currency_summary(grouped_cents, label="Filtered payments"):
    """Show separate money cards for each currency (never mix currencies)."""
    cards = []
    for currency, cents in sorted(grouped_cents.items()):
        cards.append(
            '<div class="if-pay-currency">'
            f'<div class="if-pay-label">{escape(label)} · {escape(str(currency))}</div>'
            f'<strong>{escape(money(cents, currency))}</strong>'
            '</div>'
        )
    if cards:
        st.html('<div class="if-pay-currency-grid">' + "".join(cards) + '</div>')


# ============================================================
# TAB 1 — INVOICE BALANCES
# ============================================================

def render_balances(rows, overview):
    section("Invoice Balances", "Search active invoices and track outstanding amounts.")

    if overview["outstanding_by_currency"]:
        currency_summary(
            overview["outstanding_by_currency"],
            label="Outstanding",
        )

    if not rows:
        empty_state("No active invoices", "Create an invoice to start tracking payments.", "▤")
        st.page_link(
            "pages/saved_invoices.py",
            label="Open Saved Invoices",
            icon=":material/receipt_long:",
        )
        return

    currencies = sorted({str(row["currency"]) for row in rows})
    search_col, status_col, currency_col = st.columns([2, 1.2, 1])

    with search_col:
        search = st.text_input(
            "Search invoice or contact",
            placeholder="Invoice number or customer / supplier",
            key="payments_balance_search",
        ).strip().casefold()

    with status_col:
        status = st.selectbox(
            "Payment status",
            ["All Statuses", "Paid", "Partially Paid", "Unpaid", "Overdue"],
            key="payments_balance_status",
        )

    with currency_col:
        currency = st.selectbox(
            "Currency", ["All"] + currencies, key="payments_balance_currency"
        )

    matches = [
        row for row in rows
        if (not search or search in f"{row['invoice_number']} {row['contact']}".casefold())
        and (status == "All Statuses" or row["status_label"] == status)
        and (currency == "All" or row["currency"] == currency)
    ]

    st.caption(f"Showing {len(matches)} of {len(rows)} active invoices")

    if not matches:
        empty_state("No matching invoices", "Try another search, status or currency.", "⌕")
        return

    status_icons = {
        "Paid": "🟢", "Partially Paid": "🟠", "Unpaid": "🔴", "Overdue": "⚠️"
    }

    table_data = []
    for row in matches:
        label = row["status_label"]
        table_data.append({
            "Invoice": row["invoice_number"],
            "Contact": row["contact"],
            "Type": row["invoice_type"],
            "Currency": row["currency"],
            "Total": int(row["total_cents"]) / 100,
            "Paid": int(row["paid_cents"]) / 100,
            "Remaining": int(row["remaining_cents"]) / 100,
            "Due Date": row["due_date"],
            "Status": f"{status_icons.get(label, '●')} {label}",
            "Days Overdue": row["overdue_days"],
        })

    st.dataframe(
        table_data,
        hide_index=True,
        width="stretch",
        row_height=39,
        column_config={
            "Contact": st.column_config.TextColumn("Customer / Supplier", width="large"),
            "Total": st.column_config.NumberColumn("Total", format="%.2f"),
            "Paid": st.column_config.NumberColumn("Paid", format="%.2f"),
            "Remaining": st.column_config.NumberColumn("Remaining", format="%.2f"),
        },
    )

    st.caption(
        "Amounts are displayed in each row's currency. "
        "Different currencies are not added together."
    )

    st.download_button(
        "Export Filtered Balances (CSV)",
        data=pd.DataFrame(table_data).to_csv(index=False).encode("utf-8-sig"),
        file_name="invoice_balances_filtered.csv",
        mime="text/csv",
        key="payments_balances_export",
    )

    if st.button(
        "Manage Invoices",
        icon=":material/receipt_long:",
        type="secondary",
        key="payments_manage_invoices",
    ):
        st.switch_page("pages/saved_invoices.py")


# ============================================================
# TAB 2 — REGISTER PAYMENT
# ============================================================

def render_register_payment(rows):
    section(
        "Register Payment",
        "Record a payment against an active invoice with money still due.",
    )

    payable = [row for row in rows if int(row["remaining_cents"]) > 0]
    if not payable:
        empty_state(
            "No outstanding invoices",
            "All active invoices are settled, or no invoices exist.",
        )
        return

    labels = {
        row["id"]: (
            f"{row['invoice_number']} — {row['contact']} "
            f"({money(row['remaining_cents'], row['currency'])} due)"
        )
        for row in payable
    }

    selected_id = st.selectbox(
        "Select invoice",
        options=list(labels),
        format_func=lambda invoice_id: labels[invoice_id],
        key="payments_selected_invoice",
    )
    selected = next(row for row in payable if row["id"] == selected_id)

    # Remaining balance is the actionable amount, so it is emphasized.
    stat_cards([
        (
            "Invoice total",
            money(selected["total_cents"], selected["currency"]),
            "Original total",
        ),
        (
            "Already paid",
            money(selected["paid_cents"], selected["currency"]),
            "Recorded payments",
        ),
        (
            "Remaining balance",
            money(selected["remaining_cents"], selected["currency"]),
            "Maximum you can pay",
        ),
    ], highlight_index=2)

    st.html(
        '<div class="if-pay-tip">'
        'Payments are validated before saving. Amounts cannot exceed the remaining '
        'invoice balance, and the date cannot be earlier than the invoice date.'
        '</div>'
    )

    with st.form(f"payment_form_{selected_id}", clear_on_submit=True):
        amount = st.text_input(
            f"Payment amount ({selected['currency']})",
            placeholder="e.g. 30.00",
            help="Use a dot for decimals. Up to two decimal places.",
        )

        left, right = st.columns(2)
        with left:
            payment_date = st.date_input("Payment date", value=date.today())
        with right:
            method = st.selectbox("Payment method", PAYMENT_METHODS)

        note = st.text_area(
            "Payment note (optional)",
            placeholder="Transaction reference or description",
            max_chars=300,
            height=85,
        )

        submitted = st.form_submit_button(
            "Register Payment", type="primary", use_container_width=True
        )

    if submitted:
        try:
            register_payment(
                invoice_id=selected_id,
                amount=amount.strip(),
                payment_date=payment_date.isoformat(),
                method=method,
                note=note.strip(),
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["payment_notice"] = "Payment registered successfully."
            st.rerun()


# ============================================================
# TAB 3 — PAYMENT HISTORY
# ============================================================

def render_history(history):
    section(
        "Payment History",
        "Search registered transactions, including payments on archived invoices.",
    )

    if not history:
        empty_state("No payments recorded", "Your first payment will appear here when saved.", "▤")
        return

    currencies = sorted({str(item["currency"]) for item in history})

    # Four filters share one row on desktop.
    search_col, currency_col, method_col, period_col = st.columns([2.2, 1, 1, 1.15])

    with search_col:
        search = st.text_input(
            "Search transaction",
            placeholder="Invoice number, contact or note",
            key="payments_history_search",
        ).strip().casefold()

    with currency_col:
        currency = st.selectbox(
            "Currency", ["All"] + currencies, key="payments_history_currency"
        )

    with method_col:
        method = st.selectbox(
            "Method", ["All"] + list(PAYMENT_METHODS), key="payments_history_method"
        )

    with period_col:
        period = st.selectbox(
            "Date range",
            ["All dates", "Last 7 days", "Last 30 days", "Last 90 days"],
            key="payments_history_period",
        )

    days = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
    }.get(period)
    cutoff = date.today() - timedelta(days=days - 1) if days else None

    filtered = []
    for payment in history:
        terms = (
            f"{payment['invoice_number']} {payment['contact']} "
            f"{payment.get('note') or ''}"
        ).casefold()
        if search and search not in terms:
            continue
        if currency != "All" and payment["currency"] != currency:
            continue
        if method != "All" and payment["method"] != method:
            continue
        if cutoff and date.fromisoformat(str(payment["payment_date"])) < cutoff:
            continue
        filtered.append(payment)

    st.caption(f"Showing {len(filtered)} of {len(history)} recorded payments")

    if not filtered:
        empty_state("No matching transactions", "Try changing the search or filters.", "⌕")
        return

    # Derived from the visible transactions only, grouped by currency.
    totals_by_currency = defaultdict(int)
    for payment in filtered:
        totals_by_currency[str(payment["currency"])] += int(payment["amount_cents"])

    if len(totals_by_currency) == 1:
        only_currency, total_cents = next(iter(totals_by_currency.items()))
        stat_cards([
            ("Filtered payments", money(total_cents, only_currency), "Total of visible transactions"),
            ("Transactions", str(len(filtered)), "Matching payment records"),
        ], highlight_index=0)
    else:
        currency_summary(totals_by_currency, label="Filtered payments")
        st.caption("Totals are separated by currency; different currencies are never combined.")

    table_data = []
    for item in filtered:
        table_data.append({
            "Payment ID": item["id"],
            "Invoice": item["invoice_number"],
            "Contact": item["contact"],
            "Date": item["payment_date"],
            "Method": item["method"],
            "Currency": item["currency"],
            "Amount": int(item["amount_cents"]) / 100,
            "Note": item.get("note") or "",
        })

    st.dataframe(
        table_data,
        hide_index=True,
        width="stretch",
        row_height=39,
        column_config={
            "Contact": st.column_config.TextColumn("Customer / Supplier", width="large"),
            "Amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "Note": st.column_config.TextColumn("Reference / Note", width="large"),
        },
    )

    st.download_button(
        "Export Filtered History (CSV)",
        data=pd.DataFrame(table_data).to_csv(index=False).encode("utf-8-sig"),
        file_name="payment_history_filtered.csv",
        mime="text/csv",
        key="payments_history_export",
    )


# ============================================================
# TAB 4 — FINANCIAL INSIGHTS
# ============================================================

def render_financial_insights(rows):
    section(
        "Financial Insights",
        "Currency-specific financial analytics from active invoices.",
    )

    currencies = sorted({str(row["currency"]) for row in rows})
    if not currencies:
        empty_state(
            "No financial activity", "Create a saved invoice to activate business analytics.", "▤"
        )
        return

    currency = st.selectbox(
        "Reporting currency", currencies, key="payment_analytics_currency"
    )
    insights = get_financial_insights(currency)

    # Emphasize the meaningful metric, not a zero just because it is first.
    sales = int(insights["sales_invoiced_cents"])
    purchases = int(insights["purchases_invoiced_cents"])
    receivables = int(insights["receivables_cents"])
    payables = int(insights["payables_cents"])

    stat_cards([
        ("Sales invoiced", money(sales, currency), "Active sales invoices"),
        ("Purchases invoiced", money(purchases, currency), "Active purchase invoices"),
        (
            "Cash received",
            money(insights["cash_received_cents"], currency),
            "Recorded incoming payments",
        ),
        (
            "Cash paid",
            money(insights["cash_paid_cents"], currency),
            "Recorded outgoing payments",
        ),
    ], highlight_index=1 if purchases > sales else (0 if sales > 0 else None))

    stat_cards([
        ("Receivables", money(receivables, currency), "Customers still owe"),
        ("Payables", money(payables, currency), "Suppliers still owed"),
        (
            "Overdue receivables",
            money(insights["overdue_receivables_cents"], currency),
            "Late customer payments",
        ),
        (
            "Overdue payables",
            money(insights["overdue_payables_cents"], currency),
            "Late supplier payments",
        ),
    ], highlight_index=1 if payables > receivables else (0 if receivables > 0 else None))

    # Charts already used on Dashboard — preserve existing implementation.
    render_financial_intelligence(insights, currency)

    section(
        "Invoices requiring attention",
        "Overdue and upcoming obligations in this currency.",
    )

    overdue = int(insights["overdue_count"])
    due_soon = int(insights["due_soon_count"])

    if overdue == 0 and due_soon == 0 and not insights["attention"]:
        empty_state(
            "All caught up",
            "No overdue or soon-due invoices for this currency.",
        )
    else:
        relevant_cards = []
        if overdue > 0:
            relevant_cards.append(("Overdue", overdue, "Past due date"))
        if due_soon > 0:
            relevant_cards.append(("Due within 7 days", due_soon, "Upcoming deadline"))
        if relevant_cards:
            stat_cards(relevant_cards, highlight_index=0)

        if insights["attention"]:
            attention_rows = []
            for row in insights["attention"]:
                attention_rows.append({
                    "Invoice": row["Invoice"],
                    "Contact": row["Contact"],
                    "Type": row["Type"],
                    "Due Date": row["Due Date"],
                    "Remaining": money(row["Remaining Cents"], currency),
                    "Status": row["Status"],
                    "Days Overdue": row["Days Overdue"],
                })
            st.dataframe(attention_rows, hide_index=True, width="stretch")

    section(
        "Recent transactions",
        "The latest payments for active invoices in this currency.",
    )

    if insights["recent_payments"]:
        recent_rows = []
        for row in insights["recent_payments"]:
            recent_rows.append({
                "Invoice": row["invoice_number"],
                "Contact": row["contact"],
                "Type": row["invoice_type"],
                "Amount": money(row["amount_cents"], currency),
                "Date": row["payment_date"],
                "Method": row["method"],
            })
        st.dataframe(recent_rows, hide_index=True, width="stretch")
    else:
        empty_state(
            "No recent transactions", "Recorded payments will appear here.", "▤"
        )

    st.caption(
        "Cash movements reflect recorded transactions, not a verified "
        "bank balance or accounting profit."
    )


# ============================================================
# PAGE INITIALIZATION & NAVIGATION
# ============================================================

initialize_payment_store()
apply_hover_effects()
st.html(PAYMENTS_CSS)

st.html("""
<div class="if-pay-hero">
    <div class="if-pay-eyebrow">FINANCIAL WORKSPACE</div>
    <h1>Payment Management</h1>
    <p>Track outstanding balances, register payments and review transaction history.</p>
</div>
""")

notice = st.session_state.pop("payment_notice", None)
if notice:
    st.success(notice)

balance_summary = summarize_invoice_balances(list_invoice_balances())
active_rows = balance_summary["rows"]

stat_cards([
    ("Active invoices", balance_summary["total_count"], "Active saved invoice records"),
    ("Fully paid", balance_summary["paid_count"], "Invoices with zero balance"),
    ("Outstanding", balance_summary["outstanding_count"], "Invoices still requiring payment"),
    ("Overdue", balance_summary["overdue_count"], "Invoices past their due date"),
], highlight_index=0)

if balance_summary["overdue_count"]:
    st.warning(
        f"{balance_summary['overdue_count']} invoice(s) have passed their payment deadline."
    )

# Tabs retain the fast client-side switching that was verified in the browser.
balances_tab, register_tab, history_tab, insights_tab = st.tabs([
    "Invoice Balances", "Register Payment", "Payment History", "Financial Insights"
])

with balances_tab:
    render_balances(active_rows, balance_summary)

with register_tab:
    render_register_payment(active_rows)

with history_tab:
    render_history(list_payment_history())

with insights_tab:
    render_financial_insights(active_rows)
