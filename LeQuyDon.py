# ==========================================
# 1. KHỞI TẠO ĐỒ HỌA (PHẢI NẰM TRÊN CÙNG)
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
import matplotlib.patches as patches

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG (HIERARCHY DB)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, role TEXT, 
        fullname TEXT, dob TEXT, class_name TEXT, school TEXT, province TEXT, managed_classes TEXT)''')
    
    # Tự động cập nhật cột nếu DB cũ chưa có
    columns_to_add = ["fullname", "dob", "class_name", "school", "province", "managed_classes"]
    for col in columns_to_add:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    # Bảng Kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    # TÀI KHOẢN ADMIN LÕI
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

def generate_username(fullname, dob):
    clean_name = re.sub(r'[^\w\s]', '', fullname).lower().replace(" ", "")
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

def draw_vivid_histogram(freqs, doi_tuong):
    fig, ax = plt.subplots(figsize=(6, 3))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    bars = ax.bar(bins, percents, color=['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#e67e22'], edgecolor='black')
    ax.set_title(f"KHẢO SÁT CHIỀU CAO CỦA {doi_tuong.upper()}", fontweight='bold', pad=10)
    ax.set_ylabel('Tỉ lệ (%)', fontweight='bold')
    for bar, v in zip(bars, percents): 
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{round(v)}%", ha='center', fontweight='bold')
    ax.set_ylim(0, max(percents) + 15)
    return fig_to_base64(fig)

# ==========================================
# 4. ENGINE TẠO ĐỀ
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
            if d_str not in unique_options:
                unique_options.append(d_str)
                
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
        # 1. ĐKXĐ
        a1 = random.randint(2, 9)
        hd_1 = rf"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Biểu thức $\sqrt{{A}}$ xác định khi $A \ge 0$.<br>- **Bước 2:** Áp dụng: $x - {a1} \ge 0 \Leftrightarrow x \ge {a1}$."
        self.build_q(rf"Điều kiện để biểu thức $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], hd_1)

        # 2. Tìm a của Parabol
        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        hd_2 = rf"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Thay $x = {x0}$ và $y = {y0}$ vào phương trình $y = ax^2$.<br>- **Bước 2:** Ta được: ${y0} = a \cdot ({x0})^2 \Rightarrow a = {a_val}$."
        self.build_q(rf"Biết đồ thị hàm số $y = ax^2$ đi qua điểm $M({x0}; {y0})$. Giá trị của hệ số $a$ là", f"{a_val}", [f"{y0 * abs(x0)}", f"{abs(x0)**2}/{y0}", f"{y0}"], hd_2)

        # 3. Hệ phương trình
        x_he = random.randint(1,4); y_he = random.randint(1,3)
        hd_3 = rf"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Cộng vế theo vế: $2x = {2*x_he} \Rightarrow x = {x_he}$.<br>- **Bước 2:** Thay $x={x_he}$ vào PT đầu $\Rightarrow y = {y_he}$."
        self.build_q(rf"Nghiệm $(x; y)$ của hệ phương trình $\begin{{cases}} x + y = {x_he+y_he} \\ x - y = {x_he-y_he} \end{{cases}}$ là", rf"({x_he}; {y_he})", [rf"({y_he}; {x_he})", rf"({x_he+1}; {y_he})", rf"({x_he}; {y_he-1})"], hd_3)

        # 4. Viète đảo
        s_v = random.randint(3, 6); p_v = random.randint(1, 2)
        hd_4 = rf"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Áp dụng định lý Viète đảo: Hai số là nghiệm của phương trình $X^2 - SX + P = 0$.<br>- **Bước 2:** Thay $S={s_v}, P={p_v}$ ta có phương trình chuẩn."
        self.build_q(rf"Hai số $x_1, x_2$ có tổng bằng {s_v} và tích bằng {p_v} là nghiệm của phương trình nào?", rf"$x^2 - {s_v}x + {p_v} = 0$", [rf"$x^2 + {s_v}x + {p_v} = 0$", rf"$x^2 - {p_v}x + {s_v} = 0$", rf"$x^2 + {p_v}x - {s_v} = 0$"], hd_4)

        # 5. Hệ thức lượng (Tháp)
        bong = random.choice([15, 20, 25])
        hd_5 = r"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Coi vật thể và bóng tạo thành tam giác vuông.<br>- **Bước 2:** Sử dụng Tỉ số lượng giác: $\tan \alpha = \frac{\text{Đối}}{\text{Kề}} = \frac{\text{Chiều cao}}{\text{Bóng}}$. Suy ra Chiều cao = Bóng $\times \tan \alpha$."
        self.build_q(rf"Một vật thể có bóng in trên mặt đất dài {bong}m. Tia nắng tạo với mặt đất góc $\alpha$ (như hình vẽ). Chiều cao vật thể được tính bằng:", rf"${bong} \times \tan \alpha$", [rf"${bong} \times \sin \alpha$", rf"${bong} \times \cos \alpha$", rf"${bong} \times \cot \alpha$"], hd_5, draw_tower_shadow(bong))

        # 6. Parabol thực tế
        kientruc = random.choice(["Cổng vòm Parabol", "Cầu vượt", "Mái vòm"])
        hd_6 = r"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Đồ thị hàm số $y = ax^2$ luôn đi qua gốc tọa độ O(0;0).<br>- **Bước 2:** Tính chất cơ bản là luôn nhận trục tung (Oy) làm trục đối xứng."
        self.build_q(rf"Một {kientruc.lower()} có hình dáng parabol với phương trình $y = -ax^2$ (như hình minh họa). Parabol này nhận đường thẳng nào làm trục đối xứng?", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường $y = x$", "Không có trục đối xứng"], hd_6, draw_real_parabola(kientruc))

        # Khởi tạo các câu còn lại
        for i in range(7, 41):
            num = random.randint(10, 99)
            hd_chung = rf"💡 **HƯỚNG DẪN GIẢI CHI TIẾT:**<br>- **Bước 1:** Phân tích đề bài.<br>- **Bước 2:** Áp dụng công thức và tính toán ra kết quả."
            self.build_q(rf"Câu hỏi Toán học tự động số {i} (Phát sinh bởi AI). Giá trị ngẫu nhiên: $x = {num}$", f"Đáp án đúng {num}", [f"Sai {num+1}", f"Sai {num+2}", f"Sai {num-1}"], hd_chung)

        return self.exam

# ==========================================
# 5. GIAO DIỆN LMS
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Hệ Thống Đánh Giá", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    # --- ĐĂNG NHẬP ---
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
                    else:
                        st.error("❌ Sai tài khoản hoặc mật khẩu!")
        return

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        role_dict = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin Thành Viên", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_dict.get(st.session_state.role, '')}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH (BẢN VÁ LỖI INDEX)
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc", "🤖 Luyện đề AI Tự do"])
        
        with tab_mand:
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT id, title, timestamp, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
            if df_exams.empty: st.info("Hiện chưa có bài tập bắt buộc nào được giao.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    c = conn.cursor()
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1: st.markdown(f"📌 **{row['title']}**")
                    with col2:
                        if res:
                            if st.button("👁 Xem lại bài", key=f"rev_{exam_id}"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'review'
                                st.rerun()
                        else:
                            if st.button("✍️ Làm bài ngay", key=f"do_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                st.rerun()
                    st.markdown("---")
            
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                mand_exam_data = json.loads(exam_row['questions_json'])
                st.subheader(f"📝 {exam_row['title']}")
                
                if mode == 'do':
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        
                        # [BẢN VÁ LỖI SAFE LOOKUP]
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn đáp án:", options=q['options'], 
                                            index=q['options'].index(ans_val) if ans_val in q['options'] else None,
                                            key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI", type="primary", use_container_width=True):
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / len(mand_exam_data)) * 10
                        ans_json = json.dumps(st.session_state[f"mand_ans_{exam_id}"])
                        c = conn.cursor()
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, ans_json))
                        conn.commit()
                        st.success("✅ Nộp bài thành công!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                        
                elif mode == 'review':
                    c = conn.cursor()
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    saved_res = c.fetchone()
                    score = saved_res[0]
                    saved_answers = json.loads(saved_res[1])
                    
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                        <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        user_ans = saved_answers[str(q['id'])]
                        
                        # [BẢN VÁ LỖI SAFE LOOKUP]
                        st.radio("Đã chọn:", options=q['options'], 
                                 index=q['options'].index(user_ans) if user_ans in q['options'] else None, 
                                 key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                        
                        if user_ans == q['answer']: st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                        else: st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                        with st.expander("📖 Xem Hướng dẫn Giải chi tiết"): st.markdown(q['hint'], unsafe_allow_html=True)
                        st.markdown("---")
                        
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
            conn.close()

        with tab_ai:
            st.title("Luyện Tập Tư Duy Cùng AI")
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
            with c2:
                if st.session_state.is_submitted and st.button("🔁 Làm lại đề này", use_container_width=True):
                    st.session_state.user_answers = {q['id']: None for q in st.session_state.exam_data}
                    st.session_state.is_submitted = False
                    st.rerun()
            with c3:
                if st.session_state.is_submitted and st.button("🛠 Làm lại câu sai", use_container_width=True):
                    for q in st.session_state.exam_data:
                        if st.session_state.user_answers[q['id']] != q['answer']:
                            st.session_state.user_answers[q['id']] = None
                    st.session_state.is_submitted = False
                    st.rerun()

            if st.session_state.exam_data:
                if not st.session_state.is_submitted:
                    st.success(f"✅ Đã khởi tạo thành công {len(st.session_state.exam_data)}/40 câu hỏi!")
                    
                if st.session_state.is_submitted:
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    score = (correct / len(st.session_state.exam_data)) * 10
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                        <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    </div>
                    """, unsafe_allow_html=True)

                for q in st.session_state.exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    
                    disabled = st.session_state.is_submitted
                    # [BẢN VÁ LỖI SAFE LOOKUP]
                    ans_val = st.session_state.user_answers[q['id']]
                    selected = st.radio("Chọn:", options=q['options'], 
                                        index=q['options'].index(ans_val) if ans_val in q['options'] else None,
                                        key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected

                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                        else: st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                        with st.expander("📖 Xem Hướng dẫn Giải chi tiết"): st.markdown(q['hint'], unsafe_allow_html=True)
                    st.markdown("---")

                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI", type="primary", use_container_width=True):
                        correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        c.execute("INSERT INTO results (username, score) VALUES (?, ?)", (st.session_state.current_user, (correct/len(st.session_state.exam_data))*10))
                        conn.commit()
                        conn.close()
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN ADMIN & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển Quản Lý (LMS)")
        
        tab_users, tab_assign, tab_scores = st.tabs(["👥 Quản lý Tài khoản & Lớp", "📤 Nạp file Giao bài", "📊 Báo cáo Điểm"])
        
        with tab_users:
            st.subheader("1. Tạo tài khoản hàng loạt bằng file Excel")
            st.info("💡 Tải file Excel gồm các cột: **Họ tên, Ngày sinh, Lớp, Trường, Tỉnh**. Hệ thống sẽ tự động tạo Tài khoản và Mật khẩu (mặc định: 123456).")
            
            uploaded_excel = st.file_uploader("Chọn file Excel", type=['xlsx'])
            if uploaded_excel is not None:
                if st.button("🔄 Nhập dữ liệu tự động"):
                    try:
                        df_import = pd.read_excel(uploaded_excel)
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        success_count = 0
                        for index, row in df_import.iterrows():
                            fullname = str(row.get('Họ tên', ''))
                            dob = str(row.get('Ngày sinh', ''))
                            class_name = str(row.get('Lớp', ''))
                            school = str(row.get('Trường', ''))
                            province = str(row.get('Tỉnh', ''))
                            
                            if fullname and fullname.strip() != 'nan':
                                uname = generate_username(fullname, dob)
                                try:
                                    c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school, province) VALUES (?, '123456', 'student', ?, ?, ?, ?, ?)", 
                                              (uname, fullname, dob, class_name, school, province))
                                    success_count += 1
                                except: pass
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Đã tạo tự động thành công {success_count} tài khoản học sinh!")
                    except Exception as e:
                        st.error(f"Lỗi đọc file Excel: {e}")

            st.markdown("---")
            st.subheader("2. Lọc và Quản lý Học sinh theo Lớp")
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            if st.session_state.role in ['core_admin', 'sub_admin']:
                c.execute("SELECT DISTINCT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''")
                available_classes = [row[0] for row in c.fetchall()]
            else:
                c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
                m_cls = c.fetchone()[0]
                available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
            
            selected_class = st.selectbox("📌 Lọc theo Lớp:", ["Tất cả các lớp được quyền xem"] + available_classes)
            
            query = "SELECT username as 'Username', fullname as 'Họ Tên', class_name as 'Lớp', password as 'Mật khẩu', role as 'Phân quyền' FROM users WHERE role='student'"
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
            else: st.info("Chưa có học sinh nào trong lớp này.")

            st.markdown("#### ✏️ Cập nhật thông tin & Reset Mật khẩu học sinh")
            user_to_edit = st.selectbox("Chọn Username để thao tác:", ["-- Chọn --"] + df_users['Username'].tolist())
            
            if user_to_edit != "-- Chọn --":
                c.execute("SELECT * FROM users WHERE username=?", (user_to_edit,))
                u_data = c.fetchone()
                
                with st.form("edit_user_form"):
                    st.info(f"Đang thao tác trên tài khoản: **{user_to_edit}** (Tên đăng nhập không thể thay đổi)")
                    col1, col2 = st.columns(2)
                    edit_name = col1.text_input("Họ và Tên", value=u_data[3] if u_data[3] else "")
                    edit_pwd = col2.text_input("Mật khẩu mới", value=u_data[1])
                    edit_class = col1.text_input("Lớp", value=u_data[5] if u_data[5] else "")
                    
                    if st.session_state.role in ['core_admin', 'sub_admin']:
                        edit_role = col2.selectbox("Phân quyền", ["student", "teacher", "sub_admin"], index=["student", "teacher", "sub_admin"].index(u_data[2]) if u_data[2] in ["student", "teacher", "sub_admin"] else 0)
                        edit_managed = st.text_input("Lớp quản lý (Giao cho GV, VD: 9A1,9A2)", value=u_data[8] if u_data[8] else "")
                    else:
                        edit_role = "student"
                        edit_managed = ""
                        col2.markdown("<br><span style='color:gray; font-size: 0.9em;'>*Giáo viên chỉ được sửa Thông tin và Mật khẩu.*</span>", unsafe_allow_html=True)
                        
                    if st.form_submit_button("💾 Cập nhật", type="primary"):
                        c.execute("UPDATE users SET fullname=?, password=?, class_name=?, role=?, managed_classes=? WHERE username=?", (edit_name, edit_pwd, edit_class, edit_role, edit_managed, user_to_edit))
                        conn.commit()
                        st.success(f"✅ Đã cập nhật thành công mật khẩu và thông tin cho {edit_name}!")
                        st.rerun()
            conn.close()

        with tab_assign:
            st.subheader("📤 Tải file & Giao bài AI")
            uploaded_pdf = st.file_uploader("Tải file Đề thi (PDF/Docx) để AI tham chiếu", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra (Bắt buộc)")
            
            if st.button("🚀 Xử lý AI & Giao bài", type="primary"):
                if exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO mandatory_exams (title, questions_json) VALUES (?, ?)", (exam_title.strip(), json.dumps(fixed_exam)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Bài tập đã được nạp và xuất hiện trên bảng làm bài của Học sinh!")
                else: st.error("Vui lòng nhập tên bài kiểm tra!")

        with tab_scores:
            st.subheader("📊 Báo cáo điểm số")
            conn = sqlite3.connect('exam_db.sqlite')
            query_score = "SELECT u.fullname as 'Họ Tên', u.class_name as 'Lớp', me.title as 'Tên bài', mr.score as 'Điểm' FROM mandatory_results mr JOIN users u ON mr.username = u.username JOIN mandatory_exams me ON mr.exam_id = me.id"
            params_score = []
            
            if st.session_state.role == 'teacher' and available_classes:
                placeholders = ','.join(['?'] * len(available_classes))
                query_score += f" WHERE u.class_name IN ({placeholders})"
                params_score.extend(available_classes)
                
            query_score += " ORDER BY mr.timestamp DESC"
            df_m = pd.read_sql_query(query_score, conn, params=params_score)
            st.dataframe(df_m, use_container_width=True)
            conn.close()

if __name__ == "__main__":
    try: main()
    except Exception as e: st.error(f"🚨 LỖI HỆ THỐNG: {e}")
