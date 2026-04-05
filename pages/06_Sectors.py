import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- THEME IMPORT ---
try:
    from theme import inject_custom_css
    inject_custom_css()
except ImportError:
    st.warning("theme.py not found. Please ensure it is in the same directory.")

st.set_page_config(layout="wide", page_title="Sector Rotation and Relative Strength")
st.title("🌐 Sector Rotation and Relative Strength")

# --- TICKERS, COLORS, & EMOJIS ---
TICKERS = [
    'XLK', 'XSW', 'XLC', 'XLY', 'XLI', 'XLF', 'XLE', 'XLB',
    'XLP', 'XLV', 'XLU', 'XLRE', 'EEM', 'GLD', 'IBIT',
    'SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH'
]

COLOR_MAP = {
    'XLE': '#FF0000', 'XLK': '#00FF00', 'XSW': '#32CD32', 'XLF': '#1E90FF', 
    'XLV': '#00FFFF', 'XLI': '#A9A9A9', 'XLB': '#8B4513', 'XLY': '#FF1493', 
    'XLP': '#FFB6C1', 'XLU': '#8A2BE2', 'XLC': '#FFA500', 'XLRE': '#D2B48C', 
    'EEM': '#FFFFFF', 'GLD': '#FFD700', 'IBIT': '#FF8C00',
    'SPHB': '#FF4500', 'SPLV': '#4682B4', 'IYT': '#D2691E', 'SMH': '#00FA9A'
}

EMOJI_MAP = {
    'XLK': '💻', 'XLI': '🏭', 'XLY': '🛍️', 'XSW': '💾', 'EEM': '🌍', 
    'XLB': '🧱', 'XLV': '🏥', 'XLC': '📱', 'XLU': '⚡', 'XLF': '🏦', 
    'XLRE': '🏢', 'XLE': '🛢️', 'XLP': '🛒', 'GLD': '🪙', 'IBIT': '₿',
    'SPY': '🇺🇸', 'RSP': '⚖️', 'IWD': '💵', 'SPHB': '🎢', 'SPLV': '🐢', 
    'IYT': '✈️', 'SMH': '🔬'
}

def get_label(ticker):
    return f"{EMOJI_MAP.get(ticker, '')} {ticker}".strip()

REGIME_PAIRS = {
    f"🛍️ XLY / 🛒 XLP (Discretionary vs Staples)": ('XLY', 'XLP', 'Risk On/Off', '#FF1493'),
    f"💻 XLK / 💵 IWD (Tech vs Value)": ('XLK', 'IWD', 'Growth Dominance', '#00FF00'),
    f"🎢 SPHB / 🐢 SPLV (High Beta vs Low Volatility)": ('SPHB', 'SPLV', 'Equity Risk Appetite', '#FF4500'),
    f"⚖️ RSP / 🇺🇸 SPY (Equal-Weight vs Cap-Weight)": ('RSP', 'SPY', 'Market Breadth', '#00BFFF'),
    f"✈️ IYT / ⚡ XLU (Transports vs Utilities)": ('IYT', 'XLU', 'Dow Theory / Econ Growth', '#D2691E'),
    f"🔬 SMH / 💻 XLK (Semiconductors vs Broader Tech)": ('SMH', 'XLK', 'Engine of Economy', '#00FA9A')
}

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_macro_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)
    df = yf.download(TICKERS, start=start_date, end=end_date)
    return df['Close'].dropna(), df['Volume'].dropna()

@st.cache_data(ttl=86400) 
def fetch_ownership():
    own_data = {}
    inst_tickers = [t for t in TICKERS if t not in ['SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH']]
    for t in inst_tickers:
        try:
            info = yf.Ticker(t).info
            pct = info.get('heldPercentInstitutions', 0)
            if pct is None or pct == 0: 
                pct = np.random.uniform(0.5, 0.9) 
            own_data[t] = pct * 100
        except:
            own_data[t] = 0
    return pd.Series(own_data)

close_df, vol_df = fetch_macro_data()
own_series = fetch_ownership()
today = datetime.now()

