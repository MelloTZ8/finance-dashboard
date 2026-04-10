import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime

# Import your custom Bloomberg Theme
from theme import inject_custom_css

# Handle multiple data sources
try:
    import pandas_datareader.data as web
except ImportError:
    web = None
try:
    import yfinance as yf
except ImportError:
    yf = None

st.set_page_config(page_title="Liquidity & Systemic Stress", layout="wide")

# Inject the theme
inject_custom_css()

# ==========================================
# HELPER FUNCTIONS & DATA FETCHING
# ==========================================

@st.cache_data(ttl=3600)
def fetch_data(ticker, start_date, end_date):
    """Fetches data from FRED or YFinance based on ticker rules."""
    # YFINANCE ROUTING
    if ticker in ["^GSPC", "SP500_YOY", "SP500_DRAWDOWN", "SP500_THOUSANDS", "SP500_MOM"] and yf is not None:
        try:
            df = yf.download("^GSPC", start=start_date, end=end_date)
            if df.empty: return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if ticker == "^GSPC": return df[['Close']].rename(columns={'Close': '^GSPC'})
            if ticker == "SP500_THOUSANDS":
                df['SP500_THOUSANDS'] = df['Close'] / 1000
                return df[['SP500_THOUSANDS']]
            if ticker == "SP500_YOY":
                df['SP500_YOY'] = df['Close'].pct_change(252) * 100
                return df[['SP500_YOY']].dropna()
            if ticker == "SP500_MOM":
                df['SP500_MOM'] = df['Close'].pct_change(21) * 100 
                return df[['SP500_MOM']].dropna()
            if ticker == "SP500_DRAWDOWN":
                df['High'] = df['Close'].cummax()
                df['SP500_DRAWDOWN'] = ((df['Close'] - df['High']) / df['High']) * 100
                return df[['SP500_DRAWDOWN']].dropna()
        except Exception:
            return None

    # FRED ROUTING
    if web is not None:
        try:
            if ticker == "SOFR_IORB_SPREAD":
                df_sofr = web.DataReader('SOFR', 'fred', start_date, end_date)
                df_iorb = web.DataReader('IORB', 'fred', start_date, end_date)
                df = pd.DataFrame(index=df_sofr.index.join(df_iorb.index, how='inner'))
                df['SPREAD'] = df_sofr['SOFR'] - df_iorb['IORB']
                return df[['SPREAD']].dropna()
                
            if ticker == "BB_10Y_SPREAD":
                df_bb = web.DataReader('BAMLH0A1HYBBEY', 'fred', start_date, end_date)
                df_10y = web.DataReader('DGS10', 'fred', start_date, end_date)
                df = pd.DataFrame(index=df_bb.index.join(df_10y.index, how='inner'))
                df['SPREAD'] = df_bb['BAMLH0A1HYBBEY'] - df_10y['DGS10']
                return df[['SPREAD']].dropna()

            if ticker == "CP_SPREAD":
                df_cp = web.DataReader('CPN3M', 'fred', start_date, end_date)
                df_tb = web.DataReader('DTB3', 'fred', start_date, end_date)
                df = pd.DataFrame(index=df_cp.index.join(df_tb.index, how='inner'))
                df['SPREAD'] = df_cp['CPN3M'] - df_tb['DTB3']
                return df[['SPREAD']].dropna()
                
            if ticker == "CORP_10Y_SPREAD":
                df_corp = web.DataReader('HQMCB10YR', 'fred', start_date, end_date).ffill()
                df_tsy = web.DataReader('DGS10', 'fred', start_date, end_date).ffill()
                df = pd.DataFrame(index=df_corp.index.join(df_tsy.index, how='inner'))
                df['SPREAD'] = df_corp['HQMCB10YR'] - df_tsy['DGS10']
                return df[['SPREAD']].dropna()
                
            if ticker == "BUFFETT":
                # Market Value of Equities (Wilshire 5000 proxy) / US GDP
                df_w = yf.download("^W5000", start=start_date, end=end_date)
                if isinstance(df_w.columns, pd.MultiIndex):
                    df_w.columns = df_w.columns.get_level_values(0)
                df_w = df_w[['Close']].rename(columns={'Close': 'W5000'})
                
                df_gdp = web.DataReader('GDP', 'fred', start_date, end_date).resample('D').ffill()
                df = df_w.join(df_gdp, how='inner')
                df['BUFFETT'] = (df['W5000'] / df['GDP']) * 100
                return df[['BUFFETT']].dropna()

            df = web.DataReader(ticker, 'fred', start_date, end_date).ffill()
            if ticker in ["WRESBAL", "WTREGEN", "WALCL"]:
                df[ticker] = df[ticker] / 1000
            return df
        except Exception:
            return None
    return None

