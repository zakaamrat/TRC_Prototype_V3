import streamlit as st
import random
import os
import requests
import base64
from datetime import datetime
from difflib import SequenceMatcher
import speech_recognition as sr

# --------------------------
# CONFIG & SECRETS (SECURE)
# --------------------------
st.set_page_config(page_title="Oman AI Learning", layout="centered")

# We now pull these from the hidden "Secrets" vault
SHEET_URL = st.secrets["SHEET_URL"]
AUDIO_URL = st.secrets["AUDIO_URL"]
TEACHER_PASSWORD = st.secrets["TEACHER_PASSWORD"]
EXCEL_LINK = st.secrets["EXCEL_LINK"]
DRIVE_LINK = st.secrets["DRIVE_LINK"]

# --------------------------
# SESSION STATE INIT
# --------------------------
for key in ["consent", "captcha_ok", "saved", "session_count"]:
    if key not in st.session_state:
        st.session_state[key] = False if key != "session_count" else 0

# --------------------------
# HEADER / FOOTER STYLE
# --------------------------
col1, col2 = st.columns([1, 3])

with col1:
    st.image("omani_avatar.png", width=150)
with col2:
    st.markdown("""
        <div style='text-align: left; padding-top: 20px;'>
            <h3 style='margin-bottom: 0;'> Prototype App for evaluation of Omani school level with AI English Learning System</h3>
            <p style='font-size:14px; color: #555; margin-top: 5px;'>
                <strong>Phonetic Approximation Capture</strong><br>
                Building a pronunciation error corpus for Omani learners<br>
                Supported by The Research Council (TRC), Oman<br>
                <i>Developed By Dr. Marwan @ Sohar University</i>
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
import os
#st.write("Files Streamlit can see:", os.listdir("."))
# --------------------------
# CONSENT
# --------------------------
if not st.session_state.consent:
    st.subheader("Consent / الموافقة")
    st.markdown("<small>I agree to share my responses and audio for research and possible commercialization.<br>أوافق على مشاركة إجاباتي والتسجيل الصوتي لأغراض البحث .</small>", unsafe_allow_html=True)
    if st.button("I Agree / أوافق"):
        st.session_state.consent = True
        st.rerun()
    st.stop()

# --------------------------
# CAPTCHA (FIXED LOGIC)
# --------------------------
if 'captcha_code' not in st.session_state:
    st.session_state.captcha_code = ''.join(random.choices("ABC123XYZ", k=3))

if not st.session_state.captcha_ok:
    user_input = st.text_input(f"Verification: Please enter the code: **{st.session_state.captcha_code}**")
    if user_input:
        if user_input == st.session_state.captcha_code:
            st.session_state.captcha_ok = True
            st.success("CAPTCHA Verified!")
            st.rerun()
        else:
            st.error("Incorrect code. Please try again.")
    st.stop() 

# --------------------------
# STUDENT INFO
# --------------------------
st.subheader("Student Info")
age = st.selectbox("Age", list(range(10, 21)))
gender = st.selectbox("Gender", ["Male", "Female"])

# --------------------------
# SENTENCES
# --------------------------
# 
arabic_sentences = st.secrets["ARABIC_SENTENCES"] * 100
# --------------------------
# SENTENCES (SECURE)
# --------------------------
# 
if "ARABIC_SENTENCES" in st.secrets:
    arabic_sentences = st.secrets["ARABIC_SENTENCES"] * 10
else:
    # جمل احتياطية في حال تعذر الاتصال بالخزنة
    arabic_sentences = ["يرجى إضافة الجمل في Secrets"]

if "sentence" not in st.session_state:
    st.session_state.sentence = random.choice(arabic_sentences)

st.subheader("📖 Read/translate this sentence in english only:")
st.success(st.session_state.sentence)
#if "sentence" not in st.session_state:
   # st.session_state.sentence = random.choice(arabic_sentences)

#st.subheader("📖 Read/translate this sentence in english only:")
#st.success(st.session_state.sentence)

if st.button("🔄 New Sentence"):
    st.session_state.sentence = random.choice(arabic_sentences)
    st.session_state.saved = False
    st.rerun()

st.markdown("<h3 style='color:red;'>⬇️ اضغط ايقونة الميكروفون للتسجيل</h3>", unsafe_allow_html=True)

# --------------------------
# AUDIO INPUT & ANIMATION
# --------------------------
audio = st.audio_input("Record")

st.markdown("""
<style>
@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
.animated-arrow { display: inline-block; animation: float 1.5s ease-in-out infinite; color: Green; font-size: 30px; }
.arabic-text { direction: rtl; text-align: left; color: Green; font-family: 'Arial', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class='arabic-text'><span class='animated-arrow'>⬆️</span><h3 style='display: inline-block; margin-left: 10px;'>اضغط ايقونة المربع عندما تنتهي من القراءة</h3></div>""", unsafe_allow_html=True)

recognized_text = ""
if audio:
    recognizer = sr.Recognizer()
    audio_bytes = audio.read()
    if not os.path.exists("audio_data"):
        os.makedirs("audio_data")

    filename = st.session_state.sentence.replace(" ", "_")[:20] + f"_{random.randint(1,100)}.wav"
    filepath = os.path.join("audio_data", filename)

    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    with sr.AudioFile(filepath) as source:
        audio_data = recognizer.record(source)
        try:
            recognized_text = recognizer.recognize_google(audio_data, language="en-US")
            st.write("Recognized:", recognized_text)
        except:
            st.error("Recognition failed")

# --------------------------
# ERROR DETECTION
# --------------------------
def detect_error(original, spoken):
    score = SequenceMatcher(None, original, spoken).ratio()
    if "p" in spoken.lower() or "b" in spoken.lower(): return "p/b confusion"
    if score > 0.85: return "Correct"
    return "Review Needed"

# --------------------------
# SAVE AUTOMATICALLY
# --------------------------
def upload_audio(filepath, filename):
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    requests.post(AUDIO_URL, json={"file": encoded, "filename": filename})

if recognized_text and not st.session_state.saved:
    error_type = detect_error(st.session_state.sentence, recognized_text)
    data = {
        "timestamp": str(datetime.now()),
        "age": age,
        "gender": gender,
        "original": st.session_state.sentence,
        "spoken": recognized_text,
        "mistake_type": error_type
    }
    requests.post(SHEET_URL, json=data)
    upload_audio(filepath, filename)
    st.session_state.saved = True
    st.success("✔✔✔ Saved Successfully!")

    st.markdown("⭐⭐⭐⭐⭐")
    st.markdown("شكراً لك 🙏")
    st.markdown("Thank you!")

import streamlit as st

# 1. Define the specific URL of your application
APP_URL = "https://trc-prototype-v2-english-evaluation-oman-school-level.streamlit.app/#read-translate-this-sentence-in-english-only"

# 2. Styling for the "Hard Refresh" Button
st.markdown("""
<style>
    .refresh-button {
        display: inline-block;
        padding: 0.5em 1em;
        color: white;
        background-color: #ff4b4b;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
        width: 100%;
        border: none;
        cursor: pointer;
    }
    .refresh-button:hover {
        background-color: #ff3333;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 3. The "New Record" Button Logic
st.markdown(f"""
    <div style="text-align: center; direction: rtl;">
        <p style="color: #666; font-size: 14px;">للبدء من جديد ومسح الذاكرة المؤقتة، اضغط الزر أدناه:</p>
        <a href="{APP_URL}" target="_self" class="refresh-button">
            🔄 تسجيل جديد / محاولة مرة أخرى
        </a>
    </div>
""", unsafe_allow_html=True)

# --------------------------
# --------------------------
# TEACHER LOGIN (SECURE)
# --------------------------
st.markdown("---")
entry_pass = st.text_input("Teacher Access", type="password")

if entry_pass == TEACHER_PASSWORD:
    st.success("Access Granted")
    st.markdown(f"""
    📊 [Open Excel Data]({EXCEL_LINK})  
    🎧 [Open Audio Folder]({DRIVE_LINK})
    """)

# --------------------------
# FOOTER
# --------------------------
st.markdown("<div style='font-size:10px;text-align:center;'>Contact: MShare@su.edu.om</div>", unsafe_allow_html=True)
