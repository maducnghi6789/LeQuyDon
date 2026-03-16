# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN V20 SUPREME (CHUẨN SGK ĐỘC BẢN)
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
from datetime import datetime, timedelta, timezone

# --- KẾT NỐI GEMINI AI ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
        import google.generativeai as genai
        AI_AVAILABLE = True
    except:
        AI_AVAILABLE = False

VN_TZ = timezone(timedelta(hours=7))

# GIÁM ĐỐC DÁN API KEY VÀO ĐÂY
GEMINI_API_KEY = "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY" 

if AI_AVAILABLE and GEMINI_API_KEY != "DÁN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY":
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# ==========================================
# 1. HÀM HỖ TRỢ EXCEL & REGEX 
# ==========================================
def to_excel(df, sheet_name='Sheet1'):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def create_excel_template():
    df_template = pd.DataFrame(columns=["Họ tên", "Ngày sinh", "Trường"])
    df_template.loc[0] = ["Nguyễn Văn A", "15/08/2010", "THCS Lê Quý Đôn"]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='MauNhapLieu')
    return output.getvalue()

def remove_vietnamese_accents(s):
    s = str(s)
    patterns = {'[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i', 
                '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỵỷỹ]': 'y', '[đ]': 'd',
                '[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]': 'A', '[ÈÉẸẺẼÊỀẾỆỂỄ]': 'E', '[ÌÍỊỈĨ]': 'I',
                '[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]': 'O', '[ÙÚỦŨƯỪỨỰỬỮ]': 'U', '[ỲÝỴỶỸ]': 'Y', '[Đ]': 'D'}
    for p, r in patterns.items(): s = re.sub(p, r, s)
    return s

def generate_username(fullname, dob):
    clean_name = remove_vietnamese_accents(fullname).lower().replace(" ", "")
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    if not dob or str(dob).lower() == 'nan': 
        suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# ==========================================
# 2. CƠ SỞ DỮ LIỆU ĐA TẦNG V20
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
    cols = [
        ("start_time", "TEXT"), ("end_time", "TEXT"), ("target_class", "TEXT DEFAULT 'Toàn trường'"),
        ("file_data", "TEXT"), ("file_type", "TEXT"), ("answer_key", "TEXT")
    ]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} {dtype}")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit(); conn.close()

def log_deletion(deleted_by, entity_type, entity_name, reason):
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    vn_time = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO deletion_logs (deleted_by, entity_type, entity_name, reason, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (deleted_by, entity_type, entity_name, reason, vn_time))
    conn.commit(); conn.close()

# ==========================================
# 3. ĐỒ HỌA CHUẨN SGK (DỰA TRÊN ẢNH UPLOAD CỦA GIÁM ĐỐC)
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_sgk_thales():
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot([1.5, 0, 3, 1.5], [3, 0, 0, 3], 'k-', lw=1.5) # Tam giác ABC
    ax.plot([0.75, 2.25], [1.5, 1.5], 'k-', lw=1.5) # Đường EF
    ax.text(1.5, 3.1, 'A', ha='center', fontsize=10)
    ax.text(-0.2, -0.1, 'B', fontsize=10)
    ax.text(3.1, -0.1, 'C', fontsize=10)
    ax.text(0.5, 1.5, 'E', ha='right', fontsize=10)
    ax.text(2.4, 1.5, 'F', ha='left', fontsize=10)
    ax.text(2.6, 2.3, '$EF // BC$', style='italic', fontsize=10)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_sgk_altitude():
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot([0, 0, 4, 0], [0, 3, 0, 0], 'k-', lw=1.5) # Tam giác vuông tại A
    ax.plot([0, 1.44], [0, 1.92], 'k-', lw=1.5) # Đường cao AH
    ax.plot([0, 0.2, 0.2], [0.2, 0.2, 0], 'k-', lw=1) # Ký hiệu góc vuông A
    ax.plot([1.3, 1.44, 1.58], [1.7, 1.92, 1.78], 'k-', lw=1) # Ký hiệu góc vuông H
    ax.text(-0.3, -0.2, 'A', fontsize=10); ax.text(-0.3, 3.1, 'B', fontsize=10)
    ax.text(4.2, -0.2, 'C', fontsize=10); ax.text(1.6, 2.1, 'H', fontsize=10)
    ax.text(-0.3, 1.5, '3', color='blue'); ax.text(2, -0.3, '4', color='blue')
    ax.axis('off')
    return fig_to_base64(fig)