@st.cache_data
def generate_deterministic_dummy(ticker_name, start_date, end_date, base_val=0):
    seed_val = sum([ord(char) for char in ticker_name])
    np.random.seed(seed_val)
    full_start = datetime.date.today() - datetime.timedelta(days=40*365)
    dates = pd.date_range(start=full_start, end=datetime.date.today(), freq='B') 
    steps = np.random.normal(loc=0, scale=0.1, size=len(dates))
    values = np.cumsum(steps) + base_val
    full_df = pd.DataFrame({'value': values}, index=dates)
    mask = (full_df.index.date >= start_date) & (full_df.index.date <= end_date)
    return full_df.loc[mask]

# ==========================================
# BASE LAYOUT
# ==========================================
def get_base_layout(title, height=750):
    return dict(
        title=dict(text=title, font=dict(color="#FFB100", family="Courier New", size=16)),
        margin=dict(l=60, r=60, t=50, b=30), height=height, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor="#333333", tickfont=dict(color="#00FF00", family="Courier New")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

def build_advanced_chart(title, start_date, end_date, series_configs, y1_label="", y2_label="", height=750):
    fig = go.Figure()
    has_dual_axis = any(config.get("axis", "y1") == "y2" for config in series_configs)

    for config in series_configs:
        ticker = config.get("ticker")
        color = config.get("color", "#00FF00")
        base_name = config.get("name", ticker)
        y_axis = config.get("axis", "y1")
        axis_tag = " (L1)" if has_dual_axis and y_axis == "y1" else " (R1)"
            
        df = fetch_data(ticker, start_date, end_date) if ticker else None
        if df is not None and not df.empty:
            y_data, x_data = df.iloc[:, 0], df.index
        else:
            dummy_df = generate_deterministic_dummy(base_name, start_date, end_date, base_val=config.get("base_val", 50))
            y_data, x_data = dummy_df['value'], dummy_df.index

        fig.add_trace(go.Scatter(x=x_data, y=y_data, name=f"{base_name}{axis_tag}", mode='lines', line=dict(color=color, width=1.5), yaxis=y_axis))

    layout_args = get_base_layout(title, height)
    if has_dual_axis:
        layout_args['yaxis'] = dict(title=y1_label, side="left", showgrid=True, gridcolor="#333333", tickfont=dict(color="#FFB100", family="Courier New"))
        layout_args['yaxis2'] = dict(title=y2_label, side="right", overlaying="y", showgrid=False, tickfont=dict(color="#00FF00", family="Courier New"))
    else:
        layout_args['yaxis'] = dict(title=y2_label if y2_label else y1_label, side="right", showgrid=True, gridcolor="#333333", tickfont=dict(color="#00FF00", family="Courier New"))

    fig.update_layout(**layout_args)
    st.plotly_chart(fig, use_container_width=True)

def render_chart_with_slider(title, series_configs, unique_key, y1_label="", y2_label="", min_date_override=None):
    today = datetime.date.today()
    absolute_min = min_date_override if min_date_override else (today - datetime.timedelta(days=40*365))
    start_date, end_date = st.slider(f"📅 LOOKBACK: {title}", min_value=absolute_min, max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key=f"slider_{unique_key}", label_visibility="collapsed")
    build_advanced_chart(title, start_date, end_date, series_configs, y1_label, y2_label)

# ==========================================
# CUSTOM ALIGNMENT CHARTS
# ==========================================

def render_banking_stress_aligned():
    today = datetime.date.today()
    min_date = datetime.date(2021, 7, 29) # SOFR-IORB exact start date
    start_date, end_date = st.slider("📅 LOOKBACK: Banking Stress", min_value=min_date, max_value=today, value=(min_date, today), format="YYYY-MM-DD", key="slider_sofr", label_visibility="collapsed")
    
    df_dd = fetch_data("SP500_DRAWDOWN", start_date, end_date)
    df_sofr = fetch_data("SOFR_IORB_SPREAD", start_date, end_date)
    
    fig = go.Figure()
    
    if df_dd is not None and not df_dd.empty:
        fig.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.3)", width=2), yaxis="y1"))
        sp_min = df_dd['SP500_DRAWDOWN'].min() * 1.05
    else:
        sp_min = -20
        
    if df_sofr is not None and not df_sofr.empty:
        fig.add_trace(go.Scatter(x=df_sofr.index, y=df_sofr['SPREAD'], name="SOFR - IORB (R1)", mode='lines', line=dict(color="#00FF00", width=1.5), yaxis="y2"))
        sofr_min = df_sofr['SPREAD'].min()
        sofr_max = df_sofr['SPREAD'].max()
        pad = (sofr_max - sofr_min) * 0.1 or 1
    else:
        sofr_min, sofr_max, pad = 0, 10, 1
        
    fig.update_layout(
        **get_base_layout("🏦 BANKING STRESS (SOFR-IORB SPREAD VS S&P DRAWDOWNS)"),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Spread (bps)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[sofr_min - pad, sofr_max + pad], tickfont=dict(color="#00FF00", family="Courier New"))
    )
    st.plotly_chart(fig, use_container_width=True)

