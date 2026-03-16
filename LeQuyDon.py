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
# 1. CẤU HÌNH API & HỆ THỐNG V19
# ==========================================
VN_TZ = timezone(timedelta(hours=7))

# GIÁM ĐỐC DÁN KEY GEMINI VÀO ĐÂY ĐỂ KÍCH HOẠT HỆ THỐNG
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- VÁ LỖI 35: TÀI KHOẢN KHÔNG DẤU CHUẨN 100% ---
def generate_username(fullname, dob):
    s = str(fullname)
    patterns = {'[àáảãạăằắẳẵặâầấẩẫậ]': 'a', '[èéẻẽẹêềếểễệ]': 'e', '[ìíỉĩị]': 'i', 
                '[òóỏõọôồốổỗộơờớởỡợ]': 'o', '[ùúủũụưừứửữự]': 'u', '[ỳýỷỹỵ]': 'y', '[đ]': 'd'}
    for p, c in patterns.items(): s = re.sub(p, c, s, flags=re.I)
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU & LƯU VẾT (AUDIT LOG V19)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                 fullname TEXT, dob TEXT, class_name TEXT, managed_classes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, 
                 file_data TEXT, file_type TEXT, target_class TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, 
                 entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME)''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống', '', '', '')")
    conn.commit(); conn.close()

# ==========================================
# 3. KHỐI LOGIC AI MỞ (MÃ NGUỒN API GEMINI)
# ==========================================
class GeminiAIEngine:
    @staticmethod
    def call_ai(prompt, file_data=None, file_type=None):
        if GEMINI_API_KEY == "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY": 
            st.warning("⚠️ Chưa cấu hình API Key cho Gemini AI.")
            return None
        try:
            content = [prompt]
            if file_data: content.append({"mime_type": file_type, "data": file_data})
            response = ai_model.generate_content(content)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            return json.loads(json_match.group()) if json_match else None
        except Exception as e:
            st.error(f"❌ Lỗi AI: {e}")
            return None

# ==========================================
# 4. GIAO DIỆN LÀM BÀI ĐỒNG NHẤT (VẤN ĐỀ 2)
# ==========================================
def render_exam_interface(data, key):
    st.divider()
    user_answers = {}
    for q in data:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        user_answers[q['id']] = st.radio(f"Chọn đáp án:", q['options'], key=f"{key}_{q['id']}")
    
    if st.button("📤 NỘP BÀI VÀ XEM GIẢI CHI TIẾT", key=f"btn_{key}", type="primary"):
        st.balloons()
        st.header("📊 KẾT QUẢ & HƯỚNG DẪN GIẢI")
        for q in data:
            is_correct = (user_answers[q['id']] == q['answer'])
            color = "#2e7d32" if is_correct else "#d32f2f"
            st.markdown(f"""<div style="padding:10px; border-radius:5px; border-left: 5px solid {color}; background-color: #f9f9f9; margin-bottom: 10px;">
                <b>Câu {q['id']}:</b> {'✅ Đúng' if is_correct else '❌ Sai'} | Đáp án đúng: <b>{q['answer']}</b>
            </div>""", unsafe_allow_html=True)
            with st.expander(f"🔍 Xem cách giải chi tiết câu {q['id']}"):
                st.write(q['explanation'])

# ==========================================
# 5. GIAO DIỆN CHÍNH LMS V19
# ==========================================
def main():
    st.set_page_config(page_title="Lê Quý Đôn LMS V19 AI", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🏫 ĐĂNG NHẬP V19</h1>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 1.2, 1])
        with col_c:
            with st.form("login"):
                u = st.text_input("Tài khoản").strip()
                p = st.text_input("Mật khẩu", type="password").strip()
                if st.form_submit_button("🚀 ĐĂNG NHẬP"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    res = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                    if res:
                        st.session_state.update({"current_user": u, "role": res[0], "fullname": res[1]})
                        st.rerun()
                    else: st.error("Sai thông tin đăng nhập!")
        return

    # --- SIDEBAR & LOGOUT ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        st.write(f"Vai trò: {st.session_state.role}")
        if st.button("🚪 Đăng xuất"): st.session_state.clear(); st.rerun()

    # --- PHÂN QUYỀN GIAO DIỆN ---
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        
        with t1: # VẤN ĐỀ 1
            if st.button("🚀 SINH ĐỀ 40 CÂU MỚI (DYNAMIC AI)"):
                with st.spinner("Gemini AI đang soạn đề..."):
                    prompt = "Tạo đề thi trắc nghiệm Toán 9 ôn thi vào 10, 40 câu hỏi ngẫu nhiên, nội dung thực tế, không lặp lại câu trước, định dạng JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'...', 'explanation':'...'}]"
                    st.session_state.prac_data = GeminiAIEngine.call_ai(prompt)
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam_interface(st.session_state.prac_data, "practice")

        with t2: # VẤN ĐỀ 2
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']} ({row['timestamp']})"):
                    if st.button("✍️ Vào làm bài", key=f"ex_{row['id']}"):
                        with st.spinner("AI đang số hóa đề thi..."):
                            prompt = "Đọc đề thi này và trích xuất sang JSON danh sách câu hỏi trắc nghiệm kèm giải thích."
                            st.session_state.active_mand = GeminiAIEngine.call_ai(prompt, row['file_data'], row['file_type'])
                    if 'active_mand' in st.session_state and st.session_state.active_mand:
                        render_exam_interface(st.session_state.active_mand, "mandatory")

    else: # QUẢN TRỊ (ADMIN/GIÁO VIÊN)
        st.title("🛠️ QUẢN TRỊ HỆ THỐNG V19")
        m1, m2 = st.tabs(["🏫 Học sinh & Lớp", "📤 Giao đề thi"])
        
        with m1: # NẠP EXCEL (FIX LỖI 34)
            st.subheader("Nạp danh sách học sinh")
            up = st.file_uploader("Chọn file Excel", type=['xlsx'])
            if up and st.button("🔄 Nạp dữ liệu"):
                try:
                    df = pd.read_excel(up)
                    conn = sqlite3.connect('exam_db.sqlite')
                    for _, r in df.iterrows():
                        un = generate_username(r['Họ tên'], r['Ngày sinh'])
                        conn.execute("INSERT OR IGNORE INTO users VALUES (?, '123456', 'student', ?, ?, ?, '9A')", 
                                     (un, r['Họ tên'], r['Ngày sinh']))
                    conn.commit(); st.success("✅ Nạp thành công!")
                except Exception as e: st.error(e)

        with m2: # PHÁT ĐỀ (VẤN ĐỀ 2)
            st.subheader("Giao đề bằng Ảnh hoặc PDF")
            title = st.text_input("Tên đề thi")
            f = st.file_uploader("Tải tệp", type=['pdf', 'jpg', 'png'])
            if f and st.button("🚀 PHÁT ĐỀ TOÀN TRƯỜNG"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", 
                             (title, b64, f.type, datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("🔥 Đã giao bài!")

if __name__ == "__main__":
    main()
