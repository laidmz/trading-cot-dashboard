import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="COT Institutional Terminal", layout="wide")

# --- PROFESSIONAL FINANCIAL UI CSS ---
st.markdown("""
    <style>
    /* منع الخلفية البيضاء الافتراضية */
    .stApp { background-color: #0b0e14; color: #e1e4e8; }
    
    /* ستايل البطاقات الاحترافية */
    .metric-card {
        background-color: #151921;
        border: 1px solid #232834;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* تلوين القيم المالية */
    .value-up { color: #00ff88; font-family: 'Courier New', monospace; font-size: 1.5rem; font-weight: bold; }
    .value-down { color: #ff3344; font-family: 'Courier New', monospace; font-size: 1.5rem; font-weight: bold; }
    .label { color: #8b949e; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* جدول مخصص */
    .styled-table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.9em; min-width: 400px; }
    .styled-table thead tr { background-color: #1f242d; color: #ffffff; text-align: left; }
    .styled-table th, .styled-table td { padding: 12px 15px; border-bottom: 1px solid #232834; }
    </style>
    """, unsafe_allow_html=True)

# --- MOCK DATA (As per your request) ---
COT_DATA = {
    "EUR": {"Score": 100, "Net": 144903, "D_Net": 50832, "Phase": "Accumulation", "Flow": "Bullish"},
    "CAD": {"Score": 100, "Net": -86640, "D_Net": 63774, "Phase": "Emerging", "Flow": "Bullish"},
    "AUD": {"Score": 100, "Net": -21895, "D_Net": 62281, "Phase": "Emerging", "Flow": "Bullish"},
    "GBP": {"Score": 94, "Net": -48498, "D_Net": 44723, "Phase": "Emerging", "Flow": "Bullish"},
    "JPY": {"Score": 43, "Net": -2942, "D_Net": -29459, "Phase": "Distribution", "Flow": "Bearish"},
    "CHF": {"Score": 42, "Net": -38907, "D_Net": -3547, "Phase": "Mixed", "Flow": "Neutral"}
}

# --- HEADER SECTION ---
def draw_header():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"# 🏛️ COT Institutional Terminal <span style='font-size:15px; color:#8b949e;'>v3.2 | Real-time Analysis</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='text-align:right; padding-top:20px;'>{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    st.markdown("---")

# --- KPI METRICS COMPONENT ---
def draw_kpis(asset):
    data = COT_DATA[asset]
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<div class='metric-card'><div class='label'>Current Net Position</div><div class='value-up' style='color:{('#00ff88' if data['Net']>0 else '#ff3344')}'>{data['Net']:,}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='label'>4-Week Change</div><div class='value-up'>{data['D_Net']:+,}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='label'>Institutional Score</div><div class='value-up' style='color:#4e73df'>{data['Score']}/100</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><div class='label'>Phase</div><div class='value-up' style='color:#e1e4e8; font-size:1.2rem;'>{data['Phase']}</div></div>", unsafe_allow_html=True)

# --- MAIN APP LAYOUT ---
def main():
    draw_header()
    
    # Sidebar selection
    st.sidebar.title("🎛️ Control Panel")
    selected_asset = st.sidebar.selectbox("Market Focus", list(COT_DATA.keys()))
    
    # KPIs section
    draw_kpis(selected_asset)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Dashboard Area
    col_left, col_right = st.columns([2, 1.2])
    
    with col_left:
        st.subheader(f"📈 {selected_asset} Sentiment Roadmap")
        # الرسم البياني التفاعلي
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3, 4], y=[100000, 115000, 138000, 144903], 
                                 name="Net", line=dict(color='#00ff88', width=4), fill='tozeroy'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          height=400, margin=dict(l=0, r=0, t=20, b=0), font_color="#8b949e",
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#232834'))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🏆 Currency Strength Matrix")
        # تحويل البيانات إلى جدول احترافي
        s_df = pd.DataFrame.from_dict(COT_DATA, orient='index').reset_index()
        s_df.columns = ['Asset', 'Score', 'Net', 'Δ4W', 'Phase', 'Flow']
        
        # التنسيق البصري للجدول
        def style_score(val):
            color = '#00ff88' if val > 70 else '#ff3344' if val < 50 else '#ffcc00'
            return f'color: {color}; font-weight: bold'
        
        st.dataframe(s_df.sort_values('Score', ascending=False).style.applymap(style_score, subset=['Score']), 
                     use_container_width=True, hide_index=True)

    st.divider()
    
    # فرص التداول (Opportunities)
    st.subheader("🎯 Institutional Opportunities (High Probabilities)")
    op_col1, op_col2, op_col3 = st.columns(3)
    
    with op_col1:
        st.success("**Strong Buy (Bullish Accumulation)**")
        st.markdown("• **EUR/JPY** (Score Diff: +57)\n\n• **AUD/CHF** (Score Diff: +58)")
    with col_right: # Use this for space or additional info
        pass
    with op_col2:
        st.error("**Strong Sell (Bearish Distribution)**")
        st.markdown("• **JPY/EUR** (Score Diff: -57)\n\n• **CHF/AUD** (Score Diff: -58)")
    with op_col3:
        st.info("**Watchlist (Neutral/Mixed)**")
        st.markdown("• **NZD/USD** (Score: 53)\n\n• **GBP/CAD** (Score: 94/100 Mixed)")

if __name__ == "__main__":
    main()
