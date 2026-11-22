
"""InvoiceFlow Pro — Dashboard visual design.

Presentation only. No database or financial calculations.
"""

import streamlit as st


DASHBOARD_CSS = """
<style>

/* ==========================================
   INVOICEFLOW PRO — DASHBOARD DESIGN SYSTEM
========================================== */

:root {
    --if-ink: #173645;
    --if-muted: #718796;
    --if-line: #dde9e9;
    --if-green: #087d66;
    --if-green-deep: #104b42;
    --if-surface: #ffffff;
    --if-shadow: 0 10px 30px rgba(16, 51, 60, .055);
}

/* ==========================================
   PREMIUM DASHBOARD HEADER
========================================== */

.if-hero {
    position: relative !important;
    overflow: hidden !important;
    isolation: isolate;

    background: linear-gradient(
        115deg,
        #142d3d 0%,
        #145248 55%,
        #08886c 100%
    ) !important;

    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 22px !important;

    padding: 32px 38px !important;
    min-height: 138px;

    box-shadow:
        0 16px 35px rgba(13,56,57,.11) !important;

    margin-bottom: 18px !important;
}

.if-hero::before,
.if-hero::after {
    content: "";
    position: absolute;
    pointer-events: none;
    border: 1px solid rgba(255,255,255,.11);
    border-radius: 50%;
    z-index: -1;
}

.if-hero::before {
    width: 390px;
    height: 390px;
    right: -110px;
    top: -260px;
}

.if-hero::after {
    width: 235px;
    height: 235px;
    right: 85px;
    bottom: -210px;
}

.if-hero-title {
    font-size: clamp(24px, 2.5vw, 34px) !important;
    font-weight: 820 !important;
    letter-spacing: -.8px !important;
    line-height: 1.14 !important;
    color: #fff !important;
}

.if-hero-description {
    color: #d4e9e8 !important;
    font-size: 13px !important;
    max-width: 680px !important;
    line-height: 1.7 !important;
    margin-top: 10px !important;
}

/* ==========================================
   PREMIUM NAVIGATION TABS
========================================== */

div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 7px !important;

    background: #eaf0f2 !important;
    border: 1px solid #dce7ea !important;
    border-radius: 13px !important;

    padding: 5px !important;
    margin: 8px 0 15px !important;

    width: fit-content;
    max-width: 100%;
}

div[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 9px !important;
    min-height: 40px !important;
    padding: 8px 16px !important;

    color: #536d7a !important;
    font-weight: 650 !important;

    transition:
        background .2s ease,
        color .2s ease,
        box-shadow .2s ease;
}

div[data-testid="stTabs"]
[data-baseweb="tab"][aria-selected="true"] {
    background: white !important;
    color: #087c64 !important;

    box-shadow:
        0 2px 7px rgba(15,52,64,.09) !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-testid="stTabs"] [data-baseweb="tab-border"] {
    background-color: transparent !important;
}

/* ==========================================
   FINANCIAL PERFORMANCE HEADER
========================================== */

.if-fin-hero {
    padding: 16px 0 7px !important;
    margin: 0 0 10px !important;
}

.if-fin-hero h2 {
    font-size: clamp(23px, 2.1vw, 28px) !important;
    letter-spacing: -.55px !important;
    color: var(--if-ink) !important;
}

.if-fin-eyebrow {
    font-size: 10px !important;
    letter-spacing: 2px !important;
}

.if-fin-hero p {
    color: var(--if-muted) !important;
}

/* ==========================================
   SECTION HEADINGS
========================================== */

.if-fin-section {
    margin: 20px 0 12px !important;
}

.if-fin-section h3 {
    font-size: 19px !important;
    letter-spacing: -.3px !important;
    color: var(--if-ink) !important;
}

.if-fin-section p {
    font-size: 12px !important;
}

/* ==========================================
   PREMIUM KPI CARDS
========================================== */

.if-fin-kpis {
    gap: 14px !important;
    margin: 15px 0 18px !important;
}

.if-fin-card {
    min-height: 140px;

    border: 1px solid var(--if-line) !important;
    border-radius: 18px !important;

    padding: 22px !important;

    box-shadow: var(--if-shadow) !important;

    transition:
        transform .22s ease,
        box-shadow .22s ease !important;
}

.if-fin-card:hover {
    transform: translateY(-3px) !important;

    box-shadow:
        0 16px 34px rgba(15,52,65,.11) !important;
}

.if-fin-card.primary {
    background: linear-gradient(
        125deg,
        #17463e,
        #077e65
    ) !important;

    border-color: transparent !important;

    box-shadow:
        0 16px 32px rgba(7,125,101,.16) !important;
}

.if-fin-card .if-fin-value {
    font-size: clamp(22px, 2vw, 29px) !important;
    margin: 17px 0 13px !important;
    letter-spacing: -.6px !important;
}

.if-fin-card .if-fin-label {
    font-size: 12px !important;
    font-weight: 700 !important;
}

/* ==========================================
   SECONDARY KPI CARDS
========================================== */

.if-fin-stats {
    gap: 14px !important;
    margin: 0 0 22px !important;
}

.if-fin-stat {
    border-radius: 15px !important;
    padding: 19px 21px !important;

    border: 1px solid var(--if-line) !important;

    box-shadow:
        0 5px 20px rgba(16,51,60,.035);
}

.if-fin-stat .if-fin-value {
    font-size: 28px !important;
}

/* ==========================================
   DATA TABLES AND PANELS
========================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
}

div[data-testid="stDataFrame"] {
    border-radius: 13px;
    overflow: hidden;

    box-shadow:
        0 4px 16px rgba(19,51,62,.035);
}

/* ==========================================
   BUTTONS AND INTERACTIONS
========================================== */

div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button {
    min-height: 39px;

    border-radius: 11px !important;
    font-weight: 630 !important;

    transition:
        transform .18s ease,
        box-shadow .18s ease !important;
}

div[data-testid="stButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-1px);

    box-shadow:
        0 5px 14px rgba(13,74,67,.09);
}

div[data-testid="stButton"] button:focus-visible,
div[data-testid="stDownloadButton"] button:focus-visible,
div[data-testid="stPageLink"] a:focus-visible {
    outline: 3px solid rgba(5,135,100,.28) !important;
    outline-offset: 3px;
}

/* ==========================================
   PAGE NAVIGATION LINKS
========================================== */

div[data-testid="stPageLink"] a {
    border-radius: 11px !important;
    padding: 10px 13px !important;

    transition: background .18s ease !important;
}

div[data-testid="stPageLink"] a:hover {
    background: rgba(8,125,102,.055) !important;
}

/* ==========================================
   SPREADSHEET ANALYSIS
========================================== */

div[data-testid="stMarkdownContainer"] h2 {
    color: var(--if-ink) !important;
    letter-spacing: -.45px;
    font-weight: 750;
}

div[data-testid="stAlert"] {
    border-radius: 14px !important;
}

div[data-testid="stExpander"] {
    border-radius: 14px !important;
    overflow: hidden;
}

/* ==========================================
   INFORMATION / DISCLAIMER
========================================== */

.if-fin-tip {
    background: #eef6f3;
    border: 1px solid #d5e9df;
    border-radius: 11px;

    padding: 12px 15px;
    line-height: 1.6;

    color: #587568 !important;
}

/* ==========================================
   TABLET RESPONSIVENESS
========================================== */

@media (max-width: 1100px) {

    .if-fin-kpis {
        grid-template-columns:
            repeat(2, minmax(0,1fr)) !important;
    }

    .if-fin-stats {
        grid-template-columns:
            repeat(3, minmax(0,1fr)) !important;
    }

}

/* ==========================================
   MOBILE RESPONSIVENESS
========================================== */

@media (max-width: 740px) {

    .if-hero {
        padding: 24px 20px !important;
        border-radius: 17px !important;
    }

    .if-fin-kpis {
        grid-template-columns: 1fr !important;
    }

    .if-fin-stats {
        grid-template-columns: 1fr !important;
    }

    div[data-testid="stTabs"]
    [data-baseweb="tab-list"] {
        width: 100%;
    }

    div[data-testid="stTabs"]
    [data-baseweb="tab"] {
        flex: 1;
        padding: 8px 9px !important;
        font-size: 12px !important;
    }

}

/* ==========================================
   ACCESSIBILITY
========================================== */

@media (prefers-reduced-motion: reduce) {

    .if-fin-card,
    div[data-testid="stTabs"] [data-baseweb="tab"],
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button,
    div[data-testid="stPageLink"] a {
        transition: none !important;
    }

    .if-fin-card:hover,
    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        transform: none !important;
    }

}

</style>
"""


def apply_dashboard_skin():
    """Apply the Dashboard visual styles."""
    st.html(DASHBOARD_CSS)
