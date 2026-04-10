import streamlit as st

def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Main background */
        .stApp { background-color: #000000 !important; }
       
        /* Safely apply Monospace ONLY to actual text elements */
        p, h1, h2, h3, h4, h5, h6, li, td, th, label, div[data-testid="stMetricValue"], .stMetric label {
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Target actual text content for Neon Green */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        .stDataFrame td,
        .stDataFrame th {
            color: #00FF00 !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
        }

        /* Override headers to Bloomberg Amber */
        h1, h2, h3, h4, h5, h6, .stSubheader {
            color: #FFB100 !important;
            text-transform: uppercase !important;
            border-bottom: 1px solid #333333;
            padding-bottom: 5px;
        }
       
        /* --- SIDEBAR STYLING --- */
        [data-testid="stSidebar"] {
            background-color: #0a0a0a !important;
            border-right: 1px solid #FFB100;
        }
        /* Sidebar: keep natural casing (E-Terminal, page titles) — main area still uppercase headers */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6 {
            text-transform: none !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] a {
            color: #FFB100 !important;
            text-decoration: none !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-size: 14px !important;
        }
        [data-testid="stSidebar"] a:hover {
            color: #00FF00 !important; /* Flash green on hover */
        }

        /* Metrics Readouts - Neon Green */
        [data-testid="stMetricValue"] {
            color: #00FF00 !important;
            font-size: 28px !important;
            font-weight: bold;
        }

        /* Tab Styling */
        [data-baseweb="tab-list"] { background-color: #000000 !important; }
        [data-baseweb="tab"] {
            background-color: #111111 !important;
            color: #FFB100 !important;
            border: 1px solid #333333;
            font-size: 14px !important;
        }
        [aria-selected="true"] {
            background-color: #FFB100 !important;
            color: #000000 !important;
        }
        [aria-selected="true"] span, [aria-selected="true"] p {
            color: #000000 !important;
            font-weight: bold;
        }

        /* --- MENU CARD STYLING --- */
        div.menu-card {
            background-color: #0a0a0a;
            border: 1px solid #333333;
            border-left: 3px solid #FFB100;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 3px;
            position: relative;
        }
        div.menu-card h4 {
            color: #FFB100 !important;
            margin-top: 0px;
            margin-bottom: 10px;
            font-size: 16px !important;
            border-bottom: none;
        }
        div.menu-card p {
            margin-bottom: 0px;
            font-size: 13px !important;
        }

        /* Switchboard: bordered blocks + page links on home only (0-E-TERMINAL) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #0a0a0a !important;
            border: 1px solid #333333 !important;
            border-left: 3px solid #FFB100 !important;
            padding: 10px 12px !important;
            margin-bottom: 12px !important;
            border-radius: 3px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPageLink-Container"] a {
            color: #FFB100 !important;
            font-weight: bold !important;
            font-size: 15px !important;
            text-decoration: none !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
            color: #aaaaaa !important;
            font-size: 14px !important;
            line-height: 1.45 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Construction Tag Styling */
        .construction-tag {
            color: #FF4500 !important;
            font-size: 11px !important;
            font-weight: bold;
            border: 1px dashed #FF4500;
            padding: 2px 6px;
            border-radius: 3px;
            display: inline-block;
            margin-top: 8px;
            background-color: rgba(255, 69, 0, 0.1);
        }

        /* Adjust dividers */
        hr {
            border: 0;
            border-top: 1px solid #333333 !important;
        }

        /* --- BLOOMBERG TERMINAL (raw HTML in markdown on home / ribbons) --- */
        [data-testid="stMarkdownContainer"] .bb-terminal,
        [data-testid="stMarkdownContainer"] .bb-terminal * {
            font-family: 'Courier New', Courier, monospace !important;
        }
        /* Switchboard / MARKETS section titles — baseline for hero scale */
        h3.bb-switchboard-section {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #FFB100 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            border-bottom: 1px solid #333333 !important;
            padding-bottom: 6px !important;
            margin: 0 0 0.35rem 0 !important;
        }
        .bb-terminal .bb-hero-title {
            font-size: calc(1.5rem * 1.15) !important;
            font-weight: 700;
            color: #FFB100 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .bb-terminal .bb-hero-date {
            font-size: 1.05rem;
            color: #888888 !important;
            font-weight: 400;
        }
        .bb-terminal .bb-section-head {
            font-size: 14px;
            font-weight: 700;
            color: #FFB100 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            border-bottom: 1px solid #333333;
            padding-bottom: 5px;
            margin: 0 0 8px 0;
        }
        .bb-terminal .bb-label {
            color: #00FF00 !important;
            font-weight: 700;
        }
        .bb-terminal .bb-price {
            color: #FFB100 !important;
            font-weight: 700;
        }
        .bb-terminal .bb-pos { color: #00FF00 !important; font-weight: 700; }
        .bb-terminal .bb-neg { color: #FF0000 !important; font-weight: 700; }
        .bb-terminal .bb-flat { color: #AAAAAA !important; }
        .bb-terminal .bb-muted { color: #888888 !important; }
        .bb-terminal .bb-sep { color: #444444 !important; }
        .bb-terminal .bb-cyan { color: #00BFFF !important; font-weight: 700; }
        .bb-terminal .bb-vix-tag {
            color: #FFB100 !important;
            font-weight: 700;
        }
        .bb-terminal .bb-ribbon-sub {
            font-size: 11px;
            font-weight: 700;
            color: #888888 !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin: 0 0 6px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )