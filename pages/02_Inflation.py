import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

# --- INLINE BLOOMBERG THEME ---
st.set_page_config(layout="wide", page_title="Inflation & Purchasing Power")
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; }
    p, h1, h2, h3, h4, h5, h6, li, td, th, label, div[data-testid="stMetricValue"], .stMetric label {
        font-family: 'Courier New', Courier, monospace !important;
    }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, .stDataFrame td, .stDataFrame th {
        color: #00FF00 !important; font-size: 14px !important; line-height: 1.5 !important;
    }
    h1, h2, h3, h4, h5, h6, .stSubheader {
        color: #FFB100 !important; text-transform: uppercase !important; border-bottom: 1px solid #333333; padding-bottom: 5px;
    }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #FFB100; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] a {
        color: #FFB100 !important; text-decoration: none !important; font-family: 'Courier New', Courier, monospace !important;
    }
    [data-baseweb="tab-list"] { background-color: #000000 !important; }
    [data-baseweb="tab"] { background-color: #111111 !important; color: #FFB100 !important; border: 1px solid #333333; }
    [aria-selected="true"] { background-color: #FFB100 !important; color: #000000 !important; }
    [aria-selected="true"] span, [aria-selected="true"] p { color: #000000 !important; font-weight: bold; }
    hr { border: 0; border-top: 1px solid #333333 !important; }
</style>
""", unsafe_allow_html=True)

# --- TICKERS & EMOJIS ---
FRED_SERIES = {
    'Headline CPI': 'CPIAUCSL',
    'Core CPI': 'CPILFESL',       
    'Core PCE': 'PCEPILFE',
    'PPI': 'PPIFIS'
}

FRED_NATIVE_PERCENT = {
    'Sticky CPI': 'CORESTICKM159SFRBATL', # Explicitly 159 as requested (1-Month Series)
    '5Y Breakeven': 'T5YIE'               
}

FRED_HOUSING_SERIES = {
    'Rent of Primary Residence': 'CUSR0000SEHA',
    'Owners Equivalent Rent': 'CUSR0000SEHC',
    'Case-Shiller': 'CSUSHPISA'
}

FRED_WAGES_SERIES = {
    'AHE': 'CES0500000003',   # Average Hourly Earnings
    'AWE': 'CES0500000011',   # Average Weekly Earnings
    'Hours': 'CES0500000005'  # Average Weekly Hours
}

EMOJI_MAP = {
    'Headline CPI': '🛒', 'Core CPI': '🏷️', 'Core PCE': '🦅', 
    'PPI': '🏭', 'Sticky CPI': '🍯', '5Y Breakeven': '🔮'
}

TITLE_DETAILS = {
    'Headline CPI': 'Consumer Price Index (All Items)',
    'Core CPI': 'Consumer Price Index (Less Food & Energy)',
    'Core PCE': 'Personal Consumption Expenditures (Less Food & Energy)',
    'PPI': 'Producer Price Index (Final Demand)',
    'Sticky CPI': 'Sticky Price Consumer Price Index (Less Food & Energy)',
    '5Y Breakeven': 'Market-Implied Inflation Expectations'
}

# --- DATA FETCHING FUNCTIONS ---
def fetch_fred_series(s_id, start_date, units=None):
    api_key = st.secrets["FRED_API_KEY"]
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={s_id}&api_key={api_key}&file_type=json&observation_start={start_date}"
    if units: url += f"&units={units}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return pd.Series(dtype=float, name=f"ERROR_{response.status_code}")
        obs = response.json().get('observations', [])
        df = pd.DataFrame(obs)[['date', 'value']]
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)
        return df['value']
    except Exception as e:
        return pd.Series(dtype=float, name=f"EXCEPTION_{str(e)}")

@st.cache_data(ttl=86400)
def fetch_inflation_data():
    start_date = (datetime.now() - timedelta(days=12 * 365)).strftime('%Y-%m-%d')
    all_data = {}
    
    all_data['Headline Index'] = fetch_fred_series('CPIAUCSL', start_date)
    
    for name, s_id in FRED_SERIES.items():
        all_data[name] = fetch_fred_series(s_id, start_date, units='pc1')

    for name, s_id in FRED_NATIVE_PERCENT.items():
        all_data[name] = fetch_fred_series(s_id, start_date) # Pulled completely raw
    
    df_final = pd.DataFrame(all_data)
    df_monthly = df_final.drop(columns=['5Y Breakeven']).resample('MS').first().ffill()
    df_daily = df_final[['5Y Breakeven']].ffill().dropna()

    return df_monthly, df_daily

@st.cache_data(ttl=86400)
def fetch_housing_data():
    start_date = (datetime.now() - timedelta(days=40 * 365)).strftime('%Y-%m-%d') 
    df_housing = pd.DataFrame()
    for name, s_id in FRED_HOUSING_SERIES.items():
        df_housing[name] = fetch_fred_series(s_id, start_date, units='pc1')
    return df_housing.resample('MS').first().ffill()

@st.cache_data(ttl=86400)
def fetch_wages_and_sentiment():
    start_date_wages = (datetime.now() - timedelta(days=21 * 365)).strftime('%Y-%m-%d')
    df_wages = pd.DataFrame()
    for name, s_id in FRED_WAGES_SERIES.items():
        df_wages[name] = fetch_fred_series(s_id, start_date_wages, units='pc1')
    
    # Removed destructive .dropna() that was killing the dataframe prior to 2006
    df_wages = df_wages.resample('MS').first().ffill()
    
    start_date_sent = '1960-01-01'
    df_sentiment = pd.DataFrame()
    df_sentiment['UMCSENT'] = fetch_fred_series('UMCSENT', start_date_sent) 
    df_sentiment['MICH'] = fetch_fred_series('MICH', start_date_sent) 
    df_sentiment = df_sentiment.resample('MS').first().ffill()
    
    return df_wages, df_sentiment

df_monthly, df_daily = fetch_inflation_data()
df_housing = fetch_housing_data()
df_wages, df_sentiment = fetch_wages_and_sentiment()
today = datetime.now()

# --- UI HEADER & CLOCK ---
col_title, col_clock = st.columns([3, 1])
with col_title:
    st.title("💸 Macro Inflation & Sentiment Terminal")

with col_clock:
    latest_dt = df_monthly['Headline CPI'].dropna().index[-1]
    curr_yoy = df_monthly['Headline CPI'].iloc[-1]
    
    try:
        last_dec = df_monthly['Headline Index'].loc[f"{latest_dt.year - 1}-12-01"]
        curr_idx = df_monthly['Headline Index'].iloc[-1]
        ytd_val = ((curr_idx / last_dec) - 1) * 100
    except: ytd_val = 0.0

    color = "#00FF00" if curr_yoy <= 2.3 else "#FF0000"
    ytd_color = "#FF0000" if ytd_val > 0 else "#00FF00" 

    st.markdown(f"""
    <div style="text-align: right; padding-top: 15px;">
        <span style="color: #FFB100; font-size: 14px; font-weight: bold; letter-spacing: 1px;">ACTUAL INFLATION ({latest_dt.strftime('%b %Y')})</span><br>
        <span style="font-size: 38px; color: {color}; font-weight: bold; line-height: 1;">YoY: {curr_yoy:.1f}%</span><br>
        <span style="font-size: 18px; color: {ytd_color}; font-weight: bold;">YTD: {ytd_val:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📉 INFLATION TERMINAL", "🏠 HOUSING VS RENT", "💼 WAGES", "🧠 CONSUMER SENTIMENT"])

# ==========================================
# TAB 1: INFLATION TERMINAL
# ==========================================
with tab1:
    slider_options = list(range(6, 121))
    format_lookback = lambda m: f"{(today - relativedelta(months=m)).strftime('%b %Y')} ({m} Mos)"

    def render_section(name):
        st.subheader(f"{EMOJI_MAP.get(name, '')} {name} - *{TITLE_DETAILS.get(name, '')}*")
        
        months_back = st.select_slider("LOOKBACK", options=slider_options, value=24, format_func=format_lookback, key=f"s_{name}", label_visibility="collapsed")
        
        fig = go.Figure()
        
        if name == '5Y Breakeven':
            plot_df = df_daily['5Y Breakeven'].iloc[-months_back*21:] 
            if not plot_df.empty:
                y_min, y_max = plot_df.min() - 0.05, plot_df.max() + 0.05
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df.values, mode='lines', line=dict(color='#FFB100', width=3), fill='tozeroy', fillcolor='rgba(255,177,0,0.1)'))
                fig.update_layout(yaxis=dict(range=[y_min, y_max]))
        else:
            plot_df = df_monthly[name].dropna().iloc[-months_back:]
            y_min, y_max = plot_df.min() - 0.3, plot_df.max() + 0.3
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df.values, marker_color='#FFB100', text=[f"{v:.1f}%" for v in plot_df.values], textposition='none'))
            
            targets = {'Headline CPI': 2.3, 'Core CPI': 2.0, 'Core PCE': 2.0}
            if name in targets:
                fig.add_hline(
                    y=targets[name], 
                    line_dash="dash", 
                    line_color="#00FF00", 
                    line_width=3, 
                    annotation_text=f"FED TARGET ({targets[name]:.1f}%)",
                    annotation_position="top left",
                    annotation_font=dict(color="#00FF00", size=14, weight="bold")
                )
            
            fig.update_layout(yaxis=dict(range=[y_min, y_max]))

        fig.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400, margin=dict(l=0, r=0, b=0, t=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

    for section in ['Headline CPI', 'Core CPI', 'Core PCE', 'PPI', 'Sticky CPI', '5Y Breakeven']:
        render_section(section)

# ==========================================
# TAB 2: HOUSING PRICE INDEX VS RENT INFLATION
# ==========================================
with tab2:
    st.subheader("🏠 Home Price Index vs. Rent Inflation Divergence")
    if not df_housing.empty:
        col_slider1, col_slider2 = st.columns([2, 1])
        with col_slider1:
            min_date, max_date = df_housing.dropna().index.min().date(), df_housing.dropna().index.max().date()
            start_date, end_date = st.slider("SELECT HISTORICAL DATA RANGE", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM YYYY")
        with col_slider2:
            lag_shift = st.slider("SHIFT RENT / OER LINES (MONTHS)", min_value=-24, max_value=24, value=0)
            
        mask = (df_housing.index.date >= start_date) & (df_housing.index.date <= end_date)
        plot_df = df_housing.loc[mask]

        if not plot_df.empty:
            l_data_min, l_data_max = plot_df['Case-Shiller'].min(), plot_df['Case-Shiller'].max()
            r_data_min = plot_df[['Rent of Primary Residence', 'Owners Equivalent Rent']].min().min()
            r_data_max = plot_df[['Rent of Primary Residence', 'Owners Equivalent Rent']].max().max()

            effective_r_min = min(r_data_min, (l_data_min + 5) / 2)
            effective_r_max = max(r_data_max, (l_data_max + 5) / 2)

            r_min_final = np.floor(effective_r_min / 2.5) * 2.5
            r_max_final = np.ceil(effective_r_max / 2.5) * 2.5
            l_min_final = 2 * r_min_final - 5
            l_max_final = 2 * r_max_final - 5

            fig_house = make_subplots(specs=[[{"secondary_y": True}]])
            fig_house.add_trace(go.Bar(x=plot_df.index, y=plot_df['Case-Shiller'], name="S&P/CS National Home Price (L)", marker=dict(color='rgba(0,191,255,0.8)')), secondary_y=False)

            shifted_dates = plot_df.index + pd.DateOffset(months=lag_shift)

            fig_house.add_trace(go.Scatter(x=shifted_dates, y=plot_df['Rent of Primary Residence'], mode='lines', name="Rent of Primary Residence (R)", line=dict(color='#FF0000', width=2)), secondary_y=True)
            fig_house.add_trace(go.Scatter(x=shifted_dates, y=plot_df['Owners Equivalent Rent'], mode='lines', name="Owners' Equivalent Rent (R)", line=dict(color='#FFFF00', width=2, dash='solid')), secondary_y=True)
            
            fig_house.add_hline(y=0, line_dash="solid", line_color="#FFFFFF", secondary_y=False)
            x_max_extended = end_date + relativedelta(months=48)

            fig_house.update_layout(
                template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=600, margin=dict(l=0, r=0, b=0, t=20), hovermode="closest",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(range=[start_date, x_max_extended], gridcolor="#222222"),
                yaxis=dict(title="S&P/CS Home Price (YoY %)", range=[l_min_final, l_max_final], dtick=5, gridcolor="#222222", side="left"),
                yaxis2=dict(title="Rent Inflation (YoY %)", range=[r_min_final, r_max_final], dtick=2.5, gridcolor="#222222", showgrid=True, side="right", overlaying="y")
            )
            st.plotly_chart(fig_house, use_container_width=True)

# ==========================================
# TAB 3: WAGES (ALL EMPLOYEES, PRIVATE NONFARM)
# ==========================================
with tab3:
    st.subheader("💼 Wages & Hours (YoY % Change)")
    st.markdown("*All employees on private nonfarm payrolls, seasonally adjusted*")
    
    # --- DIAGNOSTIC ERROR CATCHER ---
    if df_wages.dropna(how='all').empty:
        st.error("⚠️ DATA FETCH ERROR: No wage data was returned from the FRED API. See raw API state below:")
        st.dataframe(df_wages.tail(10))
    else:
        slider_options_w = list(range(12, 241))
        format_lookback_w = lambda m: f"{(today - relativedelta(months=m)).strftime('%b %Y')} ({m} Mos)"
        
        months_back_w = st.select_slider("LOOKBACK WINDOW", options=slider_options_w, value=120, format_func=format_lookback_w, key="wages_slider", label_visibility="collapsed")
        
        plot_wages = df_wages.iloc[-months_back_w:].dropna(how='all')

        fig_wages = go.Figure()
        
        # 1. Average Hourly Earnings (Solid Red)
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['AHE'], mode='lines', name="Average Hourly Earnings", line=dict(color='#FF0000', width=2)))
        
        # 2. Average Weekly Earnings (Dashed Yellow)
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['AWE'], mode='lines', name="Average Weekly Earnings", line=dict(color='#FFFF00', width=2, dash='dash')))
        
        # 3. Average Weekly Hours (Dotted Blue)
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['Hours'], mode='lines', name="Average Weekly Hours", line=dict(color='#00BFFF', width=2, dash='dot')))
        
        fig_wages.add_hline(y=0, line_dash="solid", line_color="#888888")
        
        y_min_w, y_max_w = plot_wages.min().min() - 0.5, plot_wages.max().max() + 0.5
        
        fig_wages.update_layout(
            template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="YoY % Change", gridcolor="#222222", range=[y_min_w, y_max_w]), 
            xaxis=dict(gridcolor="#222222"),
            height=500, margin=dict(l=0, r=0, b=0, t=10), hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_wages, use_container_width=True)

