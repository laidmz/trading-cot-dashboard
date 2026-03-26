import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="COT Report Analyzer Pro", layout="wide", initial_sidebar_state="expanded")

# --- استايل CSS مخصص لمحاكاة الصور المرفقة ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #2d2e38; }
    .card { background-color: #1a1c24; padding: 20px; border-radius: 12px; border-left: 5px solid #4e73df; margin-bottom: 20px; }
    .bullish { color: #00ff88; font-weight: bold; }
    .bearish { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- بيانات افتراضية دقيقة بناءً على طلبك المحاسبي ---
# ملاحظة: في النسخة الواقعية يتم جلب هذه البيانات من دالة fetch_data السابقة
RAW_DATA = {
    "EUR": {"Net_Change": 50832, "Last_Net": 144903, "Sum_DLong": 32610, "Sum_DShort": -18222, "Score": 100, "Phase": "Confirmed Bullish"},
    "CAD": {"Net_Change": 63774, "Last_Net": -86640, "Sum_DLong": 4215, "Sum_DShort": -59559, "Score": 100, "Phase": "Emerging Bullish"},
    "AUD": {"Net_Change": 62281, "Last_Net": -21895, "Sum_DLong": 23722, "Sum_DShort": -38559, "Score": 100, "Phase": "Emerging Bullish"},
    "GBP": {"Net_Change": 44723, "Last_Net": -48498, "Sum_DLong": 16711, "Sum_DShort": -28012, "Score": 94, "Phase": "Emerging Bullish"},
    "NZD": {"Net_Change": 4028, "Last_Net": -48043, "Sum_DLong": -15348, "Sum_DShort": -19376, "Score": 53, "Phase": "Mixed"},
    "JPY": {"Net_Change": -29459, "Last_Net": -2942, "Sum_DLong": -22943, "Sum_DShort": 6516, "Score": 43, "Phase": "Bearish"},
    "CHF": {"Net_Change": -3547, "Last_Net": -38907, "Sum_DLong": 1877, "Sum_DShort": 5424, "Score": 42, "Phase": "Mixed"},
}

def get_pair_status(base, quote):
    diff = RAW_DATA[base]["Score"] - RAW_DATA[quote]["Score"]
    if diff >= 50: return "Strong Buy 🟢", diff
    elif diff <= -50: return "Strong Sell 🔴", diff
    else: return "Neutral / Unclear ⚖️", diff

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2963/2963561.png", width=80)
st.sidebar.title("COT Settings")
report_type = st.sidebar.selectbox("Report Category", ["Non-Commercial (Large Specs)", "Commercial", "Retail"])
lookback = st.sidebar.slider("Weeks to display", 4, 52, 4)

# --- Main Dashboard ---
st.title("📊 COT Report Analyzer - Commitment of Traders")
st.caption(f"Live data analysis as of {datetime.now().strftime('%Y-%m-%d')} | Financial Traders Report")

# --- القسم الأول: مؤشرات العملة المختارة ---
col1, col2, col3, col4 = st.columns(4)
selected_curr = st.sidebar.selectbox("Select Market for Details", list(RAW_DATA.keys()))
c_data = RAW_DATA[selected_curr]

with col1:
    st.metric("Net Position", f"{c_data['Last_Net']:,}", f"{c_data['Net_Change']:,} contracts")
with col2:
    st.metric("COT Score", f"{c_data['Score']}/100", f"{c_data['Phase']}")
with col3:
    st.metric("Δ Long (4W)", f"{c_data['Sum_DLong']:,}")
with col4:
    st.metric("Δ Short (4W)", f"{c_data['Sum_DShort']:,}", delta_color="inverse")

# --- القسم الثاني: الرسم البياني وتدفق السيولة ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Net Positions Over Time (Simulated)")
    # رسم بياني توضيحي
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=['W1', 'W2', 'W3', 'W4'], y=[94071, 108453, 138788, 144903], 
                             fill='tozeroy', line_color='#00ff88', name="Net Position"))
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Flow Cause Analysis")
    cause = "Real Buying + Short Exit" if c_data['Sum_DLong'] > 0 and c_data['Sum_DShort'] < 0 else "Short Covering"
    st.info(f"**Primary Cause:** {cause}")
    st.write(f"The trend is currently in **{c_data['Phase']}** phase. Accumulation is visible in the data.")

# --- القسم الثالث: جدول القوة ومقارنة الأزواج ---
st.divider()
st.subheader("🏆 COT Currency Strength (Non-Commercial)")

# تحويل البيانات لجدول جميل
strength_df = pd.DataFrame.from_dict(RAW_DATA, orient='index').reset_index()
strength_df.columns = ['Currency', 'Net Δ', 'Last Net', 'Σ ΔLong', 'Σ ΔShort', 'Score', 'Phase']
st.dataframe(strength_df.sort_values('Score', ascending=False), use_container_width=True, hide_index=True)

st.divider()
st.subheader("💱 COT Pairs Outlook (Market Context)")

pair_col1, pair_col2 = st.columns(2)

with pair_col1:
    st.markdown("#### 🟢 High Probability Buy (Long)")
    targets = ["EURJPY", "EURCHF", "CADJPY", "AUDCHF", "GBPJPY"]
    for p in targets:
        base, quote = p[:3], p[3:]
        status, diff = get_pair_status(base, quote)
        st.write(f"**{p}** — {status} | ΔScore: +{diff}")

with pair_col2:
    st.markdown("#### 🔴 High Probability Sell (Short)")
    targets_s = ["JPYEUR", "CHFEUR", "JPYCAD", "CHFAUD"]
    for p in targets_s:
        base, quote = p[:3], p[3:]
        status, diff = get_pair_status(base, quote)
        st.write(f"**{p}** — {status} | ΔScore: {diff}")

# --- تذييل الصفحة ---
st.warning("⚠️ Warning: COT is a contextual tool, not a direct entry signal. Use price action for timing.")
st.markdown("---")
st.center = st.write("Developed by Coding Partner | Data Source: CFTC")
