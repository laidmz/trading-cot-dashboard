import streamlit as st
import pandas as pd
from cot_reports import cot # مكتبة جلب البيانات الحالية
import datetime

# إعداد واجهة التطبيق
st.set_page_config(page_title="EUR FX COT Live Analyzer", layout="wide")
st.title("📊 محلل بيانات COT الحي - اليورو (EUR FX)")

# دالة لتنسيق الألوان
def color_value(val):
    color = "green" if val >= 0 else "red"
    return f"<span style='color:{color}; font-weight:bold;'>{val:+,}</span>"

@st.cache_data(ttl=86400) # التخزين لمدة يوم (التقرير يصدر أسبوعياً)
def fetch_live_data():
    try:
        # جلب بيانات العام الحالي (2026) من بورصة شيكاغو (CME)
        df = cot.get_cot(year=2026, cot_report_type='legacy_fut')
        
        # تصفية البيانات لعملة اليورو فقط
        # الاسم الرسمي في التقرير هو "EURO CURRENCY - CHICAGO MERCANTILE EXCHANGE"
        eur_df = df[df['Market_and_Exchange_Names'].str.contains("EURO CURRENCY", na=False)].copy()
        
        # تحويل التاريخ وتنسيق الأعمدة الهامة
        eur_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(eur_df['Report_Date_as_MM_DD_YYYY'])
        eur_df = eur_df.sort_values('Report_Date_as_MM_DD_YYYY', ascending=False)
        
        # اختيار الأعمدة المطلوبة (Non-Commercial Long/Short)
        final_df = eur_df[['Report_Date_as_MM_DD_YYYY', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All']].copy()
        final_df.columns = ['Date', 'Long', 'Short']
        return final_df
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات الحية: {e}")
        return None

# تنفيذ الجلب
with st.spinner('جاري سحب أحدث البيانات من موقع CFTC...'):
    df = fetch_live_data()

if df is not None and not df.empty:
    # 1. الحسابات الحالية (أحدث أسبوع)
    latest = df.iloc[0]
    net_now = latest['Long'] - latest['Short']
    
    # 2. حساب التغير لـ 6 أسابيع (إذا توفرت البيانات)
    if len(df) >= 7:
        target_week = df.iloc[6] # الأسبوع السابع للمقارنة بالستة الماضية
        long_diff = latest['Long'] - target_week['Long']
        short_diff = latest['Short'] - target_week['Short']
        prev_date = target_week['Date'].date()
    else:
        long_diff = short_diff = 0
        prev_date = "غير متوفر"

    # عرض النتائج في بطاقات علوية
    st.subheader(f"📅 تقرير الأسبوع الحالي: {latest['Date'].date()}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("صافي المراكز (Net)", f"{net_now:,}", delta_color="normal")
        st.markdown(f"النتيجة: {color_value(net_now)}", unsafe_allow_html=True)
        
    with c2:
        st.metric("تغير الشراء (6 أسابيع)", f"{long_diff:,}")
        st.markdown(f"الفرق: {color_value(long_diff)}", unsafe_allow_html=True)

    with c3:
        st.metric("تغير البيع (6 أسابيع)", f"{short_diff:,}")
        st.markdown(f"الفرق: {color_value(short_diff)}", unsafe_allow_html=True)

    st.divider()

    # 3. جدول المقارنة التاريخية
    st.subheader("📜 سجل البيانات لآخر 10 أسابيع")
    
    # إضافة عمود الصافي للجدول
    df['Net'] = df['Long'] - df['Short']
    
    # تنسيق الجدول للعرض بالألوان
    display_df = df.head(10).copy()
    st.dataframe(display_df.style.applymap(lambda x: 'color: green' if str(x).startswith('+') or (isinstance(x, (int, float)) and x > 0) else 'color: red', subset=['Net']))

    # 4. خلاصة التحليل
    st.subheader("💡 الملخص الفني")
    if net_now > 0 and long_diff > 0:
        st.success("النتيجة النهائية: صعودي (Bullish) - الحيتان يزيدون مراكز الشراء.")
    elif net_now < 0 and short_diff > 0:
        st.error("النتيجة النهائية: هبوطي (Bearish) - الحيتان يزيدون مراكز البيع.")
    else:
        st.warning("النتيجة النهائية: تذبذب أو جني أرباح - مراكز غير منتظمة.")

else:
    st.info("لم يتم العثور على بيانات للعام الحالي بعد، تأكد من تحديث السنة في الكود `year=2026` عند صدور أول تقرير.")
