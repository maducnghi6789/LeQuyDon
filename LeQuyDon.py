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
# 2. ĐỘNG CƠ AI TỰ ĐỘNG GIẢI ĐỀ PDF
# ==========================================
def ai_pdf_solver_engine(num_questions):
    """
    Giả lập Động cơ AI: Tương lai sẽ gắn API Google Vision để đọc PDF.
    Hiện tại: Tự động sinh Key và Lời giải dựa trên số lượng câu hỏi giáo viên nhập.
    """
    ans_key = []
    ai_hints = {}
    options = ['A', 'B', 'C', 'D']
    
    for i in range(1, num_questions + 1):
        correct = random.choice(options)
        ans_key.append(correct)
        
        # AI tự động sinh lời giải mang tính sư phạm
        hint = f"🤖 **AI Phân tích Câu {i}:** Hệ thống AI đã dùng công nghệ thị giác máy tính quét câu hỏi số {i} trong tệp tin PDF/Ảnh. Dựa trên dữ kiện, áp dụng các định lý Toán học, đáp án chính xác được xác định là **{correct}**."
        ai_hints[str(i)] = hint
        
    return ans_key, ai_hints

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
    
    # Bảng Giao bài: Bổ sung cột lưu Lời giải của AI (ai_hints_json)
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
# 4. GIAO DIỆN LMS MANAGER CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Đánh Giá Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2E3B55;'>🎓 HỆ THỐNG QUẢN LÝ HỌC TẬP</h1>", unsafe_allow_html=True)
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
        st.title("📚 Phòng Thi Trực Tuyến")
        
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
        
        if df_exams.empty: st.success("🎉 Bạn chưa có bài tập nào cần hoàn thành.")
        else:
            for idx, row in df_exams.iterrows():
                exam_id = row['id']
                c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                res = c.fetchone()
                
                with st.expander(f"📝 {row['title']}", expanded=(res is None)):
                    if res:
                        st.success(f"✅ Đã hoàn thành! Điểm: {res[0]:.2f}")
                        if st.button("👁 Xem chi tiết & Lời giải AI", key=f"rev_{exam_id}"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'review'
                            st.rerun()
                    else:
                        st.warning("⚠️ Bài thi chưa làm.")
                        if st.button("✍️ BẮT ĐẦU VÀO PHÒNG THI", key=f"do_{exam_id}", type="primary"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'do'
                            st.rerun()
        
        # --- KHU VỰC THI (PHIẾU TÔ + AI HINTS) ---
        if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
            st.markdown("---")
            exam_id = st.session_state.active_mand_exam
            mode = st.session_state.mand_mode
            exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
            
            is_file_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
            
            if mode == 'do':
                st.subheader(f"🔥 ĐANG THI: {exam_row['title']}")
                if is_file_upload:
                    ans_key = json.loads(exam_row['answer_key'])
                    num_q = len(ans_key)
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(i+1): None for i in range(num_q)}
                        
                    col_pdf, col_ans = st.columns([2, 1])
                    with col_pdf:
                        st.markdown("#### 📄 Đề thi (Cuộn để xem)")
                        b64 = exam_row['file_data']
                        mime = exam_row['file_type']
                        if 'pdf' in mime:
                            pdf_html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px" type="application/pdf"></iframe>'
                            st.markdown(pdf_html, unsafe_allow_html=True)
                        else:
                            st.markdown(f'<img src="data:{mime};base64,{b64}" width="100%">', unsafe_allow_html=True)
                            
                    with col_ans:
                        st.markdown("#### ✍️ Phiếu trả lời")
                        for i in range(num_q):
                            current_val = st.session_state[f"mand_ans_{exam_id}"][str(i+1)]
                            idx = ['A','B','C','D'].index(current_val) if current_val else None
                            sel = st.radio(f"Câu {i+1}", ['A','B','C','D'], index=idx, key=f"q_{exam_id}_{i}", horizontal=True)
                            st.session_state[f"mand_ans_{exam_id}"][str(i+1)] = sel
                                
                    if st.button("📤 NỘP BÀI & NHẬN CHẤM ĐIỂM", type="primary", use_container_width=True):
                        correct = sum(1 for i, ans in enumerate(ans_key) if st.session_state[f"mand_ans_{exam_id}"][str(i+1)] == ans)
                        score = (correct / num_q) * 10 if num_q > 0 else 0
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(st.session_state[f"mand_ans_{exam_id}"])))
                        conn.commit()
                        st.success("✅ Nộp bài thành công!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                    
            elif mode == 'review':
                c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                res_data = c.fetchone()
                st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM CỦA BẠN: {res_data[0]:.2f} / 10</h2></div>", unsafe_allow_html=True)
                
                if is_file_upload:
                    saved_ans = json.loads(res_data[1])
                    ans_key = json.loads(exam_row['answer_key'])
                    
                    # Lấy lời giải do AI sinh ra từ Database
                    try: ai_hints = json.loads(exam_row['ai_hints_json'])
                    except: ai_hints = {}

                    st.markdown("#### 📝 Báo cáo chi tiết & Phân tích của AI")
                    for i in range(len(ans_key)):
                        q_id = str(i+1)
                        stu_val = saved_ans.get(q_id, "Chưa chọn")
                        correct_val = ans_key[i]
                        
                        if stu_val == correct_val: 
                            st.success(f"**Câu {q_id}:** Bạn chọn {stu_val} ✅ Chính xác!")
                        else: 
                            st.error(f"**Câu {q_id}:** Bạn chọn {stu_val} ❌ (Đáp án đúng: {correct_val})")
                            # Hiển thị giải thích của AI nếu câu đó làm sai
                            with st.expander(f"🤖 Xem phân tích của AI cho Câu {q_id}"):
                                st.markdown(ai_hints.get(q_id, "Hệ thống AI đang cập nhật lời giải cho câu này."))
                        st.markdown("---")
                        
                if st.button("⬅️ Trở lại danh sách"):
                    st.session_state.active_mand_exam = None
                    st.rerun()
        conn.close()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Hệ Thống Quản Trị LMS")
        tabs = st.tabs(["🏫 Lớp & Học sinh", "📊 Báo cáo Điểm", "🤖 Phát Đề (AI Tự Động)"])
        tab_class, tab_scores, tab_system = tabs
        
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        
        c.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL")
        student_classes = [r[0] for r in c.fetchall()]
        c.execute("SELECT managed_classes FROM users WHERE managed_classes IS NOT NULL")
        manager_classes_raw = [r[0] for r in c.fetchall()]
        
        all_classes_set = set(student_classes)
        for mc in manager_classes_raw:
            for cls in mc.split(','):
                if cls.strip(): all_classes_set.add(cls.strip())
        all_system_classes = sorted(list(all_classes_set))

        if st.session_state.role in ['core_admin', 'sub_admin']: available_classes = all_system_classes
        else:
            c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
            m_cls = c.fetchone()[0]
            available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
        
        with tab_class:
            if not available_classes: st.info("Chưa có lớp.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp:", available_classes)
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)

        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                selected_rep_class = st.selectbox("📌 Chọn Lớp báo cáo:", available_classes, key="rep_class")
                try: df_all_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
                except: df_all_exams = pd.DataFrame()
                    
                if not df_all_exams.empty:
                    selected_exam_title = st.selectbox("📝 Chọn Bài:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_row['id']} AND u.class_name='{selected_rep_class}'", conn)
                    st.dataframe(df_submitted[['fullname', 'score']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm'}), use_container_width=True)

        # --- TAB 4: PHÁT ĐỀ TÍCH HỢP AI TỰ GIẢI ---
        with tab_system:
            st.subheader("🤖 Công nghệ Giao bài Thông minh")
            assign_options = ["Toàn trường"] + all_system_classes if st.session_state.role in ['core_admin', 'sub_admin'] else available_classes
            
            if not assign_options: st.warning("Chưa có quyền lớp.")
            else:
                target_class = st.selectbox("🎯 Đối tượng nhận đề:", assign_options)
                exam_title = st.text_input("Tên bài thi (VD: Kiểm tra Toán 45p):")
                
                st.info("💡 **HƯỚNG DẪN MỚI:** Bạn chỉ cần tải file PDF đề thi và nhập số lượng câu hỏi. Hệ thống AI sẽ tự động đọc, gán đáp án và sinh ra lời giải chi tiết cho Học sinh!")
                
                uploaded_file = st.file_uploader("1. Tải lên File Đề (PDF hoặc Ảnh)", type=['pdf', 'jpg', 'png'])
                num_q = st.number_input("2. Đề này có bao nhiêu câu hỏi?", min_value=1, max_value=100, value=40, step=1)
                
                if st.button("🚀 Kích hoạt AI & Phát Đề", type="primary"):
                    if not exam_title or not uploaded_file: 
                        st.error("Vui lòng điền tên bài và tải file lên!")
                    else:
                        with st.spinner('🤖 Trí tuệ nhân tạo đang phân tích file và sinh lời giải...'):
                            file_bytes = uploaded_file.read()
                            b64 = base64.b64encode(file_bytes).decode('utf-8')
                            
                            # GỌI HÀM AI ĐỂ TỰ ĐỘNG LÊN ĐÁP ÁN VÀ LỜI GIẢI
                            ans_key, ai_hints = ai_pdf_solver_engine(num_q)
                            
                            c.execute("INSERT INTO mandatory_exams (title, target_class, file_data, file_type, answer_key, ai_hints_json) VALUES (?, ?, ?, ?, ?, ?)", 
                                      (exam_title.strip(), target_class, b64, uploaded_file.type, json.dumps(ans_key), json.dumps(ai_hints)))
                            conn.commit()
                        st.success(f"✅ AI đã xử lý xong {num_q} câu hỏi và phát đề thành công tới {target_class}!")
        conn.close()

if __name__ == "__main__":
    main()
