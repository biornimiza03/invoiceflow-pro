
"""Reusable hover effects for InvoiceFlow Pro."""

import streamlit as st


def apply_hover_effects():
    """Apply premium hover effects to page controls."""

    st.html("""
    <style>

    /* ========================================
       SECONDARY BUTTONS
    ======================================== */

    [data-testid="stMain"]
    :is(
        [data-testid="stButton"],
        [data-testid="stFormSubmitButton"],
        [data-testid="stDownloadButton"]
    )
    button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) {

        transition:
            background-color 0.22s ease,
            border-color 0.22s ease,
            color 0.22s ease,
            box-shadow 0.22s ease !important;
    }

    [data-testid="stMain"]
    :is(
        [data-testid="stButton"],
        [data-testid="stFormSubmitButton"],
        [data-testid="stDownloadButton"]
    )
    button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover {

        background-color: #e9f7f0 !important;
        border-color: #aedcc8 !important;
        color: #0c7056 !important;

        box-shadow:
            0 3px 12px rgba(18, 122, 89, 0.07) !important;
    }

    /* Text inside hovered buttons */

    [data-testid="stMain"]
    :is(
        [data-testid="stButton"],
        [data-testid="stFormSubmitButton"],
        [data-testid="stDownloadButton"]
    )
    button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover p {

        color: #0c7056 !important;
    }

    /* ========================================
       PRIMARY GREEN BUTTONS
    ======================================== */

    [data-testid="stMain"]
    :is(
        [data-testid="stButton"],
        [data-testid="stFormSubmitButton"],
        [data-testid="stDownloadButton"]
    )
    button:is([data-testid="stBaseButton-primary"], [kind="primary"]):hover {

        background-color: #086b56 !important;
        border-color: #086b56 !important;

        box-shadow:
            0 5px 15px rgba(8, 107, 86, 0.15) !important;
    }

    /* ========================================
       PAGE NAVIGATION LINKS
    ======================================== */

    [data-testid="stMain"]
    [data-testid="stPageLink"] a {

        border-radius: 11px !important;

        transition:
            background-color 0.22s ease,
            color 0.22s ease !important;
    }

    [data-testid="stMain"]
    [data-testid="stPageLink"] a:hover {

        background-color: #e9f7f0 !important;
        color: #0c7056 !important;
    }

    /* ========================================
       EXPANDERS
    ======================================== */

    [data-testid="stMain"]
    [data-testid="stExpander"] summary {

        transition:
            background-color 0.22s ease,
            color 0.22s ease !important;
    }

    [data-testid="stMain"]
    [data-testid="stExpander"] summary:hover {

        background-color: #e9f7f0 !important;
        color: #0c7056 !important;
    }

    /* ========================================
       NAVIGATION TABS
    ======================================== */

    [data-testid="stMain"]
    [data-testid="stTabs"]
    [data-baseweb="tab"]:not([aria-selected="true"]) {

        transition:
            background-color 0.22s ease,
            color 0.22s ease !important;
    }

    [data-testid="stMain"]
    [data-testid="stTabs"]
    [data-baseweb="tab"]:not([aria-selected="true"]):hover {

        background-color: #e9f7f0 !important;
        color: #0c7056 !important;
        border-radius: 9px !important;
    }

    /* ========================================
       SEGMENTED CONTROLS
    ======================================== */

    [data-testid="stMain"]
    [data-testid="stSegmentedControl"]
    button[aria-pressed="false"]:hover {

        background-color: #e9f7f0 !important;
        color: #0c7056 !important;
    }

    /* ========================================
       KEYBOARD ACCESSIBILITY
    ======================================== */

    [data-testid="stMain"] button:focus-visible,
    [data-testid="stMain"] a:focus-visible,
    [data-testid="stMain"] summary:focus-visible {

        outline: 2px solid #0c9270 !important;
        outline-offset: 2px;
    }

    /* ========================================
       REDUCED MOTION
    ======================================== */

    @media (prefers-reduced-motion: reduce) {

        [data-testid="stMain"] button,
        [data-testid="stMain"] a,
        [data-testid="stMain"] summary,
        [data-testid="stMain"] [data-baseweb="tab"] {

            transition: none !important;
        }
    }

    </style>
    """)
