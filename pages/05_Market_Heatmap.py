import time
from datetime import datetime, timedelta
import sys
import os

import feedparser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Go up one level to grab our master theme file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from theme import inject_custom_css

# --- 1. PAGE CONFIG & SETUP ---
st.set_page_config(page_title="Dash 1.0", layout="wide")

# Cloud-Safe Session State Init
if "pg" not in st.session_state:
    st.session_state.pg = 0

# --- 2. GLOBAL CONSTANTS ---
CATEGORIES = {
    "B: Digital Assets": {"IBIT": "₿ IBIT", "MSTR": "₿ MSTR"},
    "C: Tech": {"MSFT": "💻 MSFT", "AAPL": "💻 AAPL", "GOOGL": "💻 GOOGL"},
    "D: Semis": {"NVDA": "📟 NVDA", "AMD": "📟 AMD", "AVGO": "📟 AVGO"},
    "A: Indicators": {
        "TIP": "🟦 TIP", "TLT": "🟦 TLT", "DX-Y.NYB": "🟦 DXY",
        "^TNX": "🟦 10Y", "^VIX": "💀 VIX",
    },
    "E: Energy/Inf": {"XLE": "🔥 XLE", "XOM": "🔥 XOM", "DBC": "🔥 DBC"},
    "F: Financials": {"KBE": "🏦 KBE", "JPM": "🏦 JPM", "BRK-B": "🏦 BRK"},
    "G: Defensive": {"SCHD": "🛡️ SCHD", "WMT": "🛡️ WMT", "PG": "🛡️ PG"},
}

COLOR_MAP = {
    "🟦 TIP": "#0000FF", "🟦 TLT": "#4169E1", "🟦 DXY": "#00BFFF", "🟦 10Y": "#191970",
    "💀 VIX": "#708090", "₿ IBIT": "#FF8C00", "₿ MSTR": "#E67E22", "💻 MSFT": "#00FFFF",
    "💻 AAPL": "#20B2AA", "💻 GOOGL": "#48D1CC", "📟 NVDA": "#FFD700", "📟 AMD": "#DAA520",
    "📟 AVGO": "#BDB76B", "🔥 XLE": "#FF0000", "🔥 XOM": "#DC143C", "🔥 DBC": "#8B0000",
    "🟡 GLD": "#FFD700", "🏦 KBE": "#800080", "🏦 JPM": "#9370DB", "🏦 BRK": "#4B0082",
    "🛡️ SCHD": "#008000", "🛡️ WMT": "#32CD32", "🛡️ PG": "#228B22",
}

CATEGORY_EMOJIS = {
    "Indicators": "📉", "Digital Assets": "₿", "Tech": "💻", "Semis": "📟",
    "Energy/Inf": "🔥", "Financials": "🏦", "Defensive": "🛡️",
}

RSS_URLS = {
    "CNBC Alerts": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=401&id=10000664",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/marketpulse/",
    "Yahoo": "https://finance.yahoo.com/news/rssindex",
    "FT": "https://www.ft.com/?format=rss",
}


# --- 3. DATA & UTILITY LAYER ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_market_data(ticker_list: list[str]) -> pd.DataFrame:
    for _ in range(3):
        try:
            df = yf.download(
                ticker_list + ["GLD"], period="3y", progress=False, auto_adjust=False, threads=True,
            )
            if isinstance(df.columns, pd.MultiIndex):
                if "Close" in df.columns.get_level_values(0):
                    df = df["Close"]
                else:
                    df = df.xs("Close", axis=1, level=0, drop_level=True)
            if not df.empty:
                if "^TNX" in df.columns:
                    df["^TNX"] = df["^TNX"] / 10
                return df.dropna(how="all")
        except Exception:
            time.sleep(2)
    return pd.DataFrame()

def get_perf_and_trend(series: pd.Series, days: int) -> tuple[str, str]:
    try:
        if len(series) < days:
            return "0.00%", "⚪"
        start_val = series.iloc[-days]
        end_val = series.iloc[-1]
        if start_val == 0 or pd.isna(start_val) or pd.isna(end_val):
            return "0.00%", "⚪"
        pct = ((end_val - start_val) / start_val) * 100
        return f"{pct:.2f}%", "🟢" if pct > 0 else "🔴"
    except Exception:
        return "0.00%", "⚪"