# ==========================================
# TAB 4: CONSUMER SENTIMENT
# ==========================================
with tab4:
    if not df_sentiment.empty:
        s_min_date = df_sentiment.dropna().index.min().date()
        s_max_date = df_sentiment.dropna().index.max().date()

        st.subheader("🧠 U.S. Consumer Sentiment Index")
        start_s1, end_s1 = st.slider("LOOKBACK WINDOW", min_value=s_min_date, max_value=s_max_date, value=(s_min_date, s_max_date), format="MMM YYYY", key="sent_slider1")
        mask_s1 = (df_sentiment.index.date >= start_s1) & (df_sentiment.index.date <= end_s1)
        plot_sent = df_sentiment.loc[mask_s1].dropna(subset=['UMCSENT'])
        
        fig_s1 = go.Figure()
        if not plot_sent.empty:
            y_min_s1, y_max_s1 = plot_sent['UMCSENT'].min() - 2, plot_sent['UMCSENT'].max() + 2
            
            fig_s1.add_trace(go.Scatter(x=plot_sent.index, y=plot_sent['UMCSENT'], mode='lines', line=dict(color='#00BFFF', width=2), fill='tozeroy', fillcolor='rgba(0,191,255,0.1)', name="Sentiment Index"))
            fig_s1.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(title="Index Value", gridcolor="#222222", range=[y_min_s1, y_max_s1]), xaxis=dict(gridcolor="#222222"), height=400, margin=dict(l=0, r=0, b=0, t=10), hovermode="x unified")
            st.plotly_chart(fig_s1, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("📈 UMich 1-Year Consumer Inflation Expectations")
        start_s2, end_s2 = st.slider("LOOKBACK WINDOW", min_value=s_min_date, max_value=s_max_date, value=(s_min_date, s_max_date), format="MMM YYYY", key="sent_slider2")
        mask_s2 = (df_sentiment.index.date >= start_s2) & (df_sentiment.index.date <= end_s2)
        plot_mich = df_sentiment.loc[mask_s2].dropna(subset=['MICH']) 
        
        fig_s2 = go.Figure()
        if not plot_mich.empty:
            y_min_m, y_max_m = plot_mich['MICH'].min() - 0.5, plot_mich['MICH'].max() + 0.5
            fig_s2.add_trace(go.Scatter(x=plot_mich.index, y=plot_mich['MICH'], mode='lines', line=dict(color='#FFB100', width=2), fill='tozeroy', fillcolor='rgba(255,177,0,0.1)', name="1-Yr Expectations"))
            fig_s2.add_hline(y=2.0, line_dash="dash", line_color="#00FF00", annotation_text="Fed 2% Target", annotation_position="top left", annotation_font=dict(color="#00FF00", size=14, weight="bold"))
            fig_s2.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(title="Expected Inflation (%)", gridcolor="#222222", range=[y_min_m, y_max_m]), xaxis=dict(gridcolor="#222222"), height=400, margin=dict(l=0, r=0, b=0, t=10), hovermode="x unified")
            st.plotly_chart(fig_s2, use_container_width=True)