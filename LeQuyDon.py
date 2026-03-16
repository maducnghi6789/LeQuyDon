# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN V19 SUPREME (HỘI TỤ LÕI & AI)
# ==========================================
import matplotlib
matplotlib.use('Agg')

import streamlit as st
import streamlit.components.v1 as components
import random
import math
import pandas as pd
import sqlite3
import base64
import json
import re
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from datetime import datetime, timedelta, timezone

# --- KIỂM TRA THƯ VIỆN GOOGLE AI (VÁ LỖI 38) ---
try:
    import google.generativeai as genai
    AI_READY = True
except ImportError:
    AI_READY = False

VN_TZ = timezone(timedelta(hours=7))

# --- CẤU HÌNH API GEMINI (DÁN MÃ CỦA GIÁM ĐỐC VÀO ĐÂY) ---
GEMINI_API_KEY = "AIzaSyDMdmMYUpqnB5wPxcF94Spy6LkNBdkKh2w" 

if AI_READY and GEMINI_API_KEY != "AIzaSyDMdmMYUpqnB5wPxcF94Spy6LkNBdkKh2w":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. PHỤC HỒI HÀM HỖ TRỢ V19 (DỰA TRÊN CORE.TXT)
# ==========================================
def to_excel(df, sheet_name='Sheet1'):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def remove_vietnamese_accents(s):
    s = str(s)
    patterns = {'[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i', 
                '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỷỹỵ]': 'y', '[đ]': 'd',
                '[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]': 'A', '[ÈÉẸẺẼÊỀẾỆỂỄ]': 'E', '[ÌÍỊỈĨ]': 'I',
                '[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]': 'O', '[ÙÚỦŨƯỪỨỰỬỮ]': 'U', '[ỲÝỴỶỸ]': 'Y', '[Đ]': 'D'}
    for p, r in patterns.items(): s = re.sub(p, r, s)
    return s

def generate_username(fullname, dob):
    clean_name = remove_vietnamese_accents(fullname).lower().replace(" ", "")
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V19 (BẢO TOÀN LÕI)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, dob TEXT, class_name TEXT, school TEXT, managed_classes TEXT)''')
    # Vá lỗi Database nếu thiếu cột (Fix lỗi 39)
    cols = [("fullname", "TEXT"), ("dob", "TEXT"), ("class_name", "TEXT"), ("school", "TEXT"), ("managed_classes", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
        except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, file_data TEXT, file_type TEXT, target_class TEXT, start_time TEXT, end_time TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

# ==========================================
# 3. MỞ MẠCH AI GEMINI (VẤN ĐỀ 1 & 2)
# ==========================================
class GeminiAIEngine:
    @staticmethod
    def call_ai(prompt, file_data=None, file_type=None):
        if not AI_READY or GEMINI_API_KEY == "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY": return None
        try:
            content = [prompt]
            if file_data: content.append({"mime_type": file_type, "data": file_data})
            res = ai_model.generate_content(content)
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

# ==========================================
# 4. ĐIỀU HÀNH HỆ THỐNG (V19 ULTIMATE)
# ==========================================
def main():
    st.set_page_config(page_title="Lê Quý Đôn V19 SUPREME", layout="wide")
    init_db()

    if 'current_user' not in st.session_state or st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center;'>🎓 HỆ THỐNG QUẢN LÝ THI V19</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login"):
                u = st.text_input("👤 Tài khoản").strip()
                p = st.text_input("🔑 Mật khẩu", type="password").strip()
                if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    r = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                    if r:
                        st.session_state.update({"current_user": u, "role": r[0], "fullname": r[1]})
                        st.rerun()
                    else: st.error("Sai thông tin!")
        return

    # --- SIDEBAR V19 CHUẨN ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        st.write(f"Vai trò: **{st.session_state.role}**")
        if st.button("🚪 Đăng xuất", type="primary"): st.session_state.clear(); st.rerun()

    # --- PHÂN QUYỀN GIAO DIỆN ---
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        with t1: # VẤN ĐỀ 1: SINH ĐỀ THỰC TẾ
            if st.button("🔄 SINH ĐỀ 40 CÂU THỰC TẾ (GEMINI AI)"):
                with st.spinner("AI đang soạn đề..."):
                    prompt = "Tạo đề thi Toán 9 ôn thi vào 10 chuyên, 40 câu thực tế, không hình vẽ, độ khó tăng dần, JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'...', 'explanation':'...'}]"
                    st.session_state.prac_data = GeminiAIEngine.call_ai(prompt)
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam(st.session_state.prac_data, "prac")

        with t2: # VẤN ĐỀ 2: SỐ HÓA ĐỀ BẮT BUỘC
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Vào làm bài", key=f"ex_{row['id']}"):
                        with st.spinner("AI đang số hóa đề..."):
                            prompt = "Đọc đề này và chuyển sang JSON trắc nghiệm kèm giải thích chi tiết từng câu."
                            st.session_state.mand_data = GeminiAIEngine.call_ai(prompt, row['file_data'], row['file_type'])
                    if 'mand_data' in st.session_state and st.session_state.mand_data:
                        render_exam(st.session_state.mand_data, "mand")
    
    else: # QUẢN TRỊ V19 (ADMIN LÕI, THÀNH VIÊN, GIÁO VIÊN)
        st.title("🛠️ QUẢN TRỊ HỆ THỐNG V19")
        tabs = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi", "📊 Báo cáo điểm", "📜 Nhật ký hệ thống"])
        
        with tabs[0]: # QUẢN LÝ LỚP (BẢO TOÀN LÕI)
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx'])
            if up and st.button("🔄 Nạp dữ liệu"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, '9A')", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Nạp xong!")
            conn = sqlite3.connect('exam_db.sqlite')
            st.dataframe(pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn))

        with tabs[1]: # GIAO ĐỀ AI VISION
            tit = st.text_input("Tên đề")
            f = st.file_uploader("Tải tệp đề", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", (tit, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đã giao bài!")

def render_exam(questions, session_id):
    st.divider()
    answers = {}
    for q in questions:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        answers[q['id']] = st.radio("Chọn đáp án:", q['options'], key=f"{session_id}_{q['id']}")
    if st.button("📤 NỘP BÀI", key=f"btn_{session_id}", type="primary"):
        st.balloons()
        for q in questions:
            correct = (answers[q['id']] == q['answer'])
            color = "green" if correct else "red"
            st.markdown(f"**Câu {q['id']}:** Đáp án: **{q['answer']}**")
            with st.expander("🔍 Giải thích"): st.write(q['explanation'])

if __name__ == "__main__":
    main()
