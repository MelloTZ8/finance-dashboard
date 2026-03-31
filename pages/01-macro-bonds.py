import streamlit as st
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime

# We need to go up one folder level to grab the theme file since this script is inside /pages
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from theme import inject_custom_css

# --- 1. PAGE CONFIG & BLOOMBERG THEME ---
st.set_page_config(page_title="TERMINAL: BOND WATCH", layout="wide")

# Inject the master CSS
inject_custom_css()

st.title("Macro Bond Watch")
# ... (the rest of your bond script stays exactly the same)

st.title("Macro Bond Watch")
st.markdown("Tracking the Treasury curve and spread dynamics to front-run regime shifts.")

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    # 1. Grab your secret key from the "vault"
    api_key = st.secrets["FRED_API_KEY"]
    
    end = datetime.date.today()
    start = datetime.date(1994, 1, 1) 
    
    tickers = ['DGS3MO', 'DGS2', 'DGS5', 'DGS10', 'DGS30']
    df = web.DataReader(tickers, 'fred', start, end)
    df.columns = ['3-Month', '2-Year', '5-Year', '10-Year', '30-Year']
    
    df.dropna(inplace=True)
    
    df['10Y_3M_Spread'] = df['10-Year'] - df['3-Month']
    df['10Y_2Y_Spread'] = df['10-Year'] - df['2-Year']
    df['30Y_5Y_Spread'] = df['30-Year'] - df['5-Year']
    
    return df

df = load_data()

# --- 3. INTERACTIVE CONTROLS ---
min_date = df.index.min().to_pydatetime()
max_date = df.index.max().to_pydatetime()

start_date, end_date = st.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MMM YYYY"
)

MACD_OPTIONS = ['10Y_2Y_Spread', '10Y_3M_Spread', '30Y_5Y_Spread']
MACD_DISPLAY_LABELS = {
    '10Y_2Y_Spread': '2s10s (10Y - 2Y)',
    '10Y_3M_Spread': '3m10s (10Y - 3M)',
    '30Y_5Y_Spread': '5s30s (30Y - 5Y)',
}

# Use state so the chart can render before the dropdown is displayed later in the UI.
DEFAULT_MACD_TARGET = '10Y_2Y_Spread'
macd_target = st.session_state.get("macd_target", DEFAULT_MACD_TARGET)

macd_label = MACD_DISPLAY_LABELS[macd_target]

df_filtered = df[(df.index >= start_date) & (df.index <= end_date)].copy()

# --- 4. MACD CALCULATION ---
df_filtered['MACD_Line'] = df_filtered[macd_target].ewm(span=12, adjust=False).mean() - df_filtered[macd_target].ewm(span=26, adjust=False).mean()
df_filtered['Signal_Line'] = df_filtered['MACD_Line'].ewm(span=9, adjust=False).mean()
df_filtered['MACD_Hist'] = df_filtered['MACD_Line'] - df_filtered['Signal_Line']
df_filtered['Hist_Color'] = ['#00FF00' if val > 0 else '#FF0000' for val in df_filtered['MACD_Hist']]

# --- 5. CHART BUILDING ---
yield_cols = ['3-Month', '2-Year', '5-Year', '10-Year', '30-Year']
colors = ['#FF0000', '#FF4500', '#FFD700', '#00BFFF', '#0000FF']

# --- A. Build COMBINED View ---
fig_combined = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
    subplot_titles=('1. Absolute Treasury Yields', '2. Spread Regimes: 2s10s, 3m10s & 5s30s', f'MACD: {macd_label}'),
    row_heights=[0.5, 0.3, 0.2]
)

for col, color in zip(yield_cols, colors):
    fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered[col], mode='lines', name=col, line=dict(color=color, width=2), legend="legend"), row=1, col=1)

fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['10Y_3M_Spread'], mode='lines', name='10Y - 3M Spread', line=dict(color='#00FF00', width=2), legend="legend2"), row=2, col=1)
fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['10Y_2Y_Spread'], mode='lines', name='10Y - 2Y Spread (2s10s)', line=dict(color='#FFFF00', width=2), legend="legend2"), row=2, col=1)
fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['30Y_5Y_Spread'], mode='lines', name='30Y - 5Y Spread (5s30s)', line=dict(color='#8A2BE2', width=2), legend="legend2"), row=2, col=1)
fig_combined.add_hline(y=0, line_dash="dash", line_color="white", line_width=1.5, row=2, col=1)

