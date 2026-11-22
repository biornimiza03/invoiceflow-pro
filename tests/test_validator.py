
from pathlib import Path

import pandas as pd

from invoiceflow.validator import validate_invoices


def test_sample_invoice_validation():
    file_path = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "sample_invoices.csv"
    )

    invoices = pd.read_csv(file_path, dtype=str)
    result = validate_invoices(invoices)

    assert len(result) == 5

    assert (
        result["validation_status"] == "Valid"
    ).sum() == 3

    assert (
        result["validation_status"] == "Needs review"
    ).sum() == 2

    assert "Duplicate invoice" in result.iloc[3]["validation_issues"]

    assert "Expected 120.00" in result.iloc[4]["validation_issues"]
