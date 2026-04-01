import streamlit as st
import yfinance as yf
import pandas as pd
import math
from datetime import datetime, timezone

# Assuming theme.py is in the same directory
from theme import inject_custom_css

# --- 1. PAGE CONFIG & STATE ---
st.set_page_config(
    page_title="E-TERMINAL", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
inject_custom_css()

# --- 2. LEFT-HAND INDEX (SIDEBAR) ---
# We removed the manual page links to prevent redundant double-navigation.
# Streamlit auto-generates the sidebar nav from the pages/ directory.
with st.sidebar:
    st.markdown("### ⚡ SYSTEM STATUS")
    st.markdown("---")
    st.markdown("SYS.STAT: <span style='color:#00FF00;'>ONLINE</span>", unsafe_allow_html=True)

# --- 3. DATA ENGINE (Header Tickers) ---
@st.cache_data(ttl=600)
def get_header_data() -> dict:
    """
    Fetches market data and calculates historical anchors (1D, 1W, 1M, YTD, YoY).
    Uses caching to prevent rate-limiting from yfinance.
    """
    tickers = ["^GSPC", "^IXIC", "^DJI", "CL=F", "ES=F", "NQ=F", "BTC-USD", "^VIX"]
    
    try:
        raw = yf.download(tickers, period="2y", progress=False, threads=False)
        if raw.empty:
            return {}
    except Exception as e:
        st.error(f"Data Feed Error: {e}")
        return {}

    close = raw["Close"].copy()
    if isinstance(close.columns, pd.MultiIndex):
        close.columns = close.columns.droplevel(0)

    y = datetime.now().year
    metrics = {k: {} for k in ["curr", "prev_1d", "prev_1w", "prev_1m", "ytd", "yoy"]}

    for t in tickers:
        if t not in close.columns:
            continue
            
        s = close[t].dropna()
        if s.empty:
            continue
            
        idx = s.index
        metrics["curr"][t] = float(s.iloc[-1])
        metrics["prev_1d"][t] = float(s.iloc[-2]) if len(s) >= 2 else float("nan")
        metrics["prev_1w"][t] = float(s.iloc[-6]) if len(s) >= 6 else float(s.iloc[0])
        metrics["prev_1m"][t] = float(s.iloc[-22]) if len(s) >= 22 else float(s.iloc[0])

        if idx.tz is not None:
            y0 = pd.Timestamp(f"{y}-01-01").tz_localize(idx.tz)
        else:
            y0 = pd.Timestamp(f"{y}-01-01")
            
        ytd_s = s[s.index >= y0]
        metrics["ytd"][t] = float(ytd_s.iloc[0]) if not ytd_s.empty else metrics["curr"][t]

        yoy_i = -252 if len(s) >= 252 else 0
        metrics["yoy"][t] = float(s.iloc[yoy_i])

    return {k: pd.Series(v) for k, v in metrics.items()}

h_data = get_header_data()

# --- 4. HELPER FUNCTIONS ---
def calc_perf(ticker: str, period_key: str) -> float:
    if not h_data:
        return float("nan")
        
    curr = h_data.get("curr", pd.Series()).get(ticker, float("nan"))
    prev = h_data.get(period_key, pd.Series()).get(ticker, float("nan"))
    
    if math.isnan(curr) or math.isnan(prev) or prev == 0:
        return float("nan")
    return ((curr - prev) / prev) * 100

def _pct_txt(val: float) -> str:
    if val is None or math.isnan(val) or math.isinf(val):
        return "—"
    return f"{val:+.2f}%"

def _perf_class(val: float) -> str:
    if val is None or math.isnan(val):
        return "bb-flat"
    if val > 0:
        return "bb-pos"
    if val < 0:
        return "bb-neg"
    return "bb-flat"

def bb_fmt(ticker_label: str, ticker_sym: str) -> str:
    if not h_data or ticker_sym not in h_data.get('curr', {}):
        return f"<div><span class='bb-label'>{ticker_label}</span> <span class='bb-muted'>NO DATA</span></div>"
        
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

def btc_fmt() -> str:
    if not h_data or 'BTC-USD' not in h_data.get('curr', {}):
        return "<div><span class='bb-muted'>BTC-USD NO DATA</span></div>"
        
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
    st.markdown(f'<div class="bb-terminal"><p class="bb-ribbon-sub" style="font-weight:bold; color:#888;">{text}</p></div>', unsafe_allow_html=True)

def switchboard_card(page: str, title: str, blurb: str) -> None:
    with st.container(border=True):
        st.page_link(page, label=title, use_container_width=True)
        st.caption(blurb)

# --- 5. HEADER SECTION ---
col_t1, col_t2 = st.columns([1, 1])

with col_t1:
    st.markdown(
        f"""<div class="bb-terminal" style="line-height:1.25;">
        <span class="bb-hero-title" style="font-size: 24px; font-weight: bold;">E-TERMINAL</span>
        <span class="bb-hero-date" style="margin-left:8px; color:#888;">// {datetime.now().strftime('%d %b %Y')}</span>
        </div>""",
        unsafe_allow_html=True,
    )

with col_t2:
    if h_data and '^VIX' in h_data.get('curr', {}):
        vix_val = h_data['curr']['^VIX']
        vix_pct = calc_perf('^VIX', 'prev_1d')
        
        daily_implied = vix_val / math.sqrt(256)
        monthly_implied = vix_val / math.sqrt(12)
        vix_chg_cls = _perf_class(vix_pct)

        st.markdown(f"""
        <div class="bb-terminal" style="text-align: right; margin-top: 6px;">
            <div style="font-size: 17px; white-space: nowrap;">
                <span class="bb-vix-tag" style="background:#333; padding:2px 6px; border-radius:3px;">VIX</span>
                <span class="bb-price" style="font-size: 22px; margin-left: 6px; font-weight:bold;">{vix_val:.2f}</span>
                <span class="{vix_chg_cls}" style="font-size: 16px;"> ({vix_pct:+.2f}%)</span>
            </div>
            <div class="bb-muted" style="font-size: 14px; margin-top: 5px; white-space: nowrap; color:#aaa;">
                DAILY σ <span class="bb-cyan" style="color:#00ffff;">{daily_implied:.2f}%</span>
                <span class="bb-sep" style="margin: 0 6px;">·</span>
                30D σ <span class="bb-cyan" style="color:#00ffff;">{monthly_implied:.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Ticker Ribbon
st.markdown("---")
st.markdown('<h3 class="bb-switchboard-section">MARKETS</h3>', unsafe_allow_html=True)

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
        <p style="font-size:14px; margin:0;"><span class="bb-muted" style="color:#888;">FEED:</span> <span class="bb-pos" style="color:#00FF00;">ACTIVE</span></p>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- 6. SWITCHBOARD DIRECTORY ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<h3 class="bb-switchboard-section">[A] SYSTEMIC INPUTS</h3>', unsafe_allow_html=True)
    switchboard_card("pages/01_Macro_Bonds.py", "Macro Bond Watch", "The cost of money. Treasury curve and spread dynamics.")
    switchboard_card("pages/02_Inflation.py", "Inflation", "The rate of debasement. CPI, PPI, and breakevens.")
    switchboard_card("pages/03_Liquidity.py", "Liquidity", "The systemic money flow. Fed Balance Sheet & Repo.")

with col2:
    st.markdown('<h3 class="bb-switchboard-section">[B] RISK & EQUITY FLOW</h3>', unsafe_allow_html=True)
    switchboard_card("pages/04_Global_Markets.py", "Global Markets", "Cross-border liquidity and FX correlations.")
    switchboard_card("pages/05_Market_Heatmap.py", "Market Heatmap", "Breadth, internals, and immediate price action.")
    switchboard_card("pages/06_Sectors.py", "Sectors", "Capital rotation and internal equity breadth.")
    switchboard_card("pages/07_Options_Flow.py", "Options Flow", "Unusual activity, sweeps, and flow versus spot.")

with col3:
    st.markdown('<h3 class="bb-switchboard-section">[C] HARD ASSETS & ALPHA</h3>', unsafe_allow_html=True)
    switchboard_card("pages/08_Crypto_Terminal.py", "Crypto Terminal", "Digital beta. Correlation to DXY and local BTC liquidity.")
    switchboard_card("pages/09_Metals.py", "Metals", "Growth/Fear barometer. Gold, Silver, and Copper flows.")
    switchboard_card("pages/10_Energy.py", "Energy", "The global input cost. Oil, Gas, and Refined Products.")
    switchboard_card("pages/11_Positioning.py", "Positioning", "Crowding, CTA/dealer context, and net exposure.")
    switchboard_card("pages/12_Options_Analyzer.py", "Options Analyzer", "Structures, greeks, and scenario tools for single names.")