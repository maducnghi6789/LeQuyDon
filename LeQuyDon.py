# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN V20 (NÂNG CẤP ĐỒ HỌA AI)
# ==========================================
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

# --- KẾT NỐI GEMINI AI ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
        import google.generativeai as genai
        AI_AVAILABLE = True
    except:
        AI_AVAILABLE = False

VN_TZ = timezone(timedelta(hours=7))

# GIÁM ĐỐC DÁN API KEY VÀO ĐÂY
GEMINI_API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY" 

if AI_AVAILABLE and GEMINI_API_KEY != "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# ==========================================
# 1. HÀM HỖ TRỢ EXCEL & REGEX 
# ==========================================
def to_excel(df, sheet_name='Sheet1'):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def create_excel_template():
    df_template = pd.DataFrame(columns=["Họ tên", "Ngày sinh", "Trường"])
    df_template.loc[0] = ["Nguyễn Văn A", "15/08/2010", "THCS Lê Quý Đôn"]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='MauNhapLieu')
    return output.getvalue()

def remove_vietnamese_accents(s):
    s = str(s)
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    return s

def generate_username(fullname, dob):
    clean_name = remove_vietnamese_accents(fullname).lower().replace(" ", "")
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    if not dob or str(dob).lower() == 'nan': 
        suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V20
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
    cols = [
        ("start_time", "TEXT"), ("end_time", "TEXT"), ("target_class", "TEXT DEFAULT 'Toàn trường'"),
        ("file_data", "TEXT"), ("file_type", "TEXT"), ("answer_key", "TEXT")
    ]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} {dtype}")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

def log_deletion(deleted_by, entity_type, entity_name, reason):
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    vn_time = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO deletion_logs (deleted_by, entity_type, entity_name, reason, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (deleted_by, entity_type, entity_name, reason, vn_time))
    conn.commit(); conn.close()

# ==========================================
# 3. ĐỒ HỌA TOÁN HỌC DỰ PHÒNG (LÕI V19)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    fig, ax = plt.subplots(figsize=(3, 2))
    a = random.choice([0.5, 1, 2, -0.5, -1, -2])
    x = np.linspace(-3, 3, 100); y = a * x**2
    color = '#2980b9' if a > 0 else '#e74c3c'
    ax.plot(x, y, color=color, lw=2)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.text(0.2, max(y)*0.9, 'y', style='italic'); ax.text(3.2, 0.2, 'x', style='italic'); ax.text(-0.3, -0.3, 'O')
    return fig_to_base64(fig), a

# ==========================================
# 4. BỘ MÁY SINH ĐỀ AI GEMINI ĐA DẠNG & SVG (MỚI)
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def format_options(self, correct, distractors):
        opts = [correct] + distractors[:3]
        random.shuffle(opts)
        return opts

    def generate_all(self):
        ai_questions = []
        if ai_model:
            try:
                # Prompt tối ưu hóa cho đồ họa AI và chống lặp
                prompt = """Đóng vai giáo viên chuyên ra đề Toán 9 theo chuẩn SGK. 
                Hãy sáng tác 40 câu hỏi trắc nghiệm Toán 9 ôn thi vào lớp 10 chuyên.
                YÊU CẦU NGHIÊM NGẶT:
                1. Tính độc bản: KHÔNG ĐƯỢC lặp lại mô típ cũ. Đảo lộn hoàn toàn dạng bài và nội dung thực tế (cầu đường, quỹ đạo, lãi suất, đo đạc).
                2. Phân loại mức độ: BẮT BUỘC ghi rõ [Nhận biết], [Thông hiểu], [Vận dụng], [Vận dụng cao] ở đầu mỗi câu.
                3. Hình ảnh do AI tự tạo (CỰC KỲ QUAN TRỌNG): Với các bài toán thực tế cần hình vẽ (ít nhất 10 câu), hãy tự tạo mã HTML/SVG chuẩn, màu sắc sinh động, rõ ràng (ví dụ: vẽ cái thang, tháp, biểu đồ). Đặt mã SVG vào trường 'image_svg'. Nếu câu nào không cần hình, để 'image_svg': "".
                4. ĐỊNH DẠNG JSON: Trả về ĐÚNG chuỗi JSON nguyên khối, tuyệt đối hợp lệ.
                
                MẪU JSON:
                [
                  {
                    "question": "[Vận dụng] Một cái thang dài 5m dựa vào tường...",
                    "options": ["A", "B", "C", "D"],
                    "answer": "A",
                    "hint": "HD: Áp dụng Pytago...",
                    "image_svg": "<svg height='150' width='150'><line x1='0' y1='100' x2='50' y2='0' style='stroke:red;stroke-width:2'/></svg>"
                  }
                ]"""
                res = ai_model.generate_content(prompt)
                match = re.search(r'\[.*\]', res.text, re.DOTALL)
                if match:
                    ai_questions = json.loads(match.group())
            except Exception as e:
                pass # Lỗi AI sẽ tự sinh thêm dữ liệu dự phòng

        final_pool = []

        # Xử lý câu hỏi AI: Đảo lộn ngẫu nhiên vị trí các đáp án (A B C D)
        for q in ai_questions:
            opts = q.get("options", [])
            random.shuffle(opts)
            final_pool.append({
                "q": q.get("question", ""),
                "opts": opts,
                "a": q.get("answer", ""),
                "h": q.get("hint", ""),
                "i_svg": q.get("image_svg", ""),
                "i": None
            })

        # Bù thêm bằng ngân hàng dự phòng nếu AI sinh chưa đủ 40 câu do giới hạn token
        if len(final_pool) < 40:
            img_para, a_val = draw_real_parabola()
            ans_para = r"Hệ số $a > 0$" if a_val > 0 else r"Hệ số $a < 0$"
            opts = self.format_options(ans_para, [r"Hệ số $a < 0$" if a_val > 0 else r"Hệ số $a > 0$", "Hàm số đồng biến", "Phương trình vô nghiệm"])
            final_pool.append({"q": "[Vận dụng] Quan sát quỹ đạo bay mô phỏng của quả bóng. Khẳng định nào sau đây ĐÚNG về hệ số $a$?", "opts": opts, "a": ans_para, "h": "Quan sát bề lõm của Parabol.", "i_svg": "", "i": img_para})
            
            while len(final_pool) < 40:
                final_pool.append({
                    "q": f"[Nhận biết] Căn bậc hai số học của {random.choice([16, 25, 36, 49, 64])} là:",
                    "opts": ["4", "5", "6", "7", "8"][:4],
                    "a": "4", "h": "Căn số học luôn không âm", "i_svg": "", "i": None
                })

        random.shuffle(final_pool)
        final_pool = final_pool[:40]

        for i, q in enumerate(final_pool):
            self.exam.append({
                "id": i + 1, "question": q["q"], "options": q["opts"],
                "answer": q["a"], "hint": q["h"], "image_svg": q["i_svg"], "image": q["i"]
            })
            
        return self.exam

