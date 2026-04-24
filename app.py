import streamlit as st
import pandas as pd
import plotly.express as px
import io
import asyncio
from telegram import Bot
from groq import Groq

# --- SOZLAMALAR ---
TELEGRAM_BOT_TOKEN = "8282946366:AAFnXnwHppJZIngvxFIQvNLjYSWpIG7O8OI"
TELEGRAM_CHAT_ID = "-1003964666189"
# BU YERGA GROQ KALITINI QO'YING
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# --- SAHIFA DIZAYNI ---
st.set_page_config(page_title="AI Financial Auditor Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0f172a; color: #f8fafc; }
    .ai-box {
        background: rgba(0, 255, 150, 0.05);
        border-left: 5px solid #00ff96;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKSIYALAR (HAMMASI SHU YERDA BO'LISHI SHART) ---
def get_data_smart(df, code):
    """Exceldan kodni topib, uning raqamini aniqlaydi"""
    for col in df.columns:
        for row_idx, val in enumerate(df[col]):
            if str(val).strip() == str(code):
                for offset in range(1, 6):
                    if col + offset < len(df.columns):
                        check_val = df.iloc[row_idx, col + offset]
                        try:
                            num = float(str(check_val).replace(',', '').replace(' ', '').strip())
                            if not pd.isna(num): return num
                        except: continue
    return 0

def get_ai_analysis(data):
    """Groq AI orqali tahlil qilish (To'g'rilangan variant)"""
    prompt = f"""
    Siz professional auditorsiz. Kompaniya ma'lumotlari:
    Tushum: {data['Tushum']} so'm, Foyda: {data['Foyda']} so'm, 
    Aktivlar: {data['Aktivlar']} so'm, Likvidlik: {data['Likvidlik']:.2f}, ROE: {data['ROE']:.1f}%.
    Ushbu raqamlarni tahlil qiling va o'zbek tilida qisqa professional xulosa hamda 3 ta aniq tavsiya yozing.
    """
    try:
        # Llama 3 modelidan foydalanamiz
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        # Natijani to'g'ri olish (error bo'lsa list qaytarmaydi)
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq AI bilan bog'lanishda xatolik: {str(e)}"


# --- ASOSIY QISM ---
st.title("🛡️ Sun'iy intellekt moliyaviy auditori")

uploaded_file = st.file_uploader("Excel yuklash", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)
    
    # Ma'lumotlarni yig'ish
    moliya = {
        'Tushum': get_data_smart(df, '010'),
        'Foyda': get_data_smart(df, '190'),
        'Aktivlar': get_data_smart(df, '480'),
        'Joriy Aktiv': get_data_smart(df, '290'),
        'Majburiyat': get_data_smart(df, '690'),
        'Sarmoya': get_data_smart(df, '490')
    }
    
    # Hisob-kitoblar
    moliya['Likvidlik'] = moliya['Joriy Aktiv'] / moliya['Majburiyat'] if moliya['Majburiyat'] > 0 else 0
    moliya['ROE'] = (moliya['Foyda'] / moliya['Sarmoya']) * 100 if moliya['Sarmoya'] > 0 else 0

    # AI Tahlil
    st.subheader("🤖 AI Auditor Xulosasi")
    with st.spinner("AI tahlil qilmoqda..."):
        ai_insight = get_ai_analysis(moliya)
        st.markdown(f'<div class="ai-box">{ai_insight}</div>', unsafe_allow_html=True)

    # Dashboard
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Tushum", f"{moliya['Tushum']:,.0f}")
    c2.metric("💵 Foyda", f"{moliya['Foyda']:,.0f}")
    c3.metric("💧 Likvidlik", f"{moliya['Likvidlik']:.2f}")
    c4.metric("📈 ROE", f"{moliya['ROE']:.1f}%")

    if st.button("🚀 Telegramga yuborish"):
        msg = f"🏛 *AI AUDIT HISOBOTI*\n\n{ai_insight}"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([moliya]).to_excel(writer, index=False)
        output.seek(0)
        
        if asyncio.run(send_report_to_telegram(msg, output)):
            st.success("✅ Telegramga yuborildi!")
