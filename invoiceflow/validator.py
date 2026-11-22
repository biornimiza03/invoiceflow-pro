from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd

from invoiceflow.reader import REQUIRED_COLUMNS


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_invoice_date(value, field, issues):
    text = clean_text(value)

    if not text:
        return None

    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()

        if parsed.isoformat() != text:
            raise ValueError

        return parsed

    except ValueError:
        issues.append(
            f"Invalid {field}: expected YYYY-MM-DD"
        )
        return None



def validate_invoices(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()

    statuses = []
    descriptions = []
    seen_invoices = set()

    for _, row in result.iterrows():
        issues = []

        # 1. Check for missing information
        for column in sorted(REQUIRED_COLUMNS):
            if not clean_text(row[column]):
                issues.append(f"Missing {column}")

        # 2. Check for duplicate invoices
        number = clean_text(row["invoice_number"]).casefold()
        supplier = clean_text(row["supplier"]).casefold()

        if number and supplier:
            invoice_key = (supplier, number)

            if invoice_key in seen_invoices:
                issues.append("Duplicate invoice")
            else:
                seen_invoices.add(invoice_key)

        # Check invoice dates
        invoice_date = parse_invoice_date(
            row["invoice_date"],
            "invoice_date",
            issues,
        )

        due_date = parse_invoice_date(
            row["due_date"],
            "due_date",
            issues,
        )

        if invoice_date and due_date:
            if due_date < invoice_date:
                issues.append(
                    "Due date is before invoice date"
                )

        # Check currency
        currency = clean_text(row["currency"]).upper()

        if currency and currency not in {"EUR", "USD", "ALL"}:
            issues.append("Unsupported currency")

        # Check payment status
        payment_status = clean_text(
            row["payment_status"]
        ).lower()

        if payment_status and payment_status not in {
            "paid",
            "unpaid",
        }:
            issues.append("Invalid payment_status")



        # 3. Read financial values safely
        amounts = {}

        for column in ["subtotal", "vat_rate", "total"]:
            raw_value = clean_text(row[column])

            if not raw_value:
                continue

            try:
                amount = Decimal(raw_value)

                if not amount.is_finite():
                    raise InvalidOperation

                amounts[column] = amount

            except InvalidOperation:
                issues.append(f"Invalid number: {column}")

        # 4. Verify invoice total
        if len(amounts) == 3:
            subtotal = amounts["subtotal"]
            vat_rate = amounts["vat_rate"]
            total = amounts["total"]

            if (
                subtotal < 0
                or total < 0
                or not 0 <= vat_rate <= 100
            ):
                issues.append("Invalid financial value")
            else:
                expected_total = (
                    subtotal * (1 + vat_rate / 100)
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                actual_total = total.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                if actual_total != expected_total:
                    issues.append(
                        f"Incorrect total. Expected {expected_total}"
                    )

        statuses.append(
            "Needs review" if issues else "Valid"
        )

        descriptions.append(
            "; ".join(issues) if issues else "No issues"
        )

    result["validation_status"] = statuses
    result["validation_issues"] = descriptions

    return result
