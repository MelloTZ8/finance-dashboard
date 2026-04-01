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
    st.markdown("SYS.STAT: ONLINE")

# --- 3. DATA ENGINE (Header Tickers) ---
@st.cache_data(ttl=600)
def get_header_data():
    """Per-symbol OHLC calendars differ (cash vs futures vs crypto). Do not ffill a
    shared date index for returns: that makes the last two rows identical for symbols
    that did not print on the latest bar, so 1D shows 0% or wrong values."""
    tickers = ["^GSPC", "^IXIC", "^DJI", "CL=F", "ES=F", "NQ=F", "BTC-USD", "^VIX"]
    raw = yf.download(tickers, period="2y", progress=False, threads=False)
    close = raw["Close"].copy()
    if isinstance(close.columns, pd.MultiIndex):
        close.columns = close.columns.droplevel(0)

    y = datetime.now().year
    curr, prev_1d, prev_1w, prev_1m, start_ytd, start_yoy = (
        {},
        {},
        {},
        {},
        {},
        {},
    )

    for t in tickers:
        if t not in close.columns:
            continue
        s = close[t].dropna()
        if s.empty:
            continue
        idx = s.index
        curr[t] = float(s.iloc[-1])
        prev_1d[t] = float(s.iloc[-2]) if len(s) >= 2 else float("nan")
        prev_1w[t] = float(s.iloc[-6]) if len(s) >= 6 else float(s.iloc[0])
        prev_1m[t] = float(s.iloc[-22]) if len(s) >= 22 else float(s.iloc[0])

        y0 = pd.Timestamp(year=y, month=1, day=1, tz=idx.tz) if idx.tz is not None else pd.Timestamp(year=y, month=1, day=1)
        ytd_s = s[s.index >= y0]
        start_ytd[t] = float(ytd_s.iloc[0]) if not ytd_s.empty else curr[t]

        yoy_i = -252 if len(s) >= 252 else 0
        start_yoy[t] = float(s.iloc[yoy_i])

    return {
        "curr": pd.Series(curr),
        "prev_1d": pd.Series(prev_1d),
        "prev_1w": pd.Series(prev_1w),
        "prev_1m": pd.Series(prev_1m),
        "ytd": pd.Series(start_ytd),
        "yoy": pd.Series(start_yoy),
    }

h_data = get_header_data()

def calc_perf(ticker, period_key):
    curr = h_data["curr"].get(ticker, float("nan"))
    prev = h_data[period_key].get(ticker, float("nan"))
    try:
        c, p = float(curr), float(prev)
    except (TypeError, ValueError):
        return float("nan")
    if math.isnan(c) or math.isnan(p) or p == 0:
        return float("nan")
    return ((c - p) / p) * 100


def _pct_txt(val: float) -> str:
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return "—"
    return f"{val:+.2f}%"


def _perf_class(val: float) -> str:
    if val > 0:
        return "bb-pos"
    if val < 0:
        return "bb-neg"
    return "bb-flat"


def bb_fmt(ticker_label, ticker_sym):
    price = h_data['curr'][ticker_sym]
    p1d = calc_perf(ticker_sym, 'prev_1d')
    p1m = calc_perf(ticker_sym, 'prev_1m')
    pytd = calc_perf(ticker_sym, 'ytd')

    return f"""
    <div class="bb-terminal terminal-ticker-row" style="margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 6px;">
        <div style="display: flex; align-items: baseline; justify-content: space-between; gap: 8px; white-space: nowrap;">
            <span class="bb-label" style="font-size: 14px;">{ticker_label}</span>
            <span class="bb-price" style="font-size: 16px;">{price:,.2f}</span>
        </div>
        <div style="font-size: 14px; margin-top: 4px; white-space: nowrap;">
            <span class="{_perf_class(p1d)}">1D {_pct_txt(p1d)}</span>
            <span class="bb-sep" style="margin: 0 5px;">·</span>
            <span class="{_perf_class(p1m)}">1M {_pct_txt(p1m)}</span>
            <span class="bb-sep" style="margin: 0 5px;">·</span>
            <span class="{_perf_class(pytd)}">YTD {_pct_txt(pytd)}</span>
        </div>
    </div>
    """


