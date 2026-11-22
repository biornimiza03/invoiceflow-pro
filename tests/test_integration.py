
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from invoiceflow.reader import read_invoice_file
from invoiceflow.validator import validate_invoices
from invoiceflow.analytics import build_currency_analytics
from invoiceflow.reporter import (
    build_excel_report,
    build_csv_report,
)


SAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "sample_data"
    / "sample_invoices.csv"
)


def load_sample():
    return pd.read_csv(
        SAMPLE_PATH,
        dtype=str,
        keep_default_na=False,
    )


def create_csv_upload(data, filename):
    content = data.to_csv(index=False).encode("utf-8-sig")

    uploaded_file = BytesIO(content)
    uploaded_file.name = filename

    return uploaded_file


def test_excel_import():
    sample = load_sample()

    excel_file = BytesIO()

    sample.to_excel(
        excel_file,
        index=False,
        engine="openpyxl",
    )

    excel_file.seek(0)
    excel_file.name = "sample_invoices.xlsx"

    imported = read_invoice_file(excel_file)
    validated = validate_invoices(imported)

    assert len(imported) == 5

    assert (
        validated["validation_status"] == "Valid"
    ).sum() == 3

    assert (
        validated["validation_status"] == "Needs review"
    ).sum() == 2


def test_duplicates_across_files():
    sample = load_sample()

    first_file = create_csv_upload(
        sample.iloc[[0]],
        "file_a.csv",
    )

    second_file = create_csv_upload(
        sample.iloc[[0]],
        "file_b.csv",
    )

    first = read_invoice_file(first_file)
    second = read_invoice_file(second_file)

    first["source_file"] = "file_a.csv"
    second["source_file"] = "file_b.csv"

    combined = pd.concat(
        [first, second],
        ignore_index=True,
    )

    validated = validate_invoices(combined)

    assert len(validated) == 2

    assert validated.iloc[0]["validation_status"] == "Valid"

    assert (
        validated.iloc[1]["validation_status"]
        == "Needs review"
    )

    assert (
        "Duplicate invoice"
        in validated.iloc[1]["validation_issues"]
    )

    analytics = build_currency_analytics(
        validated,
        "EUR",
    )

    assert analytics["total"] == Decimal("120")


def test_spreadsheet_formula_protection():
    sample = load_sample().iloc[[0]].copy()

    sample.loc[sample.index[0], "supplier"] = "=1+1"

    validated = validate_invoices(sample)

    # Verify CSV export
    csv_content = build_csv_report(validated)

    csv_data = pd.read_csv(
        StringIO(csv_content.decode("utf-8-sig")),
        dtype=str,
        keep_default_na=False,
    )

    assert csv_data.iloc[0]["supplier"] == "'=1+1"

    # Verify Excel export
    excel_content = build_excel_report(validated)

    workbook = load_workbook(
        BytesIO(excel_content)
    )

    cell = workbook["All Invoices"]["B2"]

    assert cell.value == "'=1+1"
    assert cell.data_type != "f"

    workbook.close()
