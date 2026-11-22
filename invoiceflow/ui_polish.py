
"""Reusable UI improvements for InvoiceFlow Pro."""

import streamlit as st


def apply_ui_polish():
    """Apply shared visual styles and motion effects."""

    st.html(
        """
        <style>

        /* ----------------------------------
           ANIMATION
        ---------------------------------- */

        @keyframes if-fade-in {
            from {
                opacity: 0;
                transform: translateY(7px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        div[class*="st-key-if_motion_"] {
            animation: if-fade-in 220ms ease-out both;
        }

        /* ----------------------------------
           SELECTED INVOICE SUMMARY
        ---------------------------------- */

        .st-key-if_invoice_summary {
            background: #FFFFFF;
            border: 1px solid #DFE8EB;
            border-radius: 18px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow:
                0 5px 22px rgba(16, 43, 55, 0.045);
        }

        /* ----------------------------------
           INVOICE CONTENT PANELS
        ---------------------------------- */

        div[class*="st-key-if_motion_"] {
            border-radius: 12px;
        }

        /* ----------------------------------
           RESPONSIVE SPACING
        ---------------------------------- */

        @media (max-width: 768px) {

            .st-key-if_invoice_summary {
                padding: 14px;
                border-radius: 12px;
            }

        }

        /* ----------------------------------
           ACCESSIBILITY
        ---------------------------------- */

        @media (prefers-reduced-motion: reduce) {

            div[class*="st-key-if_motion_"] {
                animation: none !important;
            }

        }

        </style>
        """
    )
