# ==========================================
# QUAN TRỌNG: 2 DÒNG NÀY PHẢI NẰM TRÊN CÙNG
# ==========================================
import matplotlib
matplotlib.use('Agg')

import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

# ==========================================
# 1. DATABASE INIT & SECURITY
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # BẢO MẬT: TÀI KHOẢN ADMIN GỐC 
    c.execute("INSERT OR IGNORE INTO users VALUES ('maducnghi6789@gmail.com', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student')")
    conn.commit()
    conn.close()

# ==========================================
# 2. HỆ THỐNG VẼ HÌNH ĐỒ HỌA SINH ĐỘNG
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#f8f9fa', dpi=200)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(-4, 4, 100)
    y = -0.3 * x**2 + 5
    
    ax.plot(x, y, color='#c0392b', lw=3.5, label="Cổng vòm")
    ax.fill_between(x, y, 0, color='#e74c3c', alpha=0.15)
    ax.axhline(0, color='#2980b9', lw=4, label="Mặt đường")
    
    ax.axvline(0, color='black', lw=1, linestyle='--')
    ax.text(0.2, 5.2, 'y', fontsize=10, style='italic')
    ax.text(4.2, 0.2, 'x', fontsize=10, style='italic')
    ax.text(0.2, -0.6, 'O', fontsize=10, fontweight='bold')
    
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.axis('off')
    return fig_to_base64(fig)

def draw_tower_shadow():
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([-1, 5], [0, 0], color='#27ae60', lw=4) 
    ax.plot([0, 0], [0, 4], color='#7f8c8d', lw=6)
    ax.plot([3, 0], [0, 4], color='#f39c12', lw=2, linestyle='--')
    
    ax.plot([0, 0.3, 0.3, 0], [0.3, 0.3, 0, 0], color='red', lw=1.5)
    arc = patches.Arc((3, 0), 1, 1, angle=0, theta1=120, theta2=180, color='blue', lw=2)
    ax.add_patch(arc)
    
    ax.text(-0.8, 2, 'Tháp', rotation=90, fontweight='bold', color='#34495e')
    ax.text(1.2, -0.5, 'Bóng trên mặt đất', fontsize=9)
    ax.text(2.2, 0.2, r'$\alpha$', fontsize=12, color='blue')
    
    ax.set_xlim(-1, 4); ax.set_ylim(-1, 4.5)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_vivid_histogram(freqs):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    
    colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#e67e22']
    bars = ax.bar(bins, percents, color=colors, edgecolor='#2c3e50', linewidth=1)
    
    ax.set_title("BIỂU ĐỒ KHẢO SÁT THỰC TẾ", fontweight='bold', color='#c0392b', pad=15)
    ax.set_ylabel('Tỉ lệ (%)', fontweight='bold')
    ax.grid(axis='y', linestyle=':', alpha=0.7)
    
    for bar, v in zip(bars, percents): 
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{round(v)}%", ha='center', fontweight='bold')
    ax.set_ylim(0, max(percents) + 15)
    return fig_to_base64(fig)

