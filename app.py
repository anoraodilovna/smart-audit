import streamlit as st
import pandas as pd
import plotly.express as px
import io, asyncio, json, re
from telegram import Bot
from groq import Groq

# --- SOZLAMALAR ---
# GitHub-ga yuklashda bularni st.secrets ga o'tkazish tavsiya etiladi
TELEGRAM_BOT_TOKEN = "8282946366:AAFnXnwHppJZIngvxFIQvNLjYSWpIG7O8OI"
TELEGRAM_CHAT_ID = "-1003964666189"
GROQ_API_KEY = "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" 

client = Groq(api_key=GROQ_API_KEY)

# --- SAHIFA SOZLAMALARI ---
st.set_page_config(page_title="AI Auditor Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0a0f1a; color: #e2e8f0; }
    div[data-testid="stMetric"] {
        background: #161e2e;
        border: 2px solid #1e293b;
        border-radius: 20px;
        padding: 25px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.8rem !important; }
    .ai-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-left: 6px solid #38bdf8;
        padding: 25px; border-radius: 12px; margin: 20px 0; font-size: 1.1rem; line-height: 1.7;
    }
    .stButton>button {
        background: linear-gradient(90deg, #0284c7, #7c3aed);
        color: white; border-radius: 12px; width: 100%; padding: 15px; font-weight: bold; border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- AI TAHLIL FUNKSIYASI (XATOLIKDAN HIMOYaLANGAN) ---
def get_ai_comprehensive_analysis(full_df):
    excel_sample = full_df.fillna("").astype(str).values.tolist()
    context = "\n".join([" | ".join(row) for row in excel_sample[:130]])

    prompt = f"""
    Siz professional auditorsiz. Quyidagi jadvalni tahlil qiling:
    {context}

    Vazifa:
    1. Kompaniya holati haqida o'zbekcha strategik tahlil yozing.
    2. Oxirida FAQAT mana bu formatda raqamlarni bering:
    DATA: {{"tushum": 100, "foyda": 50, "aktiv": 500, "majburiyat": 200}}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1 
        )
        res = completion.choices[0].message.content
        
        # Tahlil va JSON ma'lumotni ajratish
        if "DATA:" in res:
            parts = res.split("DATA:")
            analysis_text = parts[0].strip()
            json_part = parts[1].strip()
            
            # JSON-ni tozalash (extra data xatosini oldini olish uchun)
            try:
                # Faqat { } qavslar orasidagi qismni olamiz
                json_match = re.search(r'\{.*\}', json_part, re.DOTALL)
                if json_match:
                    data_values = json.loads(json_match.group())
                else:
                    data_values = {"tushum": 0, "foyda": 0, "aktiv": 0, "majburiyat": 0}
            except:
                data_values = {"tushum": 0, "foyda": 0, "aktiv": 0, "majburiyat": 0}
        else:
            analysis_text = res
            data_values = {"tushum": 0, "foyda": 0, "aktiv": 0, "majburiyat": 0}
            
        return analysis_text, data_values
    except Exception as e:
        return f"⚠️ Tahlil jarayonida kutilmagan holat: {str(e)}", {"tushum": 0, "foyda": 0, "aktiv": 0, "majburiyat": 0}

async def send_to_tg(text, excel):
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown')
        await bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=excel, filename="Audit_AI.xlsx")
        return True
    except: return False

# --- ASOSIY QISM ---
st.title("🛡️ Moliyaviy auditor razvedkasi sun'iy intellekt")
uploaded_file = st.sidebar.file_uploader("Excelni yuklang", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)
    
    with st.spinner("🚀 AI tahlil tayyorlamoqda..."):
        tahlil, raqamlar = get_ai_comprehensive_analysis(df)
    
    st.markdown("### 📊 Asosiy Balans Ko'rsatkichlari")
    c1, c2, c3, c4 = st.columns(4)
    
    def safe_float(val):
        try: return float(val)
        except: return 0.0

    v_tushum = safe_float(raqamlar.get('tushum', 0))
    v_foyda = safe_float(raqamlar.get('foyda', 0))
    v_aktiv = safe_float(raqamlar.get('aktiv', 0))
    v_majburiyat = safe_float(raqamlar.get('majburiyat', 0))

    c1.metric("💰 Umumiy Tushum", f"{v_tushum:,.0f} s.")
    c2.metric("💵 Sof Foyda", f"{v_foyda:,.0f} s.")
    
    likv = v_aktiv / v_majburiyat if v_majburiyat > 0 else 0
    c3.metric("💧 Likvidlik", f"{likv:.2f}")
    
    roe = (v_foyda / v_aktiv) * 100 if v_aktiv > 0 else 0
    c4.metric("📈 ROE", f"{roe:.1f}%")

    st.markdown("---")
    st.subheader("🤖 AI Auditorning Strategik Xulosasi")
    st.markdown(f'<div class="ai-box">{tahlil}</div>', unsafe_allow_html=True)

    # Grafiklar
    col_l, col_r = st.columns(2)
    with col_l:
        fig1 = px.bar(x=['Tushum', 'Foyda', 'Majburiyat'], 
                      y=[v_tushum, v_foyda, v_majburiyat],
                      color=['Tushum', 'Foyda', 'Majburiyat'], 
                      template="plotly_dark", title="Moliyaviy Balans")
        st.plotly_chart(fig1, use_container_width=True)
    with col_r:
        fig2 = px.pie(names=['Aktivlar', 'Majburiyatlar'], 
                      values=[v_aktiv, v_majburiyat], 
                      hole=0.4, template="plotly_dark", title="Aktiv/Majburiyat nisbati")
        st.plotly_chart(fig2, use_container_width=True)

    if st.button("🚀 Hisobotni Telegramga yuborish"):
        msg = f"🏛 *AI AUDIT HISOBOTI*\n\n{tahlil}"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([raqamlar]).to_excel(writer, index=False)
        output.seek(0)
        if asyncio.run(send_to_tg(msg, output)):
            st.success("✅ Telegramga yuborildi!")
            st.balloons()
