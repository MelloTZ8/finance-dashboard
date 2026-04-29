import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# --- THEME INJECTION ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from theme import inject_custom_css

st.set_page_config(page_title="E-Terminal | Energy & Pulse", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()  # Executes your required st.markdown HTML/CSS override

# Initialize FRED using your specified secrets key
api_key = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=api_key)

# --- DATA FETCHING (CACHED) ---
@st.cache_data(ttl=3600)
def get_energy_data():
    tickers = {
        "WTI": "CL=F", 
        "BRENT": "BZ=F", 
        "RBOB": "RB=F",
        "XLE": "XLE", 
        "DXY": "DX-Y.NYB",
        "TAN": "TAN",
        "URA": "URA",
        "SPY": "SPY"
    }
    # Download 1 year of data
    data = yf.download(list(tickers.values()), period="1y")['Close']
    
    # Mathematical Spreads
    # RBOB is priced in $/gallon. 42 gallons in a barrel.
    data['Crack_Spread'] = (data[tickers["RBOB"]] * 42) - data[tickers["WTI"]]
    data['Brent_WTI_Spread'] = data[tickers["BRENT"]] - data[tickers["WTI"]]
    
    return data, tickers

@st.cache_data(ttl=86400)
def get_fred_energy():
    series = {
        "Crude_Prod": "WCRFPUS2",         # Weekly US Field Production of Crude Oil
        "NatGas_Storage": "NWGICUS2",     # Weekly Working Gas in Underground Storage
        "Crude_Inventories": "WCESTUS1",  # Weekly US Ending Stocks of Crude Oil (Excl. SPR)
        "SPR": "WCSSTUS1"                 # Weekly US Ending Stocks of Crude Oil in SPR
    }
    
    df_list = []
    for name, s_id in series.items():
        try:
            s = fred.get_series(s_id)
            df = s.to_frame(name)
            df_list.append(df)
        except Exception as e:
            print(f"FRED API Warning: Failed to load {name} (ID: {s_id}). Error: {e}")
            df_list.append(pd.DataFrame(columns=[name]))
            
    if df_list:
        return pd.concat(df_list, axis=1).ffill()
    else:
        return pd.DataFrame()

# --- PREP DATA ---
prices, ticker_map = get_energy_data()
macro_data = get_fred_energy()

# --- HEADER & TABS ---
st.markdown('<h3 class="bb-switchboard-section">ENERGY TERMINAL ⚡</h3>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "MARKET PULSE", "INTERMARKET", "DOWNSTREAM", "UPSTREAM", "INVENTORIES"
])