# ==========================================
# 3. AI TẠO ĐỀ: 40 CÂU HỎI BÁM SÁT MA TRẬN
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
        for _ in range(2): 
            a = random.randint(2, 9)
            self.build_q(rf"Điều kiện để $\sqrt{{x-{a}}}$ có nghĩa là", rf"$x \ge {a}$", [rf"$x > {a}$", rf"$x \le {a}$", rf"$x < {a}$"], "Biểu thức dưới dấu căn $\ge 0$.")
        for _ in range(2): 
            sq = random.choice([16, 25, 36, 49, 64, 81])
            rt = int(math.sqrt(sq))
            self.build_q(rf"Căn bậc hai số học của ${sq}$ là", rf"${rt}$", [rf"-${rt}$", rf"${rt}$ và -${rt}$", rf"${sq**2}$"], "Căn bậc hai số học chỉ lấy giá trị dương.")
        for _ in range(2): 
            a = random.randint(2, 5); b = random.randint(1, 4)
            self.build_q(rf"Với $x < {a}$, rút gọn $\sqrt{{({a}-x)^2}} + x - {b}$ ta được", rf"${a-b}$", [rf"${b-a}$", rf"$2x - {a+b}$", rf"${a+b}$"], r"Do $x<a$ nên $|a-x| = a-x$.")

        # --- CHỦ ĐỀ 2: HÀM SỐ & PARABOL THỰC TẾ (3 CÂU) ---
        self.build_q(r"Một chiếc cổng hình parabol có phương trình $y=-ax^2$ (như hình minh họa). Cổng nhận đường thẳng nào làm trục đối xứng?", 
                     "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường thẳng y=x", "Không có trục đối xứng"], 
                     "Parabol $y=ax^2$ luôn nhận trục tung làm trục đối xứng.", draw_real_parabola())
        for _ in range(2):
            x0 = random.choice([2, 3]); y0 = random.choice([4, 9, 12, 18])
            self.build_q(rf"Đồ thị hàm số $y=ax^2$ đi qua điểm $M({x0}; {y0})$. Giá trị của $a$ là", rf"${y0}/{x0**2}$" if y0%(x0**2)!=0 else rf"${y0//(x0**2)}$", 
                         [rf"${y0*x0}$", rf"${x0**2}/{y0}$", rf"${y0}$"], "Thay tọa độ x, y vào phương trình để tìm a.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & BÀI TOÁN KINH TẾ (8 CÂU) ---
        for _ in range(3): 
            self.build_q(r"Hệ phương trình nào sau đây KHÔNG phải là hệ bậc nhất hai ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", 
                         [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} 3x - y = 1 \\ x + y = 2 \end{cases}$"], "Hệ bậc nhất không chứa căn của ẩn.")
        for _ in range(4): 
            m = random.randint(2, 5); n = random.randint(1, 4)
            self.build_q(rf"Tổng các nghiệm của phương trình $(x-{m})(2x-{2*n}) = 0$ là", rf"${m+n}$", [rf"${abs(m-n)}$", rf"${m*n}$", rf"${m+2*n}$"], "Giải từng nhân tử bằng 0 rồi cộng lại.")
        
        price = random.choice([5, 6, 7]); drop = random.choice([1, 2])
        self.build_q(rf"Một cửa hàng bán {price*100} áo/tháng với giá {price} trăm nghìn/áo. Giảm giá {drop} trăm nghìn thì bán thêm 50 áo. Để doanh thu cực đại, hàm số doanh thu lập được là hàm bậc mấy?", 
                     "Bậc 2", ["Bậc 1", "Bậc 3", "Bậc 4"], "Doanh thu tạo ra hàm bậc 2 (Parabol).")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂU) ---
        for _ in range(3):
            c = random.randint(2, 5)
            self.build_q(rf"Nghiệm của bất phương trình $2x - {2*c} \ge 0$ là", rf"$x \ge {c}$", [rf"$x \le {c}$", rf"$x > {c}$", rf"$x < {c}$"], "Chuyển vế và chia cho số dương.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG THỰC TẾ (5 CÂU) ---
        self.build_q(r"Một bóng tháp in trên mặt đất dài 15m. Tia nắng mặt trời tạo với mặt đất một góc $\alpha$ (như hình minh họa). Công thức tính chiều cao tháp là:", 
                     r"$15 \times \tan \alpha$", [r"$15 \times \sin \alpha$", r"$15 \times \cos \alpha$", r"$15 \times \cot \alpha$"], 
                     r"Sử dụng Tỉ số lượng giác: $\tan = \text{Đối} / \text{Kề}$. Chiều cao = Bóng $\times \tan \alpha$.", draw_tower_shadow())
        for _ in range(4):
            c1, c2, huyen = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17)])
            self.build_q(rf"Tam giác ABC vuông tại A, hai cạnh góc vuông là {c1} và {c2}. Cạnh huyền bằng", rf"${huyen}$", [rf"${c1+c2}$", rf"${abs(c1-c2)}$", rf"${huyen+1}$"], "Áp dụng định lý Pytago.")

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN (6 CÂU) ---
        for _ in range(6):
            r = random.choice([3, 4, 5]); d = r*2
            self.build_q(rf"Bán kính đường tròn ngoại tiếp hình chữ nhật có đường chéo dài {d} cm là", rf"${r}$ cm", [rf"${d}$ cm", rf"${d*2}$ cm", rf"${r*2}$ cm"], "Bán kính bằng một nửa đường chéo.")

        # --- CHỦ ĐỀ 7: HÌNH KHỐI THỰC TẾ (3 CÂU) ---
        for _ in range(3):
            bk = random.choice([2, 3]); cao = random.choice([5, 10])
            self.build_q(rf"Một bồn nước hình trụ có bán kính đáy {bk}m, chiều cao {cao}m. Thể tích bồn nước là", rf"${bk**2 * cao}\pi$ $m^3$", [rf"${bk * cao}\pi$ $m^3$", rf"${2*bk * cao}\pi$ $m^3$", rf"${bk**2 * cao}$ $m^3$"], r"Công thức: $V = \pi r^2 h$.")

        # --- CHỦ ĐỀ 8: THỐNG KÊ XÁC SUẤT (6 CÂU) ---
        freqs = [random.randint(10, 40) for _ in range(5)]
        max_idx = freqs.index(max(freqs))
        bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
        self.build_q(rf"Dựa vào biểu đồ khảo sát thực tế, nhóm chiều cao nào có tỉ lệ học sinh đông nhất?", 
                     rf"Nhóm {bins[max_idx]}", [rf"Nhóm {bins[(max_idx+1)%5]}", rf"Nhóm {bins[(max_idx+2)%5]}", rf"Nhóm {bins[(max_idx+3)%5]}"], 
                     "Quan sát biểu đồ, cột nào cao nhất tương ứng với tỉ lệ lớn nhất.", draw_vivid_histogram(freqs))
        for _ in range(5):
            name = random.choice(["An", "Bình", "Châu", "Dương"])
            self.build_q(rf"Bạn {name} gieo một con xúc xắc cân đối. Xác suất để xuất hiện mặt chẵn (2, 4, 6) là", r"$\frac{1}{2}$", [r"$\frac{1}{6}$", r"$\frac{1}{3}$", r"$\frac{2}{3}$"], "Có 3 mặt chẵn trên tổng 6 mặt.")

        return self.exam[:40]