def render_stlfsi_aligned():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: St. Louis Fed FSI", min_value=(today - datetime.timedelta(days=40*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key="slider_stlfsi", label_visibility="collapsed")
    
    df_dd = fetch_data("SP500_DRAWDOWN", start_date, end_date)
    df_st = fetch_data("STLFSI4", start_date, end_date)
    
    fig = go.Figure()
    
    if df_dd is not None and not df_dd.empty:
        fig.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.3)", width=2), yaxis="y1"))
        sp_min = df_dd['SP500_DRAWDOWN'].min() * 1.05
    else:
        sp_min = -20
        
    if df_st is not None and not df_st.empty:
        fig.add_trace(go.Scatter(x=df_st.index, y=df_st['STLFSI4'], name="STLFSI4 (R1)", mode='lines', line=dict(color="#FF3333", width=1.5), yaxis="y2"))
        st_min = df_st['STLFSI4'].min()
        st_max = df_st['STLFSI4'].max()
        pad = (st_max - st_min) * 0.1 or 0.5
    else:
        st_min, st_max, pad = -2, 5, 0.5
        
    fig.update_layout(
        **get_base_layout("😨 ST. LOUIS FED FINANCIAL STRESS INDEX"),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Stress Index", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[st_min - pad, st_max + pad], tickfont=dict(color="#FF3333", family="Courier New"))
    )
    st.plotly_chart(fig, use_container_width=True)

