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
        self.build_q(r"Cho hàm số $y = -3x^2$. Kết luận nào sau đây là ĐÚNG?", "Hàm số đồng biến khi $x < 0$ và nghịch biến khi $x > 0$.", ["Hàm số luôn đồng biến.", "Hàm số luôn nghịch biến.", "Hàm số đồng biến khi $x > 0$ và nghịch biến khi $x < 0$."], "Dựa vào dấu của hệ số a.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH & HỆ (8 CÂU) ---
        # Câu 10
        self.build_q(r"Hệ phương trình nào sau đây KHÔNG phải là hệ hai phương trình bậc nhất hai ẩn?", r"$\begin{cases} \sqrt{x} + y = 1 \\ x - y = 0 \end{cases}$", 
                     [r"$\begin{cases} x + 2y = 1 \\ x - y = 0 \end{cases}$", r"$\begin{cases} 2x = 1 \\ y = 0 \end{cases}$", r"$\begin{cases} 3x - y = 1 \\ x + y = 2 \end{cases}$"], "Hệ bậc nhất không chứa căn của ẩn.")
        # Câu 11
        self.build_q(r"Cặp số $(x; y)$ nào sau đây là nghiệm của phương trình $2x - y = 3$?", "(2; 1)", ["(1; 2)", "(-1; 1)", "(0; 3)"], "Thay tọa độ vào phương trình.")
        # Câu 12
        sum_v = random.randint(3, 7); prod_v = random.randint(2, 6)
        self.build_q(rf"Theo định lý Viète, nếu phương trình bậc hai có 2 nghiệm $x_1, x_2$ thỏa mãn $x_1 + x_2 = {sum_v}$ và $x_1x_2 = {prod_v}$, thì đó là phương trình nào?", rf"$x^2 - {sum_v}x + {prod_v} = 0$", [rf"$x^2 + {sum_v}x + {prod_v} = 0$", rf"$x^2 - {prod_v}x + {sum_v} = 0$", rf"$x^2 + {prod_v}x - {sum_v} = 0$"], "Phương trình có dạng $x^2 - Sx + P = 0$.")
        # Câu 13
        m = random.randint(2, 4); n = random.randint(5, 7)
        self.build_q(rf"Tổng các nghiệm của phương trình $(x - {m})(3x - {3*n}) = 0$ là", f"{m + n}", [f"{abs(m - n)}", f"{m * n}", f"{m + 3*n}"], "Giải từng nhân tử bằng 0 rồi cộng lại.")
        # Câu 14
        self.build_q(r"Số nghiệm của phương trình $\frac{x^2 - 4}{x - 2} = 0$ là", "1 nghiệm", ["0 nghiệm", "2 nghiệm", "3 nghiệm"], "Chú ý điều kiện xác định $x \ne 2$.")
        # Câu 15
        items = [("áo sơ mi", "cái", 200, 10, 50), ("trà sữa", "cốc", 30, 2, 20), ("vé xem phim", "vé", 80, 5, 30)]
        item, unit, price, drop, boost = random.choice(items)
        self.build_q(rf"Kinh doanh thực tế: Một cửa hàng bán {price*10} {item}/tháng với giá {price} nghìn/{unit}. Khảo sát cho thấy cứ giảm giá {drop} nghìn thì bán thêm được {boost} {item}. Hàm số biểu diễn doanh thu theo mức giảm giá là hàm số bậc mấy?", 
                     "Bậc 2 (Parabol)", ["Bậc 1 (Đường thẳng)", "Bậc 3", "Bậc 4"], "Doanh thu = (Giá - x) * (Số lượng + k*x) tạo ra hàm bậc 2.")
        # Câu 16
        self.build_q(rf"Giải bài toán bằng cách lập PT: {names[0]} đi xe đạp từ A đến B với vận tốc $x$ km/h. Lúc về, {names[0]} tăng vận tốc thêm 4 km/h. Biểu thức thời gian về ít hơn thời gian đi 15 phút (quãng đường 10km) là", 
                     r"$\frac{10}{x} - \frac{10}{x+4} = \frac{1}{4}$", [r"$\frac{10}{x+4} - \frac{10}{x} = \frac{1}{4}$", r"$\frac{10}{x} + \frac{10}{x+4} = 15$", r"$\frac{10}{x} - \frac{10}{x+4} = 15$"], "Thời gian = Quãng đường / Vận tốc. Đổi 15 phút = 1/4 giờ.")
        # Câu 17
        self.build_q(r"Cho phương trình $x^2 - 5x + m = 0$. Để phương trình có 2 nghiệm phân biệt thì $m$ phải thỏa mãn:", r"$m < \frac{25}{4}$", [r"$m > \frac{25}{4}$", r"$m \le \frac{25}{4}$", r"$m \ge \frac{25}{4}$"], "Tính $\Delta = 25 - 4m > 0$.")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂU) ---
        # Câu 18
        self.build_q(r"Với mọi số thực $a < b$, khẳng định nào sau đây luôn ĐÚNG?", r"$a - 7 < b - 7$", [r"$a + 7 > b + 7$", r"$-3a < -3b$", r"$3a > 3b$"], "Cộng/trừ 2 vế BĐT với cùng một số thì chiều không đổi.")
        # Câu 19
        c_bpt = random.randint(3, 6)
        self.build_q(rf"Tập nghiệm của bất phương trình $3x - {3*c_bpt} > 0$ là", rf"$x > {c_bpt}$", [rf"$x \ge {c_bpt}$", rf"$x < {c_bpt}$", rf"$x \le {c_bpt}$"], "Chuyển vế và chia cho số dương.")
        # Câu 20
        self.build_q(r"Giá trị nhỏ nhất của biểu thức $P = \sqrt{x - 2} + 5$ (với $x \ge 2$) là", "5", ["2", "7", "0"], "Vì căn bậc hai luôn không âm nên min P = 5 khi x = 2.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG THỰC TẾ (5 CÂU) ---
        # Câu 21
        bong = random.choice([15, 20, 25, 30])
        img_thap = draw_tower_shadow(bong)
        self.build_q(rf"Thực tế lượng giác: Một bóng tháp in trên mặt đất dài {bong}m. Tia nắng mặt trời tạo với mặt đất một góc $\alpha$ (như hình minh họa). Công thức tính chiều cao tháp là:", 
                     rf"${bong} \times \tan \alpha$", [rf"${bong} \times \sin \alpha$", rf"${bong} \times \cos \alpha$", rf"${bong} \times \cot \alpha$"], 
                     r"$\tan = \text{Đối} / \text{Kề}$. Chiều cao = Bóng $\times \tan \alpha$.", img_thap)
        # Câu 22
        c1, c2, huyen = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17)])
        self.build_q(rf"Một chiếc thang dài {huyen}m dựa vào tường. Biết chân thang cách chân tường {c1}m. Chiều cao từ mặt đất lên đỉnh thang là", f"{c2}m", [f"{c2 + 2}m", f"{abs(huyen - c1)}m", f"{huyen + c1}m"], "Áp dụng định lý Pytago.")
        # Câu 23
        self.build_q(r"Cho tam giác $ABC$ vuông tại $A$, đường cao $AH$. Hệ thức lượng nào sau đây ĐÚNG?", r"$AH^2 = HB \cdot HC$", [r"$AH^2 = AB \cdot AC$", r"$AB^2 = HB \cdot HC$", r"$AC^2 = HB \cdot BC$"], "Bình phương đường cao bằng tích hai hình chiếu.")
        # Câu 24
        bk_nt = random.choice([4, 5, 6])
        self.build_q(rf"Bán kính đường tròn ngoại tiếp tam giác đều cạnh $a$ là $R$. Biết $a = {bk_nt}\sqrt{{3}}$ cm, tính $R$.", f"{bk_nt} cm", [f"{bk_nt * 2} cm", f"{bk_nt + 1} cm", f"{bk_nt * 3} cm"], r"Công thức $a = R\sqrt{3}$.")
        # Câu 25
        self.build_q(r"Khẳng định nào sau đây về Tỉ số lượng giác của hai góc phụ nhau là ĐÚNG?", r"$\sin 30^\circ = \cos 60^\circ$", [r"$\sin 30^\circ = \sin 60^\circ$", r"$\tan 30^\circ = \tan 60^\circ$", r"$\cos 30^\circ = \cot 60^\circ$"], "Hai góc phụ nhau thì sin góc này bằng cos góc kia.")

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN (6 CÂU) ---
        # Câu 26
        r1 = random.choice([1.4, 1.5, 1.6]); r2 = random.choice([1.1, 1.2, 1.3])
        self.build_q(r"Quan sát hình minh họa, hai đường tròn cắt nhau có bao nhiêu điểm chung?", "2 điểm", ["1 điểm", "0 điểm", "3 điểm"], "Cắt nhau tại chính xác 2 điểm.", draw_intersecting_circles(r1, r2))
        # Câu 27
        self.build_q(r"Tính chất tiếp tuyến: Từ điểm $M$ nằm ngoài đường tròn $(O)$, kẻ hai tiếp tuyến $MA, MB$. Khẳng định nào SAI?", r"Góc $OMA$ khác góc $OMB$", [r"$MA = MB$", r"$OM$ là tia phân giác của góc $AOB$", r"$OM$ vuông góc với $AB$"], "Tính chất hai tiếp tuyến cắt nhau.")
        # Câu 28
        g_tam = random.choice([50, 60, 70, 80])
        self.build_q(rf"Góc ở tâm $\widehat{{AOB}} = {g_tam}^\circ$. Góc nội tiếp $\widehat{{ACB}}$ cùng chắn cung nhỏ $AB$ có số đo là", rf"{g_tam // 2}$^\circ$", [rf"{g_tam}$^\circ$", rf"{180 - g_tam}$^\circ$", rf"{g_tam * 2}$^\circ$"], "Góc nội tiếp bằng nửa góc ở tâm cùng chắn một cung.")
        # Câu 29
        canh_hv = random.choice([4, 6, 8, 10])
        self.build_q(rf"Bán kính đường tròn nội tiếp hình vuông có cạnh {canh_hv} cm là", f"{canh_hv // 2} cm", [f"{canh_hv} cm", f"{canh_hv * 2} cm", rf"{canh_hv // 2}\sqrt{{2}} cm"], "Bán kính bằng một nửa độ dài cạnh.")
        # Câu 30
        self.build_q(r"Diện tích hình quạt tròn bán kính $R$, cung $n^\circ$ được tính theo công thức nào?", r"$S = \frac{\pi R^2 n}{360}$", [r"$S = \frac{\pi R n}{180}$", r"$S = \pi R^2$", r"$S = 2\pi R$"], "Học thuộc công thức SGK.")
        # Câu 31
        self.build_q(r"Tứ giác $ABCD$ nội tiếp đường tròn. Biết góc $A = 80^\circ$, tính số đo góc $C$ đối diện.", "100$^\circ$", ["80$^\circ$", "90$^\circ$", "180$^\circ$"], "Tổng hai góc đối của tứ giác nội tiếp bằng 180 độ.")

        # --- CHỦ ĐỀ 7: HÌNH KHỐI THỰC TẾ (3 CÂU) ---
        # Câu 32
        self.build_q(r"Công thức tính Thể tích khối cầu bán kính $R$ là", r"$V = \frac{4}{3}\pi R^3$", [r"$V = \frac{1}{3}\pi R^3$", r"$V = 4\pi R^2$", r"$V = \pi R^2 h$"], "Công thức chuẩn SGK.")
        # Câu 33
        bk_tru = random.choice([2, 3]); cao_tru = random.choice([5, 10])
        self.build_q(rf"Thực tế: Một bồn chứa nước hình trụ có bán kính đáy {bk_tru}m, chiều cao {cao_tru}m. Dung tích tối đa của bồn nước là", rf"{bk_tru**2 * cao_tru}$\pi$ m$^3$", [rf"{bk_tru * cao_tru}$\pi$ m$^3$", rf"{2 * bk_tru * cao_tru}$\pi$ m$^3$", rf"{bk_tru**2 * cao_tru}$ m$^3$"], r"Công thức: $V = \pi r^2 h$.")
        # Câu 34
        canh_lp = random.choice([3, 4, 5])
        self.build_q(rf"Một khối rubik hình lập phương có cạnh {canh_lp} cm. Diện tích toàn phần của khối rubik đó là", f"{6 * canh_lp**2} cm$^2$", [f"{4 * canh_lp**2} cm$^2$", f"{canh_lp**3} cm$^3$", f"{canh_lp**2} cm$^2$"], r"Diện tích toàn phần = 6 $\times$ (Cạnh)$^2$.")

        # --- CHỦ ĐỀ 8: THỐNG KÊ XÁC SUẤT (6 CÂU) ---
        # Câu 35
        dt = random.choice(["Lớp 9A", "Học sinh Nam", "Học sinh Nữ"])
        freqs = [random.randint(10, 40) for _ in range(5)]
        max_idx = freqs.index(max(freqs))
        bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
        self.build_q(rf"Đọc biểu đồ: Nhóm chiều cao nào của {dt} có tỉ lệ đông nhất?", rf"Nhóm {bins[max_idx]}", [rf"Nhóm {bins[(max_idx+1)%5]}", rf"Nhóm {bins[(max_idx+2)%5]}", rf"Nhóm {bins[(max_idx+3)%5]}"], "Quan sát biểu đồ, cột nào cao nhất tương ứng với tỉ lệ lớn nhất.", draw_vivid_histogram(freqs, dt))
        # Câu 36
        self.build_q(r"Không gian mẫu của phép thử tung đồng thời 2 đồng xu là", r"$\Omega = \{SS, SN, NS, NN\}$", [r"$\Omega = \{S, N\}$", r"$\Omega = \{SS, NN\}$", r"$\Omega = \{1, 2, 3, 4, 5, 6\}$"], "Mỗi đồng xu có 2 mặt, tổng cộng 2x2=4 trường hợp.")
        # Câu 37
        self.build_q(rf"Bạn {names[1]} kiểm tra chất lượng 50 bóng đèn thì thấy có 2 bóng bị hỏng. Tần số tương đối của bóng đèn bị hỏng là", "4%", ["2%", "5%", "10%"], "Tần số tương đối = (2 / 50) * 100%.")
        # Câu 38
        self.build_q(rf"Bảng điểm Toán: 7 điểm (4 bạn), 8 điểm (5 bạn), 9 điểm (2 bạn). Tần số của điểm 8 là", "5", ["4", "8", "2"], "Đọc trực tiếp từ bảng dữ liệu.")
        # Câu 39
        self.build_q(rf"Trò chơi: Bạn {names[2]} gieo một con xúc xắc 6 mặt cân đối. Xác suất để xuất hiện mặt lớn hơn 4 chấm (5, 6) là", r"$\frac{1}{3}$", [r"$\frac{1}{6}$", r"$\frac{1}{2}$", r"$\frac{2}{3}$"], "Có 2 mặt thỏa mãn trên tổng 6 mặt (2/6 = 1/3).")
        # Câu 40
        so_bi = random.randint(3, 5)
        self.build_q(rf"Hộp có {so_bi} bi xanh và {so_bi+2} bi đỏ. Xác suất để bạn {names[3]} bốc ngẫu nhiên được 1 viên bi xanh là", rf"$\frac{{{so_bi}}}{{{2*so_bi + 2}}}$", [rf"$\frac{{{so_bi+2}}}{{{2*so_bi + 2}}}$", r"$\frac{1}{2}$", rf"$\frac{{{so_bi}}}{{{so_bi + 2}}}$"], "Xác suất = Số bi xanh / Tổng số bi.")

        return self.exam

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
            <p style='color: #777; font-size: 18px;'>Kỳ thi tuyển sinh vào lớp 10 THPT (Ma trận 40 Câu Chống Lặp)</p>
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
        st.title("📝 Đề Thi Thử Vào 10 THPT (Ma trận 40 Câu VioEdu Style)")
        st.warning("⏱ Thời gian: 90 phút. Đề thi gồm chính xác 40 câu trắc nghiệm được sinh bởi AI với ngữ cảnh thực tế độc lập.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 LÀM ĐỀ MỚI (Trộn AI)", use_container_width=True):
                gen = ExamGenerator()
                st.session_state.exam_data = gen.generate_all()
                st.session_state.user_answers = {q['id']: None for q in st.session_state.exam_data}
                st.session_state.is_submitted = False
                st.rerun()
        with c2:
            if st.session_state.is_submitted and st.button("🔁 Làm lại đề vừa thi", use_container_width=True):
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
            # Thông báo chứng minh đã tạo đủ 40 câu
            st.success(f"✅ Hệ thống đã sinh ngẫu nhiên thành công bộ đề **{len(st.session_state.exam_data)}/40** câu hỏi chuẩn ma trận!")

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

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🚨 HỆ THỐNG PHÁT HIỆN LỖI: {e}")