# ==========================================
# 4. GIAO DIỆN HỆ THỐNG
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    if st.session_state.current_user is None:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #2E3B55;'>🎓 HỆ THỐNG KIỂM TRA ĐÁNH GIÁ NĂNG LỰC</h1>
            <p style='color: #777; font-size: 18px;'>Kỳ thi tuyển sinh vào lớp 10 THPT (Toán Thực Tế)</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### 🔒 Cổng Đăng Nhập")
                user = st.text_input("👤 Tài khoản (Email / ID)")
                pwd = st.text_input("🔑 Mật khẩu", type="password")
                submitted = st.form_submit_button("🚀 Đăng nhập hệ thống", use_container_width=True)
                
                if submitted:
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("SELECT role FROM users WHERE username=? AND password=?", (user.strip(), pwd.strip()))
                    res = c.fetchone()
                    conn.close()
                    if res:
                        st.session_state.current_user = user.strip()
                        st.session_state.role = res[0]
                        st.rerun()
                    else:
                        st.error("❌ Tài khoản hoặc mật khẩu không chính xác!")
        return

    with st.sidebar:
        st.markdown(f"### 👤 Xin chào, **{st.session_state.current_user}**")
        st.markdown(f"**Vai trò:** {'👑 Quản trị viên' if st.session_state.role == 'admin' else '🎓 Học sinh'}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.role == 'student':
        st.title("📝 Đề Thi Thử Vào 10 THPT (Toán Thực Tế)")
        st.warning("⏱ Thời gian: 90 phút. Đề thi gồm 40 câu trắc nghiệm AI sinh tự động.")
        
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
                score = (correct / 40) * 10
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    <h4 style="color: #2E7D32;">Đúng {correct} / 40 câu hỏi.</h4>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            for q in st.session_state.exam_data:
                st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                if q['image']:
                    st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:400px; border-radius: 8px; box-shadow: 2px 4px 10px rgba(0,0,0,0.15); margin-bottom: 15px;">', unsafe_allow_html=True)
                
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
                    with st.expander("📖 Xem hướng dẫn tư duy"):
                        st.markdown(q['hint'], unsafe_allow_html=True)
                st.markdown("---")

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

    # --- GIAO DIỆN ADMIN ---
    elif st.session_state.role == 'admin':
        st.title("⚙ Hệ Thống Quản Trị")
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
            
            safe_users = [u for u in df_users['Tài khoản'] if u != 'maducnghi6789@gmail.com' and u != st.session_state.current_user]
            with st.form("del_user"):
                del_u = st.selectbox("Chọn tài khoản", ["-- Chọn --"] + safe_users)
                if st.form_submit_button("Xóa vĩnh viễn"):
                    if del_u != "-- Chọn --":
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (del_u,))
                        c.execute("DELETE FROM results WHERE username=?", (del_u,))
                        conn.commit()
                        conn.close()
                        st.success(f"Đã xóa {del_u}")
                        st.rerun()

# ==========================================
# KHỐI LỆNH CHẠY APP CÓ BẢO VỆ (TRY-CATCH TỰ ĐỘNG BÁO LỖI)
# ==========================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🚨 HỆ THỐNG PHÁT HIỆN LỖI: {e}")
        st.warning("Bạn hãy chụp ảnh dòng lỗi màu đỏ ở trên và gửi cho tôi để fix ngay nhé!")