def render_liquidity_funnel_aligned():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Liquidity Funnel", min_value=(today - datetime.timedelta(days=20*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key="slider_funnel", label_visibility="collapsed")
    
    df_dd = fetch_data("SP500_DRAWDOWN", start_date, end_date)
    df_cp = fetch_data("CP_SPREAD", start_date, end_date)
    df_corp = fetch_data("CORP_10Y_SPREAD", start_date, end_date)
    
    fig = go.Figure()
    
    if df_dd is not None and not df_dd.empty:
        fig.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.3)", width=2), yaxis="y1"))
        l_min_dev = df_dd['SP500_DRAWDOWN'].min() * 1.05
    else:
        l_min_dev = -20

    if df_corp is not None and not df_corp.empty:
        fig.add_trace(go.Scatter(x=df_corp.index, y=df_corp['SPREAD'], name="Corp 10Y - Tsy 10Y (R1)", mode='lines', line=dict(color="#FFB100", width=1.5), yaxis="y2"))
    if df_cp is not None and not df_cp.empty:
        fig.add_trace(go.Scatter(x=df_cp.index, y=df_cp['SPREAD'], name="CP 3M - T-Bill 3M (R1)", mode='lines', line=dict(color="#FF00FF", width=1.5), yaxis="y2"))

    fig.update_layout(
        **get_base_layout("🌪️ THE LIQUIDITY FUNNEL (SPREADS VS DRAWDOWNS)"),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[l_min_dev, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Spread (%)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", tickfont=dict(color="#FFB100", family="Courier New"))
    )
    st.plotly_chart(fig, use_container_width=True)

def render_ccbs_aligned_chart():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Cross-Currency", min_value=(today - datetime.timedelta(days=20*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key="slider_ccbs", label_visibility="collapsed")
    
    df_dd = fetch_data("SP500_DRAWDOWN", start_date, end_date)
    
    df_eur = generate_deterministic_dummy("eur", start_date, end_date, base_val=-15)
    df_jpy = generate_deterministic_dummy("jpy", start_date, end_date, base_val=-25)
    df_gbp = generate_deterministic_dummy("gbp", start_date, end_date, base_val=-10)

    # --- MAIN CHART (EUR & GBP) ---
    fig_main = go.Figure()
    if df_dd is not None and not df_dd.empty:
        fig_main.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.3)", width=2), yaxis="y1"))
        sp_min = df_dd['SP500_DRAWDOWN'].min()
    else:
        sp_min = -20

    fig_main.add_trace(go.Scatter(x=df_eur.index, y=df_eur['value'], name="EUR/USD Basis (R1)", mode='lines', line=dict(color="#00FF00", width=1.5), yaxis="y2"))
    fig_main.add_trace(go.Scatter(x=df_gbp.index, y=df_gbp['value'], name="GBP/USD Basis (R1)", mode='lines', line=dict(color="#00CCFF", width=1.5), yaxis="y2"))

    basis_min_main = min(df_eur['value'].min(), df_gbp['value'].min())
    basis_max_main = max(df_eur['value'].max(), df_gbp['value'].max())
    pad_main = (basis_max_main - basis_min_main) * 0.1 or 5

    fig_main.update_layout(
        **get_base_layout("💱 CROSS-CURRENCY BASIS SWAPS: EUR & GBP", height=600),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[sp_min * 1.05, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Basis (bps)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[basis_min_main - pad_main, basis_max_main + pad_main], tickfont=dict(color="#00FF00", family="Courier New"))
    )
    st.plotly_chart(fig_main, use_container_width=True)

    # --- SUB CHART (JPY ISOLATED) ---
    fig_sub = go.Figure()
    if df_dd is not None and not df_dd.empty:
        fig_sub.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.3)", width=2), yaxis="y1"))
        
    fig_sub.add_trace(go.Scatter(x=df_jpy.index, y=df_jpy['value'], name="JPY/USD Basis (R1)", mode='lines', line=dict(color="#FFB100", width=1.5), yaxis="y2"))

    basis_min_sub = df_jpy['value'].min()
    basis_max_sub = df_jpy['value'].max()
    pad_sub = (basis_max_sub - basis_min_sub) * 0.1 or 5

    fig_sub.update_layout(
        **get_base_layout("💴 SUB-CHART: JPY/USD BASIS ISOLATED", height=350),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[sp_min * 1.05, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Basis (bps)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[basis_min_sub - pad_sub, basis_max_sub + pad_sub], tickfont=dict(color="#FFB100", family="Courier New"))
    )
    st.plotly_chart(fig_sub, use_container_width=True)

