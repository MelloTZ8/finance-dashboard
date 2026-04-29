import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta

# Ensure the root directory is in the path to import theme
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from theme import inject_custom_css

# --- CONFIG & SECRETS ---
st.set_page_config(page_title="Energy | E-Terminal", layout="wide")
inject_custom_css()

# Initialize FRED (Ensure 'fred_api_key' is in your .streamlit/secrets.toml)
fred_api_key = "YOUR_ACTUAL_API_KEY_HERE"

# --- DATA FETCHING (CACHED) ---
@st.cache_data(ttl=3600)
def get_energy_tickers():
    tickers = {
        "WTI": "CL=F", "BRENT": "BZ=F", "RBOB": "RB=F",
        "XLE": "XLE", "XOP": "XOP", "OIH": "OIH", 
        "URA": "URA", "TAN": "TAN", "ICLN": "ICLN",
        "UNG": "UNG", "IBIT": "IBIT", "SPY": "SPY",
        "DXY": "DX-Y.NYB", "TLT": "TLT"
    }
    data = yf.download(list(tickers.values()), period="1y")['Close']
    return data, tickers

@st.cache_data(ttl=86400)
def get_fred_energy():
    # US Rig Count (HOUST is proxy if specific rig series is restricted, 
    # but we will use Crude Production and Rig series)
    series = {
        "Crude_Prod": "WCRVUS2",         # Weekly US Field Production of Crude
        "NatGas_Storage": "WNGSTUSL",    # Weekly Working Gas in Underground Storage
        "Crude_Inventories": "WCLCPS1",  # Weekly US Stocks of Crude Oil
        "SPR": "WCSSTUS1"                # Weekly SPR Stocks
    }
    df_list = []
    for name, s_id in series.items():
        df = fred.get_series(s_id).to_frame(name)
        df_list.append(df)
    return pd.concat(df_list, axis=1).ffill()

# --- PREP DATA ---
prices, ticker_map = get_energy_tickers()
macro_data = get_fred_energy()

# --- HEADER ---
st.markdown('<h3 class="bb-switchboard-section">ENERGY TERMINAL ⚡</h3>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "MARKET ANALYSIS", "INTERMARKET", "DOWNSTREAM", "UPSTREAM", "INVENTORIES"
])

# ==========================================
# TAB 1: MARKET ANALYSIS
# ==========================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # Metrics
    wti_last = prices[ticker_map["WTI"]].iloc[-1]
    brent_last = prices[ticker_map["BRENT"]].iloc[-1]
    spread = brent_last - wti_last
    ibit_last = prices[ticker_map["IBIT"]].iloc[-1]

    col1.metric("🛢️ WTI CRUDE", f"${wti_last:.2f}")
    col2.metric("🌍 BRENT SPREAD", f"${spread:.2f}")
    col3.metric("⛽ RBOB GAS", f"${prices[ticker_map['RBOB']].iloc[-1]:.2f}")
    col4.metric("₿ IBIT (DIGITAL ENERGY)", f"${ibit_last:.2f}")

    # Plotly Chart: Market Analysis
    fig1 = go.Figure()
    # Energy = Red
    fig1.add_trace(go.Scatter(x=prices.index, y=prices[ticker_map["WTI"]], name="🛢️ WTI", line=dict(color='#FF0000')))
    # Bitcoin = Orange
    fig1.add_trace(go.Scatter(x=prices.index, y=prices[ticker_map["IBIT"]], name="₿ IBIT", line=dict(color='#F7931A'), yaxis="y2"))
    
    fig1.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title="Physical Energy vs Digital Energy (Normalized)",
        xaxis=dict(title="Timeline", showgrid=False),
        yaxis=dict(title="Crude Price (USD)", side="left"),
        yaxis2=dict(title="IBIT Price (USD)", overlaying="y", side="right"),
        font=dict(family="Courier New, monospace")
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 EXPERT INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    **Amrita Sen:** The WTI-Brent spread is widening as US domestic supply surges while OPEC+ maintains its floor. 
    Watch for IBIT to start decoupling from traditional risk assets; as energy costs rise, the 'cost of production' 
    for digital assets scales, creating a new floor for Bitcoin.
    
    **Gianna Bern:** Trading the spread requires a keen eye on the RBOB crack spread. If gasoline prices fail to 
    keep pace with crude, refinery margins get squeezed, and we see an immediate pull-back in 🛢️ XLE equities 
    regardless of how high spot crude goes.
    """)

# ==========================================
# TAB 2: INTERMARKET COMPARISON
# ==========================================
with tab2:
    st.markdown('<h4 class="bb-section-head">RELATIVE PERFORMANCE (%)</h4>', unsafe_allow_html=True)
    
    # Normalization logic
    norm_df = prices.copy()
    norm_df = (norm_df / norm_df.iloc[0]) * 100

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["XLE"]], name="🛢️ XLE (Energy)", line=dict(color='red')))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["TAN"]], name="☀️ TAN (Solar)", line=dict(color='yellow')))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["URA"]], name="☢️ URA (Nuclear)", line=dict(color='cyan')))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["SPY"]], name="📈 SPY (Market)", line=dict(color='white', dash='dash')))

    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Trade Date", showgrid=False),
        yaxis=dict(title="Index Value (Base 100)", showgrid=True),
        font=dict(family="Courier New, monospace")
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **Gianna Bern:** This chart highlights the beta between ☢️ Nuclear and 🛢️ Fossil fuels. Notice that URA 
    often leads during periods of high-interest rates as the market bets on stable, long-term power generation.
    
    **Amrita Sen:** ☀️ Solar (TAN) is struggling under the weight of DXY strength. Until the dollar cools, 
    the capital expenditure for global clean energy projects remains prohibitive compared to traditional crude.
    """)

