
from datetime import date


def describe_invoice_balance(invoice, as_of=None):
    """
    Calculate an invoice's current payment status.

    An overdue invoice has an unpaid balance
    and a due date earlier than today.
    """

    today = as_of if as_of is not None else date.today()

    total = int(invoice["total_cents"])
    paid = int(invoice["paid_cents"])
    due_date = date.fromisoformat(invoice["due_date"])

    if total < 0 or paid < 0 or paid > total:
        raise ValueError("Inconsistent invoice balance.")

    remaining = total - paid

    overdue_days = (
        max(0, (today - due_date).days)
        if remaining > 0
        else 0
    )

    if remaining == 0:
        status = "Paid"

    elif overdue_days > 0:
        status = "Overdue"

    elif paid > 0:
        status = "Partially Paid"

    else:
        status = "Unpaid"

    return {
        **invoice,
        "remaining_cents": remaining,
        "status_label": status,
        "is_overdue": overdue_days > 0,
        "overdue_days": overdue_days,
    }


def summarize_invoice_balances(invoices, as_of=None):
    """
    Summarize payment statuses and unpaid amounts.

    Different currencies are kept separate.
    """

    rows = [
        describe_invoice_balance(invoice, as_of)
        for invoice in invoices
    ]

    outstanding_by_currency = {}

    for invoice in rows:
        currency = invoice["currency"]

        outstanding_by_currency[currency] = (
            outstanding_by_currency.get(currency, 0)
            + invoice["remaining_cents"]
        )

    return {
        "rows": rows,
        "total_count": len(rows),
        "paid_count": sum(
            row["remaining_cents"] == 0
            for row in rows
        ),
        "outstanding_count": sum(
            row["remaining_cents"] > 0
            for row in rows
        ),
        "overdue_count": sum(
            row["is_overdue"]
            for row in rows
        ),
        "outstanding_by_currency": outstanding_by_currency,
    }
