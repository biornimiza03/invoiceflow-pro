
import pytest

from invoiceflow.database import create_contact
from invoiceflow.invoice_store import (
    initialize_invoice_store,
    create_saved_invoice,
    archive_saved_invoice,
)
from invoiceflow.payments import (
    initialize_payment_store,
    register_payment,
    list_invoice_balances,
    list_payment_history,
)


@pytest.fixture
def sample_invoice(tmp_path):
    db_path = tmp_path / "payments_test.db"

    initialize_invoice_store(db_path)
    initialize_payment_store(db_path)

    supplier_id = create_contact(
        "Supplier",
        "Test Supplier",
        db_path=db_path,
    )

    invoice_id = create_saved_invoice(
        invoice_type="Purchase",
        contact_id=supplier_id,
        invoice_number="TEST-001",
        invoice_date="2026-11-17",
        due_date="2026-12-01",
        currency="EUR",
        subtotal="100.00",
        vat_rate="20",
        db_path=db_path,
    )

    return db_path, invoice_id


def test_partial_and_full_payment(sample_invoice):
    db_path, invoice_id = sample_invoice

    register_payment(
        invoice_id, "50.00", "2026-11-18",
        "Bank transfer", db_path=db_path,
    )

    balance = list_invoice_balances(db_path)[0]

    assert balance["paid_cents"] == 5000
    assert balance["remaining_cents"] == 7000
    assert balance["payment_status"] == "partial"

    register_payment(
        invoice_id, "70.00", "2026-11-19",
        "Cash", db_path=db_path,
    )

    balance = list_invoice_balances(db_path)[0]

    assert balance["paid_cents"] == 12000
    assert balance["remaining_cents"] == 0
    assert balance["payment_status"] == "paid"


def test_cannot_overpay(sample_invoice):
    db_path, invoice_id = sample_invoice

    with pytest.raises(ValueError, match="exceeds"):
        register_payment(
            invoice_id, "150.00", "2026-11-18",
            "Cash", db_path=db_path,
        )

    assert list_payment_history(db_path) == []


def test_cannot_pay_archived_invoice(sample_invoice):
    db_path, invoice_id = sample_invoice

    archive_saved_invoice(invoice_id, db_path=db_path)

    with pytest.raises(ValueError, match="Active invoice"):
        register_payment(
            invoice_id, "20.00", "2026-11-18",
            "Cash", db_path=db_path,
        )


@pytest.mark.parametrize(
    "invalid_amount",
    ["0", "-5", "1.001", "nan"],
)
def test_invalid_payment_amount(
    sample_invoice,
    invalid_amount,
):
    db_path, invoice_id = sample_invoice

    with pytest.raises(ValueError):
        register_payment(
            invoice_id,
            invalid_amount,
            "2026-11-18",
            "Cash",
            db_path=db_path,
        )
