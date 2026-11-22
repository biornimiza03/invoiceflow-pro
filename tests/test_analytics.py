
from decimal import Decimal
from pathlib import Path

import pandas as pd

from invoiceflow.analytics import build_currency_analytics
from invoiceflow.validator import validate_invoices


def load_sample():
    file_path = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "sample_invoices.csv"
    )

    invoices = pd.read_csv(file_path, dtype=str)

    return validate_invoices(invoices)


def test_financial_totals():
    validated = load_sample()

    result = build_currency_analytics(
        validated,
        "EUR",
    )

    assert result["count"] == 3
    assert result["total"] == Decimal("540")
    assert result["paid"] == Decimal("300")
    assert result["unpaid"] == Decimal("240")

    assert len(result["suppliers"]) == 3
    assert len(result["months"]) == 1


def test_currency_separation():
    validated = load_sample()

    usd_invoice = validated.iloc[[0]].copy()
    usd_invoice["invoice_number"] = "INV-USD"
    usd_invoice["currency"] = "USD"

    combined = pd.concat(
        [validated, usd_invoice],
        ignore_index=True,
    )

    eur = build_currency_analytics(
        combined,
        "EUR",
    )

    usd = build_currency_analytics(
        combined,
        "USD",
    )

    assert eur["total"] == Decimal("540")
    assert usd["total"] == Decimal("120")
