# ==========================================
# QUAN TRỌNG: 2 DÒNG NÀY PHẢI NẰM TRÊN CÙNG ĐỂ CHỐNG SẬP MÁY CHỦ
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
# 2. HỆ THỐNG VẼ HÌNH ĐỒ HỌA SINH ĐỘNG (BIẾN ĐỔI THEO ĐỀ BÀI)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#f8f9fa', dpi=200)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola(ten_cong_trinh):
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(-4, 4, 100)
    y = -0.3 * x**2 + 5
    ax.plot(x, y, color='#c0392b', lw=3.5, label=ten_cong_trinh)
    ax.fill_between(x, y, 0, color='#e74c3c', alpha=0.15)
    ax.axhline(0, color='#2980b9', lw=4, label="Mặt phẳng")
    ax.axvline(0, color='black', lw=1, linestyle='--')
    ax.text(0.2, 5.2, 'y', fontsize=10, style='italic')
    ax.text(4.2, 0.2, 'x', fontsize=10, style='italic')
    ax.text(0.2, -0.6, 'O', fontsize=10, fontweight='bold')
    ax.set_title(ten_cong_trinh.upper(), fontsize=10, fontweight='bold', color='#2c3e50')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.axis('off')
    return fig_to_base64(fig)

def draw_tower_shadow(chieu_dai_bong):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([-1, 5], [0, 0], color='#27ae60', lw=4) 
    ax.plot([0, 0], [0, 4], color='#7f8c8d', lw=6)
    ax.plot([3, 0], [0, 4], color='#f39c12', lw=2, linestyle='--')
    ax.plot([0, 0.3, 0.3, 0], [0.3, 0.3, 0, 0], color='red', lw=1.5)
    arc = patches.Arc((3, 0), 1, 1, angle=0, theta1=120, theta2=180, color='blue', lw=2)
    ax.add_patch(arc)
    ax.text(-0.8, 2, 'Vật thể', rotation=90, fontweight='bold', color='#34495e')
    # AI tự động chèn chiều dài bóng vào hình ảnh
    ax.text(1.2, -0.6, f'Bóng dài {chieu_dai_bong}m', fontsize=10, fontweight='bold', color='#d35400')
    ax.text(2.2, 0.2, r'$\alpha$', fontsize=12, color='blue')
    ax.set_xlim(-1, 4); ax.set_ylim(-1, 4.5)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_vivid_histogram(freqs, doi_tuong):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#e67e22']
    bars = ax.bar(bins, percents, color=colors, edgecolor='#2c3e50', linewidth=1)
    ax.set_title(f"KHẢO SÁT CHIỀU CAO CỦA {doi_tuong.upper()}", fontweight='bold', color='#c0392b', pad=15)
    ax.set_ylabel('Tỉ lệ (%)', fontweight='bold')
    ax.grid(axis='y', linestyle=':', alpha=0.7)
    for bar, v in zip(bars, percents): 
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{round(v)}%", ha='center', fontweight='bold')
    ax.set_ylim(0, max(percents) + 15)
    return fig_to_base64(fig)

