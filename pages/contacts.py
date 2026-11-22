
"""InvoiceFlow Pro — premium Customers & Suppliers workspace.

UI only: contact validation and SQLite operations remain in invoiceflow.database.
"""

import hashlib
from html import escape

import streamlit as st

from invoiceflow.database import (
    archive_contact,
    create_contact,
    initialize_database,
    list_archived_contacts,
    list_contacts,
    restore_contact,
    update_contact,
)
from invoiceflow.hover_effects import apply_hover_effects


# ============================================================
# PAGE STYLES — SINGLE CSS BLOCK
# ============================================================

CONTACTS_CSS = """
<style>
/* Section headings */
.if-contact-heading { margin: 21px 0 15px; }
.if-contact-heading h3 { color:#1d3b49; font-size:19px; font-weight:760; margin:0 0 6px; }
.if-contact-heading p { color:#748895; font-size:12px; line-height:1.65; margin:0; }

/* Contact overview cards */
.if-contact-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:13px; margin:22px 0 27px; }
.if-contact-stat {
    min-width:0; padding:19px 20px; background:#fff; border:1px solid #dfe9e9;
    border-radius:16px; box-shadow:0 5px 18px rgba(18,55,60,.04);
}
.if-contact-stat.featured { background:linear-gradient(125deg,#155047,#09846a); border-color:transparent; }
.if-contact-stat-label { color:#718693; font-size:12px; font-weight:650; }
.if-contact-stat-value { color:#183543; font-size:29px; font-weight:800; line-height:1.15; margin:11px 0 8px; }
.if-contact-stat-note { color:#90a0a9; font-size:11px; line-height:1.5; }
.if-contact-stat.featured .if-contact-stat-label,
.if-contact-stat.featured .if-contact-stat-note { color:#d1f1e6; }
.if-contact-stat.featured .if-contact-stat-value { color:#fff; }

/* Premium tabs: same visual language as Payments */
[data-testid="stTabs"] [role="tablist"],
.stTabs [role="tablist"],
.stTabs [data-baseweb="tab-list"] {
    display:flex !important; align-items:center !important; flex-wrap:wrap !important;
    gap:9px !important; padding:7px 0 13px !important;
    border-bottom:none !important; background:transparent !important;
}
[data-testid="stTabs"] [data-testid="stTab"],
[data-testid="stTabs"] [role="tab"],
.stTabs [role="tab"],
.stTabs [data-baseweb="tab"] {
    box-sizing:border-box !important; display:inline-flex !important;
    align-items:center !important; justify-content:center !important;
    min-height:42px !important; padding:10px 17px !important;
    background:#fff !important; border:1px solid #dce8e4 !important;
    border-radius:10px !important; color:#45636c !important;
    font-size:13px !important; font-weight:600 !important;
    box-shadow:0 2px 8px rgba(20,60,60,.025) !important;
    transition:background-color .2s ease,border-color .2s ease,
               color .2s ease,box-shadow .2s ease !important;
}
[data-testid="stTabs"] [role="tab"] p,
[data-testid="stTabs"] [data-testid="stTab"] p,
.stTabs [role="tab"] p { color:inherit !important; font-size:inherit !important; font-weight:inherit !important; }
[data-testid="stTabs"] [data-testid="stTab"]:hover,
[data-testid="stTabs"] [role="tab"]:hover,
.stTabs [role="tab"]:hover,
.stTabs [data-baseweb="tab"]:hover {
    background:#e9f7f0 !important; border-color:#b3dcc9 !important; color:#087b61 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][data-selected],
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
[data-testid="stTabs"] [data-testid="stTab"][data-selected],
.stTabs [role="tab"][aria-selected="true"],
.stTabs [role="tab"][data-selected],
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background:#e5f5ec !important; border-color:#97cdb5 !important;
    color:#087b61 !important; font-weight:700 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none !important; }
[data-testid="stTabs"] [role="tab"]:focus-visible { outline:2px solid #0c9270 !important; outline-offset:2px; }

/* Panels and tables */
.st-key-contacts_add_panel,
.st-key-contacts_edit_panel,
.st-key-contacts_archive_panel,
.st-key-contacts_restore_panel {
    background:#fff !important; border:1px solid #dfe9e5 !important;
    border-radius:16px !important; padding:19px 22px !important;
    box-shadow:0 5px 18px rgba(18,55,60,.035);
}
[data-testid="stMain"] [data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
[data-testid="stMain"] [data-testid="stForm"] { border-radius:13px; }

/* Inline preview */
.if-contact-preview {
    display:flex; align-items:flex-start; justify-content:space-between; gap:16px;
    border:1px solid #dce9e5; background:linear-gradient(120deg,#fff,#f7fcfa);
    border-radius:15px; padding:18px 21px; margin:19px 0 7px;
}
.if-contact-preview-title { color:#193746; font-size:17px; font-weight:750; margin-bottom:7px; overflow-wrap:anywhere; }
.if-contact-preview-meta { color:#647e88; font-size:12px; line-height:1.8; overflow-wrap:anywhere; }
.if-contact-tag { display:inline-block; flex-shrink:0; border-radius:9px; padding:7px 11px;
    background:#e9f7f0; color:#087b61; font-size:12px; font-weight:700; }

/* Empty states and explanatory notes */
.if-contact-empty {
    display:flex; align-items:center; gap:16px; padding:23px;
    background:#fbfdfc; border:1px solid #dfeae7; border-radius:15px; margin:15px 0;
}
.if-contact-empty-icon { display:grid; place-items:center; flex-shrink:0;
    width:46px; height:46px; border-radius:13px; font-size:23px;
    background:#e9f7f0; color:#0b8968; }
.if-contact-empty-title { color:#193746; font-size:16px; font-weight:750; margin-bottom:6px; }
.if-contact-empty-description { color:#758b97; font-size:12px; line-height:1.65; }
.if-contact-note { padding:12px 15px; margin:14px 0;
    border-radius:11px; border:1px solid #dcece4; background:#f2faf6;
    color:#537b6e; font-size:12px; line-height:1.7; }

/* Secondary buttons */
[data-testid="stMain"] [data-testid="stDownloadButton"] button {
    background:#fff !important; color:#146b59 !important;
    border:1px solid #bfded2 !important; border-radius:10px !important;
    font-weight:650 !important;
    transition:background-color .2s ease,border-color .2s ease,color .2s ease !important;
}
[data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
    background:#e9f7f0 !important; border-color:#95cdb7 !important; color:#087b61 !important;
}

@media (max-width:1080px) { .if-contact-stats { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:600px) {
    .if-contact-stats { grid-template-columns:1fr; }
    .if-contact-preview { flex-direction:column; }
    .if-contact-empty { padding:17px; }
    .st-key-contacts_add_panel,
    .st-key-contacts_edit_panel,
    .st-key-contacts_archive_panel,
    .st-key-contacts_restore_panel { padding:16px !important; }
}
@media (prefers-reduced-motion:reduce) {
    [data-testid="stTabs"] [role="tab"],
    [data-testid="stMain"] [data-testid="stDownloadButton"] button { transition:none !important; }
}

/* ========================================
   PREMIUM ORANGE ARCHIVE BUTTON
======================================== */

[data-testid="stMain"]
.st-key-contacts_archive_button
[data-testid="stButton"] button,
[data-testid="stMain"]
.st-key-contacts_archive_button button {

    background: #FFF0DC !important;
    color: #9A5109 !important;

    border: 1px solid #EDB66F !important;
    border-radius: 10px !important;

    font-weight: 700 !important;

    box-shadow:
        0 3px 10px rgba(180, 110, 30, 0.06) !important;

    transition:
        background-color 0.2s ease,
        border-color 0.2s ease,
        color 0.2s ease,
        box-shadow 0.2s ease !important;
}

/* Hover — stronger orange */

[data-testid="stMain"]
.st-key-contacts_archive_button
[data-testid="stButton"] button:hover:not(:disabled),
[data-testid="stMain"]
.st-key-contacts_archive_button button:hover:not(:disabled) {

    background: #FFDCAB !important;
    color: #824000 !important;

    border-color: #DB933C !important;

    box-shadow:
        0 4px 13px rgba(180, 110, 30, 0.12) !important;
}

/* Keep button text orange */

[data-testid="stMain"]
.st-key-contacts_archive_button button p {

    color: inherit !important;
    font-weight: inherit !important;
}

/* Disabled — confirmation not checked */

[data-testid="stMain"]
.st-key-contacts_archive_button button:disabled {

    background: #F8F2E9 !important;
    border-color: #E6D9C7 !important;
    color: #A08E79 !important;

    box-shadow: none !important;
    cursor: not-allowed !important;
}

/* Respect reduced motion */

@media (prefers-reduced-motion: reduce) {
    .st-key-contacts_archive_button button {
        transition: none !important;
    }
}

</style>
"""


