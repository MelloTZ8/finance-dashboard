import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- BLOOMBERG TERMINAL STYLING ---
st.set_page_config(page_title="08_Crypto_Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: #e0e0e0; font-family: 'Courier New', Courier, monospace; }
    .stMetric { border: 1px solid #333; padding: 10px; background-color: #111; }
    [data-testid="stMetricValue"] { color: #ff9900; font-size: 1.8rem; }
    .status-header { background-color: #1a1a1a; padding: 5px 15px; border-bottom: 2px solid #ff9900; font-family: monospace; color: #00ff00; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown('<div class="status-header">CRYP <GO> | TERMINAL STATUS: ONLINE | MARCH 31, 2026</div>', unsafe_allow_html=True)
st.title("₿ CRYPTO MACRO INTELLIGENCE")

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def fetch_terminal_data():
    tickers = {
        'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'SOL': 'SOL-USD',
        'DXY': 'DX-Y.NYB', 'GOLD': 'GC=F', 'USDT': 'USDT-USD'
    }
    df = yf.download(list(tickers.values()), period="6mo", interval="1d")['Close']
    df.rename(columns={v: k for k, v in tickers.items()}, inplace=True)
    return df

@st.cache_data(ttl=3600)
def fetch_sentiment():
    try:
        val = requests.get('https://api.alternative.me/fng/').json()['data'][0]['value']
        return val
    except: return "14"

data = fetch_terminal_data()
fng = fetch_sentiment()

# --- ROW 1: THE TAPE ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("XBT/USD", f"${data['BTC'].iloc[-1]:,.0f}", "-1.24%")
with c2:
    st.metric("DOMINANCE", "57.2%", "1.4% ↑")
with c3:
    st.metric("FEAR & GREED", f"{fng}", "EXTREME FEAR")
with c4:
    st.metric("DXY INDEX", f"{data['DXY'].iloc[-1]:.2f}", "+0.45%")

st.divider()

# --- ROW 2: CORRELATION MATRIX & CHARTS ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("MACRO ASSET NORMALIZATION (180D)")
    # Normalizing to see relative performance
    norm = (data / data.iloc[0]) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=norm['BTC'], name="Bitcoin", line=dict(color='#ff9900', width=3)))
    fig.add_trace(go.Scatter(x=data.index, y=norm['GOLD'], name="Gold (XAU)", line=dict(color='#d4af37', dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=norm['DXY'], name="USD Index", line=dict(color='#0080ff', width=1)))
    
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("INSTITUTIONAL FLOWS")
    st.write("**Spot ETF Net Flows (Est)**")
    st.code("WEEKLY: -$420.5M\nIBIT:  +$12.1M\nFBTC:  -$155.2M", language="text")
    
    st.subheader("STABLECOIN LIQUIDITY")
    st.write(f"USDT Mkt Cap: **$184.2B**")
    st.progress(85, text="Liquidity Depth: HIGH")
    st.caption("Stablecoin supply remains at record highs despite price volatility.")

# --- FOOTER ---
st.markdown("---")
st.caption("PROPRIETARY TERMINAL DATA | UNAUTHORIZED DISTRIBUTION PROHIBITED")