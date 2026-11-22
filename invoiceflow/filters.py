
import pandas as pd


def filter_invoices(
    data: pd.DataFrame,
    supplier="All suppliers",
    currency="All currencies",
    payment_status="All payments",
    validation_status="All statuses",
) -> pd.DataFrame:
    result = data.copy()

    if supplier != "All suppliers":
        result = result[
            result["supplier"]
            .fillna("")
            .str.strip()
            .str.casefold() == supplier.casefold()
        ]

    if currency != "All currencies":
        result = result[
            result["currency"]
            .fillna("")
            .str.strip()
            .str.casefold() == currency.casefold()
        ]

    if payment_status != "All payments":
        result = result[
            result["payment_status"]
            .fillna("")
            .str.strip()
            .str.casefold() == payment_status.casefold()
        ]

    if validation_status != "All statuses":
        result = result[
            result["validation_status"]
            .fillna("")
            .str.strip()
            .str.casefold() == validation_status.casefold()
        ]

    return result
