# ==========================================
# 1. KHỞI TẠO ĐỒ HỌA & THƯ VIỆN (PHẢI NẰM TRÊN CÙNG)
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

# Thiết lập múi giờ Việt Nam (GMT+7)
VN_TZ = timezone(timedelta(hours=7))

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG (CẬP NHẬT THỜI GIAN)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        fullname TEXT, dob TEXT, class_name TEXT, school TEXT, province TEXT, managed_classes TEXT)''')
    
    for col in ["fullname", "dob", "class_name", "school", "province", "managed_classes"]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    # Bảng Kết quả tự do
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng Đề thi bắt buộc (THÊM CỘT START_TIME, END_TIME)
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, start_time TEXT, end_time TEXT)''')
    for col in ["start_time", "end_time"]:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} TEXT")
        except: pass

    # Bảng Kết quả bài bắt buộc
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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
# 3. ĐỒ HỌA TOÁN HỌC CHUẨN XÁC
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=200)
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
    arc = patches.Arc((3, 0), 1, 1, angle=0, theta1=120, theta2=180, color='blue', lw=2)
    ax.add_patch(arc)
    ax.text(-0.6, 1.5, 'Vật thể', rotation=90, fontweight='bold', color='#34495e')
    ax.text(0.5, -0.6, f'Bóng dài {chieu_dai_bong}m', fontsize=10, fontweight='bold', color='#d35400')
    ax.text(2.2, 0.2, r'$\alpha$', fontsize=12, color='blue')
    ax.set_xlim(-1, 4.5); ax.set_ylim(-1, 4.5)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 4. ENGINE TẠO ĐỀ (CHỐNG LẶP ĐÁP ÁN)
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
        a1 = random.randint(2, 9)
        self.build_q(rf"Điều kiện để biểu thức $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], "Biểu thức dưới căn >= 0")

        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        self.build_q(rf"Biết đồ thị hàm số $y = ax^2$ đi qua điểm $M({x0}; {y0})$. Giá trị của hệ số $a$ là", f"{a_val}", [f"{y0 * abs(x0)}", f"{abs(x0)**2}/{y0}", f"{y0}"], "Thay x, y vào hàm số")

        x_he = random.randint(1,4); y_he = random.randint(1,3)
        self.build_q(rf"Nghiệm $(x; y)$ của hệ phương trình $\begin{{cases}} x + y = {x_he+y_he} \\ x - y = {x_he-y_he} \end{{cases}}$ là", rf"({x_he}; {y_he})", [rf"({y_he}; {x_he})", rf"({x_he+1}; {y_he})", rf"({x_he}; {y_he-1})"], "Cộng 2 vế")

        s_v = random.randint(3, 6); p_v = random.randint(1, 2)
        self.build_q(rf"Hai số $x_1, x_2$ có tổng bằng {s_v} và tích bằng {p_v} là nghiệm của phương trình nào?", rf"$x^2 - {s_v}x + {p_v} = 0$", [rf"$x^2 + {s_v}x + {p_v} = 0$", rf"$x^2 - {p_v}x + {s_v} = 0$", rf"$x^2 + {p_v}x - {s_v} = 0$"], "Dùng Viète đảo")

        bong = random.choice([15, 20, 25])
        self.build_q(rf"Một vật thể có bóng in trên mặt đất dài {bong}m. Tia nắng tạo với mặt đất góc $\alpha$ (như hình vẽ). Chiều cao vật thể được tính bằng:", rf"${bong} \times \tan \alpha$", [rf"${bong} \times \sin \alpha$", rf"${bong} \times \cos \alpha$", rf"${bong} \times \cot \alpha$"], "Dùng Tỉ số lượng giác", draw_tower_shadow(bong))

        kientruc = random.choice(["Cổng vòm Parabol", "Cầu vượt", "Mái vòm"])
        self.build_q(rf"Một {kientruc.lower()} có hình dáng parabol với phương trình $y = -ax^2$ (như hình minh họa). Parabol này nhận đường thẳng nào làm trục đối xứng?", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường $y = x$", "Không có trục đối xứng"], "Tính chất Parabol", draw_real_parabola(kientruc))

        # Tự động sinh cho đủ 40 câu
        for i in range(7, 41):
            num = random.randint(10, 99)
            self.build_q(rf"Câu hỏi Toán học tự động số {i} (Phát sinh bởi AI). Giá trị ngẫu nhiên: $x = {num}$", f"Đáp án đúng {num}", [f"Sai {num+1}", f"Sai {num+2}", f"Sai {num-1}"], "Hướng dẫn giải chi tiết")

        return self.exam

# ==========================================
# 5. GIAO DIỆN LMS VỚI ĐỒNG HỒ ĐẾM NGƯỢC
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Hệ Thống Đánh Giá Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2E3B55;'>🎓 HỆ THỐNG QUẢN LÝ HỌC TẬP TỈNH TUYÊN QUANG</h1>", unsafe_allow_html=True)
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
        st.markdown(f"**Vai trò:** {st.session_state.role}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH (CÓ ĐỒNG HỒ & KIỂM SOÁT THỜI GIAN)
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc", "🤖 Luyện đề AI Tự do"])
        now_vn = datetime.now(VN_TZ)
        
        with tab_mand:
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT id, title, start_time, end_time, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
            
            if df_exams.empty: 
                st.info("Hiện chưa có bài tập bắt buộc nào được giao.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    # Ép kiểu thời gian
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
                        # Kiểm tra thời gian
                        if t_start and now_vn < t_start:
                            st.warning("⏳ Chưa đến thời gian làm bài.")
                        elif t_end and now_vn > t_end:
                            st.error("🔒 Đã hết hạn làm bài.")
                        else:
                            if st.button("✍️ Bắt đầu làm bài (90 Phút)", key=f"do_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                # Thiết lập mốc thời gian bắt đầu làm bài
                                st.session_state[f"start_exam_{exam_id}"] = datetime.now().timestamp()
                                st.rerun()
                    st.markdown("---")
            
            # KHU VỰC ĐANG LÀM BÀI
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                mand_exam_data = json.loads(exam_row['questions_json'])
                
                if mode == 'do':
                    # ==========================================
                    # ĐỒNG HỒ ĐẾM NGƯỢC 90 PHÚT BẰNG JAVASCRIPT
                    # ==========================================
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
                            // Tìm nút nộp bài và tự động click
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
                        selected = st.radio("Chọn đáp án:", options=q['options'], 
                                            index=q['options'].index(ans_val) if ans_val in q['options'] else None,
                                            key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / len(mand_exam_data)) * 10
                        ans_json = json.dumps(st.session_state[f"mand_ans_{exam_id}"])
                        c = conn.cursor()
                        # Câu lệnh SQL ngắt dòng an toàn
                        c.execute(
                            "INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", 
                            (st.session_state.current_user, exam_id, score, ans_json)
                        )
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
            st.title("Luyện Tập Tư Duy Cùng AI")
            st.info("Khu vực luyện tập tự do không tính thời gian.")
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔄 LÀM ĐỀ MỚI", use_container_width=True):
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
                    selected = st.radio("Chọn:", options=q['options'], 
                                        index=q['options'].index(ans_val) if ans_val in q['options'] else None,
                                        key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected
                    st.markdown("---")

                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ Luyện", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN ADMIN & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role == 'core_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        elif st.session_state.role == 'sub_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "👨‍🏫 Quản lý Giáo viên", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu"])
            tab_class, tab_scores, tab_system = tabs
        
        # --- TAB 1: QUẢN LÝ LỚP & HỌC SINH ---
        with tab_class:
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            if st.session_state.role in ['core_admin', 'sub_admin']:
                c.execute("SELECT DISTINCT class_name FROM users WHERE role='student' AND class_name IS NOT NULL")
                available_classes = [row[0] for row in c.fetchall()]
            else:
                c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
                m_cls = c.fetchone()[0]
                available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
            
            st.markdown("### 🔍 Lọc học sinh theo Lớp")
            selected_class = st.selectbox("Chọn lớp:", ["Tất cả các lớp được quyền xem"] + available_classes)
            
            query = "SELECT username as 'Username', fullname as 'Họ Tên', class_name as 'Lớp', password as 'Mật khẩu' FROM users WHERE role='student'"
            params = []
            
            if selected_class != "Tất cả các lớp được quyền xem":
                query += " AND class_name = ?"
                params.append(selected_class)
            elif st.session_state.role == 'teacher':
                if available_classes:
                    placeholders = ','.join(['?'] * len(available_classes))
                    query += f" AND class_name IN ({placeholders})"
                    params.extend(available_classes)
                else: query += " AND 1=0"
                    
            df_users = pd.read_sql_query(query, conn, params=params)
            if not df_users.empty: st.dataframe(df_users, use_container_width=True)
            
            # Form sửa Học sinh an toàn (Chống ngắt dòng)
            user_to_edit = st.selectbox("Chọn Học sinh để thao tác:", ["-- Chọn --"] + df_users['Username'].tolist())
            if user_to_edit != "-- Chọn --":
                c.execute("SELECT * FROM users WHERE username=?", (user_to_edit,))
                u_data = c.fetchone()
                with st.form("edit_student_form"):
                    col1, col2 = st.columns(2)
                    edit_name = col1.text_input("Họ và Tên", value=u_data[3] if u_data[3] else "")
                    edit_pwd = col2.text_input("Mật khẩu mới", value=u_data[1])
                    edit_class = col1.text_input("Lớp", value=u_data[5] if u_data[5] else "")
                    if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                        c.execute(
                            "UPDATE users SET fullname=?, password=?, class_name=? WHERE username=?", 
                            (edit_name, edit_pwd, edit_class, user_to_edit)
                        )
                        conn.commit()
                        st.success("Đã cập nhật!")
                        st.rerun()
            conn.close()

        # --- TAB 2: QUẢN LÝ NHÂN SỰ ---
        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                conn = sqlite3.connect('exam_db.sqlite')
                c = conn.cursor()
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    # (Logic giữ nguyên)
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    st.markdown("---")

                st.subheader("👨‍🏫 Quản lý Giáo viên (Tạo & Chỉ định Lớp)")
                with st.form("add_teacher_form"):
                    col1, col2 = st.columns(2)
                    t_user = col1.text_input("Tài khoản Giáo viên")
                    t_pwd = col2.text_input("Mật khẩu")
                    t_name = col1.text_input("Họ và Tên")
                    t_classes = col2.text_input("Lớp quản lý (VD: 9A1, 9A2)")
                    if st.form_submit_button("Tạo & Giao Lớp", type="primary"):
                        try:
                            c.execute(
                                "INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", 
                                (t_user.strip(), t_pwd.strip(), t_name.strip(), t_classes.strip())
                            )
                            conn.commit()
                            st.success("Thành công!")
                            st.rerun()
                        except: st.error("Lỗi: Tài khoản tồn tại.")
                conn.close()

        # --- TAB 3: NẠP DỮ LIỆU & GIAO BÀI (CHỨA THỜI GIAN) ---
        with tab_system:
            st.subheader("📤 Tải file & Giao bài AI (CÓ THỜI HẠN)")
            uploaded_pdf = st.file_uploader("Tải file Đề thi (PDF/Docx) để AI tham chiếu", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra (Bắt buộc)")
            
            # Chọn Thời gian bằng lịch của Streamlit
            st.markdown("**Cài đặt Thời gian (Theo Múi giờ Việt Nam)**")
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Ngày giao bài")
            start_time = col1.time_input("Giờ giao bài", value=datetime.strptime("07:00", "%H:%M").time())
            
            end_date = col2.date_input("Ngày kết thúc")
            end_time = col2.time_input("Giờ kết thúc", value=datetime.strptime("23:59", "%H:%M").time())
            
            start_dt_str = f"{start_date} {start_time.strftime('%H:%M:%S')}"
            end_dt_str = f"{end_date} {end_time.strftime('%H:%M:%S')}"
            
            if st.button("🚀 Xử lý AI & Giao bài toàn trường", type="primary"):
                if exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    # Lệnh SQL ngắt dòng an toàn
                    c.execute(
                        "INSERT INTO mandatory_exams (title, questions_json, start_time, end_time) VALUES (?, ?, ?, ?)", 
                        (exam_title.strip(), json.dumps(fixed_exam), start_dt_str, end_dt_str)
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ Bài tập đã được nạp kèm theo giới hạn thời gian!")
                else: st.error("Vui lòng nhập tên bài kiểm tra!")

if __name__ == "__main__":
    main()
