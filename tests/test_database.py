
import pytest

from invoiceflow.database import (
    initialize_database,
    create_contact,
    list_contacts,
    update_contact,
    archive_contact,
    list_archived_contacts,
restore_contact,
)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.db"
    initialize_database(path)
    return path


def test_create_contact(database):
    create_contact(
        "Supplier",
        "Alpha Services",
        "alpha@example.com",
        db_path=database,
    )

    contacts = list_contacts(database)

    assert len(contacts) == 1
    assert contacts[0]["name"] == "Alpha Services"


def test_duplicate_contact(database):
    create_contact(
        "Customer",
        "Example Company",
        db_path=database,
    )

    with pytest.raises(ValueError, match="already exists"):
        create_contact(
            "Customer",
            "Example Company",
            db_path=database,
        )


def test_update_contact(database):
    contact_id = create_contact(
        "Supplier",
        "Original Name",
        db_path=database,
    )

    update_contact(
        contact_id,
        "Supplier",
        "Updated Name",
        db_path=database,
    )

    contacts = list_contacts(database)

    assert contacts[0]["name"] == "Updated Name"


def test_archive_contact(database):
    contact_id = create_contact(
        "Customer",
        "Test Customer",
        db_path=database,
    )

    archive_contact(contact_id, db_path=database)

    assert list_contacts(database) == []


def test_restore_archived_contact(database):
    contact_id = create_contact(
        "Customer",
        "Demo Retail Ltd",
        db_path=database,
    )

    # Archive the contact
    archive_contact(contact_id, db_path=database)

    assert len(list_contacts(database)) == 0
    assert len(list_archived_contacts(database)) == 1

    # Restore the contact
    restore_contact(contact_id, db_path=database)

    active = list_contacts(database)
    archived = list_archived_contacts(database)

    assert len(active) == 1
    assert len(archived) == 0
    assert active[0]["name"] == "Demo Retail Ltd"


def test_cannot_restore_active_contact(database):
    contact_id = create_contact(
        "Supplier",
        "Alpha Services",
        db_path=database,
    )

    with pytest.raises(
        ValueError,
        match="Archived contact not found",
    ):
        restore_contact(contact_id, db_path=database)
