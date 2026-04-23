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
    .expert-note {
        background-color: #0a0a0a;
        border-left: 3px solid #FFB100;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 25px;
    }
    .expert-header {
        color: #FFB100;
        font-weight: bold;
        font-size: 12px;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
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
    'Sticky CPI': 'CORESTICKM159SFRBATL', 
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
        all_data[name] = fetch_fred_series(s_id, start_date) 
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
    df_wages = df_wages.resample('MS').first().ffill()
    start_date_sent = '1960-01-01'
    df_sentiment = pd.DataFrame()
    df_sentiment['UMCSENT'] = fetch_fred_series('UMCSENT', start_date_sent) 
    df_sentiment['MICH'] = fetch_fred_series('MICH', start_date_sent) 
    df_sentiment = df_sentiment.resample('MS').first().ffill()
    return df_wages, df_sentiment

# --- NEW: EXPERT NOTES RENDERER ---
def render_expert_note(chart_key):
    notes = {
        'Headline CPI': "Headline CPI tracks the total change in prices for a basket of goods/services consumed by urban households. El-Erian emphasizes that while Headline creates political noise, it often falls victim to volatile energy swings. Knotek views this as the outer shell of inflation—easy to see, but potentially misleading for long-term policy. Look for the 'last mile' problem here; getting from 3% to 2% is structurally harder than getting from 9% to 3% due to embedded service costs.",
        'Core CPI': "Core CPI strips out food and energy to reveal the underlying trend. This represents the 'Inflation Mosaic' that El-Erian frequently discusses—a shift from transitory supply shocks to persistent demand-side pressures. It is the fundamental recipe for price-setting behavior. If Core remains elevated while Headline drops, Edward Knotek warns that inflation expectations have likely become 'unanchored,' requiring higher-for-longer rates to break the momentum.",
        'Core PCE': "The Fed’s preferred gauge, Core PCE, uses a chain-weighted recipe that accounts for 'substitution'—if beef is expensive, people buy chicken. El-Erian views this as a more accurate reflection of the 'New Normal' in consumer behavior. Because it captures broader rural and business data, Knotek uses it to 'nowcast' the Fed's next move. A divergence between CPI and PCE often signals a shift in consumer resilience or a structural change in healthcare and financial service costs.",
        'PPI': "PPI measures inflation at the producer/wholesale level—the 'input costs' of the economy. It is the leading edge of the inflation pipeline. Knotek monitors this for 'pass-through' effects; if PPI stays high, companies eventually pass those costs to consumers. El-Erian notes that in a world of deglobalization and supply chain fragmentation, PPI volatility is a permanent feature. Watch for a tightening gap between PPI and CPI, which signals squeezed corporate profit margins.",
        'Sticky CPI': "Sticky CPI focuses on items like medical care and insurance that change prices slowly—this is Edward Knotek’s specialty. It is the 'heart' of inflation persistence. Unlike 'Flexible' goods (gas, clothes), once Sticky CPI rises, it rarely comes down quickly. El-Erian warns that high Sticky CPI represents 'inflation inertia.' If this line is flat or rising, the Fed is effectively trapped, as monetary policy has a significantly longer lag in cooling these specific service-based sectors.",
        '5Y Breakeven': "This is the market's 'crystal ball,' derived from the difference between nominal and inflation-protected Treasuries (TIPS). It represents the Market-Implied expectation for average inflation over the next five years. El-Erian views this as a measure of Fed credibility—if breakevens rise, the market is calling the Fed's bluff. Knotek treats this as a critical input for price stability; when expectations rise, workers demand higher wages, creating the dreaded wage-price spiral the Fed fears most.",
        'Housing Divergence': "This chart pits Case-Shiller (real-time home prices) against Rent/OER (the survey-based 'Owner’s Equivalent Rent' used in CPI). Knotek’s research highlights the 12-to-18 month lag between home price changes and CPI reflection. El-Erian calls this a 'lagged distortion' that can make the Fed look like they are fighting yesterday’s war. Watch for the 'De-Inversion'—if Case-Shiller drops but Rents stay high, the inflation data will remain artificially 'hot' even as the real economy cools.",
        'Wages': "Tracking Average Hourly Earnings (AHE) vs. Hours reveals the labor market's true heat. El-Erian watches for structural 'labor shortages' that drive wages higher regardless of productivity. Knotek monitors the YoY % change as a precursor to service-sector inflation. The 'recipe' to watch is the spread between Earnings and Hours—if earnings rise while hours fall, it suggests a tightening labor market where employers are paying more for less output, a direct threat to the 2% inflation target.",
        'Sentiment': "The UMich index measures how the public 'feels' about the economy, which El-Erian argues is the ultimate driver of consumer spending resilience. Knotek focuses specifically on the 'MICH' expectations component; if consumers expect 4% inflation, they spend now rather than later, creating a self-fulfilling prophecy. Look for the 'sentiment-reality gap'—if consumers are depressed but spending continues, the Fed has more room to hike. If sentiment and spending both crater, a hard landing is imminent."
    }
    
    st.markdown(f"""
    <div class="expert-note">
        <div class="expert-header">TERMINAL INTELLIGENCE: El-Erian (Allianz) & Knotek II (Cleveland Fed)</div>
        {notes.get(chart_key, "No notes available for this section.")}
    </div>
    """, unsafe_allow_html=True)

# --- EXECUTION ---
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
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df.values, marker_color='#FFB100'))
            targets = {'Headline CPI': 2.3, 'Core CPI': 2.0, 'Core PCE': 2.0}
            if name in targets:
                fig.add_hline(y=targets[name], line_dash="dash", line_color="#00FF00", line_width=3, annotation_text=f"FED TARGET", annotation_position="top left")
            fig.update_layout(yaxis=dict(range=[y_min, y_max]))

        fig.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(l=0, r=0, b=0, t=10))
        st.plotly_chart(fig, use_container_width=True)
        # --- ADD NOTE ---
        render_expert_note(name)
        st.markdown("---")

    for section in ['Headline CPI', 'Core CPI', 'Core PCE', 'PPI', 'Sticky CPI', '5Y Breakeven']:
        render_section(section)

