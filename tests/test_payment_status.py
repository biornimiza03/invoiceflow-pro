
from datetime import date

import pytest

from invoiceflow.payment_status import (
    describe_invoice_balance,
    summarize_invoice_balances,
)


TEST_DATE = date(2026, 11, 18)


def make_balance(
    total=18000,
    paid=0,
    due="2026-12-01",
    currency="EUR",
):
    return {
        "invoice_number": "TEST-001",
        "total_cents": total,
        "paid_cents": paid,
        "due_date": due,
        "currency": currency,
    }


@pytest.mark.parametrize(
    "paid,due,status,days",
    [
        (0, "2026-12-01", "Unpaid", 0),
        (5000, "2026-12-01", "Partially Paid", 0),
        (18000, "2026-11-01", "Paid", 0),
        (0, "2026-11-10", "Overdue", 8),
        (5000, "2026-11-10", "Overdue", 8),
        (0, "2026-11-18", "Unpaid", 0),
    ],
)
def test_payment_statuses(paid, due, status, days):
    invoice = make_balance(
        paid=paid,
        due=due,
    )

    result = describe_invoice_balance(
        invoice,
        as_of=TEST_DATE,
    )

    assert result["status_label"] == status
    assert result["overdue_days"] == days
    assert result["remaining_cents"] == 18000 - paid


def test_currencies_remain_separate():
    invoices = [
        make_balance(
            total=18000,
            paid=5000,
            due="2026-11-10",
        ),
        make_balance(
            total=3000,
            paid=0,
            due="2026-12-01",
        ),
        make_balance(
            total=10000,
            paid=10000,
            due="2026-11-10",
            currency="USD",
        ),
    ]

    result = summarize_invoice_balances(
        invoices,
        as_of=TEST_DATE,
    )

    assert result["total_count"] == 3
    assert result["paid_count"] == 1
    assert result["outstanding_count"] == 2
    assert result["overdue_count"] == 1

    assert result["outstanding_by_currency"] == {
        "EUR": 16000,
        "USD": 0,
    }


def test_empty_invoice_list():
    result = summarize_invoice_balances(
        [],
        as_of=TEST_DATE,
    )

    assert result["total_count"] == 0
    assert result["overdue_count"] == 0
    assert result["outstanding_by_currency"] == {}


def test_inconsistent_payment_balance():
    invoice = make_balance(
        total=10000,
        paid=12000,
    )

    with pytest.raises(
        ValueError,
        match="Inconsistent invoice balance",
    ):
        describe_invoice_balance(
            invoice,
            as_of=TEST_DATE,
        )
