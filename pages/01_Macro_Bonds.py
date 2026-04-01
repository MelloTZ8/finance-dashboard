import streamlit as st
from fredapi import Fred
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import sys
import os
from utils import terminal_style

terminal_style()

# --- 1. PAGE CONFIG & SETUP ---
st.set_page_config(page_title="TERMINAL: BOND WATCH", layout="wide")

# Inject custom CSS from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from theme import inject_custom_css

# --- 2. GLOBAL CONSTANTS ---
MACD_OPTIONS = ['10Y_2Y_Spread', '10Y_3M_Spread', '30Y_5Y_Spread']
MACD_DISPLAY_LABELS = {
    '10Y_2Y_Spread': '2s10s (10Y - 2Y)',
    '10Y_3M_Spread': '3m10s (10Y - 3M)',
    '30Y_5Y_Spread': '5s30s (30Y - 5Y)',
}
DEFAULT_MACD_TARGET = '10Y_2Y_Spread'
YIELD_COLS = ['3-Month', '2-Year', '5-Year', '10-Year', '30-Year']
YIELD_COLORS = ['#FF0000', '#FF4500', '#FFD700', '#00BFFF', '#0000FF']


# --- 3. DATA LAYER ---
@st.cache_data
def load_data():
    """Fetches Treasury data from FRED and calculates key spreads."""
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
    start = "1994-01-01" 
    
    # Fetch series
    s_3m = fred.get_series('DGS3MO', observation_start=start)
    s_2y = fred.get_series('DGS2', observation_start=start)
    s_5y = fred.get_series('DGS5', observation_start=start)
    s_10y = fred.get_series('DGS10', observation_start=start)
    s_30y = fred.get_series('DGS30', observation_start=start)
    
    # Bind into DataFrame
    df = pd.DataFrame({
        '3-Month': s_3m,
        '2-Year': s_2y,
        '5-Year': s_5y,
        '10-Year': s_10y,
        '30-Year': s_30y
    })
    
    df.dropna(inplace=True)
    
    # Calculate Spreads
    df['10Y_3M_Spread'] = df['10-Year'] - df['3-Month']
    df['10Y_2Y_Spread'] = df['10-Year'] - df['2-Year']
    df['30Y_5Y_Spread'] = df['30-Year'] - df['5-Year']
    
    return df

def apply_macd_calculations(df, target_spread):
    """Calculates MACD momentum indicators for the selected spread."""
    df_calc = df.copy()
    df_calc['MACD_Line'] = df_calc[target_spread].ewm(span=12, adjust=False).mean() - df_calc[target_spread].ewm(span=26, adjust=False).mean()
    df_calc['Signal_Line'] = df_calc['MACD_Line'].ewm(span=9, adjust=False).mean()
    df_calc['MACD_Hist'] = df_calc['MACD_Line'] - df_calc['Signal_Line']
    df_calc['Hist_Color'] = ['#00FF00' if val > 0 else '#FF0000' for val in df_calc['MACD_Hist']]
    return df_calc


# --- 4. VISUALIZATION LAYER ---
def apply_terminal_style(fig):
    """Applies the master terminal aesthetic to individual Plotly figures."""
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier New, monospace", color="#00FF00")
    )
    return fig

def build_combined_chart(df, macd_label):
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=('1. Absolute Treasury Yields', '2. Spread Regimes: 2s10s, 3m10s & 5s30s', f'MACD: {macd_label}'),
        row_heights=[0.5, 0.3, 0.2]
    )

    # 1. Absolute Yields
    for col, color in zip(YIELD_COLS, YIELD_COLORS):
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col, line=dict(color=color, width=2), legend="legend"), row=1, col=1)

    # 2. Spread Regimes
    fig.add_trace(go.Scatter(x=df.index, y=df['10Y_3M_Spread'], mode='lines', name='10Y - 3M Spread', line=dict(color='#00FF00', width=2), legend="legend2"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['10Y_2Y_Spread'], mode='lines', name='10Y - 2Y Spread (2s10s)', line=dict(color='#FFFF00', width=2), legend="legend2"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['30Y_5Y_Spread'], mode='lines', name='30Y - 5Y Spread (5s30s)', line=dict(color='#8A2BE2', width=2), legend="legend2"), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="white", line_width=1.5, row=2, col=1)

    # 3. MACD Momentum
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=df['Hist_Color'], name='MACD Histogram', showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], mode='lines', name='MACD Line', line=dict(color='#00BFFF', width=1.5), showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], mode='lines', name='Signal Line', line=dict(color='#FFA500', width=1.5), showlegend=False), row=3, col=1)
    fig.add_hline(y=0, line_color="white", line_width=1, row=3, col=1)

    fig.update_layout(
        template='plotly_dark', hovermode='closest', height=900, margin=dict(b=40, t=60),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        legend2=dict(orientation="h", yanchor="bottom", y=0.60, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)")
    )
    return fig

