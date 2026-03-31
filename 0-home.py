import streamlit as st

# --- 1. PAGE CONFIG & BLOOMBERG THEME ---
st.set_page_config(page_title="TERMINAL: SWITCHBOARD", layout="wide", initial_sidebar_state="expanded")

# Bloomberg Terminal CSS Injection
st.markdown(
    """
    <style>
    /* Main background */
    .stApp { background-color: #000000 !important; }
    
    /* Safely apply Monospace ONLY to actual text elements */
    p, h1, h2, h3, h4, h5, h6, li, td, th, label, div[data-testid="stMetricValue"], .stMetric label {
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Target actual text content for Neon Green */
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] li {
        color: #00FF00 !important;
        font-size: 14px !important; 
        line-height: 1.5 !important;
    }

    /* Override headers to Bloomberg Amber */
    h1, h2, h3, h4 {
        color: #FFB100 !important;
        text-transform: uppercase !important;
        border-bottom: 1px solid #333333;
        padding-bottom: 5px;
    }
    
    /* --- SIDEBAR STYLING --- */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #FFB100;
    }
    
    /* Sidebar Links - Amber */
    [data-testid="stSidebar"] a {
        color: #FFB100 !important;
        text-decoration: none !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] a:hover {
        color: #00FF00 !important;
    }

    /* --- MENU CARD STYLING --- */
    div.menu-card {
        background-color: #0a0a0a;
        border: 1px solid #333333;
        border-left: 3px solid #FFB100;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 3px;
        position: relative;
    }
    div.menu-card h4 {
        color: #FFB100 !important;
        margin-top: 0px;
        margin-bottom: 10px;
        font-size: 16px !important;
        border-bottom: none;
    }
    div.menu-card p {
        margin-bottom: 0px;
        font-size: 13px !important;
    }
    
    .construction-tag {
        color: #FF4500 !important; 
        font-size: 11px !important;
        font-weight: bold;
        border: 1px dashed #FF4500;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline-block;
        margin-top: 8px;
        background-color: rgba(255, 69, 0, 0.1);
    }

    hr {
        border: 0;
        border-top: 1px solid #333333 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. LEFT-HAND INDEX (SIDEBAR) ---
with st.sidebar:
    st.markdown("### ⚡ TERMINAL INDEX")
    st.markdown("---")
    
    st.page_link("0-home.py", label="[01] Home: Switchboard")
    st.page_link("pages/1-market-heatmap.py", label="[02] Market Heatmap")
    st.page_link("pages/2-macro-bonds.py", label="[03] Macro Bond Watch")
    st.page_link("pages/3-inflation.py", label="[04] Inflation 🚧")
    st.page_link("pages/4-metals.py", label="[05] Metals 🚧")
    st.page_link("pages/5-energy.py", label="[06] Energy 🚧")
    st.page_link("pages/6-global-markets.py", label="[07] Global Markets 🚧")
    st.page_link("pages/7-sectors.py", label="[08] Sectors 🚧")
    st.page_link("pages/8-positioning.py", label="[09] Positioning 🚧")
    st.page_link("pages/9-options-flow.py", label="[10] Options Flow 🚧")
    st.page_link("pages/10-options-analyzer.py", label="[11] Options Analyzer 🚧")
    st.page_link("pages/11-liquidity.py", label="[12] Liquidity 🚧")
    
    st.markdown("---")
    st.markdown("<span style='color:#00FF00; font-size:12px;'>SYS.STAT: ONLINE</span>", unsafe_allow_html=True)


# --- 3. HEADER ---
st.title("SYS_NAV // COMMAND CENTER")
st.markdown("Main Switchboard: Select an active module from the sidebar index to navigate the terminal.")
st.markdown("---")

# --- 4. SWITCHBOARD GRID (CARDS) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### MACRO & RATES")
    st.markdown("""
        <div class="menu-card">
            <h4>[03] Macro Bond Watch</h4>
            <p>The cost of money. Tracking the Treasury curve and spread dynamics.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="menu-card">
            <h4>[04] Inflation</h4>
            <p>The rate of debasement. CPI, PPI, and breakeven tracking.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[12] Liquidity</h4>
            <p>The systemic money flow. Central bank balance sheets and repo markets.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### EQUITIES & FLOWS")
    st.markdown("""
        <div class="menu-card">
            <h4>[02] Market Heatmap</h4>
            <p>The daily vibe check. Breadth, depth, and immediate price action.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[07] Global Markets</h4>
            <p>The geographic capital flow. Tracking international indices and FX.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[08] Sectors</h4>
            <p>The internal market rotation. Relative strength across SPX components.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[09] Positioning</h4>
            <p>The structural "bodies buried." COT reports and dealer gamma exposure.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("### CMDTYS & DERIVATIVES")
    st.markdown("""
        <div class="menu-card">
            <h4>[05] Metals</h4>
            <p>The growth/fear barometer. Gold, Silver, Copper, and Platinum groups.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[06] Energy</h4>
            <p>The global input cost. Crude, Natural Gas, and refined products.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[10] Options Flow</h4>
            <p>The real-time "Whale" tape. Sweeps, blocks, and unusual activity.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card">
            <h4>[11] Options Analyzer</h4>
            <p>The Black-Scholes engine. Volatility surfaces and Greeks calculator.</p>
            <span class="construction-tag">🚧 OFFLINE // UNDER CONSTRUCTION</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("*SYSTEM STATUS: PARTIAL UPLINK. CORE MODULES ONLINE.*")