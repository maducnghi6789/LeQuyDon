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

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='DanhSachTaiKhoan')
    return output.getvalue()

def create_excel_template():
    df_template = pd.DataFrame(columns=["Họ tên", "Ngày sinh", "Trường"])
    df_template.loc[0] = ["Nguyễn Văn A", "15/08/2010", "THCS Lê Quý Đôn"]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='MauNhapLieu')
    return output.getvalue()

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    for col in ["fullname", "dob", "class_name", "school", "province", "managed_classes"]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    for col in ["start_time", "end_time", "target_class"]:
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
    if not dob or str(dob).lower() == 'nan': suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 3. HỆ THỐNG VẼ HÌNH HỌC TỰ ĐỘNG
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    fig, ax = plt.subplots(figsize=(3, 2))
    x = np.linspace(-3, 3, 100); y = -0.5 * x**2 + 4.5
    ax.plot(x, y, color='#c0392b', lw=2)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.text(0.2, 4.7, 'y', style='italic'); ax.text(3.2, 0.2, 'x', style='italic'); ax.text(0.1, -0.5, 'O')
    return fig_to_base64(fig)

def draw_intersecting_circles():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal') 
    c1 = plt.Circle((-0.8, 0), 1.5, color='#2980b9', fill=False, lw=1.5)
    c2 = plt.Circle((0.8, 0), 1.2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    ax.plot(0, 1.15, 'ko', markersize=4); ax.plot(0, -1.15, 'ko', markersize=4)
    ax.set_xlim(-2.5, 2.5); ax.set_ylim(-2, 2); ax.axis('off')
    return fig_to_base64(fig)

def draw_tower_shadow(bong):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([-1, 4], [0, 0], color='#27ae60', lw=3) 
    ax.plot([0, 0], [0, 3], color='#7f8c8d', lw=4)
    ax.plot([2.5, 0], [0, 3], color='#f39c12', lw=1.5, linestyle='--')
    ax.text(-0.8, 1.5, 'Tháp', rotation=90, fontsize=8)
    ax.text(0.5, -0.5, f'Bóng: {bong}m', fontsize=8)
    ax.text(1.8, 0.1, r'$\alpha$', fontsize=10, color='blue')
    ax.set_xlim(-1, 3); ax.set_ylim(-1, 3.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_histogram():
    fig, ax = plt.subplots(figsize=(4, 2.5))
    bins = ['[5;6)', '[6;7)', '[7;8)', '[8;9)', '[9;10]']
    percents = [10, 25, 40, 15, 10]
    bars = ax.bar(bins, percents, color=['#3498db']*5, edgecolor='black')
    bars[2].set_color('#e74c3c') 
    ax.set_title("Phổ điểm môn Toán", fontsize=9)
    ax.set_ylabel('% Học sinh', fontsize=8)
    ax.set_ylim(0, 50)
    return fig_to_base64(fig)

# ==========================================
# 4. BỘ MÁY SINH ĐỀ CHUẨN MA TRẬN 40 CÂU (ĐÃ FIX LỖI CÚ PHÁP)
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
                
        fallbacks = ["0", "1", "-1", "2", "Vô nghiệm", "Không xác định", "Kết quả khác"]
        for fb in fallbacks:
            if len(unique_options) == 4: break
            if fb not in unique_options: unique_options.append(fb)
                
        final_options = unique_options[:4]
        random.shuffle(final_options)
        self.exam.append({"id": self.q_count, "question": text, "options": final_options, "answer": correct_str, "hint": hint, "image": img_b64})
        self.q_count += 1

    def generate_all(self):
        # --- CHỦ ĐỀ 1: ĐẠI SỐ - CĂN THỨC & HÀM SỐ (10 Câu) ---
        a1 = random.randint(2, 9)
        self.build_q(rf"Điều kiện để biểu thức $\sqrt{{x - {a1}}}$ có nghĩa là", rf"$x \ge {a1}$", [rf"$x > {a1}$", rf"$x \le {a1}$", rf"$x < {a1}$"], rf"💡 **HD:** Căn thức bậc hai xác định khi biểu thức dưới căn không âm $\Rightarrow x - {a1} \ge 0 \Leftrightarrow x \ge {a1}$.")
        
        a2 = random.choice([16, 25, 36, 49, 64, 81])
        c2 = int(math.sqrt(a2))
        self.build_q(rf"Căn bậc hai số học của ${a2}$ là", f"{c2}", [f"$-{c2}$", rf"$\pm {c2}$", f"{a2**2}"], rf"💡 **HD:** Căn bậc hai số học của một số dương $a$ là số dương $x$ sao cho $x^2 = a$. Vậy đáp án là {c2}.")
        
        a3 = random.randint(2, 5); b3 = random.randint(6, 9)
        self.build_q(rf"Với $x < {a3}$, rút gọn biểu thức $\sqrt{{({a3} - x)^2}} + x - {b3}$ ta được:", f"{a3 - b3}", [f"{b3 - a3}", rf"$2x - {a3+b3}$", rf"$-2x + {a3+b3}$"], rf"💡 **HD:** Do $x < {a3} \Rightarrow {a3} - x > 0$. Suy ra $\sqrt{{({a3}-x)^2}} = |{a3}-x| = {a3}-x$. Biểu thức bằng $({a3}-x) + x - {b3} = {a3-b3}$.")
        
        a4 = random.choice([2, 3, 5])
        self.build_q(rf"Trục căn thức ở mẫu của biểu thức $\frac{{{a4}}}{{\sqrt{{{a4}}}}}$ ta được:", rf"$\sqrt{{{a4}}}$", [f"{a4}", "1", rf"${a4}\sqrt{{{a4}}}$"], rf"💡 **HD:** Nhân cả tử và mẫu với $\sqrt{{{a4}}}$, ta có $\frac{{{a4}\sqrt{{{a4}}}}}{{\sqrt{{{a4}}} \cdot \sqrt{{{a4}}}}} = \frac{{{a4}\sqrt{{{a4}}}}}{{{a4}}} = \sqrt{{{a4}}}$.")
        
        self.build_q(r"Với $a > 0, b > 0$, biểu thức $\sqrt{9a^2b}$ bằng", r"$3a\sqrt{b}$", [r"$-3a\sqrt{b}$", r"$9a\sqrt{b}$", r"$3a^2\sqrt{b}$"], r"💡 **HD:** Đưa thừa số ra ngoài dấu căn: $\sqrt{9a^2b} = \sqrt{(3a)^2 \cdot b} = |3a|\sqrt{b} = 3a\sqrt{b}$ (do $a>0$).")
        
        # [FIX LỖI CÂU 6 Ở ĐÂY - Tách riêng biến và LaTeX để Python không bị nhầm lẫn]
        a6 = random.choice([-2, -3, -4, -5])
        q6_hint = r"💡 **HD:** Hàm số $y = ax+b$ nghịch biến trên $\mathbb{R}$ khi hệ số $a < 0$. Ở đây $a = " + f"{a6}" + r" < 0$."
        self.build_q(rf"Hàm số $y = {a6}x + 3$ là hàm số:", r"Nghịch biến trên $\mathbb{R}$", [r"Đồng biến trên $\mathbb{R}$", r"Nghịch biến khi $x < 0$", r"Đồng biến khi $x > 0$"], q6_hint)
        
        b7 = random.randint(2, 9)
        self.build_q(rf"Đồ thị hàm số $y = 2x - {b7}$ cắt trục tung tại điểm có tọa độ là:", rf"$(0; -{b7})$", [rf"$(0; {b7})$", rf"$({b7}; 0)$", rf"$(0; 2)$"], rf"💡 **HD:** Điểm nằm trên trục tung có hoành độ $x=0$. Thay $x=0$ vào hàm số ta được $y = -{b7}$.")
        
        self.build_q(r"Quan sát hình vẽ. Đồ thị hàm số $y = ax^2 (a \ne 0)$ luôn nhận đường thẳng nào làm trục đối xứng?", "Trục tung (Oy)", ["Trục hoành (Ox)", "Đường thẳng $y = x$", "Đường thẳng $y = -x$"], "💡 **HD:** Đồ thị hàm số $y=ax^2$ là một Parabol đi qua gốc tọa độ O và nhận trục Oy làm trục đối xứng.", draw_real_parabola())
        
        x9 = random.choice([-2, 2, 3]); y9 = random.choice([4, 12, 18])
        a9 = y9 // (x9**2) if y9 % (x9**2) == 0 else f"{y9}/{x9**2}"
        self.build_q(rf"Biết đồ thị hàm số $y = ax^2$ đi qua điểm $M({x9}; {y9})$. Giá trị của hệ số $a$ là:", f"{a9}", [f"{y9 * abs(x9)}", f"{x9**2}", f"{y9}"], rf"💡 **HD:** Thay tọa độ $x = {x9}, y = {y9}$ vào pt $y = ax^2$, ta có: ${y9} = a \cdot ({x9})^2 \Rightarrow a = {a9}$.")
        
        self.build_q(r"Số giao điểm của Parabol $y = x^2$ và đường thẳng $y = x + 2$ là:", "2", ["0", "1", "3"], r"💡 **HD:** Xét pt hoành độ giao điểm: $x^2 = x + 2 \Leftrightarrow x^2 - x - 2 = 0$. PT này có $\Delta = (-1)^2 - 4(1)(-2) = 9 > 0$, nên có 2 nghiệm phân biệt.")

        # --- CHỦ ĐỀ 2: ĐẠI SỐ - PHƯƠNG TRÌNH & HỆ (10 Câu) ---
        self.build_q(r"Phương trình nào sau đây là phương trình bậc nhất hai ẩn $x, y$?", r"$2x - 3y = 5$", [r"$xy = 5$", r"$2x^2 - y = 0$", r"$x - \frac{1}{y} = 2$"], r"💡 **HD:** Phương trình bậc nhất 2 ẩn có dạng $ax + by = c$ (với $a,b$ không đồng thời bằng 0).")
        
        # [FIX LỖI CÂU 12 - Tách chuỗi ngoặc nhọn LaTeX]
        x12 = random.randint(1,4); y12 = random.randint(1,3)
        q12_text = r"Nghiệm $(x; y)$ của hệ phương trình $\begin{cases} x + y = " + f"{x12+y12}" + r" \\ x - y = " + f"{x12-y12}" + r" \end{cases}$ là:"
        self.build_q(q12_text, rf"$({x12}; {y12})$", [rf"$({y12}; {x12})$", rf"$({x12+1}; {y12})$", rf"$({x12}; -{y12})$"], rf"💡 **HD:** Cộng 2 vế ta được $2x = {2*x12} \Rightarrow x = {x12}$. Thay vào PT trên suy ra $y = {y12}$.")
        
        b13 = random.randint(3, 5); c13 = random.randint(1, 2)
        self.build_q(rf"Biệt thức $\Delta$ của phương trình $x^2 + {b13}x + {c13} = 0$ bằng:", f"{b13**2 - 4*1*c13}", [f"{b13**2 + 4*c13}", f"{b13 - 4*c13}", f"{b13**2 - c13}"], rf"💡 **HD:** Công thức $\Delta = b^2 - 4ac = ({b13})^2 - 4 \cdot 1 \cdot {c13} = {b13**2 - 4*c13}$.")
        
        # [FIX LỖI CÂU 14, 15 - Tách chuỗi phân số]
        b14 = random.randint(2, 8); c14 = random.randint(-5, -1)
        q14_hint = r"💡 **HD:** Theo định lý Vi-ét, tổng hai nghiệm $S = x_1 + x_2 = -\frac{b}{a} = -\frac{" + f"{-b14}" + r"}{1} = " + f"{b14}$."
        self.build_q(rf"Gọi $x_1, x_2$ là hai nghiệm của PT $x^2 - {b14}x {c14} = 0$. Tổng $x_1 + x_2$ bằng:", f"{b14}", [f"{-b14}", f"{c14}", f"{-c14}"], q14_hint)
        
        q15_hint = r"💡 **HD:** Theo định lý Vi-ét, tích hai nghiệm $P = x_1 \cdot x_2 = \frac{c}{a} = \frac{" + f"{c14}" + r"}{1} = " + f"{c14}$."
        self.build_q(rf"Gọi $x_1, x_2$ là hai nghiệm của PT $x^2 - {b14}x {c14} = 0$. Tích $x_1 \cdot x_2$ bằng:", f"{c14}", [f"{-c14}", f"{b14}", f"{-b14}"], q15_hint)
        
        # [FIX LỖI CÂU 16 - Tách chuỗi ngoặc nhọn của Tập hợp]
        m16 = random.randint(2, 4); n16 = random.randint(5, 7)
        ans16 = r"$\{" + f"{m16}; {n16}" + r"\}$"
        dis16_1 = r"$\{" + f"{-m16}; {-n16}" + r"\}$"
        dis16_2 = r"$\{" + f"{m16 * n16}" + r"\}$"
        dis16_3 = r"$\{" + f"{m16}; {-n16}" + r"\}$"
        self.build_q(rf"Tập nghiệm của phương trình $(x - {m16})(x - {n16}) = 0$ là:", ans16, [dis16_1, dis16_2, dis16_3], rf"💡 **HD:** PT $\Leftrightarrow x - {m16} = 0$ hoặc $x - {n16} = 0 \Leftrightarrow x = {m16}$ hoặc $x = {n16}$.")
        
        a17 = random.randint(1, 3)
        q17_text = r"Điều kiện xác định của phương trình $\frac{x+1}{x-" + f"{a17}" + r"} = 2$ là:"
        self.build_q(q17_text, rf"$x \ne {a17}$", [rf"$x \ne -{a17}$", rf"$x > {a17}$", rf"$x \ge {a17}$"], rf"💡 **HD:** Phương trình có nghĩa khi mẫu số khác 0 $\Rightarrow x - {a17} \ne 0 \Leftrightarrow x \ne {a17}$.")
        
        v18 = random.choice([30, 40, 50])
        self.build_q(rf"Một ô tô đi quãng đường 120km với vận tốc $x$ km/h. Thời gian đi là:", r"$\frac{120}{x}$ giờ", [rf"$120x$ giờ", r"$\frac{x}{120}$ giờ", rf"$120 + x$ giờ"], r"💡 **HD:** Công thức tính thời gian: $t = \frac{S}{v} = \frac{120}{x}$.")
        
        self.build_q(r"Với mọi số thực $a, b$ thoả mãn $a < b$, khẳng định nào sau đây LUÔN ĐÚNG?", r"$a - 5 < b - 5$", [r"$a + 5 > b + 5$", r"$-2a < -2b$", r"$3a > 3b$"], r"💡 **HD:** Cộng hoặc trừ cùng một số vào 2 vế của BĐT thì chiều BĐT không đổi.")
        
        sv20 = random.randint(4, 7); pv20 = random.randint(2, 3)
        self.build_q(rf"Hai số có tổng bằng {sv20} và tích bằng {pv20} là nghiệm của phương trình nào?", rf"$x^2 - {sv20}x + {pv20} = 0$", [rf"$x^2 + {sv20}x + {pv20} = 0$", rf"$x^2 - {pv20}x + {sv20} = 0$", rf"$x^2 + {pv20}x - {sv20} = 0$"], r"💡 **HD:** Theo hệ thức Vi-ét đảo, hai số là nghiệm của PT $X^2 - SX + P = 0$.")

        # --- CHỦ ĐỀ 3: HÌNH HỌC (12 Câu) ---
        self.build_q(r"Cho $\Delta ABC$ vuông tại $A$, đường cao $AH$. Khẳng định ĐÚNG là:", r"$AH^2 = HB \cdot HC$", [r"$AH^2 = AB \cdot AC$", r"$AB^2 = HB \cdot HC$", r"$AC^2 = HB \cdot BC$"], r"💡 **HD:** Trong tam giác vuông, bình phương đường cao ứng với cạnh huyền bằng tích hai hình chiếu của 2 cạnh góc vuông.")
        
        self.build_q(r"Cho góc nhọn $\alpha$. Hệ thức nào sau đây ĐÚNG?", r"$\sin^2 \alpha + \cos^2 \alpha = 1$", [r"$\sin \alpha + \cos \alpha = 1$", r"$\tan \alpha \cdot \cot \alpha = 0$", r"$\sin^2 \alpha - \cos^2 \alpha = 1$"], r"💡 **HD:** Hệ thức cơ bản của lượng giác.")
        
        bong23 = random.choice([20, 30, 40])
        self.build_q(rf"Một cột tháp có bóng trên mặt đất dài {bong23}m. Tia nắng tạo với mặt đất góc $45^\circ$ (như hình vẽ). Chiều cao tháp là:", rf"${bong23}$ m", [rf"${bong23}\sqrt{{2}}$ m", rf"${bong23}\sqrt{{3}}$ m", rf"${bong23}/2$ m"], rf"💡 **HD:** Dùng Tan: Chiều cao = Bóng $\times \tan(45^\circ) = {bong23} \times 1 = {bong23}m$.", draw_tower_shadow(bong23))
        
        self.build_q(r"Quan sát hình vẽ, hai đường tròn này có bao nhiêu điểm chung?", "2 điểm chung", ["0 điểm chung", "1 điểm chung", "3 điểm chung"], "💡 **HD:** Hai đường tròn cắt nhau tại 2 điểm phân biệt.", draw_intersecting_circles())
        
        self.build_q(r"Từ điểm $M$ nằm ngoài đường tròn $(O)$, kẻ 2 tiếp tuyến $MA, MB$. Khẳng định SAI là:", r"$\widehat{OMA} \ne \widehat{OMB}$", [r"$MA = MB$", r"$OM$ là phân giác góc $\widehat{AOB}$", r"$OM \perp AB$"], r"💡 **HD:** Tính chất 2 tiếp tuyến cắt nhau: $\widehat{OMA} = \widehat{OMB}$.")
        
        self.build_q(r"Góc nội tiếp chắn nửa đường tròn có số đo bằng:", r"$90^\circ$", [r"$180^\circ$", r"$60^\circ$", r"$45^\circ$"], r"💡 **HD:** Định lý SGK Toán 9: Góc nội tiếp chắn nửa đường tròn luôn là góc vuông.")
        
        g27 = random.choice([60, 70, 80])
        self.build_q(rf"Biết góc ở tâm $\widehat{{AOB}} = {g27}^\circ$. Góc nội tiếp $\widehat{{ACB}}$ cùng chắn cung $AB$ có số đo bằng:", rf"${g27//2}^\circ$", [rf"${g27}^\circ$", rf"${g27*2}^\circ$", rf"${180 - g27}^\circ$"], r"💡 **HD:** Góc nội tiếp bằng một nửa số đo góc ở tâm cùng chắn một cung.")
        
        self.build_q(r"Tứ giác $ABCD$ nội tiếp đường tròn. Biết $\widehat{A} = 85^\circ$, tính $\widehat{C}$ (góc đối diện).", r"$95^\circ$", [r"$85^\circ$", r"$105^\circ$", r"$180^\circ$"], r"💡 **HD:** Tổng số đo 2 góc đối diện của tứ giác nội tiếp bằng $180^\circ$.")
        
        R29 = random.choice([3, 4, 5])
        self.build_q(rf"Chu vi đường tròn có bán kính $R = {R29}$ cm là:", rf"${2*R29}\pi$ cm", [rf"${R29}\pi$ cm", rf"${R29**2}\pi$ cm", rf"${2*R29}$ cm"], r"💡 **HD:** Công thức chu vi đường tròn $C = 2\pi R$.")
        
        h30 = random.choice([5, 6]); r30 = random.choice([2, 3])
        q30_ans = r"$" + f"{r30**2 * h30}" + r"\pi$ cm$^3$"
        q30_dis1 = r"$" + f"{2*r30 * h30}" + r"\pi$ cm$^3$"
        q30_dis2 = r"$" + f"{r30 * h30}" + r"\pi$ cm$^3$"
        q30_dis3 = r"$\frac{" + f"{r30**2 * h30}" + r"\pi}{3}$ cm$^3$"
        self.build_q(rf"Một hình trụ có bán kính đáy $r={r30}$ cm, chiều cao $h={h30}$ cm. Thể tích hình trụ là:", q30_ans, [q30_dis1, q30_dis2, q30_dis3], r"💡 **HD:** Công thức thể tích khối trụ $V = \pi r^2 h$.")
        
        self.build_q(r"Công thức tính diện tích xung quanh của hình nón bán kính đáy $r$, đường sinh $l$ là:", r"$S = \pi r l$", [r"$S = 2\pi r l$", r"$S = \pi r^2 l$", r"$S = \frac{1}{3} \pi r l$"], r"💡 **HD:** Công thức chuẩn SGK: $S = \pi r l$.")
        
        self.build_q(r"Công thức tính diện tích mặt cầu bán kính $R$ là:", r"$S = 4\pi R^2$", [r"$S = \frac{4}{3}\pi R^3$", r"$S = \pi R^2$", r"$S = 2\pi R^2$"], r"💡 **HD:** Diện tích mặt cầu $S = 4\pi R^2$.")

        # --- CHỦ ĐỀ 4: THỐNG KÊ & XÁC SUẤT (8 Câu) ---
        self.build_q(r"Dựa vào biểu đồ Phổ điểm Toán, nhóm điểm nào có tỉ lệ học sinh đạt cao nhất?", r"Nhóm $[7;8)$", [r"Nhóm $[6;7)$", r"Nhóm $[8;9)$", r"Nhóm $[5;6)$"], r"💡 **HD:** Cột màu đỏ cao nhất tương ứng với nhóm [7;8) chiếm 40%.", draw_histogram())
        
        self.build_q(r"Gieo đồng thời hai đồng xu cân đối. Tập hợp các kết quả có thể xảy ra (Không gian mẫu) là:", r"$\{SS, SN, NS, NN\}$", [r"$\{S, N\}$", r"$\{SS, NN\}$", r"$\{1, 2, 3, 4\}$"], r"💡 **HD:** Có $2 \times 2 = 4$ trường hợp: Sấp-Sấp, Sấp-Ngửa, Ngửa-Sấp, Ngửa-Ngửa.")
        
        self.build_q(r"Gieo một con xúc xắc 6 mặt. Xác suất xuất hiện mặt có số chấm lớn hơn 4 là:", r"$\frac{1}{3}$", [r"$\frac{1}{6}$", r"$\frac{1}{2}$", r"$\frac{2}{3}$"], r"💡 **HD:** Mặt > 4 gồm {5, 6} (2 kết quả). Xác suất = $\frac{2}{6} = \frac{1}{3}$.")
        
        bx36 = random.randint(3,5); bd36 = random.randint(4,6)
        q36_ans = r"$\frac{" + f"{bd36}" + r"}{" + f"{bx36+bd36}" + r"}$"
        self.build_q(rf"Hộp có {bx36} bi xanh và {bd36} bi đỏ. Xác suất bốc 1 viên bi ra bi đỏ là:", q36_ans, [r"$\frac{1}{2}$", rf"$\frac{{{bx36}}}{{{bx36+bd36}}}$", rf"$\frac{{{bd36}}}{{{bx36}}}$"], rf"💡 **HD:** Tổng bi: {bx36+bd36}. Bi đỏ: {bd36}. Xác suất = $\frac{{{bd36}}}{{{bx36+bd36}}}$.")
        
        self.build_q(r"Kiểm tra 50 bóng đèn thì thấy có 2 bóng bị hỏng. Tần số tương đối của bóng đèn hỏng là:", r"$4\%$", [r"$2\%$", r"$5\%$", r"$20\%$"], r"💡 **HD:** Tần số tương đối = $\frac{2}{50} \times 100\% = 4\%$.")
        
        self.build_q(r"Bảng điểm của 4 học sinh: 7, 8, 8, 9. Điểm trung bình là:", r"$8,0$", [r"$7,5$", r"$8,5$", r"$8,2$"], r"💡 **HD:** $\bar{X} = \frac{7+8+8+9}{4} = 8,0$.")
        
        self.build_q(r"Cầu thủ sút phạt 100 quả, trúng đích 85 quả. Xác suất thực nghiệm sút trúng là:", r"$0,85$", [r"$0,15$", r"$8,5$", r"$15$"], r"💡 **HD:** Xác suất = Số lần trúng / Tổng số lần = $\frac{85}{100} = 0,85$.")
        
        self.build_q(r"Trong các biến cố sau khi gieo 1 xúc xắc, biến cố nào là CHẮC CHẮN?", r"Xuất hiện mặt có số chấm nhỏ hơn 7", [r"Xuất hiện mặt 6 chấm", r"Xuất hiện mặt chẵn", r"Xuất hiện mặt lớn hơn 7"], r"💡 **HD:** Xúc xắc có 6 mặt từ 1 đến 6, nên việc gieo ra mặt nhỏ hơn 7 là điều chắc chắn xảy ra.")

        return self.exam

# ==========================================
# 5. GIAO DIỆN LMS MANAGER CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="LMS - Đánh Giá Tuyên Quang", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2E3B55;'>🎓 HỆ THỐNG QUẢN LÝ HỌC TẬP</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### 🔒 Cổng Đăng Nhập")
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
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cls = c.fetchone()
            student_class = res_cls[0] if res_cls else ""
            
            query_exams = "SELECT id, title, start_time, end_time, questions_json FROM mandatory_exams WHERE target_class='Toàn trường' OR target_class=? ORDER BY id DESC"
            df_exams = pd.read_sql_query(query_exams, conn, params=(student_class,))
            
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
                    js_timer = f"""<script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId); document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG TỰ ĐỘNG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{ if (btns[i].innerText.includes('NỘP BÀI CHÍNH THỨC')) {{ btns[i].click(); break; }} }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60); var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Thời gian còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script><div id="clock" style="font-size:22px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:8px; margin-bottom:15px;"></div>"""
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 {exam_row['title']}")
                    if f"mand_ans_{exam_id}" not in st.session_state:
                        st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                        
                    for q in mand_exam_data:
                        st.markdown(f"**{q['question']}**", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / 40) * 10
                        c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(st.session_state[f"mand_ans_{exam_id}"])))
                        conn.commit()
                        st.success("✅ Đã nộp bài!")
                        st.session_state.active_mand_exam = None
                        st.rerun()
                        
                elif mode == 'review':
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
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                        with st.expander("📖 Xem Lời Giải Chi Tiết"): st.markdown(q['hint'], unsafe_allow_html=True)
                        st.markdown("---")
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
            conn.close()

        with tab_ai:
            st.title("Luyện Tập Tự Do (40 Câu Chuẩn Ma Trận)")
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ MỚI AI", use_container_width=True):
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
                    
                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.success("✅ Đúng")
                        else: st.error(f"❌ Sai. Đáp án: {q['answer']}")
                        with st.expander("📖 Lời Giải"): st.markdown(q['hint'], unsafe_allow_html=True)
                    st.markdown("---")
                
                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ LUYỆN", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu (Giao bài)"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "⚙️ Nạp dữ liệu (Giao bài)"])
            tab_class, tab_scores, tab_system = tabs
        
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        
        c.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL")
        student_classes = [r[0] for r in c.fetchall()]
        c.execute("SELECT managed_classes FROM users WHERE managed_classes IS NOT NULL")
        manager_classes_raw = [r[0] for r in c.fetchall()]
        
        all_classes_set = set(student_classes)
        for mc in manager_classes_raw:
            for cls in mc.split(','):
                if cls.strip(): all_classes_set.add(cls.strip())
        all_system_classes = sorted(list(all_classes_set))

        if st.session_state.role in ['core_admin', 'sub_admin']: available_classes = all_system_classes
        else:
            c.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,))
            m_cls = c.fetchone()[0]
            available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
        
        # --- TAB 1: QUẢN LÝ LỚP & HỌC SINH ---
        with tab_class:
            if not available_classes: st.info("Chưa có lớp học nào được tạo hoặc được phân công cho bạn.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                c.execute("SELECT fullname FROM users WHERE role='student' AND class_name=?", (selected_class,))
                existing_names = [row[0].strip().lower() for row in c.fetchall()]

                with st.expander(f"➕ Tạo tài khoản Học sinh cho lớp {selected_class}", expanded=False):
                    template_excel = create_excel_template()
                    st.download_button(label="⬇️ TẢI FILE EXCEL MẪU", data=template_excel, file_name="Mau_Danh_Sach_Hoc_Sinh.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                    uploaded_excel = st.file_uploader("Nạp file Excel (Đã điền)", type=['xlsx'])
                    if uploaded_excel is not None:
                        if st.button("🔄 Nạp dữ liệu"):
                            try:
                                df_import = pd.read_excel(uploaded_excel)
                                count_success = 0
                                for _, row in df_import.iterrows():
                                    fullname = str(row.get('Họ tên', '')).strip()
                                    dob = str(row.get('Ngày sinh', '')).strip()
                                    school = str(row.get('Trường', '')).strip()
                                    if fullname and fullname.lower() != 'nan':
                                        if dob.lower() == 'nan': dob = ""
                                        if school.lower() == 'nan': school = ""
                                        if fullname.lower() in existing_names and not dob: continue 
                                        uname = generate_username(fullname, dob)
                                        try:
                                            c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, fullname, dob, selected_class, school))
                                            count_success += 1
                                            existing_names.append(fullname.lower()) 
                                        except: pass
                                conn.commit()
                                st.success(f"✅ Đã tạo {count_success} tài khoản!")
                                st.rerun()
                            except: st.error("Lỗi đọc file Excel.")
                    
                    st.markdown("**Hoặc Tạo Thủ Công:**")
                    with st.form("manual_add"):
                        c1, c2 = st.columns(2)
                        m_name = c1.text_input("Họ và Tên (Bắt buộc)")
                        m_dob = c2.text_input("Ngày sinh")
                        m_school = c1.text_input("Trường")
                        if st.form_submit_button("Tạo nhanh"):
                            if m_name:
                                if m_name.strip().lower() in existing_names and not m_dob.strip(): st.error("⚠️ Bị trùng. BẮT BUỘC nhập 'Ngày sinh'!")
                                else:
                                    uname = generate_username(m_name, m_dob)
                                    c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, m_name, m_dob, selected_class, m_school))
                                    conn.commit()
                                    st.success(f"✅ Đã tạo: {uname} | Pass: 123456")
                                    st.rerun()

                st.markdown("---")
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên', dob as 'Ngày sinh', school as 'Trường' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                if not df_students.empty:
                    excel_export = to_excel(df_students)
                    st.download_button(label=f"📥 XUẤT EXCEL DANH SÁCH LỚP {selected_class}", data=excel_export, file_name=f"Danh_sach_{selected_class}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    st.markdown("#### ✏️ Tùy chỉnh thông tin & Xóa Học sinh")
                    user_to_edit = st.selectbox("Chọn Học sinh:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        c.execute("SELECT fullname, password, dob, school, class_name FROM users WHERE username=?", (user_to_edit,))
                        u_data = c.fetchone()
                        with st.form("edit_form"):
                            c1, c2 = st.columns(2)
                            edit_name = c1.text_input("Họ và Tên", value=u_data[0])
                            edit_pwd = c2.text_input("Mật khẩu", value=u_data[1])
                            edit_dob = c1.text_input("Ngày sinh", value=u_data[2] if u_data[2] else "")
                            edit_school = c2.text_input("Trường", value=u_data[3] if u_data[3] else "")
                            edit_class = st.text_input("Đổi Lớp", value=u_data[4])
                            if st.form_submit_button("💾 Cập nhật"):
                                c.execute("UPDATE users SET fullname=?, password=?, dob=?, school=?, class_name=? WHERE username=?", (edit_name, edit_pwd, edit_dob, edit_school, edit_class, user_to_edit))
                                conn.commit()
                                st.success("✅ Cập nhật thành công!")
                                st.rerun()
                        if st.button("🗑 XÓA TÀI KHOẢN NÀY", type="secondary"):
                            c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                            c.execute("DELETE FROM mandatory_results WHERE username=?", (user_to_edit,))
                            conn.commit()
                            st.rerun()
                st.markdown("---")
                with st.expander("🚨 Dọn dẹp Cuối năm (Xóa lớp)"):
                    if st.checkbox("Xóa vĩnh viễn toàn bộ học sinh lớp này."):
                        if st.button("🗑 XÓA LỚP", type="primary"):
                            for u in df_students['Tài khoản'].tolist():
                                c.execute("DELETE FROM users WHERE username=?", (u,))
                                c.execute("DELETE FROM mandatory_results WHERE username=?", (u,))
                            conn.commit()
                            st.rerun()

        # --- TAB 2: QUẢN LÝ NHÂN SỰ ---
        if st.session_state.role in ['core_admin', 'sub_admin']:
            with tab_staff:
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    with st.form("add_sa"):
                        c1, c2 = st.columns(2)
                        sa_user = c1.text_input("Tài khoản (viết liền)")
                        sa_pwd = c2.text_input("Mật khẩu")
                        sa_name = c1.text_input("Họ Tên")
                        sa_class = c2.text_input("Giao Lớp quản lý (VD: 9E)")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'sub_admin', ?, ?)", (sa_user, sa_pwd, sa_name, sa_class))
                                conn.commit()
                                st.rerun()
                            except: st.error("❌ Tên tồn tại!")
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    sa_to_del = st.selectbox("Xóa Admin:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    if sa_to_del != "-- Chọn --" and st.button("Xóa"):
                        c.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                        conn.commit()
                        st.rerun()
                    st.markdown("---")

                if st.session_state.role == 'sub_admin':
                    st.subheader("🛡️ Hồ sơ của tôi (Tự nhận lớp)")
                    c.execute("SELECT managed_classes, password FROM users WHERE username=?", (st.session_state.current_user,))
                    my_data = c.fetchone()
                    with st.form("self_edit_form"):
                        col1, col2 = st.columns(2)
                        my_pass = col1.text_input("Đổi mật khẩu", value=my_data[1])
                        my_cls = col2.text_input("Tự nhận lớp quản lý (VD: 9A)", value=my_data[0] if my_data[0] else "")
                        if st.form_submit_button("Lưu Hồ sơ", type="primary"):
                            c.execute("UPDATE users SET password=?, managed_classes=? WHERE username=?", (my_pass, my_cls, st.session_state.current_user))
                            conn.commit()
                            st.rerun()
                    st.markdown("---")

                st.subheader("👨‍🏫 Quản lý Giáo viên")
                with st.form("add_gv"):
                    c1, c2 = st.columns(2)
                    t_user = c1.text_input("Tài khoản GV")
                    t_pwd = c2.text_input("Mật khẩu")
                    t_name = c1.text_input("Họ và Tên")
                    t_classes = c2.text_input("Lớp QL (VD: 9A1)")
                    if st.form_submit_button("Tạo GV", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", (t_user, t_pwd, t_name, t_classes))
                            conn.commit()
                            st.rerun()
                        except: st.error("❌ Tồn tại!")
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                t_to_del = st.selectbox("Xóa GV:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_del != "-- Chọn --" and st.button("Xóa GV"):
                    c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                    conn.commit()
                    st.rerun()

        # --- TAB 3: BÁO CÁO ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                selected_rep_class = st.selectbox("📌 Chọn Lớp xem báo cáo:", available_classes, key="rep_class")
                df_all_exams = pd.read_sql_query("SELECT id, title, questions_json FROM mandatory_exams ORDER BY id DESC", conn)
                if df_all_exams.empty: st.info("Chưa có bài tập.")
                else:
                    selected_exam_title = st.selectbox("📝 Chọn Bài:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    
                    df_class_students = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{selected_rep_class}'", conn)
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng HS", len(df_class_students))
                    c2.metric("Đã nộp", len(df_submitted))
                    c3.metric("Chưa nộp", len(df_class_students) - len(df_submitted))
                    
                    t1, t2 = st.tabs(["✅ Bảng Điểm", "❌ HS Chưa Làm Bài"])
                    with t1:
                        if not df_submitted.empty: st.dataframe(df_submitted[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Nộp lúc'}), use_container_width=True)
                        else: st.info("Chưa có ai nộp.")
                    with t2:
                        submitted_users = df_submitted['username'].tolist()
                        df_missing = df_class_students[~df_class_students['username'].isin(submitted_users)]
                        if not df_missing.empty: st.dataframe(df_missing[['username', 'fullname']], use_container_width=True)
                        else: st.success("100% HS đã nộp bài.")
            
        # --- TAB 4: NẠP DỮ LIỆU & GIAO BÀI ---
        with tab_system:
            st.subheader("📤 Giao bài AI (KẾT NỐI THEO LỚP)")
            assign_options = ["Toàn trường"] if st.session_state.role in ['core_admin', 'sub_admin'] else []
            assign_options.extend(available_classes)
            
            if not assign_options: st.warning("Bạn chưa được cấp quyền quản lý lớp nào.")
            else:
                target_class = st.selectbox("🎯 Giao bài cho đối tượng:", assign_options)
                uploaded_pdf = st.file_uploader("Tải Đề thi (PDF)", type=['pdf', 'docx'])
                exam_title = st.text_input("Tên bài kiểm tra (VD: Khảo sát Toán 9)")
                col1, col2 = st.columns(2)
                s_date = col1.date_input("Ngày giao")
                s_time = col1.time_input("Giờ giao", value=datetime.strptime("07:00", "%H:%M").time())
                e_date = col2.date_input("Ngày thu")
                e_time = col2.time_input("Giờ thu", value=datetime.strptime("23:59", "%H:%M").time())
                
                if st.button("🚀 Giao bài", type="primary"):
                    if exam_title:
                        gen = ExamGenerator()
                        fixed_exam = gen.generate_all()
                        s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                        e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                        c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?, ?, ?, ?, ?)", (exam_title.strip(), json.dumps(fixed_exam), s_str, e_str, target_class))
                        conn.commit()
                        st.success(f"✅ Đã phát đề thành công tới {target_class}!")
                    else: st.error("Cần nhập tên bài!")
        conn.close()

if __name__ == "__main__":
    main()
