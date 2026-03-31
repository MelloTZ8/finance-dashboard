import streamlit as st
from theme import inject_custom_css  # <--- ADD THIS LINE

# --- 1. PAGE CONFIG & BLOOMBERG THEME ---
st.set_page_config(page_title="TERMINAL: SWITCHBOARD", layout="wide", initial_sidebar_state="expanded")

# Inject the master CSS
inject_custom_css()  # <--- ADD THIS LINE

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