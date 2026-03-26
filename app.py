import streamlit as st
import pandas as pd
import requests
import io

# إعداد الصفحة
st.set_page_config(page_title="EUR FX COT Tracker", layout="wide")

st.title("🇪🇺 محلل التزام المتداولين (COT) لليورو")

@st.cache_data(ttl=3600)
def get_live_cot_data():
    # رابط البيانات المباشرة لعام 2026 من موقع CFTC (صيغة مضغوطة أو نصية)
    # سنستخدم الرابط الذي يحتوي على بيانات السنة الحالية كاملة
    url = "https://www.cftc.gov/dea/newcot/deahist2026.zip"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            from zipfile import ZipFile
            with ZipFile(io.BytesIO(response.content)) as z:
                # فتح ملف الـ CSV داخل الـ ZIP (عادة يكون ملف واحد)
                filename = z.namelist()[0]
                with z.open(filename) as f:
                    df = pd.read_csv(f)
            
            # تصفية البيانات لليورو فقط
            # الاسم الرسمي في التقارير: "EURO CURRENCY - CHICAGO MERCANTILE EXCHANGE"
            eur_df = df[df['Market_and_Exchange_Names'].str.contains("EURO CURRENCY", na=False)].copy()
            
            # ترتيب البيانات حسب التاريخ (الأحدث أولاً)
            eur_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(eur_df['Report_Date_as_MM_DD_YYYY'])
            eur_df = eur_df.sort_values('Report_Date_as_MM_DD_YYYY', ascending=False)
            
            return eur_df
        else:
            return None
    except Exception as e:
        st.error(f"خطأ في الاتصال بموقع CFTC: {e}")
        return None

# جلب البيانات
df = get_live_cot_data()

if df is not None and not df.empty:
    # استخراج الأعمدة المطلوبة
    # NonComm_Positions_Long_All = الشراء لغير التجاريين
    # NonComm_Positions_Short_All = البيع لغير التجاريين
    
    latest = df.iloc[0]
    
    # 1. حساب الصافي الحالي
    net_now = latest['NonComm_Positions_Long_All'] - latest['NonComm_Positions_Short_All']
    net_color = "green" if net_now >= 0 else "red"
    
    # حساب فروقات 6 أسابيع
    if len(df) >= 7:
        past_6w = df.iloc[6]
        long_diff = latest['NonComm_Positions_Long_All'] - past_6w['NonComm_Positions_Long_All']
        short_diff = latest['NonComm_Positions_Short_All'] - past_6w['NonComm_Positions_Short_All']
    else:
        long_diff = short_diff = 0

    # العرض المرئي (Metrics)
    st.info(f"آخر تحديث للتقرير: {latest['Report_Date_as_MM_DD_YYYY'].date()}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### صافي المراكز (Net)")
        st.markdown(f"<h2 style='color:{net_color};'>{net_now:+,}</h2>", unsafe_allow_html=True)
        st.caption("Long - Short")

    with col2:
        st.markdown(f"### تغير الشراء (6 أسابيع)")
        l_color = "green" if long_diff >= 0 else "red"
        st.markdown(f"<h2 style='color:{l_color};'>{long_diff:+,}</h2>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"### تغير البيع (6 أسابيع)")
        s_color = "green" if short_diff >= 0 else "red"
        st.markdown(f"<h2 style='color:{s_color};'>{short_diff:+,}</h2>", unsafe_allow_html=True)

    st.divider()

    # المقارنة النهائية
    st.subheader("🏁 الخلاصة الفنية")
    final_net = long_diff - short_diff
    final_color = "green" if final_net >= 0 else "red"
    final_text = "قوة شرائية متزايدة" if final_net >= 0 else "قوة بيعية متزايدة"
    
    st.markdown(f"""
    <div style="padding:20px; border-radius:10px; background-color:#f0f2f6; border-left: 10px solid {final_color};">
        <h3 style="color:{final_color}; margin:0;">{final_text}</h3>
        <p style="color:black;">صافي التغير الإجمالي: {final_net:+,}</p>
    </div>
    """, unsafe_allow_html=True)

    # جدول تفصيلي
    with st.expander("شاهد سجل البيانات التاريخية"):
        history = df[['Report_Date_as_MM_DD_YYYY', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All']].copy()
        history.columns = ['التاريخ', 'الشراء (Long)', 'البيع (Short)']
        st.dataframe(history.head(10))

else:
    st.warning("⚠️ لا توجد بيانات متاحة حالياً لعام 2026. قد يكون التقرير لم يصدر بعد أو هناك صيانة في موقع CFTC.")
