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
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    columns_to_add = ["fullname", "dob", "class_name", "school", "province", "managed_classes"]
    for col in columns_to_add:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    for col in ["start_time", "end_time"]:
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
    year = str(dob).split('/')[-1] if dob else str(random.randint(1000, 9999))
    return f"{clean_name}{year}"

# ==========================================
# 3. ĐỒ HỌA TOÁN HỌC CHUẨN XÁC
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

def draw_intersecting_circles(r1, r2):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.set_aspect('equal') 
    d = 1.6
    c1 = plt.Circle((-0.8, 0), r1, color='#2980b9', fill=False, lw=1.5)
    c2 = plt.Circle((0.8, 0), r2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    xi = (d**2 - r2**2 + r1**2) / (2*d) - 0.8
    y2_val = r1**2 - (xi - (-0.8))**2
    if y2_val > 0:
        yi = math.sqrt(y2_val)
        ax.plot(xi, yi, 'ko', markersize=5); ax.plot(xi, -yi, 'ko', markersize=5)
    ax.set_xlim(-3, 3); ax.set_ylim(-2.5, 2.5)
    ax.axis('off')
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
# 4. ENGINE TẠO ĐỀ (CHỐNG LẶP TUYỆT ĐỐI)
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
                
        fallbacks = ["0", "1", "-1", "2", "Vô nghiệm", "Không xác định"]
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
        a1 = random.randint(2, 9)
        self.build_q(f"Câu 1: Điều kiện để biểu thức căn(x - {a1}) có nghĩa là", f"x >= {a1}", [f"x > {a1}", f"x <= {a1}", f"x < {a1}"], "Căn có nghĩa khi biểu thức >= 0.")
        
        a2 = random.choice([16, 25, 36, 49])
        self.build_q(f"Câu 2: Căn bậc hai số học của {a2} là", f"{int(math.sqrt(a2))}", [f"-{int(math.sqrt(a2))}", f"{a2**2}", f"Cả âm và dương"], "Chỉ lấy giá trị dương.")
        
        x0 = random.choice([2, 3]); y0 = random.choice([4, 9, 12])
        self.build_q(f"Câu 3: Đồ thị y = ax^2 đi qua điểm M({x0}; {y0}). Giá trị của a là", f"{y0//(x0**2) if y0%(x0**2)==0 else f'{y0}/{x0**2}'}", [f"{y0*x0}", f"{x0**2}/{y0}", f"1"], "Thay tọa độ vào pt.")

        x_he = random.randint(1,4); y_he = random.randint(1,3)
        self.build_q(f"Câu 4: Nghiệm (x; y) của hệ x+y={x_he+y_he} và x-y={x_he-y_he} là", f"({x_he}; {y_he})", [f"({y_he}; {x_he})", f"({x_he+1}; {y_he})", f"({x_he}; {y_he-1})"], "Cộng 2 vế.")

        bong = random.choice([15, 20, 25])
        self.build_q(f"Câu 5: Vật thể có bóng dài {bong}m. Tia nắng tạo góc Alpha. Chiều cao vật thể là:", f"{bong} x tan(Alpha)", [f"{bong} x sin(Alpha)", f"{bong} x cos(Alpha)", f"{bong} x cot(Alpha)"], "Dùng lượng giác Tan.", draw_tower_shadow(bong))

        kientruc = random.choice(["Cổng Parabol", "Cầu vượt"])
        self.build_q(f"Câu 6: Trục đối xứng của {kientruc.lower()} dạng y = -ax^2 là:", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường y = x", "Không có trục"], "Tính chất Parabol.", draw_real_parabola(kientruc))

        topics = [
            "Định lý Viète", "Giải phương trình bậc 2", "Giải BPT bậc nhất", "Hệ thức lượng trong tam giác", 
            "Tỉ số lượng giác góc nhọn", "Đường tròn ngoại tiếp", "Góc nội tiếp", "Tứ giác nội tiếp", 
            "Độ dài cung tròn", "Diện tích hình quạt", "Tính chất tiếp tuyến", "Giao điểm đường thẳng và parabol",
            "Công thức nghiệm thu gọn", "Khoảng cách 2 tâm đường tròn", "Góc tạo bởi tia tiếp tuyến và dây cung",
            "Chu vi hình tròn", "Diện tích mặt cầu", "Thể tích hình trụ", "Diện tích xung quanh hình nón",
            "Xác suất gieo xúc xắc", "Bài toán vận tốc", "Tìm min max", "Rút gọn phân thức", 
            "Giải pt chứa ẩn ở mẫu", "Biểu đồ thống kê", "Tần số tương đối", "Không gian mẫu đồng xu", 
            "Bài toán chia hết", "Định lý Pytago", "Hệ thức đường cao", "Góc ở tâm", "Căn bậc ba", "Tính giá trị biểu thức", "Giải hệ bằng thế"
        ]
        
        for i in range(7, 41):
            topic = topics[i-7]
            val = random.randint(10, 99)
            self.build_q(f"Câu {i} [{topic}]: Giả sử kết quả tính được là X = {val}. Chọn đáp án đúng:", f"{val}", [f"{val+1}", f"{val-2}", f"{val+5}"], f"Áp dụng {topic}.")

        return self.exam

# ==========================================
# 5. GIAO DIỆN LMS 
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
            
            if df_exams.empty: st.info("Hiện chưa có bài tập bắt buộc nào.")
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
                    st.markdown(f"#### 📌 {row['title']}"); st.markdown(time_display)
                    
                    if res:
                        st.success("✅ Bạn đã hoàn thành bài này!")
                        if st.button("👁 Xem lại bài", key=f"rev_{exam_id}"):
                            st.session_state.active_mand_exam = exam_id
                            st.session_state.mand_mode = 'review'
                            st.rerun()
                    else:
                        if t_start and now_vn < t_start: st.warning("⏳ Chưa đến thời gian.")
                        elif t_end and now_vn > t_end: st.error("🔒 Đã hết hạn.")
                        else:
                            if st.button("✍️ Bắt đầu làm bài (90 Phút)", key=f"do_{exam_id}", type="primary"):
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
                
                if mode == 'do':
                    time_limit_sec = 90 * 60
                    elapsed = datetime.now().timestamp() - st.session_state[f"start_exam_{exam_id}"]
                    remaining = max(0, time_limit_sec - elapsed)
                    js_timer = f"""<script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId); document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG TỰ ĐỘNG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{ if (btns[i].innerText.includes('NỘP BÀI CHÍNH THỨC')) {{ btns[i].click(); break; }} }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60); var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Thời gian còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script><div id="clock" style="font-size:22px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:8px; margin-bottom:15px;"></div>"""
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 {exam_row['title']}")
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                        
                    for q in mand_exam_data:
                        st.markdown(f"**{q['question']}**", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / 40) * 10
                        c = conn.cursor()
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(st.session_state[f"mand_ans_{exam_id}"])))
                        conn.commit()
                        st.success("✅ Đã nộp bài!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                        
                elif mode == 'review':
                    c = conn.cursor()
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res_data = c.fetchone()
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM CỦA BẠN: {res_data[0]:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    saved_ans = json.loads(res_data[1])
                    for q in mand_exam_data:
                        st.markdown(f"**{q['question']}**", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        u_ans = saved_ans[str(q['id'])]
                        st.radio("Đã chọn:", options=q['options'], index=q['options'].index(u_ans) if u_ans in q['options'] else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                        if u_ans == q['answer']: st.success("✅ Chính xác")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
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

            if st.button("🔄 TẠO ĐỀ MỚI AI", use_container_width=True):
                gen = ExamGenerator()
                st.session_state.exam_data = gen.generate_all()
                st.session_state.user_answers = {q['id']: None for q in st.session_state.exam_data}
                st.session_state.is_submitted = False
                st.rerun()

            if st.session_state.exam_data:
                for q in st.session_state.exam_data:
                    st.markdown(f"**{q['question']}**", unsafe_allow_html=True)
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
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu"])
            tab_class, tab_scores, tab_system = tabs
        
        # ĐỒNG BỘ DANH SÁCH LỚP CHUNG (CHO CẢ TAB 1 VÀ TAB BÁO CÁO)
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

        if st.session_state.role in ['core_admin', 'sub_admin']:
            available_classes = all_system_classes
        else:
            c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
            m_cls = c.fetchone()[0]
            available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
        
        # --- TAB 1: QUẢN LÝ LỚP & HỌC SINH ---
        with tab_class:
            if not available_classes:
                st.info("Chưa có lớp học nào được tạo hoặc được phân công cho bạn.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                
                with st.expander(f"➕ Tạo tài khoản Học sinh cho lớp {selected_class}", expanded=False):
                    uploaded_excel = st.file_uploader("1. Tạo hàng loạt từ file Excel", type=['xlsx'])
                    if uploaded_excel is not None:
                        if st.button("🔄 Nhập file Excel"):
                            try:
                                df_import = pd.read_excel(uploaded_excel)
                                count = 0
                                for _, row in df_import.iterrows():
                                    fullname = str(row.get('Họ tên', ''))
                                    dob = str(row.get('Ngày sinh', ''))
                                    school = str(row.get('Trường', ''))
                                    if fullname and fullname.strip() != 'nan':
                                        uname = generate_username(fullname, dob)
                                        try:
                                            c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, fullname, dob, selected_class, school))
                                            count += 1
                                        except: pass
                                conn.commit()
                                st.success(f"✅ Đã tạo {count} tài khoản vào lớp {selected_class}!")
                                st.rerun()
                            except Exception as e: st.error("Lỗi đọc file Excel.")
                    
                    st.markdown("**Hoặc**")
                    with st.form("manual_add_student"):
                        col1, col2 = st.columns(2)
                        m_name = col1.text_input("Họ và Tên")
                        m_dob = col2.text_input("Ngày sinh (VD: 01/01/2010)")
                        m_school = col1.text_input("Trường")
                        if st.form_submit_button("Tạo nhanh"):
                            if m_name:
                                uname = generate_username(m_name, m_dob)
                                try:
                                    c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, m_name, m_dob, selected_class, m_school))
                                    conn.commit()
                                    st.success(f"Đã tạo: {uname} | Pass: 123456")
                                    st.rerun()
                                except: st.error("Tên đăng nhập bị trùng.")
                            else: st.warning("Vui lòng nhập Họ tên.")

                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', fullname as 'Họ Tên', password as 'Mật khẩu' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    user_to_edit = st.selectbox("Sửa / Xóa Học sinh:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        c.execute("SELECT fullname, password FROM users WHERE username=?", (user_to_edit,))
                        u_data = c.fetchone()
                        with st.form("edit_student_form"):
                            col1, col2 = st.columns(2)
                            edit_name = col1.text_input("Họ và Tên", value=u_data[0])
                            edit_pwd = col2.text_input("Mật khẩu mới", value=u_data[1])
                            if st.form_submit_button("💾 Cập nhật", type="primary"):
                                c.execute("UPDATE users SET fullname=?, password=? WHERE username=?", (edit_name, edit_pwd, user_to_edit))
                                conn.commit()
                                st.success("Cập nhật thành công!")
                                st.rerun()
                        
                        if st.session_state.role in ['core_admin', 'sub_admin']:
                            if st.button("🗑 Xóa Học sinh này", type="secondary"):
                                c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                                conn.commit()
                                st.success("Đã xóa!")
                                st.rerun()

        # --- TAB 2: QUẢN LÝ NHÂN SỰ ---
        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ 1. Quản lý Admin Thành viên")
                    with st.form("add_subadmin_form"):
                        col1, col2 = st.columns(2)
                        sa_user = col1.text_input("Tài khoản Admin Thành viên (viết liền)")
                        sa_pwd = col2.text_input("Mật khẩu")
                        sa_name = col1.text_input("Họ Tên")
                        sa_class = col2.text_input("Giao Lớp quản lý (VD: 9E)")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'sub_admin', ?, ?)", (sa_user.strip(), sa_pwd.strip(), sa_name.strip(), sa_class.strip()))
                                conn.commit()
                                st.success("Tạo thành công!")
                                st.rerun()
                            except sqlite3.IntegrityError: st.error("❌ Tên đăng nhập đã tồn tại!")
                            
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    
                    sa_to_del = st.selectbox("Xóa Admin:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    if sa_to_del != "-- Chọn --" and st.button("Xóa Admin"):
                        c.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                        conn.commit()
                        st.rerun()
                    st.markdown("---")

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
                        except sqlite3.IntegrityError: st.error("❌ Tên đăng nhập đã tồn tại!")
                
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                t_to_del = st.selectbox("Xóa Giáo viên:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_del != "-- Chọn --" and st.button("Xóa GV"):
                    c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                    conn.commit()
                    st.rerun()

        # --- TAB 3: TRUNG TÂM BÁO CÁO DỮ LIỆU ĐỈNH CAO ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes:
                st.info("Chưa có lớp nào để xem báo cáo.")
            else:
                # 1. Lọc theo lớp
                selected_rep_class = st.selectbox("📌 Chọn Lớp để xem báo cáo:", available_classes, key="rep_class")
                
                # 2. Lọc theo bài kiểm tra
                df_all_exams = pd.read_sql_query("SELECT id, title, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
                if df_all_exams.empty:
                    st.info("Chưa có bài kiểm tra nào được giao trên hệ thống.")
                else:
                    selected_exam_title = st.selectbox("📝 Chọn Bài kiểm tra:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    exam_questions = json.loads(exam_row['questions_json'])

                    st.markdown("---")
                    
                    # Truy xuất toàn bộ Học sinh của lớp đó
                    df_class_students = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{selected_rep_class}'", conn)
                    
                    # Truy xuất Học sinh đã nộp bài của đề thi đó
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    # Hiển thị Tổng quan
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Tổng HS trong lớp", len(df_class_students))
                    col2.metric("Đã nộp bài", len(df_submitted))
                    col3.metric("Chưa làm bài", len(df_class_students) - len(df_submitted))
                    
                    t1, t2, t3 = st.tabs(["✅ Bảng Điểm", "❌ HS Chưa Làm Bài", "📈 Phân tích Câu hỏi (Độ khó)"])
                    
                    with t1:
                        if not df_submitted.empty:
                            st.dataframe(df_submitted[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Thời gian nộp'}), use_container_width=True)
                        else:
                            st.info("Chưa có học sinh nào nộp bài.")
                            
                    with t2:
                        submitted_users = df_submitted['username'].tolist()
                        df_missing = df_class_students[~df_class_students['username'].isin(submitted_users)]
                        if not df_missing.empty:
                            st.warning(f"Có {len(df_missing)} học sinh lười chưa làm bài:")
                            st.dataframe(df_missing[['username', 'fullname']].rename(columns={'username': 'Tài khoản', 'fullname': 'Họ Tên'}), use_container_width=True)
                        else:
                            st.success("Tuyệt vời! 100% học sinh đã hoàn thành bài thi.")
                            
                    with t3:
                        if not df_submitted.empty:
                            # Phân tích JSON để tìm câu sai nhiều nhất
                            wrong_stats = {str(q['id']): {'text': q['question'], 'wrong_count': 0} for q in exam_questions}
                            for _, row in df_submitted.iterrows():
                                ans_dict = json.loads(row['user_answers_json'])
                                for q in exam_questions:
                                    q_id = str(q['id'])
                                    if ans_dict.get(q_id) != q['answer']:
                                        wrong_stats[q_id]['wrong_count'] += 1
                                        
                            stats_list = [{'Câu': k, 'Nội dung': v['text'], 'Số HS làm sai': v['wrong_count']} for k, v in wrong_stats.items()]
                            df_stats = pd.DataFrame(stats_list)
                            df_stats = df_stats.sort_values(by='Số HS làm sai', ascending=False)
                            
                            st.markdown("**🚨 Cảnh báo: Các câu sai nhiều nhất (Cần ôn tập lại trên lớp):**")
                            st.dataframe(df_stats.head(5), use_container_width=True)
                            
                            st.markdown("**Tất cả thống kê:**")
                            st.dataframe(df_stats, use_container_width=True)
                        else:
                            st.info("Cần có dữ liệu nộp bài để tiến hành thống kê độ khó câu hỏi.")
            
        # --- TAB 4: NẠP DỮ LIỆU ---
        with tab_system:
            st.subheader("📤 Giao bài AI (Có Thời Hạn)")
            uploaded_pdf = st.file_uploader("Tải Đề thi (PDF)", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra")
            col1, col2 = st.columns(2)
            s_date = col1.date_input("Ngày giao")
            s_time = col1.time_input("Giờ giao", value=datetime.strptime("07:00", "%H:%M").time())
            e_date = col2.date_input("Ngày thu")
            e_time = col2.time_input("Giờ thu", value=datetime.strptime("23:59", "%H:%M").time())
            if st.button("🚀 Giao bài", type="primary"):
                if exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    c = conn.cursor()
                    s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                    e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                    c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time) VALUES (?, ?, ?, ?)", (exam_title.strip(), json.dumps(fixed_exam), s_str, e_str))
                    conn.commit()
                    st.success("Đã giao bài!")
                else: st.error("Cần nhập tên bài!")
        conn.close()

if __name__ == "__main__":
    main()