# ==========================================
# TAB 1: MARKET PULSE (The Executive View)
# ==========================================
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="menu-card"><h4>🌍 WTI VS. BRENT SPREAD</h4><p class="bb-muted">Global vs. Domestic Supply Tightness</p></div>', unsafe_allow_html=True)
        fig_spread = go.Figure()
        fig_spread.add_trace(go.Scatter(x=prices.index, y=prices['Brent_WTI_Spread'], name="Spread (USD)", line=dict(color='#00FFFF', width=2)))
        fig_spread.add_hline(y=0, line_dash="dash", line_color="#333333")
        fig_spread.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="Premium/Discount ($)", showgrid=True, gridcolor="#333333", color="#00FF00"),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_spread, use_container_width=True)

    with col2:
        st.markdown('<div class="menu-card"><h4>⛽ RBOB CRACK SPREAD</h4><p class="bb-muted">Leading Indicator for Refinery Profitability</p></div>', unsafe_allow_html=True)
        fig_crack = go.Figure()
        fig_crack.add_trace(go.Scatter(x=prices.index, y=prices['Crack_Spread'], name="Margin ($/bbl)", line=dict(color='#00FF00', width=2)))
        fig_crack.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="Margin ($/bbl)", showgrid=True, gridcolor="#333333", color="#00FF00"),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_crack, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="menu-card"><h4>💵 DXY VS. 🛢️ WTI CRUDE</h4><p class="bb-muted">The Macro Ceiling for Commodity Pricing</p></div>', unsafe_allow_html=True)
        fig_dxy = go.Figure()
        fig_dxy.add_trace(go.Scatter(x=prices.index, y=prices[ticker_map["DXY"]], name="DXY (LHS)", line=dict(color='#FF00FF', width=2)))
        fig_dxy.add_trace(go.Scatter(x=prices.index, y=prices[ticker_map["WTI"]], name="WTI (RHS)", yaxis="y2", line=dict(color='#FF0000', width=2)))
        fig_dxy.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="DXY Index", showgrid=True, gridcolor="#333333", color="#FF00FF"),
            yaxis2=dict(title="WTI Price ($)", overlaying="y", side="right", color="#FF0000", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_dxy, use_container_width=True)

    with col4:
        st.markdown('<div class="menu-card"><h4>🛢️ XLE VS. WTI CRUDE</h4><p class="bb-muted">Tracking Equity Front-Running (Base 100)</p></div>', unsafe_allow_html=True)
        norm_xle = (prices[ticker_map["XLE"]] / prices[ticker_map["XLE"]].iloc[0]) * 100
        norm_wti = (prices[ticker_map["WTI"]] / prices[ticker_map["WTI"]].iloc[0]) * 100
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=prices.index, y=norm_xle, name="XLE (Equities)", line=dict(color='#FFB100', width=2)))
        fig_eq.add_trace(go.Scatter(x=prices.index, y=norm_wti, name="WTI (Spot)", line=dict(color='#FF0000', width=2)))
        fig_eq.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="Normalized Index", showgrid=True, gridcolor="#333333", color="#00FF00"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_eq, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 MARKET PULSE INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    > **Amrita Sen (Macro & Geopolitics):** "The pulse of the physical market lies in the spreads. When the WTI vs. Brent spread widens, you are seeing the tension between booming domestic U.S. shale production and global supply bottlenecks. Simultaneously, the DXY acts as gravity for the entire commodity complex. Because crude is priced globally in dollars, a surging DXY creates an artificial ceiling on WTI. If you see WTI rallying *despite* a strong dollar, that is a massive signal of underlying physical market tightness."
    > 
    > **Gianna Bern (Risk & Financials):** "Watch the financial derivatives and the equities to see where the smart money is moving before it hits the spot price. The RBOB crack spread is the lifeblood of refiners—if that margin blows out, refiners will aggressively bid up WTI to capture the profit, eventually dragging crude higher. On the equity side, XLE versus spot WTI tells you what the market expects next. If XLE starts breaking out while WTI is flat, the equities are front-running a structural supply deficit."
    """)

# ==========================================
# TAB 2: INTERMARKET COMPARISON
# ==========================================
with tab2:
    st.markdown('<h4 class="bb-section-head">RELATIVE PERFORMANCE (%)</h4>', unsafe_allow_html=True)
    norm_df = (prices / prices.iloc[0]) * 100

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["XLE"]], name="🛢️ XLE", line=dict(color='#FF0000', width=2)))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["TAN"]], name="☀️ TAN", line=dict(color='#FFFF00', width=2)))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["URA"]], name="☢️ URA", line=dict(color='#00FFFF', width=2)))
    fig2.add_trace(go.Scatter(x=norm_df.index, y=norm_df[ticker_map["SPY"]], name="📈 SPY", line=dict(color='#FFFFFF', dash='dash', width=2)))

    fig2.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(title="Trade Date", showgrid=False, color="#FFB100"),
        yaxis=dict(title="Index Value (Base 100)", showgrid=True, gridcolor="#333333", color="#00FF00"),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 INTERMARKET INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    > **Gianna Bern:** "This chart highlights the beta between ☢️ Nuclear and 🛢️ Fossil fuels. Notice that URA often leads during periods of high-interest rates as the market bets on stable, long-term power generation."
    > 
    > **Amrita Sen:** "☀️ Solar (TAN) is struggling under the weight of DXY strength. Until the dollar cools, the capital expenditure for global clean energy projects remains prohibitive compared to traditional crude."
    """)