def draw_intersecting_circles(r1, r2):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    c1 = plt.Circle((-0.8, 0), r1, color='#2980b9', fill=False, lw=1.5)
    c2 = plt.Circle((0.8, 0), r2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    ax.plot(0, 1.15, 'ko'); ax.plot(0, -1.15, 'ko') 
    ax.set_xlim(-3, 3); ax.set_ylim(-2, 2)
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 3. AI TẠO ĐỀ: CHÍNH XÁC 40 CÂU KHÔNG LẶP
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
        names = random.sample(["An", "Bình", "Châu", "Dương", "Hải", "Linh", "Minh", "Nam"], 5)
        
        # --- CHỦ ĐỀ 1: CĂN THỨC (6 CÂU) ---
        # Câu 1
        a1 = random.randint(2, 9)
        self.build_q(rf"Điều kiện để $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], "Biểu thức dưới dấu căn phải không âm.")
        # Câu 2
        a2 = random.randint(2, 7)
        self.build_q(rf"Tập hợp các giá trị của $x$ để căn thức $\sqrt{{{a2} - 2x}}$ xác định là", r"$x \le " + str(a2/2) + r"$", [r"$x \ge " + str(a2/2) + r"$", r"$x < " + str(a2/2) + r"$", r"$x > " + str(a2/2) + r"$"], "Giải bất phương trình $-2x \ge -a$.")
        # Câu 3
        sq = random.choice([16, 25, 36, 49, 64, 81])
        rt = int(math.sqrt(sq))
        self.build_q(f"Căn bậc hai số học của {sq} là", f"{rt}", [f"-{rt}", f"{rt} và -{rt}", f"{sq**2}"], "Căn bậc hai số học chỉ lấy giá trị dương.")
        # Câu 4
        a4 = random.randint(2, 5); b4 = random.randint(6, 10)
        self.build_q(rf"Với $x < {a4}$, kết quả rút gọn của biểu thức $\sqrt{{({a4} - x)^2}} + x - {b4}$ là", f"{a4 - b4}", [f"{b4 - a4}", rf"$2x - {a4 + b4}$", f"{a4 + b4}"], r"Do $x < a$ nên $|a - x| = a - x$.")
        # Câu 5
        c5 = random.choice([2, 3, 5])
        self.build_q(rf"Trục căn thức ở mẫu của biểu thức $\frac{{{c5}}}{{\sqrt{{{c5}}}}}$ ta được kết quả là", rf"$\sqrt{{{c5}}}$", [f"{c5}", f"1", rf"${c5}\sqrt{{{c5}}}$"], "Nhân cả tử và mẫu với căn thức ở mẫu.")
        # Câu 6
        self.build_q(r"Với $a > 0, b > 0$, biểu thức $\sqrt{16a^2b}$ được rút gọn thành", r"$4a\sqrt{b}$", [r"$-4a\sqrt{b}$", r"$16a\sqrt{b}$", r"$4a^2\sqrt{b}$"], "Đưa thừa số ra ngoài dấu căn.")

        # --- CHỦ ĐỀ 2: HÀM SỐ & ĐỒ THỊ (3 CÂU) ---
        # Câu 7
        kientruc = random.choice(["Cổng vòm Parabol", "Cầu vượt Parabol", "Mái vòm nhà thi đấu"])
        img_para = draw_real_parabola(kientruc)
        self.build_q(rf"Một {kientruc.lower()} có hình dáng là một parabol với phương trình $y = -ax^2$ (như hình minh họa). Cổng nhận đường thẳng nào làm trục đối xứng?", 
                     "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường thẳng y = x", "Không có trục đối xứng"], 
                     "Parabol luôn nhận trục tung làm trục đối xứng.", img_para)
        # Câu 8
        x0 = random.choice([-2, -3, 2, 3]); y0 = random.choice([4, 9, 12, 18])
        a_val = y0 // (x0**2) if y0 % (x0**2) == 0 else f"{y0}/{x0**2}"
        self.build_q(rf"Biết quỹ đạo chuyển động là một Parabol đi qua điểm $M({x0}; {y0})$ có phương trình $y = ax^2$. Giá trị của hệ số $a$ là", f"{a_val}", [f"{y0 * abs(x0)}", f"{abs(x0)**2}/{y0}", f"{y0}"], "Thay tọa độ x, y vào phương trình để tìm a.")
        # Câu 9
        self.build_q(r"Cho hàm số $y = -3x^2$. Kết luận nào sau đây là ĐÚNG?", "Hàm số đồng biến khi $x < 0$ và nghịch biến khi $x > 0$.", ["Hàm số luôn đồng biến.", "Hàm số luôn nghịch biến.", "Hàm số đồng biến khi $x > 0$ và
