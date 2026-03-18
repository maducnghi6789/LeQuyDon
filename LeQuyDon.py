# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN V20 SUPREME ULTIMATE (DYNAMIC API KEY)
# Cải tiến: Khung nhập API Key trực tiếp trên giao diện (Chống rò rỉ, chống lỗi 54)
# Giữ nguyên: Đồ họa SGK, Trộn đề độc bản, AI bóc tách PDF bằng File API
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
import time
import os
import tempfile
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone

# --- KẾT NỐI GEMINI AI THƯ VIỆN ---
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.5.2"])
        import google.generativeai as genai
        AI_AVAILABLE = True
    except:
        AI_AVAILABLE = False

VN_TZ = timezone(timedelta(hours=7))

# --- 🛡️ ĐỘNG CƠ AI QUÉT MẠNG VÀ PHÂN TÍCH (NHẬN API KEY ĐỘNG TỪ GIAO DIỆN) ---
def generate_ai_content_with_fallback(prompt, api_key, file_bytes=None, mime_type=None):
    if not AI_AVAILABLE:
        raise Exception("Hệ thống máy chủ chưa cài đặt thư viện google-generativeai.")
    if not api_key or len(api_key) < 20:
        raise Exception("API Key không hợp lệ. Vui lòng kiểm tra lại ô nhập Key ở Menu bên trái.")

    # Xác thực API Key trực tiếp
    genai.configure(api_key=api_key)

    # Danh sách các model AI để quét dự phòng liên hoàn
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro-vision',
        'gemini-pro'
    ]

    last_error = ""

    # KỊCH BẢN 1: XỬ LÝ FILE PDF/ẢNH (DÙNG UPLOAD API HOẶC INLINE)
    if file_bytes and mime_type:
        if "pdf" in mime_type.lower():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            uploaded_file = None
            try:
                uploaded_file = genai.upload_file(path=tmp_path, mime_type=mime_type)
                
                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(m_name)
                        res = model.generate_content([prompt, uploaded_file])
                        return res
                    except Exception as e:
                        last_error = str(e)
                        continue 
                        
                raise Exception(f"Google từ chối phân tích. Lỗi: {last_error}")
            finally:
                if uploaded_file:
                    try: genai.delete_file(uploaded_file.name)
                    except: pass
                try: os.remove(tmp_path)
                except: pass
        else:
            contents = [prompt, {"mime_type": mime_type, "data": file_bytes}]
            for m_name in models_to_try:
                try:
                    model = genai.GenerativeModel(m_name)
                    return model.generate_content(contents)
                except Exception as e:
                    last_error = str(e)
                    continue
            raise Exception(f"Lỗi phân tích Ảnh AI: {last_error}")
            
    # KỊCH BẢN 2: CHỈ CÓ VĂN BẢN (SINH ĐỀ TỰ LUYỆN)
    else:
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                return model.generate_content(prompt)
            except Exception as e:
                last_error = str(e)
                continue
        raise Exception(f"Lỗi Sinh đề AI: {last_error}")

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
# 3. ĐỒ HỌA TOÁN HỌC ĐỘNG CHUẨN SGK
# ==========================================
def fig_to_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def draw_dynamic_parabola(a_val):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    x = np.linspace(-3, 3, 100); y = a_val * x**2
    color = '#2980b9' if a_val > 0 else '#e74c3c'
    ax.plot(x, y, color=color, lw=2.5)
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xticks([]); ax.set_yticks([]) 
    ax.text(0.2, max(y)*0.9 if a_val>0 else min(y)*0.9, 'y', style='italic', fontsize=11)
    ax.text(3.2, 0.2, 'x', style='italic', fontsize=11)
    ax.text(-0.4, -0.4, 'O', fontsize=11)
    return fig_to_base64(fig)

