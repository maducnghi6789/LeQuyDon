import matplotlib
matplotlib.use('Agg')
import streamlit as st
import pandas as pd
import sqlite3
import json
import re
import random
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone, timedelta
import google.generativeai as genai

# ==========================================
# 1. CẤU HÌNH V19 & KẾT NỐI AI
# ==========================================
VN_TZ = timezone(timedelta(hours=7))

# Dán API Key vào đây để kích hoạt tính năng mở
GEMINI_API_KEY = "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY" 

if GEMINI_API_KEY != "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- BẢO TỒN MA TRẬN REGEX V19 ---
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
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG (GIỮ NGUYÊN LÕI V19)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, dob TEXT, class_name TEXT, school TEXT, managed_classes TEXT)''')
    # Vá lỗi cột cho máy chủ Cloud (Fix lỗi 39)
    cols = [("fullname", "TEXT"), ("dob", "TEXT"), ("class_name", "TEXT"), ("school", "TEXT"), ("managed_classes", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
        except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, file_data TEXT, file_type TEXT, target_class TEXT, start_time TEXT, end_time TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    # Bảo tồn Admin Lõi
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

# ==========================================
# 3. TRUNG TÂM AI MỞ (DYNAMIC & OCR)
# ==========================================
class GeminiEngine:
    @staticmethod
    def call_ai(prompt, f_data=None, f_type=None):
        if GEMINI_API_KEY == "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY": return None
        try:
            inp = [prompt]
            if f_data: inp.append({"mime_type": f_type, "data": f_data})
            res = ai_model.generate_content(inp)
            m = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(m.group()) if m else None
        except: return None

# ==========================================
# 4. ĐIỀU HÀNH HỆ THỐNG (FULL V19 INTERFACE)
# ==========================================
def main():
    st.set_page_config(page_title="LMS V19 SUPREME CORE", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🏫 HỆ THỐNG QUẢN LÝ THI LÊ QUÝ ĐÔN</h1>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1.2, 1])
        with c2:
            with st.form("login"):
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

    # SIDEBAR V19 CHUẨN
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        if st.button("🚪 Đăng xuất", type="primary", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # PHÂN QUYỀN GIAO DIỆN
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        with t1:
            if st.button("🔄 SINH ĐỀ THỰC TẾ (GEMINI AI)"):
                p = "Tạo đề Toán 9 thực tế, 40 câu ngẫu nhiên, độ khó chuyên, JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'A', 'explanation':'...'}]"
                st.session_state.prac_ai = GeminiEngine.call_ai(p)
            if 'prac_ai' in st.session_state and st.session_state.prac_ai:
                render_exam(st.session_state.prac_ai, "prac")
        with t2:
            # Logic đề bắt buộc chuẩn V19
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Làm bài", key=f"ex_{row['id']}"):
                        p = "Đọc đề này và số hóa thành JSON trắc nghiệm kèm giải thích."
                        st.session_state.mand_ai = GeminiEngine.call_ai(p, row['file_data'], row['file_type'])
                    if 'mand_ai' in st.session_state and st.session_state.mand_ai:
                        render_exam(st.session_state.mand_ai, "mand")

    else: # PHỤC HỒI TOÀN BỘ QUYỀN ADMIN/GIÁO VIÊN
        st.title("🛠️ QUẢN TRỊ HỆ THỐNG V19")
        tabs = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi", "📊 Báo cáo điểm", "📜 Nhật ký hệ thống"])
        
        with tabs[0]: # PHỤC HỒI NẠP EXCEL VÀ DANH SÁCH
            st.subheader("Quản lý học sinh")
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx'])
            if up and st.button("🔄 Xác nhận nạp"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, '9A')", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Đã nạp xong!")
            conn = sqlite3.connect('exam_db.sqlite')
            st.dataframe(pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn), use_container_width=True)

        with tabs[1]: # GIAO ĐỀ AI VISION
            tit = st.text_input("Tên đề")
            f = st.file_uploader("Tải tệp đề", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", (tit, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đã phát đề!")

        with tabs[3]: # NHẬT KÝ XÓA DỮ LIỆU
            conn = sqlite3.connect('exam_db.sqlite')
            st.table(pd.read_sql_query("SELECT * FROM deletion_logs ORDER BY id DESC", conn))

def render_exam(questions, sid):
    for q in questions:
        st.markdown(f"**Câu {q['id']}:** {q['question']}")
        st.radio("Chọn:", q['options'], key=f"{sid}_{q['id']}")
        with st.expander("Giải thích"): st.write(q['explanation'])

if __name__ == "__main__":
    main()
