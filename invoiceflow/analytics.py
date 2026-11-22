
from decimal import Decimal

import pandas as pd


def build_currency_analytics(data, currency):
    # Only approved invoices are included
    valid = data.loc[
        data["validation_status"] == "Valid"
    ].copy()

    valid["currency"] = (
        valid["currency"].str.strip().str.upper()
    )

    valid = valid.loc[
        valid["currency"] == currency
    ].copy()

    if valid.empty:
        return None

    # Preserve precision for financial calculations
    valid["amount"] = valid["total"].map(
        lambda value: Decimal(str(value).strip())
    )

    valid["payment_status"] = (
        valid["payment_status"].str.strip().str.lower()
    )

    valid["supplier"] = valid["supplier"].str.strip()

    valid["month"] = pd.to_datetime(
        valid["invoice_date"],
        format="%Y-%m-%d",
    ).dt.strftime("%Y-%m")

    total = sum(valid["amount"], Decimal("0"))

    paid = sum(
        valid.loc[
            valid["payment_status"] == "paid",
            "amount",
        ],
        Decimal("0"),
    )

    unpaid = sum(
        valid.loc[
            valid["payment_status"] == "unpaid",
            "amount",
        ],
        Decimal("0"),
    )

    # Group totals by supplier
    suppliers = (
        valid.groupby("supplier", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total"})
        .sort_values("supplier")
    )

    # Group totals by month
    months = (
        valid.groupby("month", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total"})
        .sort_values("month")
    )

    # Charts need numeric values
    # Decimal remains the source for exact financial totals
    suppliers["total"] = suppliers["total"].astype(float)
    months["total"] = months["total"].astype(float)

    return {
        "count": len(valid),
        "total": total,
        "paid": paid,
        "unpaid": unpaid,
        "suppliers": suppliers,
        "months": months,
    }
