# ==========================================
# 1. KHỞI TẠO ĐỒ HỌA & THƯ VIỆN
# ==========================================
import matplotlib
matplotlib.use('Agg')
import streamlit as st
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

# THƯ VIỆN ĐỌC PDF VÀ GỌI GEMINI AI
try:
    import PyPDF2
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Cần cài đặt thư viện: Mở terminal gõ `pip install PyPDF2 google-generativeai`")

VN_TZ = timezone(timedelta(hours=7))

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='DanhSachTaiKhoan')
    return output.getvalue()

def create_excel_template():
    df_template = pd.DataFrame(columns=["Họ tên", "Ngày sinh", "Trường"])
    df_template.loc[0] = ["Nguyễn Văn A", "15/08/2010", "THCS Lê Quý Đôn"]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='MauNhapLieu')
    return output.getvalue()

# ==========================================
# 2. BỘ NÃO AI THỰC SỰ (GOOGLE GEMINI API)
# ==========================================
def extract_text_from_pdf(file_bytes):
    """Mắt thần: Trích xuất nội dung văn bản từ tệp PDF"""
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return ""

def call_gemini_to_solve(pdf_text, num_questions, api_key):
    """
    Não bộ: Gửi nội dung PDF lên máy chủ Google Gemini để nhờ AI giải trực tiếp.
    ĐÃ FIX LỖI 404: Sử dụng model 'gemini-pro' cực kỳ ổn định.
    """
    try:
        genai.configure(api_key=api_key)
        # Chuyển sang dùng gemini-pro (phiên bản chuẩn mực nhất cho xử lý Text/JSON)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Bạn là một Chuyên gia Giáo dục. Dưới đây là nội dung trích xuất từ một đề thi trắc nghiệm PDF:
        --- BẮT ĐẦU ĐỀ THI ---
        {pdf_text}
        --- KẾT THÚC ĐỀ THI ---
        
        Đề thi này có tổng cộng {num_questions} câu hỏi trắc nghiệm (A, B, C, D).
        Nhiệm vụ của bạn:
        1. Phân tích nội dung đề thi, tự giải từng câu hỏi một cách chính xác nhất.
        2. Sinh ra Hướng dẫn giải chi tiết cho từng câu (ngắn gọn, dễ hiểu).
        3. Trả kết quả về BẮT BUỘC theo đúng định dạng JSON như sau (Không xuất ra text gì khác ngoài JSON):
        {{
            "answer_key": ["A", "B", "C", "D", ...],
            "ai_hints": {{
                "1": "Giải thích câu 1...",
                "2": "Giải thích câu 2..."
            }}
        }}
        Lưu ý: Mảng "answer_key" phải có đúng {num_questions} phần tử. Object "ai_hints" phải có đúng {num_questions} keys từ "1" đến "{num_questions}".
        """
        
        response = model.generate_content(prompt)
        
        # Bộ lọc bọc thép: Dọn dẹp rác markdown để lấy JSON chuẩn
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        data = json.loads(clean_text.strip())
        
        return data.get("answer_key", []), data.get("ai_hints", {})
        
    except Exception as e:
        st.error(f"Lỗi kết nối AI: {str(e)}")
        return [], {}

# ==========================================
# 3. CƠ SỞ DỮ LIỆU ĐA TẦNG
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    for col in ["fullname", "dob", "class_name", "school", "province", "managed_classes"]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cols = [("start_time", "TEXT"), ("end_time", "TEXT"), ("target_class", "TEXT"), 
            ("file_data", "TEXT"), ("file_type", "TEXT"), ("answer_key", "TEXT"), ("ai_hints_json", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} {dtype}")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

def generate_username(fullname, dob):
    clean_name = re.sub(r'[^\w\s]', '', str(fullname)).lower().replace(" ", "")
    if not dob or str(dob).lower() == 'nan': suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 4. BỘ MÁY ĐỀ TỰ LUYỆN AI (GIỮ NGUYÊN)
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def generate_all(self):
        pool = []
        pool.append({"q": r"Điều kiện xác định của biểu thức $\sqrt{2x - 4}$ là:", "a": r"$x \ge 2$", "d": [r"$x > 2$", r"$x \le 2$", r"$x < 2$"], "h": "💡 HD: Biểu thức dưới căn $\ge 0$.", "i": None})
        pool.append({"q": r"Giá trị của biểu thức $\sqrt{12} - 2\sqrt{3}$ bằng:", "a": "0", "d": [r"$\sqrt{9}$", r"$2\sqrt{3}$", "3"], "h": r"💡 HD: $\sqrt{12} = 2\sqrt{3}$.", "i": None})
        pool.append({"q": r"Nghiệm của hệ phương trình $\begin{cases} x - y = 1 \\ 2x + y = 5 \end{cases}$ là:", "a": r"$(2; 1)$", "d": [r"$(1; 2)$", r"$(3; -1)$", r"$(2; -1)$"], "h": "💡 HD: Cộng 2 vế: $3x = 6 \Rightarrow x=2$.", "i": None})
        pool.append({"q": r"Tập nghiệm của phương trình $x^2 - 5x + 6 = 0$ là:", "a": r"$\{2; 3\}$", "d": [r"$\{-2; -3\}$", r"$\{1; 6\}$", r"$\{-1; -6\}$"], "h": "💡 HD: $2+3=5$ và $2 \times 3=6$.", "i": None})
        
        selected_normal = random.sample(pool * 15, 38)
        hardcore_bank = [
            {"q": r"**[Toán Chuyên]** Tìm số cặp nghiệm nguyên dương $(x; y)$ của phương trình: $xy - 2x - 3y + 5 = 0$.", "a": "2 cặp", "d": ["0 cặp", "1 cặp", "Vô số cặp"], "h": r"💡 **HD:** Đưa về $(x-3)(y-2) = 1$."},
            {"q": r"**[Toán Chuyên]** Cho $x, y > 0$ thỏa mãn $x+y=1$. Tìm giá trị nhỏ nhất của biểu thức $A = \frac{1}{x^2+y^2} + \frac{1}{xy}$.", "a": "6", "d": ["4", "8", "2"], "h": r"💡 **HD:** Điểm rơi Cauchy."}
        ]
        final_questions = selected_normal + random.sample(hardcore_bank, 2)
        random.shuffle(final_questions)

        for i, hc in enumerate(final_questions):
            opts = [hc["a"]] + hc["d"][:3]
            random.shuffle(opts)
            self.exam.append({"id": i + 1, "question": hc["q"], "options": opts, "answer": hc["a"], "hint": hc["h"], "image": hc.get("i", None)})
        return self.exam
# ==========================================
# 5. GIAO DIỆN LMS MANAGER CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Quản Lý Giáo Dục", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2E3B55;'>🎓 HỆ THỐNG THI TRỰC TUYẾN</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### 🔒 Cổng Đăng Nhập")
                user = st.text_input("👤 Tài khoản")
                pwd = st.text_input("🔑 Mật khẩu", type="password")
                if st.form_submit_button("🚀 Đăng nhập", use_container_width=True):
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (user.strip(), pwd.strip()))
                    res = c.fetchone()
                    conn.close()
                    if res:
                        st.session_state.current_user = user.strip()
                        st.session_state.role = res[0]
                        st.session_state.fullname = res[1]
                        st.rerun()
                    else: st.error("❌ Sai tài khoản hoặc mật khẩu!")
        return

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_map.get(st.session_state.role, '')}")
        
        if st.session_state.role == 'student':
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cl = c.fetchone()
            st.markdown(f"**Lớp học:** {res_cl[0] if res_cl and res_cl[0] else 'Chưa phân lớp'}")
            conn.close()

        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH 
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc (Giáo viên giao)", "🤖 Luyện đề Tự do"])
        
        with tab_mand:
            st.info("📌 Xem đề thi PDF bên trái và tô đáp án điện tử bên phải.")
            conn = sqlite3.connect('exam_db.sqlite')
            try: df_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            except: df_exams = pd.DataFrame()
            
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cls = c.fetchone()
            student_class = str(res_cls[0]).strip().lower() if res_cls and res_cls[0] else ""
            
            valid_rows = []
            for idx, row in df_exams.iterrows():
                tc = str(row.get('target_class', 'Toàn trường')).strip().lower()
                if 'toàn' in tc or 'trường' in tc or 'truong' in tc or (student_class != "" and student_class in tc):
                    valid_rows.append(row)
            df_exams = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
            
            if df_exams.empty: st.success("Hiện chưa có bài tập nào dành cho bạn.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    st.markdown(f"#### 📜 {row['title']}")
                    
                    if res:
                        st.success(f"✅ Đã hoàn thành! Điểm của bạn: {res[0]:.2f}")
                        if st.button("👁 Xem chấm điểm & Lời giải AI", key=f"rev_{exam_id}"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'review'
                            st.rerun()
                    else:
                        if st.button("✍️ BẮT ĐẦU THI", key=f"do_{exam_id}", type="primary"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'do'
                            st.rerun()
                    st.markdown("---")
            
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                
                is_file_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
                
                if mode == 'do':
                    st.subheader(f"📝 ĐANG THI: {exam_row['title']}")
                    
                    if is_file_upload:
                        ans_key = json.loads(exam_row['answer_key'])
                        num_q = len(ans_key)
                        if f"mand_ans_{exam_id}" not in st.session_state:
                            st.session_state[f"mand_ans_{exam_id}"] = {str(i+1): None for i in range(num_q)}
                            
                        # GIAO DIỆN CHIA ĐÔI: BÊN TRÁI PDF, BÊN PHẢI TÔ TRẮC NGHIỆM
                        col_pdf, col_ans = st.columns([1.5, 1])
                        
                        with col_pdf:
                            st.markdown("#### 📄 TỜ ĐỀ THI")
                            b64 = exam_row['file_data']
                            mime = exam_row['file_type']
                            if 'pdf' in mime:
                                pdf_html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px" type="application/pdf"></iframe>'
                                st.markdown(pdf_html, unsafe_allow_html=True)
                            else:
                                st.markdown(f'<img src="data:{mime};base64,{b64}" width="100%">', unsafe_allow_html=True)
                                
                        with col_ans:
                            st.markdown("#### ✍️ PHIẾU TÔ ĐÁP ÁN")
                            st.info("Lướt đề bên trái và tick chọn đáp án bên dưới.")
                            
                            grid_cols = st.columns(2)
                            for i in range(num_q):
                                with grid_cols[i % 2]:
                                    current_val = st.session_state[f"mand_ans_{exam_id}"][str(i+1)]
                                    idx = ['A','B','C','D'].index(current_val) if current_val else None
                                    sel = st.radio(f"Câu {i+1}", ['A','B','C','D'], index=idx, key=f"q_{exam_id}_{i}", horizontal=True)
                                    st.session_state[f"mand_ans_{exam_id}"][str(i+1)] = sel
                                    
                            st.markdown("---")
                            if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True):
                                correct = sum(1 for i, ans in enumerate(ans_key) if st.session_state[f"mand_ans_{exam_id}"][str(i+1)] == ans)
                                score = (correct / num_q) * 10 if num_q > 0 else 0
                                c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(st.session_state[f"mand_ans_{exam_id}"])))
                                conn.commit()
                                st.success("✅ Đã nộp bài!")
                                st.session_state.active_mand_exam = None
                                st.rerun()

                elif mode == 'review':
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res_data = c.fetchone()
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM CỦA BẠN: {res_data[0]:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    
                    if is_file_upload:
                        saved_ans = json.loads(res_data[1])
                        ans_key = json.loads(exam_row['answer_key'])
                        try: ai_hints = json.loads(exam_row['ai_hints_json'])
                        except: ai_hints = {}
                        
                        st.markdown("#### 📝 BẢNG ĐỐI CHIẾU ĐÁP ÁN & AI GIẢI THÍCH")
                        for i in range(len(ans_key)):
                            q_id = str(i+1)
                            stu_val = saved_ans.get(q_id, "Chưa chọn")
                            correct_val = ans_key[i]
                            
                            if stu_val == correct_val: 
                                st.success(f"**Câu {q_id}:** Bạn chọn {stu_val} ✅ Chính xác!")
                            else: 
                                st.error(f"**Câu {q_id}:** Bạn chọn {stu_val} ❌ (Đáp án đúng: {correct_val})")
                                # Hiển thị Lời giải AI
                                with st.expander(f"🤖 Xem AI (Gemini) Hướng dẫn giải Câu {q_id}"):
                                    st.markdown(ai_hints.get(q_id, "AI chưa cập nhật lời giải."))
                            st.markdown("---")
                            
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
            conn.close()

        with tab_ai:
            st.title("🤖 Luyện Tập Đề Thi AI")
            st.info("Khu vực tự luyện tập. Hệ thống sẽ tự động sinh 40 câu ngẫu nhiên.")
            # ... (Phần logic AI Tự luyện giữ nguyên như các bản trước) ...

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển")
        tabs = st.tabs(["🏫 Lớp & Học sinh", "📊 Báo cáo", "🤖 Phát Đề (Gemini AI Đọc PDF)"])
        tab_class, tab_scores, tab_system = tabs
        
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        
        c.execute("SELECT DISTINCT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''")
        all_system_classes = sorted([r[0].strip() for r in c.fetchall()])
        
        with tab_class:
            c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
            m_cls_raw = c.fetchone()[0]
            my_managed_classes = sorted([x.strip() for x in str(m_cls_raw).split(',') if x.strip()]) if m_cls_raw else []
            view_classes = all_system_classes if st.session_state.role in ['core_admin', 'sub_admin'] else my_managed_classes

            if not view_classes: st.info("Chưa có lớp nào.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp:", view_classes)
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)

        with tab_scores:
            st.subheader("📊 Báo cáo Điểm")
            if view_classes:
                selected_rep_class = st.selectbox("📌 Chọn Lớp:", view_classes, key="rep_class")
                try: df_all_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
                except: df_all_exams = pd.DataFrame()
                if not df_all_exams.empty:
                    selected_exam_title = st.selectbox("📝 Chọn Bài:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_row['id']} AND u.class_name='{selected_rep_class}'", conn)
                    st.dataframe(df_submitted[['fullname', 'score']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm'}), use_container_width=True)

        # --- TAB 4: PHÁT ĐỀ TÍCH HỢP GEMINI AI ---
        with tab_system:
            st.subheader("🚀 Giao Bài (Gemini AI Tự Động Giải Đề)")
            
            if st.session_state.role in ['core_admin', 'sub_admin']:
                assign_options = ["Toàn trường"] + all_system_classes
            else:
                assign_options = view_classes
            
            if not assign_options: 
                st.warning("Bạn chưa được cấp quyền quản lý lớp nào.")
            else:
                target_class = st.selectbox("🎯 Đối tượng nhận đề:", assign_options)
                exam_title = st.text_input("Tên bài thi (VD: Đề Toán Giữa Kỳ 2):")
                
                st.markdown("---")
                st.info("💡 **SỨC MẠNH CỦA GEMINI AI:** Bạn hãy nhập API Key của Google, tải file PDF lên và nhập tổng số lượng câu hỏi. Hệ thống sẽ tự động quét PDF, gửi cho AI để tự lập đáp án và viết lời giải chi tiết cho Học sinh!")
                
                api_key_input = st.text_input("🔑 Nhập Google Gemini API Key (Miễn phí từ Google AI Studio):", type="password")
                uploaded_file = st.file_uploader("1. Tải lên File Đề (Bắt buộc là tệp PDF)", type=['pdf'])
                num_q = st.number_input("2. Đề thi này có tổng cộng bao nhiêu câu hỏi?", min_value=1, max_value=100, value=40, step=1)
                
                if st.button("🚀 Gửi PDF cho AI Xử lý & Phát Đề", type="primary"):
                    if not exam_title or not uploaded_file or not api_key_input: 
                        st.error("Vui lòng điền tên bài, tải file PDF và nhập API Key!")
                    else:
                        with st.spinner('🤖 Đang kết nối với máy chủ Google Gemini để phân tích tệp PDF. Vui lòng đợi trong giây lát...'):
                            file_bytes = uploaded_file.read()
                            b64 = base64.b64encode(file_bytes).decode('utf-8')
                            
                            # 1. Trích xuất văn bản từ PDF
                            pdf_text = extract_text_from_pdf(file_bytes)
                            
                            # 2. Bơm văn bản vào não bộ Gemini AI để lấy Đáp án & Lời giải thật
                            ans_key, ai_hints = call_gemini_to_solve(pdf_text, num_q, api_key_input)
                            
                            if not ans_key:
                                st.error("❌ AI gặp sự cố trong việc phân tích tệp PDF. Vui lòng kiểm tra lại API Key hoặc đảm bảo tệp PDF chứa văn bản có thể đọc được.")
                            else:
                                c.execute("INSERT INTO mandatory_exams (title, target_class, file_data, file_type, answer_key, ai_hints_json) VALUES (?, ?, ?, ?, ?, ?)", 
                                          (exam_title.strip(), target_class, b64, uploaded_file.type, json.dumps(ans_key), json.dumps(ai_hints)))
                                conn.commit()
                                st.success(f"✅ Tuyệt vời! Gemini AI đã tự động giải xong {num_q} câu hỏi! Đã phát đề thành công tới {target_class}.")
        conn.close()

if __name__ == "__main__":
    main()

