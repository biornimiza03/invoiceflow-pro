
from pathlib import Path

import pandas as pd


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_INVOICE_ROWS = 10_000

REQUIRED_COLUMNS = {
    "invoice_number",
    "supplier",
    "invoice_date",
    "due_date",
    "currency",
    "subtotal",
    "vat_rate",
    "total",
    "payment_status",
}


def read_invoice_file(uploaded_file):
    """Read and check an uploaded invoice spreadsheet."""

    extension = Path(uploaded_file.name).suffix.lower()

    # 1. Check file extension
    if extension not in {".csv", ".xlsx"}:
        raise ValueError(
            "Unsupported file format. Use CSV or XLSX."
        )

    # 2. Check file size before reading
    file_size = uploaded_file.getbuffer().nbytes

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            "File is too large. Maximum size is 5 MB."
        )

    if file_size == 0:
        raise ValueError("The uploaded file is empty.")

    # Start reading from the beginning
    uploaded_file.seek(0)

    # 3. Read CSV or Excel
    try:
        if extension == ".csv":
            data = pd.read_csv(
                uploaded_file,
                dtype=str,
                encoding="utf-8-sig",
                keep_default_na=False,
                nrows=MAX_INVOICE_ROWS + 1,
            )
        else:
            data = pd.read_excel(
                uploaded_file,
                dtype=str,
                keep_default_na=False,
                nrows=MAX_INVOICE_ROWS + 1,
            )

    except pd.errors.EmptyDataError as error:
        raise ValueError(
            "The file does not contain a valid table."
        ) from error

    # 4. Normalize column names
    data.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in data.columns
    ]

    # 5. Check duplicate column names
    if data.columns.duplicated().any():
        raise ValueError(
            "Duplicate column names found."
        )

    # 6. Check required columns
    missing = REQUIRED_COLUMNS - set(data.columns)

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing))
        )

    # 7. Check number of invoice rows
    if len(data) > MAX_INVOICE_ROWS:
        raise ValueError(
            f"Too many invoices. Maximum is {MAX_INVOICE_ROWS}."
        )

    if data.empty:
        raise ValueError(
            "The file contains no invoice rows."
        )

    return data