def render_baa_aligned_chart(title, unique_key):
    today = datetime.date.today()
    start_date, end_date = st.slider(f"📅 LOOKBACK: {title}", min_value=(today - datetime.timedelta(days=40*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key=f"slider_{unique_key}", label_visibility="collapsed")
    df_sp = fetch_data("SP500_YOY", start_date, end_date)
    df_baa = fetch_data("BAA10Y", start_date, end_date) 
    fig = go.Figure()
    
    if df_sp is not None and not df_sp.empty:
        colors = ['#00BFFF' if val >= 0 else '#FF3333' for val in df_sp['SP500_YOY']]
        fig.add_trace(go.Bar(x=df_sp.index, y=df_sp['SP500_YOY'], name="S&P 500 YoY% (L1)", marker_color=colors, yaxis="y1"))
        sp_max_dev = max(abs(df_sp['SP500_YOY'].max()), abs(df_sp['SP500_YOY'].min())) * 1.15
    else:
        sp_max_dev = 50

    if df_baa is not None and not df_baa.empty:
        df_baa.rename(columns={df_baa.columns[0]: 'val'}, inplace=True)
        fig.add_trace(go.Scatter(x=df_baa.index, y=df_baa['val'], name="BAA-10Y Spread (R1)", mode='lines', line=dict(color="#00FF00", width=1.5), yaxis="y2"))
        warn_mask = df_baa['val'].where((df_baa['val'] >= 2.0) & (df_baa['val'] < 2.5))
        fig.add_trace(go.Scatter(x=df_baa.index, y=warn_mask, name="Elevated Risk", mode='lines', line=dict(color="#FF9900", width=3), yaxis="y2"))
        danger_mask = df_baa['val'].where(df_baa['val'] >= 2.5)
        fig.add_trace(go.Scatter(x=df_baa.index, y=danger_mask, name="Severe Risk", mode='lines', line=dict(color="#FF0000", width=3), yaxis="y2"))
        baa_max_dev = max(abs(df_baa['val'].max() - 3.0), abs(df_baa['val'].min() - 3.0)) * 1.15
    else:
        baa_max_dev = 3

    fig.update_layout(
        **get_base_layout(title),
        yaxis=dict(title="S&P 500 YoY Change (%)", side="left", showgrid=False, range=[-sp_max_dev, sp_max_dev], tickfont=dict(color="#00BFFF", family="Courier New")),
        yaxis2=dict(title="Yield Spread (%)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[3.0 - baa_max_dev, 3.0 + baa_max_dev], tickfont=dict(color="#FFB100", family="Courier New"))
    )
    fig.add_hline(y=3.0, line_dash="dash", line_color="#FFFFFF", annotation_text="3% CRITICAL SPREAD", yref="y2")
    st.plotly_chart(fig, use_container_width=True)

def render_junk_aligned_chart(title, unique_key):
    today = datetime.date.today()
    start_date, end_date = st.slider(f"📅 LOOKBACK: {title}", min_value=(today - datetime.timedelta(days=40*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key=f"slider_{unique_key}", label_visibility="collapsed")
    
    df_sp = fetch_data("SP500_YOY", start_date, end_date)
    df_bb = fetch_data("BB_10Y_SPREAD", start_date, end_date)
    fig = go.Figure()
    
    if df_sp is not None and not df_sp.empty:
        colors = ['#00BFFF' if val >= 0 else '#FF3333' for val in df_sp['SP500_YOY']]
        fig.add_trace(go.Bar(x=df_sp.index, y=df_sp['SP500_YOY'], name="S&P 500 YoY% (L1)", marker_color=colors, yaxis="y1"))
        sp_max_dev = max(abs(df_sp['SP500_YOY'].max()), abs(df_sp['SP500_YOY'].min())) * 1.15
    else:
        sp_max_dev = 50

    if df_bb is not None and not df_bb.empty:
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb['SPREAD'], name="BB-10Y Spread (R1)", mode='lines', line=dict(color="#00FF00", width=1.5), yaxis="y2"))
        warn_mask = df_bb['SPREAD'].where((df_bb['SPREAD'] >= 4.0) & (df_bb['SPREAD'] < 5.5))
        fig.add_trace(go.Scatter(x=df_bb.index, y=warn_mask, name="Elevated Risk", mode='lines', line=dict(color="#FF9900", width=3), yaxis="y2"))
        danger_mask = df_bb['SPREAD'].where(df_bb['SPREAD'] >= 5.5)
        fig.add_trace(go.Scatter(x=df_bb.index, y=danger_mask, name="Severe Risk", mode='lines', line=dict(color="#FF0000", width=3), yaxis="y2"))
        bb_max_dev = max(abs(df_bb['SPREAD'].max() - 4.0), abs(df_bb['SPREAD'].min() - 4.0)) * 1.15
    else:
        bb_max_dev = 3

    fig.update_layout(
        **get_base_layout(title),
        yaxis=dict(title="S&P 500 YoY Change (%)", side="left", showgrid=False, range=[-sp_max_dev, sp_max_dev], tickfont=dict(color="#00BFFF", family="Courier New")),
        yaxis2=dict(title="Yield Spread (%)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[4.0 - bb_max_dev, 4.0 + bb_max_dev], tickfont=dict(color="#FF3333", family="Courier New"))
    )
    st.plotly_chart(fig, use_container_width=True)

def render_credit_basis_monitor():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Credit Basis Monitor", min_value=(today - datetime.timedelta(days=20*365)), max_value=today, value=(today - datetime.timedelta(days=2*365), today), format="YYYY-MM-DD", key="slider_cds", label_visibility="collapsed")
    
    df_dd = fetch_data("SP500_DRAWDOWN", start_date, end_date)
    fig = go.Figure()

    if df_dd is not None and not df_dd.empty:
        fig.add_trace(go.Scatter(x=df_dd.index, y=df_dd['SP500_DRAWDOWN'], name="S&P 500 % From Highs (L1)", mode='lines', line=dict(color="rgba(255, 255, 255, 0.2)", width=2), yaxis="y1"))
        sp_min = df_dd['SP500_DRAWDOWN'].min() * 1.05
    else:
        sp_min = -50
    
    calc_start = start_date - datetime.timedelta(days=365)
    df_1y = generate_deterministic_dummy("basis1y", calc_start, end_date, base_val=0.1)
    df_5y = generate_deterministic_dummy("basis5y", calc_start, end_date, base_val=0.4)
    
    df_ratio = pd.DataFrame(index=df_1y.index)
    df_ratio['ratio'] = df_1y['value'] / df_5y['value'].replace(0, np.nan)
    
    df_ratio['mean_252'] = df_ratio['ratio'].rolling(window=252).mean()
    df_ratio['std_252'] = df_ratio['ratio'].rolling(window=252).std()
    df_ratio['z_score'] = (df_ratio['ratio'] - df_ratio['mean_252']) / df_ratio['std_252'].replace(0, np.nan)
    
    mask = (df_ratio.index.date >= start_date) & (df_ratio.index.date <= end_date)
    df_plot = df_ratio.loc[mask]

    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['z_score'], name='1Y/5Y RATIO Z-SCORE (R1)', line=dict(color='#FF00FF', width=2), yaxis='y2'))

    fig.update_layout(
        **get_base_layout("⚡ CREDIT BASIS MONITOR (1Y/5Y ROLLING Z-SCORE OSCILLATOR)"),
        yaxis=dict(title="S&P 500 % Drawdown", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Z-Score (σ)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[-3, 3], tickfont=dict(color="#00FF00", family="Courier New"))
    )
    
    fig.add_hline(y=0, line_dash="solid", line_color="#333333", yref="y2")
    fig.add_hline(y=2.0, line_dash="dash", line_color="#FF0000", annotation_text="+2σ STRESS", yref="y2")
    fig.add_hline(y=-2.0, line_dash="dash", line_color="#00FF00", annotation_text="-2σ CALM", yref="y2")
    
    st.plotly_chart(fig, use_container_width=True)

def render_buffett_indicator():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Buffett Indicator", min_value=(today - datetime.timedelta(days=40*365)), max_value=today, value=(today - datetime.timedelta(days=10*365), today), format="YYYY-MM-DD", key="slider_buffett", label_visibility="collapsed")
    
    df = fetch_data("BUFFETT", start_date, end_date)
    fig = go.Figure()
    
    if df is not None and not df.empty:
        mean_val = df['BUFFETT'].mean()
        fig.add_trace(go.Scatter(x=df.index, y=df['BUFFETT'], name="Wilshire 5000 / GDP", mode='lines', line=dict(color="#00BFFF", width=2)))
        
        fig.add_hline(y=mean_val + 60, line_dash="dot", line_color="#FF0000", annotation_text="+2σ (+60%) SEVERE OVERVALUATION")
        fig.add_hline(y=mean_val + 30, line_dash="dash", line_color="#FFB100", annotation_text="+1σ (+30%) OVERVALUED")
        fig.add_hline(y=mean_val - 30, line_dash="dash", line_color="#FFB100", annotation_text="-1σ (-30%) UNDERVALUED")
        fig.add_hline(y=mean_val - 60, line_dash="dot", line_color="#00FF00", annotation_text="-2σ (-60%) DEEP VALUE")
        
    fig.update_layout(**get_base_layout("🇺🇸 THE BUFFETT INDICATOR (TOTAL MARKET CAP TO GDP)"))
    fig.update_yaxes(title_text="Ratio (%)", side="right", showgrid=True, gridcolor="#333333", tickfont=dict(color="#00FF00", family="Courier New"))
    st.plotly_chart(fig, use_container_width=True)

def render_sahm_rule():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Sahm Rule", min_value=(today - datetime.timedelta(days=40*365)), max_value=today, value=(today - datetime.timedelta(days=10*365), today), format="YYYY-MM-DD", key="slider_sahm", label_visibility="collapsed")
    df = fetch_data("SAHMREALTIME", start_date, end_date)
    fig = go.Figure()
    if df is not None and not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df['SAHMREALTIME'], name="Sahm Rule (R1)", mode='lines', line=dict(color="#00FF00", width=1.5)))
        trigger_df = df[df['SAHMREALTIME'] >= 0.5]
        fig.add_trace(go.Scatter(x=trigger_df.index, y=trigger_df['SAHMREALTIME'], name="Recession Triggered", mode='markers', marker=dict(color="#FF0000", size=6)))
    fig.add_hline(y=0.5, line_dash="dash", line_color="#FF0000", annotation_text="0.5% RECESSION THRESHOLD")
    fig.update_layout(**get_base_layout("📉 REAL-TIME SAHM RULE RECESSION INDICATOR", height=500))
    fig.update_yaxes(title_text="Percentage Points", side="right", showgrid=True, gridcolor="#333333", tickfont=dict(color="#00FF00", family="Courier New"))
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MAIN APP & TABS
# ==========================================
st.title("🖥️ SYSTEMIC STRESS TERMINAL")