# ============================================================
# PRESENTATION HELPERS
# ============================================================

def heading(title, description):
    st.html(
        '<div class="if-contact-heading">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(description)}</p>'
        '</div>'
    )


def empty_state(title, description, symbol="▤"):
    st.html(
        '<div class="if-contact-empty">'
        f'<div class="if-contact-empty-icon" aria-hidden="true">{escape(symbol)}</div>'
        '<div>'
        f'<div class="if-contact-empty-title">{escape(title)}</div>'
        f'<div class="if-contact-empty-description">{escape(description)}</div>'
        '</div></div>'
    )


def overview_cards(active, archived):
    customers = sum(item["contact_type"] == "Customer" for item in active)
    suppliers = sum(item["contact_type"] == "Supplier" for item in active)
    values = [
        ("Active Contacts", len(active), "Available in your directory"),
        ("Customers", customers, "Active customer records"),
        ("Suppliers", suppliers, "Active supplier records"),
        ("Archived Contacts", len(archived), "Available for restoration"),
    ]

    blocks = []

    for index, (label, number, note) in enumerate(values):
        modifier = " featured" if index == 0 else ""

        blocks.append(
            f'<div class="if-contact-stat{modifier}">'
            f'<div class="if-contact-stat-label">{escape(label)}</div>'
            f'<div class="if-contact-stat-value">{number}</div>'
            f'<div class="if-contact-stat-note">{escape(note)}</div>'
            '</div>'
        )

    st.html(
        '<section class="if-contact-stats" aria-label="Contact overview">'
        + "".join(blocks)
        + '</section>'
    )


