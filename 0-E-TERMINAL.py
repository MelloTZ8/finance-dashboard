import streamlit as st
import yfinance as yf
import pandas as pd
import math
from datetime import datetime, timedelta, timezone
import sys
import os

from theme import inject_custom_css

# --- 1. PAGE CONFIG & STATE ---
st.set_page_config(page_title="0-E-TERMINAL", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

# --- 2. LEFT-HAND INDEX (SIDEBAR) ---
with st.sidebar:
    st.markdown("### ⚡ TERMINAL INDEX")
    st.markdown("---")
    
    st.page_link("0-E-TERMINAL.py", label="[00] Home: Switchboard")
    st.page_link("pages/01-macro-bonds.py", label="[01] Macro Bond Watch")
    st.page_link("pages/02-inflation.py", label="[02] Inflation")
    st.page_link("pages/03-liquidity.py", label="[03] Liquidity")
    st.page_link("pages/04-crypto.py", label="[04] Crypto Terminal")
    st.page_link("pages/05-global-markets.py", label="[05] Global Markets")
    st.page_link("pages/06-metals.py", label="[06] Metals")
    st.page_link("pages/07-energy.py", label="[07] Energy")
    st.page_link("pages/08-market-heatmap.py", label="[08] Market Heatmap")
    st.page_link("pages/09-sectors.py", label="[09] Sectors")
    st.page_link("pages/10-positioning.py", label="[10] Positioning")
    st.page_link("pages/11-options-flow.py", label="[11] Options Flow")
    st.page_link("pages/12-options-analyzer.py", label="[12] Options Analyzer")
    
    st.markdown("---")
    st.markdown("<span style='color:#00FF00; font-size:12px;'>SYS.STAT: ONLINE</span>", unsafe_allow_html=True)

# --- 3. DATA ENGINE (Header Tickers) ---
@st.cache_data(ttl=600)
def get_header_data():
    # S&P, Nasdaq, Dow, Crude, ES Futures, NQ Futures, BTC, VIX
    tickers = ["^GSPC", "^IXIC", "^DJI", "CL=F", "ES=F", "NQ=F", "BTC-USD", "^VIX"]
    data = yf.download(tickers, period="2y", progress=False)['Close']
    data.ffill(inplace=True) # Prevent NA drops due to holiday/futures hours mismatches
    
    curr = data.iloc[-1]
    prev_1d = data.iloc[-2]
    prev_1w = data.iloc[-6]
    prev_1m = data.iloc[-22] if len(data) >= 22 else data.iloc[0]
    
    # YTD Calculation
    year_start = datetime(datetime.now().year, 1, 1)
    ytd_data = data.loc[data.index >= pd.to_datetime(year_start)]
    start_ytd = ytd_data.iloc[0] if not ytd_data.empty else curr
    
    # YoY Calculation
    yoy_idx = -252 if len(data) >= 252 else 0
    start_yoy = data.iloc[yoy_idx]
    
    return {
        "curr": curr, "prev_1d": prev_1d, "prev_1w": prev_1w, "prev_1m": prev_1m,
        "ytd": start_ytd, "yoy": start_yoy
    }

h_data = get_header_data()

def calc_perf(ticker, period_key):
    return ((h_data['curr'][ticker] - h_data[period_key][ticker]) / h_data[period_key][ticker]) * 100

def bb_fmt(ticker_label, ticker_sym):
    price = h_data['curr'][ticker_sym]
    p1d = calc_perf(ticker_sym, 'prev_1d')
    p1m = calc_perf(ticker_sym, 'prev_1m')
    pytd = calc_perf(ticker_sym, 'ytd')
    
    def color(val): return "#00FF00" if val > 0 else "#FF0000" if val < 0 else "#AAAAAA"
    
    return f"""
    <div style="margin-bottom: 6px; border-bottom: 1px solid #333; padding-bottom: 2px;">
        <span style="font-family: Arial, sans-serif; font-weight: bold; font-size: 14px; color: #E0E0E0; display: inline-block; width: 65px;">{ticker_label}</span>
        <span style="font-family: 'Courier New', monospace; font-size: 15px; color: #FFB100; display: inline-block; width: 85px; text-align: right;">{price:,.2f}</span>
        <span style="font-family: 'Courier New', monospace; font-size: 12px; margin-left: 10px;">
            1D: <span style="color: {color(p1d)}; font-weight: bold;">{p1d:+.2f}%</span> | 
            1M: <span style="color: {color(p1m)};">{p1m:+.2f}%</span> | 
            YTD: <span style="color: {color(pytd)};">{pytd:+.2f}%</span>
        </span>
    </div>
    """

def btc_fmt():
    btc = h_data['curr']['BTC-USD']
    p1d = calc_perf('BTC-USD', 'prev_1d')
    p1w = calc_perf('BTC-USD', 'prev_1w')
    p1m = calc_perf('BTC-USD', 'prev_1m')
    pytd = calc_perf('BTC-USD', 'ytd')
    pyoy = calc_perf('BTC-USD', 'yoy')
    
    def color(val): return "#00FF00" if val > 0 else "#FF0000" if val < 0 else "#AAAAAA"
    
    return f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #E0E0E0;">Current Price</div>
    <div style="font-family: 'Courier New', monospace; font-size: 26px; font-weight: bold; color: #FFB100;">${btc:,.0f} <span style="font-size: 16px; color: {color(p1d)};">({p1d:+.2f}%)</span></div>
    <div style="font-family: 'Courier New', monospace; font-size: 12px; margin-top: 8px; color: #AAAAAA;">
        1W: <span style="color: {color(p1w)};">{p1w:+.2f}%</span> | 
        1M: <span style="color: {color(p1m)};">{p1m:+.2f}%</span> | 
        YTD: <span style="color: {color(pytd)};">{pytd:+.2f}%</span> | 
        1Y: <span style="color: {color(pyoy)};">{pyoy:+.2f}%</span>
    </div>
    """

# --- 4. HEADER SECTION ---
col_t1, col_t2 = st.columns([1, 1])
with col_t1:
    st.markdown(f"# 0-E-TERMINAL // {datetime.now().strftime('%d %b %Y')}")
with col_t2:
    vix_val = h_data['curr']['^VIX']
    vix_pct = calc_perf('^VIX', 'prev_1d')
    
    # Implied Vol Math
    daily_implied = vix_val / math.sqrt(256)
    monthly_implied = vix_val / math.sqrt(12)
    
    vix_color = "#00FF00" if vix_pct >= 0 else "#FF0000"
    
    st.markdown(f"""
    <div style="text-align: right; margin-top: 10px;">
        <div style="font-family: Arial, sans-serif; font-size: 20px; font-weight: bold; color: #E0E0E0;">
            VIX: <span style="font-family: 'Courier New', monospace; color: #FFB100; font-size: 24px;">{vix_val:.2f}</span> 
            <span style="font-family: 'Courier New', monospace; color: {vix_color}; font-size: 18px;">({vix_pct:+.2f}%)</span>
        </div>
        <div style="font-family: 'Courier New', monospace; font-size: 13px; color: #AAAAAA; margin-top: 5px;">
            Daily Implied Move: <span style="color: #00BFFF; font-weight: bold;">{daily_implied:.2f}%</span> | 
            30-Day Implied Move: <span style="color: #00BFFF; font-weight: bold;">{monthly_implied:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Ticker Ribbon
st.markdown("---")
c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 0.6])

