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

# --- KIỂM TRA THƯ VIỆN AI ---
try:
    import google.generativeai as genai
    AI_READY = True
except:
    AI_READY = False

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG V19 SIÊU CẤP
# ==========================================
VN_TZ = timezone(timedelta(hours=7))
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if AI_READY and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# Bộ lọc tài khoản sạch V19 (Fix lỗi 35)
def generate_username(fullname, dob):
    s = str(fullname)
    patterns = {'[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i', '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỵỷỹ]': 'y', '[đ]': 'd'}
    for p, c in patterns.items(): s = re.sub(p, c, s, flags=re.I)
    clean = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V19 (HỒI SINH GỐC)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, dob TEXT, class_name TEXT, managed_classes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, file_data TEXT, file_type TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME)''')
    
    # Tự động vá cột nếu thiếu (Lỗi 39)
    cols = [("fullname", "TEXT"), ("dob", "TEXT"), ("class_name", "TEXT"), ("managed_classes", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
        except: pass

    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

def log_action(deleted_by, entity_type, entity_name, reason):
    conn = sqlite3.connect('exam_db.sqlite')
    vn_time = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO deletion_logs (deleted_by, entity_type, entity_name, reason, timestamp) VALUES (?, ?, ?, ?, ?)", 
                 (deleted_by, entity_type, entity_name, reason, vn_time))
    conn.commit(); conn.close()

# ==========================================
# 3. TRUNG TÂM ĐIỀU HÀNH AI (CỐT LÕI MỞ)
# ==========================================
class V19AIEngine:
    @staticmethod
    def generate_practice_exam():
        """Vấn đề 1: Gemini sinh đề động kèm logic hình vẽ"""
        prompt = """Bạn là chuyên gia giáo dục. Hãy tạo đề thi trắc nghiệm Toán 9 (40 câu).
        YÊU CẦU CỰC KỲ QUAN TRỌNG:
        1. Nội dung mở, sinh động, thực tế, không lặp lại câu trước.
        2. Nếu là câu hình học, hãy mô tả tọa độ các điểm để tôi vẽ bằng code.
        3. Xuất kết quả duy nhất dạng JSON list:
        [{"id":1, "question":"...", "options":["A","B","C","D"], "answer":"A", "explanation":"..."}]"""
        try:
            res = ai_model.generate_content(prompt)
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

    @staticmethod
    def digitize_exam(file_b64, mime):
        """Vấn đề 2: Gemini OCR & Digitalization (Biến PDF/Ảnh thành bài thi tương tác)"""
        prompt = """Hãy đọc đề thi này và 'số hóa' nó. 
        Biến các câu hỏi trong ảnh/file thành danh sách câu hỏi trắc nghiệm JSON.
        Giữ nguyên bản gốc 100%. Phải có hướng dẫn giải chi tiết cho từng câu."""
        try:
            res = ai_model.generate_content([prompt, {"mime_type": mime, "data": file_b64}])
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

# ==========================================
# 4. GIAO DIỆN V19 GOLDEN (BẢO TỒN)
# ==========================================
def render_exam_ui(questions, session_key):
    st.divider()
    user_choices = {}
    for q in questions:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        user_choices[q['id']] = st.radio("Chọn đáp án:", q['options'], key=f"{session_key}_{q['id']}")
    
    if st.button("📤 NỘP BÀI CHÍNH THỨC", key=f"btn_{session_key}", type="primary", use_container_width=True):
        st.balloons()
        st.header("📊 BẢNG VÀNG KẾT QUẢ")
        for q in questions:
            is_correct = (user_choices[q['id']] == q['answer'])
            color = "#2e7d32" if is_correct else "#d32f2f"
            st.markdown(f"<div style='padding:15px; border-left: 8px solid {color}; background-color:#f8f9fa; border-radius:10px; margin-bottom:10px;'><b>Câu {q['id']}:</b> Đáp án: {q['answer']}</div>", unsafe_allow_html=True)
            with st.expander("🔍 Xem hướng dẫn giải chi tiết từ AI"):
                st.write(q['explanation'])

def main():
    st.set_page_config(page_title="Lê Quý Đôn V19 SUPREME AI", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🏫 HỆ THỐNG QUẢN LÝ THI LÊ QUÝ ĐÔN</h1>", unsafe_allow_html=True)
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
                    else: st.error("Sai thông tin đăng nhập!")
        return

    # SIDEBAR V19 CHUẨN
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        st.write(f"Cấp độ: **{st.session_state.role}**")
        if st.button("🚪 Đăng xuất", type="primary", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        with t1:
            if st.button("🔄 SINH ĐỀ 40 CÂU MỚI (DYNAMIC GEMINI)"):
                with st.spinner("AI đang sáng tạo đề thi mới..."):
                    st.session_state.prac_data = V19AIEngine.generate_practice_exam()
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam_ui(st.session_state.prac_data, "practice")

        with t2:
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Bắt đầu làm bài", key=f"ex_{row['id']}"):
                        with st.spinner("AI đang số hóa nội dung đề thi..."):
                            st.session_state.mand_data = V19AIEngine.digitize_exam(row['file_data'], row['file_type'])
                    if 'mand_data' in st.session_state and st.session_state.mand_data:
                        render_exam_ui(st.session_state.mand_data, "mandatory")

    # --- GIAO DIỆN QUẢN TRỊ (BẢO TỒN V19) ---
    else:
        st.title("🛠️ HỆ THỐNG QUẢN TRỊ V19 SUPREME")
        tabs = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi (AI Vision)", "📊 Báo cáo điểm", "📜 Nhật ký hệ thống"])
        
        with tabs[0]: # Quản lý học sinh - Fix lỗi 34, 35
            st.subheader("Nạp danh sách & Quản lý tài khoản")
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx'])
            if up and st.button("🔄 Xác nhận nạp dữ liệu"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users VALUES (?, '123456', 'student', ?, ?, ?, '9A', '')", 
                                 (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Đã nạp thành công danh sách sạch!")
            
            conn = sqlite3.connect('exam_db.sqlite')
            df_u = pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn)
            st.dataframe(df_u, use_container_width=True)

        with tabs[1]: # Giao đề (Vấn đề 2)
            st.subheader("Phát đề thi bằng Ảnh/PDF")
            tit = st.text_input("Tên bài kiểm tra")
            f = st.file_uploader("Tải tệp đề", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", 
                             (tit, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đã giao đề! AI đã sẵn sàng số hóa cho học sinh.")

        with tabs[3]: # Nhật ký Audit Log
            st.subheader("Nhật ký lưu vết hệ thống")
            conn = sqlite3.connect('exam_db.sqlite')
            st.table(pd.read_sql_query("SELECT * FROM deletion_logs ORDER BY id DESC", conn))

if __name__ == "__main__":
    main()
