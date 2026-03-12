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
# 3. HỆ THỐNG VẼ HÌNH HỌC TỰ ĐỘNG CHUẨN XÁC
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_real_parabola():
    fig, ax = plt.subplots(figsize=(3, 2))
    x = np.linspace(-3, 3, 100); y = 0.5 * x**2
    ax.plot(x, y, color='#2980b9', lw=2)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.text(0.2, 4.5, 'y', style='italic'); ax.text(3.2, 0.2, 'x', style='italic'); ax.text(-0.3, -0.3, 'O')
    return fig_to_base64(fig)

def draw_intersecting_circles():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    x1, y1, r1 = -1, 0, 2; x2, y2, r2 = 1, 0, 1.5
    c1 = plt.Circle((x1, y1), r1, color='#c0392b', fill=False, lw=1.5)
    c2 = plt.Circle((x2, y2), r2, color='#27ae60', fill=False, lw=1.5)
    ax.add_patch(c1); ax.add_patch(c2)
    d = x2 - x1
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(r1**2 - a**2)
    x3 = x1 + a; y3_1 = y1 + h; y3_2 = y1 - h
    ax.plot(x3, y3_1, 'ko', markersize=5); ax.plot(x3, y3_2, 'ko', markersize=5)
    ax.plot([x1, x2], [y1, y2], 'k--', lw=0.8)
    ax.plot([x3, x3], [y3_1, y3_2], 'b--', lw=0.8)
    ax.set_xlim(-3.5, 3); ax.set_ylim(-2.5, 2.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_right_triangle(a, b):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([0, b, 0, 0], [0, 0, a, 0], color='#2c3e50', lw=2)
    ax.plot([0, 0.3, 0.3], [0.3, 0.3, 0], color='red', lw=1)
    # FIX LỖI: Đẩy chữ xa ra khỏi nét vẽ để không bị đè
    ax.text(-0.3, -0.3, 'A', fontweight='bold', ha='center', va='center')
    ax.text(b + 0.3, -0.3, 'B', fontweight='bold', ha='center', va='center')
    ax.text(-0.3, a + 0.3, 'C', fontweight='bold', ha='center', va='center')
    ax.text(b/2, -0.6, f'{b} cm', color='blue', ha='center')
    ax.text(-0.8, a/2, f'{a} cm', color='blue', va='center')
    # Tăng giới hạn trục để hình có không gian thở
    ax.set_xlim(-1.5, b + 1.5)
    ax.set_ylim(-1.5, a + 1.5)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_pie_chart():
    fig, ax = plt.subplots(figsize=(3, 3))
    labels = ['Giỏi', 'Khá', 'TB', 'Yếu']
    sizes = [25, 45, 20, 10]
    colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']
    explode = (0.1, 0, 0, 0)  
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    ax.axis('equal') 
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
# 4. BỘ MÁY SINH ĐỀ CHUẨN MA TRẬN 40 CÂU 
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
                
        fallbacks = ["0", "1", "-1", "2", "Vô nghiệm", "Không xác định"]
        for fb in fallbacks:
            if len(unique_options) == 4: break
            if fb not in unique_options: unique_options.append(fb)
                
        final_options = unique_options[:4]
        random.shuffle(final_options)
        self.exam.append({"id": self.q_count, "question": text, "options": final_options, "answer": correct_str, "hint": hint, "image": img_b64})
        self.q_count += 1

    def generate_all(self):
        # Đã xóa các cụm từ "Câu 1:" trong string để giao diện tự đánh số.
        
        # --- CHỦ ĐỀ 1: ĐẠI SỐ (8 Câu) ---
        a1 = random.randint(2, 9)
        self.build_q(r"Điều kiện xác định của biểu thức $\sqrt{2x - " + str(2*a1) + r"}$ là:", r"$x \ge " + str(a1) + r"$", [r"$x > " + str(a1) + r"$", r"$x \le " + str(a1) + r"$", r"$x < " + str(a1) + r"$"], r"💡 **HD:** Biểu thức dưới căn không âm: $2x - " + str(2*a1) + r" \ge 0 \Leftrightarrow x \ge " + str(a1) + r"$.")

        self.build_q(r"Giá trị của biểu thức $\sqrt{12} - 2\sqrt{3}$ bằng:", "0", [r"$\sqrt{9}$", r"$2\sqrt{3}$", "3"], r"💡 **HD:** $\sqrt{12} = \sqrt{4 \cdot 3} = 2\sqrt{3}$. Vậy $2\sqrt{3} - 2\sqrt{3} = 0$.")

        a3 = random.randint(3, 5)
        self.build_q(r"Với $a \ge 0$, biểu thức $\sqrt{" + str(a3**2) + r"a^2}$ bằng:", str(a3) + "a", [r"$-" + str(a3) + r"a$", str(a3**2) + "a", str(a3) + "|a|"], r"💡 **HD:** Đưa ra ngoài dấu căn, với $a \ge 0 \Rightarrow " + str(a3) + r"a$.")

        a4 = random.randint(2, 7)
        self.build_q(r"Trục căn thức ở mẫu của biểu thức $\frac{1}{\sqrt{" + str(a4) + r"} - 1}$ ta được:", r"$\frac{\sqrt{" + str(a4) + r"} + 1}{" + str(a4-1) + r"}$", [r"$\frac{\sqrt{" + str(a4) + r"} - 1}{" + str(a4-1) + r"}$", r"$\sqrt{" + str(a4) + r"} + 1$", r"$\frac{\sqrt{" + str(a4) + r"} + 1}{" + str(a4+1) + r"}$"], r"💡 **HD:** Nhân tử và mẫu với lượng liên hợp $(\sqrt{" + str(a4) + r"} + 1)$.")

        m5 = random.randint(2, 5)
        self.build_q(r"Để hàm số $y = (m - " + str(m5) + r")x + 3$ đồng biến trên $\mathbb{R}$, thì điều kiện của $m$ là:", r"$m > " + str(m5) + r"$", [r"$m < " + str(m5) + r"$", r"$m \ne " + str(m5) + r"$", r"$m \ge " + str(m5) + r"$"], r"💡 **HD:** Hàm số đồng biến khi hệ số $a > 0 \Leftrightarrow m - " + str(m5) + r" > 0$.")

        self.build_q(r"Đường thẳng $y = 2x + 1$ song song với đường thẳng nào dưới đây?", r"$y = 2x - 3$", [r"$y = -2x + 1$", r"$y = \frac{1}{2}x + 1$", r"$y = 2x + 1$"], r"💡 **HD:** Song song khi $a=a'$ và $b \ne b'$.")

        self.build_q(r"Quan sát đồ thị Parabol $y = ax^2$ trong hình vẽ. Khẳng định nào sau đây ĐÚNG?", r"Hệ số $a > 0$", [r"Hệ số $a < 0$", r"Hàm số luôn nghịch biến", r"Đồ thị nhận trục $Ox$ làm trục đối xứng"], r"💡 **HD:** Bề lõm hướng lên trên $\Rightarrow a > 0$.", draw_real_parabola())

        c8 = random.randint(1, 4)
        self.build_q(r"Tọa độ giao điểm của parabol $y = x^2$ và đường thẳng $y = " + str(c8**2) + r"$ là:", r"$( " + str(c8) + r"; " + str(c8**2) + r")$ và $(-" + str(c8) + r"; " + str(c8**2) + r")$", [r"$( " + str(c8) + r"; " + str(c8**2) + r")$", r"$(-" + str(c8) + r"; " + str(c8**2) + r")$", r"$(0; 0)$"], r"💡 **HD:** Giải phương trình hoành độ giao điểm.")

        # --- CHỦ ĐỀ 2: PHƯƠNG TRÌNH & THỰC TẾ (8 Câu) ---
        self.build_q(r"Nghiệm của hệ phương trình $\begin{cases} x - y = 1 \\ 2x + y = 5 \end{cases}$ là:", r"$(2; 1)$", [r"$(1; 2)$", r"$(3; -1)$", r"$(2; -1)$"], r"💡 **HD:** Cộng 2 vế: $3x = 6 \Rightarrow x=2$.")

        self.build_q(r"Giá cước taxi: 10.000đ cho 1km đầu tiên, từ km thứ 2 giá 15.000đ/km. Hỏi đi 5km phải trả bao nhiêu tiền?", "70.000 đ", ["75.000 đ", "50.000 đ", "60.000 đ"], r"💡 **HD:** Tiền = 10.000 + 4 $\times$ 15.000 = 70.000đ.")

        p11 = random.choice([100, 200, 300])
        self.build_q(r"Bác An gửi tiết kiệm " + str(p11) + r" triệu đồng với lãi suất 6%/năm. Sau 1 năm, tổng số tiền bác An nhận được cả gốc và lãi là:", str(int(p11 * 1.06)) + r" triệu", [str(int(p11 * 0.06)) + r" triệu", str(p11 + 6) + r" triệu", str(int(p11 * 1.6)) + r" triệu"], r"💡 **HD:** Tổng = Gốc $\times (1 + 0.06)$.")

        self.build_q(r"Tập nghiệm của phương trình $x^2 - 5x + 6 = 0$ là:", r"$\{2; 3\}$", [r"$\{-2; -3\}$", r"$\{1; 6\}$", r"$\{-1; -6\}$"], r"💡 **HD:** $2+3=5$ và $2 \times 3=6$.")

        self.build_q(r"Cho phương trình $2x^2 - 7x + 3 = 0$. Tổng hai nghiệm $x_1 + x_2$ bằng:", r"$\frac{7}{2}$", [r"$-\frac{7}{2}$", r"$\frac{3}{2}$", r"$7$"], r"💡 **HD:** Theo Vi-ét: $S = -\frac{b}{a}$.")

        self.build_q(r"Giả sử phương trình $x^2 - 4x + 1 = 0$ có 2 nghiệm dương $x_1, x_2$. Giá trị của biểu thức $x_1^2 + x_2^2$ là:", "14", ["16", "18", "12"], r"💡 **HD:** $x_1^2 + x_2^2 = S^2 - 2P = 4^2 - 2(1) = 14$.")

        self.build_q(r"Hai vòi nước cùng chảy vào 1 bể cạn thì 6 giờ đầy bể. Nếu vòi 1 chảy một mình 10 giờ đầy bể, thì vòi 2 chảy một mình đầy bể trong bao lâu?", "15 giờ", ["12 giờ", "16 giờ", "4 giờ"], r"💡 **HD:** 1 giờ vòi 2 chảy: $1/6 - 1/10 = 1/15$ bể.")

        self.build_q(r"Số nghiệm của phương trình $x^4 - 3x^2 - 4 = 0$ là:", "2 nghiệm", ["4 nghiệm", "1 nghiệm", "Vô nghiệm"], r"💡 **HD:** Đặt $t = x^2 (t \ge 0) \Rightarrow t=4$ (nhận) $\Rightarrow x = \pm 2$.")

        # --- CHỦ ĐỀ 3: HÌNH HỌC (12 Câu) ---
        c17_1 = random.choice([3, 6, 9]); c17_2 = int(c17_1 * 4/3)
        huyen17 = int(math.sqrt(c17_1**2 + c17_2**2))
        self.build_q(r"Dựa vào kích thước $\Delta ABC$ vuông tại $A$ trên hình vẽ, độ dài cạnh huyền $BC$ là:", str(huyen17) + " cm", [str(c17_1+c17_2) + " cm", str(huyen17**2) + " cm", str(huyen17+1) + " cm"], r"💡 **HD:** Định lý Pytago: $BC = \sqrt{AB^2 + AC^2}$.", draw_right_triangle(c17_1, c17_2))

        self.build_q(r"Trong tam giác $ABC$ vuông tại $A$, tỉ số $\frac{AB}{BC}$ là tỉ số lượng giác nào của $\widehat{C}$?", r"$\sin C$", [r"$\cos C$", r"$\tan C$", r"$\cot C$"], r"💡 **HD:** $\sin$ = Đối / Huyền.")

        self.build_q(r"Cho tam giác vuông có 2 hình chiếu của 2 cạnh góc vuông lên cạnh huyền là 4cm và 9cm. Độ dài đường cao ứng với cạnh huyền là:", "6 cm", ["13 cm", "36 cm", "5 cm"], r"💡 **HD:** $h^2 = b' \cdot c' = 4 \times 9 = 36 \Rightarrow h = 6$.")

        self.build_q(r"Cho đường tròn $(O)$ bán kính 5cm. Khoảng cách từ tâm $O$ đến dây $AB$ bằng 3cm. Độ dài dây $AB$ là:", "8 cm", ["4 cm", "10 cm", "6 cm"], r"💡 **HD:** Pytago: $(AB/2)^2 = 5^2 - 3^2 = 16 \Rightarrow AB = 8$.")

        self.build_q(r"Quan sát hình vẽ, dây cung chung của hai đường tròn cắt nhau có tính chất gì?", "Vuông góc với đường nối tâm", ["Song song với đường nối tâm", "Đi qua tâm của cả hai đường tròn", "Bằng tổng 2 bán kính"], r"💡 **HD:** Đường nối tâm là đường trung trực của dây chung.", draw_intersecting_circles())

        self.build_q(r"Tứ giác $ABCD$ nội tiếp. Biết $\widehat{A} = 70^\circ, \widehat{B} = 100^\circ$. Số đo $\widehat{C}$ là:", r"$110^\circ$", [r"$80^\circ$", r"$70^\circ$", r"$100^\circ$"], r"💡 **HD:** Tổng 2 góc đối diện $= 180^\circ \Rightarrow \widehat{C} = 180^\circ - 70^\circ = 110^\circ$.")

        self.build_q(r"Tam giác $ABC$ nội tiếp đường tròn $(O)$ có cạnh $BC$ là đường kính. Khẳng định ĐÚNG là:", r"$\Delta ABC$ vuông tại $A$", [r"$\Delta ABC$ đều", r"$\Delta ABC$ cân tại $A$", r"$\widehat{A} = 60^\circ$"], r"💡 **HD:** Góc nội tiếp chắn nửa đường tròn là góc vuông.")

        self.build_q(r"Diện tích hình quạt tròn bán kính $R=6cm$, góc ở tâm $60^\circ$ là:", r"$6\pi$ cm$^2$", [r"$12\pi$ cm$^2$", r"$36\pi$ cm$^2$", r"$2\pi$ cm$^2$"], r"💡 **HD:** $S = \frac{\pi R^2 n}{360} = 6\pi$.")

        self.build_q(r"Độ dài cung $90^\circ$ của đường tròn bán kính 4cm là:", r"$2\pi$ cm", [r"$4\pi$ cm", r"$8\pi$ cm", r"$\pi$ cm"], r"💡 **HD:** $l = \frac{\pi R n}{180} = 2\pi$.")

        self.build_q(r"Hình nón có bán kính đáy $r=3$, chiều cao $h=4$. Thể tích là:", r"$12\pi$", [r"$36\pi$", r"$15\pi$", r"$9\pi$"], r"💡 **HD:** $V = \frac{1}{3}\pi r^2 h = 12\pi$.")

        self.build_q(r"Nếu tăng bán kính mặt cầu lên 2 lần thì diện tích mặt cầu tăng lên mấy lần?", "4 lần", ["2 lần", "8 lần", "16 lần"], r"💡 **HD:** Diện tích tỷ lệ với bình phương bán kính.")

        self.build_q(r"Một lon sữa bò hình trụ có bán kính đáy 4cm, cao 10cm. Thể tích lon sữa là:", r"$160\pi$ cm$^3$", [r"$40\pi$ cm$^3$", r"$80\pi$ cm$^3$", r"$320\pi$ cm$^3$"], r"💡 **HD:** $V = \pi r^2 h = 160\pi$.")

        # --- CHỦ ĐỀ 4: XÁC SUẤT THỐNG KÊ (6 Câu) ---
        self.build_q(r"Dựa vào Biểu đồ phổ điểm, tổng tỉ lệ học sinh đạt điểm từ 7 trở lên (Nhóm [7;8), [8;9), [9;10]) là:", "65%", ["40%", "75%", "50%"], r"💡 **HD:** Cộng tỉ lệ 3 cột cuối: $40\% + 15\% + 10\% = 65\%$.", draw_histogram())

        self.build_q(r"Dựa vào biểu đồ phân loại học lực, nhóm học sinh nào chiếm đa số?", "Khá (45%)", ["Giỏi (25%)", "Trung bình (20%)", "Yếu (10%)"], r"💡 **HD:** Khá chiếm 45%.", draw_pie_chart())

        self.build_q(r"Gieo 1 con xúc xắc cân đối. Xác suất để được mặt có số chấm là số nguyên tố là:", r"$\frac{1}{2}$", [r"$\frac{1}{3}$", r"$\frac{1}{6}$", r"$\frac{2}{3}$"], r"💡 **HD:** Các số nguyên tố: 2, 3, 5 (3 kết quả) $\Rightarrow P = 3/6 = 1/2$.")

        self.build_q(r"Rút ngẫu nhiên 1 lá bài từ bộ bài tú lơ khơ 52 lá. Số phần tử của không gian mẫu là:", "52", ["13", "4", "26"], r"💡 **HD:** Không gian mẫu có 52 lá.")

        self.build_q(r"Trong 20 ngày đi học, Nam đi muộn 2 ngày. Xác suất thực nghiệm của biến cố 'Nam đi học đúng giờ' là:", r"$\frac{9}{10}$", [r"$\frac{1}{10}$", r"$\frac{1}{20}$", r"$90$"], r"💡 **HD:** $(20-2)/20 = 9/10$.")

        self.build_q(r"Một hộp có thẻ đánh số từ 1 đến 10. Rút 1 thẻ, xác suất rút được thẻ là số chia hết cho 3 là:", r"$\frac{3}{10}$", [r"$\frac{1}{3}$", r"$\frac{4}{10}$", r"$\frac{1}{10}$"], r"💡 **HD:** Các số chia hết cho 3: 3, 6, 9 $\Rightarrow P = 3/10$.")
        
        # --- CHỦ ĐỀ 5: ĐẠI VẬN DỤNG CAO (2 CÂU CHỐT ĐIỂM 10) ---
        # CÂU 39: Giải phương trình vô tỷ bằng phương pháp Đánh giá (Bunhiacopxki)
        m39 = random.randint(2, 5)
        ans_39 = r"$x = " + str(m39) + r"$"
        dis39_1 = r"$x = " + str(m39-1) + r"$"
        dis39_2 = r"$x = " + str(m39+1) + r"$"
        hint_39 = r"💡 **HD (Câu chốt 9.5 điểm):** Phương pháp Đánh giá.<br>Áp dụng BĐT Bunhiacopxki cho Vế Trái (VT):<br> $VT^2 = (1 \cdot \sqrt{x - " + str(m39-1) + r"} + 1 \cdot \sqrt{" + str(m39+1) + r" - x})^2 \le (1^2+1^2)(x - " + str(m39-1) + r" + " + str(m39+1) + r" - x) = 4 \Rightarrow VT \le 2$.<br>Biến đổi Vế Phải (VP): $VP = (x - " + str(m39) + r")^2 + 2 \ge 2$.<br>Để $VT = VP$ thì cả hai vế phải bằng 2 $\Rightarrow (x - " + str(m39) + r")^2 = 0 \Leftrightarrow x = " + str(m39) + r"$. Thử lại thấy thỏa mãn."
        self.build_q(r"Giải phương trình vô tỷ: $\sqrt{x - " + str(m39-1) + r"} + \sqrt{" + str(m39+1) + r" - x} = x^2 - " + str(2*m39) + r"x + " + str(m39**2 + 2) + r"$. Nghiệm của phương trình là:", ans_39, [dis39_1, dis39_2, "Vô nghiệm"], hint_39)
        
        # CÂU 40: Tìm GTLN bằng BĐT Bunhiacopxki (Toán HSG)
        c40 = random.choice([3, 12, 27]) 
        if c40 == 3: ans40 = r"$3\sqrt{2}$"; dis40 = [r"$2\sqrt{3}$", r"$6$", r"$3$"]
        elif c40 == 12: ans40 = r"$6\sqrt{2}$"; dis40 = [r"$4\sqrt{3}$", r"$12$", r"$6$"]
        else: ans40 = r"$9\sqrt{2}$"; dis40 = [r"$6\sqrt{3}$", r"$18$", r"$9$"]
        hint_40 = r"💡 **HD (Câu chốt 10 điểm):** Áp dụng BĐT Bunhiacopxki cho 3 bộ số $(1, 1, 1)$ và $(\sqrt{x+y}, \sqrt{y+z}, \sqrt{z+x})$ ta có:<br> $P^2 \le (1^2+1^2+1^2)[(x+y) + (y+z) + (z+x)] = 3 \cdot 2(x+y+z) = 6 \cdot " + str(c40) + r" = " + str(6*c40) + r"$.<br>Suy ra $P \le \sqrt{" + str(6*c40) + r"}$. Do đó $P_{max} = " + ans40 + r"$. Dấu '=' xảy ra khi $x=y=z=" + str(c40//3) + r"$. Tôn vinh vẻ đẹp của Toán học!"
        self.build_q(r"Cho các số thực dương $x, y, z$ thỏa mãn điều kiện $x+y+z = " + str(c40) + r"$. Tìm giá trị lớn nhất của biểu thức $P = \sqrt{x+y} + \sqrt{y+z} + \sqrt{z+x}$.", ans40, dis40, hint_40)

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
        tab_mand, tab_ai = st.tabs(["🔥 Bài tập Bắt buộc", "🤖 Luyện đề Đa dạng"])
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
                        # CHUẨN HÓA ĐÁNH SỐ THỨ TỰ CÂU HỎI
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                        if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                        ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                        selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                        st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                        st.markdown("---")
                    
                    if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                        correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                        score = (correct / len(mand_exam_data)) * 10
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
                        # CHUẨN HÓA ĐÁNH SỐ THỨ TỰ
                        st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
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
            st.title("Luyện Tập Đề Thi (40 Câu Chuẩn Ma Trận VN)")
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
                # HIỂN THỊ ĐIỂM SỐ KHI LÀM BÀI XONG
                if st.session_state.is_submitted:
                    correct_ans = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    score_ai = (correct_ans / len(st.session_state.exam_data)) * 10
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM CỦA BẠN: {score_ai:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    st.markdown("---")

                for q in st.session_state.exam_data:
                    # CHUẨN HÓA ĐÁNH SỐ THỨ TỰ
                    st.markdown(f"**Câu {q['id']}:** {q['question']}", unsafe_allow_html=True)
                    if q['image']: st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                    disabled = st.session_state.is_submitted
                    ans_val = st.session_state.user_answers[q['id']]
                    selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    if not disabled: st.session_state.user_answers[q['id']] = selected
                    
                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.success("✅ Đúng")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
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
                    exam_questions = json.loads(exam_row['questions_json'])
                    df_class_students = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{selected_rep_class}'", conn)
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng HS", len(df_class_students))
                    c2.metric("Đã nộp", len(df_submitted))
                    c3.metric("Chưa nộp", len(df_class_students) - len(df_submitted))
                    
                    t1, t2, t3 = st.tabs(["✅ Bảng Điểm", "❌ HS Chưa Làm Bài", "📈 Thống kê Độ Khó Câu Hỏi"])
                    with t1:
                        if not df_submitted.empty: st.dataframe(df_submitted[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Nộp lúc'}), use_container_width=True)
                        else: st.info("Chưa có ai nộp.")
                    with t2:
                        submitted_users = df_submitted['username'].tolist()
                        df_missing = df_class_students[~df_class_students['username'].isin(submitted_users)]
                        if not df_missing.empty: st.dataframe(df_missing[['username', 'fullname']], use_container_width=True)
                        else: st.success("100% HS đã nộp bài.")
                    with t3:
                        if not df_submitted.empty:
                            wrong_stats = {str(q['id']): {'text': q['question'], 'wrong_count': 0} for q in exam_questions}
                            for _, row in df_submitted.iterrows():
                                ans_dict = json.loads(row['user_answers_json'])
                                for q in exam_questions:
                                    q_id = str(q['id'])
                                    if ans_dict.get(q_id) != q['answer']: wrong_stats[q_id]['wrong_count'] += 1
                            stats_list = [{'Câu': k, 'Nội dung': v['text'], 'Số HS làm sai': v['wrong_count']} for k, v in wrong_stats.items()]
                            df_stats = pd.DataFrame(stats_list).sort_values(by='Số HS làm sai', ascending=False)
                            st.markdown("**🚨 TOP 5 câu sai nhiều nhất:**")
                            st.dataframe(df_stats.head(5), use_container_width=True)
                            st.markdown("**Chi tiết:**")
                            st.dataframe(df_stats, use_container_width=True)
                        else: st.info("Cần có HS nộp bài để AI phân tích.")
            
        # --- TAB 4: NẠP DỮ LIỆU & GIAO BÀI ---
        with tab_system:
            st.subheader("📤 Giao bài AI (Theo Lớp)")
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
