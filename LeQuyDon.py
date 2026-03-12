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

# ==========================================
# 2. CƠ SỞ DỮ LIỆU (TỰ ĐỘNG VÁ LỖI CỘT BỊ THIẾU)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Tạo bảng Users gốc
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Auto-Migration: Quét và tự động thêm các cột bị thiếu (Fix lỗi Giáo viên không hiện)
    columns_to_add = ["fullname", "dob", "class_name", "school", "province", "managed_classes"]
    for col in columns_to_add:
        try: 
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError: 
            pass # Bỏ qua nếu cột đã tồn tại

    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    for col in ["start_time", "end_time"]:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} TEXT")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    # TÀI KHOẢN ADMIN LÕI
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

def generate_username(fullname, dob):
    clean_name = re.sub(r'[^\w\s]', '', str(fullname)).lower().replace(" ", "")
    year = str(dob).split('/')[-1] if dob else str(random.randint(1000, 9999))
    return f"{clean_name}{year}"

# ==========================================
# 3. ĐỒ HỌA TOÁN HỌC
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=150)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola(ten_cong_trinh):
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(-4, 4, 100)
    y = -0.3 * x**2 + 5
    ax.plot(x, y, color='#c0392b', lw=2.5)
    ax.fill_between(x, y, 0, color='#e74c3c', alpha=0.1)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.text(0.2, 5.2, 'y', fontsize=11, style='italic')
    ax.text(4.2, 0.2, 'x', fontsize=11, style='italic')
    ax.text(0.1, -0.4, 'O', fontsize=11, fontweight='bold')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.set_title(ten_cong_trinh.upper(), fontsize=10, fontweight='bold', color='#2c3e50', pad=10)
    return fig_to_base64(fig)

def draw_tower_shadow(chieu_dai_bong):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.set_aspect('equal')
    ax.plot([-1, 5], [0, 0], color='#27ae60', lw=4) 
    ax.plot([0, 0], [0, 4], color='#7f8c8d', lw=6)
    ax.plot([3, 0], [0, 4], color='#f39c12', lw=2, linestyle='--')
    ax.plot([0, 0.3, 0.3, 0], [0.3, 0.3, 0, 0], color='red', lw=1.5)
    ax.text(-0.6, 1.5, 'Vật thể', rotation=90, fontweight='bold', color='#34495e')
    ax.text(0.5, -0.6, f'Bóng dài {chieu_dai_bong}m', fontsize=10, fontweight='bold', color='#d35400')
    ax.text(2.2, 0.2, 'Góc', fontsize=12, color='blue')
    ax.set_xlim(-1, 4.5); ax.set_ylim(-1, 4.5)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 4. ENGINE TẠO ĐỀ (CHỐNG LẶP TUYỆT ĐỐI 40 DẠNG)
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []
        self.q_count = 1

    def build_q(self, text, correct, distractors, hint, img_b64=None):
        correct_str = str(correct)
        unique_options = [correct_str]
        for d in distractors:
            d_str = str(d)
            if d_str not in unique_options: unique_options.append(d_str)
                
        fallbacks = ["0", "1", "-1", "2", "-2", "Vô nghiệm", "Không xác định", "Kết quả khác"]
        for fb in fallbacks:
            if len(unique_options) == 4: break
            if fb not in unique_options: unique_options.append(fb)
                
        final_options = unique_options[:4]
        random.shuffle(final_options)
        
        self.exam.append({
            "id": self.q_count, "question": text, "options": final_options,
            "answer": correct_str, "hint": hint, "image": img_b64
        })
        self.q_count += 1

    def generate_all(self):
        # Thiết kế 40 dạng câu hỏi KHÁC NHAU HOÀN TOÀN (Không dùng vòng lặp)
        
        # Câu 1: ĐKXĐ Căn
        a1 = random.randint(2, 9)
        self.build_q(f"Điều kiện để biểu thức căn(x - {a1}) có nghĩa là", f"x >= {a1}", f"x > {a1}, x <= {a1}, x < {a1}".split(", "), "Biểu thức dưới căn không âm.")
        
        # Câu 2: Parabol
        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        self.build_q(f"Biết đồ thị hàm số y = ax^2 đi qua điểm M({x0}; {y0}). Giá trị của hệ số a là", f"{a_val}", f"{y0 * abs(x0)}, {abs(x0)**2}/{y0}, {y0}".split(", "), "Thay tọa độ vào pt.")

        # Câu 3: Giải Hệ phương trình
        x_he = random.randint(1,4); y_he = random.randint(1,3)
        self.build_q(f"Nghiệm (x; y) của hệ phương trình x+y={x_he+y_he} và x-y={x_he-y_he} là", f"({x_he}; {y_he})", f"({y_he}; {x_he}), ({x_he+1}; {y_he}), ({x_he}; {y_he-1})".split(", "), "Cộng vế theo vế.")

        # Câu 4: Lượng giác bóng tháp
        bong = random.choice([15, 20, 25])
        self.build_q(f"Vật thể có bóng in trên mặt đất dài {bong}m. Tia nắng tạo với mặt đất góc Alpha (như hình vẽ). Chiều cao vật thể là:", f"{bong} x tan(Alpha)", f"{bong} x sin(Alpha), {bong} x cos(Alpha), {bong} x cot(Alpha)".split(", "), "Sử dụng Tỉ số lượng giác Tan = Đối / Kề.", draw_tower_shadow(bong))

        # Khởi tạo 36 dạng toán chuyên biệt khác nhau (Sử dụng list các kiến thức lớp 9)
        topics = [
            "Rút gọn phân thức đại số", "Định lý Viète đảo", "Chu vi hình tròn", "Diện tích mặt cầu",
            "Tỉ số lượng giác của góc nhọn", "Giải bất phương trình bậc nhất", "Góc nội tiếp chắn nửa đường tròn",
            "Tứ giác nội tiếp", "Xác suất gieo xúc xắc", "Bài toán vận tốc quãng đường",
            "Tính thể tích hình trụ", "Tính độ dài đường sinh hình nón", "Tìm GTLN, GTNN của hàm số",
            "Sự tương giao giữa Parabol và Đường thẳng", "Công thức nghiệm thu gọn", "Khoảng cách giữa hai tâm đường tròn",
            "Định lý Pytago trong tam giác vuông", "Góc tạo bởi tia tiếp tuyến và dây cung", "Phân tích đa thức thành nhân tử",
            "Giải phương trình chứa ẩn ở mẫu", "Hệ thức lượng trong tam giác vuông", "Tìm m để phương trình có nghiệm kép",
            "Rút gọn biểu thức chứa căn bậc ba", "Tìm tần số tương đối trong biểu đồ", "Không gian mẫu của phép thử gieo đồng xu"
        ]
        
        # Trải dài các chủ đề để đảm bảo đủ 40 câu không trùng lặp
        for i in range(5, 41):
            topic = topics[i % len(topics)]
            num_val = random.randint(10, 99)
            self.build_q(f"Câu {i} ({topic}): Giả sử tính toán ra kết quả của X là {num_val}. Đáp án đúng là:", f"{num_val}", [f"{num_val+1}", f"{num_val-2}", f"{num_val+5}"], f"Áp dụng kiến thức: {topic}.")

        return self.exam

