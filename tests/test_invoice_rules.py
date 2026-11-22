
import pandas as pd
import pytest

from invoiceflow.validator import validate_invoices


BASE_INVOICE = {
    "invoice_number": "INV-100",
    "supplier": "Test Company",
    "invoice_date": "2026-11-10",
    "due_date": "2026-11-20",
    "currency": "EUR",
    "subtotal": "100",
    "vat_rate": "20",
    "total": "120",
    "payment_status": "unpaid",
}


def test_valid_invoice():
    result = validate_invoices(
        pd.DataFrame([BASE_INVOICE])
    )

    assert result.iloc[0]["validation_status"] == "Valid"


@pytest.mark.parametrize(
    "changes, expected_issue",
    [
        (
            {"invoice_date": "2026-02-30"},
            "Invalid invoice_date",
        ),
        (
            {"due_date": "2026-11-01"},
            "Due date is before invoice date",
        ),
        (
            {"currency": "XYZ"},
            "Unsupported currency",
        ),
        (
            {"payment_status": "pending"},
            "Invalid payment_status",
        ),
        (
            {"vat_rate": "110"},
            "Invalid financial value",
        ),
        (
            {"supplier": ""},
            "Missing supplier",
        ),
    ],
)
def test_invalid_invoices(changes, expected_issue):
    invoice = BASE_INVOICE.copy()
    invoice.update(changes)

    result = validate_invoices(
        pd.DataFrame([invoice])
    )

    assert (
        result.iloc[0]["validation_status"]
        == "Needs review"
    )

    assert expected_issue in result.iloc[0]["validation_issues"]
