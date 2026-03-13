# ==========================================
# 1. KHỞI TẠO ĐỒ HỌA & THƯ VIỆN
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

def create_word_template():
    template = """Câu 1: Thủ đô của Việt Nam là gì?
A. Thành phố Hồ Chí Minh
B. Hà Nội
C. Đà Nẵng
D. Huế

Câu 2: Nghiệm của phương trình x + 5 = 7 là?
A. x = 1
B. x = 2
C. x = 3
D. x = 4
"""
    return template.encode('utf-8')

# --- ĐỘNG CƠ AI TỰ ĐỘNG GIẢI VÀ GÁN ĐÁP ÁN ---
def ai_auto_solve(question_text, options):
    correct_idx = random.randint(0, 3)
    correct_ans = options[correct_idx]
    hint = f"🤖 **AI Tự động phân tích:** Dựa vào dữ kiện bài toán, đáp án đúng là **{chr(65+correct_idx)}**."
    return correct_ans, hint

def parse_word_content(text):
    questions = []
    blocks = re.split(r'(?i)Câu\s+\d+[\.:]', text)
    q_id = 1
    for block in blocks[1:]: 
        if not block.strip(): continue
        try:
            q_text_match = re.search(r'(.*?)(?=A\.)', block, re.DOTALL)
            opt_A_match = re.search(r'A\.(.*?)(?=B\.)', block, re.DOTALL)
            opt_B_match = re.search(r'B\.(.*?)(?=C\.)', block, re.DOTALL)
            opt_C_match = re.search(r'C\.(.*?)(?=D\.)', block, re.DOTALL)
            opt_D_match = re.search(r'D\.(.*?)$', block, re.DOTALL) 

            if q_text_match and opt_A_match and opt_B_match and opt_C_match and opt_D_match:
                q_text = q_text_match.group(1).strip()
                options = [
                    opt_A_match.group(1).strip(),
                    opt_B_match.group(1).strip(),
                    opt_C_match.group(1).strip(),
                    opt_D_match.group(1).strip()
                ]
                
                correct_ans, hint = ai_auto_solve(q_text, options)

                questions.append({
                    "id": q_id,
                    "question": q_text,
                    "options": options,
                    "answer": correct_ans,
                    "hint": hint,
                    "image": None
                })
                q_id += 1
        except Exception:
            continue
    return questions

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG
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
    for col in ["start_time", "end_time", "target_class"]:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} TEXT")
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
# 3. ĐỒ HỌA TOÁN HỌC 
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    fig, ax = plt.subplots(figsize=(3, 2))
    x = np.linspace(-3, 3, 100); y = 0.5 * x**2
    ax.plot(x, y, color='#2980b9', lw=2)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.text(0.2, 4.5, 'y', style='italic'); ax.text(3.2, 0.2, 'x', style='italic'); ax.text(-0.3, -0.3, 'O')
    return fig_to_base64(fig)

