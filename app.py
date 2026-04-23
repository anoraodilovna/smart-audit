import streamlit as st
import pandas as pd
import plotly.express as px
import io
import asyncio
from telegram import Bot

# --- SOZLAMALAR ---
# Sizning ma'lumotlaringiz joylandi
TELEGRAM_BOT_TOKEN = "8282946366:AAFnXnwHppJZIngvxFIQvNLjYSWpIG7O8OI"
TELEGRAM_CHAT_ID = "7887284457"

# --- SAHIFA DIZAYNI ---
st.set_page_config(page_title="AI Financial Auditor Pro", page_icon="💎", layout="wide")

# Premium Dark Glass UI
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
    .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(15px); 
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: bold; font-size: 1.8rem; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #007bff, #00d4ff);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 15px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 20px rgba(0,212,255,0.4); }
    </style>
""", unsafe_allow_html=True)

# --- AQLLI MA'LUMOT QIDIRISH ---
def get_data_smart(df, code):
    """Exceldan kodni topib, uning yonidagi birinchi raqamni aniqlaydi"""
    for col in df.columns:
        for row_idx, val in enumerate(df[col]):
            if str(val).strip() == str(code):
                # Kod topilgach, o'ngdagi 5 ta ustunni tekshiradi
                for offset in range(1, 6):
                    if col + offset < len(df.columns):
                        check_val = df.iloc[row_idx, col + offset]
                        try:
                            num = float(str(check_val).replace(',', '').replace(' ', '').strip())
                            if not pd.isna(num): return num
                        except: continue
    return 0

async def send_report_to_telegram(text, excel_data):
    """Natijalarni Telegram bot orqali yuborish"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        # Summary yuborish
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown')
        # Excel faylni yuborish
        await bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=excel_data, filename="Audit_Hisoboti.xlsx")
        return True
    except Exception as e:
        return f"Xato: {e}"

# --- ASOSIY QISM ---
st.title("🛡️ AI Financial Auditor Intelligence")
st.write("Professional moliyaviy tahlil va avtomatlashtirilgan hisobot tizimi")
st.markdown("---")

uploaded_file = st.file_uploader("Moliyaviy hisobotni (Excel 1-2 shakl) yuklang", type="xlsx")

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

    # Dashboard ko'rsatkichlari
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Umumiy Tushum", f"{moliya['Tushum']:,.0f}")
    c2.metric("💵 Sof Foyda", f"{moliya['Foyda']:,.0f}")
    
    likv = moliya['Joriy Aktiv'] / moliya['Majburiyat'] if moliya['Majburiyat'] > 0 else 0
    c3.metric("💧 Likvidlik", f"{likv:.2f}")
    
    roe = (moliya['Foyda'] / moliya['Sarmoya']) * 100 if moliya['Sarmoya'] > 0 else 0
    c4.metric("📈 ROE (Rentabellik)", f"{roe:.1f}%")

    # Grafiklar qismi (Faqat raqami borlarini ko'rsatadi)
    plot_data = {k: v for k, v in moliya.items() if v > 0}
    
    st.subheader("📊 Vizual Dashboard")
    col_left, col_right = st.columns(2)
    
    if plot_data:
        fig_bar = px.bar(x=list(plot_data.keys()), y=list(plot_data.values()), 
                         title="Asosiy Moliyaviy Ko'rsatkichlar",
                         color=list(plot_data.keys()), template="plotly_dark")
        col_left.plotly_chart(fig_bar, use_container_width=True)
        
        fig_pie = px.pie(names=list(plot_data.keys()), values=list(plot_data.values()), 
                         title="Mablag'lar nisbati", hole=.4, template="plotly_dark")
        col_right.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Excel faylda tahlil uchun yetarli raqamlar topilmadi (010, 190, 480 kodlarini tekshiring).")

    # --- TELEGRAM INTEGRATSIYA ---
    st.markdown("---")
    if st.button("🚀 Hisobotni Telegramga va Excelga eksport qilish"):
        # Telegram xabari
        msg = f"""
🏛 *YANGI AUDIT HISOBOTI TAYYOR*

💰 *Sof Foyda:* {moliya['Foyda']:,.0f} so'm
📈 *ROE (Rentabellik):* {roe:.1f}%
💧 *Likvidlik koeffitsienti:* {likv:.2f}
📉 *Jami Aktivlar:* {moliya['Aktivlar']:,.0f}

🤖 _Ushbu hisobot AI Auditor platformasi orqali generatsiya qilindi._
        """
        
        # Excel faylni xotirada yaratish
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([moliya]).to_excel(writer, index=False, sheet_name='Audit_Results')
        output.seek(0)
        
        # Bot orqali yuborish
        res = asyncio.run(send_report_to_telegram(msg, output))
        
        if res == True:
            st.success("✅ Muvaffaqiyatli! Hisobot Telegramingizga yuborildi.")
            st.balloons()
        else:
            st.error(f"❌ Xatolik yuz berdi: {res}")
