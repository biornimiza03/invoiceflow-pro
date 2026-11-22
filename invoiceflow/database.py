
import sqlite3
from contextlib import closing
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "invoiceflow.db"
)

CONTACT_TYPES = ("Customer", "Supplier")


def initialize_database(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_type TEXT NOT NULL
                    CHECK(contact_type IN ('Customer', 'Supplier')),
                name TEXT NOT NULL COLLATE NOCASE,
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contact_type, name)
            )
        """)
        connection.commit()


def validate_contact(contact_type, name, email="", phone=""):
    name = name.strip()
    email = email.strip()
    phone = phone.strip()

    if contact_type not in CONTACT_TYPES:
        raise ValueError("Invalid contact type.")

    if not name:
        raise ValueError("Contact name is required.")

    if len(name) > 120 or len(email) > 254 or len(phone) > 40:
        raise ValueError("One or more fields are too long.")

    if email and (
        "@" not in email
        or " " in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise ValueError("Invalid email address.")

    return contact_type, name, email, phone


def create_contact(
    contact_type, name, email="", phone="", db_path=DB_PATH
):
    values = validate_contact(contact_type, name, email, phone)

    with closing(sqlite3.connect(db_path)) as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO contacts
                (contact_type, name, email, phone)
                VALUES (?, ?, ?, ?)
                """,
                values,
            )
            connection.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "This contact already exists for this type."
            ) from error


def list_contacts(db_path=DB_PATH):
    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, contact_type, name, email, phone
            FROM contacts
            WHERE is_active = 1
            ORDER BY contact_type, name
            """
        ).fetchall()

        return [dict(row) for row in rows]


def update_contact(
    contact_id, contact_type, name,
    email="", phone="", db_path=DB_PATH
):
    values = validate_contact(contact_type, name, email, phone)

    with closing(sqlite3.connect(db_path)) as connection:
        try:
            cursor = connection.execute(
                """
                UPDATE contacts
                SET contact_type = ?, name = ?, email = ?, phone = ?
                WHERE id = ? AND is_active = 1
                """,
                (*values, contact_id),
            )

            if cursor.rowcount == 0:
                raise ValueError("Contact not found.")

            connection.commit()

        except sqlite3.IntegrityError as error:
            raise ValueError(
                "This contact already exists for this type."
            ) from error


def archive_contact(contact_id, db_path=DB_PATH):
    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE contacts
            SET is_active = 0
            WHERE id = ? AND is_active = 1
            """,
            (contact_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError("Contact not found.")

        connection.commit()


def list_archived_contacts(db_path=DB_PATH):
    """Return all archived contacts."""

    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, contact_type, name, email, phone
            FROM contacts
            WHERE is_active = 0
            ORDER BY contact_type, name
            """
        ).fetchall()

        return [dict(row) for row in rows]


def restore_contact(contact_id, db_path=DB_PATH):
    """Restore an archived contact."""

    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE contacts
            SET is_active = 1
            WHERE id = ? AND is_active = 0
            """,
            (contact_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Archived contact not found."
            )

        connection.commit()
