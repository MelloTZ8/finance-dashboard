import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Assuming your theme.py applies global styling or Plotly templates
# import theme 

st.set_page_config(page_title="Liquidity & Systemic Stress", layout="wide")

# --- Helper function for placeholder charts ---
# Swap this out with your actual data fetching logic (e.g., yfinance, FRED API)
def create_placeholder_chart(title, color="#00ff00"):
    fig = go.Figure()
    # Generating dummy historical data (no forecasts)
    dates = pd.date_range(start="2024-01-01", periods=100)
    values = np.cumsum(np.random.randn(100)) + 50
    
    fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', line=dict(color=color, width=2)))
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=40, b=20),
        height=250,
        # Set template="plotly_dark" here if theme.py doesn't set it globally
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    return fig

# ==========================================
# 1. MAIN PAGE: SYSTEMIC LIQUIDITY & FUNDING
# ==========================================
st.title("Systemic Liquidity & Market Stress")
st.markdown("### 1. Systemic Liquidity & Funding (The 'Main Domino')")
st.markdown("Tracking the actual movement of cash. If the plumbing breaks, everything else follows.")

# Top Row: The heavy hitters
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(create_placeholder_chart("LIBOR/SOFR Spreads", "#FF9900"), use_container_width=True)
with col2:
    st.plotly_chart(create_placeholder_chart("Reverse Repo (RRP) Levels", "#00BFFF"), use_container_width=True)

# Bottom Row: Secondary liquidity gauges
col3, col4, col5 = st.columns(3)
with col3:
    st.plotly_chart(create_placeholder_chart("Ted Spread", "#FF3333"), use_container_width=True)
with col4:
    st.plotly_chart(create_placeholder_chart("Cross-Currency Basis Swaps", "#9933FF"), use_container_width=True)
with col5:
    st.plotly_chart(create_placeholder_chart("Commercial Paper Rates", "#33FF99"), use_container_width=True)

st.divider()

# ==========================================
# 2-4. SECONDARY TABS
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "2. Credit Risk & Solvency", 
    "3. Macro & Recessionary Gauges", 
    "4. Market Sentiment & Alerts"
])

# --- TAB 1: Credit Risk ---
with tab1:
    st.markdown("#### Default Risk")
    st.markdown("Tracking if liquidity issues are turning into insolvency issues.")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(create_placeholder_chart("High Yield (Junk) Credit Spreads"), use_container_width=True)
    with c2:
        st.plotly_chart(create_placeholder_chart("Credit Default Swaps (CDS)"), use_container_width=True)

# --- TAB 2: Macro Gauges ---
with tab2:
    st.markdown("#### Economic Cycle & Policy")
    st.markdown("Long-term trends confirming the underlying economy.")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(create_placeholder_chart("Financial Conditions Index (FCI)"), use_container_width=True)
    with c2:
        st.plotly_chart(create_placeholder_chart("The 'Sahm Rule' Monitor"), use_container_width=True)

# --- TAB 3: Market Sentiment ---
with tab3:
    st.markdown("#### Technical 'Crash' Indicators")
    st.markdown("Specific to the stock market's internal health.")
    # Centered single chart for the omen
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.plotly_chart(create_placeholder_chart("The 'Hindenburg Omen' Tracker", "#FF00FF"), use_container_width=True)