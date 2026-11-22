
import sqlite3
from contextlib import closing
from datetime import date

from invoiceflow.database import DB_PATH
from invoiceflow.invoice_store import CURRENCIES
from invoiceflow.payments import initialize_payment_store
from invoiceflow.payment_status import describe_invoice_balance


def get_financial_insights(currency, as_of=None, db_path=DB_PATH):
    """
    Build financial analytics for one currency.

    Only active invoices are included.
    Recorded payments are separated from invoiced totals.
    """

    if currency not in CURRENCIES:
        raise ValueError("Unsupported currency.")

    today = as_of if as_of is not None else date.today()
    initialize_payment_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        invoices = connection.execute(
            """
            SELECT
                i.id,
                i.invoice_number,
                i.invoice_type,
                i.invoice_date,
                i.due_date,
                i.currency,
                i.total_cents,
                c.name AS contact,
                COALESCE(
                    (
                        SELECT SUM(p.amount_cents)
                        FROM payments AS p
                        WHERE p.invoice_id = i.id
                    ),
                    0
                ) AS paid_cents
            FROM invoices AS i
            JOIN contacts AS c
                ON c.id = i.contact_id
            WHERE i.is_active = 1
              AND i.currency = ?
            ORDER BY i.due_date, i.id
            """,
            (currency,),
        ).fetchall()

        payments = connection.execute(
            """
            SELECT
                p.id,
                p.payment_date,
                p.amount_cents,
                p.method,
                i.invoice_type,
                i.invoice_number,
                c.name AS contact
            FROM payments AS p
            JOIN invoices AS i
                ON i.id = p.invoice_id
            JOIN contacts AS c
                ON c.id = i.contact_id
            WHERE i.is_active = 1
              AND i.currency = ?
            ORDER BY p.payment_date DESC, p.id DESC
            """,
            (currency,),
        ).fetchall()

    summary = {
        "currency": currency,
        "active_count": len(invoices),
        "overdue_count": 0,
        "due_soon_count": 0,
        "sales_invoiced_cents": 0,
        "purchases_invoiced_cents": 0,
        "cash_received_cents": 0,
        "cash_paid_cents": 0,
        "receivables_cents": 0,
        "payables_cents": 0,
        "overdue_receivables_cents": 0,
        "overdue_payables_cents": 0,
    }

    invoiced_months = {}
    payment_months = {}
    attention = []

    # INVOICE ANALYTICS

    for raw_invoice in invoices:
        invoice = describe_invoice_balance(
            dict(raw_invoice),
            as_of=today,
        )

        total = invoice["total_cents"]
        remaining = invoice["remaining_cents"]
        invoice_type = invoice["invoice_type"]

        month = invoice["invoice_date"][:7]

        if month not in invoiced_months:
            invoiced_months[month] = {
                "Month": month,
                "Sales": 0,
                "Purchases": 0,
            }

        if invoice_type == "Sale":
            summary["sales_invoiced_cents"] += total
            summary["receivables_cents"] += remaining
            invoiced_months[month]["Sales"] += total

            if invoice["is_overdue"]:
                summary["overdue_receivables_cents"] += remaining

        else:
            summary["purchases_invoiced_cents"] += total
            summary["payables_cents"] += remaining
            invoiced_months[month]["Purchases"] += total

            if invoice["is_overdue"]:
                summary["overdue_payables_cents"] += remaining

        if invoice["is_overdue"]:
            summary["overdue_count"] += 1

        days_until_due = (
            date.fromisoformat(invoice["due_date"]) - today
        ).days

        due_soon = (
            remaining > 0
            and 0 <= days_until_due <= 7
        )

        if due_soon:
            summary["due_soon_count"] += 1

        if invoice["is_overdue"] or due_soon:
            attention.append({
                "Invoice": invoice["invoice_number"],
                "Contact": invoice["contact"],
                "Type": invoice_type,
                "Due Date": invoice["due_date"],
                "Remaining Cents": remaining,
                "Status": invoice["status_label"]
                    if invoice["is_overdue"]
                    else "Due Soon",
                "Days Overdue": invoice["overdue_days"],
            })

    # PAYMENT ANALYTICS

    for raw_payment in payments:
        payment = dict(raw_payment)
        amount = payment["amount_cents"]
        month = payment["payment_date"][:7]

        if month not in payment_months:
            payment_months[month] = {
                "Month": month,
                "Cash In": 0,
                "Cash Out": 0,
            }

        if payment["invoice_type"] == "Sale":
            summary["cash_received_cents"] += amount
            payment_months[month]["Cash In"] += amount

        else:
            summary["cash_paid_cents"] += amount
            payment_months[month]["Cash Out"] += amount

    summary["monthly_invoiced"] = [
        invoiced_months[month]
        for month in sorted(invoiced_months)
    ]

    summary["monthly_payments"] = [
        payment_months[month]
        for month in sorted(payment_months)
    ]

    summary["attention"] = sorted(
        attention,
        key=lambda row: (row["Due Date"], row["Invoice"]),
    )

    summary["recent_payments"] = [
        dict(payment)
        for payment in payments[:8]
    ]

    return summary
