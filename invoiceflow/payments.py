
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal, InvalidOperation

from invoiceflow.database import DB_PATH
from invoiceflow.invoice_store import initialize_invoice_store


PAYMENT_METHODS = (
    "Bank transfer",
    "Cash",
    "Card",
    "Other",
)


def initialize_payment_store(db_path=DB_PATH):
    """Create the payments table if it does not exist."""

    initialize_invoice_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL
                    REFERENCES invoices(id),
                amount_cents INTEGER NOT NULL
                    CHECK(amount_cents > 0),
                payment_date TEXT NOT NULL,
                method TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()


def amount_to_cents(amount):
    """Convert a monetary amount into integer cents."""

    try:
        value = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Invalid payment amount.") from error

    if not value.is_finite() or not (
        Decimal("0") < value <= Decimal("100000000")
    ):
        raise ValueError("Payment amount must be positive.")

    cents = value * 100

    if cents != cents.to_integral_value():
        raise ValueError(
            "Payment amount supports at most two decimals."
        )

    return int(cents)


def register_payment(
    invoice_id,
    amount,
    payment_date,
    method,
    note="",
    db_path=DB_PATH,
):
    """Register a payment without exceeding invoice total."""

    initialize_payment_store(db_path)

    cents = amount_to_cents(amount)

    try:
        paid_on = date.fromisoformat(str(payment_date))
    except ValueError as error:
        raise ValueError("Invalid payment date.") from error

    if paid_on.isoformat() != str(payment_date):
        raise ValueError("Use YYYY-MM-DD for payment date.")

    if method not in PAYMENT_METHODS:
        raise ValueError("Invalid payment method.")

    note = str(note).strip()

    if len(note) > 300:
        raise ValueError("Payment note is too long.")

    with closing(sqlite3.connect(db_path, timeout=10)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # Lock the database for this short transaction.
        connection.execute("BEGIN IMMEDIATE")

        invoice = connection.execute(
            """
            SELECT total_cents, is_active, invoice_date
            FROM invoices
            WHERE id = ?
            """,
            (invoice_id,),
        ).fetchone()

        if not invoice or invoice[1] != 1:
            raise ValueError("Active invoice not found.")

        if paid_on < date.fromisoformat(invoice[2]):
            raise ValueError(
                "Payment date cannot precede invoice date."
            )

        already_paid = connection.execute(
            """
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM payments
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        ).fetchone()[0]

        remaining = invoice[0] - already_paid

        if remaining <= 0:
            raise ValueError("Invoice is already fully paid.")

        if cents > remaining:
            raise ValueError(
                "Payment exceeds the remaining balance."
            )

        cursor = connection.execute(
            """
            INSERT INTO payments (
                invoice_id, amount_cents,
                payment_date, method, note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                invoice_id,
                cents,
                paid_on.isoformat(),
                method,
                note,
            ),
        )

        new_paid = already_paid + cents

        status = (
            "paid"
            if new_paid == invoice[0]
            else "partial"
        )

        connection.execute(
            """
            UPDATE invoices
            SET payment_status = ?
            WHERE id = ?
            """,
            (status, invoice_id),
        )

        connection.commit()
        return cursor.lastrowid


def list_invoice_balances(db_path=DB_PATH):
    """Return paid and remaining amounts for active invoices."""

    initialize_payment_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                i.id,
                i.invoice_number,
                i.invoice_type,
                c.name AS contact,
                i.currency,
                i.due_date,
                i.total_cents,
                COALESCE(p.paid_cents, 0) AS paid_cents,
                i.total_cents
                    - COALESCE(p.paid_cents, 0)
                    AS remaining_cents,
                i.payment_status
            FROM invoices AS i
            JOIN contacts AS c
                ON c.id = i.contact_id
            LEFT JOIN (
                SELECT
                    invoice_id,
                    SUM(amount_cents) AS paid_cents
                FROM payments
                GROUP BY invoice_id
            ) AS p
                ON p.invoice_id = i.id
            WHERE i.is_active = 1
            ORDER BY i.id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def list_payment_history(db_path=DB_PATH):
    """Return recorded payments, including archived invoices."""

    initialize_payment_store(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                p.id,
                i.invoice_number,
                c.name AS contact,
                i.currency,
                p.amount_cents,
                p.payment_date,
                p.method,
                p.note
            FROM payments AS p
            JOIN invoices AS i
                ON i.id = p.invoice_id
            JOIN contacts AS c
                ON c.id = i.contact_id
            ORDER BY p.payment_date DESC, p.id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