# ==========================================
# 5. GIAO DIỆN HỆ THỐNG V20
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống LMS V20", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'fullname' not in st.session_state: st.session_state.fullname = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🎓 HỆ THỐNG KIỂM TRA TRỰC TUYẾN V20</h1>", unsafe_allow_html=True)
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
                    else:
                        st.error("❌ Sai tài khoản hoặc mật khẩu!")
        return

    # --- SIDEBAR TÀI KHOẢN ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_map.get(st.session_state.role, '')}")
        
        if st.session_state.role == 'student':
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cl = c.fetchone()
            st.markdown(f"**Lớp học:** {res_cl[0] if res_cl and res_cl[0] else 'Chưa cập nhật'}")
            conn.close()
            
            st.markdown("---")
            with st.expander("🔑 Đổi mật khẩu"):
                new_pw = st.text_input("Nhập mật khẩu mới:", type="password", key="new_pw_stu")
                if st.button("Lưu mật khẩu", key="btn_save_pw_stu"):
                    if new_pw.strip():
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        c.execute("UPDATE users SET password=? WHERE username=?", (new_pw.strip(), st.session_state.current_user))
                        conn.commit()
                        conn.close()
                        st.success("✅ Đổi mật khẩu thành công!")
                    else:
                        st.error("Mật khẩu không hợp lệ!")

        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH 
    # ==========================
    if st.session_state.role == 'student':
        # YÊU CẦU 1: Đổi tên tab thành "Đề tự luyện"
        tab_mand, tab_ai = st.tabs(["🔥 Bài kiểm tra Bắt buộc", "🤖 Đề tự luyện"])
        now_vn = datetime.now(VN_TZ)
        
        with tab_mand:
            st.info("📌 Khu vực làm các bài thi chính thức. Đối với Đề tải lên (PDF), xem nội dung bên trái và tô đáp án bên phải.")
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            try: df_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            except: df_exams = pd.DataFrame()
            
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cls = c.fetchone()
            student_class = str(res_cls[0]).strip().lower() if res_cls and res_cls[0] else ""
            
            valid_rows = []
            for idx, row in df_exams.iterrows():
                tc = str(row.get('target_class', '')).strip().lower()
                if tc == 'toàn trường' or tc == student_class or tc == 'none' or tc == '':
                    valid_rows.append(row)
            df_exams = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
            
            if df_exams.empty: st.success("Hiện chưa có bài kiểm tra nào được giao cho lớp của bạn.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    try:
                        t_start = datetime.strptime(row['start_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        t_end = datetime.strptime(row['end_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        time_display = f"⏰ Từ: {t_start.strftime('%d/%m %H:%M')} ⭢ Đến: {t_end.strftime('%d/%m %H:%M')}"
                    except:
                        t_start = None; t_end = None
                        time_display = "⏰ Thời gian: Không giới hạn"

                    c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    
                    st.markdown(f"#### 📜 {row['title']}")
                    st.markdown(time_display)
                    
                    if res:
                        st.success(f"✅ Đã nộp bài! Điểm số: **{res[0]:.2f}**")
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button("👁 Xem lại kết quả", key=f"rev_{exam_id}", use_container_width=True):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'review'
                                st.rerun()
                        with col_btn2:
                            if st.button("🏆 Bảng Xếp Hạng", key=f"rank_{exam_id}", use_container_width=True):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'ranking'
                                st.rerun()
                    else:
                        if t_start and now_vn < t_start: st.warning("⏳ Chưa đến thời gian làm bài.")
                        elif t_end and now_vn > t_end: st.error("🔒 Đã hết hạn làm bài.")
                        else:
                            if st.button("✍️ VÀO PHÒNG THI", key=f"do_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                st.session_state[f"start_exam_{exam_id}"] = datetime.now().timestamp()
                                st.rerun()
                    st.markdown("---")
            
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                is_pdf_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
                
                if mode == 'do':
                    time_limit_sec = 90 * 60
                    elapsed = datetime.now().timestamp() - st.session_state.get(f"start_exam_{exam_id}", datetime.now().timestamp())
                    remaining = max(0, time_limit_sec - elapsed)
                    js_timer = f"""<script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId); document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{ if (btns[i].innerText === '📤 NỘP BÀI CHÍNH THỨC') {{ btns[i].click(); break; }} }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60); var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script><div id="clock" style="font-size:20px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:5px; margin-bottom:10px;"></div>"""
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 ĐANG THI: {exam_row['title']}")
                    
                    if is_pdf_upload:
                        ans_key = []
                        try: ans_key = json.loads(exam_row['answer_key'])
                        except: pass
                        num_q = len(ans_key)
                        
                        if f"mand_ans_{exam_id}" not in st.session_state:
                            st.session_state[f"mand_ans_{exam_id}"] = {str(i+1): None for i in range(num_q)}
                            
                        if ai_model and st.button("✨ Nhờ AI số hóa đề này thành trắc nghiệm"):
                            with st.spinner("Đang phân tích PDF..."):
                                prompt = "Đọc đề này và chuyển sang JSON trắc nghiệm kèm giải chi tiết: [{'id': 1, 'question': '...', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'hint': '...'}]"
                                try:
                                    res = ai_model.generate_content([prompt, {"mime_type": exam_row['file_type'], "data": exam_row['file_data']}])
                                    match = re.search(r'\[.*\]', res.text, re.DOTALL)
                                    if match: st.session_state[f"ai_digitized_{exam_id}"] = json.loads(match.group())
                                except: st.error("Lỗi kết nối AI!")

                        if f"ai_digitized_{exam_id}" in st.session_state:
                            mand_exam_data = st.session_state[f"ai_digitized_{exam_id}"]
                            for q in mand_exam_data:
                                st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                                ans_val = st.session_state[f"mand_ans_{exam_id}"].get(str(q['id']))
                                selected = st.radio("Chọn đáp án:", options=q.get('options', ['A','B','C','D']), index=q['options'].index(ans_val) if ans_val in q.get('options', []) else None, key=f"m_q_{exam_id}_{q['id']}")
                                st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                                st.markdown("---")
                        else:
                            col_pdf, col_ans = st.columns([1.5, 1])
                            with col_pdf:
                                st.markdown("#### 📄 NỘI DUNG ĐỀ THI")
                                b64 = exam_row['file_data']
                                mime = exam_row['file_type']
                                if 'pdf' in str(mime).lower():
                                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700px" type="application/pdf"></iframe>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<img src="data:{mime};base64,{b64}" width="100%">', unsafe_allow_html=True)
                            with col_ans:
                                st.markdown("#### ✍️ PHIẾU TÔ TRẮC NGHIỆM")
                                grid_cols = st.columns(2)
                                for i in range(num_q):
                                    with grid_cols[i % 2]:
                                        q_str = str(i+1)
                                        current_val = st.session_state[f"mand_ans_{exam_id}"][q_str]
                                        idx = ['A','B','C','D'].index(current_val) if current_val in ['A','B','C','D'] else None
                                        sel = st.radio(f"Câu {q_str}", ['A','B','C','D'], index=idx, key=f"q_{exam_id}_{q_str}", horizontal=True)
                                        st.session_state[f"mand_ans_{exam_id}"][q_str] = sel
                                     
                        st.markdown("---")
                        if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                            correct = 0
                            stu_ans = st.session_state[f"mand_ans_{exam_id}"]
                            for i, correct_ans in enumerate(ans_key):
                                if stu_ans.get(str(i+1)) == correct_ans: correct += 1
                            score = (correct / num_q) * 10 if num_q > 0 else 0
                            c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(stu_ans)))
                            conn.commit()
                            st.success("✅ Đã nộp bài thành công!")
                            st.session_state.active_mand_exam = None
                            st.rerun()

                    else:
                        mand_exam_data = json.loads(exam_row['questions_json'])
                        num_q = len(mand_exam_data)
                        if f"mand_ans_{exam_id}" not in st.session_state:
                            st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                             
                        for q in mand_exam_data:
                            st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                            if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                            
                            ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                            selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                            st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                            st.markdown("---")
                        
                        if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                            correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
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
                    saved_ans = json.loads(res_data[1])
                    
                    if is_pdf_upload:
                        ans_key = json.loads(exam_row['answer_key'])
                        num_q = len(ans_key)
                        st.markdown("#### 📝 Bảng đối chiếu kết quả")
                        grid_cols = st.columns(4)
                        for i in range(num_q):
                            with grid_cols[i % 4]:
                                stu_val = saved_ans.get(str(i+1), "Chưa chọn")
                                correct_val = ans_key[i]
                                if stu_val == correct_val: st.success(f"Câu {i+1}: {stu_val} ✅")
                                else: st.error(f"Câu {i+1}: {stu_val} ❌ (Đ/A: {correct_val})")
                    else:
                        mand_exam_data = json.loads(exam_row['questions_json'])
                        for q in mand_exam_data:
                            st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                            if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                            u_ans = saved_ans.get(str(q['id']))
                            st.radio("Đã chọn:", options=q['options'], index=q['options'].index(u_ans) if u_ans in q['options'] else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                            if u_ans == q['answer']: st.success("✅ Chính xác")
                            else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                            with st.expander("📖 Xem Lời Giải Chi Tiết"): st.markdown(q.get('hint', ''), unsafe_allow_html=True)
                            st.markdown("---")
                            
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
                
                elif mode == 'ranking':
                    st.markdown(f"<h3 style='text-align: center; color: #e67e22;'>🏆 BẢNG VÀNG THÀNH TÍCH - {exam_row['title']}</h3>", unsafe_allow_html=True)
                    if student_class: st.markdown(f"<p style='text-align: center;'>Lớp: <b>{student_class.upper()}</b></p>", unsafe_allow_html=True)
                    
                    df_rank = pd.read_sql_query(f"SELECT u.fullname, mr.score FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{student_class}' ORDER BY mr.score DESC, mr.timestamp ASC LIMIT 10", conn)
                    
                    if not df_rank.empty:
                        df_rank.index = df_rank.index + 1
                        df_rank.columns = ['Họ và Tên', 'Điểm Số']
                        st.dataframe(df_rank, use_container_width=True)
                    else:
                        st.info("Chưa có đủ dữ liệu để xếp hạng.")
                        
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()

            conn.close()

        with tab_ai:
            st.title("🤖 Luyện Tập Đa Dạng (AI Sinh Động)")
            st.info("Mỗi lần tạo mới, AI sẽ sáng tác một đề độc bản, đảo lộn đáp án, tự động vẽ đồ họa minh họa (SVG) và phân loại độ khó bám sát SGK.")
            
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ LUYỆN TẬP MỚI (AI SÁNG TÁC)", use_container_width=True):
                with st.spinner("Đang yêu cầu AI Gemini tư duy ra đề, vẽ hình và phân loại độ khó SGK..."):
                    gen = ExamGenerator()
                    st.session_state.exam_data = gen.generate_all()
                    st.session_state.user_answers = {str(q['id']): None for q in st.session_state.exam_data}
                    st.session_state.is_submitted = False
                    st.rerun()

            if st.session_state.exam_data:
                if st.session_state.is_submitted:
                    correct_ans = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[str(q['id'])] == q['answer'])
                    score_ai = (correct_ans / len(st.session_state.exam_data)) * 10
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM: {score_ai:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    st.markdown("---")

                for q in st.session_state.exam_data:
                    # Phân loại độ khó bằng màu sắc nếu nhận diện được tag SGK
                    q_text = q['question']
                    if "[Nhận biết]" in q_text: q_text = q_text.replace("[Nhận biết]", "<span style='color:blue;font-weight:bold;'>[Nhận biết]</span>")
                    elif "[Thông hiểu]" in q_text: q_text = q_text.replace("[Thông hiểu]", "<span style='color:green;font-weight:bold;'>[Thông hiểu]</span>")
                    elif "[Vận dụng cao]" in q_text: q_text = q_text.replace("[Vận dụng cao]", "<span style='color:red;font-weight:bold;'>[Vận dụng cao]</span>")
                    elif "[Vận dụng]" in q_text: q_text = q_text.replace("[Vận dụng]", "<span style='color:orange;font-weight:bold;'>[Vận dụng]</span>")
                    
                    st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                    
                    # Render đồ họa AI vẽ (SVG)
                    if q.get('image_svg'):
                        st.markdown(f"<div style='margin-bottom: 10px;'>{q['image_svg']}</div>", unsafe_allow_html=True)
                    elif q.get('image'): 
                        st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px; margin-bottom: 10px;">', unsafe_allow_html=True)
                    
                    disabled = st.session_state.is_submitted
                    ans_val = st.session_state.user_answers[str(q['id'])]
                    selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    
                    if not disabled: 
                        st.session_state.user_answers[str(q['id'])] = selected
                        
                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.success("✅ Đúng")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                        with st.expander("📖 Xem Lời Giải Chi Tiết"): st.markdown(q.get('hint', ''), unsafe_allow_html=True)
                    st.markdown("---")
                
                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ LUYỆN", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS V20)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_scores, tab_system = tabs
            tab_staff = None
        
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        
        c.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''")
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
            if not available_classes: st.info("Chưa có lớp học nào được tạo hoặc được phân công cho bạn.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                c.execute("SELECT fullname FROM users WHERE role='student' AND class_name=?", (selected_class,))
                existing_names = [row[0].strip().lower() for row in c.fetchall()]

                with st.expander(f"➕ Thêm Học sinh vào lớp {selected_class}", expanded=False):
                    template_excel = create_excel_template()
                    st.download_button(label="⬇️ TẢI FILE EXCEL MẪU", data=template_excel, file_name="Mau_Danh_Sach.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                    uploaded_excel = st.file_uploader("Nạp file Excel (Đã điền)", type=['xlsx'])
                    if uploaded_excel is not None:
                        if st.button("🔄 Nạp dữ liệu"):
                            try:
                                df_import = pd.read_excel(uploaded_excel)
                                count_success = 0
                                for _, row in df_import.iterrows():
                                    fullname = str(row.get('Họ tên', '')).strip()
                                    dob = str(row.get('Ngày sinh', '')).strip()
                                    school = str(row.get('Trường', '')).strip()
                                    if fullname and fullname.lower() != 'nan':
                                        if dob.lower() == 'nan': dob = ""
                                        if school.lower() == 'nan': school = ""
                                        if fullname.lower() in existing_names and not dob: continue 
                                        uname = generate_username(fullname, dob)
                                        try:
                                            c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, fullname, dob, selected_class, school))
                                            count_success += 1
                                            existing_names.append(fullname.lower()) 
                                        except: pass
                                conn.commit()
                                st.success(f"✅ Đã tạo {count_success} tài khoản!")
                                st.rerun()
                            except Exception: 
                                st.error("Lỗi đọc file Excel. Vui lòng kiểm tra lại định dạng.")
                    
                    st.markdown("**Hoặc Tạo Thủ Công Nhanh:**")
                    with st.form("manual_add"):
                        c1, c2 = st.columns(2)
                        m_name = c1.text_input("Họ và Tên (Bắt buộc)")
                        m_dob = c2.text_input("Ngày sinh")
                        if st.form_submit_button("Tạo nhanh"):
                            if m_name:
                                uname = generate_username(m_name, m_dob)
                                c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, ?)", (uname, m_name, m_dob, selected_class))
                                conn.commit()
                                st.success(f"✅ Đã tạo: {uname} | Pass mặc định: 123456")
                                st.rerun()

                st.markdown("---")
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên', dob as 'Ngày sinh' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                if not df_students.empty:
                    excel_export = to_excel(df_students)
                    st.download_button(label=f"📥 XUẤT EXCEL DANH SÁCH LỚP {selected_class}", data=excel_export, file_name=f"Danh_sach_{selected_class}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    st.markdown("#### ✏️ Cập nhật Thông tin Học sinh")
                    user_to_edit = st.selectbox("Chọn Học sinh cần thao tác:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        c.execute("SELECT fullname, password, dob, class_name FROM users WHERE username=?", (user_to_edit,))
                        u_data = c.fetchone()
                        with st.form("edit_form"):
                            c1, c2 = st.columns(2)
                            edit_name = c1.text_input("Họ Tên", value=u_data[0])
                            edit_pwd = c2.text_input("Mật khẩu", value=u_data[1])
                            edit_dob = c1.text_input("Ngày sinh", value=u_data[2] if u_data[2] else "")
                            edit_class = c2.text_input("Đổi Lớp", value=u_data[3])
                            
                            if st.session_state.role in ['core_admin', 'sub_admin']:
                                del_reason_stu = st.text_input("Lý do xóa (Bắt buộc nếu muốn xóa Học sinh này):")
                            
                            col_save, col_del = st.columns(2)
                            if col_save.form_submit_button("💾 Cập nhật Thông tin"):
                                c.execute("UPDATE users SET fullname=?, password=?, dob=?, class_name=? WHERE username=?", (edit_name, edit_pwd, edit_dob, edit_class, user_to_edit))
                                conn.commit()
                                st.success("✅ Cập nhật thành công!")
                                st.rerun()
                                
                            if st.session_state.role in ['core_admin', 'sub_admin']:
                                if col_del.form_submit_button("🗑 XÓA TÀI KHOẢN NÀY"):
                                    if not del_reason_stu: st.error("❌ Vui lòng nhập Lý do xóa trước khi thao tác!")
                                    else:
                                        log_deletion(st.session_state.current_user, "Học sinh", f"{user_to_edit} ({u_data[0]})", del_reason_stu)
                                        c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                                        c.execute("DELETE FROM mandatory_results WHERE username=?", (user_to_edit,))
                                        conn.commit()
                                        st.rerun()
                            else:
                                col_del.markdown("*(Chỉ Admin có quyền xóa)*")
                
                st.markdown("---")
                if st.session_state.role in ['core_admin', 'sub_admin']:
                    with st.expander("🚨 Dọn dẹp Cuối năm (Xóa toàn bộ lớp)"):
                        st.warning(f"Hành động này sẽ xóa vĩnh viễn toàn bộ học sinh và kết quả thi của lớp {selected_class}.")
                        del_reason_class = st.text_input("Lý do xóa toàn bộ lớp (Bắt buộc):")
                        if st.checkbox("Tôi xác nhận muốn xóa vĩnh viễn dữ liệu lớp này."):
                            if st.button("🗑 TIẾN HÀNH XÓA LỚP", type="primary"):
                                if not del_reason_class: 
                                    st.error("❌ Vui lòng nhập Lý do xóa lớp!")
                                else:
                                    log_deletion(st.session_state.current_user, "Lớp học", selected_class, del_reason_class)
                                    for u in df_students['Tài khoản'].tolist():
                                        c.execute("DELETE FROM users WHERE username=?", (u,))
                                        c.execute("DELETE FROM mandatory_results WHERE username=?", (u,))
                                    conn.commit()
                                    st.success(f"✅ Đã xóa thành công lớp {selected_class}!")
                                    st.rerun()

        if tab_staff:
            with tab_staff:
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    with st.form("add_sa"):
                        c1, c2 = st.columns(2)
                        sa_user = c1.text_input("Tài khoản (viết liền)")
                        sa_pwd = c2.text_input("Mật khẩu")
                        sa_name = c1.text_input("Họ Tên")
                        sa_class = c2.text_input("Giao Lớp quản lý (VD: 9A, 9B)")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'sub_admin', ?, ?)", (sa_user, sa_pwd, sa_name, sa_class))
                                conn.commit()
                                st.rerun()
                            except: st.error("❌ Tên tồn tại!")
                            
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    
                    st.markdown("**Xóa Admin Thành viên:**")
                    c_del1, c_del2 = st.columns(2)
                    sa_to_del = c_del1.selectbox("Chọn Admin cần xóa:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    sa_del_reason = c_del2.text_input("Lý do xóa Admin này (Bắt buộc):")
                    if sa_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa Admin"):
                        if not sa_del_reason: st.error("❌ Vui lòng nhập Lý do xóa!")
                        else:
                            log_deletion(st.session_state.current_user, "Admin", sa_to_del, sa_del_reason)
                            c.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                            conn.commit()
                            st.rerun()
                    st.markdown("---")

                st.subheader("👨‍🏫 Quản lý Giáo viên")
                with st.form("add_gv"):
                    c1, c2 = st.columns(2)
                    t_user = c1.text_input("Tài khoản GV")
                    t_pwd = c2.text_input("Mật khẩu")
                    t_name = c1.text_input("Họ và Tên")
                    t_classes = c2.text_input("Giao Lớp quản lý ban đầu (VD: 9A1)")
                    if st.form_submit_button("Tạo GV", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", (t_user, t_pwd, t_name, t_classes))
                            conn.commit()
                            st.rerun()
                        except: st.error("❌ Tồn tại!")
                        
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                st.markdown("#### 🔄 Phân Công Lớp Cho Giáo Viên")
                t_to_edit = st.selectbox("Chọn Giáo viên để phân lớp:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_edit != "-- Chọn --":
                    current_classes = df_teach[df_teach['Tài khoản'] == t_to_edit]['Lớp QL'].values[0]
                    with st.form("reassign_gv_form"):
                        new_classes = st.text_input("Nhập danh sách lớp mới (phân cách bằng dấu phẩy, VD: 9A, 9B, 9C)", value=str(current_classes) if pd.notna(current_classes) else "")
                        if st.form_submit_button("💾 Cập nhật phân công"):
                            c.execute("UPDATE users SET managed_classes=? WHERE username=?", (new_classes, t_to_edit))
                            conn.commit()
                            st.success(f"✅ Đã phân công thành công!")
                            st.rerun()
                
                st.markdown("---")
                st.markdown("#### 🗑 Xóa Giáo viên")
                c_delt1, c_delt2 = st.columns(2)
                t_to_del = c_delt1.selectbox("Chọn GV cần xóa:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                t_del_reason = c_delt2.text_input("Lý do xóa Giáo viên này (Bắt buộc):")
                if t_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa GV"):
                    if not t_del_reason: st.error("❌ Vui lòng nhập Lý do xóa!")
                    else:
                        log_deletion(st.session_state.current_user, "Giáo viên", t_to_del, t_del_reason)
                        c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                        conn.commit()
                        st.rerun()

                if st.session_state.role == 'core_admin':
                    st.markdown("---")
                    st.subheader("📜 Lịch Sử Xóa / Dọn Dẹp Hệ Thống")
                    try:
                        df_logs = pd.read_sql_query("SELECT deleted_by as 'Người thao tác', entity_type as 'Loại dữ liệu', entity_name as 'Tên dữ liệu', reason as 'Lý do xóa', timestamp as 'Thời gian' FROM deletion_logs ORDER BY id DESC", conn)
                        if df_logs.empty: st.info("Chưa có lịch sử xóa dữ liệu nào.")
                        else: st.dataframe(df_logs, use_container_width=True)
                    except: pass

        # --- TAB 3: BÁO CÁO PHÂN TÍCH ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                selected_rep_class = st.selectbox("📌 Chọn Lớp xem báo cáo:", available_classes, key="rep_class")
                try:
                    df_all_exams = pd.read_sql_query("SELECT id, title, questions_json, file_data, answer_key FROM mandatory_exams ORDER BY id DESC", conn)
                except:
                    df_all_exams = pd.DataFrame()
                    
                if df_all_exams.empty: st.info("Chưa có bài tập.")
                else:
                    selected_exam_title = st.selectbox("📝 Chọn Bài Kiểm Tra:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    
                    is_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
                    
                    df_class_students = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{selected_rep_class}'", conn)
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng HS trong lớp", len(df_class_students))
                    c2.metric("Số HS Đã nộp", len(df_submitted))
                    c3.metric("Số HS Chưa nộp", len(df_class_students) - len(df_submitted))
                    
                    t1, t2, t3 = st.tabs(["✅ Bảng Điểm", "❌ Danh sách HS Chưa Làm", "📈 Thống kê Câu Sai Nhiều"])
                    
                    with t1:
                        if not df_submitted.empty: 
                            df_export = df_submitted[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Thời gian nộp'})
                            st.dataframe(df_export, use_container_width=True)
                            excel_data = to_excel(df_export, sheet_name="BangDiem")
                            st.download_button(label="📥 XUẤT BẢNG ĐIỂM (EXCEL)", data=excel_data, file_name=f"BangDiem_{selected_rep_class}.xlsx", type="primary")
                        else: st.info("Chưa có học sinh nào nộp bài.")
                        
                    with t2:
                        submitted_users = df_submitted['username'].tolist()
                        df_missing = df_class_students[~df_class_students['username'].isin(submitted_users)]
                        if not df_missing.empty: 
                            st.dataframe(df_missing[['username', 'fullname']].rename(columns={'username': 'Tài khoản', 'fullname': 'Họ Tên'}), use_container_width=True)
                        else: st.success("100% Học sinh đã hoàn thành bài thi!")
                        
                    with t3:
                        if not df_submitted.empty:
                            if is_upload:
                                try: ans_key = json.loads(exam_row['answer_key'])
                                except: ans_key = []
                                wrong_stats = {str(i+1): {'text': f"Câu hỏi số {i+1} (Trong File Đề PDF)", 'wrong_count': 0} for i in range(len(ans_key))}
                                for _, row in df_submitted.iterrows():
                                    try:
                                        stu_ans = json.loads(row['user_answers_json'])
                                        for i, correct_val in enumerate(ans_key):
                                            q_id = str(i+1)
                                            if stu_ans.get(q_id) != correct_val: wrong_stats[q_id]['wrong_count'] += 1
                                    except: pass
                            else:
                                exam_questions = json.loads(exam_row['questions_json'])
                                wrong_stats = {str(q['id']): {'text': q['question'], 'wrong_count': 0} for q in exam_questions}
                                for _, row in df_submitted.iterrows():
                                    try:
                                        stu_ans = json.loads(row['user_answers_json'])
                                        for q in exam_questions:
                                            q_id = str(q['id'])
                                            if stu_ans.get(q_id) != q['answer']: wrong_stats[q_id]['wrong_count'] += 1
                                    except: pass
                            
                            stats_list = [{'Câu': k, 'Nội dung': v['text'], 'Số HS làm sai': v['wrong_count']} for k, v in wrong_stats.items()]
                            df_stats = pd.DataFrame(stats_list).sort_values(by='Số HS làm sai', ascending=False)
                            
                            st.markdown("### 🚨 TOP CÁC CÂU LÀM SAI NHIỀU NHẤT:")
                            top5 = df_stats.head(5)
                            for _, r in top5.iterrows():
                                if r['Số HS làm sai'] > 0:
                                    clean_text = r['Nội dung'].replace("$", "").replace(r"\sqrt", "căn").replace(r"\frac", "phân số")
                                    st.error(f"**Câu {r['Câu']}** ({r['Số HS làm sai']} Học sinh sai)  \n_{clean_text}_")
                            
                            st.markdown("---")
                            st.dataframe(df_stats[['Câu', 'Số HS làm sai']], use_container_width=True)
                        else: st.info("Cần có dữ liệu nộp bài để hệ thống phân tích.")

        # --- TAB 4: PHÁT ĐỀ ---
        with tab_system:
            st.subheader("📤 Phát Bài Tập Cho Học Sinh")
            
            if st.session_state.role in ['core_admin', 'sub_admin']: 
                assign_options = ["Toàn trường"] + all_system_classes
                st.success("👑 BẠN ĐANG DÙNG QUYỀN ADMIN: Có thể giao chung cho 'Toàn trường' hoặc chỉ định một lớp cụ thể.")
            else: 
                assign_options = available_classes
                st.info("👨‍🏫 BẠN ĐANG DÙNG QUYỀN GIÁO VIÊN: Bạn chỉ được phép giao đề cho các lớp thuộc quyền quản lý của bạn.")
            
            if not assign_options: st.warning("Bạn chưa được phân quyền quản lý lớp nào nên chưa thể giao bài.")
            else:
                target_class = st.selectbox("🎯 Giao bài cho đối tượng:", assign_options)
                exam_title = st.text_input("Tên bài kiểm tra (VD: Thi Giữa Kỳ Toán 9)")
                
                c1, c2 = st.columns(2)
                s_date = c1.date_input("Ngày giao")
                s_time = c1.time_input("Giờ giao", value=datetime.strptime("07:00", "%H:%M").time())
                e_date = c2.date_input("Ngày thu")
                e_time = c2.time_input("Giờ thu", value=datetime.strptime("23:59", "%H:%M").time())
                
                st.markdown("---")
                exam_type = st.radio("Lựa chọn phương thức giao bài:", ["📤 Tải lên đề thi của tôi (File PDF/Ảnh)", "🤖 Sinh ngẫu nhiên từ Ngân hàng Đề AI"])
                
                if exam_type == "📤 Tải lên đề thi của tôi (File PDF/Ảnh)":
                    st.info("💡 Học sinh sẽ nhìn thấy File đề của bạn ở nửa màn hình bên trái và điền phiếu trắc nghiệm A B C D ở nửa màn hình bên phải.")
                    uploaded_file = st.file_uploader("1. Tải File Đề (Hỗ trợ PDF, JPG, PNG)", type=['pdf', 'jpg', 'png', 'jpeg'])
                    ans_input = st.text_input("2. Nhập chuỗi Đáp án Đúng (Viết liền, VD: ABCDABCD)")
                    
                    if st.button("🚀 Phát Đề (File PDF)", type="primary"):
                        if not exam_title: st.error("Vui lòng nhập tên bài thi!")
                        elif not uploaded_file: st.error("Vui lòng tải file đề thi lên!")
                        elif not ans_input: st.error("Vui lòng nhập chuỗi đáp án!")
                        else:
                            ans_clean = list(ans_input.upper().replace(" ", "").replace(",", ""))
                            valid_chars = all(char in ['A', 'B', 'C', 'D'] for char in ans_clean)
                            if not valid_chars: 
                                st.error("❌ Chuỗi đáp án bị lỗi! Chỉ được phép chứa các chữ A, B, C, D.")
                            else:
                                file_bytes = uploaded_file.read()
                                b64 = base64.b64encode(file_bytes).decode('utf-8')
                                mime_type = uploaded_file.type
                                s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                                e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                
                                c.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                          (exam_title.strip(), s_str, e_str, target_class, b64, mime_type, json.dumps(ans_clean)))
                                conn.commit()
                                st.success(f"✅ Đã phát đề thành công tới {target_class}! Hệ thống tự động tạo phiếu tô {len(ans_clean)} câu trắc nghiệm.")
                
                else:
                    if st.button("🚀 Phát Đề AI (Trộn Ngẫu Nhiên 40 Câu)", type="primary"):
                        if exam_title:
                            gen = ExamGenerator()
                            fixed_exam = gen.generate_all()
                            s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                            e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                            c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?, ?, ?, ?, ?)", 
                                      (exam_title.strip(), json.dumps(fixed_exam), s_str, e_str, target_class))
                            conn.commit()
                            st.success(f"✅ Đã phát đề AI chuẩn 40 câu tới {target_class}!")
                        else: st.error("Vui lòng nhập tên bài thi!")
        conn.close()

if __name__ == "__main__":
    main()
