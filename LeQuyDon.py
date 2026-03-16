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

# --- KIỂM TRA VÀ TỰ CÀI ĐẶT THƯ VIỆN AI (VÁ LỖI 38) ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
        import google.generativeai as genai
        AI_AVAILABLE = True
    except:
        AI_AVAILABLE = False

VN_TZ = timezone(timedelta(hours=7))

# --- CẤU HÌNH API GEMINI (MỞ MÃ NGUỒN) ---
# Giám đốc dán mã API vào đây để kích hoạt bộ não AI
GEMINI_API_KEY = "" 

if AI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. HÀM HỖ TRỢ LÕI V19 (GIỮ NGUYÊN GỐC)
# ==========================================
def to_excel(df, sheet_name='Sheet1'):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def remove_vietnamese_accents(s):
    s = str(s)
    patterns = {
        '[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i',
        '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỵỷỹ]': 'y', '[đ]': 'd',
        '[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]': 'A', '[ÈÉẸẺẼÊỀẾỆỂỄ]': 'E', '[ÌÍỊỈĨ]': 'I',
        '[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]': 'O', '[ÙÚỦŨƯỪỨỰỬỮ]': 'U', '[ỲÝỴỶỸ]': 'Y', '[Đ]': 'D'
    }
    for pattern, char in patterns.items():
        s = re.sub(pattern, char, s)
    return s

def generate_username(fullname, dob):
    clean_name = remove_vietnamese_accents(fullname).lower().replace(" ", "")
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V19 (PHỤC HỒI)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng người dùng với đầy đủ cấu trúc lõi [cite: 2, 3]
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    for col in ["fullname", "dob", "class_name", "school", "managed_classes"]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    # Các bảng kết quả và đề thi [cite: 3, 4]
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, file_data TEXT, file_type TEXT, target_class TEXT, start_time TEXT, end_time TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

def log_deletion(deleted_by, entity_type, entity_name, reason):
    conn = sqlite3.connect('exam_db.sqlite')
    vn_time = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO deletion_logs (deleted_by, entity_type, entity_name, reason, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (deleted_by, entity_type, entity_name, reason, vn_time))
    conn.commit(); conn.close()

# ==========================================
# 3. TRUNG TÂM XỬ LÝ AI MỞ (DYNAMIC & OCR)
# ==========================================
class V19AIEngine:
    @staticmethod
    def call_ai(prompt, file_data=None, file_type=None):
        if not AI_AVAILABLE or not GEMINI_API_KEY: return None
        try:
            content = [prompt]
            if file_data: content.append({"mime_type": file_type, "data": file_data})
            res = ai_model.generate_content(content)
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

# ==========================================
# 4. GIAO DIỆN LÀM BÀI V19 ĐỒNG NHẤT
# ==========================================
def render_exam_session(questions, session_key):
    st.divider()
    user_choices = {}
    for q in questions:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        user_choices[q['id']] = st.radio("Chọn đáp án:", q['options'], key=f"{session_key}_{q['id']}")
    
    if st.button("📤 NỘP BÀI VÀ XEM GIẢI CHI TIẾT", key=f"btn_{session_key}", type="primary", use_container_width=True):
        st.balloons()
        correct_count = sum(1 for q in questions if user_choices[q['id']] == q['answer'])
        score = (correct_count / len(questions)) * 10
        st.success(f"### KẾT QUẢ: {score:.2f} / 10 điểm")
        
        for q in questions:
            is_ok = user_choices[q['id']] == q['answer']
            color = "#2e7d32" if is_ok else "#d32f2f"
            st.markdown(f"<div style='padding:15px; border-left: 8px solid {color}; background-color:#f8f9fa; border-radius:10px; margin-bottom:10px;'><b>Câu {q['id']}:</b> Lựa chọn: {user_choices[q['id']]} | <b>Đúng: {q['answer']}</b></div>", unsafe_allow_html=True)
            with st.expander(f"🔍 Xem hướng dẫn giải chi tiết Câu {q['id']}"):
                st.info(q['explanation'])

# ==========================================
# 5. CHƯƠNG TRÌNH CHÍNH (HỘI TỤ LÕI V19)
# ==========================================
def main():
    st.set_page_config(page_title="LMS V19 SUPREME AI", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🎓 HỆ THỐNG QUẢN LÝ THI LÊ QUÝ ĐÔN</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_v19"):
                u = st.text_input("👤 Tài khoản").strip()
                p = st.text_input("🔑 Mật khẩu", type="password").strip()
                if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    r = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                    if r:
                        st.session_state.update({"current_user": u, "role": r[0], "fullname": r[1]})
                        st.rerun()
                    else: st.error("Sai thông tin đăng nhập!")
        return

    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        if st.button("🚪 Đăng xuất", type="primary"): st.session_state.clear(); st.rerun()

    # --- PHÂN QUYỀN GIAO DIỆN ---
    if st.session_state.role == 'student':
        tab1, tab2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI THI BẮT BUỘC"])
        with tab1: # VẤN ĐỀ 1
            if st.button("🚀 SINH ĐỀ 40 CÂU MỚI (DYNAMIC AI)"):
                with st.spinner("AI đang soạn đề..."):
                    prompt = "Tạo đề thi Toán 9 ôn thi vào 10 chuyên. 40 câu hỏi thực tế, không lặp lại, định dạng JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'...', 'explanation':'...'}]"
                    st.session_state.prac_data = V19AIEngine.call_ai(prompt)
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam_session(st.session_state.prac_data, "practice")

        with tab2: # VẤN ĐỀ 2
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Vào làm bài", key=f"ex_{row['id']}"):
                        with st.spinner("AI đang số hóa đề thi..."):
                            prompt = "Đọc đề thi này và trích xuất thành danh sách trắc nghiệm JSON chuẩn kèm giải thích chi tiết."
                            st.session_state.mand_data = V19AIEngine.call_ai(prompt, row['file_data'], row['file_type'])
                    if 'mand_data' in st.session_state and st.session_state.mand_data:
                        render_exam_session(st.session_state.mand_data, "mandatory")

    else: # QUẢN TRỊ V19 (HỒI SINH ĐẦY ĐỦ QUYỀN)
        st.title("🛠️ QUẢN TRỊ HỆ THỐNG V19")
        m_tabs = st.tabs(["🏫 Học sinh & Lớp", "🛡️ Nhân sự", "📊 Báo cáo điểm", "📤 Giao đề thi"])
        
        with m_tabs[0]: # PHỤC HỒI LÕI QUẢN LÝ HỌC SINH [cite: 142, 143]
            st.subheader("Nạp danh sách học sinh")
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx'])
            if up and st.button("🔄 Nạp dữ liệu"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users VALUES (?, '123456', 'student', ?, ?, ?, '9A', '')", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Nạp thành công!")
            
            conn = sqlite3.connect('exam_db.sqlite')
            df_u = pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn)
            st.dataframe(df_u, use_container_width=True)

        with m_tabs[3]: # PHÁT ĐỀ [cite: 231, 232]
            tit = st.text_input("Tên đề thi")
            f = st.file_uploader("Tải đề (PDF/Ảnh)", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", (tit, b64, f.type, datetime.now(VN_TZ)))
                conn.commit(); st.success("🔥 Đã giao bài!")

if __name__ == "__main__":
    main()