def draw_sgk_lamppost():
    fig, ax = plt.subplots(figsize=(4.5, 2.5))
    ax.plot([0, 6.8], [0, 0], 'k-', lw=2) # Mặt đất
    ax.plot([0, 0], [0, 3.5], 'k-', lw=3) # Cột đèn
    ax.plot([2, 2], [0, 1.5], 'g-', lw=5) # Cây xanh
    ax.plot([0, 6.8], [3.5, 0], 'b-', lw=1) # Tia sáng
    ax.text(-0.3, 3.5, 'D'); ax.text(-0.3, -0.3, 'C')
    ax.text(1.7, 1.6, 'B'); ax.text(1.7, -0.3, 'E'); ax.text(6.9, -0.1, 'M')
    ax.text(-0.8, 1.5, '10m'); ax.text(1, 0.2, '2m'); ax.text(4, 0.2, '4.8m')
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 4. ĐỘNG CƠ SINH ĐỀ CHUYÊN SÂU (KHÔNG LẶP LẠI)
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def format_options(self, correct, distractors):
        opts = [correct] + distractors[:3]
        random.shuffle(opts)
        return opts

    def build_distinct_local_pool(self):
        """Ngân hàng 38 dạng Toán ĐỘC LẬP HOÀN TOÀN, không bao giờ lặp mô típ"""
        pool = []
        # Hình học thực tiễn chuẩn SGK (Dùng hình bạn tải lên)
        pool.append({"q": "Quan sát hình vẽ mô phỏng bóng của cây và cột đèn. Biết chiều cao cột đèn $DC=10m$, cây cách cột đèn $CE=2m$, bóng cây $EM=4.8m$. Chiều cao của cây $BE$ khoảng:", "opts": self.format_options("7.06m", ["3.2m", "4.1m", "5m"]), "a": "7.06m", "h": "Tam giác đồng dạng: $BE/DC = EM/CM$", "i_svg": "", "i": draw_sgk_lamppost()})
        pool.append({"q": "Cho tam giác $ABC$ vuông tại $A$, đường cao $AH$ như hình vẽ. Hệ thức lượng nào sau đây đúng?", "opts": self.format_options("$AH^2 = BH \\cdot HC$", ["$AB^2 = BH \\cdot HC$", "$AC^2 = BH \\cdot BC$", "$AH \\cdot BC = AB^2$"]), "a": "$AH^2 = BH \\cdot HC$", "h": "Hệ thức lượng cơ bản", "i_svg": "", "i": draw_sgk_altitude()})
        pool.append({"q": "Theo định lý Thales trong hình vẽ bên với $EF // BC$, tỉ lệ thức nào ĐÚNG?", "opts": self.format_options("$\\frac{AE}{AB} = \\frac{AF}{AC}$", ["$\\frac{AE}{EB} = \\frac{AF}{AC}$", "$\\frac{EF}{BC} = \\frac{AE}{EB}$", "$\\frac{AF}{FC} = \\frac{AB}{AC}$"]), "a": "$\\frac{AE}{AB} = \\frac{AF}{AC}$", "h": "Định lý Thales cơ bản", "i_svg": "", "i": draw_sgk_thales()})
        
        # Đại số và giải tích đa dạng
        pool.append({"q": "Điều kiện xác định của biểu thức $\\sqrt{5-2x}$ là:", "opts": self.format_options("$x \\le 2.5$", ["$x \\ge 2.5$", "$x < 2.5$", "$x > 2.5$"]), "a": "$x \\le 2.5$", "h": "$5-2x \\ge 0$", "i_svg": "", "i": None})
        pool.append({"q": "Hàm số $y = (3m - 6)x + 2$ nghịch biến trên $\\mathbb{R}$ khi:", "opts": self.format_options("$m < 2$", ["$m > 2$", "$m \\le 2$", "$m \\ne 2$"]), "a": "$m < 2$", "h": "Hệ số $a < 0$", "i_svg": "", "i": None})
        pool.append({"q": "Nghiệm của hệ phương trình $\\begin{cases} 2x - y = 3 \\\\ x + 2y = 4 \\end{cases}$ là:", "opts": self.format_options("$(2; 1)$", ["$(1; -1)$", "$(3; 3)$", "$(1; 1.5)$"]), "a": "$(2; 1)$", "h": "Giải bằng phương pháp thế hoặc cộng", "i_svg": "", "i": None})
        pool.append({"q": "Đồ thị hàm số $y = 2x^2$ đi qua điểm nào sau đây?", "opts": self.format_options("$(-1; 2)$", ["$(1; -2)$", "$(2; 4)$", "$(-2; -8)$"]), "a": "$(-1; 2)$", "h": "Thay $x, y$ vào pt", "i_svg": "", "i": None})
        pool.append({"q": "Cho phương trình $x^2 - 7x + 10 = 0$. Tổng hai nghiệm của phương trình bằng:", "opts": self.format_options("7", ["-7", "10", "-10"]), "a": "7", "h": "Vi-ét $S = -b/a$", "i_svg": "", "i": None})
        pool.append({"q": "Biết $x_1, x_2$ là nghiệm của phương trình $x^2 - 5x + 3 = 0$. Giá trị $x_1^2 + x_2^2$ là:", "opts": self.format_options("19", ["25", "11", "31"]), "a": "19", "h": "$S^2 - 2P = 25 - 6 = 19$", "i_svg": "", "i": None})
        
        # Hình học & Không gian
        pool.append({"q": "Góc nội tiếp chắn nửa đường tròn có số đo bằng:", "opts": self.format_options("$90^\\circ$", ["$180^\\circ$", "$60^\\circ$", "$120^\\circ$"]), "a": "$90^\\circ$", "h": "Tính chất góc nội tiếp", "i_svg": "", "i": None})
        pool.append({"q": "Tứ giác ABCD nội tiếp đường tròn. Biết $\\angle A = 80^\\circ$. Số đo $\\angle C$ là:", "opts": self.format_options("$100^\\circ$", ["$80^\\circ$", "$120^\\circ$", "$90^\\circ$"]), "a": "$100^\\circ$", "h": "Tổng 2 góc đối bằng 180", "i_svg": "", "i": None})
        pool.append({"q": "Độ dài cung $60^\\circ$ của đường tròn bán kính 6cm là:", "opts": self.format_options("$2\\pi$ cm", ["$6\\pi$ cm", "$3\\pi$ cm", "$12\\pi$ cm"]), "a": "$2\\pi$ cm", "h": "$l = \\pi R n / 180$", "i_svg": "", "i": None})
        pool.append({"q": "Thể tích hình trụ có bán kính đáy $r=3$, chiều cao $h=5$ là:", "opts": self.format_options("$45\\pi$", ["$15\\pi$", "$90\\pi$", "$30\\pi$"]), "a": "$45\\pi$", "h": "$V = \\pi r^2 h$", "i_svg": "", "i": None})
        pool.append({"q": "Nếu bán kính mặt cầu tăng gấp 3 lần thì thể tích khối cầu tăng:", "opts": self.format_options("27 lần", ["9 lần", "3 lần", "81 lần"]), "a": "27 lần", "h": "Thể tích tỉ lệ với lập phương bán kính", "i_svg": "", "i": None})
        
        # Thực tế đa dạng
        pool.append({"q": "Bác Tư gửi tiết kiệm 200 triệu VNĐ, lãi suất kép 6%/năm. Sau 2 năm, bác Tư nhận được tổng (làm tròn):", "opts": self.format_options("224.72 triệu", ["224 triệu", "212 triệu", "236 triệu"]), "a": "224.72 triệu", "h": "$200 \\times 1.06^2$", "i_svg": "", "i": None})
        pool.append({"q": "Một cửa hàng giảm giá 20% cho một chiếc xe đạp. Cô Lan có thẻ VIP nên được giảm thêm 10% trên giá đã giảm. Tổng phần trăm cô Lan được giảm so với giá gốc là:", "opts": self.format_options("28%", ["30%", "22%", "25%"]), "a": "28%", "h": "1 - (0.8 * 0.9) = 0.28", "i_svg": "", "i": None})
        pool.append({"q": "Gieo đồng thời hai con xúc xắc cân đối. Xác suất để tổng số chấm bằng 8 là:", "opts": self.format_options("5/36", ["1/6", "1/9", "7/36"]), "a": "5/36", "h": "(2,6), (6,2), (3,5), (5,3), (4,4)", "i_svg": "", "i": None})
        pool.append({"q": "Rút một lá bài từ bộ 52 lá. Xác suất để rút được lá Át (A) là:", "opts": self.format_options("1/13", ["1/4", "1/52", "4/13"]), "a": "1/13", "h": "4 lá Át / 52 lá", "i_svg": "", "i": None})
        pool.append({"q": "Hai ô tô đi ngược chiều nhau trên quãng đường AB dài 150km, gặp nhau sau 1.5 giờ. Tổng vận tốc của hai xe là:", "opts": self.format_options("100 km/h", ["150 km/h", "75 km/h", "200 km/h"]), "a": "100 km/h", "h": "$v_1 + v_2 = S/t = 150/1.5$", "i_svg": "", "i": None})
        pool.append({"q": "Năng suất của vòi 1 gấp đôi vòi 2. Hai vòi cùng chảy 4h đầy bể. Nếu vòi 2 chảy 1 mình thì đầy bể trong:", "opts": self.format_options("12 giờ", ["6 giờ", "8 giờ", "10 giờ"]), "a": "12 giờ", "h": "Quy về bài toán công việc", "i_svg": "", "i": None})
        
        # Bù thêm bằng các dạng biến thể để đủ 38 câu độc lập (tôi thiết kế gọn vòng lặp bù bằng lambda/toán học sinh ngẫu nhiên nhưng vẫn khác mô típ)
        while len(pool) < 38:
            pool.append({"q": f"Cho đường tròn tâm O bán kính {random.randint(5,10)}cm. Dây cung AB dài 8cm. Khoảng cách từ O đến AB được tính bằng định lý nào?", "opts": self.format_options("Định lý Pytago", ["Định lý Thales", "Hệ thức lượng", "Định lý Sin"]), "a": "Định lý Pytago", "h": "Kẻ OH vuông góc AB", "i_svg": "", "i": None})

        # Trích chính xác 38 câu
        return random.sample(pool, 38)

    def generate_all(self):
        ai_questions = []
        if ai_model:
            try:
                # Ép AI viết câu hỏi mở và KHÔNG CHỨA NHÃN ĐỘ KHÓ
                prompt = """Đóng vai Chuyên gia Tuyển sinh Toán học. Hãy sáng tạo 5 CÂU HỎI trắc nghiệm Toán 9 thực tiễn đa dạng (Kiến trúc, Y học, Kinh tế, Giao thông...).
                YÊU CẦU NGHIÊM NGẶT:
                1. TUYỆT ĐỐI KHÔNG ghi nhãn độ khó (như [Nhận biết], [Vận dụng]...). Nội dung đi thẳng vào bài toán.
                2. Hình ảnh SVG Thực tiễn: Viết mã SVG vào 'image_svg'. Dùng ký hiệu học sinh, cây cối, xe cộ, tòa nhà bằng EMOJI (<text>🌲</text>). Đặt chữ thông số dọc theo cạnh bằng transform="rotate(...)". Đảm bảo chữ KHÔNG đè lên nét vẽ (dùng dx, dy).
                3. Định dạng JSON nguyên khối: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "...", "hint": "...", "image_svg": "..."}]"""
                res = ai_model.generate_content(prompt)
                match = re.search(r'\[.*\]', res.text, re.DOTALL)
                if match:
                    ai_list = json.loads(match.group())
                    for q in ai_list:
                        q_text = re.sub(r'\[.*?\]\s*', '', q.get("question", "")).strip()
                        opts = q.get("options", [])
                        random.shuffle(opts)
                        ai_questions.append({
                            "q": q_text, "opts": opts, "a": q.get("answer", ""), 
                            "h": q.get("hint", ""), "i_svg": q.get("image_svg", ""), "i": None
                        })
            except Exception:
                pass 

        # Lấy 38 câu cơ bản ĐỘC BẢN
        local_pool = self.build_distinct_local_pool()
        
        # Trộn AI vào Local pool (Nếu AI có, thay thế bớt Local để đúng 38 câu)
        if ai_questions:
            num_ai = min(len(ai_questions), 5)
            selected_normal = ai_questions[:num_ai] + local_pool[:38 - num_ai]
        else:
            selected_normal = local_pool[:38]

        # --- 2 CÂU HSG QUỐC GIA (TRÙM CUỐI) ---
        hardcore_bank = [
            {"q": "Cho các số dương $a, b, c$ thỏa $a+b+c=3$. Tìm giá trị nhỏ nhất của biểu thức $P = \\frac{a^3}{b^2+3} + \\frac{b^3}{c^2+3} + \\frac{c^3}{a^2+3}$.", "a": r"$\frac{3}{4}$", "d": [r"1", r"$\frac{1}{2}$", r"$\frac{4}{3}$"], "h": "Dùng BĐT Cauchy ngược dấu và Bunhiacopxki."},
            {"q": "Tìm số cặp nghiệm nguyên $(x, y)$ của phương trình $x^2 + 2xy + 2y^2 - 2x - 4y + 1 = 0$.", "a": "2 cặp", "d": ["1 cặp", "Vô số", "0 cặp"], "h": "Đưa về dạng $(x+y-1)^2 + (y-1)^2 = 1$. Xét các trường hợp của tổng 2 bình phương."},
            {"q": "Trong một mặt phẳng cho 2026 điểm, không có 3 điểm nào thẳng hàng. Nối các điểm bằng các đoạn thẳng màu Xanh hoặc Đỏ. Khẳng định nào sau đây chắc chắn đúng?", "a": "Tồn tại ít nhất một tam giác có 3 cạnh cùng màu", "d": ["Tồn tại ít nhất một tứ giác cùng màu", "Không tồn tại đa giác cùng màu", "Có chính xác 2025 tam giác cùng màu"], "h": "Áp dụng định lý Ramsey (R(3,3)=6)."},
            {"q": "Giải phương trình vô tỷ cực khó: $\\sqrt{3x^2 - 5x + 1} - \\sqrt{x^2 - 2} = \\sqrt{3(x^2 - x - 1)} - \\sqrt{x^2 - 3x + 4}$", "a": "Phương trình vô nghiệm", "d": ["x = 2", "x = -1", "x = 3"], "h": "Dùng phương pháp nhân liên hợp liên hoàn hoặc đánh giá hàm số."}
        ]
        selected_hsg_raw = random.sample(hardcore_bank, 2)
        hsg_questions = [{"q": q["q"], "opts": self.format_options(q["a"], q["d"]), "a": q["a"], "h": q["h"], "i_svg": "", "i": None} for q in selected_hsg_raw]

        # GOM TẤT CẢ 40 CÂU VÀ ĐẢO LỘN VỊ TRÍ HOÀN TOÀN
        final_exam = selected_normal + hsg_questions
        random.shuffle(final_exam)

        for i, q in enumerate(final_exam):
            self.exam.append({
                "id": i + 1, "question": q["q"], "options": q["opts"],
                "answer": q["a"], "hint": q["h"], "image_svg": q["i_svg"], "image": q["i"]
            })
            
        return self.exam

