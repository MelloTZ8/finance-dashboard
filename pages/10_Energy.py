import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.graph_objects as go
import sys
import os
import datetime

# --- THEME INJECTION ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from theme import inject_custom_css

st.set_page_config(page_title="E-Terminal | Energy Dashboard", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

# Initialize FRED using your specified secrets key
api_key = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=api_key)

# --- DATA FETCHING (10 YEARS) ---
@st.cache_data(ttl=3600)
def get_master_data():
    tickers = {
        "WTI": "CL=F", "BRENT": "BZ=F", "RBOB": "RB=F", "DXY": "DX-Y.NYB",
        "XLE": "XLE", "XOP": "XOP", "OIH": "OIH", "URA": "URA", "TAN": "TAN", "ICLN": "ICLN", "UNG": "UNG",
        "TLT": "TLT", "XLP": "XLP", "XLU": "XLU", "RSP": "RSP",
        "SPY": "SPY", "DIA": "DIA", "EEM": "EEM", "XLY": "XLY", "IWM": "IWM", "QQQ": "QQQ"
    }
    data = yf.download(list(tickers.values()), period="10y")['Close']
    
    data['Crack_Spread'] = (data[tickers["RBOB"]] * 42) - data[tickers["WTI"]]
    data['WTI_Brent_Spread'] = data[tickers["WTI"]] - data[tickers["BRENT"]]
    data['DXY_WTI_Spread'] = data[tickers["DXY"]] - data[tickers["WTI"]]
    return data, tickers

@st.cache_data(ttl=86400)
def get_distillate_data():
    # Strictly utilizing the natively free FRED series for US Hubs
    series = {
        "Gulf Coast Conventional Gasoline": "DGASUSGULF",
        "New York Harbor Conventional Gasoline": "DGASNYH"
    }
    df_list = []
    for name, s_id in series.items():
        try: df_list.append(fred.get_series(s_id).to_frame(name))
        except Exception: df_list.append(pd.DataFrame(columns=[name]))
    
    return pd.concat(df_list, axis=1).ffill() if df_list else pd.DataFrame()

@st.cache_data(ttl=86400)
def get_fred_inventory():
    series = {"Crude_Prod": "WCRFPUS2", "NatGas_Storage": "NWGICUS2", "Crude_Inventories": "WCESTUS1", "SPR": "WCSSTUS1"}
    df_list = []
    for name, s_id in series.items():
        try: df_list.append(fred.get_series(s_id).to_frame(name))
        except Exception: df_list.append(pd.DataFrame(columns=[name]))
    return pd.concat(df_list, axis=1).ffill() if df_list else pd.DataFrame()

prices, t = get_master_data()
distillates = get_distillate_data()
macro_data = get_fred_inventory()

# Global Min/Max Dates
min_date = prices.index.min().date()
max_date = prices.index.max().date()
one_year_ago = max_date - datetime.timedelta(days=365)
six_months_ago = max_date - datetime.timedelta(days=180)

x_base = dict(showgrid=False, color="#FFB100")

