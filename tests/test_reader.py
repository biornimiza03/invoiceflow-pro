
from io import BytesIO
from pathlib import Path

import pytest

import invoiceflow.reader as reader


SAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "sample_data"
    / "sample_invoices.csv"
)


def make_upload(content, filename="invoices.csv"):
    file = BytesIO(content)
    file.name = filename
    return file


def test_valid_csv():
    file = make_upload(
        SAMPLE_PATH.read_bytes()
    )

    result = reader.read_invoice_file(file)

    assert len(result) == 5


def test_unsupported_format():
    file = make_upload(
        b"some data",
        filename="invoices.txt",
    )

    with pytest.raises(ValueError, match="Unsupported"):
        reader.read_invoice_file(file)


def test_missing_columns():
    file = make_upload(
        b"invoice_number,supplier\nINV-001,ABC\n"
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        reader.read_invoice_file(file)


def test_file_size_limit(monkeypatch):
    monkeypatch.setattr(
        reader,
        "MAX_FILE_SIZE_BYTES",
        100,
    )

    file = make_upload(
        SAMPLE_PATH.read_bytes()
    )

    with pytest.raises(ValueError, match="too large"):
        reader.read_invoice_file(file)


def test_row_limit(monkeypatch):
    monkeypatch.setattr(
        reader,
        "MAX_INVOICE_ROWS",
        2,
    )

    file = make_upload(
        SAMPLE_PATH.read_bytes()
    )

    with pytest.raises(ValueError, match="Too many invoices"):
        reader.read_invoice_file(file)


def test_empty_file():
    file = make_upload(b"")

    with pytest.raises(ValueError, match="empty"):
        reader.read_invoice_file(file)