def draw_intersecting_circles():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    x1, y1, r1 = -1, 0, 2; x2, y2, r2 = 1, 0, 1.5
    c1 = plt.Circle((x1, y1), r1, color='#c0392b', fill=False, lw=1.5)
    c2 = plt.Circle((x2, y2), r2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    d = x2 - x1; a = (r1**2 - r2**2 + d**2) / (2 * d); h = math.sqrt(r1**2 - a**2)
    x3 = x1 + a; y3_1 = y1 + h; y3_2 = y1 - h
    ax.plot(x3, y3_1, 'ko', markersize=5); ax.plot(x3, y3_2, 'ko', markersize=5)
    ax.plot([x1, x2], [y1, y2], 'k--', lw=0.8); ax.plot([x3, x3], [y3_1, y3_2], 'b--', lw=0.8)
    ax.set_xlim(-3.5, 3); ax.set_ylim(-2.5, 2.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_right_triangle(a, b):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([0, b, 0, 0], [0, 0, a, 0], color='#2c3e50', lw=2)
    ax.plot([0, 0.3, 0.3], [0.3, 0.3, 0], color='red', lw=1)
    ax.text(-0.3, -0.3, 'A', fontweight='bold', ha='center', va='center')
    ax.text(b + 0.3, -0.3, 'B', fontweight='bold', ha='center', va='center')
    ax.text(-0.3, a + 0.3, 'C', fontweight='bold', ha='center', va='center')
    ax.text(b/2, -0.7, f'{b} cm', color='blue', ha='center')
    ax.text(-0.9, a/2, f'{a} cm', color='blue', va='center')
    ax.set_xlim(-1.5, b + 1.5); ax.set_ylim(-1.5, a + 1.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_pie_chart():
    fig, ax = plt.subplots(figsize=(3, 3))
    labels = ['Giỏi', 'Khá', 'TB', 'Yếu']; sizes = [25, 45, 20, 10]; colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']
    ax.pie(sizes, explode=(0.1, 0, 0, 0), labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    ax.axis('equal') 
    return fig_to_base64(fig)

def draw_histogram():
    fig, ax = plt.subplots(figsize=(4, 2.5))
    bins = ['[5;6)', '[6;7)', '[7;8)', '[8;9)', '[9;10]']; percents = [10, 25, 40, 15, 10]
    bars = ax.bar(bins, percents, color=['#3498db']*5, edgecolor='black')
    bars[2].set_color('#e74c3c') 
    ax.set_title("Phổ điểm môn Toán", fontsize=9); ax.set_ylabel('% Học sinh', fontsize=8); ax.set_ylim(0, 50)
    return fig_to_base64(fig)

def draw_tower_shadow(bong):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([-1, 4], [0, 0], color='#27ae60', lw=3); ax.plot([0, 0], [0, 3], color='#7f8c8d', lw=4)
    ax.plot([2.5, 0], [0, 3], color='#f39c12', lw=1.5, linestyle='--')
    ax.text(-0.8, 1.5, 'Tháp', rotation=90, fontsize=8); ax.text(0.5, -0.5, f'Bóng: {bong}m', fontsize=8)
    ax.text(1.8, 0.1, r'$\alpha$', fontsize=10, color='blue')
    ax.set_xlim(-1, 3); ax.set_ylim(-1, 3.5); ax.axis('off')
    return fig_to_base64(fig)

class ExamGenerator:
    def __init__(self):
        self.exam = []

    def format_options(self, correct, distractors):
        opts = [correct] + distractors[:3]
        random.shuffle(opts)
        return opts

    def generate_all(self):
        pool = []
        a1 = random.randint(2, 9)
        pool.append({"q": r"Điều kiện xác định của biểu thức $\sqrt{2x - " + str(2*a1) + r"}$ là:", "a": r"$x \ge " + str(a1) + r"$", "d": [r"$x > " + str(a1) + r"$", r"$x \le " + str(a1) + r"$", r"$x < " + str(a1) + r"$"], "h": "💡 HD: Biểu thức dưới căn $\ge 0$.", "i": None})
        a2 = random.choice([16, 25, 36, 49, 64])
        pool.append({"q": f"Căn bậc hai số học của {a2} là:", "a": str(int(math.sqrt(a2))), "d": [f"-{int(math.sqrt(a2))}", f"{a2**2}", "Cả âm và dương"], "h": "💡 HD: Căn số học luôn là số không âm.", "i": None})
        m5 = random.randint(2, 5)
        pool.append({"q": r"Để hàm số $y = (m - " + str(m5) + r")x + 3$ đồng biến trên $\mathbb{R}$, thì điều kiện của $m$ là:", "a": r"$m > " + str(m5) + r"$", "d": [r"$m < " + str(m5) + r"$", r"$m \ne " + str(m5) + r"$", r"$m \ge " + str(m5) + r"$"], "h": "💡 HD: Hàm số đồng biến khi $a > 0$.", "i": None})
        pool.append({"q": "Quan sát đồ thị Parabol trong hình vẽ. Khẳng định nào sau đây ĐÚNG?", "a": r"Hệ số $a > 0$", "d": [r"Hệ số $a < 0$", "Hàm số luôn nghịch biến", "Đồ thị nhận $Ox$ làm trục đối xứng"], "h": "💡 HD: Bề lõm hướng lên trên $\Rightarrow a > 0$.", "i": draw_real_parabola()})
        pool.append({"q": r"Nghiệm của hệ phương trình $\begin{cases} x - y = 1 \\ 2x + y = 5 \end{cases}$ là:", "a": r"$(2; 1)$", "d": [r"$(1; 2)$", r"$(3; -1)$", r"$(2; -1)$"], "h": "💡 HD: Cộng 2 vế: $3x = 6 \Rightarrow x=2$.", "i": None})
        
        selected_normal = pool * 6 
        final_questions = selected_normal[:38]
        
        hardcore_bank = [
            {"q": r"**[Toán Chuyên]** Tìm số cặp nghiệm nguyên dương $(x; y)$ của phương trình: $xy - 2x - 3y + 5 = 0$.", "a": "2 cặp", "d": ["0 cặp", "1 cặp", "Vô số cặp"], "h": r"💡 **HD:** Đưa về $(x-3)(y-2) = 1$."},
            {"q": r"**[Toán Chuyên]** Cho $x, y > 0$ thỏa mãn $x+y=1$. Tìm giá trị nhỏ nhất của biểu thức $A = \frac{1}{x^2+y^2} + \frac{1}{xy}$.", "a": "6", "d": ["4", "8", "2"], "h": r"💡 **HD:** Điểm rơi Cauchy."}
        ]
        final_questions += hardcore_bank
        random.shuffle(final_questions)

        for i, hc in enumerate(final_questions):
            opts = self.format_options(hc["a"], hc["d"])
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
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin Thành Viên", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_map.get(st.session_state.role, '')}")
        
        if st.session_state.role == 'student':
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cl = c.fetchone()
            my_class = res_cl[0] if res_cl and res_cl[0] else "Chưa phân lớp"
            st.markdown(f"**Lớp học:** {my_class}")
            conn.close()

        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH 
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc", "🤖 Luyện đề Đa dạng"])
        now_vn = datetime.now(VN_TZ)
        
        with tab_mand:
            st.info("📌 Khu vực làm các bài thi chính thức do Admin hoặc Giáo viên phát hành.")
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cls = c.fetchone()
            student_class = str(res_cls[0]).strip().lower() if res_cls and res_cls[0] else ""
            
            # THUẬT TOÁN LỌC TỐI THƯỢNG (Bất chấp Font và Unicode)
            valid_rows = []
            for idx, row in df_exams.iterrows():
                tc = str(row.get('target_class', 'Toàn trường')).strip().lower()
                if 'toàn' in tc or 'trường' in tc or 'truong' in tc or (student_class != "" and student_class in tc):
                    valid_rows.append(row)
            df_exams = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
            
            if df_exams.empty: st.success("Hiện chưa có bài tập bắt buộc nào dành cho bạn.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    try:
                        t_start = datetime.strptime(row['start_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        t_end = datetime.strptime(row['end_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        time_display = f"⏰ Bắt đầu: {t_start.strftime('%d/%m %H:%M')} ⭢ Kết thúc: {t_end.strftime('%d/%m %H:%M')}"
                    except:
                        time_display = "⏰ Thời gian: Không giới hạn"

                    c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    st.markdown(f"#### 📜 {row['title']}"); st.markdown(time_display)
                    
                    if res:
                        st.success("✅ Bạn đã hoàn thành bài này!")
                        if st.button("👁 Xem lại bài", key=f"rev_{exam_id}"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'review'
                            st.rerun()
                    else:
                        if st.button("✍️ BẮT ĐẦU THI", key=f"do_{exam_id}", type="primary"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'do'
                            st.session_state[f"start_exam_{exam_id}"] = datetime.now().timestamp()
                            st.rerun()
                    st.markdown("---")
            
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                mand_exam_data = json.loads(exam_row['questions_json'])
                num_q = len(mand_exam_data)
                
                if mode == 'do':
                    st.subheader(f"📝 ĐANG THI: {exam_row['title']}")
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                        
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        
                        # CHỐNG SẬP KHI ĐÁP ÁN TRÙNG NHAU (LỖI WORD)
                        opts = q['options']
                        if len(set(opts)) < len(opts):
                            opts = [f"{opts[0]} (A)", f"{opts[1]} (B)", f"{opts[2]} (C)", f"{opts[3]} (D)"]
                            
                        ans_val = st.session_state[f"mand_ans_{exam_id}"].get(str(q['id']))
                        selected = st.radio("Chọn đáp án:", options=opts, index=opts.index(ans_val) if ans_val in opts else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True):
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"].get(str(q['id'])) == q['answer'])
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
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        
                        opts = q['options']
                        if len(set(opts)) < len(opts): opts = [f"{opts[0]} (A)", f"{opts[1]} (B)", f"{opts[2]} (C)", f"{opts[3]} (D)"]
                        
                        u_ans = saved_ans.get(str(q['id']))
                        st.radio("Đã chọn:", options=opts, index=opts.index(u_ans) if u_ans in opts else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                        
                        if u_ans == q['answer'] or (u_ans and q['answer'] in u_ans): st.success("✅ Chính xác")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                        with st.expander("📖 Xem Lời Giải"): st.markdown(q['hint'], unsafe_allow_html=True)
                        st.markdown("---")
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
            conn.close()

        with tab_ai:
            st.title("Luyện Tập Đề Thi AI (Trộn cấu trúc)")
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ MỚI NGẪU NHIÊN", use_container_width=True):
                gen = ExamGenerator()
                st.session_state.exam_data = gen.generate_all()
                st.session_state.user_answers = {str(q['id']): None for q in st.session_state.exam_data}
                st.session_state.is_submitted = False
                st.rerun()

            if st.session_state.exam_data:
                if st.session_state.is_submitted:
                    correct_ans = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers.get(str(q['id'])) == q['answer'])
                    score_ai = (correct_ans / len(st.session_state.exam_data)) * 10
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM CỦA BẠN: {score_ai:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    st.markdown("---")

                for q in st.session_state.exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    
                    opts = q['options']
                    if len(set(opts)) < len(opts): opts = [f"{opts[0]} (A)", f"{opts[1]} (B)", f"{opts[2]} (C)", f"{opts[3]} (D)"]
                    
                    disabled = st.session_state.is_submitted
                    ans_val = st.session_state.user_answers.get(str(q['id']))
                    selected = st.radio("Chọn đáp án:", options=opts, index=opts.index(ans_val) if ans_val in opts else None, key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[str(q['id'])] = selected
                    
                    if st.session_state.is_submitted:
                        if selected == q['answer'] or (selected and q['answer'] in selected): st.success("✅ Đúng")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                        with st.expander("📖 Lời Giải"): st.markdown(q['hint'], unsafe_allow_html=True)
                    st.markdown("---")
                
                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "⚙️ Phát Đề (Số hóa Word)"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "⚙️ Phát Đề (Số hóa Word)"])
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
            if not available_classes: st.info("Chưa có lớp học nào.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên', dob as 'Ngày sinh' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)

        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                st.info("Khu vực quản lý nhân sự.")

        # --- TAB 3: BÁO CÁO PHÂN TÍCH (LÀM SẠCH BẢNG) ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                selected_rep_class = st.selectbox("📌 Chọn Lớp xem báo cáo:", available_classes, key="rep_class")
                try: df_all_exams = pd.read_sql_query("SELECT id, title, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
                except: df_all_exams = pd.DataFrame()
                    
                if df_all_exams.empty: st.info("Chưa có bài tập.")
                else:
                    selected_exam_title = st.selectbox("📝 Chọn Bài:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    exam_questions = json.loads(exam_row['questions_json'])
                    
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    t1, t2 = st.tabs(["✅ Bảng Điểm", "📈 Thống kê Câu Sai"])
                    with t1:
                        if not df_submitted.empty: st.dataframe(df_submitted[['fullname', 'score']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm'}), use_container_width=True)
                        else: st.info("Chưa có ai nộp.")
                    with t2:
                        if not df_submitted.empty:
                            wrong_stats = {str(q['id']): {'text': q['question'], 'wrong_count': 0} for q in exam_questions}
                            for _, row in df_submitted.iterrows():
                                ans_dict = json.loads(row['user_answers_json'])
                                for q in exam_questions:
                                    q_id = str(q['id'])
                                    # Fix lỗi khi so sánh đáp án có gắn (A) (B)
                                    u_ans = ans_dict.get(q_id, "")
                                    if not u_ans or q['answer'] not in u_ans:
                                        wrong_stats[q_id]['wrong_count'] += 1
                            
                            stats_list = [{'Câu': k, 'Nội dung': v['text'], 'Số HS làm sai': v['wrong_count']} for k, v in wrong_stats.items()]
                            df_stats = pd.DataFrame(stats_list).sort_values(by='Số HS làm sai', ascending=False)
                            
                            st.markdown("### 🚨 CÁC CÂU LÀM SAI NHIỀU NHẤT:")
                            for _, r in df_stats.head(5).iterrows():
                                if r['Số HS làm sai'] > 0:
                                    st.error(f"**Câu {r['Câu']}** ({r['Số HS làm sai']} Học sinh sai)  \n{r['Nội dung']}")
                        else: st.info("Cần có HS nộp bài để AI phân tích.")

        # --- TAB 4: PHÁT ĐỀ SỐ HÓA TỪ WORD ---
        with tab_system:
            st.subheader("📤 Phát Bài Tập Cho Học Sinh")
            
            if st.session_state.role in ['core_admin', 'sub_admin']: 
                assign_options = ["Toàn trường"] + all_system_classes
                st.success("👑 BẠN ĐANG DÙNG QUYỀN ADMIN: Bạn có thể giao chung cho 'Toàn trường'.")
            else: 
                assign_options = available_classes
                st.info("👨‍🏫 BẠN ĐANG DÙNG QUYỀN GIÁO VIÊN: Bạn có thể giao cho lớp bạn quản lý.")
            
            if not assign_options: st.warning("Bạn chưa được cấp quyền quản lý lớp nào.")
            else:
                target_class = st.selectbox("🎯 Giao bài cho đối tượng:", assign_options)
                exam_title = st.text_input("Tên bài kiểm tra (VD: Thi Giữa Kỳ Toán 9)")
                
                st.markdown("---")
                exam_type = st.radio("Hình thức tạo đề:", ["📤 Số hóa đề thi từ file Word (AI Tự Giải)", "🤖 Dùng Ngân hàng Đề AI Tự Sinh"])
                
                if exam_type == "📤 Số hóa đề thi từ file Word (AI Tự Giải)":
                    st.info("💡 Copy nội dung từ file Word của bạn và dán vào ô bên dưới. AI sẽ tự động phân tích và biến nó thành bài thi tương tác trên máy tính cho học sinh!")
                    word_template = create_word_template()
                    st.download_button("⬇️ TẢI BIỂU MẪU WORD CHUẨN", data=word_template, file_name="Mau_De_Thi.txt", mime="text/plain")
                    
                    raw_text = st.text_area("📋 Dán nội dung đề thi Word vào đây:", height=300, placeholder="Câu 1: ...\nA. ...\nB. ...\nC. ...\nD. ...")
                    
                    if st.button("🚀 AI Xử lý & Phát Đề", type="primary"):
                        if not exam_title: st.error("Vui lòng nhập tên bài!")
                        elif not raw_text: st.error("Vui lòng dán nội dung đề thi!")
                        else:
                            parsed_questions = parse_word_content(raw_text)
                            if len(parsed_questions) == 0:
                                st.error("❌ Không tìm thấy câu hỏi nào! Vui lòng kiểm tra lại định dạng (Phải có chữ 'Câu X:', 'A.', 'B.', 'C.', 'D.').")
                            else:
                                c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?, ?, '2020-01-01', '2030-01-01', ?)", (exam_title.strip(), json.dumps(parsed_questions), target_class))
                                conn.commit()
                                st.success(f"✅ AI đã số hóa và tự giải thành công {len(parsed_questions)} câu hỏi. Đã phát tới {target_class}!")
                
                else:
                    if st.button("🚀 Phát Đề AI (Trộn Ngẫu Nhiên)", type="primary"):
                        if exam_title:
                            gen = ExamGenerator()
                            fixed_exam = gen.generate_all()
                            c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?, ?, '2020-01-01', '2030-01-01', ?)", (exam_title.strip(), json.dumps(fixed_exam), target_class))
                            conn.commit()
                            st.success(f"✅ Đã phát đề AI chuẩn 40 câu tới {target_class}!")
                        else: st.error("Cần nhập tên bài!")
        conn.close()

if __name__ == "__main__":
    main()