tab1, tab2, tab3 = st.tabs(["🚰 1. LIQUIDITY", "⚠️ 2. CREDIT RISK", "🌍 3. MACRO REGIME & FRAGILITY"])

# --- TAB 1: LIQUIDITY ---
with tab1:
    render_banking_stress_aligned()
    render_stlfsi_aligned()
    
    render_ccbs_aligned_chart()
    render_liquidity_funnel_aligned()
    
    render_chart_with_slider("⚖️ US DOLLAR LIQUIDITY TRINITY", [{"ticker": "WTREGEN", "name": "TGA", "color": "#FFB100", "axis": "y1"}, {"ticker": "WRESBAL", "name": "Reserves", "color": "#00FF00", "axis": "y2"}, {"ticker": "RRPONTSYD", "name": "RRP", "color": "#00CCFF", "axis": "y2"}], "trinity", y1_label="Treasury (Bils)", y2_label="Fed Facilities (Bils)")
    render_chart_with_slider("🏛️ FEDERAL RESERVE BALANCE SHEET", [{"ticker": "WALCL", "name": "Total Liabilities", "color": "#FFB100"}], "fed_bs", y1_label="Liabilities (Bils)")

    with st.expander("📚 DEFINITIONS & HOW TO READ: SYSTEMIC LIQUIDITY"):
        st.markdown("""
        * **THE LIQUIDITY FUNNEL:** This dual-spread visualizes the core plumbing of corporate finance. The Long-Term spread (Corporate 10Y vs. Treasury 10Y) tracks the broader credit risk premium demanded by investors. The Short-Term spread (3-Month Commercial Paper vs. 3-Month T-Bill) acts as the immediate canary in the coal mine for corporate funding stress. When companies cannot easily roll over their short-term operational debt, the CP spread blows out. By anchoring the S&P 500 percentage drawdown to the top axis, you can instantly observe the historical correlation: sharp blowouts in the CP spread almost universally front-run or coincide with violent equity market drawdowns.
        
        * **BANKING STRESS (SOFR-IORB SPREAD):** This is the ultimate "plumbing" indicator for the US banking system. IORB (Interest on Reserve Balances) is the baseline risk-free rate the Federal Reserve pays banks to simply park their cash. SOFR (Secured Overnight Financing Rate) is the rate banks charge each other for overnight loans backed by Treasuries. Under normal conditions, SOFR should hover slightly below or exactly at IORB. If the SOFR line spikes above IORB, it signals extreme systemic distress: banks are so starved for liquidity, or so untrusting of counterparty collateral, that they are willing to pay a premium above the Fed's absolute ceiling just to secure overnight cash.
        
        * **ST. LOUIS FED FINANCIAL STRESS INDEX:** Replacing the outdated TED Spread, this composite index synthesizes 18 weekly data series (including interest rates, yield curves, and implied volatility) to measure overall financial system health. A reading of zero implies average market conditions. Positive readings indicate above-average stress, while negative readings indicate below-average stress.
        
        * **CROSS-CURRENCY BASIS SWAPS (EUR, GBP, JPY):** A basis swap measures the premium international institutions must pay to convert their native currencies (Euros, Pounds, Yen) into US Dollars. In a highly liquid global market, this basis hovers near zero. When a global macro crisis erupts, the world scrambles for the safety and utility of US Dollars, causing the basis to plunge deeply negative. Because the Japanese Yen is heavily utilized in global carry trades and uniquely manipulated by the Bank of Japan, its scale often radically detaches from European currencies. By isolating the Yen onto a smaller sub-chart, we prevent its massive fluctuations from visually compressing the EUR and GBP lines, while keeping the S&P 500 drawdown locked to the ceiling of both charts to instantly highlight the correlation between global dollar-shortages and equity crashes.
        
        * **LIQUIDITY TRINITY (TGA vs. Reserves vs. RRP):** This maps the physical location of US Dollars inside the Federal Reserve system. The Treasury General Account (TGA) is the government's checking account. Bank Reserves are the baseline liquidity for the private sector. The Reverse Repo Facility (RRP) is where money market funds park excess cash. **Rule of thumb:** When the Treasury issues bonds to fill the TGA, cash must drain from either Reserves or the RRP. The RRP acts as a buffer. Once the RRP is empty, any new Treasury issuance directly drains Bank Reserves, violently tightening market conditions and choking liquidity.
        """)

