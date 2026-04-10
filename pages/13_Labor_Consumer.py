import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime

# Import your custom Bloomberg Theme
from theme import inject_custom_css

# Handle multiple data sources safely
try:
    from fredapi import Fred
except ImportError:
    Fred = None
try:
    import pandas_datareader.data as web
except ImportError:
    web = None
try:
    import yfinance as yf
except ImportError:
    yf = None

st.set_page_config(page_title="Labor & Consumer", layout="wide")

# Inject the theme globally
inject_custom_css()

# ==========================================
# AUTHENTICATION (SECURE)
# ==========================================
try:
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
except (KeyError, FileNotFoundError):
    FRED_API_KEY = None

fred = Fred(api_key=FRED_API_KEY) if Fred and FRED_API_KEY else None

if not FRED_API_KEY:
    st.warning("⚠️ No FRED API Key found in st.secrets. Relying on fallback scraper.")

# ==========================================
# HELPER FUNCTIONS & DATA FETCHING
# ==========================================

@st.cache_data(ttl=3600)
def fetch_macro_data(ticker, start_date, end_date):
    """Fetches data with a 400-day buffer to allow for YoY and rolling averages without dropping data."""
    
    buffer_date = start_date - datetime.timedelta(days=400)
    buffer_str = buffer_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # --- YFINANCE ROUTING (S&P 500 DRAWDOWNS) ---
    if ticker == "SP500_DRAWDOWN" and yf is not None:
        try:
            df = yf.download("^GSPC", start=buffer_date, end=end_date)
            if df.empty: return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df['High'] = df['Close'].cummax()
            df['SP500_DRAWDOWN'] = ((df['Close'] - df['High']) / df['High']) * 100
            df = df[['SP500_DRAWDOWN']].dropna()
            return df[df.index >= pd.to_datetime(start_date)]
        except Exception:
            return None

    # --- DUAL-ENGINE FRED ROUTING ---
    def get_fred(t):
        d = None
        if fred is not None:
            try:
                s = fred.get_series(t, observation_start=buffer_str, observation_end=end_str)
                d = pd.DataFrame(s, columns=[t])
            except Exception:
                pass
        if d is None and web is not None:
            try:
                d = web.DataReader(t, 'fred', buffer_str, end_str)
            except Exception:
                pass
        if d is not None and not d.empty:
            d.index = pd.to_datetime(d.index).tz_localize(None)
            return d
        return None

    try:
        # Complex Math Tickers
        if ticker == "ICSA_PACK":
            df = get_fred('ICSA')
            if df is not None:
                df['ICSA_4WK'] = df['ICSA'].rolling(window=4).mean()
                df = df.dropna()
                return df[df.index >= pd.to_datetime(start_date)]
                
        if ticker == "PAYEMS_3MO":
            df = get_fred('PAYEMS')
            if df is not None:
                # Calculate monthly change in thousands
                df['MOM_CHANGE'] = df['PAYEMS'].diff()
                # 3-Month Rolling Average of the MoM change
                df['PAYEMS_3MO'] = df['MOM_CHANGE'].rolling(window=3).mean()
                df = df[['PAYEMS_3MO']].dropna()
                return df[df.index >= pd.to_datetime(start_date)]

        if ticker == "JOLTS_RATIO":
            df_j = get_fred('JTSJOL')
            df_u = get_fred('UNEMPLOY')
            if df_j is not None and df_u is not None:
                # Align standard monthly frequencies
                df_j = df_j.resample('MS').first()
                df_u = df_u.resample('MS').first()
                df = df_j.join(df_u, how='inner').dropna()
                df['RATIO'] = df['JTSJOL'] / df['UNEMPLOY']
                return df[['RATIO']][df.index >= pd.to_datetime(start_date)]
                
        if ticker == "ACTLIS_YOY":
            df = get_fred('ACTLISCOUUS')
            if df is not None:
                # YoY percentage change (12 months)
                df = df.resample('MS').first()
                df['ACTLIS_YOY'] = df['ACTLISCOUUS'].pct_change(12) * 100
                df = df[['ACTLIS_YOY']].dropna()
                return df[df.index >= pd.to_datetime(start_date)]

        # Standard Tickers
        df = get_fred(ticker)
        if df is not None:
            df = df.ffill().dropna()
            return df[df.index >= pd.to_datetime(start_date)]
            
    except Exception:
        return None
    return None

