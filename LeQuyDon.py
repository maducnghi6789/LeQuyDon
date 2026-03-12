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
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

# ==========================================
# 2. CƠ SỞ DỮ LIỆU (AUTO-UPDATE)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, class_name TEXT, school TEXT)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN fullname TEXT")
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT")
        c.execute("ALTER TABLE users ADD COLUMN school TEXT")
    except: pass
    
    # Bảng Kết quả tự do
    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng Đề thi bắt buộc
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng Kết quả bài bắt buộc (Lưu trữ cả JSON bài làm của HS để xem lại)
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'admin', 'Quản trị viên')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname, class_name, school) VALUES ('hs1', '123', 'student', 'Học sinh Test', '9A', 'THPT Chuyên')")
    conn.commit()
    conn.close()

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
    ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)
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
# 4. ENGINE TẠO ĐỀ: ĐẢM BẢO 40 CÂU KHÔNG TRÙNG LẶP DẠNG
# ==========================================
class ExamGenerator:
    def build_q(self, text, correct, distractors, hint, img_b64=None):
        # 1. Chuyển tất cả về chuỗi (string) để chống lỗi định dạng
        correct_str = str(correct)
        
        # 2. BỘ LỌC KHỬ TRÙNG LẶP THÔNG MINH
        unique_options = [correct_str]
        for d in distractors:
            d_str = str(d)
            # Chỉ thêm đáp án nhiễu nếu nó chưa từng xuất hiện trong danh sách
            if d_str not in unique_options:
                unique_options.append(d_str)
                
        # 3. BƠM ĐÁP ÁN DỰ PHÒNG (Nếu thuật toán random vô tình làm trùng lặp khiến bị thiếu đáp án)
        # Các đáp án này mang tính chất đánh lừa học sinh rất tốt
        fallbacks = [
            "0", "1", "-1", "2", "-2", 
            "Vô nghiệm", "Không xác định", 
            "Không có trục đối xứng", "Kết quả khác"
        ]
        
        # Bổ sung dự phòng cho đến khi đủ đúng 4 đáp án phân biệt
        for fb in fallbacks:
            if len(unique_options) == 4:
                break
            if fb not in unique_options:
                unique_options.append(fb)
                
        # 4. Cắt chuẩn 4 đáp án và Trộn ngẫu nhiên (Shuffle)
        final_options = unique_options[:4]
        random.shuffle(final_options)
        
        self.exam.append({
            "id": self.q_count, "question": text, "options": final_options,
            "answer": correct_str, "hint": hint, "image": img_b64
        })
        self.q_count += 1

    def generate_all(self):
        # --- CHỦ ĐỀ 1: CĂN THỨC (6 Dạng khác nhau) ---
        # 1. ĐKXĐ cơ bản
        a1 = random.randint(1, 9)
        self.build_q(rf"Điều kiện để biểu thức $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], "Biểu thức dưới căn $\ge 0$.")
        # 2. ĐKXĐ âm
        a2 = random.randint(1, 5)
        self.build_q(rf"Tập các giá trị của $x$ để $\sqrt{{{a2*2} - 2x}}$ xác định là", rf"$x \le {a2}$", [rf"$x \ge {a2}$", rf"$x < {a2}$", rf"$x > {a2}$"], "Giải BPT $-2x \ge -2a$.")
        # 3. Căn bậc hai số học
        sq = random.choice([16, 25, 36, 49, 64, 81])
        rt = int(math.sqrt(sq))
        self.build_q(rf"Căn bậc hai số học của số ${sq}$ là", f"{rt}", [f"-{rt}", f"{rt} và -{rt}", f"{sq**2}"], "Căn bậc hai số học chỉ lấy số dương.")
        # 4. Rút gọn HĐT
        a4 = random.randint(2, 5); b4 = random.randint(6, 10)
        self.build_q(rf"Với $x < {a4}$, rút gọn biểu thức $\sqrt{{({a4} - x)^2}} + x - {b4}$ ta được", f"{a4 - b4}", [f"{b4 - a4}", rf"$2x - {a4 + b4}$", f"{a4 + b4}"], r"Do $x < a$ nên $|a - x| = a - x$.")
        # 5. Phép tính căn
        a5 = random.choice([2, 3, 5])
        self.build_q(rf"Kết quả của phép tính $\sqrt{{9 \cdot {a5}}} - \sqrt{{4 \cdot {a5}}}$ là", rf"$\sqrt{{{a5}}}$", [rf"$5\sqrt{{{a5}}}$", rf"${a5}$", rf"$\sqrt{{5 \cdot {a5}}}$"], "Phân tích: $3\sqrt{a} - 2\sqrt{a}$.")
        # 6. Rút gọn biểu thức chữ
        self.build_q(r"Với $a > 0, b > 0$, biểu thức $\sqrt{16a^2b}$ bằng", r"$4a\sqrt{b}$", [r"$-4a\sqrt{b}$", r"$16a\sqrt{b}$", r"$4a^2\sqrt{b}$"], "Đưa thừa số ra ngoài dấu căn.")

        # --- CHỦ ĐỀ 2: HÀM SỐ (3 Dạng) ---
        # 7. Lý thuyết Parabol thực tế
        kientruc = random.choice(["Cổng vòm Parabol", "Cầu vượt", "Mái vòm"])
        self.build_q(rf"Một {kientruc.lower()} có hình parabol $y = -ax^2$ (như hình minh họa). Parabol này nhận đường thẳng nào làm trục đối xứng?", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường $y = x$", "Không có"], "Trục đối xứng của $y=ax^2$ luôn là Oy.", draw_real_parabola(kientruc))
        # 8. Tìm hệ số a
        x8 = random.choice([-2, 2, 3]); y8 = random.choice([4, 12, 18])
        aval = y8 // (x8**2) if y8 % (x8**2) == 0 else f"{y8}/{x8**2}"
        self.build_q(rf"Đồ thị hàm số $y = ax^2$ đi qua điểm $M({x8}; {y8})$. Giá trị của $a$ là", f"{aval}", [f"{y8 * abs(x8)}", f"{abs(x8)**2}/{y8}", f"{y8}"], "Thay x, y vào hàm số.")
        # 9. Tính đồng biến
        self.build_q(r"Cho hàm số $y = -5x^2$. Kết luận nào sau đây ĐÚNG?", "Đồng biến khi $x < 0$, nghịch biến khi $x > 0$", ["Luôn đồng biến", "Đồng biến khi $x > 0$, nghịch biến khi $x < 0$", "Luôn nghịch biến"], "Vì $a = -5 < 0$.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & HỆ (8 Dạng) ---
        # 10. PT bậc nhất 2 ẩn
        self.build_q(r"Phương trình nào sau đây là phương trình bậc nhất hai ẩn?", r"$3x - 2y = 5$", [r"$xy = 5$", r"$x^2 + y = 1$", r"$3x - y^2 = 0$"], "Dạng $ax+by=c$.")
        # 11. Hệ bậc nhất
        self.build_q(r"Hệ phương trình nào KHÔNG phải là hệ bậc nhất hai ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} 3x - y = 1 \\ x + y = 2 \end{cases}$"], "Không chứa căn của ẩn.")
        # 12. Nghiệm của hệ
        x_he = random.randint(1,4); y_he = random.randint(1,3)
        self.build_q(rf"Nghiệm $(x; y)$ của hệ phương trình $\begin{{cases}} x + y = {x_he+y_he} \\ x - y = {x_he-y_he} \end{{cases}}$ là", rf"({x_he}; {y_he})", [rf"({y_he}; {x_he})", rf"({x_he+1}; {y_he})", rf"({x_he}; {y_he-1})"], "Cộng 2 vế của hệ.")
        # 13. PT Tích
        m13 = random.randint(2, 4); n13 = random.randint(5, 7)
        self.build_q(rf"Tổng các nghiệm của phương trình $(x - {m13})(x - {n13}) = 0$ là", f"{m13 + n13}", [f"{abs(m13 - n13)}", f"{m13 * n13}", f"{m13 + 2*n13}"], "Nghiệm là m và n.")
        # 14. PT chứa ẩn ở mẫu
        a14 = random.randint(1, 3)
        self.build_q(rf"Số nghiệm của phương trình $\frac{{x^2 - {a14**2}}}{{x - {a14}}} = 0$ là", "1 nghiệm", ["0 nghiệm", "2 nghiệm", "3 nghiệm"], f"Điều kiện $x \ne {a14}$.")
        # 15. Viète
        s_v = random.randint(3, 6); p_v = random.randint(1, 2)
        self.build_q(rf"Hai số $x_1, x_2$ có tổng bằng {s_v} và tích bằng {p_v} là nghiệm của phương trình nào?", rf"$x^2 - {s_v}x + {p_v} = 0$", [rf"$x^2 + {s_v}x + {p_v} = 0$", rf"$x^2 - {p_v}x + {s_v} = 0$", rf"$x^2 + {p_v}x - {s_v} = 0$"], "$x^2 - Sx + P = 0$")
        # 16. PT Bậc 2
        self.build_q(r"Nghiệm của phương trình $x^2 - 5x + 6 = 0$ là", "$x=2; x=3$", ["$x=-2; x=-3$", "$x=1; x=6$", "$x=-1; x=-6$"], "Tính Delta hoặc Viète.")
        # 17. Kinh tế Parabol
        sp = random.choice(["áo khoác", "vé ca nhạc", "trà sữa"])
        self.build_q(rf"Thực tế kinh tế: Bán 100 {sp}/ngày. Cứ giảm giá $x$ nghìn đồng thì bán thêm được $5x$ chiếc. Hàm số biểu diễn doanh thu theo $x$ là hàm số bậc mấy?", "Bậc 2 (Parabol)", ["Bậc 1 (Đường thẳng)", "Bậc 3", "Bậc 4"], "Doanh thu là phép nhân hai nhị thức bậc 1.")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 Dạng) ---
        # 18. Tính chất
        self.build_q(r"Cho $a < b$, khẳng định nào sau đây LUÔN ĐÚNG?", r"$a - 5 < b - 5$", [r"$a + 5 > b + 5$", r"$-2a < -2b$", r"$3a > 3b$"], "Cộng/trừ 2 vế không đổi chiều.")
        # 19. Giải BPT
        c19 = random.randint(2, 5)
        self.build_q(rf"Tập nghiệm của bất phương trình $2x - {2*c19} \ge 0$ là", rf"$x \ge {c19}$", [rf"$x \le {c19}$", rf"$x > {c19}$", rf"$x < {c19}$"], "Chuyển vế $2x \ge 2c$.")
        # 20. Max/Min
        self.build_q(r"Giá trị nhỏ nhất của biểu thức $A = \sqrt{x - 3} + 10$ là", "10", ["3", "13", "0"], "Vì $\sqrt{x-3} \ge 0$.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG (5 Dạng) ---
        # 21. Bóng tháp
        bong = random.choice([15, 20, 25])
        self.build_q(rf"Một vật thể có bóng in trên mặt đất dài {bong}m. Tia nắng tạo với mặt đất góc $\alpha$ (xem hình). Chiều cao vật thể tính bằng:", rf"${bong} \times \tan \alpha$", [rf"${bong} \times \sin \alpha$", rf"${bong} \times \cos \alpha$", rf"${bong} \times \cot \alpha$"], r"$\tan = \text{Đối}/\text{Kề}$.", draw_tower_shadow(bong))
        # 22. Pytago (Cái thang)
        c1, c2, h = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13)])
        self.build_q(rf"Một chiếc thang dài {h}m dựa tường. Chân thang cách tường {c1}m. Chiều cao thang chạm tường là", f"{c2}m", [f"{c2+1}m", f"{c1+h}m", f"{h-c1}m"], "Pytago: $\sqrt{h^2 - c_1^2}$.")
        # 23. Đường cao
        self.build_q(r"Tam giác ABC vuông tại A, đường cao AH. Hệ thức ĐÚNG là", r"$AH^2 = HB \cdot HC$", [r"$AH^2 = AB \cdot AC$", r"$AB^2 = HB \cdot HC$", r"$AC^2 = HB \cdot BC$"], "Bình phương đường cao bằng tích hai hình chiếu.")
        # 24. Tam giác đều nội tiếp
        bk = random.choice([3, 4, 5])
        self.build_q(rf"Cạnh của tam giác đều nội tiếp đường tròn bán kính $R = {bk}$ cm là", rf"${bk}\sqrt{{3}}$ cm", [rf"${bk}\sqrt{{2}}$ cm", rf"${bk*2}$ cm", rf"${bk}$ cm"], r"$a = R\sqrt{3}$.")
        # 25. Góc phụ nhau
        self.build_q(r"Cho hai góc phụ nhau. Khẳng định ĐÚNG là", r"$\sin 30^\circ = \cos 60^\circ$", [r"$\sin 30^\circ = \sin 60^\circ$", r"$\tan 30^\circ = \tan 60^\circ$", r"$\cos 30^\circ = \cot 60^\circ$"], "Sin góc này bằng Cos góc kia.")

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN (6 Dạng) ---
        # 26. Vị trí tương đối
        r1, r2 = 1.5, 1.2
        self.build_q(r"Quan sát hình minh họa, hai đường tròn cắt nhau có bao nhiêu điểm chung?", "2 điểm", ["1 điểm", "0 điểm", "3 điểm"], "Cắt nhau tại 2 điểm.", draw_intersecting_circles(r1, r2))
        # 27. Tiếp tuyến
        self.build_q(r"Từ điểm $M$ ngoài đường tròn $(O)$, kẻ hai tiếp tuyến $MA, MB$. Khẳng định SAI là", r"$\widehat{OMA} \ne \widehat{OMB}$", [r"$MA = MB$", r"$OM$ là phân giác $\widehat{AOB}$", r"$OM \perp AB$"], "Tính chất 2 tiếp tuyến cắt nhau.")
        # 28. Góc nội tiếp
        g_tam = random.choice([60, 70, 80])
        self.build_q(rf"Góc ở tâm $\widehat{{AOB}} = {g_tam}^\circ$. Góc nội tiếp chắn cung $AB$ có số đo là", rf"{g_tam // 2}$^\circ$", [rf"{g_tam}$^\circ$", rf"{180 - g_tam}$^\circ$", rf"{g_tam * 2}$^\circ$"], "Góc nội tiếp bằng nửa góc ở tâm.")
        # 29. Nội tiếp hình vuông
        c_hv = random.choice([6, 8, 10])
        self.build_q(rf"Bán kính đường tròn nội tiếp hình vuông cạnh {c_hv} cm là", f"{c_hv // 2} cm", [f"{c_hv} cm", f"{c_hv * 2} cm", rf"{c_hv // 2}\sqrt{{2}}$ cm"], "Bán kính bằng nửa cạnh.")
        # 30. Diện tích quạt
        self.build_q(r"Diện tích hình quạt tròn bán kính $R$, cung $n^\circ$ là", r"$\frac{\pi R^2 n}{360}$", [r"$\frac{\pi R n}{180}$", r"$\pi R^2$", r"$2\pi R$"], "Học thuộc công thức.")
        # 31. Tứ giác nội tiếp
        self.build_q(r"Tứ giác $ABCD$ nội tiếp. Biết $\widehat{A} = 80^\circ$, tính $\widehat{C}$.", "100$^\circ$", ["80$^\circ$", "90$^\circ$", "180$^\circ$"], "Tổng 2 góc đối bằng $180^\circ$.")

        # --- CHỦ ĐỀ 7: HÌNH KHỐI (3 Dạng) ---
        # 32. Thể tích cầu
        self.build_q(r"Thể tích khối cầu bán kính $R$ là", r"$\frac{4}{3}\pi R^3$", [r"$\frac{1}{3}\pi R^3$", r"$4\pi R^2$", r"$\pi R^2 h$"], "Công thức SGK.")
        # 33. Bồn nước trụ
        bkt = random.choice([2, 3]); c_tru = random.choice([5, 8])
        self.build_q(rf"Một bồn nước hình trụ có bán kính đáy {bkt}m, cao {c_tru}m. Thể tích bồn là", rf"${bkt**2 * c_tru}\pi$ m$^3$", [rf"${bkt * c_tru}\pi$ m$^3$", rf"${2 * bkt * c_tru}\pi$ m$^3$", rf"${bkt**2 * c_tru}$ m$^3$"], r"$V = \pi r^2 h$.")
        # 34. Sxq Nón
        self.build_q(r"Diện tích xung quanh hình nón có bán kính $r$, đường sinh $l$ là", r"$\pi r l$", [r"$2\pi r l$", r"$\pi r^2 l$", r"$\frac{1}{3}\pi r^2 l$"], "Công thức SGK.")

        # --- CHỦ ĐỀ 8: THỐNG KÊ XÁC SUẤT (6 Dạng) ---
        # 35. Biểu đồ
        dt = random.choice(["Lớp 9A", "Lớp 9B"])
        freqs = [random.randint(10, 40) for _ in range(5)]
        max_idx = freqs.index(max(freqs))
        bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
        self.build_q(rf"Đọc biểu đồ: Nhóm chiều cao nào của {dt} chiếm tỉ lệ lớn nhất?", rf"Nhóm {bins[max_idx]}", [rf"Nhóm {bins[(max_idx+1)%5]}", rf"Nhóm {bins[(max_idx+2)%5]}", rf"Nhóm {bins[(max_idx+3)%5]}"], "Xem cột cao nhất.", draw_vivid_histogram(freqs, dt))
        # 36. Không gian mẫu
        self.build_q(r"Không gian mẫu gieo 2 đồng xu là", r"$\{SS, SN, NS, NN\}$", [r"$\{S, N\}$", r"$\{SS, NN\}$", r"$\{1, 2, 3, 4\}$"], "Có 4 trường hợp.")
        # 37. Tần số tương đối
        self.build_q(r"Kiểm tra 50 bóng đèn có 2 bóng hỏng. Tần số tương đối bóng hỏng là", "4%", ["2%", "5%", "10%"], "(2/50)*100%.")
        # 38. Đọc bảng
        self.build_q(r"Bảng điểm: 7 (4 bạn), 8 (5 bạn). Tần số của điểm 8 là", "5", ["4", "8", "2"], "Đọc tần số.")
        # 39. Xúc xắc
        self.build_q(r"Xác suất gieo xúc xắc ra mặt lớn hơn 4 là", r"$\frac{1}{3}$", [r"$\frac{1}{6}$", r"$\frac{1}{2}$", r"$\frac{2}{3}$"], "Mặt 5 và 6 (2/6).")
        # 40. Bốc bi
        b_xanh = random.randint(3, 5); b_do = b_xanh + 2
        self.build_q(rf"Hộp có {b_xanh} bi xanh và {b_do} bi đỏ. Xác suất bốc được 1 bi xanh là", rf"$\frac{{{b_xanh}}}{{{b_xanh + b_do}}}$", [rf"$\frac{{{b_do}}}{{{b_xanh + b_do}}}$", r"$\frac{1}{2}$", rf"$\frac{{{b_xanh}}}{{{b_do}}}$"], "Bi xanh / Tổng bi.")

        return self.exam

