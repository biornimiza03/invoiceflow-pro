
from io import BytesIO

import pandas as pd
from openpyxl.styles import Font, PatternFill


def prepare_export_data(data):
    """Make spreadsheet text safe for export."""
    result = data.copy()

    for column in result.columns:
        result[column] = result[column].map(
            lambda value: (
                "'" + value
                if isinstance(value, str)
                and value.lstrip().startswith(("=", "+", "-", "@"))
                else value
            )
        )

    return result


def build_excel_report(data):
    """Create a formatted Excel report in memory."""

    valid = data[data["validation_status"] == "Valid"]
    review = data[data["validation_status"] == "Needs review"]

    summary = pd.DataFrame({
        "Metric": [
            "Total Invoices",
            "Valid Invoices",
            "Needs Review",
        ],
        "Value": [
            len(data),
            len(valid),
            len(review),
        ],
    })

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sheets = {
            "Summary": summary,
            "All Invoices": prepare_export_data(data),
            "Valid Invoices": prepare_export_data(valid),
            "Needs Review": prepare_export_data(review),
        }

        for sheet_name, frame in sheets.items():
            frame.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"

            for cell in sheet[1]:
                cell.font = Font(
                    bold=True,
                    color="FFFFFF",
                )
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor="17365D",
                )

            if sheet.max_row > 1:
                sheet.auto_filter.ref = sheet.dimensions

            for column_cells in sheet.columns:
                letter = column_cells[0].column_letter
                longest = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )

                sheet.column_dimensions[letter].width = min(
                    max(longest + 2, 14),
                    50,
                )

    return output.getvalue()


def build_csv_report(data):
    """Create a CSV report."""
    safe_data = prepare_export_data(data)

    return safe_data.to_csv(
        index=False,
    ).encode("utf-8-sig")