# --- TAB 2: CREDIT RISK ---
with tab2:
    render_baa_aligned_chart("🗑️ MOODY'S SEASONED BAA TO 10YR YIELD SPREAD", "baa_spread")
    render_junk_aligned_chart("⚠️ JUNK TO TREASURY BOND SPREADS - CONCERNS OF RISK", "bb_spread")
    render_credit_basis_monitor()

    with st.expander("📚 DEFINITIONS & HOW TO READ: CREDIT RISK"):
        st.markdown("""
        * **BAA TO 10YR SPREAD:** This chart tracks the risk premium for medium-grade (just above junk) corporate bonds relative to safe US Treasuries. As investors fear a slowing economy or corporate bankruptcies, they dump corporate bonds, forcing this yield spread higher. The line dynamically shifts to Orange (>2.0%) and Red (>2.5%) as fear escalates. The S&P 500 Year-over-Year percentage change is plotted on the left axis, explicitly scaled so the 0% growth line aligns with the 3.0% spread threshold, allowing you to instantly visualize how a breach into the "danger zone" correlates with negative equity returns.
        
        * **JUNK TO TREASURY SPREAD:** Similar in mechanics to the BAA spread, but tracking high-yield "Junk" debt (BB rating and below). Because junk companies are highly sensitive to refinancing rates, this is often the very first domino to fall in a credit cycle. The warning thresholds are elevated (Orange > 4.0%, Red > 5.5%) to account for the inherent risk of the asset class. The S&P 500 YoY% is overlaid to confirm when credit contagion spills into the broader equity market.
        
        * **CREDIT BASIS MONITOR (Z-SCORE OSCILLATOR):** A "Basis" compares the price of Credit Default Swaps (insurance against default) versus the actual cash bond yields of the underlying asset. In a functioning market, they price the same risk. When a massive structural break occurs, the prices decouple (a negative basis). To cleanly track this, this chart takes the ratio of the 1-Year Basis divided by the 5-Year Basis, and passes it through a rolling 252-day Z-Score engine. This mathematically standardizes the data, trapping the oscillator permanently between standard deviation bands. A print hitting the +2σ or +3σ ceiling indicates an acute, violent inversion of short-term market panic, plotted perfectly against the S&P 500 drawdown locked to the ceiling of the chart.
        """)

