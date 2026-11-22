
import sqlite3
from contextlib import closing

from invoiceflow.database import DB_PATH
from invoiceflow.invoice_store import (
    CURRENCIES,
    initialize_invoice_store,
)
from invoiceflow.payments import initialize_payment_store


# =====================================================
# 1. ACTIVE CURRENCIES
# =====================================================

def list_active_currencies(db_path=DB_PATH):
    """
    Return currencies used by active saved invoices.
    """

    initialize_invoice_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT currency
            FROM invoices
            WHERE is_active = 1
            ORDER BY currency
            """
        ).fetchall()

    return [row[0] for row in rows]


# =====================================================
# 2. FINANCIAL DASHBOARD SUMMARY
# =====================================================

def get_saved_dashboard_summary(currency, db_path=DB_PATH):
    """
    Calculate financial metrics for one currency.

    Includes:
    - Number of active invoices
    - Total sales invoiced
    - Total purchases invoiced
    - Outstanding sales balance
    - Outstanding purchases balance
    - Monthly sales and purchases
    """

    if currency not in CURRENCIES:
        raise ValueError("Unsupported currency.")

    # Initialize invoices AND payments tables.
    # This fixes the missing payments table error.
    initialize_payment_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        # ============================================
        # FINANCIAL METRICS
        # ============================================

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS invoice_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN i.invoice_type = 'Sale'
                            THEN i.total_cents
                            ELSE 0
                        END
                    ),
                    0
                ) AS sales_cents,

                COALESCE(
                    SUM(
                        CASE
                            WHEN i.invoice_type = 'Purchase'
                            THEN i.total_cents
                            ELSE 0
                        END
                    ),
                    0
                ) AS purchases_cents,

                COALESCE(
                    SUM(
                        CASE
                            WHEN i.invoice_type = 'Sale'
                            THEN i.total_cents
                                 - COALESCE(p.paid_cents, 0)
                            ELSE 0
                        END
                    ),
                    0
                ) AS unpaid_sales_cents,

                COALESCE(
                    SUM(
                        CASE
                            WHEN i.invoice_type = 'Purchase'
                            THEN i.total_cents
                                 - COALESCE(p.paid_cents, 0)
                            ELSE 0
                        END
                    ),
                    0
                ) AS unpaid_purchases_cents

            FROM invoices AS i

            LEFT JOIN (
                SELECT
                    invoice_id,
                    SUM(amount_cents) AS paid_cents
                FROM payments
                GROUP BY invoice_id
            ) AS p
                ON p.invoice_id = i.id

            WHERE
                i.is_active = 1
                AND i.currency = ?
            """,
            (currency,),
        ).fetchone()

        # ============================================
        # MONTHLY FINANCIAL ANALYTICS
        # ============================================

        monthly = connection.execute(
            """
            SELECT
                substr(invoice_date, 1, 7) AS month,

                COALESCE(
                    SUM(
                        CASE
                            WHEN invoice_type = 'Sale'
                            THEN total_cents
                            ELSE 0
                        END
                    ),
                    0
                ) AS sales_cents,

                COALESCE(
                    SUM(
                        CASE
                            WHEN invoice_type = 'Purchase'
                            THEN total_cents
                            ELSE 0
                        END
                    ),
                    0
                ) AS purchases_cents

            FROM invoices

            WHERE
                is_active = 1
                AND currency = ?

            GROUP BY substr(invoice_date, 1, 7)
            ORDER BY month
            """,
            (currency,),
        ).fetchall()

    # ================================================
    # PREPARE RESULTS FOR STREAMLIT
    # ================================================

    result = dict(summary)

    result["months"] = [
        dict(row)
        for row in monthly
    ]

    return result
