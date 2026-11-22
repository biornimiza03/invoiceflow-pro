
from datetime import date

import pytest

from invoiceflow.database import create_contact
from invoiceflow.invoice_store import (
    create_saved_invoice,
    archive_saved_invoice,
)
from invoiceflow.payments import (
    initialize_payment_store,
    register_payment,
)
from invoiceflow.financial_insights import (
    get_financial_insights,
)


TEST_DATE = date(2026, 11, 18)


@pytest.fixture
def business_db(tmp_path):
    db_path = tmp_path / "financial_test.db"

    initialize_payment_store(db_path)

    supplier = create_contact(
        "Supplier", "Test Supplier", db_path=db_path
    )
    customer = create_contact(
        "Customer", "Test Customer", db_path=db_path
    )

    return db_path, supplier, customer


def new_invoice(
    db_path,
    contact_id,
    number="INV-001",
    invoice_type="Purchase",
    subtotal="100.00",
    currency="EUR",
    due="2026-12-01",
):
    return create_saved_invoice(
        invoice_type=invoice_type,
        contact_id=contact_id,
        invoice_number=number,
        invoice_date="2026-11-01",
        due_date=due,
        currency=currency,
        subtotal=subtotal,
        vat_rate="20",
        db_path=db_path,
    )


def test_empty_analytics(business_db):
    db_path, _, _ = business_db

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["active_count"] == 0
    assert result["cash_received_cents"] == 0
    assert result["payables_cents"] == 0
    assert result["monthly_payments"] == []


def test_partial_purchase_payment(business_db):
    db_path, supplier, _ = business_db

    invoice_id = new_invoice(
        db_path, supplier, subtotal="150.00"
    )

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Bank transfer", db_path=db_path,
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["purchases_invoiced_cents"] == 18000
    assert result["cash_paid_cents"] == 5000
    assert result["payables_cents"] == 13000
    assert result["cash_received_cents"] == 0


def test_sales_and_purchases_separated(business_db):
    db_path, supplier, customer = business_db

    purchase = new_invoice(db_path, supplier)

    sale = new_invoice(
        db_path,
        customer,
        number="SALE-001",
        invoice_type="Sale",
        subtotal="200.00",
    )

    register_payment(
        purchase, "50.00", "2026-11-18",
        "Cash", db_path=db_path,
    )

    register_payment(
        sale, "80.00", "2026-11-18",
        "Bank transfer", db_path=db_path,
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["sales_invoiced_cents"] == 24000
    assert result["purchases_invoiced_cents"] == 12000
    assert result["cash_received_cents"] == 8000
    assert result["cash_paid_cents"] == 5000
    assert result["receivables_cents"] == 16000
    assert result["payables_cents"] == 7000


def test_overdue_invoice(business_db):
    db_path, supplier, _ = business_db

    new_invoice(
        db_path,
        supplier,
        due="2026-11-10",
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["overdue_count"] == 1
    assert result["overdue_payables_cents"] == 12000
    assert result["attention"][0]["Status"] == "Overdue"
    assert result["attention"][0]["Days Overdue"] == 8


def test_upcoming_invoice(business_db):
    db_path, supplier, _ = business_db

    new_invoice(
        db_path,
        supplier,
        due="2026-11-22",
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["due_soon_count"] == 1
    assert result["overdue_count"] == 0
    assert result["attention"][0]["Status"] == "Due Soon"


def test_currencies_are_separate(business_db):
    db_path, supplier, customer = business_db

    new_invoice(db_path, supplier)

    new_invoice(
        db_path,
        customer,
        number="USD-001",
        invoice_type="Sale",
        currency="USD",
    )

    eur = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )
    usd = get_financial_insights(
        "USD", TEST_DATE, db_path
    )

    assert eur["active_count"] == 1
    assert eur["purchases_invoiced_cents"] == 12000
    assert eur["sales_invoiced_cents"] == 0

    assert usd["active_count"] == 1
    assert usd["sales_invoiced_cents"] == 12000
    assert usd["purchases_invoiced_cents"] == 0


def test_archived_invoice_excluded(business_db):
    db_path, supplier, _ = business_db

    invoice_id = new_invoice(db_path, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=db_path,
    )

    archive_saved_invoice(
        invoice_id, db_path=db_path
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["active_count"] == 0
    assert result["cash_paid_cents"] == 0
    assert result["recent_payments"] == []


def test_monthly_cash_activity(business_db):
    db_path, supplier, _ = business_db

    invoice_id = new_invoice(db_path, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=db_path,
    )

    register_payment(
        invoice_id, "70.00", "2026-12-01",
        "Bank transfer", db_path=db_path,
    )

    result = get_financial_insights(
        "EUR", date(2026, 12, 2), db_path
    )

    monthly = result["monthly_payments"]

    assert len(monthly) == 2
    assert monthly[0]["Month"] == "2026-11"
    assert monthly[0]["Cash Out"] == 5000
    assert monthly[1]["Month"] == "2026-12"
    assert monthly[1]["Cash Out"] == 7000
    assert result["payables_cents"] == 0


def test_fully_paid_invoice_not_overdue(business_db):
    db_path, supplier, _ = business_db

    invoice_id = new_invoice(
        db_path,
        supplier,
        due="2026-11-10",
    )

    register_payment(
        invoice_id, "120.00", "2026-11-18",
        "Bank transfer", db_path=db_path,
    )

    result = get_financial_insights(
        "EUR", TEST_DATE, db_path
    )

    assert result["cash_paid_cents"] == 12000
    assert result["payables_cents"] == 0
    assert result["overdue_count"] == 0
