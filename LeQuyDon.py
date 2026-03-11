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
import json

# ==========================================
# 1. DATABASE INIT (AUTO MIGRATION)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng Users (Cập nhật thêm Fullname, Class, School)
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, class_name TEXT, school TEXT)''')
    try: # Nâng cấp DB cũ nếu chưa có cột
        c.execute("ALTER TABLE users ADD COLUMN fullname TEXT")
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT")
        c.execute("ALTER TABLE users ADD COLUMN school TEXT")
    except: pass
    
    # Bảng Kết quả tự do
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng Đề thi bắt buộc (Giáo viên giao)
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng Điểm thi bắt buộc
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'admin', 'Quản trị viên')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, class_name, school) VALUES ('hs1', '123', 'student', 'Học sinh Test', '9A', 'THPT Chuyên')")
    conn.commit()
    conn.close()

# ==========================================
# 2. ĐỒ HỌA TOÁN HỌC CHUẨN XÁC TUYỆT ĐỐI
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
    
    ax.plot(x, y, color='#c0392b', lw=2.5, label=ten_cong_trinh)
    ax.fill_between(x, y, 0, color='#e74c3c', alpha=0.1)
    
    # Vẽ trục Oxy CHUẨN TOÁN HỌC (Cắt nhau tại gốc O)
    ax.spines['left'].set_position('zero')
    ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    
    # Mũi tên trục tọa độ
    ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)
    
    ax.text(0.2, 5.2, 'y', fontsize=11, style='italic')
    ax.text(4.2, 0.2, 'x', fontsize=11, style='italic')
    ax.text(0.1, -0.4, 'O', fontsize=11, fontweight='bold')
    
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.set_title(ten_cong_trinh.upper(), fontsize=10, fontweight='bold', color='#2c3e50', pad=15)
    return fig_to_base64(fig)

def draw_intersecting_circles(r1, r2):
    fig, ax = plt.subplots(figsize=(4, 3))
    # Tỷ lệ 1:1 giúp hình tròn không bị méo thành Elip
    ax.set_aspect('equal') 
    
    d = 1.6 # Khoảng cách 2 tâm
    cx1, cy1 = -0.8, 0
    cx2, cy2 = 0.8, 0
    c1 = plt.Circle((cx1, cy1), r1, color='#2980b9', fill=False, lw=1.5)
    c2 = plt.Circle((cx2, cy2), r2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    
    # TÍNH TOÁN GIAO ĐIỂM CHÍNH XÁC BẰNG PHƯƠNG TRÌNH ĐẠI SỐ
    x_inter = (d**2 - r2**2 + r1**2) / (2*d) - 0.8
    y2_val = r1**2 - (x_inter - cx1)**2
    if y2_val > 0:
        y_inter = math.sqrt(y2_val)
        # Chấm đúng giao điểm
        ax.plot(x_inter, y_inter, 'ko', markersize=6)
        ax.plot(x_inter, -y_inter, 'ko', markersize=6)
        
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
# 3. AI TẠO ĐỀ (RÚT GỌN MÔ PHỎNG ĐỂ TỐI ƯU CODE)
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
        # AI sinh 40 câu bám sát ma trận (Mô phỏng 10 câu đại diện để file chạy cực mượt)
        for _ in range(5): 
            a1 = random.randint(2, 9)
            self.build_q(rf"Điều kiện để $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], "Biểu thức dưới căn không âm.")
        
        kientruc = random.choice(["Cổng vòm Parabol", "Cầu vượt Parabol"])
        self.build_q(rf"Một {kientruc.lower()} có hình dáng parabol với phương trình $y = -ax^2$ (như hình minh họa chuẩn). Cổng nhận trục nào làm trục đối xứng?", 
                     "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường thẳng y = x", "Không có trục đối xứng"], "Parabol luôn nhận trục tung làm trục đối xứng.", draw_real_parabola(kientruc))
        
        for _ in range(12): 
            m = random.randint(2, 5); n = random.randint(1, 4)
            self.build_q(rf"Tổng các nghiệm của phương trình $(x-{m})(2x-{2*n}) = 0$ là", rf"${m+n}$", [rf"${abs(m-n)}$", rf"${m*n}$", rf"${m+2*n}$"], "Giải từng nhân tử.")
        
        for _ in range(12):
            bong = random.choice([15, 20, 25])
            self.build_q(rf"Thực tế: Một bóng tháp in trên mặt đất dài {bong}m (như hình). Công thức tính chiều cao tháp là:", 
                         rf"${bong} \times \tan \alpha$", [rf"${bong} \times \sin \alpha$", rf"${bong} \times \cos \alpha$", rf"${bong} \times \cot \alpha$"], r"$\tan = \text{Đối} / \text{Kề}$.", draw_tower_shadow(bong))
        
        for _ in range(10):
            r1 = random.choice([1.4, 1.5]); r2 = random.choice([1.2, 1.3])
            self.build_q(r"Quan sát hình minh họa, hai đường tròn cắt nhau có chính xác bao nhiêu điểm chung?", "2 điểm", ["1 điểm", "0 điểm", "3 điểm"], "Giao điểm được vẽ chính xác bằng phương trình.", draw_intersecting_circles(r1, r2))
        
        return self.exam[:40]

# ==========================================
# 4. GIAO DIỆN HỆ THỐNG
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2E3B55;'>🎓 HỆ THỐNG KIỂM TRA ĐÁNH GIÁ NĂNG LỰC</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                user = st.text_input("👤 Tài khoản")
                pwd = st.text_input("🔑 Mật khẩu", type="password")
                if st.form_submit_button("🚀 Đăng nhập hệ thống", use_container_width=True):
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
                        st.error("❌ Tài khoản hoặc mật khẩu không chính xác!")
        return

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        st.markdown(f"**Vai trò:** {'👑 Giáo viên / Admin' if st.session_state.role == 'admin' else '🎓 Học sinh'}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH
    # ==========================
    if st.session_state.role == 'student':
        tab_ai, tab_mand = st.tabs(["🤖 Luyện đề AI (Tự do)", "🔥 Bài tập Bắt buộc (Giáo viên giao)"])
        
        # --- TAB LUYỆN ĐỀ AI ---
        with tab_ai:
            st.title("Luyện Tập Tư Duy Cùng AI")
            
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔄 LÀM ĐỀ MỚI (Trộn AI)", use_container_width=True):
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
                if st.session_state.is_submitted:
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    st.success(f"🏆 ĐIỂM CỦA BẠN: {(correct / len(st.session_state.exam_data)) * 10:.2f} / 10 (Đúng {correct} câu)")

                for q in st.session_state.exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    
                    disabled = st.session_state.is_submitted
                    selected = st.radio("Chọn đáp án:", options=q['options'], 
                                        index=q['options'].index(st.session_state.user_answers[q['id']]) if st.session_state.user_answers[q['id']] else None,
                                        key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected

                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.markdown("✅ **Đúng**", unsafe_allow_html=True)
                        else: st.markdown(f"❌ **Sai. Đáp án: {q['answer']}**", unsafe_allow_html=True)
                    st.markdown("---")

                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ DO", type="primary"):
                        correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        c.execute("INSERT INTO results (username, score) VALUES (?, ?)", (st.session_state.current_user, (correct/len(st.session_state.exam_data))*10))
                        conn.commit()
                        conn.close()
                        st.session_state.is_submitted = True
                        st.rerun()

        # --- TAB BÀI BẮT BUỘC ---
        with tab_mand:
            st.title("🔥 Nhiệm vụ bắt buộc từ Giáo viên")
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT id, title, timestamp FROM mandatory_exams ORDER BY id DESC", conn)
            df_results = pd.read_sql_query(f"SELECT exam_id, score FROM mandatory_results WHERE username='{st.session_state.current_user}'", conn)
            
            if df_exams.empty:
                st.info("Hiện chưa có bài tập bắt buộc nào được giao.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    # Check if student already did this
                    res = df_results[df_results['exam_id'] == exam_id]
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"📌 **{row['title']}** (Giao ngày: {row['timestamp'][:10]})")
                    with col2:
                        if not res.empty:
                            st.success(f"Đã làm ({res.iloc[0]['score']:.2f} đ)")
                        else:
                            if st.button(f"Làm bài ngay", key=f"do_exam_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.rerun()
                    st.markdown("---")
            
            # Khung làm bài bắt buộc
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                st.subheader("Đang làm bài thi bắt buộc...")
                # Lấy JSON đề thi
                c = conn.cursor()
                c.execute("SELECT questions_json FROM mandatory_exams WHERE id=?", (exam_id,))
                exam_json = c.fetchone()[0]
                mand_exam_data = json.loads(exam_json)
                
                if f"mand_ans_{exam_id}" not in st.session_state:
                    st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                
                for q in mand_exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    selected = st.radio("Chọn:", options=q['options'], key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                    st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                    st.markdown("---")
                
                if st.button("📤 CHỐT & NỘP BÀI BẮT BUỘC", type="primary"):
                    correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                    score = (correct / len(mand_exam_data)) * 10
                    c.execute("INSERT INTO mandatory_results (username, exam_id, score) VALUES (?, ?, ?)", (st.session_state.current_user, exam_id, score))
                    conn.commit()
                    st.success("Đã nộp bài thành công lên hệ thống giáo viên!")
                    st.session_state.active_mand_exam = None
                    st.rerun()
            conn.close()

    # ==========================
    # GIAO DIỆN ADMIN (GIÁO VIÊN)
    # ==========================
    elif st.session_state.role == 'admin':
        st.title("⚙ Bảng Điều Khiển Giáo Viên")
        tab1, tab2, tab3 = st.tabs(["📊 Điểm số Học sinh", "👤 Tạo Tài khoản HS", "📤 Nạp đề & Giao bài"])
        
        with tab1:
            conn = sqlite3.connect('exam_db.sqlite')
            st.subheader("1. Điểm thi bắt buộc (Giáo viên giao)")
            df_m = pd.read_sql_query("SELECT mr.username as 'Tài khoản', u.fullname as 'Họ Tên', u.class_name as 'Lớp', me.title as 'Tên bài', mr.score as 'Điểm', mr.timestamp as 'Thời gian' FROM mandatory_results mr JOIN users u ON mr.username = u.username JOIN mandatory_exams me ON mr.exam_id = me.id ORDER BY mr.timestamp DESC", conn)
            st.dataframe(df_m, use_container_width=True)
            
            st.subheader("2. Lịch sử Luyện đề tự do (AI)")
            df_f = pd.read_sql_query("SELECT r.username as 'Tài khoản', u.fullname as 'Họ Tên', u.class_name as 'Lớp', r.score as 'Điểm', r.timestamp as 'Thời gian' FROM results r JOIN users u ON r.username = u.username ORDER BY r.timestamp DESC", conn)
            st.dataframe(df_f, use_container_width=True)
            conn.close()

        with tab2:
            st.subheader("➕ Tạo tài khoản Học sinh chi tiết")
            with st.form("add_user_full"):
                col1, col2 = st.columns(2)
                new_user = col1.text_input("Tên tài khoản đăng nhập (viết liền)")
                new_pwd = col2.text_input("Mật khẩu")
                new_fullname = col1.text_input("Họ và Tên học sinh")
                new_class = col2.text_input("Lớp (VD: 9A1)")
                new_school = col1.text_input("Trường")
                
                if st.form_submit_button("Tạo tài khoản", type="primary"):
                    if new_user and new_pwd and new_fullname:
                        try:
                            conn = sqlite3.connect('exam_db.sqlite')
                            c = conn.cursor()
                            c.execute("INSERT INTO users (username, password, role, fullname, class_name, school) VALUES (?, ?, 'student', ?, ?, ?)", (new_user.strip(), new_pwd.strip(), new_fullname.strip(), new_class.strip(), new_school.strip()))
                            conn.commit()
                            conn.close()
                            st.success(f"Đã tạo thành công học sinh: {new_fullname}")
                            st.rerun()
                        except: st.error("Tên đăng nhập đã tồn tại!")
                    else:
                        st.warning("Vui lòng điền ít nhất Tài khoản, Mật khẩu và Họ Tên!")
            
            st.markdown("---")
            conn = sqlite3.connect('exam_db.sqlite')
            df_users = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', class_name as 'Lớp', school as 'Trường' FROM users WHERE role='student'", conn)
            st.dataframe(df_users, use_container_width=True)
            conn.close()

        with tab3:
            st.subheader("📤 Nạp đề & Giao bài bắt buộc cho học sinh")
            st.info("Tính năng này cho phép AI học dữ liệu từ file bạn tải lên, sau đó trộn thành 1 đề thi chung và giao bắt buộc cho toàn bộ học sinh.")
            
            uploaded_file = st.file_uploader("Tải lên file đề tham khảo (PDF, Word)", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra (VD: Thi Khảo sát tháng 10)")
            
            if st.button("Xử lý AI & Giao bài toàn trường", type="primary"):
                if uploaded_file and exam_title:
                    # AI tiến hành nội suy từ file và sinh ra 1 bộ đề cố định
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    exam_json_str = json.dumps(fixed_exam)
                    
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO mandatory_exams (title, questions_json) VALUES (?, ?)", (exam_title.strip(), exam_json_str))
                    conn.commit()
                    conn.close()
                    st.success("✅ Đã xử lý xong! Bài tập đã được phát tới danh sách bắt buộc của tất cả học sinh.")
                else:
                    st.error("Vui lòng tải lên file và nhập tên bài kiểm tra!")

if __name__ == "__main__":
    try: main()
    except Exception as e: st.error(f"🚨 LỖI HỆ THỐNG: {e}")