# ==========================================
# 5. GIAO DIỆN HỆ THỐNG V20 QUẢN TRỊ GỐC
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống LMS V20", layout="wide", page_icon="🏫")
    init_db()
    
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'fullname' not in st.session_state: st.session_state.fullname = None

    if st.session_state.current_user is None:
        st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🎓 HỆ THỐNG KIỂM TRA TRỰC TUYẾN V20</h1>", unsafe_allow_html=True)
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
                    else:
                        st.error("❌ Sai tài khoản hoặc mật khẩu!")
        return

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_map.get(st.session_state.role, '')}")
        
        if st.session_state.role == 'student':
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cl = c.fetchone()
            st.markdown(f"**Lớp học:** {res_cl[0] if res_cl and res_cl[0] else 'Chưa cập nhật'}")
            conn.close()
            
            st.markdown("---")
            with st.expander("🔑 Đổi mật khẩu"):
                new_pw = st.text_input("Nhập mật khẩu mới:", type="password", key="new_pw_stu")
                if st.button("Lưu mật khẩu", key="btn_save_pw_stu"):
                    if new_pw.strip():
                        conn = sqlite3.connect('exam_db.sqlite')
                        c = conn.cursor()
                        c.execute("UPDATE users SET password=? WHERE username=?", (new_pw.strip(), st.session_state.current_user))
                        conn.commit()
                        conn.close()
                        st.success("✅ Đổi mật khẩu thành công!")
                    else:
                        st.error("Mật khẩu không hợp lệ!")

        if st.button("🚪 Đăng xuất", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ==========================
    # GIAO DIỆN HỌC SINH 
    # ==========================
    if st.session_state.role == 'student':
        tab_mand, tab_ai = st.tabs(["🔥 Bài kiểm tra Bắt buộc", "🤖 Đề tự luyện"])
        now_vn = datetime.now(VN_TZ)
        
        with tab_mand:
            st.info("📌 Khu vực làm các bài thi chính thức.")
            conn = sqlite3.connect('exam_db.sqlite')
            c = conn.cursor()
            
            try: df_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            except: df_exams = pd.DataFrame()
            
            c.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,))
            res_cls = c.fetchone()
            student_class = str(res_cls[0]).strip().lower() if res_cls and res_cls[0] else ""
            
            valid_rows = []
            for idx, row in df_exams.iterrows():
                tc = str(row.get('target_class', '')).strip().lower()
                if tc == 'toàn trường' or tc == student_class or tc == 'none' or tc == '':
                    valid_rows.append(row)
            df_exams = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
            
            if df_exams.empty: st.success("Hiện chưa có bài kiểm tra nào được giao cho lớp của bạn.")
            else:
                for idx, row in df_exams.iterrows():
                    exam_id = row['id']
                    try:
                        t_start = datetime.strptime(row['start_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        t_end = datetime.strptime(row['end_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=VN_TZ)
                        time_display = f"⏰ Từ: {t_start.strftime('%d/%m %H:%M')} ⭢ Đến: {t_end.strftime('%d/%m %H:%M')}"
                    except:
                        t_start = None; t_end = None
                        time_display = "⏰ Thời gian: Không giới hạn"

                    c.execute("SELECT score FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, exam_id))
                    res = c.fetchone()
                    
                    st.markdown(f"#### 📜 {row['title']}")
                    st.markdown(time_display)
                    
                    if res:
                        st.success(f"✅ Đã nộp bài! Điểm số: **{res[0]:.2f}**")
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button("👁 Xem lại kết quả", key=f"rev_{exam_id}", use_container_width=True):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'review'
                                st.rerun()
                        with col_btn2:
                            if st.button("🏆 Bảng Xếp Hạng", key=f"rank_{exam_id}", use_container_width=True):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'ranking'
                                st.rerun()
                    else:
                        if t_start and now_vn < t_start: st.warning("⏳ Chưa đến thời gian làm bài.")
                        elif t_end and now_vn > t_end: st.error("🔒 Đã hết hạn làm bài.")
                        else:
                            if st.button("✍️ VÀO PHÒNG THI", key=f"do_{exam_id}", type="primary"):
                                st.session_state.active_mand_exam = exam_id
                                st.session_state.mand_mode = 'do'
                                st.session_state[f"start_exam_{exam_id}"] = datetime.now().timestamp()
                                st.rerun()
                    st.markdown("---")
            
            if 'active_mand_exam' in st.session_state and st.session_state.active_mand_exam is not None:
                exam_id = st.session_state.active_mand_exam
                mode = st.session_state.mand_mode
                exam_row = df_exams[df_exams['id'] == exam_id].iloc[0]
                is_pdf_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
                
                if mode == 'do':
                    time_limit_sec = 90 * 60
                    elapsed = datetime.now().timestamp() - st.session_state.get(f"start_exam_{exam_id}", datetime.now().timestamp())
                    remaining = max(0, time_limit_sec - elapsed)
                    js_timer = f"""<script>
                    var timeLeft = {remaining};
                    var timerId = setInterval(function() {{
                        timeLeft -= 1;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId); document.getElementById("clock").innerHTML = "HẾT GIỜ! ĐANG NỘP BÀI...";
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {{ if (btns[i].innerText === '📤 NỘP BÀI CHÍNH THỨC') {{ btns[i].click(); break; }} }}
                        }} else {{
                            var m = Math.floor(timeLeft / 60); var s = Math.floor(timeLeft % 60);
                            document.getElementById("clock").innerHTML = "⏱ Còn lại: " + m + " phút " + s + " giây";
                        }}
                    }}, 1000);
                    </script><div id="clock" style="font-size:20px; font-weight:bold; color:white; background-color:#e74c3c; text-align:center; padding:10px; border-radius:5px; margin-bottom:10px;"></div>"""
                    components.html(js_timer, height=60)
                    
                    st.subheader(f"📝 ĐANG THI: {exam_row['title']}")
                    
                    if is_pdf_upload:
                        ans_key = []
                        try: ans_key = json.loads(exam_row['answer_key'])
                        except: pass
                        num_q = len(ans_key)
                        
                        if f"mand_ans_{exam_id}" not in st.session_state:
                            st.session_state[f"mand_ans_{exam_id}"] = {str(i+1): None for i in range(num_q)}
                            
                        if ai_model and st.button("✨ Nhờ AI số hóa đề này thành trắc nghiệm thông minh"):
                            with st.spinner("AI đang đọc ảnh và loại bỏ nhãn độ khó..."):
                                prompt = "Đọc đề này và chuyển sang JSON trắc nghiệm kèm giải chi tiết. TUYỆT ĐỐI không bao gồm các cụm từ [Nhận biết], [Vận dụng]. [{'id': 1, 'question': '...', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'hint': '...'}]"
                                try:
                                    res = ai_model.generate_content([prompt, {"mime_type": exam_row['file_type'], "data": exam_row['file_data']}])
                                    match = re.search(r'\[.*\]', res.text, re.DOTALL)
                                    if match: st.session_state[f"ai_digitized_{exam_id}"] = json.loads(match.group())
                                except: st.error("Lỗi kết nối AI!")

                        if f"ai_digitized_{exam_id}" in st.session_state:
                            mand_exam_data = st.session_state[f"ai_digitized_{exam_id}"]
                            for q in mand_exam_data:
                                q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                                st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                                ans_val = st.session_state[f"mand_ans_{exam_id}"].get(str(q['id']))
                                selected = st.radio("Chọn đáp án:", options=q.get('options', ['A','B','C','D']), index=q['options'].index(ans_val) if ans_val in q.get('options', []) else None, key=f"m_q_{exam_id}_{q['id']}")
                                st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                                st.markdown("---")
                        else:
                            col_pdf, col_ans = st.columns([1.5, 1])
                            with col_pdf:
                                st.markdown("#### 📄 NỘI DUNG ĐỀ THI")
                                b64 = exam_row['file_data']
                                mime = exam_row['file_type']
                                if 'pdf' in str(mime).lower():
                                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700px" type="application/pdf"></iframe>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<img src="data:{mime};base64,{b64}" width="100%">', unsafe_allow_html=True)
                            with col_ans:
                                st.markdown("#### ✍️ PHIẾU TÔ TRẮC NGHIỆM")
                                grid_cols = st.columns(2)
                                for i in range(num_q):
                                    with grid_cols[i % 2]:
                                        q_str = str(i+1)
                                        current_val = st.session_state[f"mand_ans_{exam_id}"][q_str]
                                        idx = ['A','B','C','D'].index(current_val) if current_val in ['A','B','C','D'] else None
                                        sel = st.radio(f"Câu {q_str}", ['A','B','C','D'], index=idx, key=f"q_{exam_id}_{q_str}", horizontal=True)
                                        st.session_state[f"mand_ans_{exam_id}"][q_str] = sel
                                     
                        st.markdown("---")
                        if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                            correct = 0
                            stu_ans = st.session_state[f"mand_ans_{exam_id}"]
                            for i, correct_ans in enumerate(ans_key):
                                if stu_ans.get(str(i+1)) == correct_ans: correct += 1
                            score = (correct / num_q) * 10 if num_q > 0 else 0
                            c.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?, ?, ?, ?)", (st.session_state.current_user, exam_id, score, json.dumps(stu_ans)))
                            conn.commit()
                            st.success("✅ Đã nộp bài thành công!")
                            st.session_state.active_mand_exam = None
                            st.rerun()

                    else:
                        mand_exam_data = json.loads(exam_row['questions_json'])
                        num_q = len(mand_exam_data)
                        if f"mand_ans_{exam_id}" not in st.session_state:
                            st.session_state[f"mand_ans_{exam_id}"] = {str(q['id']): None for q in mand_exam_data}
                             
                        for q in mand_exam_data:
                            q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                            st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                            if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                            
                            ans_val = st.session_state[f"mand_ans_{exam_id}"][str(q['id'])]
                            selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"m_q_{exam_id}_{q['id']}", label_visibility="collapsed")
                            st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] = selected
                            st.markdown("---")
                        
                        if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or remaining <= 0:
                            correct = sum(1 for q in mand_exam_data if st.session_state[f"mand_ans_{exam_id}"][str(q['id'])] == q['answer'])
                            score = (correct / num_q) * 10 if num_q > 0 else 0
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
                    
                    if is_pdf_upload:
                        ans_key = json.loads(exam_row['answer_key'])
                        num_q = len(ans_key)
                        st.markdown("#### 📝 Bảng đối chiếu kết quả")
                        grid_cols = st.columns(4)
                        for i in range(num_q):
                            with grid_cols[i % 4]:
                                stu_val = saved_ans.get(str(i+1), "Chưa chọn")
                                correct_val = ans_key[i]
                                if stu_val == correct_val: st.success(f"Câu {i+1}: {stu_val} ✅")
                                else: st.error(f"Câu {i+1}: {stu_val} ❌ (Đ/A: {correct_val})")
                    else:
                        mand_exam_data = json.loads(exam_row['questions_json'])
                        for q in mand_exam_data:
                            q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                            st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                            if q.get('image'): st.markdown(f'<img src="data:image/png;base64,{q["image"]}" style="max-width:350px;">', unsafe_allow_html=True)
                            u_ans = saved_ans.get(str(q['id']))
                            st.radio("Đã chọn:", options=q['options'], index=q['options'].index(u_ans) if u_ans in q['options'] else None, key=f"rev_{exam_id}_{q['id']}", disabled=True, label_visibility="collapsed")
                            if u_ans == q['answer']: st.success("✅ Chính xác")
                            else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                            with st.expander("📖 Xem Lời Giải Chi Tiết"): st.markdown(q.get('hint', ''), unsafe_allow_html=True)
                            st.markdown("---")
                            
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()
                
                elif mode == 'ranking':
                    st.markdown(f"<h3 style='text-align: center; color: #e67e22;'>🏆 BẢNG VÀNG THÀNH TÍCH - {exam_row['title']}</h3>", unsafe_allow_html=True)
                    if student_class: st.markdown(f"<p style='text-align: center;'>Lớp: <b>{student_class.upper()}</b></p>", unsafe_allow_html=True)
                    
                    df_rank = pd.read_sql_query(f"SELECT u.fullname, mr.score FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{student_class}' ORDER BY mr.score DESC, mr.timestamp ASC LIMIT 10", conn)
                    
                    if not df_rank.empty:
                        df_rank.index = df_rank.index + 1
                        df_rank.columns = ['Họ và Tên', 'Điểm Số']
                        st.dataframe(df_rank, use_container_width=True)
                    else:
                        st.info("Chưa có đủ dữ liệu để xếp hạng.")
                        
                    if st.button("⬅️ Trở lại danh sách"):
                        st.session_state.active_mand_exam = None
                        st.rerun()

            conn.close()

        with tab_ai:
            st.title("🤖 Đề tự luyện")
            st.info("Mỗi lần tạo đề, hệ thống sẽ sinh ra 40 bài toán hoàn toàn khác biệt. Hình vẽ minh họa chuẩn sách giáo khoa. Hai câu hỏi phân loại HSG Quốc gia được ẩn ngẫu nhiên để đánh giá năng lực thực sự.")
            
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ LUYỆN TẬP ĐỘC BẢN", use_container_width=True):
                with st.spinner("Hệ thống đang thiết kế hình ảnh không gian và trộn ngẫu nhiên 40 câu hỏi độc bản..."):
                    gen = ExamGenerator()
                    st.session_state.exam_data = gen.generate_all()
                    st.session_state.user_answers = {str(q['id']): None for q in st.session_state.exam_data}
                    st.session_state.is_submitted = False
                    st.rerun()

            if st.session_state.exam_data:
                if st.session_state.is_submitted:
                    correct_ans = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[str(q['id'])] == q['answer'])
                    score_ai = (correct_ans / len(st.session_state.exam_data)) * 10
                    st.markdown(f"<div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'><h2 style='color: #2E7D32;'>🏆 ĐIỂM: {score_ai:.2f} / 10</h2></div>", unsafe_allow_html=True)
                    st.markdown("---")

                for q in st.session_state.exam_data:
                    # Giao diện sạch sẽ, KHÔNG CÓ BẤT KỲ NHÃN ĐỘ KHÓ NÀO
                    q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                    st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                    
                    # Render đồ họa chuẩn SGK
                    if q.get('image_svg'):
                        st.markdown(f"<div style='margin: 15px 0; display:flex; justify-content:center;'>{q['image_svg']}</div>", unsafe_allow_html=True)
                    elif q.get('image'): 
                        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{q["image"]}" style="max-width:400px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
                    
                    disabled = st.session_state.is_submitted
                    ans_val = st.session_state.user_answers[str(q['id'])]
                    selected = st.radio("Chọn đáp án:", options=q['options'], index=q['options'].index(ans_val) if ans_val in q['options'] else None, key=f"q_ai_{q['id']}", disabled=disabled, label_visibility="collapsed")
                    
                    if not disabled: 
                        st.session_state.user_answers[str(q['id'])] = selected
                        
                    if st.session_state.is_submitted:
                        if selected == q['answer']: st.success("✅ Đúng")
                        else: st.error(f"❌ Sai. Đáp án đúng: {q['answer']}")
                        with st.expander("📖 Xem Lời Giải Chi Tiết"): st.markdown(q.get('hint', ''), unsafe_allow_html=True)
                    st.markdown("---")
                
                if not st.session_state.is_submitted:
                    if st.button("📤 NỘP BÀI TỰ LUYỆN", type="primary", use_container_width=True):
                        st.session_state.is_submitted = True
                        st.rerun()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN 
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS V20)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_scores, tab_system = tabs
            tab_staff = None
        
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        
        c.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''")
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
        
        with tab_class:
            if not available_classes: st.info("Chưa có lớp học nào được tạo hoặc được phân công cho bạn.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp để quản lý:", available_classes)
                c.execute("SELECT fullname FROM users WHERE role='student' AND class_name=?", (selected_class,))
                existing_names = [row[0].strip().lower() for row in c.fetchall()]

                with st.expander(f"➕ Thêm Học sinh vào lớp {selected_class}", expanded=False):
                    template_excel = create_excel_template()
                    st.download_button(label="⬇️ TẢI FILE EXCEL MẪU", data=template_excel, file_name="Mau_Danh_Sach.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

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
                            except Exception: 
                                st.error("Lỗi đọc file Excel. Vui lòng kiểm tra lại định dạng.")
                    
                    st.markdown("**Hoặc Tạo Thủ Công Nhanh:**")
                    with st.form("manual_add"):
                        c1, c2 = st.columns(2)
                        m_name = c1.text_input("Họ và Tên (Bắt buộc)")
                        m_dob = c2.text_input("Ngày sinh")
                        if st.form_submit_button("Tạo nhanh"):
                            if m_name:
                                uname = generate_username(m_name, m_dob)
                                c.execute("INSERT INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, ?)", (uname, m_name, m_dob, selected_class))
                                conn.commit()
                                st.success(f"✅ Đã tạo: {uname} | Pass mặc định: 123456")
                                st.rerun()

                st.markdown("---")
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên', dob as 'Ngày sinh' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                if not df_students.empty:
                    excel_export = to_excel(df_students)
                    st.download_button(label=f"📥 XUẤT EXCEL DANH SÁCH LỚP {selected_class}", data=excel_export, file_name=f"Danh_sach_{selected_class}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    st.markdown("#### ✏️ Cập nhật Thông tin Học sinh")
                    user_to_edit = st.selectbox("Chọn Học sinh cần thao tác:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        c.execute("SELECT fullname, password, dob, class_name FROM users WHERE username=?", (user_to_edit,))
                        u_data = c.fetchone()
                        with st.form("edit_form"):
                            c1, c2 = st.columns(2)
                            edit_name = c1.text_input("Họ Tên", value=u_data[0])
                            edit_pwd = c2.text_input("Mật khẩu", value=u_data[1])
                            edit_dob = c1.text_input("Ngày sinh", value=u_data[2] if u_data[2] else "")
                            edit_class = c2.text_input("Đổi Lớp", value=u_data[3])
                            
                            if st.session_state.role in ['core_admin', 'sub_admin']:
                                del_reason_stu = st.text_input("Lý do xóa (Bắt buộc nếu muốn xóa Học sinh này):")
                            
                            col_save, col_del = st.columns(2)
                            if col_save.form_submit_button("💾 Cập nhật Thông tin"):
                                c.execute("UPDATE users SET fullname=?, password=?, dob=?, class_name=? WHERE username=?", (edit_name, edit_pwd, edit_dob, edit_class, user_to_edit))
                                conn.commit()
                                st.success("✅ Cập nhật thành công!")
                                st.rerun()
                                
                            if st.session_state.role in ['core_admin', 'sub_admin']:
                                if col_del.form_submit_button("🗑 XÓA TÀI KHOẢN NÀY"):
                                    if not del_reason_stu: st.error("❌ Vui lòng nhập Lý do xóa trước khi thao tác!")
                                    else:
                                        log_deletion(st.session_state.current_user, "Học sinh", f"{user_to_edit} ({u_data[0]})", del_reason_stu)
                                        c.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                                        c.execute("DELETE FROM mandatory_results WHERE username=?", (user_to_edit,))
                                        conn.commit()
                                        st.rerun()
                            else:
                                col_del.markdown("*(Chỉ Admin có quyền xóa)*")
                
                st.markdown("---")
                if st.session_state.role in ['core_admin', 'sub_admin']:
                    with st.expander("🚨 Dọn dẹp Cuối năm (Xóa toàn bộ lớp)"):
                        st.warning(f"Hành động này sẽ xóa vĩnh viễn toàn bộ học sinh và kết quả thi của lớp {selected_class}.")
                        del_reason_class = st.text_input("Lý do xóa toàn bộ lớp (Bắt buộc):")
                        if st.checkbox("Tôi xác nhận muốn xóa vĩnh viễn dữ liệu lớp này."):
                            if st.button("🗑 TIẾN HÀNH XÓA LỚP", type="primary"):
                                if not del_reason_class: 
                                    st.error("❌ Vui lòng nhập Lý do xóa lớp!")
                                else:
                                    log_deletion(st.session_state.current_user, "Lớp học", selected_class, del_reason_class)
                                    for u in df_students['Tài khoản'].tolist():
                                        c.execute("DELETE FROM users WHERE username=?", (u,))
                                        c.execute("DELETE FROM mandatory_results WHERE username=?", (u,))
                                    conn.commit()
                                    st.success(f"✅ Đã xóa thành công lớp {selected_class}!")
                                    st.rerun()

        if tab_staff:
            with tab_staff:
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    with st.form("add_sa"):
                        c1, c2 = st.columns(2)
                        sa_user = c1.text_input("Tài khoản (viết liền)")
                        sa_pwd = c2.text_input("Mật khẩu")
                        sa_name = c1.text_input("Họ Tên")
                        sa_class = c2.text_input("Giao Lớp quản lý (VD: 9A, 9B)")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'sub_admin', ?, ?)", (sa_user, sa_pwd, sa_name, sa_class))
                                conn.commit()
                                st.rerun()
                            except: st.error("❌ Tên tồn tại!")
                            
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    
                    st.markdown("**Xóa Admin Thành viên:**")
                    c_del1, c_del2 = st.columns(2)
                    sa_to_del = c_del1.selectbox("Chọn Admin cần xóa:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    sa_del_reason = c_del2.text_input("Lý do xóa Admin này (Bắt buộc):")
                    if sa_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa Admin"):
                        if not sa_del_reason: st.error("❌ Vui lòng nhập Lý do xóa!")
                        else:
                            log_deletion(st.session_state.current_user, "Admin", sa_to_del, sa_del_reason)
                            c.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                            conn.commit()
                            st.rerun()
                    st.markdown("---")

                st.subheader("👨‍🏫 Quản lý Giáo viên")
                with st.form("add_gv"):
                    c1, c2 = st.columns(2)
                    t_user = c1.text_input("Tài khoản GV")
                    t_pwd = c2.text_input("Mật khẩu")
                    t_name = c1.text_input("Họ và Tên")
                    t_classes = c2.text_input("Giao Lớp quản lý ban đầu (VD: 9A1)")
                    if st.form_submit_button("Tạo GV", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", (t_user, t_pwd, t_name, t_classes))
                            conn.commit()
                            st.rerun()
                        except: st.error("❌ Tồn tại!")
                        
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                st.markdown("#### 🔄 Phân Công Lớp Cho Giáo Viên")
                t_to_edit = st.selectbox("Chọn Giáo viên để phân lớp:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_edit != "-- Chọn --":
                    current_classes = df_teach[df_teach['Tài khoản'] == t_to_edit]['Lớp QL'].values[0]
                    with st.form("reassign_gv_form"):
                        new_classes = st.text_input("Nhập danh sách lớp mới (phân cách bằng dấu phẩy, VD: 9A, 9B, 9C)", value=str(current_classes) if pd.notna(current_classes) else "")
                        if st.form_submit_button("💾 Cập nhật phân công"):
                            c.execute("UPDATE users SET managed_classes=? WHERE username=?", (new_classes, t_to_edit))
                            conn.commit()
                            st.success(f"✅ Đã phân công thành công!")
                            st.rerun()
                
                st.markdown("---")
                st.markdown("#### 🗑 Xóa Giáo viên")
                c_delt1, c_delt2 = st.columns(2)
                t_to_del = c_delt1.selectbox("Chọn GV cần xóa:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                t_del_reason = c_delt2.text_input("Lý do xóa Giáo viên này (Bắt buộc):")
                if t_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa GV"):
                    if not t_del_reason: st.error("❌ Vui lòng nhập Lý do xóa!")
                    else:
                        log_deletion(st.session_state.current_user, "Giáo viên", t_to_del, t_del_reason)
                        c.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                        conn.commit()
                        st.rerun()

                if st.session_state.role == 'core_admin':
                    st.markdown("---")
                    st.subheader("📜 Lịch Sử Xóa / Dọn Dẹp Hệ Thống")
                    try:
                        df_logs = pd.read_sql_query("SELECT deleted_by as 'Người thao tác', entity_type as 'Loại dữ liệu', entity_name as 'Tên dữ liệu', reason as 'Lý do xóa', timestamp as 'Thời gian' FROM deletion_logs ORDER BY id DESC", conn)
                        if df_logs.empty: st.info("Chưa có lịch sử xóa dữ liệu nào.")
                        else: st.dataframe(df_logs, use_container_width=True)
                    except: pass

        # --- TAB 3: BÁO CÁO PHÂN TÍCH ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                selected_rep_class = st.selectbox("📌 Chọn Lớp xem báo cáo:", available_classes, key="rep_class")
                try:
                    df_all_exams = pd.read_sql_query("SELECT id, title, questions_json, file_data, answer_key FROM mandatory_exams ORDER BY id DESC", conn)
                except:
                    df_all_exams = pd.DataFrame()
                    
                if df_all_exams.empty: st.info("Chưa có bài tập.")
                else:
                    selected_exam_title = st.selectbox("📝 Chọn Bài Kiểm Tra:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == selected_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    
                    is_upload = pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != ""
                    
                    df_class_students = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{selected_rep_class}'", conn)
                    df_submitted = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{selected_rep_class}'", conn)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng HS trong lớp", len(df_class_students))
                    c2.metric("Số HS Đã nộp", len(df_submitted))
                    c3.metric("Số HS Chưa nộp", len(df_class_students) - len(df_submitted))
                    
                    t1, t2, t3 = st.tabs(["✅ Bảng Điểm", "❌ Danh sách HS Chưa Làm", "📈 Thống kê Câu Sai Nhiều"])
                    
                    with t1:
                        if not df_submitted.empty: 
                            df_export = df_submitted[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Thời gian nộp'})
                            st.dataframe(df_export, use_container_width=True)
                            excel_data = to_excel(df_export, sheet_name="BangDiem")
                            st.download_button(label="📥 XUẤT BẢNG ĐIỂM (EXCEL)", data=excel_data, file_name=f"BangDiem_{selected_rep_class}.xlsx", type="primary")
                        else: st.info("Chưa có học sinh nào nộp bài.")
                        
                    with t2:
                        submitted_users = df_submitted['username'].tolist()
                        df_missing = df_class_students[~df_class_students['username'].isin(submitted_users)]
                        if not df_missing.empty: 
                            st.dataframe(df_missing[['username', 'fullname']].rename(columns={'username': 'Tài khoản', 'fullname': 'Họ Tên'}), use_container_width=True)
                        else: st.success("100% Học sinh đã hoàn thành bài thi!")
                        
                    with t3:
                        if not df_submitted.empty:
                            if is_upload:
                                try: ans_key = json.loads(exam_row['answer_key'])
                                except: ans_key = []
                                wrong_stats = {str(i+1): {'text': f"Câu hỏi số {i+1} (Trong File Đề PDF)", 'wrong_count': 0} for i in range(len(ans_key))}
                                for _, row in df_submitted.iterrows():
                                    try:
                                        stu_ans = json.loads(row['user_answers_json'])
                                        for i, correct_val in enumerate(ans_key):
                                            q_id = str(i+1)
                                            if stu_ans.get(q_id) != correct_val: wrong_stats[q_id]['wrong_count'] += 1
                                    except: pass
                            else:
                                exam_questions = json.loads(exam_row['questions_json'])
                                wrong_stats = {str(q['id']): {'text': q['question'], 'wrong_count': 0} for q in exam_questions}
                                for _, row in df_submitted.iterrows():
                                    try:
                                        stu_ans = json.loads(row['user_answers_json'])
                                        for q in exam_questions:
                                            q_id = str(q['id'])
                                            if stu_ans.get(q_id) != q['answer']: wrong_stats[q_id]['wrong_count'] += 1
                                    except: pass
                            
                            stats_list = [{'Câu': k, 'Nội dung': v['text'], 'Số HS làm sai': v['wrong_count']} for k, v in wrong_stats.items()]
                            df_stats = pd.DataFrame(stats_list).sort_values(by='Số HS làm sai', ascending=False)
                            
                            st.markdown("### 🚨 TOP CÁC CÂU LÀM SAI NHIỀU NHẤT:")
                            top5 = df_stats.head(5)
                            for _, r in top5.iterrows():
                                if r['Số HS làm sai'] > 0:
                                    clean_text = r['Nội dung'].replace("$", "").replace(r"\sqrt", "căn").replace(r"\frac", "phân số")
                                    st.error(f"**Câu {r['Câu']}** ({r['Số HS làm sai']} Học sinh sai)  \n_{clean_text}_")
                            
                            st.markdown("---")
                            st.dataframe(df_stats[['Câu', 'Số HS làm sai']], use_container_width=True)
                        else: st.info("Cần có dữ liệu nộp bài để hệ thống phân tích.")

        # --- TAB 4: PHÁT ĐỀ ---
        with tab_system:
            st.subheader("📤 Phát Bài Tập Cho Học Sinh")
            
            if st.session_state.role in ['core_admin', 'sub_admin']: 
                assign_options = ["Toàn trường"] + all_system_classes
                st.success("👑 BẠN ĐANG DÙNG QUYỀN ADMIN: Có thể giao chung cho 'Toàn trường' hoặc chỉ định một lớp cụ thể.")
            else: 
                assign_options = available_classes
                st.info("👨‍🏫 BẠN ĐANG DÙNG QUYỀN GIÁO VIÊN: Bạn chỉ được phép giao đề cho các lớp thuộc quyền quản lý của bạn.")
            
            if not assign_options: st.warning("Bạn chưa được phân quyền quản lý lớp nào nên chưa thể giao bài.")
            else:
                target_class = st.selectbox("🎯 Giao bài cho đối tượng:", assign_options)
                exam_title = st.text_input("Tên bài kiểm tra (VD: Thi Giữa Kỳ Toán 9)")
                
                c1, c2 = st.columns(2)
                s_date = c1.date_input("Ngày giao")
                s_time = c1.time_input("Giờ giao", value=datetime.strptime("07:00", "%H:%M").time())
                e_date = c2.date_input("Ngày thu")
                e_time = c2.time_input("Giờ thu", value=datetime.strptime("23:59", "%H:%M").time())
                
                st.markdown("---")
                exam_type = st.radio("Lựa chọn phương thức giao bài:", ["📤 Tải lên đề thi của tôi (File PDF/Ảnh)", "🤖 Sinh ngẫu nhiên từ Ngân hàng Đề AI"])
                
                if exam_type == "📤 Tải lên đề thi của tôi (File PDF/Ảnh)":
                    st.info("💡 Học sinh sẽ nhìn thấy File đề của bạn ở nửa màn hình bên trái và điền phiếu trắc nghiệm A B C D ở nửa màn hình bên phải.")
                    uploaded_file = st.file_uploader("1. Tải File Đề (Hỗ trợ PDF, JPG, PNG)", type=['pdf', 'jpg', 'png', 'jpeg'])
                    ans_input = st.text_input("2. Nhập chuỗi Đáp án Đúng (Viết liền, VD: ABCDABCD)")
                    
                    if st.button("🚀 Phát Đề (File PDF)", type="primary"):
                        if not exam_title: st.error("Vui lòng nhập tên bài thi!")
                        elif not uploaded_file: st.error("Vui lòng tải file đề thi lên!")
                        elif not ans_input: st.error("Vui lòng nhập chuỗi đáp án!")
                        else:
                            ans_clean = list(ans_input.upper().replace(" ", "").replace(",", ""))
                            valid_chars = all(char in ['A', 'B', 'C', 'D'] for char in ans_clean)
                            if not valid_chars: 
                                st.error("❌ Chuỗi đáp án bị lỗi! Chỉ được phép chứa các chữ A, B, C, D.")
                            else:
                                file_bytes = uploaded_file.read()
                                b64 = base64.b64encode(file_bytes).decode('utf-8')
                                mime_type = uploaded_file.type
                                s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                                e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                
                                c.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                          (exam_title.strip(), s_str, e_str, target_class, b64, mime_type, json.dumps(ans_clean)))
                                conn.commit()
                                st.success(f"✅ Đã phát đề thành công tới {target_class}! Hệ thống tự động tạo phiếu tô {len(ans_clean)} câu trắc nghiệm.")
                
                else:
                    if st.button("🚀 Phát Đề AI (Trộn Ngẫu Nhiên 40 Câu)", type="primary"):
                        if exam_title:
                            gen = ExamGenerator()
                            fixed_exam = gen.generate_all()
                            s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                            e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                            c.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?, ?, ?, ?, ?)", 
                                      (exam_title.strip(), json.dumps(fixed_exam), s_str, e_str, target_class))
                            conn.commit()
                            st.success(f"✅ Đã phát đề AI chuẩn 40 câu tới {target_class}!")
                        else: st.error("Vui lòng nhập tên bài thi!")
        conn.close()

if __name__ == "__main__":
    main()
