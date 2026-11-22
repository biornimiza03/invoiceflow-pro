
from pathlib import Path

import pandas as pd

from invoiceflow.filters import filter_invoices
from invoiceflow.validator import validate_invoices


def get_sample_data():
    path = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "sample_invoices.csv"
    )

    invoices = pd.read_csv(path, dtype=str)
    return validate_invoices(invoices)


def test_no_filters():
    data = get_sample_data()

    result = filter_invoices(data)

    assert len(result) == 5


def test_supplier_filter():
    data = get_sample_data()

    result = filter_invoices(
        data,
        supplier="Beta Group",
    )

    assert len(result) == 2
    assert all(result["supplier"] == "Beta Group")


def test_combined_filters():
    data = get_sample_data()

    result = filter_invoices(
        data,
        supplier="Beta Group",
        payment_status="unpaid",
        validation_status="Needs review",
    )

    assert len(result) == 1
    assert result.iloc[0]["invoice_number"] == "INV-002"
    assert result.iloc[0]["validation_status"] == "Needs review"
