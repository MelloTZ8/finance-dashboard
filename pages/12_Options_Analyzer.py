import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objects as go
from datetime import datetime

# Must be the first Streamlit command
st.set_page_config(layout="wide", page_title="Options Strain Terminal")

# --- BLOOMBERG TERMINAL CSS INJECTION ---
bloomberg_css = """
<style>
    /* Backgrounds & Typography */
    .stApp { background-color: #000000 !important; }
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Courier New', Courier, monospace !important;
        color: #00FF00 !important;
        font-size: 14px !important;
    }
    
    /* Headers & Accents */
    h1, h2, h3, h4, h5, h6, .st-emotion-cache-10trblm {
        color: #FFB100 !important;
        text-transform: uppercase !important;
        border-bottom: 2px solid #333333 !important;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }
    
    /* Input Fields */
    div[data-baseweb="input"] > div {
        background-color: #0a0a0a !important;
        border: 1px solid #333333 !important;
    }
    input { color: #00FF00 !important; font-weight: bold; }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(bloomberg_css, unsafe_allow_html=True)
# ----------------------------------------

st.title("📊 Volatility Skew & Strain Terminal")

# --- IN-PAGE CONTROLS (Top Menu) ---
# Using columns to place the controls horizontally above the chart
col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    ticker_input = st.text_input("TICKER", value="AAPL").upper()
with col2:
    metric_choice = st.radio("Z-AXIS METRIC:", ["impliedVolatility", "lastPrice"], horizontal=True)
with col3:
    plot_style = st.radio("PLOT STYLE:", ["Divergence Surface (Mesh)", "Raw Data (Dots)"], horizontal=True)

metric_label = "Implied Volatility" if metric_choice == "impliedVolatility" else "Last Sale Price"

# --- MAIN LOGIC ---
if ticker_input:
    try:
        data = yf.Ticker(ticker_input)
        expirations = data.options
        current_price = data.history(period="1d")['Close'].iloc[-1]
        
        if not expirations:
            st.error("NO DATA FOUND.")
        else:
            all_exp_dt = [datetime.strptime(e, '%Y-%m-%d') for e in expirations]
            selected_expirations = list(expirations[:6])
            
            found_months = set()
            for dt in all_exp_dt[6:]:
                month_key = dt.strftime('%Y-%m')
                if month_key not in found_months and len(found_months) < 10:
                    selected_expirations.append(dt.strftime('%Y-%m-%d'))
                    found_months.add(month_key)

            all_data = []
            today = datetime.now()
            
            for exp in selected_expirations:
                opt = data.option_chain(exp)
                calls, puts = opt.calls.copy(), opt.puts.copy()
                calls['type'], puts['type'] = 'Call', 'Put'
                
                exp_date = datetime.strptime(exp, '%Y-%m-%d')
                dte = max((exp_date - today).days, 1) # Prevent 0 DTE math errors
                
                calls['DTE'], puts['DTE'] = dte, dte
                all_data.extend([calls, puts])

            df = pd.concat(all_data)
            
            # Clean Outliers
            if metric_choice == "impliedVolatility":
                df = df[(df[metric_choice] > 0.01) & (df[metric_choice] < 3.0)] 
            
            # Filter Moneyness
            min_strike, max_strike = current_price * 0.7, current_price * 1.3
            df = df[(df['strike'] >= min_strike) & (df['strike'] <= max_strike)]

            # --- 3D PLOT BUILDING ---
            fig = go.Figure()

            if plot_style == "Divergence Surface (Mesh)":
                # --- DIVERGENCE MATH ---
                df_calls = df[df['type'] == 'Call']
                df_puts = df[df['type'] == 'Put']

                # Create ONE unified grid for both
                xi = np.linspace(df['DTE'].min(), df['DTE'].max(), 50)
                yi = np.linspace(df['strike'].min(), df['strike'].max(), 50)
                xi, yi = np.meshgrid(xi, yi)

                # Interpolate both to the exact same coordinates
                zi_call = griddata((df_calls['DTE'], df_calls['strike']), df_calls[metric_choice], (xi, yi), method='linear')
                zi_put = griddata((df_puts['DTE'], df_puts['strike']), df_puts[metric_choice], (xi, yi), method='linear')

                # Calculate the Strain (Put Premium)
                zi_diff = zi_put - zi_call

                # The Call Surface (Ghost Wireframe)
                fig.add_trace(go.Surface(
                    x=xi, y=yi, z=zi_call,
                    name="Call Baseline",
                    colorscale=[[0, '#00FFFF'], [1, '#00FFFF']], # Solid Cyan
                    opacity=0.2, 
                    showscale=False,
                ))

                # The Put Surface (Divergence Colored)
                fig.add_trace(go.Surface(
                    x=xi, y=yi, z=zi_put,
                    surfacecolor=zi_diff, # Color based on strain
                    name="Put Strain",
                    colorscale='RdBu_r', 
                    cmin=-0.2 if metric_choice == "impliedVolatility" else -5.0, 
                    cmax=0.2 if metric_choice == "impliedVolatility" else 5.0, 
                    opacity=0.9,
                    colorbar=dict(title="Strain Spread", x=0.85)
                ))

            else:
                # --- RAW DATA DOTS ---
                for opt_type, color in [('Call', '#00FFFF'), ('Put', '#FF00FF')]:
                    sub_df = df[df['type'] == opt_type]
                    fig.add_trace(go.Scatter3d(
                        x=sub_df['DTE'],
                        y=sub_df['strike'],
                        z=sub_df[metric_choice],
                        mode='markers',
                        name=f"{opt_type}s",
                        marker=dict(size=4, color=color, opacity=0.8)
                    ))

            # --- FORMATTING ---
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Courier New, monospace", color="#00FF00"),
                title=f"{ticker_input} Options Surface | Spot Price: ${current_price:.2f}",
                scene=dict(
                    xaxis_title='Days to Expiration (DTE)',
                    yaxis_title='Strike Price',
                    zaxis_title=metric_label,
                    aspectratio=dict(x=1.2, y=1, z=0.6),
                    xaxis=dict(autorange="reversed", gridcolor="#333333", zerolinecolor="#333333"),
                    yaxis=dict(gridcolor="#333333", zerolinecolor="#333333"),
                    zaxis=dict(gridcolor="#333333", zerolinecolor="#333333")
                ),
                margin=dict(l=0, r=0, b=0, t=50),
                legend=dict(yanchor="top", y=0.9, xanchor="left", x=0.1, bgcolor="rgba(10,10,10,0.8)", bordercolor="#333333", borderwidth=1)
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"TERMINAL ERROR: {e}")

# --- TERMINAL GUIDE ---
st.markdown("---")
st.subheader("TERMINAL GUIDE: HOW TO READ THIS CHART")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    ### 1. Divergence Surface (Mesh Mode)
    This visualization measures **"Strain"** by comparing the pricing of Puts versus Calls on the exact same mathematical grid. The transparent cyan mesh is the Call baseline. The opaque surface is the Put data, colored by how much more expensive it is than the Calls.
    
    * **🔴 Deep Red (High Strain):** Put IV is drastically higher than Call IV. The market is aggressively hedging against a crash down to that specific strike/date. *Institutional fear is high.*
    * **⚪ White/Grey (Neutral):** Put-Call Parity is holding steady. Options are priced symmetrically.
    * **🔵 Blue (Upside Bias):** Call IV is higher than Put IV. This indicates a heavy demand for upside speculation, often seen right before earnings or major catalyst events.
    """)

with col_b:
    st.markdown("""
    ### 2. The Axes
    * **Z-Axis (Vertical):** Represents your selected metric (Implied Volatility or Last Price). The higher the surface, the more expensive the option premium.
    * **Y-Axis (Strike Price):** This shows the "Moneyness." The script automatically filters the view to show strikes roughly +/- 30% from the current spot price.
    * **X-Axis (Days to Expiration):** Time remaining on the contract. Notice how the surface usually slopes upward as DTE gets closer to zero (front-month options are highly sensitive to sudden moves).

    ### 3. Raw Data (Dots Mode)
    Use this toggle to verify the actual data points fetched from the market before the SciPy engine interpolates the mesh. (Cyan = Calls, Magenta = Puts).
    """)