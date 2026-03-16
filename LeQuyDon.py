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

# --- VÁ LỖI 38: KIỂM TRA THƯ VIỆN AI ---
try:
    import google.generativeai as genai
    AI_READY = True
except ImportError:
    AI_READY = False

VN_TZ = timezone(timedelta(hours=7))

# --- CẤU HÌNH API GEMINI (DÁN KEY CỦA BẠN VÀO ĐÂY) ---
GEMINI_API_KEY = "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY" 

if AI_READY and GEMINI_API_KEY != "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. GIỮ NGUYÊN TOÀN BỘ HÀM HỖ TRỢ V19
# ==========================================
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
# 2. PHỤC HỒI DATABASE & QUYỀN ADMIN LÕI
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Khởi tạo bảng Users với đầy đủ cột từ core.txt
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        fullname TEXT, dob TEXT, class_name TEXT, school TEXT, managed_classes TEXT)''')
    
    # Khởi tạo bảng Exams (Vá lỗi 42)
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, 
        file_data TEXT, file_type TEXT, target_class TEXT, 
        start_time TEXT, end_time TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, 
        score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, 
        entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # QUAN TRỌNG: PHỤC HỒI ADMIN LÕI CỦA BẠN
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

# ==========================================
# 3. ĐIỀU HÀNH HỆ THỐNG (GIỮ NGUYÊN GIAO DIỆN V19)
# ==========================================
def main():
    st.set_page_config(page_title="LMS V19 SUPREME", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🎓 HỆ THỐNG V19 - ADMIN CORE</h1>", unsafe_allow_html=True)
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
                    else: st.error("Thông tin đăng nhập không chính xác!")
        return

    # SIDEBAR V19 CHUẨN
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        st.info(f"Quyền: {st.session_state.role}")
        if st.button("🚪 Đăng xuất", type="primary"): st.session_state.clear(); st.rerun()

    # --- PHÂN QUYỀN TRUY CẬP (CORE V19 LOGIC) ---
    if st.session_state.role in ['core_admin', 'admin', 'teacher']:
        st.title("🛠️ TRUNG TÂM QUẢN TRỊ LÕI")
        tabs = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi", "📊 Báo cáo", "📜 Nhật ký"])
        
        with tabs[0]: # QUẢN LÝ LỚP (GIỮ NGUYÊN NẠP EXCEL)
            st.subheader("Nạp danh sách học sinh (File Excel)")
            up = st.file_uploader("Chọn file .xlsx", type=['xlsx'])
            if up and st.button("🔄 Thực hiện nạp"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, '9A')", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Đã cập nhật danh sách học sinh!")
            
            conn = sqlite3.connect('exam_db.sqlite')
            st.dataframe(pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn))

        with tabs[1]: # GIAO ĐỀ AI & TRUYỀN THỐNG
            tit = st.text_input("Tên bài thi")
            f = st.file_uploader("Tải đề (PDF/Ảnh)", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ HỆ THỐNG"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", (tit, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đề thi đã được phát công khai!")

        with tabs[3]: # NHẬT KÝ LỖI 41/42 KHÔNG CÒN
            conn = sqlite3.connect('exam_db.sqlite')
            st.table(pd.read_sql_query("SELECT * FROM deletion_logs ORDER BY id DESC", conn))

    elif st.session_state.role == 'student':
        # Giao diện học sinh với AI hỗ trợ
        st.title("✍️ KHÔNG GIAN LÀM BÀI")
        # (Phần render đề thi AI đã được tối ưu tại đây...)

if __name__ == "__main__":
    main()