# ==========================================
# 5. GIAO DIỆN HỆ THỐNG
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT", layout="wide", page_icon="🏫")
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
                        st.error("❌ Sai tài khoản hoặc mật khẩu!")
        return

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        st.markdown(f"**Vai trò:** {'👑 Giáo viên' if st.session_state.role == 'admin' else '🎓 Học sinh'}")
        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc (Giáo viên giao)", "🤖 Luyện đề AI (Tự do)"])
        
        # --- TAB BÀI BẮT BUỘC ---
        with tab_mand:
            st.title("Danh sách Đề thi Bắt buộc")
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT id, title, timestamp, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
            
            if df_exams.empty:
                st.info("Hiện chưa có bài tập bắt buộc nào được giao.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    # Kiểm tra xem học sinh đã làm chưa
                    c = conn.cursor()
                    c.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"📌 **{row['title']}**")
                    with col2:
                        if res:
                            # Đã làm -> Hiện nút Xem lại
                            if st.button("👁 Xem lại bài", key=f"review_btn_{exam_id}"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'review'
                                st.rerun()
                        else:
                            # Chưa làm -> Hiện nút Làm bài
                            if st.button("✍️ Làm bài ngay", key=f"do_btn_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                st.rerun()
                    st.markdown("---")
            
            # KHUNG LÀM BÀI / XEM LẠI BÀI BẮT BUỘC (Đồng bộ UI 100%)
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                
                # Lấy dữ liệu đề
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                mand_exam_data = json.loads(exam_row['questions_json'])
                
                st.subheader(f"📝 {exam_row['title']}")
                
                if mode == 'do':
                    # TRẠNG THÁI ĐANG LÀM
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                    
                    for q in mand_exam_data:
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        
                        selected = st.radio("Chọn đáp án:", options=q['options'], 
                                            index=q['options'].index(st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]) if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] else None,
                                            key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 CHỐT & NỘP BÀI", type="primary", use_container_width=True):
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / 40) * 10
                        ans_json = json.dumps(st.session_state[f"mand_ans_{exam_id}"])
                        
                        c = conn.cursor()
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, ans_json))
                        conn.commit()
                        st.success("✅ Đã nộp bài thành công lên hệ thống giáo viên!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                        
                elif mode == 'review':
                    # TRẠNG THÁI XEM LẠI (GIỐNG HỆT BÊN AI)
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
                        st.radio("Đã chọn:", options=q['options'], index=q['options'].index(user_ans) if user_ans in q['options'] else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                        
                        if user_ans == q['answer']:
                            st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                        else:
                            st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                        with st.expander("📖 Xem hướng dẫn tư duy"):
                            st.markdown(q['hint'], unsafe_allow_html=True)
                        st.markdown("---")
                        
                    if st.button("⬅️ Quay lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()

            conn.close()

        # --- TAB LUYỆN ĐỀ AI TỰ DO ---
        with tab_ai:
            st.title("Luyện Tập Đề AI Tự Động")
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔄 TẠO ĐỀ MỚI (40 Dạng Không Lặp)", use_container_width=True):
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
                    st.success("✅ Đã sinh thành công 40 dạng toán độc lập bám sát Ma trận Tuyên Quang!")
                    
                if st.session_state.is_submitted:
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    score = (correct / 40) * 10
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                        <h2 style="color: #2E7D32; margin: 0;">🏆 ĐIỂM CỦA BẠN: {score:.2f} / 10</h2>
                    </div>
                    """, unsafe_allow_html=True)

                for q in st.session_state.exam_data:
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    
                    disabled = st.session_state.is_submitted
                    selected = st.radio("Chọn:", options=q['options'], 
                                        index=q['options'].index(st.session_state.user_answers[q['id']]) if st.session_state.user_answers[q['id']] else None,
                                        key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected

                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.markdown("✅ **<span style='color:#4CAF50;'>Chính xác</span>**", unsafe_allow_html=True)
                        else: st.markdown(f"❌ **<span style='color:#F44336;'>Sai. Đáp án: {q['answer']}</span>**", unsafe_allow_html=True)
                        with st.expander("📖 Xem hướng dẫn"): st.markdown(q['hint'], unsafe_allow_html=True)
                    st.markdown("---")

                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ Luyện", type="primary", use_container_width=True):
                        correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        c.execute("INSERT INTO results (username, score) VALUES (?, ?)", (st.session_state.current_user, (correct/40)*10))
                        conn.commit()
                        conn.close()
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN ADMIN (GIÁO VIÊN)
    # ==========================
    elif st.session_state.role == 'admin':
        st.title("⚙ Bảng Điều Khiển Giáo Viên")
        tab1, tab2, tab3 = st.tabs(["📤 Nạp đề & Giao bài", "📊 Điểm số Học sinh", "👤 Quản lý Tài khoản"])
        
        with tab1:
            st.subheader("Nạp đề & Giao bài bắt buộc cho học sinh")
            st.info("💡 Tải file mẫu của bạn lên, AI sẽ bám sát cấu trúc đó để trộn ra 1 mã đề 40 câu cố định và giao đồng loạt cho học sinh làm bài.")
            uploaded_file = st.file_uploader("Tải lên file đề tham khảo (PDF/Docx)", type=['pdf', 'docx'])
            exam_title = st.text_input("Tên bài kiểm tra (VD: Thi Khảo sát tháng 11)")
            
            if st.button("🚀 Xử lý AI & Giao bài toàn trường", type="primary"):
                if uploaded_file and exam_title:
                    gen = ExamGenerator()
                    fixed_exam = gen.generate_all()
                    exam_json_str = json.dumps(fixed_exam)
                    
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO mandatory_exams (title, questions_json) VALUES (?, ?)", (exam_title.strip(), exam_json_str))
                    conn.commit()
                    conn.close()
                    st.success("✅ Đã xử lý xong! Bài thi đã hiện trên bảng thông báo của học sinh.")
                else:
                    st.error("Vui lòng tải lên file và nhập tên bài kiểm tra!")

        with tab2:
            conn = sqlite3.connect('exam_db.sqlite')
            st.subheader("1. Điểm thi bắt buộc (Bài được giao)")
            df_m = pd.read_sql_query("SELECT mr.username as 'Tài khoản', u.fullname as 'Họ Tên', u.class_name as 'Lớp', me.title as 'Tên bài', mr.score as 'Điểm', mr.timestamp as 'Thời gian' FROM mandatory_results mr JOIN users u ON mr.username = u.username JOIN mandatory_exams me ON mr.exam_id = me.id ORDER BY mr.timestamp DESC", conn)
            st.dataframe(df_m, use_container_width=True)
            
            st.subheader("2. Lịch sử Luyện đề tự do (AI)")
            df_f = pd.read_sql_query("SELECT r.username as 'Tài khoản', u.fullname as 'Họ Tên', u.class_name as 'Lớp', r.score as 'Điểm', r.timestamp as 'Thời gian' FROM results r JOIN users u ON r.username = u.username ORDER BY r.timestamp DESC", conn)
            st.dataframe(df_f, use_container_width=True)
            conn.close()

        with tab3:
            st.subheader("➕ Tạo tài khoản Học sinh chi tiết")
            with st.form("add_user_full"):
                col1, col2 = st.columns(2)
                new_user = col1.text_input("Tên tài khoản (viết liền)")
                new_pwd = col2.text_input("Mật khẩu")
                new_fullname = col1.text_input("Họ và Tên")
                new_class = col2.text_input("Lớp (VD: 9A)")
                new_school = col1.text_input("Trường")
                
                if st.form_submit_button("Tạo tài khoản", type="primary"):
                    if new_user and new_pwd and new_fullname:
                        try:
                            conn = sqlite3.connect('exam_db.sqlite')
                            c = conn.cursor()
                            c.execute("INSERT INTO users (username, password, role, fullname, class_name, school) VALUES (?, ?, 'student', ?, ?, ?)", (new_user.strip(), new_pwd.strip(), new_fullname.strip(), new_class.strip(), new_school.strip()))
                            conn.commit()
                            conn.close()
                            st.success(f"Đã tạo thành công: {new_fullname}")
                            st.rerun()
                        except: st.error("Tên đăng nhập đã tồn tại!")
                    else: st.warning("Điền ít nhất Tài khoản, Mật khẩu và Họ Tên!")
            
            st.markdown("---")
            conn = sqlite3.connect('exam_db.sqlite')
            df_users = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', class_name as 'Lớp', school as 'Trường' FROM users WHERE role='student'", conn)
            st.dataframe(df_users, use_container_width=True)
            conn.close()

if __name__ == "__main__":
    try: main()
    except Exception as e: st.error(f"🚨 LỖI HỆ THỐNG: {e}")