# ==========================================
# TAB 2: HOUSING VS RENT
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
            r_min_final, r_max_final = np.floor(r_data_min / 2.5) * 2.5, np.ceil(r_data_max / 2.5) * 2.5
            l_min_final, l_max_final = 2 * r_min_final - 5, 2 * r_max_final - 5

            fig_house = make_subplots(specs=[[{"secondary_y": True}]])
            fig_house.add_trace(go.Bar(x=plot_df.index, y=plot_df['Case-Shiller'], name="Home Price (L)", marker=dict(color='rgba(0,191,255,0.8)')), secondary_y=False)
            shifted_dates = plot_df.index + pd.DateOffset(months=lag_shift)
            fig_house.add_trace(go.Scatter(x=shifted_dates, y=plot_df['Rent of Primary Residence'], mode='lines', name="Rent (R)", line=dict(color='#FF0000', width=2)), secondary_y=True)
            fig_house.add_trace(go.Scatter(x=shifted_dates, y=plot_df['Owners Equivalent Rent'], mode='lines', name="OER (R)", line=dict(color='#FFFF00', width=2)), secondary_y=True)
            fig_house.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=600, margin=dict(l=0, r=0, b=0, t=20), hovermode="closest")
            st.plotly_chart(fig_house, use_container_width=True)
            # --- ADD NOTE ---
            render_expert_note('Housing Divergence')

# ==========================================
# TAB 3: WAGES
# ==========================================
with tab3:
    st.subheader("💼 Wages & Hours (YoY % Change)")
    if not df_wages.dropna(how='all').empty:
        slider_options_w = list(range(12, 241))
        months_back_w = st.select_slider("LOOKBACK WINDOW", options=slider_options_w, value=120, key="wages_slider", label_visibility="collapsed")
        plot_wages = df_wages.iloc[-months_back_w:].dropna(how='all')
        fig_wages = go.Figure()
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['AHE'], mode='lines', name="AHE", line=dict(color='#FF0000', width=2)))
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['AWE'], mode='lines', name="AWE", line=dict(color='#FFFF00', width=2, dash='dash')))
        fig_wages.add_trace(go.Scatter(x=plot_wages.index, y=plot_wages['Hours'], mode='lines', name="Hours", line=dict(color='#00BFFF', width=2, dash='dot')))
        fig_wages.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=500, hovermode="x unified")
        st.plotly_chart(fig_wages, use_container_width=True)
        # --- ADD NOTE ---
        render_expert_note('Wages')

# ==========================================
# TAB 4: CONSUMER SENTIMENT
# ==========================================
with tab4:
    if not df_sentiment.empty:
        st.subheader("🧠 U.S. Consumer Sentiment & Expectations")
        plot_sent = df_sentiment.dropna(subset=['UMCSENT'])
        fig_s1 = go.Figure()
        fig_s1.add_trace(go.Scatter(x=plot_sent.index, y=plot_sent['UMCSENT'], mode='lines', line=dict(color='#00BFFF', width=2), fill='tozeroy', name="Sentiment"))
        fig_s1.update_layout(template='plotly_dark', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig_s1, use_container_width=True)
        # --- ADD NOTE ---
        render_expert_note('Sentiment')