# ==========================================
# TAB 3: DOWNSTREAM
# ==========================================
with tab3:
    st.markdown('<div class="menu-card"><h4>GASOLINE CRACKS (RBOB/WTI RATIO)</h4><p class="bb-muted">Source: NYMEX</p></div>', unsafe_allow_html=True)
    crack_ratio = prices[ticker_map["RBOB"]] / prices[ticker_map["WTI"]]
    fig3 = go.Figure(go.Scatter(x=crack_ratio.index, y=crack_ratio, line=dict(color='#00FF00', width=2)))
    fig3.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
        yaxis=dict(title="Ratio", showgrid=True, gridcolor="#333333", color="#00FF00"),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 DOWNSTREAM INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    > **Amrita Sen:** "Refining utilization is peaking. We are seeing a mismatch between heavy crude availability and the lighter sweet crude US refineries are optimized for."
    > 
    > **Gianna Bern:** "Downstream risk is centered on compliance. If OPEC barrels remain heavy, refiners in the Gulf will have to pay a premium for blending, cutting into those ⛽ RBOB margins."
    """)

# ==========================================
# TAB 4: UPSTREAM
# ==========================================
with tab4:
    st.markdown('<div class="menu-card"><h4>🇺🇸 US WEEKLY CRUDE PRODUCTION</h4><p class="bb-muted">Source: EIA / FRED</p></div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=macro_data.index, y=macro_data["Crude_Prod"], name="Production", line=dict(color='#FF0000', width=2)))
    fig4.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
        yaxis=dict(title="BBL/D (000s)", showgrid=True, gridcolor="#333333", color="#00FF00"),
        font=dict(family="Courier New, monospace", size=12)
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 UPSTREAM INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    > **Amrita Sen:** "US Production is the 'tap' that won't close. Even with a falling rig count, efficiency gains in the Permian mean we are doing more with less."
    > 
    > **Gianna Bern:** "The lag between rig counts and actual production is roughly 6 months. Watch the ⛏️ XOP producers; they are signaling that capital discipline is more important than raw volume right now."
    """)

# ==========================================
# TAB 5: STORAGE & INVENTORIES
# ==========================================
with tab5:
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown('<div class="menu-card"><h4>🛢️ CRUDE STOCKS (EXCL. SPR)</h4><p class="bb-muted">Source: EIA</p></div>', unsafe_allow_html=True)
        fig_inv = go.Figure(go.Scatter(x=macro_data.index, y=macro_data["Crude_Inventories"], line=dict(color='#FFB100', width=2)))
        fig_inv.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="Thousands of Barrels", showgrid=True, gridcolor="#333333", color="#00FF00"),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_inv, use_container_width=True)
        
    with colB:
        st.markdown('<div class="menu-card"><h4>🏛️ SPR LEVELS</h4><p class="bb-muted">Strategic Petroleum Reserve</p></div>', unsafe_allow_html=True)
        fig_spr = go.Figure(go.Scatter(x=macro_data.index, y=macro_data["SPR"], line=dict(color='#FF4500', width=2)))
        fig_spr.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, color="#FFB100"),
            yaxis=dict(title="Thousands of Barrels", showgrid=True, gridcolor="#333333", color="#00FF00"),
            font=dict(family="Courier New, monospace", size=12)
        )
        st.plotly_chart(fig_spr, use_container_width=True)

    st.markdown('<h4 class="bb-section-head">🎓 INVENTORY INSIGHTS</h4>', unsafe_allow_html=True)
    st.markdown("""
    > **Amrita Sen:** "The SPR is the 'Ghost in the Machine.' Any attempt to refill it creates a floor for WTI at $70. If inventories draw down while the SPR is empty, the upside for crude is uncapped."
    > 
    > **Gianna Bern:** "Natural gas storage (🔥 UNG) is the ultimate volatility play. Unlike crude, you cannot easily move gas across oceans without liquefaction. Storage builds are localized and brutal to prices in the shoulder seasons."
    """)