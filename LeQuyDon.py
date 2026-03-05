import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO

# --- FIX 1: LỆNH CHỐNG SẬP MÁY CHỦ KHI VẼ ĐỒ HỌA ---
import matplotlib
matplotlib.use('Agg') 
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
    
    # BẢO MẬT: TÀI KHOẢN ADMIN GỐC (Chỉ người tạo App biết)
    c.execute("INSERT OR IGNORE INTO users VALUES ('maducnghi6789@gmail.com', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student')")
    conn.commit()
    conn.close()

# ==========================================
# 2. HỆ THỐNG VẼ HÌNH ĐỒ HỌA SINH ĐỘNG (TOÁN THỰC TẾ)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    # Tăng dpi=200 để nét căng trên mọi màn hình, nền xám nhạt sang trọng
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#f8f9fa', dpi=200)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    """Vẽ minh họa cổng vòm hình Parabol (Bài toán thực tế)"""
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(-4, 4, 100)
    y = -0.3 * x**2 + 5
    
    # Vẽ cổng vòm (Parabol)
    ax.plot(x, y, color='#c0392b', lw=3.5, label="Cổng vòm")
    ax.fill_between(x, y, 0, color='#e74c3c', alpha=0.15)
    
    # Vẽ mặt đường / mặt nước
    ax.axhline(0, color='#2980b9', lw=4, label="Mặt đường")
    
    # Hệ trục tọa độ mờ (Gợi ý toán học)
    ax.axvline(0, color='black', lw=1, linestyle='--')
    ax.text(0.2, 5.2, 'y', fontsize=10, style='italic')
    ax.text(4.2, 0.2, 'x', fontsize=10, style='italic')
    ax.text(0.2, -0.6, 'O', fontsize=10, fontweight='bold')
    
    ax.set_xticks([]); ax.set_yticks([]) # Giấu số liệu
    ax.axis('off')
    return fig_to_base64(fig)

def draw_tower_shadow():
    """Vẽ minh họa bài toán bóng tháp / thang dựa tường"""
    fig, ax = plt.subplots(figsize=(4, 3))
    
    # Mặt đất
    ax.plot([-1, 5], [0, 0], color='#27ae60', lw=4) 
    
    # Tháp / Tường (Đứng)
    ax.plot([0, 0], [0, 4], color='#7f8c8d', lw=6)
    
    # Tia nắng / Thang (Cạnh huyền)
    ax.plot([3, 0], [0, 4], color='#f39c12', lw=2, linestyle='--')
    
    # Ký hiệu góc vuông và góc tạo với mặt đất
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
    """Biểu đồ thống kê sinh động"""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    
    # Tạo màu gradient giả lập cho các cột
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
                     "Bậc 2", ["Bậc 1", "Bậc 3", "Bậc 4"], "Doanh thu = (Giá gốc - x) * (Số lượng + k*x) tạo ra hàm bậc 2 (Parabol).")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂU) ---
        for _ in range(3):
            c = random.randint(2, 5)
            self.build_q(rf"Nghiệm của bất phương trình $2x - {2*c} \ge 0$ là", rf"$x \ge {c}$", [rf"$x \le {c}$", rf"$x > {c}$", rf"$x < {c}$"], "Chuyển vế và chia cho số dương.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG THỰC TẾ (5 CÂU) ---
        self.build_q(r"Một bóng tháp in trên mặt đất dài 15m. Tia nắng mặt trời tạo với mặt đất một góc $\alpha$ (như hình minh họa). Công thức tính chiều cao tháp là:", 
                     r"$15 \times \tan \alpha$", [r"$15 \times \sin \alpha$", r"$15 \times \cos \alpha$", r"$15 \times \cot \alpha$"], 
                     r"Sử dụng Tỉ số lượng giác: $\tan = \text{Đối} / \text{Kề}$. Chiều cao = Bóng $\times \tan \alpha$.", draw_tower_shadow())
        for _ in range(4):
            # FIX 2: BỘ BA PYTAGO CHUẨN XÁC, KHÔNG BAO GIỜ SAI SỐ!
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
# 4. GIAO DIỆN HỆ THỐNG (UI/UX CHUYÊN NGHIỆP)
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Thi Thử THPT Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
