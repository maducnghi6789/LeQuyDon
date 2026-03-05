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
    
    ax.text(-0.8, 2, 'Vật thể', rotation=90, fontweight='bold', color='#34495e')
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

def draw_intersecting_circles():
    fig, ax = plt.subplots(figsize=(4, 2.5))
    c1 = plt.Circle((-0.8, 0), 1.5, color='blue', fill=False, lw=1.5)
    c2 = plt.Circle((0.8, 0), 1.2, color='green', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    ax.plot(0, 1.15, 'ko'); ax.plot(0, -1.15, 'ko') 
    ax.set_xlim(-2.5, 2.5); ax.set_ylim(-1.6, 1.6)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 3. AI TẠO ĐỀ: 40 CÂU HỎI ĐA DẠNG NGỮ CẢNH
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
        # Bộ tên và bối cảnh ngẫu nhiên để chống lặp
        names = random.sample(["An", "Bình", "Châu", "Dương", "Hải", "Linh", "Minh", "Nam"], 5)
        
        # --- CHỦ ĐỀ 1: CĂN THỨC (6 CÂU HOÀN TOÀN KHÁC NHAU) ---
        a1 = random.randint(2, 9)
        self.build_q(rf"Điều kiện để $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], "Biểu thức dưới dấu căn phải không âm.")
        
        a2 = random.randint(2, 7)
        self.build_q(rf"Tập hợp các giá trị của $x$ để căn thức $\sqrt{{{a2} - 2x}}$ xác định là", r"$x \le " + str(a2/2) + r"$", [r"$x \ge " + str(a2/2) + r"$", r"$x < " + str(a2/2) + r"$", r"$x > " + str(a2/2) + r"$"], "Giải bất phương trình.")
        
        sq = random.choice([16, 25, 36, 49, 64, 81])
        rt = int(math.sqrt(sq))
        self.build_q(f"Căn bậc hai số học của {sq} là", f"{rt}", [f"-{rt}", f"{rt} và -{rt}", f"{sq**2}"], "Căn bậc hai số học chỉ lấy giá trị dương.")
        
        a4 = random.randint(2, 5); b4 = random.randint(6, 10)
        self.build_q(rf"Với $x < {a4}$, kết quả rút gọn của biểu thức $\sqrt{{({a4} - x)^2}} + x - {b4}$ là", f"{a4 - b4}", [f"{b4 - a4}", rf"$2x - {a4 + b4}$", f"{a4 + b4}"], r"Do $x < a$ nên $|a - x| = a - x$.")
        
        c5 = random.choice([2, 3, 5])
        self.build_q(rf"Trục căn thức ở mẫu của biểu thức $\frac{{{c5}}}{{\sqrt{{{c5}}}}}$ ta được kết quả là", rf"$\sqrt{{{c5}}}$", [f"{c5}", f"1", rf"${c5}\sqrt{{{c5}}}$"], "Nhân cả tử và mẫu với căn thức ở mẫu.")
        
        self.build_q(r"Với $a > 0, b > 0$, biểu thức $\sqrt{16a^2b}$ được rút gọn thành", r"$4a\sqrt{b}$", [r"$-4a\sqrt{b}$", r"$16a\sqrt{b}$", r"$4a^2\sqrt{b}$"], "Đưa thừa số ra ngoài dấu căn.")

        # --- CHỦ ĐỀ 2: HÀM SỐ & ĐỒ THỊ (3 CÂU) ---
        self.build_q(r"Quan sát hình minh họa, một chiếc cổng hình parabol có phương trình $y = -ax^2$. Cổng này nhận đường thẳng nào làm trục đối xứng?", 
                     "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường thẳng y = x", "Không có trục đối xứng"], 
                     "Parabol luôn nhận trục tung làm trục đối xứng.", draw_real_parabola())
        
        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        self.build_q(rf"Biết đồ thị hàm số $y = ax^2$ đi qua điểm $M({x0}; {y0})$. Giá trị của hệ số $a$ là", f"{a_val}", [f"{y0 * abs(x0)}", f"{abs(x0)**2}/{y0}", f"{y0}"], "Thay tọa độ x, y vào phương trình để tìm a.")
        
        self.build_q(r"Cho hàm số $y = -3x^2$. Kết luận nào sau đây là ĐÚNG?", "Hàm số đồng biến khi $x < 0$ và nghịch biến khi $x > 0$.", ["Hàm số luôn đồng biến.", "Hàm số luôn nghịch biến.", "Hàm số đồng biến khi $x > 0$ và nghịch biến khi $x < 0$."], "Dựa vào dấu của hệ số a.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & HỆ (8 CÂU ĐA DẠNG) ---
        self.build_q(r"Hệ phương trình nào sau đây KHÔNG phải là hệ hai phương trình bậc nhất hai ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", 
                     [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} 3x - y = 1 \\ x + y = 2 \end{cases}$"], "Hệ bậc nhất không chứa căn của ẩn.")
        
        self.build_q(r"Cặp số $(x; y)$ nào sau đây là nghiệm của phương trình $2x - y = 3$?", "(2; 1)", ["(1; 2)", "(-1; 1)", "(0; 3)"], "Thay tọa độ vào phương trình.")
        
        sum_v = random.randint(3, 7); prod_v = random.randint(2, 6)
        self.build_q(rf"Theo định lý Viète, nếu phương trình bậc hai có 2 nghiệm $x_1, x_2$ thỏa mãn $x_1 + x_2 = {sum_v}$ và $x_1x_2 = {prod_v}$, thì đó là phương trình nào?", rf"$x^2 - {sum_v}x + {prod_v} = 0$", [rf"$x^2 + {sum_v}x + {prod_v} = 0$", rf"$x^2 - {prod_v}x + {sum_v} = 0$", rf"$x^2 + {prod_v}x - {sum_v} = 0$"], "Phương trình có dạng $x^2 - Sx + P = 0$.")
        
        m = random.randint(2, 4); n = random.randint(5, 7)
        self.build_q(rf"Tổng các nghiệm của phương trình $(x - {m})(3x - {3*n}) = 0$ là", f"{m + n}", [f"{abs(m - n)}", f"{m * n}", f"{m + 3*n}"], "Giải từng nhân tử bằng 0 rồi cộng lại.")
        
        self.build_q(r"Số nghiệm của phương trình $\frac{x^2 - 4}{x - 2} = 0$ là", "1 nghiệm", ["0 nghiệm", "2 nghiệm", "3 nghiệm"], "Chú ý điều kiện xác định $x \ne 2$.")
        
        items = [("áo sơ mi", "cái", 200, 10, 50), ("trà sữa", "cốc", 30, 2, 20), ("vé xem phim", "vé", 80, 5, 30)]
        item, unit, price, drop, boost = random.choice(items)
        self.build_q(rf"Kinh doanh thực tế: Một cửa hàng bán {price*10} {item}/tháng với giá {price} nghìn/{unit}. Khảo sát cho thấy cứ giảm giá {drop} nghìn thì bán thêm được {boost} {item}. Hàm số biểu diễn doanh thu theo mức giảm giá là hàm số bậc mấy?", 
                     "Bậc 2 (Parabol)", ["Bậc 1 (Đường thẳng)", "Bậc 3", "Bậc 4"], "Doanh thu = (Giá - x) * (Số lượng + k*x) tạo ra hàm bậc 2.")
        
        self.build_q(rf"Giải bài toán bằng cách lập PT: {names[0]} đi xe đạp từ A đến B với vận tốc $x$ km/h. Lúc về, {names[0]} tăng vận tốc thêm 4 km/h. Biểu thức thời gian về ít hơn thời gian đi 15 phút (quãng đường 10km) là", 
                     r"$\frac{10}{x} - \frac{10}{x+4} = \frac{1}{4}$", [r"$\frac{10}{x+4} - \frac{10}{x} = \frac{1}{4}$", r"$\frac{10}{x} + \frac{10}{x+4} = 15$", r"$\frac{10}{x} - \frac{10}{x+4} = 15$"], "Thời gian = Quãng đường / Vận tốc. Đổi 15 phút = 1/4 giờ.")
        
        self.build_q(r"Cho phương trình $x^2 - 5x + m = 0$. Để phương trình có 2 nghiệm phân biệt thì $m$ phải thỏa mãn:", r"$m < \frac{25}{4}$", [r"$m > \frac{25}{4}$", r"$m \le \frac{25}{4}$", r"$m \ge \frac{25}{4}$"], "Tính $\Delta = 25 - 4m > 0$.")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂ
