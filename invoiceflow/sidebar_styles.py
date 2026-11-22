
"""Premium sidebar styling for InvoiceFlow Pro."""

import streamlit as st


SIDEBAR_CSS = """
<style>

/* =========================================
   SIDEBAR — PREMIUM NAVIGATION
========================================= */

/* Brand spacing */

[data-testid="stSidebar"] .if-brand {
    margin: 18px 0 22px !important;
    gap: 13px !important;
}

[data-testid="stSidebar"] .if-brand-name {
    font-size: 23px !important;
    font-weight: 800 !important;
}

/* Navigation links created using st.page_link */

[data-testid="stSidebar"] a[href] {
    display: flex !important;
    align-items: center !important;

    min-height: 46px !important;
    margin: 5px 0 !important;
    padding: 11px 13px !important;

    border-radius: 10px !important;

    font-size: 15px !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;

    transition:
        background-color 0.2s ease,
        color 0.2s ease !important;
}

/* Larger navigation text */

[data-testid="stSidebar"] a[href] p,
[data-testid="stSidebar"] a[href] span {
    font-size: 15px !important;
    line-height: 1.4 !important;
}

/* Icons */

[data-testid="stSidebar"] a[href] svg {
    width: 18px !important;
    height: 18px !important;
    flex-shrink: 0 !important;
}

/* Hover */

[data-testid="stSidebar"] a[href]:hover {
    background: rgba(170, 213, 204, 0.13) !important;
}

/* Current page */

[data-testid="stSidebar"] a[aria-current="page"] {
    background: rgba(151, 189, 205, 0.17) !important;
    box-shadow: inset 3px 0 0 #38b996 !important;
    font-weight: 750 !important;
}

/* Section captions */

[data-testid="stSidebar"]
[data-testid="stCaptionContainer"] {
    margin-top: 15px !important;
    margin-bottom: 12px !important;
}

/* Reduced motion */

@media (prefers-reduced-motion: reduce) {
    [data-testid="stSidebar"] a[href] {
        transition: none !important;
    }
}

</style>
"""


def apply_sidebar_styles():
    st.html(SIDEBAR_CSS)
