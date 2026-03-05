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
# 2. HỆ THỐNG VẼ HÌNH ẢNH AI TỰ ĐỘNG (BASE64)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', transparent=True, dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_histogram(freqs):
    fig, ax = plt.subplots(figsize=(5, 3))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    ax.bar(bins, percents, color='#4CAF50', edgecolor='black')
    ax.set_ylabel('Tỉ lệ (%)')
    for i, v in enumerate(percents): ax.text(i, v + 2, f"{round(v)}%", ha='center')
    ax.set_ylim(0, max(percents) + 15)
    return fig_to_base64(fig)

def draw_right_triangle(label_A='A', label_B='B', label_C='C'):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 4, 0, 0], [0, 0, 3, 0], 'b-', lw=2)
    ax.text(-0.3, 3, label_A, fontsize=12, fontweight='bold')
    ax.text(4.1, -0.2, label_C, fontsize=12, fontweight='bold')
    ax.text(-0.3, -0.2, label_B, fontsize=12, fontweight='bold')
    ax.axis('off')
    return fig_to_base64(fig)

def draw_circle():
    fig, ax = plt.subplots(figsize=(3, 3))
    circle = plt.Circle((0, 0), 1, color='blue', fill=False, lw=2)
    ax.add_patch(circle)
    ax.plot(0, 0, 'ro')
    ax.text(0.1, 0.1, 'O', fontsize=12, fontweight='bold')
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
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
        # --- CHỦ ĐỀ 1: CĂN THỨC (6 CÂU) ---
        a1 = random.randint(2, 9)
        self.build_q(r"Điều kiện xác định của biểu thức $\sqrt{x-" + str(a1) + r"}$ là", 
                     rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], r"Biểu thức trong căn phải $\ge 0$.")
        a2 = random.choice([4, 9, 16, 25, 36])
        self.build_q(rf"Căn bậc hai của ${a2}$ là", rf"${int(math.sqrt(a2))}$ và -${int(math.sqrt(a2))}$", 
                     [rf"${int(math.sqrt(a2))}$", rf"-${int(math.sqrt(a2))}$", rf"${a2**2}$"], r"Mỗi số dương có 2 căn bậc hai.")
        a3 = random.randint(2, 5); b3 = random.randint(1, 4)
        self.build_q(rf"Với $x < {a3}$, biểu thức $\sqrt{{({a3}-x)^2}} + x - {b3}$ bằng", 
                     rf"${a3-b3}$", [rf"${b3-a3}$", rf"$2x - {a3+b3}$", rf"${a3+b3}$"], r"Dùng HĐT $\sqrt{A^2}=|A|$.")
        self.build_q(r"Cho $b>0$, khẳng định nào đúng?", r"$\sqrt{9b^2} = 3b$", [r"$\sqrt{9b^2} = -3b$", r"$\sqrt{9b^2} = 9b$", r"$\sqrt{9b^2} = 3b^2$"], r"$\sqrt{A^2}=|A|$")
        self.build_q(r"Với $a \ge 0$, biểu thức $\sqrt{16a} - \sqrt{9a}$ bằng", r"$\sqrt{a}$", [r"$7\sqrt{a}$", r"$a$", r"$25\sqrt{a}$"], r"Tính $4\sqrt{a} - 3\sqrt{a}$")
        self.build_q(r"Với $x>0, y>0, x \ne y$, biểu thức $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}} : \frac{1}{\sqrt{x} - \sqrt{y}}$ bằng", 
                     r"$x - y$", [r"$y - x$", r"$\sqrt{x} - \sqrt{y}$", r"$x+y$"], r"Rút gọn phân thức.")

        # --- CHỦ ĐỀ 2: HÀM SỐ (3 CÂU) ---
        self.build_q(r"Đồ thị hàm số $y=ax^2 (a \ne 0)$ có bao nhiêu trục đối xứng?", "1", ["0", "2", "Vô số"], r"Trục Oy là trục đối xứng.")
        x8 = 2; y8 = random.choice([4, 8, 12])
        self.build_q(rf"Đồ thị hàm số $y=ax^2$ đi qua điểm $M({x8}; {y8})$. Giá trị của $a$ là", 
                     rf"${y8//4}$", [rf"${y8//2}$", rf"${y8}$", rf"${y8*4}$"], r"Thay tọa độ x, y vào hàm số.")
        self.build_q(r"Gọi $A, B$ thuộc $y=2x^2$ có hoành độ -1 và 1. Chu vi tam giác $OAB$ là", r"$2\sqrt{5} + 2$", [r"$\sqrt{5} + 2$", r"$2\sqrt{5} + 1$", r"$4\sqrt{5}$"], r"Tính tọa độ và dùng Pytago.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & HỆ PT (8 CÂU) ---
        self.build_q(r"Phương trình nào dưới đây là phương trình bậc nhất hai ẩn?", r"$3x - 2y = 5$", [r"$xy = 5$", r"$x^2 + y = 1$", r"$3x - y^2 = 0$"], r"Dạng $ax+by=c$")
        self.build_q(r"Hệ phương trình nào KHÔNG là hệ PT bậc nhất 2 ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", 
                     [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} x - y = 1 \\ x + y = 2 \end{cases}$"], r"Không được chứa $\sqrt{x}$.")
        self.build_q(r"Số nghiệm của phương trình $\frac{-x+2}{x-2} + \frac{2x+6}{x} = 0$ là", "1", ["0", "2", "3"], r"Điều kiện $x \ne 2$. Rút gọn giải pt.")
        c13 = random.randint(2,5)
        self.build_q(rf"Tổng các nghiệm của PT $(x-{c13})(2x-4) = 0$ là", rf"${c13+2}$", [rf"${c13-2}$", rf"${c13*2}$", rf"${abs(c13-2)}$"], r"Nghiệm $x=c, x=2$.")
        self.build_q(r"Hệ phương trình $\begin{cases} x + y = 5 \\ x - y = 1 \end{cases}$ có nghiệm $x_0$ là", "3", ["2", "4", "1"], r"Cộng 2 vế.")
        self.build_q(r"Nghiệm của PT $x^2 - 5x + 6 = 0$ là", r"$x=2, x=3$", [r"$x=-2, x=-3$", r"$x=1, x=6$", r"$x=-1, x=-6$"], r"Bấm máy tính hoặc Viète.")
        self.build_q(r"Cho PT $x^2 - mx - 2 = 0$. Biết $x_1 - 2x_2 = 5$. Tìm m?", r"$\frac{9}{2}$", [r"$\frac{7}{2}$", r"$5$", r"$4$"], r"Dùng hệ thức Viète.")
        self.build_q(r"Bài toán kinh tế: Bán 1000 sp giá 5tr. Giảm 1tr bán thêm 200 sp. Giá để max doanh thu?", "4 triệu", ["3 triệu", "4.5 triệu", "5 triệu"], r"Lập hàm Parabol doanh thu.")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂU) ---
        self.build_q(r"Với $a < b$, khẳng định nào đúng?", r"$a - 5 < b - 5$", [r"$a + 5 > b + 5$", r"$-2a < -2b$", r"$2a > 2b$"], r"Cộng trừ không đổi chiều.")
        self.build_q(r"Nghiệm của BPT $2x - 4 \ge 0$ là", r"$x \ge 2$", [r"$x \le 2$", r"$x > 2$", r"$x < 2$"], r"Chuyển vế $2x \ge 4$.")
        self.build_q(r"Giá trị nhỏ nhất của $A = \sqrt{x-1} + 3$ là", "3", ["1", "4", "0"], r"Vì $\sqrt{x-1} \ge 0$.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG (5 CÂU) ---
        img_tri = draw_right_triangle('M', 'N', 'P')
        self.build_q(r"Cho tam giác $MNP$ vuông tại $N$ (như hình). Khẳng định đúng là", r"$\cos M = \frac{MN}{MP}$", [r"$\cos M = \frac{NP}{MP}$", r"$\sin M = \frac{MN}{MP}$", r"$\tan M = \frac{MP}{MN}$"], r"Cos = Kề / Huyền.", img_tri)
        self.build_q(r"Cho tam giác vuông có 2 góc nhọn $\alpha, \beta$. Khẳng định đúng là", r"$\sin \alpha = \cos \beta$", [r"$\sin \alpha = \sin \beta$", r"$\tan \alpha = \tan \beta$", r"$\cos \alpha = \cot \beta$"], r"Hai góc phụ nhau chéo nhau.")
        self.build_q(r"Tam giác ABC vuông tại A, $AB=3, AC=4$. Độ dài BC là", "5", ["7", "1", "25"], r"Pytago: $3^2+4^2=25$.")
        self.build_q(r"Độ dài cạnh tam giác đều nội tiếp đường tròn bán kính $R$ là", r"$R\sqrt{3}$", [r"$R\sqrt{2}$", r"$2R$", r"$R$"], r"Dùng định lý Sin.")
        self.build_q(r"Máy bay bay góc $30^\circ$, đi được 10km. Độ cao là?", "5 km", ["8.6 km", "10 km", "7 km"], r"$h = 10 \times \sin(30^\circ)$.")

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN (6 CÂU) ---
        img_cir = draw_circle()
        self.build_q(r"Số điểm chung của hai đường tròn cắt nhau là", "2", ["1", "0", "3"], r"Cắt nhau tại 2 điểm.", img_cir)
        self.build_q(r"Từ điểm $A$ ngoài $(O)$, kẻ được mấy tiếp tuyến?", "2", ["1", "3", "0"], r"Luôn kẻ được 2 tiếp tuyến.")
        self.build_q(r"Góc ở tâm $\widehat{AOB} = 60^\circ$. Số đo cung nhỏ $AB$ là", r"$60^\circ$", [r"$30^\circ$", r"$120^\circ$", r"$90^\circ$"], r"Bằng chính góc ở tâm.")
        self.build_q(r"Bán kính đường tròn nội tiếp hình vuông cạnh $4a$ là", r"$2a$", [r"$4a$", r"$a\sqrt{2}$", r"$2a\sqrt{2}$"], r"Bằng nửa cạnh hình vuông.")
        self.build_q(r"Bán kính đường tròn ngoại tiếp HCN $6 \times 8$ là", "5", ["10", "7", "14"], r"Nửa đường chéo $\sqrt{6^2+8^2}/2$.")
        self.build_q(r"Độ dài cung $60^\circ$ của đường tròn bán kính $R=3$ là", r"$\pi$", [r"$2\pi$", r"$3\pi$", r"$\frac{\pi}{2}$"], r"$l = \frac{\pi R n}{180}$.")

        # --- CHỦ ĐỀ 7: HÌNH KHỐI (3 CÂU) ---
        self.build_q(r"Thể tích khối cầu bán kính $R$ là", r"$\frac{4}{3}\pi R^3$", [r"$\frac{1}{3}\pi R^3$", r"$4\pi R^2$", r"$\pi R^2 h$"], r"Công thức SGK.")
        self.build_q(r"Hình nón có $r=3, l=5$. Diện tích xung quanh là", r"$15\pi$", [r"$30\pi$", r"$12\pi$", r"$20\pi$"], r"$S_{xq} = \pi r l$.")
        self.build_q(r"Thể tích khối lập phương cạnh $2a$ là", r"$8a^3$", [r"$4a^3$", r"$2a^3$", r"$6a^2$"], r"$V = (2a)^3$.")

        # --- CHỦ ĐỀ 8: THỐNG KÊ - XÁC SUẤT (6 CÂU) ---
        self.build_q(r"Không gian mẫu của việc tung 1 đồng xu là", r"$\{S, N\}$", [r"$\{S\}$", r"$\{N\}$", r"$\{1, 2, 3, 4, 5, 6\}$"], r"Có 2 mặt Sấp và Ngửa.")
        self.build_q(r"Bảng: 140cm (4 bạn), 141cm (5 bạn). Số bạn cao 141cm là", "5", ["4", "9", "1"], r"Nhìn vào tần số.")
        self.build_q(r"Giá trị X xuất hiện 5 lần trong N=20. Tần số tương đối là", "25%", ["20%", "5%", "50%"], r"$f = \frac{5}{20} \times 100\%$.")
        
        freqs = [10, 30, 40, 15, 5]
        img_hist = draw_histogram(freqs)
        self.build_q(r"Theo biểu đồ, nhóm học sinh cao [160; 170) chiếm tỉ lệ bao nhiêu?", "40%", ["30%", "15%", "10%"], r"Xem cột cao nhất.", img_hist)
        
        self.build_q(r"Gieo 2 xúc xắc, xác suất cả 2 mặt đều 6 chấm là", r"$\frac{1}{36}$", [r"$\frac{1}{6}$", r"$\frac{2}{6}$", r"$\frac{1}{12}$"], r"1 trường hợp trên 36.")
        self.build_q(r"Chọn 1 số từ 1 đến 10. Xác suất chọn được số nguyên tố là", r"$\frac{2}{5}$", [r"$\frac{1}{2}$", r"$\frac{3}{10}$", r"$\frac{1}{5}$"], r"Các số: 2, 3, 5, 7 (4 số).")

        return self.exam

# ==========================================
# 4. GIAO DIỆN HỆ THỐNG (UI/UX)
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT Tuyên Quang", layout="wide", page_icon="🎓")
    init_db()
    
    # Session States
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    # --- MÀN HÌNH ĐĂNG NHẬP CHUYÊN NGHIỆP ---
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

    # ==========================================
    # GIAO DIỆN HỌC SINH
    # ==========================================
    if st.session_state.role == 'student':
        st.title("📝 Đề Thi Thử Vào 10 THPT (Toán Chung)")
        st.warning("⏱ Thời gian làm bài: 90 phút. Đề thi gồm 40 câu trắc nghiệm bám sát ma trận.")
        
        # Thanh công cụ học sinh
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
            # Hiện điểm nếu đã nộp
            if st.session_state.is_submitted:
                correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                score = (correct / 40) * 10
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    <h4 style="color: #2E7D32;">Đúng {correct} / 40 câu hỏi.</h4>
                </div>
                """, unsafe_allow_html=True)

            # Render 40 Câu hỏi
            st.markdown("---")
            for q in st.session_state.exam_data:
                st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                
                # Render Ảnh Base64 nếu có
                if q['image']:
                    st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:300px; border: 1px solid #ccc; border-radius: 5px;">', unsafe_allow_html=True)
                
                disabled = st.session_state.is_submitted
                selected = st.radio("Chọn đáp án:", options=q['options'], 
                                    index=q['options'].index(st.session_state.user_answers[q['id']]) if st.session_state.user_answers[q['id']] else None,
                                    key=f"q_{q['id']}", disabled=disabled, label_visibility="collapsed")
                
                if not disabled: st.session_state.user_answers[q['id']] = selected

                # Chấm điểm từng câu
                if st.session_state.is_submitted:
                    if selected == q['answer']:
                        st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                    else:
                        st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                    with st.expander("📖 Xem hướng dẫn"):
                        st.markdown(q['hint'], unsafe_allow_html=True)
                st.markdown("---")

            # Nút nộp bài
            if not st.session_state.is_submitted:
                if st.button("📤 NỘP BÀI KIỂM TRA", type="primary", use_container_width=True):
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    score = (correct / 40) * 10
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?, ?, ?, ?)", 
                              (st.session_state.current_user, score, correct, 40 - correct))
                    conn.commit()
                    conn.close()
                    st.session_state.is_submitted = True
                    st.rerun()

    # ==========================================
    # GIAO DIỆN ADMIN (QUẢN TRỊ VIÊN)
    # ==========================================
    elif st.session_state.role == 'admin':
        st.title("⚙ Hệ Thống Quản Trị (Admin Dashboard)")
        
        tab1, tab2 = st.tabs(["📊 Thống kê Kết quả", "👤 Quản lý Tài khoản"])
        
        # TAB 1: THỐNG KÊ
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

        # TAB 2: QUẢN LÝ USER
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
