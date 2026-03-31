import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from theme import inject_custom_css

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="0-E-TERMINAL", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

# --- 2. DATA ENGINE (Header Tickers) ---
@st.cache_data(ttl=600)
def get_header_data():
    tickers = ["SPY", "QQQ", "IWM", "BTC-USD", "^VIX"]
    data = yf.download(tickers, period="2y", progress=False)['Close']
    
    # Current values
    curr = data.iloc[-1]
    prev_1d = data.iloc[-2]
    prev_1w = data.iloc[-6]
    
    # YTD Calculation
    year_start = datetime(datetime.now().year, 1, 1)
    ytd_data = data.loc[data.index >= pd.to_datetime(year_start)]
    start_ytd = ytd_data.iloc[0] if not ytd_data.empty else curr
    
    # YoY Calculation
    yoy_idx = -252 if len(data) >= 252 else 0
    start_yoy = data.iloc[yoy_idx]
    
    return {
        "curr": curr, "prev_1d": prev_1d, "prev_1w": prev_1w,
        "ytd": start_ytd, "yoy": start_yoy
    }

h_data = get_header_data()

# --- 3. HEADER SECTION ---
col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    st.markdown(f"# 0-E-TERMINAL // {datetime.now().strftime('%d %b %Y')}")
with col_t2:
    vix_val = h_data['curr']['^VIX']
    vix_pct = ((vix_val - h_data['prev_1d']['^VIX']) / h_data['prev_1d']['^VIX']) * 100
    implied_move = 72 / vix_val # User's requested formula
    st.metric("VIX SQUEEZE", f"{vix_val:.2f}", f"{vix_pct:.2f}%")
    st.markdown(f"<span style='color:#FFB100; font-size:12px;'>72/VIX Implied: {implied_move:.2f}%</span>", unsafe_allow_html=True)

# Ticker Ribbon
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)

def fmt_perf(curr, base):
    pct = ((curr - base) / base) * 100
    color = "#00FF00" if pct > 0 else "#FF0000"
    return f"<span style='color:{color};'>{pct:+.2f}%</span>"

with c1:
    st.markdown("**THE BIG THREE**")
    for t in ["SPY", "QQQ", "IWM"]:
        p = ((h_data['curr'][t] - h_data['prev_1d'][t]) / h_data['prev_1d'][t]) * 100
        st.markdown(f"{t}: ${h_data['curr'][t]:.2f} ({fmt_perf(h_data['curr'][t], h_data['prev_1d'][t])})", unsafe_allow_html=True)

with c2:
    st.markdown("**BITCOIN (BTC)**")
    btc = h_data['curr']['BTC-USD']
    st.markdown(f"Current: ${btc:,.0f}")
    st.markdown(f"1W: {fmt_perf(btc, h_data['prev_1w']['BTC-USD'])} | YTD: {fmt_perf(btc, h_data['ytd']['BTC-USD'])}", unsafe_allow_html=True)

with c3:
    st.markdown("**BTC LONG-TERM**")
    st.markdown(f"YoY Perf: {fmt_perf(btc, h_data['yoy']['BTC-USD'])}")
    st.markdown("Status: <span style='color:#00FF00;'>ACCUMULATION</span>", unsafe_allow_html=True)

with c4:
    st.markdown("**SYS.TIME**")
    st.markdown(f"UTC: {datetime.utcnow().strftime('%H:%M:%S')}")
    st.markdown("FEED: <span style='color:#00FF00;'>ACTIVE</span>", unsafe_allow_html=True)

st.markdown("---")

# --- 4. THE REORGANIZED SWITCHBOARD ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### [A] SYSTEMIC INPUTS")
    st.markdown("""
        <div class="menu-card">
            <h4>[01] Macro Bond Watch</h4>
            <p>The cost of money. Treasury curve and spread dynamics.</p>
        </div>
        <div class="menu-card">
            <h4>[02] Inflation</h4>
            <p>The rate of debasement. CPI, PPI, and breakevens.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
        <div class="menu-card">
            <h4>[03] Liquidity</h4>
            <p>The systemic money flow. Fed Balance Sheet & Repo.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### [B] RISK & EQUITY FLOW")
    st.markdown("""
        <div class="menu-card">
            <h4>[04] Crypto Terminal</h4>
            <p>Digital beta. Correlation to DXY and local BTC liquidity.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
        <div class="menu-card">
            <h4>[08] Market Heatmap</h4>
            <p>The daily vibe check. Breadth and immediate price action.</p>
        </div>
        <div class="menu-card">
            <h4>[10] Positioning</h4>
            <p>Dealer Gamma, Volatility Triggers, and COT reports.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("### [C] HARD ASSETS & ALPHA")
    st.markdown("""
        <div class="menu-card">
            <h4>[06] Metals</h4>
            <p>Growth/Fear barometer. Gold, Silver, and Copper flows.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
        <div class="menu-card">
            <h4>[07] Energy</h4>
            <p>The global input cost. Oil, Gas, and Refined Products.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
        <div class="menu-card">
            <h4>[11] Options Flow</h4>
            <p>The "Whale" tape. Real-time Sweeps and unusual activity.</p>
            <span class="construction-tag">🚧 UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)