fig_combined.add_trace(go.Bar(x=df_filtered.index, y=df_filtered['MACD_Hist'], marker_color=df_filtered['Hist_Color'], name='MACD Histogram', showlegend=False), row=3, col=1)
fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['MACD_Line'], mode='lines', name='MACD Line', line=dict(color='#00BFFF', width=1.5), showlegend=False), row=3, col=1)
fig_combined.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['Signal_Line'], mode='lines', name='Signal Line', line=dict(color='#FFA500', width=1.5), showlegend=False), row=3, col=1)
fig_combined.add_hline(y=0, line_color="white", line_width=1, row=3, col=1)

fig_combined.update_layout(
    template='plotly_dark', hovermode='closest', height=900, margin=dict(b=40, t=60),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
    # Move the Spread Regimes legend higher to avoid overlapping chart lines/y-axis.
    legend2=dict(orientation="h", yanchor="bottom", y=0.60, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)")
)

# --- B. Individual Chart Styling ---
def apply_terminal_style(fig):
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Courier New, monospace", color="#00FF00")
    )
    return fig

# 1. Yields Only
fig_yields = go.Figure()
for col, color in zip(yield_cols, colors):
    fig_yields.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered[col], mode='lines', name=col, line=dict(color=color, width=2)))
fig_yields.update_layout(title='Absolute Treasury Yields', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"))
fig_yields = apply_terminal_style(fig_yields)

# 2. Spreads Only
fig_spreads = go.Figure()
fig_spreads.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['10Y_3M_Spread'], mode='lines', name='10Y - 3M Spread', line=dict(color='#00FF00', width=2)))
fig_spreads.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['10Y_2Y_Spread'], mode='lines', name='10Y - 2Y Spread (2s10s)', line=dict(color='#FFFF00', width=2)))
fig_spreads.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['30Y_5Y_Spread'], mode='lines', name='30Y - 5Y Spread (5s30s)', line=dict(color='#8A2BE2', width=2)))
fig_spreads.add_hline(y=0, line_dash="dash", line_color="white", line_width=1.5)
fig_spreads.update_layout(
    title='Spread Regimes: 2s10s, 3m10s & 5s30s',
    # Push legend up further so it clears the plot area.
    legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)")
)
fig_spreads = apply_terminal_style(fig_spreads)

# 3. MACD Only
fig_macd = go.Figure()
fig_macd.add_trace(go.Bar(x=df_filtered.index, y=df_filtered['MACD_Hist'], marker_color=df_filtered['Hist_Color'], name='MACD Histogram'))
fig_macd.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['MACD_Line'], mode='lines', name='MACD Line', line=dict(color='#00BFFF', width=2)))
fig_macd.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['Signal_Line'], mode='lines', name='Signal Line', line=dict(color='#FFA500', width=2)))
fig_macd.add_hline(y=0, line_color="white", line_width=1)
fig_macd.update_layout(title=f'MACD: {macd_label}', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"))
fig_macd = apply_terminal_style(fig_macd)

# --- 6. UI RENDER ---
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

# --- 7. REGIME DETECTOR ---
st.markdown("---")
st.subheader("Live Market Regime")

latest_data = df_filtered.iloc[-1]
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
colC.metric(f"MACD Momentum ({macd_target[:6]})", momentum_state)

# --- 8. EDUCATIONAL SUMMARY ---
st.markdown("---")
st.subheader("The Gundlach Playbook: Reading the Regimes")
st.markdown("""
* **1. The Warning (Inversion):** When the spreads in Chart 2 drop below the zero line, the bond market is pricing in structural economic sickness.
* **2. The Event (Bull Steepener):** The danger zone is the "De-Inversion." When spreads violently cross back *above* zero, the Fed is usually panicking.
* **3. The Vigilante Premium (5s30s):** Driven by the free market. If this explodes, bond vigilantes fear runaway inflation or reckless deficit spending.
* **4. Using the MACD:** Measures spread momentum. A blue line crossing up through orange signals a steepening curve.
""")