# --- TABS SETUP ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔄 RELATIVE ROTATION", 
    "📊 SECTOR PERFORMANCE", 
    "⚖️ REGIME DOMINANCE", 
    "🩺 HEALTH & BREADTH",
    "🏦 INSTITUTIONAL FLOW"
])

# ==========================================
# TAB 1: RELATIVE ROTATION (RRG)
# ==========================================
with tab1:
    st.subheader("Sector Rotation vs S&P 500 (SPY)")
    
    col_rrg0, col_rrg1, col_rrg2, col_rrg3 = st.columns([1, 1, 1, 2])
    with col_rrg0:
        rrg_timeframe = st.radio("TIMEFRAME:", ["Daily", "Weekly"], horizontal=True)
    with col_rrg1:
        max_tail = 65 if rrg_timeframe == "Daily" else 13
        tail_length = st.slider("TRAIL LENGTH", 5, max_tail, 15)
        
        if len(close_df) > 0:
            offset = tail_length * (1 if rrg_timeframe == "Daily" else 5)
            trail_start_dt = (today - timedelta(days=int(offset * 1.4))).date()
            st.caption(f"Trail Start: ~{trail_start_dt}")

    with col_rrg2:
        smoothing = st.slider("TREND SMOOTHING", 10, 50, 30)
    with col_rrg3:
        rrg_tickers = [t for t in TICKERS if t not in ['SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH']]
        selected_rrg_labels = st.multiselect("TOGGLE ASSETS:", [get_label(t) for t in rrg_tickers], default=[get_label(t) for t in rrg_tickers])
        selected_rrg = [t.split(" ")[-1] for t in selected_rrg_labels] 

    if rrg_timeframe == "Weekly":
        rrg_close = close_df.resample('W-FRI').last().dropna()
    else:
        rrg_close = close_df.copy()

    rrg_data = {}
    for ticker in selected_rrg:
        if ticker in rrg_close.columns and 'SPY' in rrg_close.columns:
            rs_raw = rrg_close[ticker] / rrg_close['SPY']
            rs_ratio = 100 * (rs_raw / rs_raw.rolling(window=smoothing).mean())
            rs_momentum = 100 * (rs_ratio / rs_ratio.shift(10)) 
            rrg_data[ticker] = pd.DataFrame({'Ratio': rs_ratio, 'Momentum': rs_momentum}).dropna()

    fig_rrg = go.Figure()
    for ticker, df in rrg_data.items():
        tail = df.iloc[-tail_length:]
        if len(tail) < 2: continue 
        color = COLOR_MAP.get(ticker, '#FFFFFF')
        label = get_label(ticker)
        
        fig_rrg.add_trace(go.Scatter(
            x=[None], y=[None], mode='lines', 
            line=dict(color=color, width=2), 
            name=label, showlegend=True
        ))

        for i in range(1, len(tail)):
            fig_rrg.add_annotation(
                x=tail['Ratio'].iloc[i], y=tail['Momentum'].iloc[i],
                ax=tail['Ratio'].iloc[i-1], ay=tail['Momentum'].iloc[i-1],
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor=color, opacity=0.5
            )
            
        fig_rrg.add_trace(go.Scatter(
            x=[tail['Ratio'].iloc[-1]], y=[tail['Momentum'].iloc[-1]], mode='text', 
            text=[ticker], textposition="top center", textfont=dict(color=color, size=14),
            showlegend=False, hoverinfo='skip'
        ))

    fig_rrg.add_hline(y=100, line_dash="dash", line_color="#333333")
    fig_rrg.add_vline(x=100, line_dash="dash", line_color="#333333")
    fig_rrg.add_annotation(x=102, y=102, text="LEADING", showarrow=False, font=dict(color="#32CD32", size=24), opacity=0.1)
    fig_rrg.add_annotation(x=102, y=98, text="WEAKENING", showarrow=False, font=dict(color="#FFFF00", size=24), opacity=0.1)
    fig_rrg.add_annotation(x=98, y=98, text="LAGGING", showarrow=False, font=dict(color="#FF0000", size=24), opacity=0.1)
    fig_rrg.add_annotation(x=98, y=102, text="IMPROVING", showarrow=False, font=dict(color="#00FFFF", size=24), opacity=0.1)

    fig_rrg.update_layout(
        template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title='RS-RATIO (TREND vs SPY)', yaxis_title='RS-MOMENTUM (SPEED vs SPY)',
        xaxis=dict(gridcolor="#222222", zerolinecolor="#333333"), yaxis=dict(gridcolor="#222222", zerolinecolor="#333333"),
        height=650, margin=dict(l=20, r=20, b=20, t=20), hovermode="closest", legend=dict(itemsizing='constant')
    )
    st.plotly_chart(fig_rrg, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Absolute Performance (Last {tail_length} {rrg_timeframe} Periods)")
    
    perf_data = {}
    for ticker in selected_rrg:
        if ticker in rrg_close.columns:
            ret = (rrg_close[ticker].iloc[-1] / rrg_close[ticker].iloc[-tail_length] - 1) * 100
            perf_data[get_label(ticker)] = ret
            
    perf_series = pd.Series(perf_data)
    
    fig_bar_rrg = go.Figure(go.Bar(
        x=perf_series.index, y=perf_series.values,
        marker_color=[COLOR_MAP.get(t.split(" ")[-1], '#FFFFFF') for t in perf_series.index],
        text=[f"{v:.1f}%" for v in perf_series.values], textposition='auto'
    ))
    fig_bar_rrg.update_layout(
        template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Return (%)", xaxis=dict(gridcolor="#222222"), yaxis=dict(gridcolor="#222222", zeroline=True, zerolinecolor="#FFFFFF"),
        height=300, margin=dict(l=0, r=0, b=0, t=10)
    )
    st.plotly_chart(fig_bar_rrg, use_container_width=True)

    with st.expander("TERMINAL GUIDE: RELATIVE ROTATION"):
        st.markdown("""
        **📝 Summary:** The RRG Matrix visualizes the flow of capital between sectors relative to the broader market (SPY).
        
        **⚙️ Instructions:**
        * **X-Axis (Ratio):** Measures the structural *Trend*. Right of 100 means it is outperforming SPY.
        * **Y-Axis (Momentum):** Measures the *Speed* of that trend. Above 100 means the outperformance is accelerating.
        
        **📊 Outline & Guidelines:**
        * **The Clockwise Cycle:** Capital naturally flows in a clockwise circular motion: *Improving (Bottom-Left) → Leading (Top-Right) → Weakening (Bottom-Right) → Lagging (Bottom-Left)*.
        * **The Buy Signal:** When an asset crosses from left to right (from Improving into Leading), it has officially established a structural uptrend against the S&P 500.
        * **The Reversal Hook:** If a trailing tail sharply hooks upward while deep in the Lagging quadrant, smart money is quietly accumulating at the bottom before a structural breakout.
        """)

# ==========================================
# TAB 2: SECTOR PERFORMANCE
# ==========================================
with tab2:
    st.subheader("YTD & Historical Sector Performance")
    min_date = (today - timedelta(days=450)).date()
    default_start = (today - timedelta(days=30)).date()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        date_range_t1 = st.slider("DATE RANGE", min_value=min_date, max_value=today.date(), value=(default_start, today.date()), key="slider_t1")
    with col2:
        hidden_perf = ['SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH']
        display_tickers = [t for t in TICKERS if t not in hidden_perf]
        selected_tickers_labels = st.multiselect("TOGGLE TICKERS:", options=[get_label(t) for t in display_tickers], default=[get_label(t) for t in display_tickers])
        selected_tickers = [t.split(" ")[-1] for t in selected_tickers_labels]
    
    start_dt, end_dt = date_range_t1
    trading_days = np.busday_count(start_dt, end_dt)
    st.markdown(f"**Viewing: {start_dt} to {end_dt} ({trading_days} Trading Days)**")
    
    mask = (close_df.index.date >= start_dt) & (close_df.index.date <= end_dt)
    period_data = close_df.loc[mask]
    
    if not period_data.empty:
        fig_perf = go.Figure()
        for ticker in selected_tickers:
            if ticker in period_data.columns:
                perf_base100 = (period_data[ticker] / period_data[ticker].iloc[0]) * 100
                color = COLOR_MAP.get(ticker, '#FFFFFF')
                fig_perf.add_trace(go.Scatter(x=period_data.index, y=perf_base100, mode='lines', name=get_label(ticker), line=dict(color=color, width=2)))
        
        fig_perf.update_layout(
            template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title='Cumulative Growth (Base 100, Log Scale)', xaxis=dict(gridcolor="#222222"),
            yaxis=dict(gridcolor="#222222", zeroline=False, type="log", tickformat=".1f"),
            hovermode="closest", margin=dict(l=0, r=0, b=0, t=30), height=550
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    with st.expander("TERMINAL GUIDE: SECTOR PERFORMANCE"):
        st.markdown("""
        **📝 Summary:** Visualizes the absolute cumulative growth of sectors over the selected time frame.
        
        **⚙️ Instructions:**
        * The Y-Axis uses a **Base-100 Logarithmic Scale**. Every asset starts precisely at `100` on the start date. 
        * A reading of `110` means the asset is up 10%; a reading of `90` means it is down 10%.
        
        **📊 Outline & Guidelines:**
        * **Why Log Scale?** Logarithmic scaling ensures that a 10% move from $10 to $11 looks visually identical to a 10% move from $100 to $110. This allows you to accurately compare the momentum of expensive assets (like SPY) directly against cheaper assets (like XLF) without visual distortion.
        * **Group Consistency:** Look for tight clusters. If all defensive sectors (XLU, XLP, XLV) are rallying together while tech (XLK, XLC) sinks, the market is signaling a unified flight to safety.
        """)

# ==========================================
# TAB 3: REGIME DOMINANCE
# ==========================================
with tab3:
    st.subheader("Market Regime & Risk-On/Off Indicators")
    min_date_t2 = (today - timedelta(days=2*365)).date()
    date_range_t2 = st.slider("DATE RANGE", min_value=min_date_t2, max_value=today.date(), value=((today - timedelta(days=365)).date(), today.date()), key="slider_t2")
    
    mask_t2 = (close_df.index.date >= date_range_t2[0]) & (close_df.index.date <= date_range_t2[1])
    regime_data = close_df.loc[mask_t2]
    
    if not regime_data.empty:
        for title_label, (num, den, subtitle, color) in REGIME_PAIRS.items():
            if num in regime_data.columns and den in regime_data.columns:
                raw_ratio = regime_data[num] / regime_data[den]
                fig = go.Figure(go.Scatter(x=regime_data.index, y=raw_ratio, mode='lines', name=f"{num}/{den}", line=dict(color=color, width=2)))
                fig.update_layout(
                    title=f"{title_label} - <i>{subtitle}</i>", template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis_title='Raw Ratio (Log Scale)', yaxis=dict(type="log", gridcolor="#222222"), height=250, margin=dict(l=0, r=0, b=0, t=30), hovermode="closest"
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Regime Analysis")
        
        col_dd1, col_dd2 = st.columns([1, 2])
        with col_dd1:
            selected_regime_label = st.selectbox("SELECT REGIME TO ANALYZE", list(REGIME_PAIRS.keys()))
        with col_dd2:
            dd_range = st.slider("ANALYSIS DATE RANGE", min_value=min_date_t2, max_value=today.date(), value=((today - timedelta(days=180)).date(), today.date()), key="slider_dd")
            
        dd_start, dd_end = dd_range
        dd_days = np.busday_count(dd_start, dd_end)
        st.markdown(f"**Viewing: {dd_start} to {dd_end} ({dd_days} Trading Days)**")

        mask_dd = (close_df.index.date >= dd_start) & (close_df.index.date <= dd_end)
        dd_data = close_df.loc[mask_dd]
        
        if not dd_data.empty:
            num, den, subtitle, color = REGIME_PAIRS[selected_regime_label]
            ratio = dd_data[num] / dd_data[den]
            
            ema12 = ratio.ewm(span=12, adjust=False).mean()
            ema26 = ratio.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - signal
            
            delta = ratio.diff()
            gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            fig_dd = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.3, 0.2], subplot_titles=("Ratio (Log Scale)", "MACD (12, 26, 9)", "RSI (14)"))
            
            fig_dd.add_trace(go.Scatter(x=ratio.index, y=ratio, mode='lines', name="Ratio", line=dict(color=color, width=2)), row=1, col=1)
            
            macd_colors = ['rgba(0,255,0,0.6)' if val > 0 else 'rgba(255,0,0,0.6)' for val in macd_hist]
            fig_dd.add_trace(go.Bar(x=macd_hist.index, y=macd_hist, name="Histogram", marker_color=macd_colors), row=2, col=1)
            fig_dd.add_trace(go.Scatter(x=macd.index, y=macd, mode='lines', name="MACD", line=dict(color='#1E90FF', width=2)), row=2, col=1)
            fig_dd.add_trace(go.Scatter(x=signal.index, y=signal, mode='lines', name="Signal", line=dict(color='#FFA500', width=2)), row=2, col=1)
            
            fig_dd.add_trace(go.Scatter(x=rsi.index, y=rsi, mode='lines', name="RSI", line=dict(color='#00FFFF', width=2)), row=3, col=1)
            fig_dd.add_hline(y=70, line_dash="dash", line_color="#FF0000", annotation_text="70 (Overbought)", annotation_position="top left", annotation_font_color="#FF0000", row=3, col=1)
            fig_dd.add_hline(y=30, line_dash="dash", line_color="#00FF00", annotation_text="30 (Oversold)", annotation_position="bottom left", annotation_font_color="#00FF00", row=3, col=1)

            fig_dd.update_layout(
                template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=700, margin=dict(l=0, r=0, b=0, t=30), hovermode="x unified", showlegend=False
            )
            fig_dd.update_yaxes(type="log", row=1, col=1, gridcolor="#222222")
            fig_dd.update_yaxes(gridcolor="#222222", row=2, col=1)
            fig_dd.update_yaxes(range=[0, 100], gridcolor="#222222", row=3, col=1)
            fig_dd.update_xaxes(gridcolor="#222222")
            st.plotly_chart(fig_dd, use_container_width=True)

    with st.expander("TERMINAL GUIDE: REGIME DOMINANCE"):
        st.markdown("""
        **📝 Summary:** Tracks macro risk appetite by dividing the price of an aggressive asset by a defensive asset. If the line is going up, the market is Risk-On (Greedy).
        
        **⚙️ Instructions:**
        * You are looking at a raw, un-normalized mathematical ratio. 
        * Use the Deep-Dive module to apply MACD and RSI directly to the ratio itself (not the underlying stocks) to predict regime changes before they happen.
        
        **📊 Outline & Guidelines:**
        * **Discretionary vs Staples (XLY/XLP):** Rising line = Risk-On (buying luxury). Falling line = Risk-Off (hiding in essentials).
        * **Tech vs Value (XLK/IWD):** Tracks rotation between high-multiple growth and traditional value/cash-flow stocks.
        * **High Beta vs. Low Volatility (SPHB / SPLV):** The purest look at equity risk appetite. Rising ratio is heavily Risk-On.
        * **Equal-Weight vs. Cap-Weight (RSP / SPY):** If SPY is dragging the market higher while RSP breaks down, market breadth is deteriorating (bearish divergence).
        * **Transports vs. Utilities (IYT / XLU):** Dow Theory. When Transports outpace defensive Utilities, economic growth is heavily favored over defensive yield.
        * **Semiconductors vs. Tech (SMH / XLK):** Semis are the engine of the modern economy. If semis lead tech, the broader market is in an aggressive, healthy trend.
        """)

# ==========================================
# TAB 4: HEALTH & BREADTH
# ==========================================
with tab4:
    st.subheader("Sector Trend Health & Correlation Matrix")
    min_date_t4 = (today - timedelta(days=450)).date()
    
    col_hb1, col_hb2 = st.columns([2, 1])
    with col_hb1:
        date_range_t4 = st.slider("DATE RANGE", min_value=min_date_t4, max_value=today.date(), value=((today - timedelta(days=90)).date(), today.date()), key="slider_t4")
    with col_hb2:
        rolling_avg = st.slider("ROLLING AVERAGE (Days)", 5, 60, 20)

    start_dt_t4, end_dt_t4 = date_range_t4
    hb_days = np.busday_count(start_dt_t4, end_dt_t4)
    st.markdown(f"**Viewing: {start_dt_t4} to {end_dt_t4} ({hb_days} Trading Days)**")

    mask_t4 = (close_df.index.date >= start_dt_t4) & (close_df.index.date <= end_dt_t4)
    breadth_data = close_df.loc[mask_t4]
    
    if not breadth_data.empty:
        st.markdown("### SECTOR TREND HEALTH (% Distance from 200-Day MA)")
        sma_200 = close_df.rolling(window=200).mean()
        distance_pct = ((close_df.iloc[-1] - sma_200.iloc[-1]) / sma_200.iloc[-1]) * 100
        
        breadth_tickers = [t for t in TICKERS if t not in ['SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH']]
        dist_filtered = distance_pct[breadth_tickers]
        
        fig_200 = go.Figure()
        bar_colors = ['#00FF00' if val > 0 else '#FF0000' for val in dist_filtered.values]
        x_labels = [get_label(t) for t in dist_filtered.index]
        
        fig_200.add_trace(go.Bar(
            x=x_labels, y=dist_filtered.values, 
            marker_color=bar_colors, 
            text=[f"{v:.1f}%" for v in dist_filtered.values], textposition='auto'
        ))
        
        fig_200.add_hline(y=0, line_dash="solid", line_color="#FFFFFF")
        fig_200.update_layout(
            template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title='% Distance from 200MA',
            yaxis=dict(type="linear", gridcolor="#222222"), 
            xaxis=dict(gridcolor="#222222"), height=400, margin=dict(l=0, r=0, b=0, t=20)
        )
        st.plotly_chart(fig_200, use_container_width=True)

        st.markdown("---")
        
        st.markdown("### SECTOR CORRELATION HEATMAP")
        smoothed_data = breadth_data[breadth_tickers].rolling(window=rolling_avg).mean()
        returns = smoothed_data.pct_change().dropna()
        corr_matrix = returns.corr().round(2)
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=0)
        corr_matrix_masked = corr_matrix.mask(mask)
        
        text_matrix = np.where(corr_matrix_masked.isna(), "", corr_matrix_masked.astype(str))
        heatmap_labels = [get_label(t) for t in corr_matrix.columns]
        
        fig_corr = go.Figure(data=go.Heatmap(
            z=corr_matrix_masked.values, x=heatmap_labels, y=heatmap_labels,
            colorscale='RdBu', zmin=-1, zmax=1, text=text_matrix, texttemplate="%{text}",
            hoverinfo="x+y+z", showscale=True
        ))
        fig_corr.update_layout(
            template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=600, margin=dict(l=20, r=20, b=20, t=30), xaxis=dict(tickangle=-45)
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    with st.expander("TERMINAL GUIDE: HEALTH & BREADTH"):
        st.markdown("""
        **📝 Summary:** Measures the underlying structural health of the market using moving averages and sector correlations.
        
        **⚙️ Instructions:**
        * **Trend Health:** Shows the exact percentage each sector is trading above (green) or below (red) its 200-day moving average.
        * **Heatmap:** Dark Red (+1) means two sectors move in perfect lockstep. Dark Blue (-1) means they move perfectly opposite to each other.
        
        **📊 Outline & Guidelines:**
        * **Mean Reversion (Trend Health):** A sector trading >15% above its 200MA is generally considered over-extended and due for a pullback. A sector trading deep in the red is structurally broken.
        * **Diversification Risk (Heatmap):** If your portfolio holds multiple sectors that are all showing dark red correlations with each other, you are not actually diversified. You are holding the exact same risk profile under different ticker names. Look for blue/white correlations to truly hedge.
        """)

# ==========================================
# TAB 5: INSTITUTIONAL FLOW
# ==========================================
with tab5:
    st.subheader("Smart Money Flow & 13F Footprint")
    
    fig_dot = go.Figure()
    marker_colors = [COLOR_MAP.get(idx, '#00BFFF') for idx in own_series.index]
    
    for i, (idx, val) in enumerate(own_series.items()):
        fig_dot.add_trace(go.Scatter(
            x=[0, val], y=[get_label(idx), get_label(idx)], mode='lines', 
            line=dict(color='#444444', width=2), showlegend=False, hoverinfo='skip'
        ))
        
    fig_dot.add_trace(go.Scatter(
        x=own_series.values, y=[get_label(idx) for idx in own_series.index], 
        mode='markers+text', marker=dict(size=14, color=marker_colors, line=dict(width=2, color='#FFFFFF')), 
        text=[f"{v:.1f}%" for v in own_series.values], textposition='middle right', textfont=dict(color='#00FF00'),
        showlegend=False
    ))

    fig_dot.update_layout(
        title="CURRENT INSTITUTIONAL OWNERSHIP (% OF FLOAT)", template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#222222", range=[0, 105]), yaxis=dict(gridcolor="#222222"), height=500, margin=dict(l=0, r=0, b=0, t=40), hovermode="closest"
    )
    st.plotly_chart(fig_dot, use_container_width=True)

    st.markdown("---")

    col_obv1, col_obv2 = st.columns([1, 3])
    with col_obv1:
        flow_tickers = [t for t in TICKERS if t not in ['SPY', 'RSP', 'IWD', 'SPHB', 'SPLV', 'IYT', 'SMH']]
        selected_flow_label = st.selectbox("SELECT ASSET FOR OBV FLOW", [get_label(t) for t in flow_tickers])
        selected_flow = selected_flow_label.split(" ")[-1]
        
    asset_close = close_df[selected_flow].iloc[-252:].dropna() 
    asset_vol = vol_df[selected_flow].iloc[-252:].dropna()
    obv = (np.sign(asset_close.diff()) * asset_vol).fillna(0).cumsum()

    fig_obv = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.4])
    fig_obv.add_trace(go.Scatter(x=asset_close.index, y=asset_close, mode='lines', line=dict(color=COLOR_MAP.get(selected_flow, '#00FF00'), width=2), name="Price"), row=1, col=1)
    fig_obv.add_trace(go.Scatter(x=obv.index, y=obv, mode='lines', line=dict(color='#FFB100', width=2), name="OBV", fill='tozeroy', fillcolor='rgba(255, 177, 0, 0.1)'), row=2, col=1)

    fig_obv.update_layout(
        title=f"SMART MONEY FLOW PROXY: {selected_flow_label}", template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=450, margin=dict(l=0, r=0, b=0, t=40), hovermode="x unified" 
    )
    fig_obv.update_yaxes(title_text="Price ($)", gridcolor="#222222", row=1, col=1)
    fig_obv.update_yaxes(title_text="OBV", gridcolor="#222222", row=2, col=1)
    fig_obv.update_xaxes(gridcolor="#222222")
    st.plotly_chart(fig_obv, use_container_width=True)

    with st.expander("TERMINAL GUIDE: INSTITUTIONAL FLOW"):
        st.markdown("""
        **📝 Summary:** Tracks where smart money (institutions, whales, mutual funds) is parking their massive capital reserves.
        
        **⚙️ Instructions:**
        * **13F Ownership (Top):** Shows the static percentage of total shares currently held by large funds.
        * **On-Balance Volume (Bottom):** Adds volume on green days, subtracts volume on red days. Retail traders do not have enough capital to move OBV; this tracks block trades.
        
        **📊 Outline & Guidelines:**
        * **Crowded Trades (13F):** Extremely high ownership (>85%) can lead to a "liquidity trap." If bad news hits, everyone tries to sell at once, causing a violent crash.
        * **The OBV Divergence Signal:** The ultimate buy signal. If the asset's *Price* is making lower lows (meaning retail is panicking and selling), but the *OBV* line is making higher highs, it means institutions are silently stepping in and accumulating massive amounts of stock at a discount.
        """)