def display_table(contacts, *, key):
    """Render contact records; return selected row index or None."""

    records = [
        {
            "ID": item["id"],
            "Type": item["contact_type"],
            "Name": item["name"],
            "Email": item["email"] or "—",
            "Phone": item["phone"] or "—",
        }
        for item in contacts
    ]

    signature = "|".join(str(item["id"]) for item in contacts)

    signature_hash = hashlib.sha256(
        signature.encode("utf-8")
    ).hexdigest()[:12]

    event = st.dataframe(
        records,
        hide_index=True,
        width="stretch",
        row_height=39,
        on_select="rerun",
        selection_mode="single-row",
        key=f"{key}_{signature_hash}",
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Name": st.column_config.TextColumn("Contact Name", width="large"),
            "Email": st.column_config.TextColumn("Email", width="large"),
            "Phone": st.column_config.TextColumn("Phone", width="medium"),
        },
    )

    selected = event.selection.rows

    if selected and 0 <= selected[0] < len(contacts):
        return selected[0]

    return None


def contact_preview(contact):
    name = escape(str(contact["name"]))
    kind = escape(str(contact["contact_type"]))
    email = escape(str(contact.get("email") or "Not provided"))
    phone = escape(str(contact.get("phone") or "Not provided"))

    st.html(
        '<div class="if-contact-preview">'
        '<div>'
        f'<div class="if-contact-preview-title">{name}</div>'
        '<div class="if-contact-preview-meta">'
        f'Email: {email}<br>Phone: {phone}'
        '</div></div>'
        f'<span class="if-contact-tag">{kind}</span>'
        '</div>'
    )

    st.caption(
        "To update or archive this record, open the Manage Contacts tab."
    )


def reset_directory_filters():
    st.session_state["contacts_search"] = ""
    st.session_state["contacts_type_filter"] = "All"
    st.session_state["contacts_sort"] = "Name (A–Z)"


# ============================================================
# TAB 1 — ACTIVE DIRECTORY
# ============================================================

