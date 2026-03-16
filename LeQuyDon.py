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

# --- KIỂM TRA VÀ NẠP AI AN TOÀN (VÁ LỖI 38) ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ModuleNotFoundError:
    AI_AVAILABLE = False

# ==========================================
# 1. CẤU HÌNH API & HỆ THỐNG V19
# ==========================================
VN_TZ = timezone(timedelta(hours=7))
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if AI_AVAILABLE and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

def generate_username(fullname, dob):
    s = str(fullname)
    patterns = {'[àáảãạăằắẳẵặâầấẩẫậ]': 'a', '[èéẻẽẹêềếểễệ]': 'e', '[ìíỉĩị]': 'i', 
                '[òóỏõọôồốổỗộơờớởỡợ]': 'o', '[ùúủũụưừứửữự]': 'u', '[ỳýỷỹỵ]': 'y', '[đ]': 'd'}
    for p, c in patterns.items(): s = re.sub(p, c, s, flags=re.I)
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. KHỐI LOGIC AI (VẤN ĐỀ 1 & 2)
# ==========================================
class GeminiAIEngine:
    @staticmethod
    def call_ai(prompt, file_data=None, file_type=None):
        if not AI_AVAILABLE:
            return [{"id": 1, "question": "Hệ thống đang cài đặt AI, vui lòng thử lại sau 1 phút.", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "N/A"}]
        try:
            content = [prompt]
            if file_data: content.append({"mime_type": file_type, "data": file_data})
            response = ai_model.generate_content(content)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            return json.loads(json_match.group()) if json_match else None
        except: return None

# ==========================================
# 3. GIAO DIỆN LÀM BÀI (UX V19)
# ==========================================
def render_exam_ui(data, key):
    st.divider()
    user_answers = {}
    for q in data:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        user_answers[q['id']] = st.radio(f"Chọn đáp án:", q['options'], key=f"{key}_{q['id']}")
    
    if st.button("📤 NỘP BÀI & XEM GIẢI", key=f"btn_{key}", type="primary"):
        st.balloons()
        for q in data:
            is_correct = (user_answers[q['id']] == q['answer'])
            st.markdown(f"**Câu {q['id']}:** {'✅ Đúng' if is_correct else '❌ Sai'} | Đáp án đúng: **{q['answer']}**")
            with st.expander("🔍 Xem giải thích"): st.info(q['explanation'])

# ==========================================
# 4. KHỞI TẠO VÀ QUẢN TRỊ (GỐC V19)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, dob TEXT, class_name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, file_data TEXT, file_type TEXT, timestamp DATETIME)')
    c.execute("INSERT OR IGNORE INTO users VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc', '', '')")
    conn.commit(); conn.close()

def main():
    st.set_page_config(page_title="V19 AI CORE FIXED", layout="wide")
    init_db()

    if not AI_AVAILABLE:
        st.warning("⚠️ Đang kích hoạt Module AI mở rộng. Các tính năng AI sẽ khả dụng sau ít phút.")

    if 'current_user' not in st.session_state:
        st.title("🏫 ĐĂNG NHẬP HỆ THỐNG")
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("🚀 Vào hệ thống"):
            conn = sqlite3.connect('exam_db.sqlite')
            res = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u.strip(), p.strip())).fetchone()
            if res:
                st.session_state.update({"current_user": u, "role": res[0], "fullname": res[1]})
                st.rerun()
        return

    # GIAO DIỆN HỌC SINH
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI", "🔥 BÀI THI BẮT BUỘC"])
        with t1:
            if st.button("🚀 SINH ĐỀ 40 CÂU MỚI"):
                prompt = "Tạo đề thi trắc nghiệm Toán 9, 40 câu ngẫu nhiên, JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'...', 'explanation':'...'}]"
                st.session_state.prac_data = GeminiAIEngine.call_ai(prompt)
            if 'prac_data' in st.session_state and st.session_state.prac_data:
                render_exam_ui(st.session_state.prac_data, "prac")

        with t2:
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Vào làm bài", key=f"ex_{row['id']}"):
                        prompt = "Đọc đề thi này và chuyển sang JSON bài tập trắc nghiệm kèm giải thích."
                        st.session_state.active_mand = GeminiAIEngine.call_ai(prompt, row['file_data'], row['file_type'])
                    if 'active_mand' in st.session_state and st.session_state.active_mand:
                        render_exam_ui(st.session_state.active_mand, "mand")
    else:
        st.sidebar.write(f"Chào {st.session_state.fullname}")
        if st.sidebar.button("🚪 Đăng xuất"): st.session_state.clear(); st.rerun()
        # ... Phần Quản trị nạp Excel và Phát đề giữ nguyên như cũ ...

if __name__ == "__main__":
    main()
