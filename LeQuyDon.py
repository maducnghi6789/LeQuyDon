import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. DATABASE INIT & SECURITY
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student')")
    conn.commit()
    conn.close()

# ==========================================
# 2. HỆ THỐNG VẼ HÌNH ẢNH AI TỰ ĐỘNG (BẢN CHUYÊN NGHIỆP)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    # Nâng cấp độ phân giải dpi=150 cho ảnh sắc nét chuẩn HD
    plt.savefig(buf, format="png", bbox_inches='tight', transparent=True, dpi=150)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_histogram(freqs):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    bars = ax.bar(bins, percents, color='#3498db', edgecolor='#2c3e50', linewidth=1.5)
    ax.set_ylabel('Tỉ lệ (%)', fontweight='bold')
    ax.set_xlabel('Chiều cao (cm)', fontweight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    for bar, v in zip(bars, percents): 
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{round(v)}%", ha='center', fontweight='bold', color='#e74c3c')
    ax.set_ylim(0, max(percents) + 15)
    return fig_to_base64(fig)

def draw_right_triangle(label_A='M', label_B='N', label_C='P'):
    fig, ax = plt.subplots(figsize=(4, 3))
    # Vẽ các cạnh
    ax.plot([0, 4, 0, 0], [0, 0, 3, 0], color='#2c3e50', lw=2.5)
    # Ký hiệu góc vuông tại (0,0)
    ax.plot([0, 0.4, 0.4, 0], [0.4, 0.4, 0, 0], color='#e74c3c', lw=1.5)
    
    # Nhãn đỉnh
    ax.text(-0.3, 3.1, label_A, fontsize=14, fontweight='bold', color='#2980b9')
    ax.text(-0.3, -0.4, label_B, fontsize=14, fontweight='bold', color='#2980b9')
    ax.text(4.1, -0.4, label_C, fontsize=14, fontweight='bold', color='#2980b9')
    
    ax.set_xlim(-0.8, 4.8); ax.set_ylim(-0.8, 3.8)
    ax.axis('off') # Ẩn trục tọa độ
    return fig_to_base64(fig)

def draw_parabola():
    """Vẽ minh họa đồ thị Parabol chung chung, không hiện số để không lộ đề"""
    fig, ax = plt.subplots(figsize=(4, 4))
    x = np.linspace(-3, 3, 100)
    y = x**2
    ax.plot(x, y, color='#e67e22', lw=2.5, label="$y=ax^2 (a>0)$")
    
    # Hệ trục tọa độ
    ax.axhline(0, color='black', lw=1.5)
    ax.axvline(0, color='black', lw=1.5)
    ax.text(3.2, -0.5, 'x', fontsize=12, style='italic')
    ax.text(-0.5, 9.5, 'y', fontsize=12, style='italic')
    ax.text(-0.5, -0.5, 'O', fontsize=12, fontweight='bold')
    
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_xticks([]); ax.set_yticks([]) # Giấu số liệu cụ thể
    return fig_to_base64(fig)

def draw_intersecting_circles():
    """Vẽ minh họa 2 đường tròn cắt nhau"""
    fig, ax = plt.subplots(figsize=(5, 3))
    circle1 = plt.Circle((-0.8, 0), 1.5, color='#8e44ad', fill=False, lw=2)
    circle2 = plt.Circle((0.8, 0), 1.2, color='#27ae60', fill=False, lw=2)
    ax.add_patch(circle1)
    ax.add_patch(circle2)
    
    # Điểm cắt
    ax.plot(0, 1.15, 'ro'); ax.plot(0, -1.15, 'ro')
    
    ax.set_xlim(-2.5, 2.5); ax.set_ylim(-2, 2)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 3. THUẬT TOÁN SINH 40 CÂU HỎI MA TRẬN
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []
        self.q_count = 1

    def build_q(self, text, correct, distractors, hint, img_b64=None):
        options = [correct] + distractors
        random.shuffle(options)
        self.exam.append({
            "id": self.q_count, "question": text, "options": options,
            "answer": correct, "hint": hint, "image": img_b64
        })
        self.q_count += 1

    def generate_all(self):
        # --- CHỦ ĐỀ 1: CĂN THỨC ---
        a1 = random.randint(2, 9)
        self.build_q(r"Điều kiện xác định của biểu thức $\sqrt{x-" + str(a1) + r"}$ là", 
                     rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], r"Biểu thức trong căn phải $\ge 0$.")
        
        # --- CHỦ ĐỀ 2: HÀM SỐ & ĐỒ THỊ ---
        img_para = draw_parabola()
        self.build_q(r"Quan sát hình minh họa, đồ thị hàm số $y=ax^2 (a \ne 0)$ có bao nhiêu trục đối xứng?", 
                     "1 trục đối xứng", ["Không có trục nào", "2 trục đối xứng", "Vô số trục đối xứng"], 
                     r"Quan sát hình, Parabol chỉ nhận trục tung Oy làm trục đối xứng duy nhất.", img_para)
                     
        x8 = 2; y8 = random.choice([4, 8, 12])
        self.build_q(rf"Đồ thị hàm số $y=ax^2$ đi qua điểm $M({x8}; {y8})$. Giá trị của $a$ là", 
                     rf"${y8//4}$", [rf"${y8//2}$", rf"${y8}$", rf"${y8*4}$"], r"Thay tọa độ x, y vào hàm số.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & HỆ PT ---
        self.build_q(r"Hệ phương trình nào KHÔNG là hệ PT bậc nhất 2 ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", 
                     [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} x - y = 1 \\ x + y = 2 \end{cases}$"], r"Không được chứa $\sqrt{x}$.")
        self.build_q(r"Nghiệm của PT $x^2 - 5x + 6 = 0$ là", r"$x=2, x=3$", [r"$x=-2, x=-3$", r"$x=1, x=6$", r"$x=-1, x=-6$"], r"Dùng hệ thức Viète hoặc Casio.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG (HÌNH MINH HỌA CHI TIẾT) ---
        img_tri = draw_right_triangle('M', 'N', 'P')
        self.build_q(r"Cho tam giác $MNP$ vuông tại $N$ (quan sát hình minh họa). Khẳng định nào sau đây là ĐÚNG?", 
                     r"$\cos M = \frac{MN}{MP}$", [r"$\cos M = \frac{NP}{MP}$", r"$\sin M = \frac{MN}{MP}$", r"$\tan M = \frac{MP}{MN}$"], 
                     r"Cos = Kề / Huyền. Cạnh kề góc M là MN, cạnh huyền là MP.", img_tri)

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN ---
        img_circles = draw_intersecting_circles()
        self.build_q(r"Quan sát hình minh họa, số điểm chung của hai đường tròn cắt nhau là bao nhiêu?", 
                     "2 điểm chung", ["1 điểm chung", "0 điểm chung", "3 điểm chung"], 
                     r"Hai đường tròn cắt nhau luôn tạo ra chính xác 2 giao điểm phân biệt.", img_circles)

        # --- CHỦ ĐỀ 8: THỐNG KÊ (BIỂU ĐỒ CHUYÊN NGHIỆP) ---
        freqs = [10, 30, 40, 15, 5]
        img_hist = draw_histogram(freqs)
        self.build_q(r"Dựa vào biểu đồ phân bố chiều cao, nhóm học sinh có chiều cao từ 160cm đến dưới 170cm chiếm tỉ lệ bao nhiêu phần trăm?", 
                     "40%", ["30%", "15%", "10%"], 
                     r"Nhìn vào cột cao nhất trên biểu đồ ứng với khoảng [160; 170).", img_hist)

        # Trình sinh đề có thể tự động nối thêm các câu còn lại cho đủ 40 câu theo ma trận
        # ... (đã lược bớt để tập trung vào hình ảnh)
        
        return self.exam

# ==========================================
# 4. GIAO DIỆN HỆ THỐNG (UI/UX)
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT Tuyên Quang", layout="wide", page_icon="🎓")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state.current_user is None:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #2E3B55;'>🎓 HỆ THỐNG KIỂM TRA ĐÁNH GIÁ NĂNG LỰC</h1>
            <p style='color: #777; font-size: 18px;'>Kỳ thi tuyển sinh vào lớp 10 THPT Tỉnh Tuyên Quang</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.info("💡 **Tài khoản Demo:** Admin (`admin`/`admin123`) | Học sinh (`hs1`/`123`)")
            with st.form("login_form"):
                st.markdown("### 🔒 Cổng Đăng Nhập")
                user = st.text_input("👤 Tên đăng nhập")
                pwd = st.text_input("🔑 Mật khẩu", type="password")
                submitted = st.form_submit_button("🚀 Đăng nhập hệ thống", use_container_width=True)
                
                if submitted:
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pwd))
                    res = c.fetchone()
                    conn.close()
                    if res:
                        st.session_state.current_user = user
                        st.session_state.role = res[0]
                        st.rerun()
                    else:
                        st.error("❌ Tài khoản hoặc mật khẩu không chính xác!")
        return

    # --- THANH BÊN (SIDEBAR) ---
    with st.sidebar:
        st.markdown(f"### 👤 Xin chào, **{st.session_state.current_user}**")
        st.markdown(f"**Vai trò:** {'👑 Quản trị viên' if st.session_state.role == 'admin' else '🎓 Học sinh'}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH
    # ==========================
    if st.session_state.role == 'student':
        st.title("📝 Đề Thi Thử Vào 10 THPT (Toán Chung)")
        st.warning("⏱ Thời gian làm bài: 90 phút. Đề thi bám sát ma trận, tự động sinh đồ thị minh họa.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 LÀM ĐỀ MỚI (Trộn AI)", use_container_width=True):
                gen = ExamGenerator()
                st.session_state.exam_data = gen.generate_all()
                st.session_state.user_answers = {q['id']: None for q in st.session_state.exam_data}
                st.session_state.is_submitted = False
                st.rerun()
        with c2:
            if st.session_state.is_submitted and st.button("🔁 Làm lại toàn bộ", use_container_width=True):
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
            if st.session_state.is_submitted:
                correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                score = (correct / len(st.session_state.exam_data)) * 10
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    <h4 style="color: #2E7D32;">Đúng {correct} / {len(st.session_state.exam_data)} câu hỏi.</h4>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            for q in st.session_state.exam_data:
                st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                
                # Render Ảnh Base64 nét căng
                if q['image']:
                    st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:400px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">', unsafe_allow_html=True)
                
                disabled = st.session_state.is_submitted
                selected = st.radio("Chọn đáp án:", options=q['options'], 
                                    index=q['options'].index(st.session_state.user_answers[q['id']]) if st.session_state.user_answers[q['id']] else None,
                                    key=f"q_{q['id']}", disabled=disabled, label_visibility="collapsed")
                
                if not disabled: st.session_state.user_answers[q['id']] = selected

                if st.session_state.is_submitted:
                    if selected == q['answer']:
                        st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                    else:
                        st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                    with st.expander("📖 Xem hướng dẫn"):
                        st.markdown(q['hint'], unsafe_allow_html=True)
                st.markdown("---")

            if not st.session_state.is_submitted:
                if st.button("📤 NỘP BÀI KIỂM TRA", type="primary", use_container_width=True):
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    score = (correct / len(st.session_state.exam_data)) * 10
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?, ?, ?, ?)", 
                              (st.session_state.current_user, score, correct, len(st.session_state.exam_data) - correct))
                    conn.commit()
                    conn.close()
                    st.session_state.is_submitted = True
                    st.rerun()

    # ==========================
    # GIAO DIỆN ADMIN 
    # ==========================
    elif st.session_state.role == 'admin':
        st.title("⚙ Hệ Thống Quản Trị (Admin Dashboard)")
        
        tab1, tab2 = st.tabs(["📊 Thống kê Kết quả", "👤 Quản lý Tài khoản"])
        
        with tab1:
            conn = sqlite3.connect('exam_db.sqlite')
            df = pd.read_sql_query("SELECT username as 'Học sinh', score as 'Điểm', correct_count as 'Số câu đúng', wrong_count as 'Số câu sai', timestamp as 'Thời gian' FROM results ORDER BY timestamp DESC", conn)
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                c1, c2 = st.columns(2)
                c1.metric("Tổng lượt làm bài", len(df))
                c2.metric("Điểm trung bình toàn trường", f"{df['Điểm'].mean():.2f}")
            else:
                st.info("Chưa có dữ liệu bài thi.")

        with tab2:
            st.subheader("➕ Thêm tài khoản mới")
            with st.form("add_user"):
                c1, c2, c3 = st.columns(3)
                new_user = c1.text_input("Tên đăng nhập")
                new_pwd = c2.text_input("Mật khẩu")
                new_role = c3.selectbox("Quyền", ["student", "admin"])
                if st.form_submit_button("Tạo tài khoản"):
                    if new_user and new_pwd:
                        try:
                            conn = sqlite3.connect('exam_db.sqlite')
                            c = conn.cursor()
                            c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user.strip(), new_pwd.strip(), new_role))
                            conn.commit()
                            conn.close()
                            st.success(f"Đã tạo: {new_user}")
                            st.rerun()
                        except: st.error("Tên đăng nhập đã tồn tại!")
            
            st.markdown("---")
            st.subheader("🗑 Xóa tài khoản")
            conn = sqlite3.connect('exam_db.sqlite')
            df_users = pd.read_sql_query("SELECT username as 'Tài khoản', role as 'Quyền' FROM users", conn)
            st.dataframe(df_users, use_container_width=True)
            
            safe_users = [u for u in df_users['Tài khoản'] if u != 'admin' and u != st.session_state.current_user]
            with st.form("del_user"):
                del_u = st.selectbox("Chọn tài khoản cần xóa", ["-- Chọn --"] + safe_users)
                if st.form_submit_button("Xóa vĩnh viễn"):
                    if del_u != "-- Chọn --":
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (del_u,))
                        c.execute("DELETE FROM results WHERE username=?", (del_u,))
                        conn.commit()
                        conn.close()
                        st.success(f"Đã xóa {del_u}")
                        st.rerun()

if __name__ == "__main__":
    main()