def render_directory(contacts):

    heading(
        "Contact Directory",
        "Search, review and organize your active business contacts.",
    )

    if not contacts:
        empty_state(
            "No active contacts",
            "Use Add Contact to create your first customer or supplier.",
        )
        return

    search_col, type_col, sort_col, reset_col = st.columns(
        [2.2, 1.1, 1.3, .8]
    )

    with search_col:
        search = st.text_input(
            "Search contacts",
            placeholder="Name, email or phone",
            key="contacts_search",
        ).strip().casefold()

    with type_col:
        contact_type = st.selectbox(
            "Contact type",
            ["All", "Customer", "Supplier"],
            key="contacts_type_filter",
        )

    with sort_col:
        sorting = st.selectbox(
            "Sort by",
            ["Name (A–Z)", "Name (Z–A)", "Newest added"],
            key="contacts_sort",
        )

    with reset_col:
        st.button(
            "Reset",
            key="contacts_reset_filters",
            on_click=reset_directory_filters,
            use_container_width=True,
        )

    filtered = [
        contact
        for contact in contacts
        if (
            contact_type == "All"
            or contact["contact_type"] == contact_type
        )
        and (
            not search
            or search in (
                f"{contact['name']} "
                f"{contact['email']} "
                f"{contact['phone']}"
            ).casefold()
        )
    ]

    if sorting == "Newest added":
        filtered.sort(
            key=lambda contact: contact["id"],
            reverse=True,
        )
    else:
        filtered.sort(
            key=lambda contact: str(contact["name"]).casefold(),
            reverse=sorting == "Name (Z–A)",
        )

    st.caption(
        f"Showing {len(filtered)} of {len(contacts)} active contacts"
    )

    if not filtered:
        empty_state(
            "No matching contacts",
            "Try another search or reset the filters.",
            "⌕",
        )
        return

    selected_index = display_table(
        filtered,
        key="contacts_active_table",
    )

    st.caption("Click a row to preview the contact details.")

    if selected_index is not None:
        contact_preview(filtered[selected_index])


# ============================================================
# TAB 2 — CREATE CONTACT
# ============================================================

def render_create_contact():

    heading(
        "Add Contact",
        "Create a new customer or supplier for your invoice workspace.",
    )

    with st.container(border=True, key="contacts_add_panel"):

        with st.form(
            "contacts_add_form",
            clear_on_submit=True,
        ):

            contact_type = st.selectbox(
                "Contact type",
                ["Customer", "Supplier"],
            )

            name = st.text_input(
                "Contact name",
                placeholder="Company or full name",
            )

            email_col, phone_col = st.columns(2)

            with email_col:
                email = st.text_input(
                    "Email (optional)",
                    placeholder="contact@example.com",
                )

            with phone_col:
                phone = st.text_input(
                    "Phone (optional)",
                    placeholder="+355 ...",
                )

            submitted = st.form_submit_button(
                "Save Contact",
                type="primary",
                use_container_width=True,
            )

    if submitted:

        try:
            create_contact(
                contact_type,
                name,
                email,
                phone,
            )

        except ValueError as error:
            st.error(str(error))

        else:
            st.session_state["contact_notice"] = (
                "Contact created successfully."
            )
            st.rerun()


# ============================================================
# TAB 3 — EDIT AND ARCHIVE
# ============================================================

def render_manage_contacts(contacts):

    heading(
        "Manage Contacts",
        "Update contact information or move a record to the archive.",
    )

    if not contacts:
        empty_state(
            "No contacts to manage",
            "Add a contact before editing or archiving.",
        )
        return

    labels = {
        contact["id"]: (
            f"{contact['name']} ({contact['contact_type']})"
        )
        for contact in contacts
    }

    edit_tab, archive_tab = st.tabs([
        "Edit Details",
        "Archive Contact",
    ])

    # --------------------------------------------------------
    # EDIT DETAILS
    # --------------------------------------------------------

    with edit_tab:

        selected_id = st.selectbox(
            "Select contact to edit",
            options=list(labels),
            format_func=lambda contact_id: labels[contact_id],
            key="contacts_edit_selected",
        )

        selected = next(
            item
            for item in contacts
            if item["id"] == selected_id
        )

        with st.container(
            border=True,
            key="contacts_edit_panel",
        ):

            with st.form(f"contacts_edit_form_{selected_id}"):

                edited_type = st.selectbox(
                    "Contact type",
                    ["Customer", "Supplier"],
                    index=(
                        0
                        if selected["contact_type"] == "Customer"
                        else 1
                    ),
                    key=f"contacts_edit_type_{selected_id}",
                )

                edited_name = st.text_input(
                    "Contact name",
                    value=selected["name"],
                    key=f"contacts_edit_name_{selected_id}",
                )

                edit_email_col, edit_phone_col = st.columns(2)

                with edit_email_col:
                    edited_email = st.text_input(
                        "Email (optional)",
                        value=selected["email"],
                        key=f"contacts_edit_email_{selected_id}",
                    )

                with edit_phone_col:
                    edited_phone = st.text_input(
                        "Phone (optional)",
                        value=selected["phone"],
                        key=f"contacts_edit_phone_{selected_id}",
                    )

                updated = st.form_submit_button(
                    "Save Changes",
                    type="primary",
                    use_container_width=True,
                )

        if updated:

            try:
                update_contact(
                    selected_id,
                    edited_type,
                    edited_name,
                    edited_email,
                    edited_phone,
                )

            except ValueError as error:
                st.error(str(error))

            else:
                st.session_state["contact_notice"] = (
                    "Contact updated successfully."
                )
                st.rerun()

    # --------------------------------------------------------
    # ARCHIVE CONTACT
    # --------------------------------------------------------

    with archive_tab:

        archive_id = st.selectbox(
            "Select contact to archive",
            options=list(labels),
            format_func=lambda contact_id: labels[contact_id],
            key="contacts_archive_selected",
        )

        with st.container(
            border=True,
            key="contacts_archive_panel",
        ):

            st.html(
                '<div class="if-contact-note">'
                'Archiving hides this contact from the active directory '
                'and from new invoice contact selection. '
                'Existing invoices remain stored, and the contact '
                'can be restored later.'
                '</div>'
            )

            confirmed = st.checkbox(
                "I understand this contact will be archived.",
                key=f"contacts_confirm_archive_{archive_id}",
            )

            archive_clicked = st.button(
                "Archive Contact",
                disabled=not confirmed,
                key="contacts_archive_button",
                use_container_width=True,
            )

        if archive_clicked:

            try:
                archive_contact(archive_id)

            except ValueError as error:
                st.error(str(error))

            else:
                st.session_state["contact_notice"] = (
                    "Contact archived successfully."
                )
                st.rerun()


