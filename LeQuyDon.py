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
from datetime import datetime, timezone, timedelta

# --- KIỂM TRA AI AN TOÀN ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG V19
# ==========================================
VN_TZ = timezone(timedelta(hours=7))
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if AI_AVAILABLE and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

def generate_username(fullname, dob):
    s = str(fullname)
    patterns = {'[àáạăằắặâầấậ]': 'a', '[èéẹêềếệ]': 'e', '[ìíị]': 'i', '[òóọôồốộơờớợ]': 'o', '[ùúụưừứự]': 'u', '[ỳýỵ]': 'y', '[đ]': 'd'}
    for p, c in patterns.items(): s = re.sub(p, c, s, flags=re.I)
    clean = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    suffix = str(dob).split('/')[-1] if dob and str(dob) != 'nan' else str(random.randint(1000, 9999))
    return f"{clean}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. KHỞI TẠO DB THÔNG MINH (FIX LỖI 39)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Tạo bảng nếu chưa có
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # TỰ ĐỘNG CẬP NHẬT CỘT THIẾU (FIX LỖI XUNG ĐỘT PHIÊN BẢN)
    columns = [("fullname", "TEXT"), ("dob", "TEXT"), ("class_name", "TEXT"), ("managed_classes", "TEXT")]
    for col_name, col_type in columns:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except: pass # Cột đã tồn tại

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, file_data TEXT, file_type TEXT, timestamp DATETIME)''')
    
    # Nạp admin bằng từ khóa rõ ràng để tránh lỗi 39
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

# ==========================================
# 3. CỐT LÕI AI (VẤN ĐỀ 1 & 2)
# ==========================================
class SmartAI:
    @staticmethod
    def process(prompt, file_bytes=None, mime=None):
        if not AI_AVAILABLE or GEMINI_API_KEY == "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY": return None
        try:
            content = [prompt]
            if file_bytes: content.append({"mime_type": mime, "data": file_bytes})
            res = ai_model.generate_content(content)
            match = re.search(r'\[.*\]', res.text, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

# ==========================================
# 4. GIAO DIỆN ĐỒNG NHẤT
# ==========================================
def render_exam(questions, session_id):
    st.divider()
    ans = {}
    for q in questions:
        st.markdown(f"#### Câu {q['id']}: {q['question']}")
        ans[q['id']] = st.radio("Chọn:", q['options'], key=f"{session_id}_{q['id']}")
    
    if st.button("📤 NỘP BÀI CHÍNH THỨC", key=f"btn_{session_id}", type="primary"):
        st.balloons()
        for q in questions:
            is_ok = (ans[q['id']] == q['answer'])
            st.markdown(f"**Câu {q['id']}:** {'✅ Đúng' if is_ok else '❌ Sai'} | Đáp án: **{q['answer']}**")
            with st.expander("Hướng dẫn giải"): st.write(q['explanation'])

# ==========================================
# 5. CHƯƠNG TRÌNH CHÍNH (V19 FINAL)
# ==========================================
def main():
    st.set_page_config(page_title="V19 AI CORE FINAL", layout="wide")
    init_db()

    if 'current_user' not in st.session_state:
        st.title("🏫 ĐĂNG NHẬP V19")
        u = st.text_input("Tài khoản").strip()
        p = st.text_input("Mật khẩu", type="password").strip()
        if st.button("🚀 Vào hệ thống"):
            conn = sqlite3.connect('exam_db.sqlite')
            r = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if r:
                st.session_state.update({"current_user": u, "role": r[0], "fullname": r[1]})
                st.rerun()
            else: st.error("Sai thông tin!")
        return

    # SIDEBAR
    with st.sidebar:
        st.header(f"👤 {st.session_state.fullname}")
        if st.button("🚪 Đăng xuất"): st.session_state.clear(); st.rerun()

    # PHÂN QUYỀN
    if st.session_state.role == 'student':
        t1, t2 = st.tabs(["🤖 LUYỆN ĐỀ AI MỞ", "🔥 BÀI KIỂM TRA BẮT BUỘC"])
        with t1: # Vấn đề 1
            if st.button("🚀 SINH ĐỀ 40 CÂU MỚI"):
                prompt = "Tạo đề thi trắc nghiệm Toán 9 ôn thi vào 10, 40 câu ngẫu nhiên, nội dung thực tế, không lặp lại câu trước, JSON: [{'id':1, 'question':'...', 'options':['A','B','C','D'], 'answer':'...', 'explanation':'...'}]"
                st.session_state.prac = SmartAI.process(prompt)
            if 'prac' in st.session_state and st.session_state.prac: render_exam(st.session_state.prac, "pr")

        with t2: # Vấn đề 2
            conn = sqlite3.connect('exam_db.sqlite')
            exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            for _, row in exams.iterrows():
                with st.expander(f"📋 {row['title']}"):
                    if st.button("✍️ Làm bài", key=f"ex_{row['id']}"):
                        prompt = "Đọc đề thi này và trích xuất sang JSON danh sách câu hỏi trắc nghiệm kèm giải thích."
                        st.session_state.mand = SmartAI.process(prompt, row['file_data'], row['file_type'])
                    if 'mand' in st.session_state and st.session_state.mand: render_exam(st.session_state.mand, "ma")
    else:
        # Giao diện Quản trị V19
        st.title("🛠 QUẢN TRỊ V19")
        m1, m2 = st.tabs(["🏫 Học sinh", "📤 Giao đề"])
        with m1:
            up = st.file_uploader("Nạp Excel", type=['xlsx'])
            if up and st.button("Nạp"):
                df = pd.read_excel(up)
                conn = sqlite3.connect('exam_db.sqlite')
                for _, r in df.iterrows():
                    un = generate_username(r['Họ tên'], r['Ngày sinh'])
                    conn.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, dob) VALUES (?, '123456', 'student', ?, ?)", (un, r['Họ tên'], r['Ngày sinh']))
                conn.commit(); st.success("Đã nạp xong!")
        with m2:
            title = st.text_input("Tên đề")
            f = st.file_uploader("Tải tệp", type=['pdf', 'jpg', 'png'])
            if f and st.button("🚀 PHÁT ĐỀ"):
                b64 = base64.b64encode(f.read()).decode()
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO mandatory_exams (title, file_data, file_type, timestamp) VALUES (?,?,?,?)", (title, b64, f.type, datetime.now(VN_TZ)))
                conn.commit(); st.success("Đã giao bài!")

if __name__ == "__main__":
    main()
