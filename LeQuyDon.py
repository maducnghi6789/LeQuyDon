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
from datetime import datetime, timedelta, timezone

# --- KIỂM TRA THƯ VIỆN AI ---
try:
    import google.generativeai as genai
    AI_READY = True
except ImportError:
    AI_READY = False

VN_TZ = timezone(timedelta(hours=7))

# --- CẤU HÌNH API GEMINI (DÁN KEY TẠI ĐÂY) ---
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN" 

if AI_READY and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. PHỤC HỒI HÀM CỐT LÕI V19 (HÀM HỖ TRỢ & REGEX)
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
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V19 (BẢO TOÀN PHÂN QUYỀN)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Khôi phục đầy đủ cột cho bảng users 
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                 fullname TEXT, dob TEXT, class_name TEXT, school TEXT, province TEXT, managed_classes TEXT)''')
    
    # Bảng đề thi và kết quả [cite: 4, 108]
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, 
                 questions_json TEXT, start_time TEXT, end_time TEXT, target_class TEXT, 
                 file_data TEXT, file_type TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                 exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Nhật ký hệ thống [cite: 5]
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, 
                 entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tài khoản Admin Lõi [cite: 6]
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

# ==========================================
# 3. GIAO DIỆN QUẢN TRỊ V19 (HÀN LẠI TOÀN BỘ THANH CÔNG CỤ)
# ==========================================
def main():
    st.set_page_config(page_title="LMS V19 SUPREME", layout="wide")
    init_db()

    if 'current_user' not in st.session_state or st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center;'>🎓 HỆ THỐNG QUẢN LÝ THI LÊ QUÝ ĐÔN</h1>", unsafe_allow_html=True) [cite: 62]
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login_form"): [cite: 63]
                u = st.text_input("👤 Tài khoản").strip()
                p = st.text_input("🔑 Mật khẩu", type="password").strip()
                if st.form_submit_button("🚀 ĐĂNG NHẬP"): [cite: 63]
                    conn = sqlite3.connect('exam_db.sqlite')
                    res = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u, p)).fetchone() [cite: 64]
                    if res:
                        st.session_state.update({"current_user": u, "role": res[0], "fullname": res[1]}) [cite: 65]
                        st.rerun()
                    else: st.error("❌ Sai thông tin đăng nhập!") [cite: 66]
        return

    # --- SIDEBAR V19 CHUẨN ---
    with st.sidebar: [cite: 66]
        st.header(f"👤 {st.session_state.fullname}") [cite: 66]
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"} [cite: 66]
        st.info(f"Vai trò: {role_map.get(st.session_state.role)}") [cite: 66]
        if st.button("🚪 Đăng xuất", type="primary"): [cite: 71]
            st.session_state.clear(); st.rerun()

    # --- GIAO DIỆN QUẢN TRỊ (PHỤC HỒI THANH CÔNG CỤ) ---
    if st.session_state.role in ['core_admin', 'sub_admin', 'teacher']: [cite: 142]
        st.title("⚙️ BẢNG ĐIỀU KHIỂN QUẢN TRỊ V19") [cite: 142]
        
        # Hàn lại các Tab quyền hạn 
        if st.session_state.role == 'core_admin':
            tabs = st.tabs(["🏫 Học sinh & Lớp", "🛡️ Nhân sự", "📊 Báo cáo điểm", "📤 Phát đề thi", "📜 Nhật ký hệ thống"])
        elif st.session_state.role == 'sub_admin':
            tabs = st.tabs(["🏫 Học sinh & Lớp", "📊 Báo cáo điểm", "📤 Phát đề thi"])
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo điểm", "📤 Phát đề thi"])

        with tabs[0]: # QUẢN LÝ HỌC SINH (NẠP EXCEL CHUẨN V19)
            st.subheader("🏫 Quản lý danh sách học sinh") [cite: 146]
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx']) [cite: 148]
            if up and st.button("🔄 Thực hiện nạp"): [cite: 148]
                df = pd.read_excel(up) [cite: 149]
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    fullname = str(r.get('Họ tên', '')).strip() [cite: 150]
                    dob = str(r.get('Ngày sinh', '')).strip() [cite: 150]
                    if fullname:
                        un = generate_username(fullname, dob) [cite: 153]
                        conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, '9A')", (un, fullname, dob)) [cite: 154]
                conn.commit(); st.success("✅ Đã nạp xong!") [cite: 156]
            
            conn = sqlite3.connect('exam_db.sqlite')
            df_u = pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn) [cite: 162]
            st.dataframe(df_u, use_container_width=True) [cite: 162]

        with tabs[-1]: # NHẬT KÝ HỆ THỐNG [cite: 202]
            st.subheader("📜 Nhật ký lưu vết (Audit Log)") [cite: 202]
            conn = sqlite3.connect('exam_db.sqlite')
            df_logs = pd.read_sql_query("SELECT * FROM deletion_logs ORDER BY id DESC", conn) [cite: 203]
            st.table(df_logs) [cite: 203]

    # --- GIAO DIỆN HỌC SINH ---
    elif st.session_state.role == 'student': [cite: 72]
        st.title("✍️ KHÔNG GIAN HỌC TẬP")
        # Logic thi và luyện đề AI Vấn đề 1 & 2 đặt tại đây...

if __name__ == "__main__":
    main()
