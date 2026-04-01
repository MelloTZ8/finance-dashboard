import streamlit as st

def terminal_style():
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            /* You can add other terminal-style CSS here later */
        </style>
    """, unsafe_allow_html=True)