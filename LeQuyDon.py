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

# --- KIỂM TRA THƯ VIỆN GOOGLE AI ---
try:
    import google.generativeai as genai
    AI_READY = True
except:
    AI_READY = False

# ==========================================
# 1. CẤU HÌNH CỐT LÕI (V19 CHUẨN)
# ==========================================
VN_TZ = timezone(timedelta(hours=7))
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if AI_READY and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# Fix lỗi 35: Tạo tài khoản không dấu tuyệt đối
def generate_username(fullname, dob):
    s = str(fullname)
    patterns = {'[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i', '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỵỷỹ]': 'y', '[đ]': 'd'}
    for p, c in patterns.items(): s = re.sub(p, c, s, flags=re.I)
    clean = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG (GIỮ NGUYÊN GỐC V19)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng người dùng với đầy đủ các cột của V19
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        fullname TEXT, dob TEXT, class_name TEXT, managed_classes TEXT)''')
    
    # Bảng đề thi bắt buộc
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, 
        file_data TEXT, file_type TEXT, target_class TEXT, timestamp DATETIME)''')
    
    # Bảng lưu vết xóa (Audit Log)
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, 
        entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME)''')
    
    # Vá lỗi Database cho Cloud (Fix lỗi 39)
    cols = [("fullname", "TEXT"), ("dob", "TEXT"), ("class_name", "TEXT"), ("managed_classes", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
        except: pass

    c.execute("INSERT OR IGNORE INTO users VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống', '', '', '')")
    conn.commit()
    conn.close()

# ==========================================
# 3. TRUNG TÂM XỬ LÝ AI MỞ (DYNAMIC & OCR)
# ==========================================
class V19AIEngine:
    @staticmethod
    def call_gemini(prompt, file_tuple=None):
        if not AI_READY or GEMINI_API_KEY == "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY": return None
        try:
            content = [prompt]
            if file_tuple:
                content.append({"mime_type": file_tuple[0], "data": file_tuple[1]})
            res = ai_model.generate_content(content)
            # Ép AI nhả đúng định dạng JSON
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

# ==========================================
# 4. GIAO DIỆN LÀM BÀI CHUẨN V19
# ==========================================
def render_exam_session(questions, session_id):
    st.divider()
    user_choices = {}
    for q in questions:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        user_choices[q['id']] = st.radio("Chọn đáp án:", q['options'], key=f"{session_id}_{q['id']}")
    
    if st.button("📤 NỘP BÀI CHÍNH THỨC", key=f"btn_{session_id}", type="primary", use_container_width=True):
        st.balloons()
        st.header("📊 KẾT QUẢ & HƯỚNG DẪN GIẢI")
        for q in questions:
            is_correct = (user_choices[q['id']] == q['answer'])
            color = "#2e7d32" if is_correct else "#d32f2f"
            st.markdown(f"""<div style='padding:15px; border-left: 8px solid {color}; background-color:#f8f9fa; border-radius:10px; margin-bottom:10px;'>
                <b>Câu {q['id']}:</b> Đáp án của bạn: {user_choices[q['id']]} | <b>Đúng: {q['answer']}</b></div>""", unsafe_allow_html=True)
            with st.expander(f"🔍 Giải thích chi tiết từ AI cho Câu {q['id']}"):
                st.write(q['explanation'])

# ==========================================
# 5. ĐIỀU HÀNH HỆ THỐNG (CORE V19)
# ==========================================
def main():
    st.set_page_config(page_title="Lê Quý Đôn V19 ULTIMATE AI", layout="wide")
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

    # --- SIDEBAR V19 CHUẨN ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        st.write(f"Vai trò: **{st.session_state.role}**")
        if st.button("🚪 Đăng xuất", type="secondary", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        
        with t1: # VẤN ĐỀ 1: SINH ĐỀ ĐỘNG
            st.subheader("Hệ thống AI thiết kế đề thi độc bản")
            if st.button("🔄 SINH ĐỀ 40 CÂU MỚI (DYNAMIC GEMINI)"):
                prompt = "Tạo đề thi trắc nghiệm Toán 9 ôn thi vào 10. 40 câu ngẫu nhiên, không lặp lại, định dạng JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'A', 'explanation':'...'}]"
                st.session_state.prac_data = V19AIEngine.call_gemini(prompt)
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam_session(st.session_state.prac_data, "practice")

        with t2: # VẤN ĐỀ 2: SỐ HÓA ĐỀ BẮT BUỘC
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Bắt đầu làm bài", key=f"ex_{row['id']}"):
                        prompt = "Đọc đề thi này và số hóa thành JSON trắc nghiệm để học sinh làm bài trên web. Giữ nguyên nội dung gốc."
                        st.session_state.mand_data = V19AIEngine.call_gemini(prompt, (row['file_type'], row['file_data']))
                    if 'mand_data' in st.session_state and st.session_state.mand_data:
                        render_exam_session(st.session_state.mand_data, "mandatory")

    # --- GIAO DIỆN QUẢN TRỊ (GIỮ NGUYÊN V19) ---
    else:
        st.title("🛠️ QUẢN TRỊ HỆ THỐNG V19")
        tabs = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi", "📊 Báo cáo điểm", "📜 Nhật ký hệ thống"])
        
        with tabs[0]: # QUẢN LÝ LỚP - FIX LỖI 34, 35
            st.subheader("Quản lý danh sách học sinh")
            up = st.file_uploader("Nạp Excel học sinh", type=['xlsx'])
            if up and st.button("🔄 Xác nhận nạp"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, '9A')", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("✅ Đã nạp thành công!")
            
            conn = sqlite3.connect('exam_db.sqlite')
            df_u = pd.read_sql_query("SELECT username, fullname, dob, class_name FROM users WHERE role='student'", conn)
            st.dataframe(df_u, use_container_width=True)

        with tabs[1]: # GIAO ĐỀ
            st.subheader("Phát đề bài thi bằng Ảnh/PDF")
            tit = st.text_input("Tên đề thi")
            f = st.file_uploader("Tải tệp đề", type=['pdf','jpg','png'])
            if tit and f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", 
                             (tit, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đã giao đề thành công!")

        with tabs[3]: # NHẬT KÝ
            conn = sqlite3.connect('exam_db.sqlite')
            st.table(pd.read_sql_query("SELECT * FROM deletion_logs ORDER BY id DESC", conn))

if __name__ == "__main__":
    main()