def draw_dynamic_thales(AE, EB, AF, FC):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot([1.5, 0, 3, 1.5], [3, 0, 0, 3], 'k-', lw=1.5) 
    ax.plot([0.75, 2.25], [1.5, 1.5], 'b-', lw=1.5) 
    ax.text(1.5, 3.1, 'A', ha='center', fontsize=11, fontweight='bold')
    ax.text(-0.2, -0.1, 'B', fontsize=11, fontweight='bold')
    ax.text(3.1, -0.1, 'C', fontsize=11, fontweight='bold')
    ax.text(0.5, 1.5, 'E', ha='right', fontsize=11, fontweight='bold')
    ax.text(2.4, 1.5, 'F', ha='left', fontsize=11, fontweight='bold')
    ax.text(2.6, 2.3, '$EF // BC$', style='italic', fontsize=10)
    
    ax.text(0.6, 2.3, str(AE), color='red', fontsize=10, rotation=63)
    ax.text(0.2, 0.8, str(EB), color='red', fontsize=10, rotation=63)
    ax.text(2.0, 2.3, str(AF), color='red', fontsize=10, rotation=-63)
    ax.text(2.8, 0.8, str(FC), color='red', fontsize=10, rotation=-63)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_dynamic_altitude(BH, HC, AH):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot([0, 0, 4, 0], [0, 3, 0, 0], 'k-', lw=1.5) 
    ax.plot([0, 1.44], [0, 1.92], 'b-', lw=1.5) 
    ax.plot([0, 0.2, 0.2], [0.2, 0.2, 0], 'k-', lw=1) 
    ax.plot([1.3, 1.44, 1.58], [1.7, 1.92, 1.78], 'k-', lw=1) 
    ax.text(-0.3, -0.2, 'A', fontsize=11, fontweight='bold')
    ax.text(-0.3, 3.1, 'B', fontsize=11, fontweight='bold')
    ax.text(4.2, -0.2, 'C', fontsize=11, fontweight='bold')
    ax.text(1.6, 2.1, 'H', fontsize=11, fontweight='bold')
    
    ax.text(0.5, 2.6, str(BH), color='red', fontsize=10, rotation=-36)
    ax.text(2.8, 1.0, str(HC), color='red', fontsize=10, rotation=-36)
    ax.text(0.8, 0.8, str(AH), color='red', fontsize=10, rotation=53)
    ax.axis('off')
    return fig_to_base64(fig)

def draw_dynamic_shadow(h_cot, bong_cot, bong_cay):
    fig, ax = plt.subplots(figsize=(4.5, 2.5))
    ax.plot([0, 6.8], [0, 0], 'k-', lw=2) 
    ax.plot([0, 0], [0, 3.5], 'k-', lw=3) 
    ax.plot([3, 3], [0, 1.9], 'g-', lw=4) 
    ax.plot([0, 6.8], [3.5, 0], 'b-', lw=1) 
    ax.text(-0.3, 3.5, 'A', fontweight='bold')
    ax.text(-0.3, -0.3, 'B', fontweight='bold')
    ax.text(2.7, 2.0, 'C', fontweight='bold')
    ax.text(2.7, -0.3, 'D', fontweight='bold')
    ax.text(6.9, -0.1, 'M', fontweight='bold')
    
    ax.text(-0.8, 1.5, f"{h_cot}m", color='red')
    ax.text(1.5, -0.4, f"{bong_cot - bong_cay}m", color='red')
    ax.text(4.5, -0.4, f"{bong_cay}m", color='red')
    ax.axis('off')
    return fig_to_base64(fig)