# --- HEADER & TABS ---
st.markdown('<h3 class="bb-switchboard-section">ENERGY TERMINAL ⚡</h3>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["MARKET PULSE", "INTERMARKET", "DOWNSTREAM", "UPSTREAM", "INVENTORIES"])

# ==========================================
# TAB 1: MARKET PULSE 
# ==========================================
with tab1:
    # 1. WTI VS BRENT SPOT + SPREAD
    st.markdown('<div class="menu-card"><h4>🌍 WTI VS. BRENT SPOT & SPREAD</h4></div>', unsafe_allow_html=True)
    d1 = st.slider("d1", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s1")
    df1 = prices.loc[pd.to_datetime(d1[0]):pd.to_datetime(d1[1])]

    wti_max = df1[t["WTI"]].max()
    spread_min = df1['WTI_Brent_Spread'].min()
    lhs_delta = max(abs(wti_max - 90), 20) * 1.15 
    rhs_delta = max(abs(spread_min - 0), 5) * 1.15
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df1.index, y=df1[t["BRENT"]], name="🌍 BRENT Spot", line=dict(color='#00008B', width=2)))
    fig1.add_trace(go.Scatter(x=df1.index, y=df1[t["WTI"]], name="🛢️ WTI Spot", line=dict(color='#00BFFF', width=2)))
    fig1.add_trace(go.Scatter(
        x=df1.index, y=df1['WTI_Brent_Spread'], name="Spread (WTI - Brent)", yaxis="y2",
        fill='tozeroy', fillcolor='rgba(255, 69, 0, 0.10)', line=dict(color='rgba(255, 69, 0, 0.8)', width=1) # 10% Transparency
    ))
    fig1.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Spot Price ($)", range=[90 - lhs_delta, 90 + lhs_delta], showgrid=True, gridcolor="#333333", color="#00FF00"),
        yaxis2=dict(title="Spread ($/bbl)", range=[0 - rhs_delta, 0 + rhs_delta], overlaying="y", side="right", color="#FF4500", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 2. RBOB CRACK SPREAD
    st.markdown('<div class="menu-card"><h4>⛽ RBOB CRACK SPREAD (3:2:1 PROXY)</h4></div>', unsafe_allow_html=True)
    colA, colB = st.columns([3, 1])
    with colA: d2 = st.slider("d2", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s2")
    with colB: sma_window = st.slider("SMA", 20, 100, 50, step=5, label_visibility="collapsed", key="crack_sma")
    
    df2 = prices.copy()
    df2['Crack_SMA'] = df2['Crack_Spread'].rolling(window=sma_window).mean()
    df2 = df2.loc[pd.to_datetime(d2[0]):pd.to_datetime(d2[1])]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df2.index, y=df2['Crack_Spread'], name="Margin ($/bbl)", line=dict(color='#00FF00', width=2)))
    fig2.add_trace(go.Scatter(x=df2.index, y=df2['Crack_SMA'], name=f"{sma_window}D SMA", line=dict(color='#FFFFFF', width=1, dash='dot')))
    fig2.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Margin ($/bbl)", showgrid=True, gridcolor="#333333", color="#00FF00", autorange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3. DXY VS WTI CRUDE 
    st.markdown('<div class="menu-card"><h4>💵 DXY VS. 🛢️ WTI CRUDE</h4></div>', unsafe_allow_html=True)
    d3 = st.slider("d3", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s3")
    df3 = prices.loc[pd.to_datetime(d3[0]):pd.to_datetime(d3[1])]
    
    dxy_max = df3[t["DXY"]].max()
    d_spread_max = df3['DXY_WTI_Spread'].max()
    lhs_d_delta = max(abs(dxy_max - 60), 40) * 1.15
    rhs_d_delta = max(abs(d_spread_max - 0), 20) * 1.15

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df3.index, y=df3[t["DXY"]], name="DXY (LHS)", line=dict(color='#FF00FF', width=2)))
    fig3.add_trace(go.Scatter(x=df3.index, y=df3[t["WTI"]], name="WTI (LHS)", line=dict(color='#00FFFF', width=2)))
    fig3.add_trace(go.Scatter(
        x=df3.index, y=df3['DXY_WTI_Spread'], name="Spread (DXY - WTI)", yaxis="y2",
        fill='tozeroy', fillcolor='rgba(128, 128, 128, 0.3)', line=dict(color='rgba(128, 128, 128, 0.8)', width=1)
    ))
    fig3.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base,
        yaxis=dict(title="Price/Index", range=[60 - lhs_d_delta, 60 + lhs_d_delta], showgrid=True, gridcolor="#333333", color="#FF00FF"),
        yaxis2=dict(title="Spread", range=[0 - rhs_d_delta, 0 + rhs_d_delta], overlaying="y", side="right", color="#AAAAAA", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig3, use_container_width=True)

    # 4. XLE VS WTI CRUDE
    st.markdown('<div class="menu-card"><h4>🛢️ XLE VS. WTI CRUDE (LOG SCALE)</h4></div>', unsafe_allow_html=True)
    d4 = st.slider("d4", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s4")
    df4 = prices.loc[pd.to_datetime(d4[0]):pd.to_datetime(d4[1])]
    
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df4.index, y=df4[t["XLE"]], name="XLE (LHS)", line=dict(color='#FFB100', width=2)))
    fig4.add_trace(go.Scatter(x=df4.index, y=df4[t["WTI"]], name="WTI (RHS)", yaxis="y2", line=dict(color='#00FFFF', width=2)))
    fig4.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="XLE Price ($)", type="log", autorange=True, showgrid=True, gridcolor="#333333", color="#FFB100"),
        yaxis2=dict(title="WTI Price ($)", type="log", autorange=True, overlaying="y", side="right", color="#00FFFF", showgrid=False),
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", bgcolor="rgba(0,0,0,0.5)"), font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig4, use_container_width=True)

    # 5. US REGIONAL SPOT PRICES (CONVENTIONAL GASOLINE)
    st.markdown('<div class="menu-card"><h4>🛢️ US REGIONAL SPOT PRICES (CONVENTIONAL GASOLINE)</h4></div>', unsafe_allow_html=True)
    dist_min = distillates.index.min().date() if not distillates.empty else min_date
    d5 = st.slider("d5", dist_min, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s5")
    df5 = distillates.loc[pd.to_datetime(d5[0]):pd.to_datetime(d5[1])]
    
    fig5 = go.Figure()
    colors = ['#00FFFF', '#FF00FF']
    for i, col in enumerate(df5.columns):
        fig5.add_trace(go.Scatter(x=df5.index, y=df5[col], name=col, line=dict(color=colors[i%len(colors)], width=2)))
        
    fig5.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Dollars per Gallon ($/gal)", showgrid=True, gridcolor="#333333", color="#00FF00", autorange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig5, use_container_width=True)

    # --- MARKET PULSE EXPLAINERS ---
    st.markdown('<h4 class="bb-section-head">🎓 MARKET PULSE: CHART EXPLAINERS</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="menu-card">
        <h4>1. WTI VS. BRENT SPOT & SPREAD</h4>
        <p><b>Definition:</b> The price difference between US inland crude (WTI) and seaborne global crude (Brent).</p>
        <p><b>Source:</b> NYMEX / ICE via Yahoo Finance.</p>
        <p><b>How to Read:</b> A positive spread means WTI is trading at a premium; negative means a discount. 0 on the spread aligns with $90 on the price axis.</p>
        <p><b>Amrita Sen:</b> "When the WTI vs. Brent spread flips positive, you are seeing extreme tension of domestic U.S. shale disruptions versus global bottlenecks."</p>
    </div>
    <div class="menu-card">
        <h4>2. RBOB CRACK SPREAD</h4>
        <p><b>Definition:</b> Represents the gross refining margin—the difference between the price of the finished product (gasoline) and the input (crude).</p>
        <p><b>Calculation Note:</b> Since gasoline is quoted in dollars per gallon and crude in dollars per barrel, it requires a conversion factor (42 gallons per barrel).</p>
        $$ \\text{RBOB Crack} = (Price_{RBOB} \\times 42) - Price_{WTI} $$
        <p><b>Gianna Bern:</b> "The RBOB crack spread is the lifeblood of refiners—if that margin blows out, refiners will aggressively bid up WTI to capture the profit."</p>
    </div>
    <div class="menu-card">
        <h4>3. DXY VS. WTI CRUDE</h4>
        <p><b>Definition:</b> Tracking the US Dollar Index against Spot Crude.</p>
        <p><b>How to Read:</b> 60 on the LHS Index aligns with 0 on the RHS Spread. Watch for the spread blowing out as an indicator of global inflation pressure.</p>
        <p><b>Amrita Sen:</b> "The DXY acts as gravity for the entire commodity complex. Because crude is priced globally in dollars, a surging DXY creates an artificial ceiling on WTI."</p>
    </div>
    <div class="menu-card">
        <h4>4. XLE VS. WTI CRUDE</h4>
        <p><b>Definition:</b> The performance of the Energy Select Sector SPDR Fund (XLE) against Spot WTI on a Logarithmic Scale.</p>
        <p><b>Tips:</b> Log scales help identify percentage-based momentum decoupling. If XLE breaks out while WTI is flat, equities are front-running a structural supply deficit.</p>
    </div>
    <div class="menu-card">
        <h4>5. US REGIONAL SPOT PRICES (CONVENTIONAL GASOLINE)</h4>
        <p><b>Definition:</b> Spot prices for conventional gasoline at key US coastal hubs.</p>
        <p><b>Source:</b> EIA via St. Louis FRED.</p>
        <p><b>Gianna Bern:</b> "Tracking regional blendstocks exposes local refinery outages and pipeline constraints before they impact the national average."</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 2: INTERMARKET COMPARISON 
# ==========================================
with tab2:
    st.markdown('<div class="menu-card"><h4>INTERMARKET RELATIVE PERFORMANCE (%)</h4></div>', unsafe_allow_html=True)
    d6 = st.slider("d6", min_date, max_date, (six_months_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s6")
    df6 = prices.loc[pd.to_datetime(d6[0]):pd.to_datetime(d6[1])]
    
    norm_df = (df6 / df6.iloc[0]) * 100

    fig_im = go.Figure()
    im_traces = {
        "🛢️ XLE (Energy)": ("XLE", '#FF0000'), "☀️ TAN (Solar)": ("TAN", '#FFFF00'),
        "☢️ URA (Nuclear)": ("URA", '#00FFFF'), "📈 SPY (Market)": ("SPY", '#FFFFFF'),
        "💵 DXY (USD)": ("DXY", '#FF00FF'), "🛡️ TLT (Bonds)": ("TLT", '#00FF00')
    }
    for label, (tick, color) in im_traces.items():
        fig_im.add_trace(go.Scatter(x=norm_df.index, y=norm_df[t[tick]], name=label, line=dict(color=color, width=2)))

    fig_im.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Index Value (Base 100)", showgrid=True, gridcolor="#333333", autorange=True),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig_im, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 INTERMARKET: CHART EXPLAINERS</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="menu-card">
        <h4>RELATIVE PERFORMANCE MATRIX</h4>
        <p><b>Definition:</b> A percentage-normalized baseline comparing Energy, Defensive, and Broad Market sectors.</p>
        <p><b>How to Read:</b> Every asset starts at 100 at the beginning of your selected slider window.</p>
        <p><b>Gianna Bern:</b> "Notice that URA (Nuclear) often leads during periods of high-interest rates as the market bets on stable, long-term power generation."</p>
        <p><b>Amrita Sen:</b> "Solar (TAN) struggles under the weight of DXY strength. Until the dollar cools, capital expenditure for clean energy remains prohibitive."</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 3: DOWNSTREAM
# ==========================================
with tab3:
    st.markdown('<div class="menu-card"><h4>GASOLINE CRACKS (RBOB/WTI RATIO)</h4></div>', unsafe_allow_html=True)
    d7 = st.slider("d7", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s7")
    df7 = prices.loc[pd.to_datetime(d7[0]):pd.to_datetime(d7[1])]
    
    crack_ratio = df7[t["RBOB"]] / df7[t["WTI"]]
    fig_dwn = go.Figure(go.Scatter(x=crack_ratio.index, y=crack_ratio, line=dict(color='#00FF00', width=2)))
    fig_dwn.update_layout(
        height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Ratio", showgrid=True, gridcolor="#333333", color="#00FF00", autorange=True),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig_dwn, use_container_width=True)

    st.info("Refinery Utilization & OPEC+ Compliance endpoints are awaiting deployment.", icon="🏭")

    st.markdown('<h4 class="bb-section-head">🎓 DOWNSTREAM: CHART EXPLAINERS</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="menu-card">
        <h4>DOWNSTREAM CAPACITY & MARGINS</h4>
        <p><b>Gianna Bern:</b> "Downstream risk is centered on compliance. If OPEC barrels remain heavy, refiners in the Gulf will have to pay a premium for blending, cutting into those ⛽ RBOB margins."</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 4: UPSTREAM
# ==========================================
with tab4:
    st.markdown('<div class="menu-card"><h4>🇺🇸 US WEEKLY CRUDE PRODUCTION</h4></div>', unsafe_allow_html=True)
    d8 = st.slider("d8", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s8")
    df8 = macro_data.loc[pd.to_datetime(d8[0]):pd.to_datetime(d8[1])]
    
    fig_up = go.Figure(go.Scatter(x=df8.index, y=df8["Crude_Prod"], name="Production", line=dict(color='#FF0000', width=2)))
    fig_up.update_layout(
        height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="BBL/D (000s)", showgrid=True, gridcolor="#333333", color="#00FF00", autorange=True),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig_up, use_container_width=True)

    st.info("Rig Count & Global Tanker Rate endpoints are awaiting deployment.", icon="🏗️")

    st.markdown('<h4 class="bb-section-head">🎓 UPSTREAM: CHART EXPLAINERS</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="menu-card">
        <h4>UPSTREAM PRODUCTION & LOGISTICS</h4>
        <p><b>Amrita Sen:</b> "US Production is the 'tap' that won't close. Even with a falling rig count, efficiency gains in the Permian mean we are doing more with less."</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 5: STORAGE & INVENTORIES
# ==========================================
with tab5:
    st.markdown('<div class="menu-card"><h4>🛢️ CRUDE STOCKS (EXCL. SPR) & SPR LEVELS</h4></div>', unsafe_allow_html=True)
    d9 = st.slider("d9", min_date, max_date, (one_year_ago, max_date), format="MMM, YYYY", label_visibility="collapsed", key="s9")
    df9 = macro_data.loc[pd.to_datetime(d9[0]):pd.to_datetime(d9[1])]
    
    fig_inv = go.Figure()
    fig_inv.add_trace(go.Scatter(x=df9.index, y=df9["Crude_Inventories"], name="Crude Stocks", line=dict(color='#FFB100', width=2)))
    fig_inv.add_trace(go.Scatter(x=df9.index, y=df9["SPR"], name="SPR", yaxis="y2", line=dict(color='#FF4500', width=2)))
    
    fig_inv.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=x_base, yaxis=dict(title="Crude Stocks (000s BBL)", showgrid=True, gridcolor="#333333", color="#FFB100", autorange=True),
        yaxis2=dict(title="SPR (000s BBL)", overlaying="y", side="right", color="#FF4500", showgrid=False, autorange=True),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig_inv, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 INVENTORY: CHART EXPLAINERS</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="menu-card">
        <h4>THE TRUTH TAB: STORAGE</h4>
        <p><b>Definition:</b> The residual balance. If supply exceeds demand, it shows up here in the tanks.</p>
        <p><b>Source:</b> Energy Information Administration (EIA).</p>
        <p><b>Amrita Sen:</b> "The SPR is the 'Ghost in the Machine.' Any attempt to refill it creates a floor for WTI at $70. If inventories draw down while the SPR is empty, the upside for crude is uncapped."</p>
    </div>
    """, unsafe_allow_html=True)