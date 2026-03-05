import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # Bảng Kết quả thi
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tạo tài khoản mặc định nếu chưa có
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs2', '123', 'student')")
    conn.commit()
    conn.close()

# ==========================================
# PHẦN 2: HELPER VẼ HÌNH ĐỘNG (BASE64)
# ==========================================
def generate_histogram_base64(freqs):
    fig, ax = plt.subplots(figsize=(6, 3))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    total = sum(freqs)
    percents = [f / total * 100 for f in freqs]
    
    ax.bar(bins, percents, color='#f28e2b', edgecolor='black')
    ax.set_ylabel('Tần số tương đối (%)')
    ax.set_xlabel('Chiều cao (cm)')
    
    for i, v in enumerate(percents):
        ax.text(i, v + 2, f"{round(v)}%", ha='center', fontweight='bold')
    
    ax.set_ylim(0, max(percents) + 15)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ==========================================
# PHẦN 3: THUẬT TOÁN TẠO 40 CÂU HỎI THEO MA TRẬN
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def build_q(self, q_id, text, correct, distractors, hint, img_b64=None):
        options = [correct] + distractors
        random.shuffle(options)
        self.exam.append({
            "id": q_id,
            "question": text,
            "options": options,
            "answer": correct,
            "hint": hint,
            "image": img_b64
        })

    def generate_all(self):
        # --- CHỦ ĐỀ 1: CĂN THỨC (6 CÂU) ---
        # Câu 1 (NB): ĐKXĐ của căn
        a1 = random.randint(1, 9)
        self.build_q(1, f"Điều kiện xác định của biểu thức $\sqrt{{x-{a1}}}$ là", 
                     f"$x \ge {a1}$", [f"$x > {a1}$", f"$x \le {a1}$", f"$x < {a1}$"], 
                     "Biểu thức trong căn phải $\ge 0$.")
        
        # Câu 2 (NB): Căn bậc hai của một số chính phương
        a2 = random.choice([4, 9, 16, 25, 36, 49, 64, 81])
        ans2 = int(math.sqrt(a2))
        self.build_q(2, f"Căn bậc hai của ${a2}$ là", 
                     f"${ans2}$ và -${ans2}$", [f"${ans2}$", f"-${ans2}$", f"${a2**2}$ và -${a2**2}$"], 
                     "Số dương có hai căn bậc hai là hai số đối nhau.")
        
        # Câu 3 (TH): Rút gọn căn chứa bình phương
        a3 = random.randint(2, 5)
        b3 = random.randint(1, 4)
        self.build_q(3, f"Với $x < {a3}$, biểu thức $\sqrt{{({a3}-x)^2}} + x - {b3}$ bằng", 
                     f"${a3-b3}$", [f"$-{a3-b3}$", f"$2x - {a3+b3}$", f"${a3+b3} - 2x$"], 
                     "Sử dụng hằng đẳng thức $\sqrt{A^2} = |A|$. Do $x < a$ nên $|a-x| = a-x$.")

        # Câu 4 (NB): Căn thức chứa biến
        b4 = random.choice([4, 9, 25])
        ans4 = int(math.sqrt(b4))
        self.build_q(4, f"Cho $b>0$, khẳng định nào dưới đây đúng?", 
                     f"$\sqrt{{{b4}b^2}} = {ans4}b$", [f"$\sqrt{{{b4}b^2}} = -{ans4}b$", f"$\sqrt{{{b4}b^2}} = {b4}b$", f"$\sqrt{{{b4}b^2}} = {ans4}b^2$"], 
                     "$\sqrt{A^2 B} = |A|\sqrt{B}$. Vì $b>0$ nên $|b|=b$.")

        # Câu 5 (TH): Rút gọn biểu thức căn chứa hệ số
        self.build_q(5, f"Với $a \ge 0$, biểu thức $\sqrt{{9a}} + \sqrt{{16a}} - \sqrt{{64a}}$ bằng", 
                     f"$-\sqrt{{a}}$", [f"$15\sqrt{{a}}$", f"$a$", f"$-a$"], 
                     "Phân tích: $3\sqrt{a} + 4\sqrt{a} - 8\sqrt{a} = -\sqrt{a}$.")

        # Câu 6 (VD/VDC): Biểu thức chứa chữ (Phân loại)
        self.build_q(6, f"Với $x>0, y>0, x \\ne y$, biểu thức $P = \dfrac{{x\sqrt{{y}} + y\sqrt{{x}}}}{{\sqrt{{xy}}}} : \dfrac{{1}}{{\sqrt{{x}} - \sqrt{{y}}}}$ bằng", 
                     f"$x - y$", [f"$y - x$", f"$\sqrt{{x}} - \sqrt{{y}}$", f"$\sqrt{{y}} - \sqrt{{x}}$"], 
                     "Rút gọn phân thức thứ nhất được $(\sqrt{x}+\sqrt{y})$, nhân nghịch đảo phân thức thứ hai và dùng HĐT $a^2-b^2$.")

        # --- CHỦ ĐỀ 2: HÀM SỐ Y=AX^2 VÀ ĐỒ THỊ (3 CÂU) ---
        # Câu 7 (NB)
        self.build_q(7, f"Đồ thị hàm số $y=ax^2 (a \\ne 0)$ có bao nhiêu trục đối xứng?", 
                     "1", ["0", "2", "3", "Vô số"], 
                     "Parabol $y=ax^2$ luôn nhận trục tung (Oy) làm trục đối xứng duy nhất.")
        
        # Câu 8 (TH): Tìm hệ số a
        x8 = random.choice([2, 3])
        y8 = random.choice([4, 6, 8, 10, 12])
        self.build_q(8, f"Đồ thị hàm số $y=ax^2 (a \\ne 0)$ đi qua điểm $({x8}; {y8})$. Giá trị của $a$ là", 
                     f"$\dfrac{{{y8}}}{{{x8**2}}}$", [f"$\dfrac{{{x8**2}}}{{{y8}}}$", f"${y8*x8**2}$", f"$\dfrac{{{y8}}}{{{x8}}}$"], 
                     "Thay tọa độ $x, y$ vào hàm số để tìm $a$.")

        # Câu 9 (VD): Chu vi tam giác trên parabol
        a9 = random.choice([2, 3])
        self.build_q(9, f"Gọi $A, B$ là các điểm thuộc đồ thị hàm số $y={a9}x^2$ lần lượt có hoành độ $-1$ và $1$. Chu vi tam giác $OAB$ là", 
                     f"$2\sqrt{{{1+a9**2}}} + 2$ cm.", [f"$\sqrt{{{1+a9**2}}} + 2$ cm.", f"$2\sqrt{{{1+a9**2}}} + 1$ cm.", f"$2\sqrt{{{1+a9**2}}}$ cm."], 
                     f"Tính tọa độ $A(-1, {a9}), B(1, {a9})$. Tính $OA, OB, AB$ bằng công thức khoảng cách.")

        # --- CHỦ ĐỀ 3: PHƯƠNG TRÌNH VÀ HỆ (8 CÂU) ---
        # Câu 10 (TH): Phương trình quy về bậc nhất ẩn mẫu
        x10 = random.randint(1, 3)
        self.build_q(10, f"Số nghiệm của phương trình $\dfrac{{-x+{x10}}}{{x-{x10}}} + \dfrac{{2x+6}}{{x}} = 0$ là", 
                     "1", ["0", "2", "3"], 
                     "Rút gọn phân thức đầu thành $-1$ (với đk $x \\ne {x10}$), giải phương trình $-1 + (2x+6)/x = 0$.")

        # Câu 11 (TH): Phương trình tích
        c11 = random.randint(2, 4)
        self.build_q(11, f"Tổng các nghiệm của phương trình $({c11}x - 8)(x - 2) = 0$ là", 
                     f"${8//c11 + 2}$", [f"${8//c11 - 2}$", f"${8//c11 * 2}$", f"${abs(8//c11 - 2)}$"], 
                     "Tìm từng nghiệm $x$ rồi cộng lại.")

        # Câu 12 (NB): Nhận biết hệ PT bậc nhất 2 ẩn
        self.build_q(12, f"Hệ phương trình nào dưới đây KHÔNG là hệ hai phương trình bậc nhất hai ẩn?", 
                     f"$\begin{{cases}} \sqrt{{x}} + y = 0 \\\\ 2x + y = 1 \end{{cases}}$", 
                     [f"$\begin{{cases}} x - 2y = 3 \\\\ x - 4y = 1 \end{{cases}}$", f"$\begin{{cases}} x + 2y = 2 \\\\ x - y = 1 \end{{cases}}$", f"$\begin{{cases}} x - y = 0 \\\\ 2x + 3y = 1 \end{{cases}}$"], 
                     "Hệ PT bậc nhất hai ẩn chỉ chứa bậc 1 của $x$ và $y$, không chứa $\sqrt{x}$.")

        # Câu 13 (NB): Phương trình bậc nhất hai ẩn
        self.build_q(13, f"Phương trình nào dưới đây là phương trình bậc nhất hai ẩn?", 
                     f"$3x + 2y = 8$", [f"$x + xy = 0$", f"$x + 3y^2 = 3$", f"$3x^2 - 2y = 5$"], 
                     "Dạng chuẩn: $ax+by=c$ với $a, b$ không đồng thời bằng 0.")

        # Câu 14 (TH): Giải hệ phương trình
        self.build_q(14, f"Hệ phương trình $\begin{{cases}} x + y = 10 \\\\ 2x - y = -1 \end{{cases}}$ nhận cặp số $(x_0; y_0)$ là nghiệm. Giá trị $x_0$ là", 
                     "3", ["-3", "7", "-7"], 
                     "Cộng vế theo vế hai phương trình để triệt tiêu $y$.")

        # Câu 15 (NB): Giải phương trình bậc 2 cơ bản
        c15 = random.choice([3, 8])
        self.build_q(15, f"Gọi $x_1, x_2$ với $x_1 < x_2$ là hai nghiệm của phương trình $x(x+2) = {c15}$. Giá trị $x_1$ là", 
                     f"{-3 if c15==3 else -4}", ["1", "3", "2", "-1", "-2"][:3], 
                     "Khai triển thành $x^2 + 2x - C = 0$ và giải PT bậc hai, lấy nghiệm nhỏ hơn.")

        # Câu 16 (VD): Viète
        self.build_q(16, f"Cho phương trình $x^2 - mx - 2 = 0$ (với $m>0$) có 2 nghiệm $x_1, x_2$ thỏa mãn $x_1 - 2x_2 = 5$. Biết $m$ có dạng phân số tối giản $\dfrac{{a}}{{b}}$, hiệu $a^2 - b^2$ bằng", 
                     "45", ["49", "53", "4"], 
                     "Kết hợp Hệ thức Viète $x_1+x_2=m, x_1 x_2=-2$ và đk $x_1 - 2x_2 = 5$ để giải ra $m$.")

        # Câu 17 (VDC): Bài toán thực tế Max/Min Hệ PT
        self.build_q(17, f"Một công ty bán 800 máy tính bảng/tuần giá 8 triệu/chiếc. Cứ giảm 200.000đ thì bán thêm 80 chiếc. Để doanh thu cao nhất (M tỉ đồng), bán với giá m triệu/chiếc. Tổng $M + m$ bằng", 
                     "13", ["11", "15", "17"], 
                     "Lập hàm doanh thu theo biến giảm giá $x$, tìm đỉnh Parabol.")

        # --- CHỦ ĐỀ 4: BẤT PHƯƠNG TRÌNH (3 CÂU) ---
        # Câu 18 (NB): Tính chất BĐT
        self.build_q(18, f"Với $a < b$, kết luận nào dưới đây đúng?", 
                     f"$a - 3 < b - 3$", [f"$a + 3 > b + 3$", f"$-3a < -3b$", f"$3a > 3b$"], 
                     "Cộng/trừ cùng một số vào 2 vế của BĐT thì chiều BĐT không đổi.")

        # Câu 19 (TH): Giải BPT
        self.build_q(19, f"Nghiệm của bất phương trình $3(x+4) - 4(x+2) \le 0$ là", 
                     f"$x \ge 4$", [f"$x \le 4$", f"$x \ge -4$", f"$x \le -4$"], 
                     "Nhân phá ngoặc và chuyển vế.")

        # Câu 20 (VDC): Max/Min biểu thức đại số (Dựa theo cấu trúc BPT VDC)
        self.build_q(20, f"Tìm giá trị nhỏ nhất của biểu thức $A = x - 2\sqrt{{x-1}} + 5$ với $x \ge 1$.", 
                     "4", ["5", "3", "6"], 
                     "Biến đổi $A = (\sqrt{x-1} - 1)^2 + 4 \ge 4$.")

        # --- CHỦ ĐỀ 5: HỆ THỨC LƯỢNG (5 CÂU) ---
        # Câu 21 (NB)
        self.build_q(21, f"Cho tam giác $MNP$ vuông tại $P$. Khẳng định nào đúng?", 
                     f"$\cos M = \dfrac{{MP}}{{MN}}$", [f"$\cos M = \dfrac{{NP}}{{MN}}$", f"$\cos M = \dfrac{{NP}}{{MP}}$", f"$\cos M = \dfrac{{MP}}{{NP}}$"], 
                     "Cos = Kề / Huyền.")

        # Câu 22 (NB)
        self.build_q(22, f"Cho tam giác $DEF$ vuông tại $D$. Khẳng định nào đúng?", 
                     f"$\tan E = \cot F$", [f"$\tan E = \sin F$", f"$\tan E = \cos F$", f"$\tan E = \tan F$"], 
                     "Hai góc nhọn phụ nhau thì tan góc này bằng cot góc kia.")

        # Câu 23 (TH)
        self.build_q(23, f"Cho tam giác $ABC$ vuông tại $A$, có $\widehat{{ABC}} = 60^\circ$ và $AB=4$ cm. Độ dài cạnh $BC$ là", 
                     "8 cm", ["$2\sqrt{3}$ cm", "$3\sqrt{3}$ cm", "2 cm"], 
                     "Sử dụng $\cos B = \dfrac{AB}{BC} \Rightarrow BC = \dfrac{AB}{\cos 60^\circ}$.")

        # Câu 24 (TH)
        self.build_q(24, f"Độ dài cạnh của tam giác đều nội tiếp đường tròn bán kính $R$ là", 
                     f"$R\sqrt{{3}}$", [f"$2R$", f"$\dfrac{{R\sqrt{{3}}}}{{2}}$", f"$\dfrac{{3R}}{{2}}$"], 
                     "Sử dụng định lý sin trong tam giác: $a / \sin(60^\circ) = 2R$.")

        # Câu 25 (VD): Thực tế hệ thức lượng
        deg = random.choice([25, 26, 30])
        dist = 8
        ans25 = round(dist * math.sin(math.radians(deg)), 1)
        self.build_q(25, f"Khi cất cánh, đường bay của máy bay tạo với mặt ngang góc ${deg}^\circ$. Sau khi bay được quãng đường {dist}km thì độ cao (làm tròn đến chữ số thập phân thứ nhất) là", 
                     f"{ans25} km", [f"{ans25+0.2} km", f"{ans25-0.3} km", f"{round(dist*math.cos(math.radians(deg)),1)} km"], 
                     "Độ cao $h = \text{quãng đường} \times \sin(\alpha)$.")

        # --- CHỦ ĐỀ 6: ĐƯỜNG TRÒN (6 CÂU) ---
        # Câu 26 (NB)
        self.build_q(26, f"Số điểm chung của hai đường tròn cắt nhau là", 
                     "2", ["0", "1", "3"], 
                     "Hai đường tròn cắt nhau giao tại đúng 2 điểm phân biệt.")

        # Câu 27 (NB)
        self.build_q(27, f"Từ điểm $A$ nằm ngoài đường tròn $(O)$, kẻ được tối đa bao nhiêu tiếp tuyến tới $(O)$?", 
                     "2", ["0", "1", "3"], 
                     "Từ một điểm ngoài đường tròn luôn kẻ được đúng 2 tiếp tuyến.")

        # Câu 28 (TH)
        ang = random.choice([70, 80])
        self.build_q(28, f"Trên $(O)$ lấy hai điểm $A, B$ sao cho $\widehat{{AOB}} = {ang}^\circ$. Vẽ dây $AM \perp OB$. Số đo cung nhỏ $AM$ bằng", 
                     f"{ang * 2}^\circ", [f"{ang}^\circ", f"{180 - ang}^\circ", f"{ang + 20}^\circ"], 
                     "Đường kính vuông góc với dây thì đi qua điểm chính giữa của cung.")

        # Câu 29 (TH)
        self.build_q(29, f"Đường tròn nội tiếp hình vuông cạnh $2a$ có bán kính là", 
                     f"$a$", [f"$a\sqrt{{2}}$", f"$2a\sqrt{{2}}$", f"$a\sqrt{{3}}$"], 
                     "Bán kính đường tròn nội tiếp hình vuông bằng một nửa độ dài cạnh hình vuông.")

        # Câu 30 (TH)
        self.build_q(30, f"Đường tròn ngoại tiếp hình chữ nhật có kích thước $6$ cm và $8$ cm có bán kính là", 
                     "5 cm", ["7 cm", "10 cm", "14 cm"], 
                     "Đường kính bằng độ dài đường chéo (Định lý Pytago: $\sqrt{6^2+8^2} = 10$).")

        # Câu 31 (VDC): Trang trí tường cung tròn 120 độ
        self.build_q(31, f"Người ta muốn trang trí bức tường với họa tiết là phần hình tròn bán kính 1,5m, cấu tạo bởi 2 đoạn thẳng tạo góc $120^\circ$ và một cung tròn. Độ dài dây đèn dùng trang trí (làm tròn chữ số thập phân thứ nhất) khoảng:", 
                     "9.3 m", ["6.2 m", "7.7 m", "10.7 m"], 
                     "Tính độ dài cung lớn và 2 dây cung căng cung $120^\circ$.")

        # --- CHỦ ĐỀ 7: HÌNH KHỐI (3 CÂU) ---
        # Câu 32 (NB)
        self.build_q(32, f"Thể tích của hình cầu bán kính $a$ là", 
                     f"$V = \dfrac{{4}}{{3}}\pi a^3$", [f"$V = \dfrac{{1}}{{3}}\pi a^3$", f"$V = 4\pi a^2$", f"$V = \pi a^2$"], 
                     "Công thức chuẩn sách giáo khoa.")

        # Câu 33 (TH)
        self.build_q(33, f"Một hình nón có diện tích xung quanh $S_{{xq}} = 9\pi$ cm$^2$ và đường sinh $l=3$ cm. Bán kính đáy là", 
                     "3 cm", ["1 cm", "2 cm", "4 cm"], 
                     "$S_{xq} = \pi r l \Rightarrow r = \dfrac{S_{xq}}{\pi l}$.")

        # Câu 34 (VD): Viên gạch đất sét 4 lỗ
        self.build_q(34, f"Một viên gạch hình hộp CN có đáy vuông cạnh 8cm, cao 22cm. Có 4 lỗ hình trụ xuyên qua đáy đk 2.5cm. Thể tích đất sét (làm tròn đv cm$^3$) là:", 
                     "976 cm$^3$", ["1300 cm$^3$", "432 cm$^3$", "1408 cm$^3$"], 
                     "V = Thể tích khối hộp - 4 * Thể tích khối trụ.")

        # --- CHỦ ĐỀ 8: THỐNG KÊ - XÁC SUẤT (6 CÂU) ---
        # Câu 35 (NB): Bảng tần số
        self.build_q(35, f"Cho bảng chiều cao (cm): 140 có 4 bạn, 141 có 5 bạn, 145 có 3 bạn. Có bao nhiêu bạn cao 140 cm?", 
                     "4 bạn", ["3 bạn", "5 bạn", "7 bạn"], 
                     "Nhìn trực tiếp vào tần số tương ứng trong bảng.")

        # Câu 36 (TH): Tần số tương đối
        self.build_q(36, f"Một bảng dữ liệu có tổng số quan sát $N=30$, một giá trị xuất hiện 6 lần. Tần số tương đối của giá trị đó là", 
                     "20%", ["25%", "30%", "15%"], 
                     "Tần số tương đối $f = \dfrac{n}{N} \cdot 100\% = \dfrac{6}{30} \cdot 100\%$.")

        # Câu 37 (TH): Biểu đồ ghép nhóm
        freqs_37 = [random.randint(5, 15) for _ in range(5)]
        freqs_37 = [9, 33, 31, 17, 10] # Khớp với đề mẫu
        img37 = generate_histogram_base64(freqs_37)
        self.build_q(37, f"Quan sát biểu đồ tần số tương đối ghép nhóm dưới đây. Có tổng 100 học sinh. Số học sinh có chiều cao từ 150 cm đến dưới 160 cm là", 
                     f"{freqs_37[1]} học sinh", [f"{freqs_37[0]} học sinh", f"{freqs_37[2]} học sinh", f"{freqs_37[3]} học sinh"], 
                     "Đọc % tại cột [150; 160) trên biểu đồ và nhân với 100.", img_b64=img37)

        # Câu 38 (NB): Không gian mẫu
        self.build_q(38, f"Xét phép thử: 'Viết ngẫu nhiên một số tự nhiên chẵn có 1 chữ số'. Tập hợp nào là không gian mẫu?", 
                     "$\Omega = \{0; 2; 4; 6; 8\}$", ["$\Omega = \{2; 4; 6; 8\}$", "$\Omega = \{1; 3; 5; 7; 9\}$", "$\Omega = \{0; 2; 4; 6\}$"], 
                     "Số tự nhiên chẵn 1 chữ số bao gồm cả số 0.")

        # Câu 39 (VD): Tính xác suất 2 xúc xắc
        self.build_q(39, f"Bạn Giang gieo một con xúc xắc cân đối 2 lần liên tiếp. Xác suất 'Lần 2 xuất hiện mặt 4 chấm' là", 
                     "$\dfrac{1}{6}$", ["$\dfrac{1}{36}$", "$\dfrac{2}{3}$", "$\dfrac{1}{5}$"], 
                     "Kết quả gieo lần 2 độc lập với lần 1, xác suất ra 1 mặt cụ thể luôn là 1/6.")

        # Câu 40 (VDC): Tính xác suất nâng cao
        self.build_q(40, f"Ba bạn Mai, An, Phương viết ngẫu nhiên một số tự nhiên từ 1 đến 5. Xác suất tổng ba số nhỏ hơn 13 là", 
                     "$\dfrac{21}{25}$", ["$\dfrac{24}{25}$", "$\dfrac{23}{25}$", "$\dfrac{1}{25}$"], 
                     "Tổng số trường hợp = $5 \times 5 \times 5 = 125$. Tính phần bù (Tổng $\ge 13$) gồm các bộ (5,5,5), (5,5,4)...")
        
        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN & LUỒNG XỬ LÝ
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống Ôn Thi Toán Tuyên Quang", layout="wide")
    init_db()
    
    # State Management
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    # Màn hình Đăng nhập
    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center;'>HỆ THỐNG KIỂM TRA ĐÁNH GIÁ NĂNG LỰC CẤP TỈNH</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("💡 **Gợi ý tài khoản demo:**\\n- Admin: `admin` / `admin123`\\n- Học sinh: `hs1` / `123`")
            with st.form("login_form"):
                user = st.text_input("Tên đăng nhập")
                pwd = st.text_input("Mật khẩu", type="password")
                submitted = st.form_submit_button("Đăng nhập")
                if submitted:
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pwd))
                    res = c.fetchone()
                    conn.close()
                    if res:
                        st.session_state.current_user = user
                        st.session_state.role = res[0]
                        st.rerun()
                    else:
                        st.error("Tài khoản hoặc mật khẩu không chính xác!")
        return

    # Sidebar
    with st.sidebar:
        st.success(f"👤 Xin chào: **{st.session_state.current_user}**")
        st.markdown(f"**Vai trò:** {'Quản trị viên' if st.session_state.role == 'admin' else 'Học sinh'}")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()

   # ==========================
    # GIAO DIỆN HỌC SINH
    # ==========================
    if st.session_state.role == 'student':
        st.title("📚 Đề Thi Thử Vào 10 THPT (Toán Chung)")
        st.warning("⏱ Thời gian làm bài: 90 phút. Đề thi gồm 40 câu hỏi trắc nghiệm.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 LÀM ĐỀ MỚI (Sinh bằng AI)", use_container_width=True, type="primary"):
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

        if st.session_state.exam_data:
            st.markdown("---")
            for idx, q in enumerate(st.session_state.exam_data):
                st.markdown(f"**Câu {idx + 1}:** {q['question']}", unsafe_allow_html=True)
                
                # Render Image if exists
                if q['image']:
                    st.markdown(f'<img src="data:image/png;base64,{q["image"]}" alt="chart">', unsafe_allow_html=True)
                
                disabled = st.session_state.is_submitted
                selected = st.radio(
                    "Chọn đáp án:",
                    options=q['options'],
                    index=q['options'].index(st.session_state.user_answers[q['id']]) if st.session_state.user_answers[q['id']] else None,
                    key=f"q_{q['id']}",
                    disabled=disabled,
                    label_visibility="collapsed"
                )
                if not disabled:
                    st.session_state.user_answers[q['id']] = selected

                if st.session_state.is_submitted:
                    if selected == q['answer']:
                        st.markdown("✅ **<span style='color:green;'>Chính xác</span>**", unsafe_allow_html=True)
                    else:
                        st.markdown(f"❌ **<span style='color:red;'>Sai. Đáp án đúng: {q['answer']}</span>**", unsafe_allow_html=True)
                    with st.expander("📖 Xem hướng dẫn"):
                        st.markdown(q['hint'], unsafe_allow_html=True)
                st.markdown("---")

            if not st.session_state.is_submitted:
                if st.button("📤 NỘP BÀI", type="primary", use_container_width=True):
                    # Chấm điểm và lưu DB
                    correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                    total = 40
                    score = (correct / total) * 10
                    
                    conn = sqlite3.connect('exam_db.sqlite')
                    c = conn.cursor()
                    c.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?, ?, ?, ?)", 
                              (st.session_state.current_user, score, correct, total - correct))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.is_submitted = True
                    st.rerun()
            else:
                correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
                score = (correct / 40) * 10
                st.info(f"🏆 **ĐIỂM CỦA BẠN: {score:.2f} / 10** (Đúng {correct}/40 câu)")

    # ==========================
    # GIAO DIỆN ADMIN (ĐÃ NÂNG CẤP)
    # ==========================
    elif st.session_state.role == 'admin':
        st.title("⚙ Bảng Điều Khiển Quản Trị (Admin Dashboard)")
        
        # Tạo các tab để chia bố cục cho gọn gàng
        tab1, tab2 = st.tabs(["📊 Thống kê điểm số", "👤 Quản lý Tài khoản"])
        
        # --- TAB 1: XEM ĐIỂM ---
        with tab1:
            conn = sqlite3.connect('exam_db.sqlite')
            df = pd.read_sql_query("SELECT username as 'Tài khoản', score as 'Điểm số', correct_count as 'Số câu đúng', wrong_count as 'Số câu sai', timestamp as 'Thời gian nộp' FROM results ORDER BY timestamp DESC", conn)
            conn.close()
            
            if not df.empty:
                st.subheader("Kết quả thi của Học sinh")
                st.dataframe(df, use_container_width=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Tổng lượt thi", len(df))
                with c2:
                    st.metric("Điểm trung bình", f"{df['Điểm số'].mean():.2f}")
            else:
                st.info("Chưa có học sinh nào nộp bài.")

        # --- TAB 2: TẠO TÀI KHOẢN MỚI ---
        with tab2:
            st.subheader("Tạo tài khoản mới cho Hệ thống")
            with st.form("create_user_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_username = st.text_input("Tên đăng nhập (viết liền không dấu)")
                with col2:
                    new_password = st.text_input("Mật khẩu")
                with col3:
                    new_role = st.selectbox("Phân quyền", options=["Học sinh (student)", "Quản trị viên (admin)"])
                
                submit_btn = st.form_submit_button("Tạo tài khoản", type="primary")
                
                if submit_btn:
                    if new_username.strip() == "" or new_password.strip() == "":
                        st.warning("Vui lòng điền đầy đủ Tên đăng nhập và Mật khẩu!")
                    else:
                        role_val = "admin" if "admin" in new_role else "student"
                        try:
                            conn = sqlite3.connect('exam_db.sqlite')
                            c = conn.cursor()
                            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_username.strip(), new_password.strip(), role_val))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Đã tạo thành công tài khoản: **{new_username}**")
                        except sqlite3.IntegrityError:
                            st.error(f"❌ Tên đăng nhập '{new_username}' đã tồn tại. Vui lòng chọn tên khác!")
            
            # Hiển thị danh sách tài khoản hiện có
            st.markdown("---")
            st.subheader("Danh sách tài khoản hiện tại")
            conn = sqlite3.connect('exam_db.sqlite')
            df_users = pd.read_sql_query("SELECT username as 'Tài khoản', role as 'Phân quyền' FROM users", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True)

# Lệnh thực thi App (Lùi ra sát lề trái nhất)
if __name__ == "__main__":
    main()