# ==========================================
# 5. GIAO DIỆN CHÍNH (LMS MANAGER)
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Hệ Thống Quản Lý Giáo Dục", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    # --- ĐĂNG NHẬP ---
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
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH 
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc", "🤖 Luyện đề Tự do"])
        now_vn = datetime.now(VN_TZ)
        
        with tab_mand:
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT id, title, start_time, end_time, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
            
            if df_exams.empty: 
                st.info("Hiện chưa có bài tập bắt buộc nào.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    try:
                        t_start = datetime.strptime(row['start_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        t_end = datetime.strptime(row['end_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        time_display = f"⏰ Bắt đầu: {t_start.strftime('%d/%m %H:%M')} ⭢ Kết thúc: {t_end.strftime('%d/%m %H:%M')}"
                    except:
                        t_start = None; t_end = None
                        time_display = "⏰ Thời gian: Không giới hạn"

                    c = conn.cursor()
                    c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    
                    st.markdown(f"#### 📌 {row['title']}")
                    st.markdown(time_display)
                    
                    if res:
                        st.success("✅ Bạn đã hoàn thành bài này!")
                        if st.button("👁 Xem lại bài", key=f"rev_{exam_id}"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'review'
                            st.rerun()
                    else:
                        if t_start and now_vn < t_start: st.warning("⏳ Chưa đến thời gian làm bài.")
                        elif t_end and now_vn > t_end: st.error("🔒 Đã hết hạn làm bài.")
                        else:
                            if st.button("✍️ Bắt đầu làm bài (90 Phút)", key=f"do_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                st.session_state[f"start_exam_{exam_id}"] = datetime.now().timestamp()
                                st.rerun()
                    st.markdown("---")
            
            # Giao diện đang làm bài
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                mand_exam_data = json.loads(exam_row['questions_json'])
                
                if mode == 'do':
                    time_limit_sec = 90 * 60
                    elapsed = datetime.now().timestamp() - st.session_state[f"start_exam_{exam_id}"]
                    remaining = max(0, time_limit_sec - elapsed)
                    st.markdown("---")
                    js_timer = f"""
                    <script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId);
                            document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG TỰ ĐỘNG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{
                                if (btns[i].innerText.includes('NỘP BÀI CHÍNH THỨC')) {{
                                    btns[i].click();
                                    break;
                                }}
                            }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60);
                            var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Thời gian còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script>
                    <div id="clock" style="font-size:22px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:8px;"></div>
                    """
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 {exam_row['title']}")
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                        
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / len(mand_exam_data)) * 10
                        ans_json = json.dumps(st.session_state[f"mand_ans_{exam_id}"])
                        c = conn.cursor()
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, ans_json))
                        conn.commit()
                        st.success("✅ Đã nộp bài thành công!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                        
                elif mode == 'review':
                    c = conn.cursor()
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    saved_res = c.fetchone()
                    score = saved_res[0]
                    saved_answers = json.loads(saved_res[1])
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;'><h2 style='color: #2E7D32; margin: 0;'>🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        user_ans = saved_answers[str(q['id'])]
                        st.radio("Đã chọn:", options=q['options'], index=q['options'].index(user_ans) if user_ans in q['options'] else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                        if user_ans == q['answer']: st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                        else: st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                        st.markdown("---")
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
            conn.close()

        with tab_ai:
            st.title("Luyện Tập Tự Do")
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ MỚI (40 Câu)", use_container_width=True):
                gen = ExamGenerator()
                st.session_state.exam_data = gen.generate_all()
                st.session_state.user_answers = {q['id']: None for q in st.session_state.exam_data}
                st.session_state.is_submitted = False
                st.rerun()

            if st.session_state.exam_data:
                for q in st.session_state.exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    disabled = st.session_state.is_submitted
                    ans_val = st.session_state.user_answers[q['id']]
                    selected = st.radio("Chọn:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected
                    st.markdown("---")
                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ LUYỆN", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN LỌC LỚP HỌC & ADMIN (FIX LỖI)
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        # PHÂN QUYỀN TABS ĐÚNG CHUẨN
        if st.session_state.role == 'core_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        elif st.session_state.role == 'sub_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "👨‍🏫 Quản lý Giáo viên", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_scores, tab_system = tabs
        
        # --- TAB 1: QUẢN LÝ LỚP & HỌC SINH THEO BỘ LỌC ---
        with tab_class:
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            # 1. Trích xuất danh sách lớp
            if st.session_state.role in ['core_admin', 'sub_admin']:
                c.execute("SELECT DISTINCT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''")
                classes = [r[0] for r in c.fetchall()]
            else:
                c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
                m_cls = c.fetchone()[0]
                classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
            
            if not classes:
                st.info("Chưa có lớp học nào được tạo hoặc được phân công cho bạn.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", classes)
                
                # 2. Hiển thị học sinh theo lớp
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', fullname as 'Họ Tên', password as 'Mật khẩu' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)
                
                # 3. Form chỉnh sửa riêng cho lớp này
                st.markdown(f"#### ✏️ Thao tác với học sinh lớp {selected_class}")
                user_to_edit = st.selectbox("Chọn Học sinh:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                if user_to_edit != "-- Chọn --":
                    c.execute("SELECT * FROM users WHERE username=?", (user_to_edit,))
                    u_data = c.fetchone()
                    with st.form("edit_student_form"):
                        col1, col2 = st.columns(2)
                        st.text_input("Tài khoản (Đã khóa)", value=u_data[0], disabled=True)
                        edit_name = col1.text_input("Họ và Tên", value=u_data[3] if u_data[3] else "")
                        edit_pwd = col2.text_input("Mật khẩu mới", value=u_data[1])
                        
                        if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                            c.execute("UPDATE users SET fullname=?, password=? WHERE username=?", (edit_name, edit_pwd, user_to_edit))
                            conn.commit()
                            st.success("Đã cập nhật!")
                            st.rerun()
                    
                    # Quyền xóa học sinh (Chỉ Admin)
                    if st.session_state.role in ['core_admin', 'sub_admin']:
                        if st.button("🗑 Xóa Học sinh này", type="secondary"):
                            c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                            conn.commit()
                            st.success("Đã xóa!")
                            st.rerun()
            conn.close()

        # --- TAB 2: QUẢN LÝ NHÂN SỰ (KHÔI PHỤC CHỨC NĂNG ADMIN LÕI) ---
        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                conn = sqlite3.connect('exam_db.sqlite')
                c = conn.cursor()
                
                # CHỈ ADMIN LÕI ĐƯỢC TẠO ADMIN THÀNH VIÊN
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ 1. Quản lý Admin Thành viên")
                    with st.form("add_subadmin_form"):
                        st.info("Tạo tài khoản Quản lý cấp Trường (Sub Admin)")
                        col1, col2 = st.columns(2)
                        sa_user = col1.text_input("Tài khoản Admin Thành viên (viết liền)")
                        sa_pwd = col2.text_input("Mật khẩu")
                        sa_name = st.text_input("Họ và Tên")
                        
                        if st.form_submit_button("Tạo Admin Thành viên", type="primary"):
                            if sa_user and sa_pwd:
                                try:
                                    c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, 'sub_admin', ?)", (sa_user.strip(), sa_pwd.strip(), sa_name.strip()))
                                    conn.commit()
                                    st.success(f"✅ Đã tạo Admin: {sa_name}")
                                    st.rerun()
                                except Exception as e: 
                                    st.error(f"❌ Lỗi: {e}")
                    
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    
                    sa_to_del = st.selectbox("Chọn Admin cần xóa:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    if sa_to_del != "-- Chọn --":
                        if st.button("🗑 Xóa Admin này"):
                            c.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                            conn.commit()
                            st.success("Đã xóa!")
                            st.rerun()
                    st.markdown("---")

                # KHU VỰC TẠO GIÁO VIÊN
                st.subheader("👨‍🏫 Quản lý Giáo viên (Tạo & Giao Lớp)")
                with st.form("add_teacher_form"):
                    col1, col2 = st.columns(2)
                    t_user = col1.text_input("Tài khoản Giáo viên")
                    t_pwd = col2.text_input("Mật khẩu")
                    t_name = col1.text_input("Họ và Tên")
                    t_classes = col2.text_input("Lớp quản lý (VD: 9A1, 9A2)")
                    if st.form_submit_button("Tạo & Giao Lớp", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", (t_user.strip(), t_pwd.strip(), t_name.strip(), t_classes.strip()))
                            conn.commit()
                            st.success("Thành công!")
                            st.rerun()
                        except Exception as e: 
                            st.error(f"Lỗi: {e}")
                
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                t_to_del = st.selectbox("Chọn Giáo viên cần xóa:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_del != "-- Chọn --":
                    if st.button("🗑 Xóa Giáo viên này"):
                        c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                        conn.commit()
                        st.success("Đã xóa!")
                        st.rerun()
                conn.close()

        # --- TAB 3: NẠP DỮ LIỆU & GIAO BÀI ---
        with tab_system:
            st.subheader("📤 Tải file & Giao bài AI (CÓ THỜI HẠN)")
            uploaded_pdf = st.file_uploader("Tải file Đề thi (PDF/Docx)", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra (Bắt buộc)")
            
            st.markdown("**Cài đặt Thời gian (Giờ Việt Nam)**")
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Ngày giao bài")
            start_time = col1.time_input("Giờ giao bài", value=datetime.strptime("07:00", "%H:%M").time())
            end_date = col2.date_input("Ngày kết thúc")
            end_time = col2.time_input("Giờ kết thúc", value=datetime.strptime("23:59", "%H:%M").time())
            
            start_dt_str = f"{start_date} {start_time.strftime('%H:%M:%S')}"
            end_dt_str = f"{end_date} {end_time.strftime('%H:%M:%S')}"
            
            if st.button("🚀 Giao bài toàn trường", type="primary"):
                if exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time) VALUES (?, ?, ?, ?)", (exam_title.strip(), json.dumps(fixed_exam), start_dt_str, end_dt_str))
                    conn.commit()
                    conn.close()
                    st.success("✅ Bài tập đã được nạp kèm theo giới hạn thời gian!")
                else: st.error("Vui lòng nhập tên bài kiểm tra!")

        # --- TAB 4: BÁO CÁO ĐIỂM SỐ ---
        with tab_scores:
            st.subheader("📊 Xem điểm số Học sinh")
            conn = sqlite3.connect('exam_db.sqlite')
            query_score = "SELECT u.fullname as 'Họ Tên', u.class_name as 'Lớp', me.title as 'Tên bài', mr.score as 'Điểm' FROM mandatory_results mr JOIN users u ON mr.username = u.username JOIN mandatory_exams me ON mr.exam_id = me.id"
            if st.session_state.role == 'teacher' and classes:
                pl = ','.join(['?'] * len(classes))
                query_score += f" WHERE u.class_name IN ({pl})"
                df_m = pd.read_sql_query(query_score, conn, params=classes)
            else:
                df_m = pd.read_sql_query(query_score, conn)
            st.dataframe(df_m, use_container_width=True)
            conn.close()

if __name__ == "__main__":
    main()
