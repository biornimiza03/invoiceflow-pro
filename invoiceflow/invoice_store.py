
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from invoiceflow.database import DB_PATH, initialize_database


# =====================================================
# 1. CONSTANTS
# =====================================================

CURRENCIES = ("EUR", "USD", "ALL")
INVOICE_TYPES = ("Purchase", "Sale")


# =====================================================
# 2. DATABASE INITIALIZATION
# =====================================================

def initialize_invoice_store(db_path=DB_PATH):
    """
    Initialize the invoice database.

    Creates the invoice table and applies the
    archive-column migration when necessary.
    """

    initialize_database(db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                invoice_type TEXT NOT NULL
                    CHECK(invoice_type IN ('Purchase', 'Sale')),

                invoice_number TEXT NOT NULL,

                contact_id INTEGER NOT NULL
                    REFERENCES contacts(id),

                invoice_date TEXT NOT NULL,

                due_date TEXT NOT NULL,

                currency TEXT NOT NULL
                    CHECK(currency IN ('EUR', 'USD', 'ALL')),

                subtotal_cents INTEGER NOT NULL
                    CHECK(subtotal_cents > 0),

                vat_rate_bps INTEGER NOT NULL
                    CHECK(vat_rate_bps BETWEEN 0 AND 10000),

                total_cents INTEGER NOT NULL
                    CHECK(total_cents >= 0),

                payment_status TEXT NOT NULL
                    DEFAULT 'unpaid',

                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(
                    invoice_type,
                    contact_id,
                    invoice_number
                )
            )
        """)

        # Migration for databases created before
        # the archive functionality was introduced.

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(invoices)"
            ).fetchall()
        }

        if "is_active" not in columns:
            connection.execute(
                "ALTER TABLE invoices "
                "ADD COLUMN is_active INTEGER NOT NULL "
                "DEFAULT 1 CHECK(is_active IN (0, 1))"
            )

        connection.commit()


# =====================================================
# 3. FINANCIAL CALCULATIONS
# =====================================================

def calculate_amounts(subtotal, vat_rate):
    """
    Calculate subtotal, VAT and invoice total
    using Decimal for financial precision.
    """

    try:
        amount = Decimal(str(subtotal).strip())
        rate = Decimal(str(vat_rate).strip())

    except (InvalidOperation, ValueError) as error:
        raise ValueError(
            "Subtotal and VAT must be numeric."
        ) from error

    if not amount.is_finite() or not (
        Decimal("0") < amount <= Decimal("100000000")
    ):
        raise ValueError(
            "Subtotal must be between 0 and 100,000,000."
        )

    if not rate.is_finite() or not (
        Decimal("0") <= rate <= Decimal("100")
    ):
        raise ValueError(
            "VAT must be between 0 and 100 percent."
        )

    if (
        amount * 100
        != (amount * 100).to_integral_value()
    ):
        raise ValueError(
            "Subtotal supports at most two decimal places."
        )

    if (
        rate * 100
        != (rate * 100).to_integral_value()
    ):
        raise ValueError(
            "VAT supports at most two decimal places."
        )

    subtotal_cents = int(amount * 100)
    vat_rate_bps = int(rate * 100)

    total_cents = int(
        (
            Decimal(subtotal_cents)
            * (Decimal("1") + rate / 100)
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )

    return subtotal_cents, vat_rate_bps, total_cents


# =====================================================
# 4. DATE VALIDATION
# =====================================================

def parse_date(value, field):
    """
    Validate invoice dates in YYYY-MM-DD format.
    """

    text = str(value).strip()

    try:
        parsed = date.fromisoformat(text)

    except ValueError as error:
        raise ValueError(
            f"Invalid {field}; use YYYY-MM-DD."
        ) from error

    if parsed.isoformat() != text:
        raise ValueError(
            f"Invalid {field}; use YYYY-MM-DD."
        )

    return parsed


# =====================================================
# 5. CREATE SAVED INVOICE
# =====================================================

def create_saved_invoice(
    invoice_type,
    contact_id,
    invoice_number,
    invoice_date,
    due_date,
    currency,
    subtotal,
    vat_rate,
    db_path=DB_PATH,
):
    """
    Create a new invoice linked to an active
    customer or supplier.
    """

    if invoice_type not in INVOICE_TYPES:
        raise ValueError("Invalid invoice type.")

    number = str(invoice_number).strip()

    if not number or len(number) > 60:
        raise ValueError(
            "Invoice number must contain 1–60 characters."
        )

    currency = str(currency).strip().upper()

    if currency not in CURRENCIES:
        raise ValueError("Unsupported currency.")

    issued = parse_date(
        invoice_date,
        "invoice date",
    )

    due = parse_date(
        due_date,
        "due date",
    )

    if due < issued:
        raise ValueError(
            "Due date cannot be before invoice date."
        )

    cents, bps, total_cents = calculate_amounts(
        subtotal,
        vat_rate,
    )

    expected_type = (
        "Customer"
        if invoice_type == "Sale"
        else "Supplier"
    )

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        contact = connection.execute(
            """
            SELECT contact_type, is_active
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        if (
            not contact
            or contact[1] != 1
            or contact[0] != expected_type
        ):
            raise ValueError(
                f"Select an active {expected_type.lower()}."
            )

        try:
            cursor = connection.execute(
                """
                INSERT INTO invoices (
                    invoice_type,
                    contact_id,
                    invoice_number,
                    invoice_date,
                    due_date,
                    currency,
                    subtotal_cents,
                    vat_rate_bps,
                    total_cents
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_type,
                    contact_id,
                    number,
                    issued.isoformat(),
                    due.isoformat(),
                    currency,
                    cents,
                    bps,
                    total_cents,
                ),
            )

            connection.commit()

            return cursor.lastrowid

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Duplicate invoice number for this contact and type."
            ) from error


# =====================================================
# 6. LIST ACTIVE AND ARCHIVED INVOICES
# =====================================================

def list_saved_invoices(db_path=DB_PATH, archived=False):
    """
    Return saved invoice records.

    archived=False -> active invoices
    archived=True  -> archived invoices
    """

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                i.id,
                i.invoice_type,
                i.invoice_number,
                c.name AS contact,
                i.invoice_date,
                i.due_date,
                i.currency,
                i.subtotal_cents,
                i.vat_rate_bps,
                i.total_cents,
                i.payment_status

            FROM invoices AS i

            JOIN contacts AS c
                ON c.id = i.contact_id

            WHERE i.is_active = ?

            ORDER BY i.id DESC
            """,
            (0 if archived else 1,),
        ).fetchall()

    return [
        {
            "ID": row["id"],
            "Type": row["invoice_type"],
            "Invoice": row["invoice_number"],
            "Contact": row["contact"],
            "Issued": row["invoice_date"],
            "Due": row["due_date"],
            "Currency": row["currency"],
            "Subtotal": (
                f"{Decimal(row['subtotal_cents']) / 100:.2f}"
            ),
            "VAT %": (
                f"{Decimal(row['vat_rate_bps']) / 100:.2f}"
            ),
            "Total": (
                f"{Decimal(row['total_cents']) / 100:.2f}"
            ),
            "Payment": row["payment_status"],
        }
        for row in rows
    ]


