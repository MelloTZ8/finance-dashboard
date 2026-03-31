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
        </style>
        """,
        unsafe_allow_html=True
    )