@st.cache_data(ttl=900, show_spinner=False)
def fetch_rss_feeds(active_feeds: dict, limit_days: int = 14) -> list:
    all_news = []
    limit = datetime.now() - timedelta(days=limit_days)
    for name, url in RSS_URLS.items():
        if active_feeds.get(name, False):
            try:
                feed = feedparser.parse(url)
                for entry in getattr(feed, "entries", []):
                    parsed_time = getattr(entry, "published_parsed", getattr(entry, "updated_parsed", None))
                    if parsed_time:
                        dt = datetime.fromtimestamp(time.mktime(parsed_time))
                        if dt > limit:
                            all_news.append({
                                "Date": dt, "Source": name, "Title": entry.title, "Link": entry.link,
                            })
            except Exception:
                continue
    return sorted(all_news, key=lambda x: x["Date"], reverse=True)


# --- 4. VISUALIZATION LAYER ---
def build_performance_chart(norm_data):
    fig = px.line(norm_data, log_y=True, template="plotly_dark", color_discrete_map=COLOR_MAP)
    fig.update_layout(hovermode="closest", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def build_correlation_heatmap(corr_matrix):
    masked = corr_matrix.mask(np.triu(np.ones_like(corr_matrix, dtype=bool)))
    fig = px.imshow(
        masked, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r",
        range_color=[-1, 1], template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Courier New, monospace", "color": "#00FF00"}
    )
    return fig

def draw_gauge(title: str, val: float, col, key: str) -> None:
    v = float(np.clip(val, -1, 1))
    color = (
        f"rgb(255, {int(255 * (1 - v))}, {int(255 * (1 - v))})" if v > 0
        else f"rgb({int(255 * (1 + v))}, {int(255 * (1 + v))}, 255)"
    )
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number", value=v,
            title={"text": title, "font": {"size": 14, "color": "#FFB100"}},
            number={"font": {"size": 24, "color": "#00FF00"}},
            gauge={
                "axis": {"range": [-1, 1], "tickvals": [-1, -0.5, 0, 0.5, 1], "tickfont": {"color": "#00FF00"}},
                "bar": {"color": color}, "bgcolor": "#1A1A1A", "borderwidth": 1, "bordercolor": "#333333"
            },
        )
    )
    fig.update_layout(
        height=170, margin=dict(l=10, r=10, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Courier New, monospace"},
    )
    col.plotly_chart(fig, width="stretch", key=key)


# --- 5. UI COMPONENTS ---
def render_sidebar():
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
        st.markdown("---")

        st.header("📐 Correlation Decoder")
        with st.expander("Detailed Quartile Interpretation", expanded=True):
            st.markdown("""
            **🔴 Positive (Synergy)**
            * **1.00:** Perfect Lockstep
            * **0.75 - 0.99:** Strong Synergy
            * **0.50 - 0.74:** Moderate Driver
            * **0.25 - 0.49:** Weak/Positive Drift
            * **0.00 - 0.24:** Noise/Neutral

            **🔵 Negative (Seesaw)**
            * **-1.00:** Perfect Inverse
            * **-0.75 to -0.99:** Strong Inverse
            * **-0.50 to -0.74:** Strong Hedge
            * **-0.25 to -0.49:** Weak Divergence
            * **0.00 to -0.24:** Noise/Neutral
            """)

def render_performance_snapshot(raw_data, safe_rename_map, min_date, max_date, default_start):
    st.subheader("1. Performance Snapshot")
    
    comp_start, comp_end = st.slider(
        "Chart Timeframe Window",
        min_value=min_date, max_value=max_date,
        value=(default_start, max_date), format="DD/MM/YYYY"
    )
    
    trading_days_selected = len(raw_data.loc[str(comp_start):str(comp_end)])
    st.markdown(f"**Period:** {comp_start.strftime('%d/%m/%Y')} ➔ {comp_end.strftime('%d/%m/%Y')} <span style='color:#FFB100;'>({trading_days_selected} Trading Days)</span>", unsafe_allow_html=True)

    with st.expander("⚙️ Filter Chart Assets by Category", expanded=False):
        selected_chart_labels = []
        cols = st.columns(len(CATEGORIES))
        for i, (cat, assets) in enumerate(CATEGORIES.items()):
            with cols[i]:
                st.markdown(f"**{cat.split(': ')[1]}**")
                for t, l in assets.items():
                    if t in safe_rename_map and st.checkbox(l, value=True, key=f"toggle_{t}"):
                        selected_chart_labels.append(l)

    if not selected_chart_labels:
        st.warning("Please select at least one asset to display the chart.")
    else:
        perf_window = raw_data.loc[str(comp_start):str(comp_end)].rename(columns=safe_rename_map)
        valid_chart_labels = [lbl for lbl in selected_chart_labels if lbl in perf_window.columns]
        
        if valid_chart_labels and not perf_window.empty:
            norm_data = (perf_window[valid_chart_labels] / perf_window[valid_chart_labels].iloc[0]) * 100
            st.plotly_chart(build_performance_chart(norm_data), width="stretch")
        else:
            st.warning("Selected assets are not available in this data snapshot.")

def render_market_dna_heatmap(raw_data, safe_rename_map, min_date, max_date):
    st.divider()
    st.subheader("2. Market DNA Heatmap 🔥")
    
    col_snap, col_dial = st.columns(2)
    with col_snap:
        snap_date_sel = st.slider(
            "Target Snapshot Day", min_value=min_date, max_value=max_date,
            value=max_date, format="DD/MM/YYYY"
        )
        closest_snap_idx = raw_data.index.get_indexer([pd.Timestamp(snap_date_sel)], method='pad')[0]
        actual_snap_date = raw_data.index[closest_snap_idx]
        
        days_ago = len(raw_data.loc[pd.Timestamp(actual_snap_date):pd.Timestamp(max_date)]) - 1
        day_text = "Today" if days_ago == 0 else f"{days_ago} Trading Days Ago"
        st.markdown(f"**Locked Date:** {actual_snap_date.strftime('%d/%m/%Y')} <span style='color:#FFB100;'>({day_text})</span>", unsafe_allow_html=True)
        
    with col_dial:
        window_size = st.slider("🎛️ Sensitivity Dial (Lookback Window)", min_value=5, max_value=60, value=21, step=1)
        st.markdown(f"**Engine Setting:** <span style='color:#00FF00;'>Computing {window_size}-Day Rolling Correlation</span>", unsafe_allow_html=True)

    full_window = raw_data.iloc[: closest_snap_idx + 1]
    effective_window_size = min(window_size, len(full_window))
    corr_window = full_window.iloc[-effective_window_size:].rename(columns=safe_rename_map)

    ordered_labels = [safe_rename_map[t] for t in safe_rename_map if t != "GLD"]
    if "GLD" in safe_rename_map: ordered_labels.append("🟡 GLD")

    present_labels = [lbl for lbl in ordered_labels if lbl in corr_window.columns]
    
    corr_matrix = pd.DataFrame()
    if len(present_labels) >= 2:
        corr_matrix = corr_window[present_labels].corr()
        st.plotly_chart(build_correlation_heatmap(corr_matrix), width="stretch")
    else:
        st.error("Not enough overlapping data to compute correlations.")
        
    return full_window, corr_matrix, actual_snap_date, window_size, present_labels

def render_macro_command_center(full_window, corr_matrix, safe_rename_map, actual_snap_date, window_size, present_labels):
    st.divider()
    st.subheader("3. Macro Command Center: Gauges")
    
    if len(present_labels) < 2 or corr_matrix.empty:
        return

    anchors = [
        ("TLT", "📉 Bonds"), ("^TNX", "🏛️ 10Y Yield"), ("DX-Y.NYB", "💵 US Dollar"),
        ("MSTR", "₿ Crypto"), ("MSFT", "💻 Tech"), ("NVDA", "📟 Semis"),
        ("XLE", "🔥 Energy"), ("JPM", "🏦 Banks"), ("WMT", "🛡️ Defensive"), ("^VIX", "💀 Volatility"),
    ]

    for ticker, row_title in anchors:
        if ticker not in full_window.columns or ticker not in safe_rename_map:
            continue

        st.markdown(f"### {row_title} vs Sector Averages")
        t_col, g_col = st.columns([2, 8])
        anchor_s = full_window[ticker]

        p_data = {
            "Period": ["1D", "1M", "3M", "6M"],
            "Perf %": [get_perf_and_trend(anchor_s, d)[0] for d in [2, 21, 63, 126]],
            "Trend": [get_perf_and_trend(anchor_s, d)[1] for d in [2, 21, 63, 126]],
        }
        t_col.dataframe(pd.DataFrame(p_data), hide_index=True)

        active_cats = [c for c in CATEGORIES if ticker not in CATEGORIES[c] and c != "A: Indicators"]
        gauge_cols = g_col.columns(len(active_cats) + 1)
        anchor_lbl = safe_rename_map[ticker]
        section_audit = []

        for i, cat_name in enumerate(active_cats):
            cat_ticks = [tk for tk in CATEGORIES[cat_name] if tk in safe_rename_map]
            cat_labels = [safe_rename_map[tk] for tk in cat_ticks if safe_rename_map[tk] in corr_matrix.columns]
            if not cat_labels or anchor_lbl not in corr_matrix.index:
                continue

            indiv_vals = [corr_matrix.loc[anchor_lbl, lbl] for lbl in cat_labels]
            avg_val = float(np.mean(indiv_vals))
            short_name = cat_name.split(": ")[1]
            emoji = CATEGORY_EMOJIS.get(short_name, "")
            
            draw_gauge(f"{emoji} {short_name}", avg_val, gauge_cols[i], f"g_{ticker}_{cat_name}_{actual_snap_date}_{window_size}")
            
            section_audit.append({
                "Sector": short_name, "Values": ", ".join([f"{v:.2f}" for v in indiv_vals]), "Avg": f"{avg_val:.2f}",
            })

        if "🟡 GLD" in corr_matrix.columns and anchor_lbl in corr_matrix.index:
            draw_gauge("🟡 Gold", corr_matrix.loc[anchor_lbl, "🟡 GLD"], gauge_cols[-1], f"gold_{ticker}_{actual_snap_date}_{window_size}")

        with st.expander(f"🧮 {row_title} Math Audit"):
            st.dataframe(pd.DataFrame(section_audit), hide_index=True)

def render_regime_narratives(full_window):
    st.divider()
    if "^TNX" in full_window.columns and "DX-Y.NYB" in full_window.columns and len(full_window) >= 6:
        y_chg = full_window["^TNX"].diff(5).iloc[-1]
        d_chg = full_window["DX-Y.NYB"].diff(5).iloc[-1]
    else:
        y_chg, d_chg = 0.0, 0.0

    regime = (
        "STAGFLATION (Risk-Off)" if y_chg > 0 and d_chg > 0
        else "REFLATION (Sector Rotation)" if y_chg > 0
        else "DEFLATION (Risk-Off)" if d_chg > 0
        else "GOLDILOCKS (Risk-On)"
    )

    c_reg, c_nar = st.columns([1, 2])
    c_reg.metric("Detected Regime", regime, delta=f"Y:{y_chg:.2f} | D:{d_chg:.2f}", delta_color="inverse")

    with c_nar:
        st.subheader("📜 Macro States & Dependencies")
        st.markdown(r"""
        * **Goldilocks (Risk-On):** Yields $\downarrow$ + Dollar $\downarrow \rightarrow$ Broad Expansion. Capital flows into Tech, Crypto, and high-beta risk assets.
        * **Stagflation (Risk-Off / Squeeze):** Yields $\uparrow$ + Dollar $\uparrow \rightarrow$ Liquidity Squeeze. Valuations compress across the board; cash is king.
        * **Reflation (Sector Rotation):** Yields $\uparrow$ + Dollar $\downarrow \rightarrow$ Growth under pressure. Capital rotates into Value, Energy, and Financials.
        * **Deflation (Risk-Off / Flight to Safety):** Yields $\downarrow$ + Dollar $\uparrow \rightarrow$ Growth shock. Capital hides in Treasury Bonds, Gold, and Defensive stalwarts.
        """)

def render_footer_summary():
    st.divider()
    st.subheader("📝 Analysis Summary & Thesis")
    st.markdown(r"""
    <div style="font-size:18px; line-height:1.6;">
    <ul>
        <li><b>The Liquidity Squeeze (TLT vs Tech):</b> High negative correlations indicate a valuation/discount-rate squeeze. If they move together, it is a broad liquidity event.</li>
        <li><b>The Reflation Trade (Energy vs Banks):</b> Look for high positive synergy; Energy driving yields typically bolsters Bank margins.</li>
        <li><b>The Wrecking Ball (DXY):</b> When the Dollar correlates positively with all assets, we are in a 'Dollar Milkshake' flight to safety.</li>
        <li><b>The Digital Hedge (VIX vs Crypto):</b> Inverse correlation to VIX signals 'Digital Gold'. Moving with VIX signals 'High-Beta Risk'.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

def render_terminal_feed():
    st.header("🗞️ Macro Terminal Feed")
    
    with st.expander("⚙️ Feed Configuration", expanded=True):
        st.markdown("Toggle active sources for the terminal scrape:")
        fc1, fc2, fc3, fc4 = st.columns(4)
        active_feeds = {
            "CNBC Alerts": fc1.checkbox("CNBC Breaking", True),
            "MarketWatch": fc2.checkbox("MarketPulse", True),
            "Yahoo": fc3.checkbox("Yahoo Finance", True),
            "FT": fc4.checkbox("Financial Times", True),
        }
        
    st.markdown("---")

    all_news = fetch_rss_feeds(active_feeds)
    start = st.session_state.pg * 50
    
    for item in all_news[start : start + 50]:
        st.write(f"**{item['Date'].strftime('%d/%m %H:%M')}** | `{item['Source']}` : [{item['Title']}]({item['Link']})")

    c1, c2 = st.columns(2)
    if st.session_state.pg > 0 and c1.button("⬅️ Previous"):
        st.session_state.pg -= 1
        st.rerun()
    if len(all_news) > start + 50 and c2.button("Next ➡️"):
        st.session_state.pg += 1
        st.rerun()


# --- 6. MAIN EXECUTION ---
def main():
    inject_custom_css()
    render_sidebar()

    # Data Initialization
    all_tickers = list({t for c in CATEGORIES.values() for t in c.keys()} | {"GLD"})
    raw_data = load_market_data(all_tickers)
    
    rename_map = {t: l for cat in CATEGORIES.values() for t, l in cat.items()}
    rename_map["GLD"] = "🟡 GLD"

    if raw_data.empty:
        st.error("📡 Yahoo Finance API rate limit hit or unavailable. Please try again in a few minutes.")
        st.stop()

    available_tickers = [t for t in rename_map if t in raw_data.columns]
    if not available_tickers:
        st.error("No expected tickers were returned by Yahoo Finance in this run.")
        st.stop()

    safe_rename_map = {t: rename_map[t] for t in available_tickers}
    raw_data = raw_data[available_tickers]

    # Date Boundaries Calculate
    last_date = raw_data.index[-1].date()
    min_date_252 = raw_data.index[-252].date() if len(raw_data) >= 252 else raw_data.index[0].date()
    default_start = raw_data.index[-30].date() if len(raw_data) >= 30 else raw_data.index[0].date()

    # Render Tabs
    tab1, tab2 = st.tabs(["📊 Market Analysis", "📰 Terminal Feed"])

    with tab1:
        render_performance_snapshot(raw_data, safe_rename_map, min_date_252, last_date, default_start)
        
        full_window, corr_matrix, actual_snap_date, window_size, present_labels = render_market_dna_heatmap(
            raw_data, safe_rename_map, min_date_252, last_date
        )
        
        render_macro_command_center(full_window, corr_matrix, safe_rename_map, actual_snap_date, window_size, present_labels)
        render_regime_narratives(full_window)
        render_footer_summary()

    with tab2:
        render_terminal_feed()

if __name__ == "__main__":
    main()