def btc_fmt():
    btc = h_data['curr']['BTC-USD']
    p1d = calc_perf('BTC-USD', 'prev_1d')
    p1w = calc_perf('BTC-USD', 'prev_1w')
    p1m = calc_perf('BTC-USD', 'prev_1m')
    pytd = calc_perf('BTC-USD', 'ytd')
    pyoy = calc_perf('BTC-USD', 'yoy')

    return f"""
    <div class="bb-terminal terminal-btc-block">
        <div class="bb-muted" style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em;">BTC / USD</div>
        <div class="bb-price" style="font-size: 26px; line-height: 1.2; white-space: nowrap;">${btc:,.0f}</div>
        <div style="font-size: 14px; margin-top: 5px; white-space: nowrap;">
            <span class="{_perf_class(p1d)}">1D {_pct_txt(p1d)}</span>
            <span class="bb-sep" style="margin: 0 5px;">·</span>
            <span class="{_perf_class(p1w)}">1W {_pct_txt(p1w)}</span>
            <span class="bb-sep" style="margin: 0 5px;">·</span>
            <span class="{_perf_class(p1m)}">1M {_pct_txt(p1m)}</span>
        </div>
        <div style="font-size: 14px; margin-top: 3px; white-space: nowrap;">
            <span class="{_perf_class(pytd)}">YTD {_pct_txt(pytd)}</span>
            <span class="bb-sep" style="margin: 0 5px;">·</span>
            <span class="{_perf_class(pyoy)}">1Y {_pct_txt(pyoy)}</span>
        </div>
    </div>
    """


def _ribbon_sub(text: str) -> None:
    st.markdown(
        f'<div class="bb-terminal"><p class="bb-ribbon-sub">{text}</p></div>',
        unsafe_allow_html=True,
    )


def switchboard_card(page: str, title: str, blurb: str) -> None:
    with st.container(border=True):
        st.page_link(page, label=title, use_container_width=True)
        st.caption(blurb)


# --- 4. HEADER SECTION ---
col_t1, col_t2 = st.columns([1, 1])
with col_t1:
    st.markdown(
        f"""<div class="bb-terminal" style="line-height:1.25;">
        <span class="bb-hero-title">0-E-TERMINAL</span>
        <span class="bb-hero-date" style="margin-left:8px;">// {datetime.now().strftime('%d %b %Y')}</span>
        </div>""",
        unsafe_allow_html=True,
    )
