
import streamlit as st
from invoiceflow.sidebar_styles import apply_sidebar_styles


st.set_page_config(
    page_title="InvoiceFlow Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom application styles
st.html("""



<style>
.if-kpi {
    background: #FFFFFF;
    border: 1px solid #E2E8EE;
    border-radius: 14px;
    padding: 22px;
    min-height: 125px;
    box-shadow: 0 3px 12px rgba(20, 40, 50, 0.04);
}

.if-kpi--primary {
    background: linear-gradient(125deg, #103F36, #176B55);
    border-color: transparent;
}

.if-kpi-label {
    color: #627484;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 12px;
}

.if-kpi-value {
    color: #152B39;
    font-size: 29px;
    font-weight: 750;
    line-height: 1.2;
}

.if-kpi--primary .if-kpi-label {
    color: #C8EAE0;
}

.if-kpi--primary .if-kpi-value {
    color: #FFFFFF;
}
.if-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0 6px;
}

.if-logo {
    background: #168D70;
    color: white;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 22px;
}

.if-brand-name {
    font-size: 23px;
    font-weight: 750;
    color: #FFFFFF;
}

.if-brand-description {
    color: #AABCCA;
    font-size: 11px;
    letter-spacing: 1px;
}

.if-hero {
    background: linear-gradient(110deg, #173B39, #126A58);
    border-radius: 18px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 24px;
}

.if-hero-title {
    font-size: 30px;
    font-weight: 750;
    margin-bottom: 8px;
}

.if-hero-description {
    font-size: 14px;
    color: #DAF5EA;
}
</style>
""")



# Register application pages
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True,
)

invoices_page = st.Page(
    "pages/invoices.py",
    title="Invoices",
    icon=":material/receipt_long:",
)

workspace_page = st.Page(
    "legacy_app.py",
    title="Upload & Validation",
    icon=":material/upload_file:",
)
contacts_page = st.Page(
    "pages/contacts.py",
    title="Customers & Suppliers",
    icon=":material/groups:",
)
saved_invoices_page = st.Page(
    "pages/saved_invoices.py",
    title="Saved Invoices",
    icon=":material/description:",
)
payments_page = st.Page(
    "pages/payments.py",
    title="Payments",
    icon=":material/payments:",
)

navigation = st.navigation(
    [
        dashboard_page,
        invoices_page,
        saved_invoices_page,
        payments_page,
        contacts_page,
        workspace_page,
    ],
    position="hidden",
)

# Build our own sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="if-brand">
            <div class="if-logo">F</div>
            <div>
                <div class="if-brand-name">InvoiceFlow</div>
                <div class="if-brand-description">PRO WORKSPACE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("WORKSPACE")

    
    
    st.page_link(
        dashboard_page,
        label="Dashboard",
        icon=":material/dashboard:",
        width="stretch",
    )

    st.page_link(
        invoices_page,
        label="Invoices",
        icon=":material/receipt_long:",
        width="stretch",
    )
     # NEW: Saved Invoices
   
    st.page_link(
        saved_invoices_page,
        label="Saved Invoices",
        icon=":material/description:",
        width="stretch",
    )

    st.page_link(
        payments_page,
        label="Payments",
        icon=":material/payments:",
        width="stretch",
    )

    st.page_link(
        contacts_page,
        label="Customers & Suppliers",
        icon=":material/groups:",
        width="stretch",
    )


    st.page_link(
        workspace_page,
        label="Upload & Validation",
        icon=":material/upload_file:",
        width="stretch",
    )



    st.divider()
    st.caption("W01 · Python & Streamlit")

apply_sidebar_styles()
navigation.run()