def list_archived_invoices(db_path=DB_PATH):
    """
    Return invoices that have been archived.
    """

    return list_saved_invoices(
        db_path=db_path,
        archived=True,
    )


# =====================================================
# 7. ARCHIVE INVOICE
# =====================================================

def archive_saved_invoice(invoice_id, db_path=DB_PATH):
    """
    Archive an active invoice without deleting it.
    """

    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE invoices
            SET is_active = 0
            WHERE id = ?
              AND is_active = 1
            """,
            (invoice_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Active invoice not found."
            )

        connection.commit()


# =====================================================
# 8. RESTORE ARCHIVED INVOICE
# =====================================================

def restore_saved_invoice(invoice_id, db_path=DB_PATH):
    """
    Restore an archived invoice.
    """

    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE invoices
            SET is_active = 1
            WHERE id = ?
              AND is_active = 0
            """,
            (invoice_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Archived invoice not found."
            )

        connection.commit()


# =====================================================
# 9. UPDATE SAVED INVOICE — FINANCIALLY SAFE
# =====================================================

def update_saved_invoice(
    invoice_id,
    invoice_number,
    invoice_date,
    due_date,
    currency,
    subtotal,
    vat_rate,
    db_path=DB_PATH,
):
    """
    Safely update an active invoice.

    Prevents:
    - Reducing total below recorded payments
    - Changing currency after payments
    - Changing invoice number after payments
    - Moving invoice date after existing payments

    Recalculates the invoice payment status.
    """

    # Local import prevents circular imports.
    from invoiceflow.payments import initialize_payment_store

    number = str(invoice_number).strip()
    currency = str(currency).strip().upper()

    # -----------------------------------------------
    # VALIDATE INVOICE NUMBER
    # -----------------------------------------------

    if not number or len(number) > 60:
        raise ValueError(
            "Invoice number must contain 1–60 characters."
        )

    # -----------------------------------------------
    # VALIDATE CURRENCY
    # -----------------------------------------------

    if currency not in CURRENCIES:
        raise ValueError("Unsupported currency.")

    # -----------------------------------------------
    # VALIDATE DATES
    # -----------------------------------------------

    issued = parse_date(
        invoice_date,
        "invoice date",
    )

    due = parse_date(
        due_date,
        "due date",
    )

    if due < issued:
        raise ValueError(
            "Due date cannot be before invoice date."
        )

    # -----------------------------------------------
    # RECALCULATE FINANCIAL VALUES
    # -----------------------------------------------

    cents, bps, total_cents = calculate_amounts(
        subtotal,
        vat_rate,
    )

    # Ensure invoice and payment tables exist.
    initialize_payment_store(db_path)

    with closing(
        sqlite3.connect(db_path, timeout=10)
    ) as connection:

        # Lock the transaction while checking balances.
        connection.execute("BEGIN IMMEDIATE")

        # -------------------------------------------
        # LOAD EXISTING INVOICE AND PAYMENT DATA
        # -------------------------------------------

        existing = connection.execute(
            """
            SELECT
                i.invoice_number,
                i.currency,

                COALESCE(
                    SUM(p.amount_cents),
                    0
                ) AS paid_cents,

                MIN(p.payment_date) AS first_payment

            FROM invoices AS i

            LEFT JOIN payments AS p
                ON p.invoice_id = i.id

            WHERE
                i.id = ?
                AND i.is_active = 1

            GROUP BY i.id
            """,
            (invoice_id,),
        ).fetchone()

        if existing is None:
            raise ValueError(
                "Active invoice not found."
            )

        (
            old_number,
            old_currency,
            paid_cents,
            first_payment,
        ) = existing

        # -------------------------------------------
        # PREVENT INVALID FINANCIAL CHANGES
        # -------------------------------------------

        if total_cents < paid_cents:
            raise ValueError(
                "New invoice total cannot be below "
                "amount already paid."
            )

        # Extra restrictions when payments exist.
        if paid_cents > 0:

            if currency != old_currency:
                raise ValueError(
                    "Cannot change currency after payments "
                    "have been recorded."
                )

            if number != old_number:
                raise ValueError(
                    "Cannot change invoice number after payments "
                    "have been recorded."
                )

            if issued > date.fromisoformat(first_payment):
                raise ValueError(
                    "Invoice date cannot be after an "
                    "existing payment date."
                )

        # -------------------------------------------
        # RECALCULATE PAYMENT STATUS
        # -------------------------------------------

        if paid_cents == 0:
            status = "unpaid"

        elif paid_cents == total_cents:
            status = "paid"

        else:
            status = "partial"

        # -------------------------------------------
        # UPDATE INVOICE IN DATABASE
        # -------------------------------------------

        try:
            cursor = connection.execute(
                """
                UPDATE invoices

                SET
                    invoice_number = ?,
                    invoice_date = ?,
                    due_date = ?,
                    currency = ?,
                    subtotal_cents = ?,
                    vat_rate_bps = ?,
                    total_cents = ?,
                    payment_status = ?

                WHERE
                    id = ?
                    AND is_active = 1
                """,
                (
                    number,
                    issued.isoformat(),
                    due.isoformat(),
                    currency,
                    cents,
                    bps,
                    total_cents,
                    status,
                    invoice_id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Active invoice not found."
                )

            connection.commit()

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Duplicate invoice number for this contact and type."
            ) from error