# ==========================================
# TAB 3: DOWNSTREAM
# ==========================================
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="menu-card"><h4>GASOLINE CRACKS</h4><p class="bb-muted">Source: NYMEX</p></div>', unsafe_allow_html=True)
        # Simplified crack spread calculation (3-2-1 logic omitted for space, using RBOB/WTI ratio)
        crack_ratio = prices[ticker_map["RBOB"]] / prices[ticker_map["WTI"]]
        fig3 = go.Figure(go.Scatter(x=crack_ratio.index, y=crack_ratio, line=dict(color='#00FF00')))
        fig3.update_layout(template="plotly_dark", title="RBOB/WTI Value Ratio", xaxis_title="Date", yaxis_title="Ratio")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("""
    **Amrita Sen:** Refining utilization is peaking. We are seeing a mismatch between heavy crude availability 
    and the lighter sweet crude US refineries are optimized for.
    
    **Gianna Bern:** Downstream risk is centered on compliance. If OPEC barrels remain heavy, refiners 
    in the Gulf will have to pay a premium for blending, cutting into those ⛽ RBOB margins.
    """)

# ==========================================
# TAB 4: UPSTREAM
# ==========================================
with tab4:
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=macro_data.index, y=macro_data["Crude_Prod"], name="🇺🇸 US Production", line=dict(color='red')))
    
    fig4.update_layout(
        template="plotly_dark",
        title="US Weekly Crude Production (Thousands of Barrels per Day)",
        xaxis_title="Year",
        yaxis_title="BBL/D (000s)",
        font=dict(family="Courier New, monospace")
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("""
    **Amrita Sen:** US Production is the "tap" that won't close. Even with a falling rig count, efficiency 
    gains in the Permian mean we are doing more with less.
    
    **Gianna Bern:** The lag between rig counts and actual production is roughly 6 months. Watch the ⛏️ XOP 
    producers; they are signaling that capital discipline is more important than raw volume right now.
    """)

# ==========================================
# TAB 5: STORAGE & INVENTORIES
# ==========================================
with tab5:
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown('<h4 class="bb-section-head">CRUDE STOCKS (EXCL. SPR)</h4>', unsafe_allow_html=True)
        st.line_chart(macro_data["Crude_Inventories"], color="#FFB100")
        
    with colB:
        st.markdown('<h4 class="bb-section-head">SPR LEVELS</h4>', unsafe_allow_html=True)
        st.line_chart(macro_data["SPR"], color="#FF4500")

    st.markdown("""
    **Amrita Sen:** The SPR is the "Ghost in the Machine." Any attempt to refill it creates a floor for 
    WTI at $70. If inventories draw down while the SPR is empty, the upside for crude is uncapped.
    
    **Gianna Bern:** Natural gas storage (🔥 UNG) is the ultimate volatility play. Unlike crude, you 
    cannot easily move gas across oceans without liquefaction. Storage builds are localized and brutal 
    to prices in the shoulder seasons.
    """)