with c1:
    st.markdown("**MACRO INDICES**")
    st.markdown(bb_fmt("S&P 500", "^GSPC"), unsafe_allow_html=True)
    st.markdown(bb_fmt("NASDAQ", "^IXIC"), unsafe_allow_html=True)
    st.markdown(bb_fmt("DOW", "^DJI"), unsafe_allow_html=True)
    st.markdown(bb_fmt("CRUDE", "CL=F"), unsafe_allow_html=True)

with c2:
    st.markdown("**FUTURES MARKET**")
    st.markdown(bb_fmt("ES1!", "ES=F"), unsafe_allow_html=True)
    st.markdown(bb_fmt("NQ1!", "NQ=F"), unsafe_allow_html=True)

with c3:
    st.markdown("**BITCOIN (BTC)**")
    st.markdown(btc_fmt(), unsafe_allow_html=True)

with c4:
    st.markdown("**SYS.TIME**")
    # Fixed the deprecated datetime warning here:
    st.markdown(f"UTC: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
    st.markdown("FEED: <span style='color:#00FF00;'>ACTIVE</span>", unsafe_allow_html=True)

st.markdown("---")

# --- 5. THE REORGANIZED SWITCHBOARD ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### [A] SYSTEMIC INPUTS")
    st.markdown("""
        <a href="01-macro-bonds" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[01] Macro Bond Watch</h4>
                <p>The cost of money. Treasury curve and spread dynamics.</p>
            </div>
        </a>
        <a href="02-inflation" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[02] Inflation</h4>
                <p>The rate of debasement. CPI, PPI, and breakevens.</p>
            </div>
        </a>
        <a href="03-liquidity" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[03] Liquidity</h4>
                <p>The systemic money flow. Fed Balance Sheet & Repo.</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### [B] RISK & EQUITY FLOW")
    st.markdown("""
        <a href="05-global-markets" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[05] Global Markets</h4>
                <p>Cross-border liquidity and FX correlations.</p>
            </div>
        </a>
        <a href="08-market-heatmap" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[08] Market Heatmap</h4>
                <p>The daily vibe check. Breadth and immediate price action.</p>
            </div>
        </a>
        <a href="09-sectors" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[09] Sectors</h4>
                <p>Capital rotation matrices and internal breadth.</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("### [C] HARD ASSETS & ALPHA")
    st.markdown("""
        <a href="04-crypto" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[04] Crypto Terminal</h4>
                <p>Digital beta. Correlation to DXY and local BTC liquidity.</p>
            </div>
        </a>
        <a href="06-metals" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[06] Metals</h4>
                <p>Growth/Fear barometer. Gold, Silver, and Copper flows.</p>
            </div>
        </a>
        <a href="07-energy" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[07] Energy</h4>
                <p>The global input cost. Oil, Gas, and Refined Products.</p>
            </div>
        </a>
        <a href="10-positioning" target="_self" style="text-decoration: none; color: inherit;">
            <div class="menu-card">
                <h4>[10] Positioning & Options Flow</h4>
                <p>Dealer Gamma, Volatility Triggers, and Whale sweeps.</p>
            </div>
        </a>
    """, unsafe_allow_html=True)