with col_t2:
    vix_val = h_data['curr']['^VIX']
    vix_pct = calc_perf('^VIX', 'prev_1d')
    
    # Implied Vol Math
    daily_implied = vix_val / math.sqrt(256)
    monthly_implied = vix_val / math.sqrt(12)
    
    vix_chg_cls = _perf_class(vix_pct)

    st.markdown(f"""
    <div class="bb-terminal" style="text-align: right; margin-top: 6px;">
        <div style="font-size: 17px; white-space: nowrap;">
            <span class="bb-vix-tag">VIX</span>
            <span class="bb-price" style="font-size: 22px; margin-left: 6px;">{vix_val:.2f}</span>
            <span class="{vix_chg_cls}" style="font-size: 16px;"> ({vix_pct:+.2f}%)</span>
        </div>
        <div class="bb-muted" style="font-size: 14px; margin-top: 5px; white-space: nowrap;">
            DAILY σ <span class="bb-cyan">{daily_implied:.2f}%</span>
            <span class="bb-sep" style="margin: 0 6px;">·</span>
            30D σ <span class="bb-cyan">{monthly_implied:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Ticker Ribbon
st.markdown("---")
st.markdown(
    '<h3 class="bb-switchboard-section">MARKETS</h3>',
    unsafe_allow_html=True,
)
c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.15, 0.55])

with c1:
    _ribbon_sub("Indices")
    st.markdown(bb_fmt("S&P 500", "^GSPC"), unsafe_allow_html=True)
    st.markdown(bb_fmt("NASDAQ", "^IXIC"), unsafe_allow_html=True)
    st.markdown(bb_fmt("DOW", "^DJI"), unsafe_allow_html=True)
    st.markdown(bb_fmt("CRUDE", "CL=F"), unsafe_allow_html=True)

with c2:
    _ribbon_sub("Futures")
    st.markdown(bb_fmt("ES1!", "ES=F"), unsafe_allow_html=True)
    st.markdown(bb_fmt("NQ1!", "NQ=F"), unsafe_allow_html=True)

with c3:
    _ribbon_sub("Bitcoin")
    st.markdown(btc_fmt(), unsafe_allow_html=True)

with c4:
    _ribbon_sub("Sys.time")
    st.markdown(
        f"""<div class="bb-terminal">
        <p class="bb-label" style="font-size:14px; margin:0 0 6px 0;">UTC: {datetime.now(timezone.utc).strftime('%H:%M:%S')}</p>
        <p style="font-size:14px; margin:0;"><span class="bb-muted">FEED:</span> <span class="bb-pos">ACTIVE</span></p>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- 5. THE REORGANIZED SWITCHBOARD ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<h3 class="bb-switchboard-section">[A] SYSTEMIC INPUTS</h3>',
        unsafe_allow_html=True,
    )
    for path, title, blurb in (
        (
            "pages/01-macro-bonds.py",
            "[01] Macro Bond Watch",
            "The cost of money. Treasury curve and spread dynamics.",
        ),
        (
            "pages/02-inflation.py",
            "[02] Inflation",
            "The rate of debasement. CPI, PPI, and breakevens.",
        ),
        (
            "pages/03-liquidity.py",
            "[03] Liquidity",
            "The systemic money flow. Fed Balance Sheet & Repo.",
        ),
    ):
        switchboard_card(path, title, blurb)

with col2:
    st.markdown(
        '<h3 class="bb-switchboard-section">[B] RISK & EQUITY FLOW</h3>',
        unsafe_allow_html=True,
    )
    for path, title, blurb in (
        (
            "pages/05-global-markets.py",
            "[05] Global Markets",
            "Cross-border liquidity and FX correlations.",
        ),
        (
            "pages/08-market-heatmap.py",
            "[08] Market Heatmap",
            "Breadth, internals, and immediate price action.",
        ),
        (
            "pages/09-sectors.py",
            "[09] Sectors",
            "Capital rotation and internal equity breadth.",
        ),
        (
            "pages/11-options-flow.py",
            "[11] Options Flow",
            "Unusual activity, sweeps, and flow versus spot.",
        ),
    ):
        switchboard_card(path, title, blurb)

with col3:
    st.markdown(
        '<h3 class="bb-switchboard-section">[C] HARD ASSETS & ALPHA</h3>',
        unsafe_allow_html=True,
    )
    for path, title, blurb in (
        (
            "pages/04-crypto.py",
            "[04] Crypto Terminal",
            "Digital beta. Correlation to DXY and local BTC liquidity.",
        ),
        (
            "pages/06-metals.py",
            "[06] Metals",
            "Growth/Fear barometer. Gold, Silver, and Copper flows.",
        ),
        (
            "pages/07-energy.py",
            "[07] Energy",
            "The global input cost. Oil, Gas, and Refined Products.",
        ),
        (
            "pages/10-positioning.py",
            "[10] Positioning",
            "Crowding, CTA/dealer context, and net exposure.",
        ),
        (
            "pages/12-options-analyzer.py",
            "[12] Options Analyzer",
            "Structures, greeks, and scenario tools for single names.",
        ),
    ):
        switchboard_card(path, title, blurb)