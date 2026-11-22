
import pytest

from invoiceflow.database import create_contact
from invoiceflow.invoice_store import (
    initialize_invoice_store,
    create_saved_invoice,
    list_saved_invoices,
    archive_saved_invoice,
restore_saved_invoice,
list_archived_invoices,
update_saved_invoice,
)
from invoiceflow.payments import register_payment

@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.db"
    initialize_invoice_store(path)
    return path


def make_invoice(database, contact_id, **changes):
    invoice = {
        "invoice_type": "Purchase",
        "contact_id": contact_id,
        "invoice_number": "INV-100",
        "invoice_date": "2026-11-17",
        "due_date": "2026-11-30",
        "currency": "EUR",
        "subtotal": "100.00",
        "vat_rate": "20",
        "db_path": database,
    }

    invoice.update(changes)

    return create_saved_invoice(**invoice)


def test_create_and_list_invoice(database):
    contact_id = create_contact(
        "Supplier",
        "Alpha Services",
        db_path=database,
    )

    make_invoice(database, contact_id)

    rows = list_saved_invoices(database)

    assert len(rows) == 1
    assert rows[0]["Total"] == "120.00"
    assert rows[0]["Contact"] == "Alpha Services"


def test_duplicate_invoice(database):
    contact_id = create_contact(
        "Supplier",
        "Alpha Services",
        db_path=database,
    )

    make_invoice(database, contact_id)

    with pytest.raises(ValueError, match="Duplicate"):
        make_invoice(database, contact_id)


def test_wrong_contact_type(database):
    contact_id = create_contact(
        "Customer",
        "Demo Retail Ltd",
        db_path=database,
    )

    with pytest.raises(
        ValueError,
        match="active supplier",
    ):
        make_invoice(database, contact_id)


def test_financial_rounding(database):
    contact_id = create_contact(
        "Supplier",
        "Alpha Services",
        db_path=database,
    )

    make_invoice(
        database,
        contact_id,
        subtotal="0.05",
        vat_rate="10",
    )

    rows = list_saved_invoices(database)

    assert rows[0]["Total"] == "0.06"


def test_invalid_due_date(database):
    contact_id = create_contact(
        "Supplier",
        "Alpha Services",
        db_path=database,
    )

    with pytest.raises(ValueError, match="Due date"):
        make_invoice(
            database,
            contact_id,
            due_date="2026-01-01",
        )

def test_archive_and_restore_invoice(database):
    contact_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=database,
    )

    invoice_id = make_invoice(database, contact_id)

    archive_saved_invoice(invoice_id, db_path=database)

    assert list_saved_invoices(database) == []
    assert len(list_archived_invoices(database)) == 1

    restore_saved_invoice(invoice_id, db_path=database)

    assert len(list_saved_invoices(database)) == 1
    assert list_archived_invoices(database) == []


def test_invalid_archive_and_restore(database):
    contact_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=database,
    )

    invoice_id = make_invoice(database, contact_id)

    with pytest.raises(ValueError, match="Archived invoice"):
        restore_saved_invoice(invoice_id, db_path=database)

    archive_saved_invoice(invoice_id, db_path=database)

    with pytest.raises(ValueError, match="Active invoice"):
        archive_saved_invoice(invoice_id, db_path=database)

def test_update_invoice(database):
    contact_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=database,
    )

    invoice_id = make_invoice(
        database,
        contact_id,
    )

    update_saved_invoice(
        invoice_id=invoice_id,
        invoice_number="INV-UPDATED",
        invoice_date="2026-11-17",
        due_date="2026-12-01",
        currency="EUR",
        subtotal="150.00",
        vat_rate="20",
        db_path=database,
    )

    rows = list_saved_invoices(database)

    assert len(rows) == 1
    assert rows[0]["Invoice"] == "INV-UPDATED"
    assert rows[0]["Total"] == "180.00"


def test_cannot_update_archived_invoice(database):
    contact_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=database,
    )

    invoice_id = make_invoice(database, contact_id)
    archive_saved_invoice(invoice_id, db_path=database)

    with pytest.raises(ValueError, match="Active invoice"):
        update_saved_invoice(
            invoice_id=invoice_id,
            invoice_number="INV-UPDATED",
            invoice_date="2026-11-17",
            due_date="2026-12-01",
            currency="EUR",
            subtotal="150.00",
            vat_rate="20",
            db_path=database,
        )


def test_update_duplicate_invoice_number(database):
    contact_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=database,
    )

    make_invoice(database, contact_id)

    second_id = make_invoice(
        database,
        contact_id,
        invoice_number="INV-200",
    )

    with pytest.raises(ValueError, match="Duplicate"):
        update_saved_invoice(
            invoice_id=second_id,
            invoice_number="INV-100",
            invoice_date="2026-11-17",
            due_date="2026-12-01",
            currency="EUR",
            subtotal="100.00",
            vat_rate="20",
            db_path=database,
        )

def test_cannot_reduce_total_below_paid(database):
    supplier = create_contact(
        "Supplier", "Test Supplier", db_path=database
    )
    invoice_id = make_invoice(database, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=database,
    )

    with pytest.raises(ValueError, match="below"):
        update_saved_invoice(
            invoice_id, "INV-100",
            "2026-11-17", "2026-12-01",
            "EUR", "20.00", "20",
            db_path=database,
        )

    assert list_saved_invoices(database)[0]["Total"] == "120.00"


def test_cannot_change_currency_after_payment(database):
    supplier = create_contact(
        "Supplier", "Test Supplier", db_path=database
    )
    invoice_id = make_invoice(database, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=database,
    )

    with pytest.raises(ValueError, match="currency"):
        update_saved_invoice(
            invoice_id, "INV-100",
            "2026-11-17", "2026-12-01",
            "USD", "100.00", "20",
            db_path=database,
        )


def test_status_updates_when_total_equals_paid(database):
    supplier = create_contact(
        "Supplier", "Test Supplier", db_path=database
    )
    invoice_id = make_invoice(database, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=database,
    )

    update_saved_invoice(
        invoice_id, "INV-100",
        "2026-11-17", "2026-12-01",
        "EUR", "50.00", "0",
        db_path=database,
    )

    invoice = list_saved_invoices(database)[0]

    assert invoice["Total"] == "50.00"
    assert invoice["Payment"] == "paid"


def test_cannot_move_invoice_date_after_payment(database):
    supplier = create_contact(
        "Supplier", "Test Supplier", db_path=database
    )
    invoice_id = make_invoice(database, supplier)

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Cash", db_path=database,
    )

    with pytest.raises(ValueError, match="payment date"):
        update_saved_invoice(
            invoice_id, "INV-100",
            "2026-11-19", "2026-12-01",
            "EUR", "100.00", "20",
            db_path=database,
        )