# ==========================================
# BASE LAYOUT GENERATOR
# ==========================================
def get_base_layout(title, height=550):
    return dict(
        title=dict(text=title, font=dict(color="#FFB100", family="Courier New", size=16)),
        margin=dict(l=60, r=60, t=50, b=30), height=height, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor="#333333", tickfont=dict(color="#00FF00", family="Courier New")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

def add_drawdown_trace(fig, df_dd, sp_min_fallback=-50):
    """Helper to consistently add the transparent white S&P 500 drawdown to the left axis."""
    if df_dd is not None and not df_dd.empty:
        fig.add_trace(go.Scatter(
            x=df_dd.index, 
            y=df_dd['SP500_DRAWDOWN'], 
            name="S&P 500 Drawdown (L1)", 
            mode='lines', 
            line=dict(color="rgba(255, 255, 255, 0.6)", width=1.5), 
            fill='tozeroy', 
            fillcolor="rgba(255, 255, 255, 0.3)", 
            yaxis="y1"
        ))
        return df_dd['SP500_DRAWDOWN'].min() * 1.05
    return sp_min_fallback

# ==========================================
# CUSTOM CHART RENDERERS
# ==========================================

def render_jobless_claims():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Jobless Claims", min_value=(today - datetime.timedelta(days=20*365)), max_value=today, value=(today - datetime.timedelta(days=5*365), today), format="YYYY-MM-DD", key="sl_icsa", label_visibility="collapsed")
    
    df_dd = fetch_macro_data("SP500_DRAWDOWN", start_date, end_date)
    df_data = fetch_macro_data("ICSA_PACK", start_date, end_date)
    
    fig = go.Figure()
    sp_min = add_drawdown_trace(fig, df_dd)
        
    if df_data is not None and not df_data.empty:
        fig.add_trace(go.Bar(x=df_data.index, y=df_data['ICSA'], name="Weekly Claims (R1)", marker_color="rgba(0, 191, 255, 0.4)", yaxis="y2"))
        fig.add_trace(go.Scatter(x=df_data.index, y=df_data['ICSA_4WK'], name="4-Week MA (R1)", mode='lines', line=dict(color="#00BFFF", width=2.5), yaxis="y2"))
        y2_max = df_data['ICSA'].max() * 1.1
    else:
        y2_max = 500000

    fig.update_layout(
        **get_base_layout("🚨 INITIAL JOBLESS CLAIMS (THE CANARY)"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Claims", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[0, y2_max], tickfont=dict(color="#00BFFF", family="Courier New"))
    )
    st.plotly_chart(fig, width='stretch')

def render_nfp():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Nonfarm Payrolls", min_value=(today - datetime.timedelta(days=20*365)), max_value=today, value=(today - datetime.timedelta(days=5*365), today), format="YYYY-MM-DD", key="sl_nfp", label_visibility="collapsed")
    
    df_dd = fetch_macro_data("SP500_DRAWDOWN", start_date, end_date)
    df_data = fetch_macro_data("PAYEMS_3MO", start_date, end_date)
    
    fig = go.Figure()
    sp_min = add_drawdown_trace(fig, df_dd)
        
    if df_data is not None and not df_data.empty:
        colors = ['#00FF00' if val >= 0 else '#FF3333' for val in df_data['PAYEMS_3MO']]
        fig.add_trace(go.Bar(x=df_data.index, y=df_data['PAYEMS_3MO'], name="NFP 3-Mo Avg (R1)", marker_color=colors, yaxis="y2"))
        y_abs_max = max(abs(df_data['PAYEMS_3MO'].max()), abs(df_data['PAYEMS_3MO'].min())) * 1.1
    else:
        y_abs_max = 500

    fig.update_layout(
        **get_base_layout("📉 NONFARM PAYROLLS (3-MONTH ROLLING AVERAGE MOMENTUM)"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Jobs Added/Lost (Thousands)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[-y_abs_max, y_abs_max], tickfont=dict(color="#00FF00", family="Courier New"))
    )
    fig.add_hline(y=0, line_dash="solid", line_color="#FFFFFF", yref="y2", opacity=0.5)
    st.plotly_chart(fig, width='stretch')

def render_jolts():
    today = datetime.date.today()
    min_jolts_date = datetime.date(2000, 12, 1) # JOLTS data starts Dec 2000
    start_date, end_date = st.slider("📅 LOOKBACK: JOLTS Data", min_value=min_jolts_date, max_value=today, value=(today - datetime.timedelta(days=10*365), today), format="YYYY-MM-DD", key="sl_jolts", label_visibility="collapsed")
    
    df_dd = fetch_macro_data("SP500_DRAWDOWN", start_date, end_date)
    df_j = fetch_macro_data("JTSJOL", start_date, end_date)
    df_ratio = fetch_macro_data("JOLTS_RATIO", start_date, end_date)
    
    # --- CHART 1: RAW JOLTS ---
    fig1 = go.Figure()
    sp_min = add_drawdown_trace(fig1, df_dd)
        
    if df_j is not None and not df_j.empty:
        fig1.add_trace(go.Bar(x=df_j.index, y=df_j['JTSJOL'], name="Job Openings (R1)", marker_color="#FFB100", yaxis="y2"))
        j_max = df_j['JTSJOL'].max() * 1.1
    else:
        j_max = 15000

    fig1.update_layout(
        **get_base_layout("🏢 TOTAL JOB OPENINGS (JOLTS)"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Openings (Thousands)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[0, j_max], tickfont=dict(color="#FFB100", family="Courier New"))
    )
    st.plotly_chart(fig1, width='stretch')

    # --- CHART 2: JOLTS/UNEMPLOYED RATIO ---
    fig2 = go.Figure()
    add_drawdown_trace(fig2, df_dd)
        
    if df_ratio is not None and not df_ratio.empty:
        fig2.add_trace(go.Scatter(x=df_ratio.index, y=df_ratio['RATIO'], name="Openings per Unemployed (R1)", mode='lines', line=dict(color="#FF00FF", width=2.5), yaxis="y2"))
        r_max = df_ratio['RATIO'].max() * 1.1
    else:
        r_max = 2.5

    fig2.update_layout(
        **get_base_layout("⚖️ LABOR TIGHTNESS (JOB OPENINGS PER UNEMPLOYED PERSON)"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Ratio", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[0, r_max], tickfont=dict(color="#FF00FF", family="Courier New"))
    )
    fig2.add_hline(y=1.0, line_dash="dash", line_color="#00FF00", annotation_text="1.0 (BALANCED MARKET)", yref="y2")
    fig2.add_hline(y=1.2, line_dash="dot", line_color="#FFB100", annotation_text="1.2 (TIGHT)", yref="y2")
    st.plotly_chart(fig2, width='stretch')

def render_consumer_credit():
    today = datetime.date.today()
    start_date, end_date = st.slider("📅 LOOKBACK: Consumer Credit", min_value=(today - datetime.timedelta(days=30*365)), max_value=today, value=(today - datetime.timedelta(days=15*365), today), format="YYYY-MM-DD", key="sl_cc", label_visibility="collapsed")
    
    df_dd = fetch_macro_data("SP500_DRAWDOWN", start_date, end_date)
    df_cc = fetch_macro_data("DRCCLACBS", start_date, end_date)
    
    fig = go.Figure()
    sp_min = add_drawdown_trace(fig, df_dd)
        
    if df_cc is not None and not df_cc.empty:
        fig.add_trace(go.Scatter(x=df_cc.index, y=df_cc['DRCCLACBS'], name="Delinquency Rate (R1)", mode='lines', line=dict(color="#FF3333", width=2.5), yaxis="y2"))
        cc_max = df_cc['DRCCLACBS'].max() * 1.1
    else:
        cc_max = 8.0

    fig.update_layout(
        **get_base_layout("💳 CREDIT CARD DELINQUENCY RATE (ALL COMMERCIAL BANKS)"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="Rate (%)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[0, cc_max], tickfont=dict(color="#FF3333", family="Courier New"))
    )
    st.plotly_chart(fig, width='stretch')

def render_housing():
    today = datetime.date.today()
    min_date = datetime.date(2016, 7, 1) # Realtor.com data starts ~2016
    start_date, end_date = st.slider("📅 LOOKBACK: Housing Inventory", min_value=min_date, max_value=today, value=(min_date, today), format="YYYY-MM-DD", key="sl_house", label_visibility="collapsed")
    
    df_dd = fetch_macro_data("SP500_DRAWDOWN", start_date, end_date)
    df_house = fetch_macro_data("ACTLIS_YOY", start_date, end_date)
    
    fig = go.Figure()
    sp_min = add_drawdown_trace(fig, df_dd)
        
    if df_house is not None and not df_house.empty:
        colors = ['#FF3333' if val >= 0 else '#00FF00' for val in df_house['ACTLIS_YOY']] # Rising inventory (red) is bad for housing prices
        fig.add_trace(go.Bar(x=df_house.index, y=df_house['ACTLIS_YOY'], name="Active Listings YoY% (R1)", marker_color=colors, yaxis="y2"))
        y_abs = max(abs(df_house['ACTLIS_YOY'].max()), abs(df_house['ACTLIS_YOY'].min())) * 1.1
    else:
        y_abs = 50

    fig.update_layout(
        **get_base_layout("🏘️ HOUSING INVENTORY: ACTIVE LISTINGS YOY% CHANGE"),
        yaxis=dict(title="S&P Drawdown (%)", side="left", showgrid=False, range=[sp_min, 0], tickfont=dict(color="rgba(255, 255, 255, 0.5)", family="Courier New")),
        yaxis2=dict(title="YoY Change (%)", side="right", overlaying="y", showgrid=True, gridcolor="#333333", range=[-y_abs, y_abs], tickfont=dict(color="#FFB100", family="Courier New"))
    )
    fig.add_hline(y=0, line_dash="solid", line_color="#FFFFFF", yref="y2", opacity=0.5)
    st.plotly_chart(fig, width='stretch')

# ==========================================
# MAIN APP & TABS
# ==========================================
st.title("👥 LABOR & CONSUMER STRESS TERMINAL")

tab1, tab2, tab3 = st.tabs(["👔 1. EMPLOYMENT PULSE", "🧲 2. LABOR TIGHTNESS (JOLTS)", "🛒 3. CONSUMER & HOUSING"])

# --- TAB 1: EMPLOYMENT PULSE ---
with tab1:
    render_jobless_claims()
    render_nfp()
    
    with st.expander("📚 DEFINITIONS & HOW TO READ: EMPLOYMENT PULSE"):
        st.markdown("""
        * **INITIAL JOBLESS CLAIMS (THE CANARY):** Nonfarm payrolls are reported once a month and are subject to massive revisions. Initial Jobless Claims are reported every Thursday. This is the most real-time indicator of corporate layoffs. The raw bars are highly volatile, so we plot a 4-Week Moving Average over them. When the blue line starts sloping steeply upwards, corporations are actively capitulating.
        
        * **NONFARM PAYROLLS (3-MONTH MOMENTUM):** The headline NFP number is notoriously noisy. Institutional analysts smooth this out by calculating the 3-month rolling average of the monthly change. When this average drops below 100,000, economic growth is stalling. When it flashes red (drops below zero), the economy is officially shedding jobs.
        """)

# --- TAB 2: JOLTS ---
with tab2:
    render_jolts()

    with st.expander("📚 DEFINITIONS & HOW TO READ: LABOR TIGHTNESS"):
        st.markdown("""
        * **TOTAL JOB OPENINGS (JOLTS):** The Job Openings and Labor Turnover Survey. This tracks the total number of unfilled jobs in the US economy.
        
        * **LABOR TIGHTNESS RATIO:** This is Federal Reserve Chairman Jerome Powell's favorite metric. It takes the total number of job openings and divides it by the total number of unemployed persons. 
            * A reading of **1.0** means the market is perfectly balanced (one job for every one person looking).
            * During the post-COVID inflation spike, this ratio hit **2.0** (two jobs for every person), forcing companies to violently bid up wages to attract talent. Tracking this descent back to 1.0 tells you exactly how much "heat" has left the labor market.
        """)

# --- TAB 3: CONSUMER & HOUSING ---
with tab3:
    render_consumer_credit()
    render_housing()

    with st.expander("📚 DEFINITIONS & HOW TO READ: CONSUMER & HOUSING"):
        st.markdown("""
        * **CREDIT CARD DELINQUENCY RATE:** This is the ultimate "end of the conveyor belt" metric. When the consumer's wages fail to keep up with inflation, or when they lose their job, the very first bill they stop paying is unsecured credit card debt. A non-seasonal spike in this red line confirms that systemic stress has officially infected the consumer's wallet.
        
        * **ACTIVE HOUSING LISTINGS (YOY%):** The housing market is the bedrock of consumer wealth. When unemployment rises, forced selling increases, but buyer demand evaporates due to fear or lack of income. This creates a supply glut. We chart the Year-over-Year percentage change. Red bars indicate active listings are piling up faster than last year, acting as a heavy anchor on housing prices.
        """)