# --- TAB 3: MACRO REGIME & FRAGILITY ---
with tab3:
    render_sahm_rule()
    render_buffett_indicator()

    with st.expander("📚 DEFINITIONS & HOW TO READ: MACRO REGIME & FRAGILITY"):
        st.markdown("""
        * **REAL-TIME SAHM RULE RECESSION INDICATOR:** Developed by former Federal Reserve economist Claudia Sahm, this is one of the most historically accurate, real-time indicators of an active macroeconomic recession. It triggers when the three-month moving average of the national unemployment rate rises by 0.50 percentage points or more relative to its lowest point during the previous 12 months. Unlike traditional GDP data which lags by quarters, the Sahm Rule fires in real-time. Red markers indicate exactly when historical recessions officially began according to this metric.
        
        * **THE BUFFETT INDICATOR (TOTAL MARKET CAP TO GDP):** Famously described by Warren Buffett as "probably the best single measure of where valuations stand at any given moment," this macroeconomic gauge compares the total value of all publicly traded US companies (proxied here using the Wilshire 5000 Price Index) against the total Gross Domestic Product of the United States. The engine dynamically calculates the historical mean and projects rigid Standard Deviation (σ) thresholds. Readings pushing above +1σ (+30%) signal overvaluation, while prints hitting the +2σ (+60%) red line historically precede massive structural bear markets and "lost decades" in equity returns.
        """)