# ============================================================
# TAB 4 — ARCHIVED CONTACTS & RESTORE
# ============================================================

def render_archived_contacts(archived):

    heading(
        "Archived Contacts",
        "Review inactive contacts and restore them when needed.",
    )

    if not archived:

        empty_state(
            "Your archive is empty",
            "Archived customers and suppliers will appear here.",
            "▤",
        )
        return

    st.html(
        '<div class="if-contact-preview">'
        '<div>'
        '<div class="if-contact-preview-title">'
        'Archived Contact Records'
        '</div>'
        '<div class="if-contact-preview-meta">'
        'Contacts stored safely and available for restoration.'
        '</div></div>'
        f'<span class="if-contact-tag">{len(archived)}</span>'
        '</div>'
    )

    display_table(
        archived,
        key="contacts_archived_table",
    )

    archived_labels = {
        item["id"]: (
            f"{item['name']} ({item['contact_type']})"
        )
        for item in archived
    }

    with st.container(
        border=True,
        key="contacts_restore_panel",
    ):

        st.markdown("**Restore a contact**")

        st.caption(
            "Return an archived contact to the active directory. "
            "Existing invoice links are preserved."
        )

        selected_id = st.selectbox(
            "Select contact to restore",
            options=list(archived_labels),
            format_func=lambda contact_id: archived_labels[contact_id],
            key="contacts_restore_selected",
        )

        restore_clicked = st.button(
            "Restore Contact",
            type="primary",
            key="contacts_restore_button",
            use_container_width=True,
        )

    if restore_clicked:

        try:
            restore_contact(selected_id)

        except ValueError as error:
            st.error(str(error))

        else:
            st.session_state["contact_notice"] = (
                "Contact restored successfully."
            )
            st.rerun()


# ============================================================
# PAGE INITIALIZATION
# ============================================================

initialize_database()
apply_hover_effects()
st.html(CONTACTS_CSS)

st.html("""
<div class="if-hero">
    <div class="if-hero-title">
        Customers & Suppliers
    </div>
    <div class="if-hero-description">
        Manage customers, suppliers and business
        contact records in one place.
    </div>
</div>
""")

notice = st.session_state.pop(
    "contact_notice",
    None,
)

if notice:
    st.success(notice)

active_contacts = list_contacts()
archived_contacts = list_archived_contacts()

overview_cards(
    active_contacts,
    archived_contacts,
)

# Streamlit tabs enable client-side switching.
directory_tab, add_tab, manage_tab, archived_tab = st.tabs([
    "Contact Directory",
    "Add Contact",
    "Manage Contacts",
    "Archived Contacts",
])

with directory_tab:
    render_directory(active_contacts)

with add_tab:
    render_create_contact()

with manage_tab:
    render_manage_contacts(active_contacts)

with archived_tab:
    render_archived_contacts(archived_contacts)
