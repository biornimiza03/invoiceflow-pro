
import pytest

from invoiceflow.database import create_contact
from invoiceflow.invoice_store import (
    initialize_invoice_store,
    create_saved_invoice,
    update_saved_invoice,
    archive_saved_invoice,
)
from invoiceflow.saved_analytics import (
    list_active_currencies,
    get_saved_dashboard_summary,
)
from invoiceflow.payments import register_payment


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "business_test.db"
    initialize_invoice_store(path)
    return path


def save_invoice(
    database,
    contact_id,
    invoice_type="Purchase",
    number="INV-100",
    currency="EUR",
    subtotal="100.00",
):
    return create_saved_invoice(
        invoice_type=invoice_type,
        contact_id=contact_id,
        invoice_number=number,
        invoice_date="2026-11-17",
        due_date="2026-12-01",
        currency=currency,
        subtotal=subtotal,
        vat_rate="20",
        db_path=database,
    )


def test_empty_dashboard(database):
    assert list_active_currencies(database) == []

    summary = get_saved_dashboard_summary("EUR", database)

    assert summary["invoice_count"] == 0
    assert summary["sales_cents"] == 0
    assert summary["purchases_cents"] == 0
    assert summary["months"] == []


def test_sales_and_purchases_separated(database):
    supplier = create_contact(
        "Supplier", "Alpha Services", db_path=database
    )
    customer = create_contact(
        "Customer", "Demo Retail", db_path=database
    )

    save_invoice(database, supplier)

    save_invoice(
        database,
        customer,
        invoice_type="Sale",
        number="SALE-100",
        subtotal="200.00",
    )

    summary = get_saved_dashboard_summary("EUR", database)

    assert summary["invoice_count"] == 2
    assert summary["purchases_cents"] == 12000
    assert summary["sales_cents"] == 24000
    assert summary["unpaid_sales_cents"] == 24000
    assert summary["unpaid_purchases_cents"] == 12000
    assert summary["months"][0]["month"] == "2026-11"


def test_archived_invoices_excluded(database):
    supplier = create_contact(
        "Supplier", "Alpha Services", db_path=database
    )

    invoice_id = save_invoice(database, supplier)

    archive_saved_invoice(invoice_id, db_path=database)

    summary = get_saved_dashboard_summary("EUR", database)

    assert summary["invoice_count"] == 0
    assert summary["purchases_cents"] == 0
    assert list_active_currencies(database) == []


def test_currencies_separated(database):
    supplier = create_contact(
        "Supplier", "Alpha Services", db_path=database
    )

    save_invoice(database, supplier)

    save_invoice(
        database,
        supplier,
        number="INV-USD",
        currency="USD",
    )

    assert list_active_currencies(database) == ["EUR", "USD"]

    eur = get_saved_dashboard_summary("EUR", database)
    usd = get_saved_dashboard_summary("USD", database)

    assert eur["invoice_count"] == 1
    assert usd["invoice_count"] == 1
    assert eur["purchases_cents"] == 12000
    assert usd["purchases_cents"] == 12000


def test_dashboard_reflects_invoice_edit(database):
    supplier = create_contact(
        "Supplier", "Alpha Services", db_path=database
    )

    invoice_id = save_invoice(database, supplier)

    update_saved_invoice(
        invoice_id=invoice_id,
        invoice_number="INV-100",
        invoice_date="2026-11-17",
        due_date="2026-12-01",
        currency="EUR",
        subtotal="150.00",
        vat_rate="20",
        db_path=database,
    )

    summary = get_saved_dashboard_summary("EUR", database)

    assert summary["invoice_count"] == 1
    assert summary["purchases_cents"] == 18000


def test_dashboard_partial_payment(database):
    supplier = create_contact(
        "Supplier",
        "Payment Test Supplier",
        db_path=database,
    )

    invoice_id = save_invoice(
        database,
        supplier,
        subtotal="150.00",
    )

    register_payment(
        invoice_id=invoice_id,
        amount="50.00",
        payment_date="2026-11-18",
        method="Bank transfer",
        db_path=database,
    )

    summary = get_saved_dashboard_summary(
        "EUR",
        database,
    )

    assert summary["purchases_cents"] == 18000
    assert summary["unpaid_purchases_cents"] == 13000

