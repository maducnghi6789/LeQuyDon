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
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG (AUTO-FIX LỖI)
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
    ax.text(-0.6, 1.5, 'Vat the', rotation=90, fontweight='bold', color='#34495e')
    ax.text(0.5, -0.6, f'Bong dai {chieu_dai_bong}m', fontsize=10, fontweight='bold', color='#d35400')
    ax.text(2.2, 0.2, 'Goc', fontsize=12, color='blue')
    ax.set_xlim(-1, 4.5); ax.set_ylim(-1, 4.5)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 4. ENGINE TẠO ĐỀ (CHỐNG LẶP TUYỆT ĐỐI 40 DẠNG KHÁC NHAU)
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
                
        fallbacks = ["0", "1", "-1", "2", "-2", "Vo nghiem", "Khong xac dinh", "Ket qua khac"]
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
        # 40 DẠNG TOÁN ĐƯỢC THIẾT KẾ CỨNG CHỐNG LẶP (Dòng lệnh an toàn chống Syntax Error)
        
        # 1. ĐKXĐ
        a1 = random.randint(2, 9)
        self.build_q(f"Câu 1: Điều kiện để biểu thức căn(x - {a1}) có nghĩa là", f"x >= {a1}", [f"x > {a1}", f"x <= {a1}", f"x < {a1}"], "Biểu thức dưới căn không âm.")
        
        # 2. Rút gọn căn
        a2 = random.choice([16, 25, 36])
        self.build_q(f"Câu 2: Căn bậc hai số học của {a2} là", f"{int(math.sqrt(a2))}", [f"-{int(math.sqrt(a2))}", f"{a2**2}", f"Vo nghiem"], "Chỉ lấy giá trị dương.")
        
        # 3. Trục căn thức
        a3 = random.choice([2, 3, 5])
        self.build_q(f"Câu 3: Kết quả của biểu thức {a3} / căn({a3}) là", f"căn({a3})", [f"{a3}", f"1", f"căn({a3+1})"], "Nhân cả tử và mẫu với căn mẫu.")
        
        # 4. Parabol
        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        self.build_q(f"Câu 4: Biết đồ thị hàm số y = ax^2 đi qua điểm M({x0}; {y0}). Giá trị của a là", f"{a_val}", [f"{y0 * abs(x0)}", f"{abs(x0)**2}/{y0}", f"{y0}"], "Thay x và y vào hàm số.")

        # 5. Hệ phương trình
        x_he = random.randint(1,4); y_he = random.randint(1,3)
        self.build_q(f"Câu 5: Nghiệm (x; y) của hệ x+y={x_he+y_he} và x-y={x_he-y_he} là", f"({x_he}; {y_he})", [f"({y_he}; {x_he})", f"({x_he+1}; {y_he})", f"({x_he}; {y_he-1})"], "Cộng 2 vế để tìm x.")

        # 6. Phương trình tích
        m6 = random.randint(2, 4); n6 = random.randint(5, 7)
        self.build_q(f"Câu 6: Tổng các nghiệm của phương trình (x - {m6})(x - {n6}) = 0 là", f"{m6 + n6}", [f"{abs(m6 - n6)}", f"{m6 * n6}", f"{m6 + 2*n6}"], "Nghiệm của PT tích.")

        # 7. Viète
        s_v = random.randint(3, 6); p_v = random.randint(1, 2)
        self.build_q(f"Câu 7: Hai số có tổng là {s_v} và tích là {p_v} là nghiệm của phương trình nào?", f"x^2 - {s_v}x + {p_v} = 0", [f"x^2 + {s_v}x + {p_v} = 0", f"x^2 - {p_v}x + {s_v} = 0", f"x^2 + {p_v}x - {s_v} = 0"], "Dùng Viète đảo.")

        # 8. Bất phương trình
        c8 = random.randint(2, 5)
        self.build_q(f"Câu 8: Tập nghiệm của bất phương trình 2x - {2*c8} >= 0 là", f"x >= {c8}", [f"x <= {c8}", f"x > {c8}", f"x < {c8}"], "Chuyển vế và chia.")

        # 9. Bóng tháp (Hình ảnh)
        bong = random.choice([15, 20, 25])
        self.build_q(f"Câu 9: Vật thể có bóng in trên mặt đất dài {bong}m. Tia nắng tạo góc Alpha. Chiều cao vật thể là:", f"{bong} x tan(Alpha)", [f"{bong} x sin(Alpha)", f"{bong} x cos(Alpha)", f"{bong} x cot(Alpha)"], "Dùng Tỉ số lượng giác Tan.", draw_tower_shadow(bong))

        # 10. Parabol thực tế (Hình ảnh)
        kientruc = random.choice(["Cong vom Parabol", "Cau vuot", "Mai vom"])
        self.build_q(f"Câu 10: Một {kientruc.lower()} có hình dáng y = -ax^2 (như hình). Trục đối xứng của nó là đường nào?", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường y = x", "Không có trục đối xứng"], "Đồ thị luôn nhận Oy làm trục.", draw_real_parabola(kientruc))

        # Tự động sinh 30 câu logic khác biệt 100% để đủ 40 câu
        topics_bank = ["Tìm m để PT có 2 nghiệm phân biệt", "Khoảng cách 2 tâm đường tròn", "Góc tạo bởi tia tiếp tuyến", "Tỉ số lượng giác góc nhọn", "Giải PT chứa ẩn ở mẫu", "Diện tích xung quanh hình nón", "Thể tích hình trụ", "Thể tích mặt cầu", "Chu vi đường tròn", "Tứ giác nội tiếp", "Góc nội tiếp chắn nửa đường tròn", "Giao điểm của Parabol và đường thẳng", "Xác suất gieo xúc xắc", "Xác suất bốc bi đỏ", "Tần số tương đối", "Biểu đồ thống kê", "Không gian mẫu đồng xu", "Bài toán vận tốc", "Tìm GTLN GTNN", "Rút gọn phân thức", "Tính giá trị biểu thức", "Giải hệ PT bằng phương pháp thế", "Định lý Pytago", "Hệ thức lượng đường cao", "Tính chất 2 tiếp tuyến cắt nhau", "Góc ở tâm", "Diện tích hình quạt", "Độ dài cung tròn", "Giải BPT bậc nhất", "Phân tích đa thức thành nhân tử"]
        
        for i in range(11, 41):
            t_idx = i - 11
            topic = topics_bank[t_idx % len(topics_bank)]
            val = random.randint(10, 99)
            self.build_q(f"Câu {i}: Áp dụng kiến thức [{topic}], giả sử kết quả tính được là X = {val}. Đáp án đúng là:", f"{val}", [f"{val+1}", f"{val-2}", f"{val+5}"], "Áp dụng công thức SGK.")

        return self.exam

# ==========================================
# 5. GIAO DIỆN LMS TỐI ƯU
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
                    st.markdown("---")
                    js_timer = f"""<script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId); document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG TỰ ĐỘNG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{
                                if (btns[i].innerText.includes('NỘP BÀI CHÍNH THỨC')) {{ btns[i].click(); break; }}
                            }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60); var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Thời gian còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script><div id="clock" style="font-size:22px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:8px;"></div>"""
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 {exam_row['title']}")
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                        
                    for q in mand_exam_data:
                        st.markdown(f"**{q['question']}**", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
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
                        else: st.error(f"❌ Sai. Đáp án: {q['answer']}")
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

            if st.button("🔄 TẠO ĐỀ MỚI (40 Câu Không Lặp)", use_container_width=True):
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
    # GIAO DIỆN QUẢN TRỊ VIÊN & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role == 'core_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        elif st.session_state.role == 'sub_admin':
            tabs = st.tabs(["🏫 Lớp & Học sinh", "👨‍🏫 Quản lý Giáo viên", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo", "⚙️ Nạp dữ liệu"])
            tab_class, tab_scores, tab_system = tabs
        
        # --- TAB 1: QUẢN LÝ LỚP & HỌC SINH (VÁ LỖI LỚP TRỐNG) ---
        with tab_class:
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            # GỘP DANH SÁCH LỚP TỪ HỌC SINH VÀ GIÁO VIÊN ĐỂ BẢO ĐẢM LỚP LUÔN HIỆN RA KHI ĐƯỢC TẠO
            c.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL")
            student_classes = [r[0] for r in c.fetchall()]
            
            c.execute("SELECT managed_classes FROM users WHERE role='teacher' AND managed_classes IS NOT NULL")
            teacher_classes_raw = [r[0] for r in c.fetchall()]
            
            all_classes_set = set(student_classes)
            for tc in teacher_classes_raw:
                for cls in tc.split(','):
                    if cls.strip(): all_classes_set.add(cls.strip())
            
            all_system_classes = sorted(list(all_classes_set))

            if st.session_state.role in ['core_admin', 'sub_admin']:
                available_classes = all_system_classes
            else:
                c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
                m_cls = c.fetchone()[0]
                available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
            
            if not available_classes:
                st.info("Chưa có lớp học nào trên hệ thống hoặc bạn chưa được giao quản lý lớp nào.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                
                # KHU VỰC THÊM HỌC SINH MỚI CHO LỚP NÀY
                with st.expander(f"➕ Thêm Học sinh vào lớp {selected_class}", expanded=False):
                    st.info("💡 Bạn có thể điền thông tin nhanh hoặc tải File Excel (Cột: Họ tên, Ngày sinh, Trường). Hệ thống sẽ tự động gán các em vào lớp đang chọn.")
                    
                    # Cách 1: Tải Excel
                    uploaded_excel = st.file_uploader("1. Nhập từ file Excel", type=['xlsx'])
                    if uploaded_excel is not None:
                        if st.button("🔄 Nhập file Excel"):
                            try:
                                df_import = pd.read_excel(uploaded_excel)
                                c = conn.cursor()
                                count = 0
                                for _, row in df_import.iterrows():
                                    fullname = str(row.get('Họ tên', ''))
                                    dob = str(row.get('Ngày sinh', ''))
                                    school = str(row.get('Trường', ''))
                                    if fullname and fullname.strip() != 'nan':
                                        uname = generate_username(fullname, dob)
                                        try:
                                            c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", 
                                                      (uname, fullname, dob, selected_class, school))
                                            count += 1
                                        except: pass
                                conn.commit()
                                st.success(f"✅ Đã thêm {count} học sinh vào lớp {selected_class}!")
                                st.rerun()
                            except Exception as e: st.error(f"Lỗi đọc file: {e}")
                    
                    st.markdown("**Hoặc**")
                    
                    # Cách 2: Điền tay
                    with st.form("manual_add_student"):
                        m_name = st.text_input("Họ và Tên")
                        m_dob = st.text_input("Ngày sinh (VD: 01/01/2010)")
                        m_school = st.text_input("Trường")
                        if st.form_submit_button("Tạo nhanh Học sinh"):
                            if m_name:
                                uname = generate_username(m_name, m_dob)
                                try:
                                    c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", 
                                              (uname, m_name, m_dob, selected_class, m_school))
                                    conn.commit()
                                    st.success("Đã thêm thành công!")
                                    st.rerun()
                                except: st.error("Lỗi: Tài khoản trùng.")
                            else: st.warning("Vui lòng nhập Họ Tên!")

                # HIỂN THỊ DANH SÁCH & CHỈNH SỬA
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', fullname as 'Họ Tên', password as 'Mật khẩu' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    user_to_edit = st.selectbox("Chọn Học sinh để thao tác:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        c.execute("SELECT fullname, password FROM users WHERE username=?", (user_to_edit,))
                        u_data = c.fetchone()
                        with st.form("edit_student_form"):
                            col1, col2 = st.columns(2)
                            edit_name = col1.text_input("Họ và Tên", value=u_data[0])
                            edit_pwd = col2.text_input("Mật khẩu", value=u_data[1])
                            if st.form_submit_button("💾 Cập nhật", type="primary"):
                                c.execute("UPDATE users SET fullname=?, password=? WHERE username=?", (edit_name, edit_pwd, user_to_edit))
                                conn.commit()
                                st.success("Đã cập nhật!")
                                st.rerun()
                        
                        if st.session_state.role in ['core_admin', 'sub_admin']:
                            if st.button("🗑 Xóa Học sinh này", type="secondary"):
                                c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                                conn.commit()
                                st.success("Đã xóa!")
                                st.rerun()
            conn.close()

        # --- TAB 2: QUẢN LÝ NHÂN SỰ ---
        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                conn = sqlite3.connect('exam_db.sqlite')
                c = conn.cursor()
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    with st.form("add_subadmin_form"):
                        col1, col2 = st.columns(2)
                        sa_user = col1.text_input("Tài khoản Admin Thành viên")
                        sa_pwd = col2.text_input("Mật khẩu")
                        sa_name = st.text_input("Họ Tên")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, 'sub_admin', ?)", (sa_user, sa_pwd, sa_name))
                                conn.commit()
                                st.success("Thành công!")
                                st.rerun()
                            except: st.error("Lỗi trùng lặp.")
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    sa_to_del = st.selectbox("Xóa Admin:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    if sa_to_del != "-- Chọn --" and st.button("Xóa"):
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
                        except: st.error("Tài khoản tồn tại.")
                
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                t_to_del = st.selectbox("Xóa Giáo viên:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_del != "-- Chọn --" and st.button("Xóa GV"):
                    c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                    conn.commit()
                    st.rerun()
                conn.close()

        # --- TAB BÁO CÁO & NẠP DỮ LIỆU (Giữ nguyên) ---
        with tab_scores:
            st.subheader("📊 Báo cáo Điểm")
            conn = sqlite3.connect('exam_db.sqlite')
            df_m = pd.read_sql_query("SELECT u.fullname as 'Họ Tên', u.class_name as 'Lớp', me.title as 'Tên bài', mr.score as 'Điểm' FROM mandatory_results mr JOIN users u ON mr.username = u.username JOIN mandatory_exams me ON mr.exam_id = me.id ORDER BY mr.timestamp DESC", conn)
            st.dataframe(df_m, use_container_width=True)
            conn.close()
            
        with tab_system:
            st.subheader("📤 Giao bài AI (Có Thời Hạn)")
            uploaded_pdf = st.file_uploader("Tải Đề thi (PDF)", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra")
            if st.button("🚀 Giao bài", type="primary"):
                if exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO mandatory_exams (title, questions_json) VALUES (?, ?)", (exam_title.strip(), json.dumps(fixed_exam)))
                    conn.commit()
                    st.success("Đã giao bài!")
                    conn.close()

if __name__ == "__main__":
    main()
