
from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from invoiceflow.validator import validate_invoices
from invoiceflow.reporter import build_excel_report


def test_excel_report():
    file_path = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "sample_invoices.csv"
    )

    invoices = pd.read_csv(file_path, dtype=str)
    validated = validate_invoices(invoices)

    excel_bytes = build_excel_report(validated)

    workbook = load_workbook(
        BytesIO(excel_bytes),
        read_only=True,
        data_only=True,
    )

    assert workbook.sheetnames == [
        "Summary",
        "All Invoices",
        "Valid Invoices",
        "Needs Review",
    ]

    assert workbook["All Invoices"].max_row == 6
    assert workbook["Valid Invoices"].max_row == 4
    assert workbook["Needs Review"].max_row == 3

    workbook.close()
