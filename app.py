import streamlit as st
import pandas as pd
import requests
import io

# إعداد واجهة التطبيق
st.set_page_config(page_title="COT Analyzer - EUR FX", layout="wide")
st.title("📊 محرر تقرير COT لعملة اليورو (EUR FX)")

def get_color(value):
    """دالة لتحديد اللون بناءً على القيمة"""
    return "green" if value >= 0 else "red"

def format_delta(val):
    """تنسيق الرقم مع إشارة + أو -"""
    return f"{val:+,.0f}"

@st.cache_data(ttl=3600)  # تخزين البيانات لمدة ساعة لتسريع التطبيق
def load_cot_data():
    # رابط بيانات COT التاريخية لعام 2026 (أو العام الحالي)
    url = "https://www.cftc.gov/dea/newcot/deahist2026.zip" # يمكن تغيير السنة حسب الحاجة
    # ملاحظة: للتبسيط سنستخدم دالة تجلب البيانات الحالية من ملف مضغوط أو API
    # هنا سنقوم بمحاكاة جلب البيانات ومعالجتها لليورو
    try:
        # ملاحظة: جلب البيانات مباشرة من CFTC يتطلب معالجة لملف ZIP
        # سنفترض هنا معالجة البيانات النصية المباشرة لليورو
        # في التطبيق الفعلي يفضل استخدام مكتبة مثل cot_reports أو جلب CSV جاهز
        
        # بيانات تجريبية لمحاكاة الوظائف المطلوبة (EUR FX - Chicago Mercantile Exchange)
        data = {
            'Date': pd.date_range(start='2026-02-01', periods=10, freq='W-FRI'),
            'Long': [150000, 155000, 148000, 160000, 165000, 170000, 172000, 168000, 175000, 180000],
            'Short': [100000, 98000, 105000, 102000, 95000, 90000, 88000, 92000, 85000, 80000]
        }
        df = pd.DataFrame(data).sort_values(by='Date', ascending=False)
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

df = load_cot_data()

if df is not None:
    # 1. حساب الصافي الحالي
    current = df.iloc[0]
    net_position = current['Long'] - current['Short']
    
    # 2. حساب فرق الـ Long لمدة 6 أسابيع
    long_6w_ago = df.iloc[5]['Long'] if len(df) >= 6 else df.iloc[-1]['Long']
    long_diff = current['Long'] - long_6w_ago
    
    # 3. حساب فرق الـ Short لمدة 6 أسابيع
    short_6w_ago = df.iloc[5]['Short'] if len(df) >= 6 else df.iloc[-1]['Short']
    short_diff = current['Short'] - short_6w_ago

    # عرض النتائج في بطاقات (Metrics)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### صافي المراكز (Net)")
        color = get_color(net_position)
        st.markdown(f"<h2 style='color:{color};'>{format_delta(net_position)}</h2>", unsafe_allow_html=True)
        st.caption("Long - Short (Current)")

    with col2:
        st.markdown(f"### تغير الشراء (6 أسابيع)")
        color = get_color(long_diff)
        st.markdown(f"<h2 style='color:{color};'>{format_delta(long_diff)}</h2>", unsafe_allow_html=True)
        st.caption(f"مقارنة بـ {df.iloc[5]['Date'].date()}")

    with col3:
        st.markdown(f"### تغير البيع (6 أسابيع)")
        color = get_color(short_diff)
        st.markdown(f"<h2 style='color:{color};'>{format_delta(short_diff)}</h2>", unsafe_allow_html=True)
        st.caption(f"مقارنة بـ {df.iloc[5]['Date'].date()}")

    st.divider()

    # 4. المقارنة النهائية والتحليل
    st.subheader("🏁 المقارنة النهائية للاتجاه")
    
    sentiment = "صعودي (Bullish)" if net_position > 0 and long_diff > 0 else "هبوطي (Bearish)"
    sentiment_color = "green" if "صعودي" in sentiment else "red"
    
    st.markdown(f"""
    <div style="padding:20px; border-radius:10px; border: 2px solid {sentiment_color}; text-align:center;">
        <h1 style="color:{sentiment_color};">{sentiment}</h1>
        <p>بناءً على تزايد عقود الشراء وصافي المراكز الإيجابي</p>
    </div>
    """, unsafe_allow_html=True)

    # عرض جدول البيانات التاريخية
    with st.expander("عرض البيانات التاريخية"):
        st.table(df)

else:
    st.warning("يرجى التأكد من اتصال الإنترنت أو تحديث روابط البيانات.")