# ==========================================
# 4. ĐỘNG CƠ SINH ĐỀ CHUYÊN SÂU 
# ==========================================
class ExamGenerator:
    def __init__(self, api_key):
        self.exam = []
        self.api_key = api_key

    def format_options(self, correct, distractors):
        opts = [correct] + distractors[:3]
        random.shuffle(opts)
        return opts

    def get_38_distinct_local_questions(self):
        pool = []
        ae = random.randint(2, 6); eb = random.randint(2, 6); af = random.randint(2, 6)
        fc = round((eb * af) / ae, 1)
        ans_q1 = str(int(fc)) if fc.is_integer() else str(fc)
        pool.append({"q": "Quan sát hình vẽ, biết $EF // BC$. Theo định lý Thales, độ dài đoạn $FC$ ($x$) bằng bao nhiêu?", "opts": self.format_options(ans_q1, [str(round(fc+1, 1)), str(round(fc+0.5, 1)), str(round(fc-1, 1))]), "a": ans_q1, "h": "Tỉ số Thales: AE/EB = AF/FC.", "i_svg": "", "i": draw_dynamic_thales(ae, eb, af, 'x')})
        
        bh = random.choice([2, 4, 9]); hc = random.choice([3, 4, 16])
        ah = round(math.sqrt(bh * hc), 1)
        ans_q2 = str(int(ah)) if ah.is_integer() else str(ah)
        pool.append({"q": f"Cho $\\Delta ABC$ vuông tại $A$, có đường cao $AH = h$. Biết $BH = {bh}$ và $HC = {hc}$. Tính độ dài $h$.", "opts": self.format_options(ans_q2, [str(round(ah+2, 1)), str(round(ah+1, 1)), str(round(ah-1, 1))]), "a": ans_q2, "h": "$AH^2 = BH \\cdot HC$.", "i_svg": "", "i": draw_dynamic_altitude(bh, hc, 'h')})
        
        h_cot = random.choice([8, 10, 12]); b_cay = random.choice([3, 4]); dist = random.choice([2, 4])
        b_cot = b_cay + dist
        h_cay = round((h_cot * b_cay) / b_cot, 1)
        ans_q3 = f"{str(int(h_cay)) if h_cay.is_integer() else str(h_cay)} m"
        pool.append({"q": f"Một cột đèn $AB$ cao {h_cot}m có bóng trên mặt đất dài {b_cot}m. Cùng lúc đó, bóng của cây $CD$ dài {b_cay}m. Chiều cao của cây là:", "opts": self.format_options(ans_q3, [f"{round(h_cay+1,1)} m", f"{round(h_cay+0.5,1)} m", f"{round(h_cay-0.5,1)} m"]), "a": ans_q3, "h": "Hai tam giác tạo bởi tia sáng đồng dạng.", "i_svg": "", "i": draw_dynamic_shadow(h_cot, b_cot, b_cay)})

        a_val = random.choice([1, 2, -1, -2])
        ans_q4 = r"$a > 0$" if a_val > 0 else r"$a < 0$"
        pool.append({"q": "Quan sát đồ thị hàm số $y = ax^2$ dưới đây. Khẳng định nào sau đây là ĐÚNG về hệ số $a$?", "opts": self.format_options(ans_q4, [r"$a < 0$" if a_val > 0 else r"$a > 0$", "Hàm số luôn đồng biến", "Đồ thị đi qua điểm (0; 2)"]), "a": ans_q4, "h": "Bề lõm quay lên thì a > 0.", "i_svg": "", "i": draw_dynamic_parabola(a_val)})

        num = random.choice([16, 25, 36, 49, 64, 81])
        ans_q5 = str(int(math.sqrt(num)))
        pool.append({"q": f"Căn bậc hai số học của {num} là:", "opts": self.format_options(ans_q5, [f"-{ans_q5}", str(num**2), "Cả âm và dương"]), "a": ans_q5, "h": "Căn số học luôn không âm", "i_svg": "", "i": None})
        pool.append({"q": "Biểu thức $\\sqrt{(x-3)^2}$ sau khi rút gọn bằng:", "opts": self.format_options("$|x-3|$", ["$x-3$", "$\\pm(x-3)$", "$3-x$"]), "a": "$|x-3|$", "h": "$\\sqrt{A^2} = |A|$", "i_svg": "", "i": None})

        lai = random.choice([5, 6, 7])
        ans_q7 = f"{int(100 * (1 + lai/100)**2)} triệu"
        pool.append({"q": f"Bác Tư gửi 100 triệu VNĐ, lãi kép {lai}%/năm. Sau 2 năm bác nhận được tổng số tiền (làm tròn) là:", "opts": self.format_options(ans_q7, [f"{int(100 * (1 + lai/100))} triệu", f"{100 + lai*2} triệu", f"{int(100 * (1 + lai/100)**2) + 2} triệu"]), "a": ans_q7, "h": "Dùng công thức lãi kép", "i_svg": "", "i": None})

        v1 = 40; v2 = 60; t = 2
        ans_q8 = f"{v1+v2} km/h"
        pool.append({"q": f"Hai ô tô xuất phát cùng lúc và đi ngược chiều trên quãng đường AB dài {(v1+v2)*t} km. Chúng gặp nhau sau {t} giờ. Tổng vận tốc hai xe là:", "opts": self.format_options(ans_q8, [f"{(v1+v2)*t} km/h", f"{(v1+v2)/t} km/h", f"{v1+v2+10} km/h"]), "a": ans_q8, "h": "$v_1 + v_2 = S/t$", "i_svg": "", "i": None})

        pool.append({"q": "Gieo đồng thời hai con xúc xắc cân đối và đồng chất. Xác suất để tổng số chấm trên hai mặt bằng 7 là:", "opts": self.format_options("1/6", ["5/36", "1/12", "7/36"]), "a": "1/6", "h": "Có 6 biến cố: (1,6), (2,5), (3,4)...", "i_svg": "", "i": None})
        pool.append({"q": "Đường thẳng đi qua hai điểm $A(0; 2)$ và $B(1; 4)$ có phương trình là:", "opts": self.format_options("$y = 2x + 2$", ["$y = x + 2$", "$y = 2x - 2$", "$y = 4x$"]), "a": "$y = 2x + 2$", "h": "Lập hệ phương trình tìm a, b", "i_svg": "", "i": None})
        pool.append({"q": "Nghiệm $(x; y)$ của hệ phương trình $\\begin{cases} 2x - y = 1 \\\\ x + y = 5 \\end{cases}$ là:", "opts": self.format_options("$(2; 3)$", ["$(3; 2)$", "$(1; 4)$", "$(4; 1)$"]), "a": "$(2; 3)$", "h": "Cộng hai vế", "i_svg": "", "i": None})
        pool.append({"q": "Cho tứ giác $ABCD$ nội tiếp đường tròn. Nếu góc $\\angle A = 75^\\circ$ thì góc đối diện $\\angle C$ bằng:", "opts": self.format_options("$105^\\circ$", ["$75^\\circ$", "$100^\\circ$", "$85^\\circ$"]), "a": "$105^\\circ$", "h": "Tổng hai góc đối bằng 180", "i_svg": "", "i": None})
        pool.append({"q": "Công thức tính thể tích của khối nón có bán kính đáy $r$ và chiều cao $h$ là:", "opts": self.format_options("$V = \\frac{1}{3}\\pi r^2 h$", ["$V = \\pi r^2 h$", "$V = \\frac{4}{3}\\pi r^3$", "$V = 2\\pi r h$"]), "a": "$V = \\frac{1}{3}\\pi r^2 h$", "h": "Công thức cơ bản SGK", "i_svg": "", "i": None})
        pool.append({"q": "Độ dài cung tròn $60^\\circ$ của đường tròn bán kính $R = 6$ cm là:", "opts": self.format_options("$2\\pi$ cm", ["$6\\pi$ cm", "$3\\pi$ cm", "$12\\pi$ cm"]), "a": "$2\\pi$ cm", "h": "$l = \\frac{\\pi R n}{180}$", "i_svg": "", "i": None})

        S = random.randint(3, 7); P = random.randint(-2, 3)
        ans_q15 = str(S**2 - 2*P)
        pool.append({"q": f"Biết phương trình bậc hai có hai nghiệm thỏa mãn $x_1+x_2={S}$ và $x_1x_2={P}$. Giá trị của $x_1^2 + x_2^2$ là:", "opts": self.format_options(ans_q15, [str(S**2 + 2*P), str(S**2), str(S**2 - P)]), "a": ans_q15, "h": "$S^2 - 2P$", "i_svg": "", "i": None})

        diverse_templates = [
            ("Tập nghiệm của phương trình $x^4 - 5x^2 + 4 = 0$ là:", "$\\pm 1, \\pm 2$", ["$1, 4$", "$\\pm 1, 2$", "Vô nghiệm"]),
            ("Hệ số góc của đường thẳng $3x + 2y - 5 = 0$ là:", "$-1.5$", ["1.5", "3", "2"]),
            ("Giá trị của $\\sin 30^\\circ + \\cos 60^\\circ$ là:", "1", ["$0$", "$\\sqrt{3}$", "$\\frac{1}{2}$"]),
            ("Tâm đường tròn ngoại tiếp tam giác vuông nằm ở đâu?", "Trung điểm cạnh huyền", ["Trực tâm", "Trọng tâm", "Giao 3 đường phân giác"]),
            ("Phương trình nào sau đây là phương trình bậc nhất hai ẩn?", "$2x - 3y = 5$", ["$x^2 - y = 0$", "$x + y^2 = 1$", "$\\frac{1}{x} + y = 2$"]),
            ("Hàm số $y = \\sqrt{m-2} \\cdot x + 3$ là hàm số bậc nhất khi:", "$m > 2$", ["$m \\ge 2$", "$m < 2$", "$m \\ne 2$"]),
            ("Số đo góc tạo bởi tiếp tuyến và dây cung bằng:", "Nửa số đo cung bị chắn", ["Số đo cung bị chắn", "Số đo góc ở tâm", "Gấp đôi số đo cung"]),
            ("Diện tích mặt cầu bán kính $R=3$ là:", "$36\\pi$", ["$12\\pi$", "$27\\pi$", "$9\\pi$"]),
            ("Điều kiện để phương trình $ax^2 + bx + c = 0$ (a khác 0) có 2 nghiệm phân biệt là:", "$\\Delta > 0$", ["$\\Delta \\ge 0$", "$\\Delta = 0$", "$\\Delta < 0$"]),
            ("Cho $\\Delta ABC$ đều cạnh $a$. Chiều cao của tam giác là:", "$\\frac{a\\sqrt{3}}{2}$", ["$\\frac{a}{2}$", "$a\\sqrt{3}$", "$\\frac{a\\sqrt{2}}{2}$"]),
            ("Biểu thức $\\sqrt{A^2}$ luôn bằng:", "$|A|$", ["A", "-A", "$\\pm A$"]),
            ("Giao điểm của hai đường cao trong tam giác gọi là:", "Trực tâm", ["Trọng tâm", "Tâm đường tròn nội tiếp", "Tâm đường tròn ngoại tiếp"]),
            ("Với góc nhọn $\\alpha$, hệ thức nào SAI?", "$\\sin^2\\alpha - \\cos^2\\alpha = 1$", ["$\\sin^2\\alpha + \\cos^2\\alpha = 1$", "$\\tan\\alpha = \\frac{\\sin\\alpha}{\\cos\\alpha}$", "$\\tan\\alpha \\cdot \\cot\\alpha = 1$"]),
            ("Đồ thị hàm số $y = 2x - 4$ cắt trục hoành tại điểm có hoành độ là:", "2", ["-4", "-2", "4"]),
            ("Hai đường thẳng $y = 2x+1$ và $y = 2x-3$ có vị trí tương đối là:", "Song song", ["Cắt nhau", "Trùng nhau", "Vuông góc"]),
            ("Diện tích hình quạt tròn bán kính R, cung $n^\\circ$ là:", "$\\frac{\\pi R^2 n}{360}$", ["$\\frac{\\pi R n}{180}$", "$\\frac{\\pi R^2 n}{180}$", "$\\pi R^2$"]),
            ("Căn bậc ba của -27 là:", "-3", ["3", "Không tồn tại", "$\\pm 3$"]),
            ("Rút gọn $\\sqrt{8} - \\sqrt{2}$ ta được:", "$\\sqrt{2}$", ["$\\sqrt{6}$", "$2\\sqrt{2}$", "4"]),
            ("Một vòi nước chảy đầy bể trong 6 giờ. Trong 1 giờ vòi đó chảy được:", "1/6 bể", ["6 bể", "1/3 bể", "2/3 bể"]),
            ("Phương trình $\\frac{x}{2} + \\frac{y}{3} = 1$ có bao nhiêu nghiệm?", "Vô số nghiệm", ["1 nghiệm", "2 nghiệm", "Vô nghiệm"]),
            ("Cho $x > 0$. Rút gọn $x \\sqrt{\\frac{1}{x}}$ ta được:", "$\\sqrt{x}$", ["x", "1", "$\\frac{1}{x}$"]),
            ("Tứ giác có 4 đỉnh nằm trên đường tròn gọi là:", "Tứ giác nội tiếp", ["Hình vuông", "Hình bình hành", "Hình thoi"]),
            ("Phân tích đa thức $x^2 - y^2$ thành nhân tử:", "$(x-y)(x+y)$", ["$(x-y)^2$", "$(x+y)^2$", "$x(x-y)$"])
        ]
        
        for tpl in diverse_templates:
            pool.append({"q": tpl[0], "opts": self.format_options(tpl[1], tpl[2]), "a": tpl[1], "h": "Lý thuyết Toán 9.", "i_svg": "", "i": None})
            if len(pool) == 38: break

        return pool

    def generate_all(self):
        ai_questions = []
        if self.api_key:
            try:
                seed = time.time()
                prompt = f"""Mốc thời gian: {seed}. 
                Đóng vai Chuyên gia Tuyển sinh Toán học. Sáng tạo 5 CÂU HỎI trắc nghiệm Toán 9 thực tiễn đa dạng.
                YÊU CẦU:
                1. TUYỆT ĐỐI KHÔNG GHI NHÃN ĐỘ KHÓ. Nội dung đi thẳng vào câu hỏi.
                2. Với câu hỏi cần hình SVG: Phải dùng thẻ viewBox. Chữ số BẮT BUỘC dùng dx, dy để cách xa nét vẽ.
                3. Trả về ĐÚNG JSON nguyên khối: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "...", "hint": "...", "image_svg": ""}}]"""
                
                res = generate_ai_content_with_fallback(prompt, self.api_key)
                raw_text = re.sub(r'```json\n?', '', res.text)
                raw_text = re.sub(r'```\n?', '', raw_text)
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                
                if match:
                    parsed_q = json.loads(match.group())
                    for q in parsed_q:
                        q_text = re.sub(r'\[.*?\]\s*', '', q.get("question", "")).strip()
                        opts = q.get("options", [])
                        random.shuffle(opts)
                        ai_questions.append({
                            "q": q_text, "opts": opts, "a": q.get("answer", ""), 
                            "h": q.get("hint", ""), "i_svg": q.get("image_svg", ""), "i": None
                        })
            except Exception:
                pass 

        local_distinct_pool = self.get_38_distinct_local_questions()
        
        if ai_questions:
            num_ai = min(len(ai_questions), 10)
            final_pool = ai_questions[:num_ai] + local_distinct_pool[:38 - num_ai]
        else:
            final_pool = local_distinct_pool[:38]

        hsg_bank = [
            {"q": "Cho các số thực dương $a, b, c$ thỏa mãn $a^2+b^2+c^2=3$. Tìm giá trị nhỏ nhất của biểu thức $P = \\frac{a^3}{\\sqrt{b^2+3}} + \\frac{b^3}{\\sqrt{c^2+3}} + \\frac{c^3}{\\sqrt{a^2+3}}$.", "a": r"$\frac{3}{2}$", "d": [r"1", r"$\frac{1}{2}$", r"3"], "h": "Sử dụng BĐT AM-GM và Bunhiacopxki."},
            {"q": "Tìm tất cả các nghiệm nguyên $(x, y)$ thỏa mãn phương trình: $x^3 + y^3 = (x+y)^2$.", "a": "4 cặp: (0,0), (1,0), (0,1), (2,2)", "d": ["2 cặp", "Vô số cặp", "Vô nghiệm"], "h": "Phân tích $(x+y)(x^2-xy+y^2 - x - y) = 0$."},
            {"q": "Trên bảng viết 2026 số 1. Mỗi lần cho phép xóa 2 số a, b bất kỳ và viết lại bằng số $a+b+ab$. Hỏi sau 2025 lần thực hiện, số còn lại trên bảng là bao nhiêu?", "a": "$2^{2026} - 1$", "d": ["$2026!$", "$2026^2$", "$2^{2025}$"], "h": "Dùng tính chất bất biến: $(a+1)(b+1) - 1 = a+b+ab$."},
            {"q": "Giải phương trình vô tỷ: $\\sqrt{x - \\frac{1}{x}} - \\sqrt{1 - \\frac{1}{x}} = \\frac{x-1}{x}$.", "a": "$x = \\frac{1+\\sqrt{5}}{2}$", "d": ["$x = 2$", "$x = 1$", "Vô nghiệm"], "h": "Điều kiện $x \\ge 1$. Nhân lượng liên hợp 2 vế."}
        ]
        selected_hsg_raw = random.sample(hsg_bank, 2)
        hsg_questions = [{"q": q["q"], "opts": self.format_options(q["a"], q["d"]), "a": q["a"], "h": q["h"], "i_svg": "", "i": None} for q in selected_hsg_raw]

        final_pool.extend(hsg_questions)
        random.shuffle(final_pool)

        for i, q in enumerate(final_pool[:40]):
            self.exam.append({
                "id": i + 1, "question": q["q"], "options": q["opts"],
                "answer": q["a"], "hint": q["h"], "image_svg": q["i_svg"], "image": q["i"]
            })
            
        return self.exam