def build_yields_chart(df):
    fig = go.Figure()
    for col, color in zip(YIELD_COLS, YIELD_COLORS):
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col, line=dict(color=color, width=2)))
    fig.update_layout(title='Absolute Treasury Yields', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"))
    return apply_terminal_style(fig)

def build_spreads_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['10Y_3M_Spread'], mode='lines', name='10Y - 3M Spread', line=dict(color='#00FF00', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['10Y_2Y_Spread'], mode='lines', name='10Y - 2Y Spread (2s10s)', line=dict(color='#FFFF00', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['30Y_5Y_Spread'], mode='lines', name='30Y - 5Y Spread (5s30s)', line=dict(color='#8A2BE2', width=2)))
    fig.add_hline(y=0, line_dash="dash", line_color="white", line_width=1.5)
    fig.update_layout(
        title='Spread Regimes: 2s10s, 3m10s & 5s30s',
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)")
    )
    return apply_terminal_style(fig)

def build_macd_chart(df, macd_label):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=df['Hist_Color'], name='MACD Histogram'))
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], mode='lines', name='MACD Line', line=dict(color='#00BFFF', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], mode='lines', name='Signal Line', line=dict(color='#FFA500', width=2)))
    fig.add_hline(y=0, line_color="white", line_width=1)
    fig.update_layout(title=f'MACD: {macd_label}', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"))
    return apply_terminal_style(fig)


# --- 5. UI COMPONENTS ---
def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚡ TERMINAL INDEX")
        st.markdown("---")
        # --- UPDATED FILE STRUCTURE LINKS ---
        st.page_link("00_E-Terminal.py", label="[00] Home: Switchboard")
        st.page_link("pages/01_Macro_Bonds.py", label="[01] Macro Bond Watch")
        st.page_link("pages/02_Inflation.py", label="[02] Inflation")
        st.page_link("pages/03_Liquidity.py", label="[03] Liquidity")
        st.page_link("pages/04_Global_Markets.py", label="[04] Global Markets")
        st.page_link("pages/05_Market_Heatmap.py", label="[05] Market Heatmap")
        st.page_link("pages/06_Sectors.py", label="[06] Sectors")
        st.page_link("pages/07_Options_Flow.py", label="[07] Options Flow")
        st.page_link("pages/08_Crypto_Terminal.py", label="[08] Crypto Terminal")
        st.page_link("pages/09_Metals.py", label="[09] Metals")
        st.page_link("pages/10_Energy.py", label="[10] Energy")
        st.page_link("pages/11_Positioning.py", label="[11] Positioning")
        st.page_link("pages/12_Options_Analyzer.py", label="[12] Options Analyzer")
        # ------------------------------------
        st.markdown("---")
        st.markdown("<span style='color:#00FF00; font-size:12px;'>SYS.STAT: ONLINE</span>", unsafe_allow_html=True)

def render_regime_detector(df, target_spread):
    st.markdown("---")
    st.subheader("Live Market Regime")

    latest_data = df.iloc[-1]
    val_2s10s = latest_data['10Y_2Y_Spread']
    val_3m10s = latest_data['10Y_3M_Spread']
    macd_hist = latest_data['MACD_Hist']

    if val_2s10s < 0 and val_3m10s < 0:
        if macd_hist > 0:
            regime = "INVERTED BUT STEEPENING (Approaching De-Inversion)"
            regime_color = "#FFA500" 
        else:
            regime = "DEEPLY INVERTED (Recession Warning)"
            regime_color = "#FF0000" 
    elif val_2s10s > 0 and val_3m10s > 0:
        regime = "NORMAL / POSITIVE CURVE"
        regime_color = "#00FF00" 
    elif (val_2s10s > 0 and val_3m10s < 0) or (val_2s10s < 0 and val_3m10s > 0):
        regime = "DE-INVERTING (The 'Event' Zone)"
        regime_color = "#FFFF00" 
    else:
        regime = "TRANSITIONING"
        regime_color = "#FFFFFF"

    st.markdown(f"**Latest Data Date:** {latest_data.name.strftime('%B %d, %Y')}")
    st.markdown(f"**Current Status:** <span style='color:{regime_color}; font-size: 22px; font-weight: bold;'>{regime}</span>", unsafe_allow_html=True)

    colA, colB, colC = st.columns(3)
    colA.metric("2s10s Spread", f"{val_2s10s:.2f}%")
    colB.metric("3m10s Spread", f"{val_3m10s:.2f}%")
    momentum_state = "Bullish (Steepening)" if macd_hist > 0 else "Bearish (Flattening/Inverting)"
    colC.metric(f"MACD Momentum ({target_spread[:6]})", momentum_state)

def render_educational_summary():
    st.markdown("---")
    st.subheader("The Gundlach Playbook: Reading the Regimes")
    st.markdown("""
    * **1. The Warning (Inversion):** When the spreads in Chart 2 drop below the zero line, the bond market is pricing in structural economic sickness.
    * **2. The Event (Bull Steepener):** The danger zone is the "De-Inversion." When spreads violently cross back *above* zero, the Fed is usually panicking.
    * **3. The Vigilante Premium (5s30s):** Driven by the free market. If this explodes, bond vigilantes fear runaway inflation or reckless deficit spending.
    * **4. Using the MACD:** Measures spread momentum. A blue line crossing up through orange signals a steepening curve.
    """)


# --- 6. MAIN EXECUTION ---
def main():
    inject_custom_css()
    render_sidebar()

    st.title("Macro Bond Watch")
    st.markdown("Tracking the Treasury curve and spread dynamics to front-run regime shifts.")

    # Load Base Data
    df = load_data()

    # Date Controls
    min_date = df.index.min().to_pydatetime()
    max_date = df.index.max().to_pydatetime()
    start_date, end_date = st.slider(
        "Select Date Range",
        min_value=min_date, max_value=max_date,
        value=(min_date, max_date), format="MMM YYYY"
    )

    # State & Target Management
    macd_target = st.session_state.get("macd_target", DEFAULT_MACD_TARGET)
    macd_label = MACD_DISPLAY_LABELS[macd_target]

    # Filter & Process Data
    df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]
    df_processed = apply_macd_calculations(df_filtered, macd_target)

    # Build Charts
    fig_combined = build_combined_chart(df_processed, macd_label)
    fig_yields = build_yields_chart(df_processed)
    fig_spreads = build_spreads_chart(df_processed)
    fig_macd = build_macd_chart(df_processed, macd_label)

    # UI Rendering: Tabs
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Combined Dashboard", "📈 1. Yield Spectrum", "📉 2. Spread Regimes", "📉 3. MACD Momentum"])

    with tab1:
        st.plotly_chart(fig_combined, width="stretch")
    with tab2:
        st.plotly_chart(fig_yields, width="stretch")
    with tab3:
        st.plotly_chart(fig_spreads, width="stretch")
    with tab4:
        st.plotly_chart(fig_macd, width="stretch")
        st.selectbox(
            "Select Spread for MACD Analysis",
            options=MACD_OPTIONS,
            format_func=lambda x: MACD_DISPLAY_LABELS[x],
            key="macd_target",
        )

    # Render Bottom Modules
    render_regime_detector(df_processed, macd_target)
    render_educational_summary()

if __name__ == "__main__":
    main()