# ==========================================
# 5. GIAO DIỆN HỆ THỐNG V20
# ==========================================
def main():
    st.set_page_config(page_title="Hệ Thống LMS V20", layout="wide", page_icon="🏫")
    init_db()
    
    # KHOẢNG TRỐNG LƯU API KEY CHO PHIÊN LÀM VIỆC
    if 'dynamic_api_key' not in st.session_state:
        st.session_state.dynamic_api_key = ""
        
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

    # --- SIDEBAR CẢI TIẾN: NHẬP API KEY TẠI ĐÂY ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        role_map = {"core_admin": "👑 Giám Đốc", "sub_admin": "🛡 Admin", "teacher": "👨‍🏫 Giáo viên", "student": "🎓 Học sinh"}
        st.markdown(f"**Vai trò:** {role_map.get(st.session_state.role, '')}")
        
        # CHỖ NHẬP API KEY MỚI (An toàn, bảo mật)
        if st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
            st.markdown("---")
            st.markdown("### 🤖 Cấu hình Trí tuệ Nhân tạo")
            api_input = st.text_input("🔑 Nhập API Key Gemini (Bảo mật):", type="password", value=st.session_state.dynamic_api_key)
            if api_input != st.session_state.dynamic_api_key:
                st.session_state.dynamic_api_key = api_input
                st.success("Đã nạp chìa khóa AI!")
        
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

        st.markdown("---")
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
                            if f"mand_ans_{exam_id}" not in st.session_state:
                                st.session_state[f"mand_ans_{exam_id}"] = {str(i+1): None for i in range(num_q)}
                            
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
                            
                            if q.get('image_svg'):
                                st.markdown(f"<div style='margin: 15px 0; display:flex; justify-content:center;'>{q['image_svg']}</div>", unsafe_allow_html=True)
                            elif q.get('image'): 
                                st.markdown(f'<div style="text-align:left;"><img src="data:image/png;base64,{q["image"]}" style="max-width:350px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
                            
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
                        
                        if pd.notnull(exam_row.get('questions_json')) and exam_row.get('questions_json') != "":
                            st.markdown("---")
                            st.markdown("#### 💡 Lời giải chi tiết")
                            try:
                                ai_hints = json.loads(exam_row['questions_json'])
                                for q in ai_hints:
                                    with st.expander(f"Câu {q['id']}: Xem lời giải"):
                                        st.markdown(q.get('hint', 'Chưa có lời giải.'))
                            except: pass
                    else:
                        mand_exam_data = json.loads(exam_row['questions_json'])
                        for q in mand_exam_data:
                            q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                            st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                            if q.get('image_svg'):
                                st.markdown(f"<div style='margin: 15px 0; display:flex; justify-content:center;'>{q['image_svg']}</div>", unsafe_allow_html=True)
                            elif q.get('image'): 
                                st.markdown(f'<div style="text-align:left;"><img src="data:image/png;base64,{q["image"]}" style="max-width:350px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
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
            if 'exam_data' not in st.session_state: st.session_state.exam_data = None
            if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
            if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

            if st.button("🔄 TẠO ĐỀ LUYỆN TẬP MỚI", use_container_width=True):
                with st.spinner("Đang xáo trộn dữ liệu và vẽ đồ họa chuẩn SGK..."):
                    # CHỖ NÀY AI DÙNG KEY ĐỘNG TỪ SIDEBAR ĐỂ SINH CÂU HỎI MỚI
                    gen = ExamGenerator(st.session_state.dynamic_api_key)
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
                    q_text = re.sub(r'\[.*?\]\s*', '', q['question']).strip()
                    st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                    
                    if q.get('image_svg'):
                        st.markdown(f"<div style='margin: 15px 0; display:flex; justify-content:center;'>{q['image_svg']}</div>", unsafe_allow_html=True)
                    elif q.get('image'): 
                        st.markdown(f'<div style="text-align:left;"><img src="data:image/png;base64,{q["image"]}" style="max-width:350px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
                    
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
                
                uploaded_file = st.file_uploader("1. Tải File Đề (Hỗ trợ PDF, JPG, PNG)", type=['pdf', 'jpg', 'png', 'jpeg'])
                
                pdf_method = st.radio("2. Phương thức tạo Đáp án & Lời giải:", ["✍️ Nhập chuỗi đáp án thủ công", "🤖 AI tự động đọc file và tạo (Khuyên dùng)"])
                
                if pdf_method == "✍️ Nhập chuỗi đáp án thủ công":
                    ans_input = st.text_input("Nhập chuỗi Đáp án Đúng (Viết liền, VD: ABCDABCD)")
                    if st.button("🚀 Phát Đề (Thủ công)", type="primary"):
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
                                s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                                e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                c.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                          (exam_title.strip(), s_str, e_str, target_class, b64, uploaded_file.type, json.dumps(ans_clean)))
                                conn.commit()
                                st.success(f"✅ Đã phát đề thành công tới {target_class}! Học sinh sẽ tô phiếu trắc nghiệm {len(ans_clean)} câu.")
                else:
                    if 'pdf_ai_preview' not in st.session_state: st.session_state.pdf_ai_preview = None
                    
                    if st.button("🤖 Phân tích Đề bằng AI", type="primary"):
                        if not exam_title: 
                            st.error("Vui lòng nhập tên bài thi!")
                        elif not uploaded_file: 
                            st.error("Vui lòng tải file đề thi lên!")
                        elif not st.session_state.dynamic_api_key: 
                            st.error("❌ Bạn chưa nhập API Key ở Menu bên trái!")
                        else:
                            with st.spinner("AI đang đọc tài liệu và phân tích đáp án chuyên sâu..."):
                                try:
                                    uploaded_file.seek(0)
                                    file_bytes = uploaded_file.read()
                                    prompt = "Đọc đề thi này (PDF/Ảnh). Trích xuất toàn bộ câu hỏi thành danh sách JSON. Cấu trúc BẮT BUỘC: [{'id': 1, 'question': 'nội dung', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'hint': 'Lời giải chi tiết từng bước'}]. LƯU Ý: Trường 'answer' CHỈ ĐƯỢC chứa 1 CHỮ CÁI A, B, C hoặc D. TUYỆT ĐỐI không xuất định dạng Markdown ```json."
                                    
                                    # Gọi AI với key nhập từ UI
                                    res = generate_ai_content_with_fallback(prompt, st.session_state.dynamic_api_key, file_bytes, uploaded_file.type)
                                    
                                    raw_text = re.sub(r'```json\n?', '', res.text)
                                    raw_text = re.sub(r'```\n?', '', raw_text)
                                    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                                    
                                    if match:
                                        st.session_state.pdf_ai_preview = json.loads(match.group())
                                        st.rerun()
                                    else:
                                        st.error("AI không thể bóc tách được định dạng file này. Hãy đảm bảo ảnh/pdf rõ nét.")
                                except Exception as e:
                                    st.error(f"Lỗi AI: {str(e)}")
                                    
                    if st.session_state.pdf_ai_preview:
                        st.success("✅ AI đã hoàn tất bóc tách! Mời thầy/cô soát duyệt:")
                        ans_key_ai = []
                        with st.expander("🔍 XEM TRƯỚC ĐÁP ÁN & LỜI GIẢI AI SOẠN", expanded=True):
                            for q in st.session_state.pdf_ai_preview:
                                st.markdown(f"**Câu {q['id']}:** {q.get('question','')}")
                                ans_letter = re.sub(r'[^A-D]', '', str(q.get('answer', 'A')).upper())
                                final_ans = ans_letter[0] if ans_letter else 'A'
                                ans_key_ai.append(final_ans)
                                
                                st.markdown(f"- ✅ **Đáp án đúng:** {final_ans}")
                                st.markdown(f"- 💡 **Lời giải:** {q.get('hint','')}")
                                st.markdown("---")
                        
                        col_d, col_h = st.columns(2)
                        with col_d:
                            if st.button("🚀 XÁC NHẬN PHÁT ĐỀ NÀY", use_container_width=True):
                                uploaded_file.seek(0)
                                file_bytes = uploaded_file.read()
                                b64 = base64.b64encode(file_bytes).decode('utf-8')
                                s_str = f"{s_date} {s_time.strftime('%H:%M:%S')}"
                                e_str = f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                
                                c.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key, questions_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                          (exam_title.strip(), s_str, e_str, target_class, b64, uploaded_file.type, json.dumps(ans_key_ai), json.dumps(st.session_state.pdf_ai_preview)))
                                conn.commit()
                                st.session_state.pdf_ai_preview = None
                                st.success(f"✅ Đã phát đề thành công! Học sinh sẽ làm bài trên file và có thể xem lời giải chi tiết sau khi nộp.")
                                time.sleep(1); st.rerun()
                        with col_h:
                            if st.button("❌ Hủy & Thử lại", use_container_width=True):
                                st.session_state.pdf_ai_preview = None
                                st.rerun()
                
                else:
                    if st.button("🚀 Phát Đề AI (Trộn Ngẫu Nhiên 40 Câu)", type="primary"):
                        if not st.session_state.dynamic_api_key:
                            st.error("❌ Bạn chưa nhập API Key ở Menu bên trái!")
                        elif exam_title:
                            gen = ExamGenerator(st.session_state.dynamic_api_key)
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
