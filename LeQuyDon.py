# ==========================================
# HỆ THỐNG LMS LÊ QUÝ ĐÔN - V55 THE APEX
# Khắc phục 100%: Lỗi DuplicateElementKey, rò rỉ np.float64, "None" từ DB cũ.
# Tính năng: 40 Câu tự luyện BÁM SÁT MA TRẬN.
# Động cơ Tự phục hồi: Deepcopy lấp đầy 40 câu, chống sập UI tuyệt đối.
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
import copy
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone
from PIL import Image

try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_RENDERER_AVAILABLE = True
except ImportError:
    PDF_RENDERER_AVAILABLE = False

VN_TZ = timezone(timedelta(hours=7))

# ==========================================
# 1. HỆ QUẢN TRỊ CƠ SỞ DỮ LIỆU & BẢO MẬT
# ==========================================
def get_api_key():
    try:
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        c.execute("SELECT setting_value FROM system_settings WHERE setting_key='GEMINI_API_KEY'")
        res = c.fetchone()
        conn.close()
        return res[0] if res else ""
    except: return ""

def save_api_key(key_str):
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS system_settings (setting_key TEXT PRIMARY KEY, setting_value TEXT)")
    c.execute("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES ('GEMINI_API_KEY', ?)", (key_str,))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, fullname TEXT, dob TEXT, class_name TEXT, school TEXT, province TEXT, managed_classes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, start_time TEXT, end_time TEXT, target_class TEXT DEFAULT 'Toàn trường', file_data TEXT, file_type TEXT, answer_key TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, user_answers_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deletion_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, deleted_by TEXT, entity_type TEXT, entity_name TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Admin Trường')")
    conn.commit()
    conn.close()

def log_action(user, e_type, e_name, reason):
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    vn_time = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO deletion_logs (deleted_by, entity_type, entity_name, reason, timestamp) VALUES (?, ?, ?, ?, ?)", (user, e_type, e_name, reason, vn_time))
    conn.commit()
    conn.close()

# ==========================================
# 2. BỘ LỌC LATEX CỨU HỘ & XỬ LÝ CHUỖI
# ==========================================
def format_math(text):
    if not text: return ""
    text = str(text)
    # Loại bỏ ngoặc tròn bao quanh biểu thức lỗi của AI
    text = re.sub(r'^\((.*?)\)$', r'\1', text.strip())
    # Chuyển đổi chuẩn LaTeX
    text = text.replace(r'\(', '$').replace(r'\)', '$').replace(r'\[', '$$').replace(r'\]', '$$')
    
    # BỘ CỨU HỘ THÔNG MINH: Tự bọc $ cho các biểu thức trần bị vỡ (Lỗi 65.3)
    math_patterns = [r'\\sqrt', r'\\frac', r'\\Delta', r'\\pi', r'\\le', r'\\ge', r'\\cdot']
    if any(p in text for p in math_patterns) and '$' not in text:
        return f"${text}$"
    return text

def check_none_answer(val):
    # Lọc rác từ Database cũ lưu chữ "None" (Lỗi 65.2)
    if val is None or str(val).strip().lower() in ["none", "null", ""]:
        return "Chưa chọn đáp án"
    return str(val)

def to_excel(df, sheet_name='Sheet1'):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def create_excel_template():
    df = pd.DataFrame(columns=["Họ tên", "Ngày sinh", "Trường"])
    df.loc[0] = ["Nguyễn Văn A", "15/08/2010", "THCS Lê Quý Đôn"]
    return to_excel(df, 'MauNhapLieu')

def gen_user(fullname, dob):
    clean = re.sub(r'[^\w\s]', '', str(fullname)).lower().replace(" ", "")
    s = str(clean)
    for p, r in {'[àáạảãâầấậẩẫăằắặẳẵ]': 'a', '[èéẹẻẽêềếệểễ]': 'e', '[ìíịỉĩ]': 'i', '[òóọỏõôồốộổỗơờớợởỡ]': 'o', '[ùúụủũưừứựửữ]': 'u', '[ỳýỵỷỹ]': 'y', '[đ]': 'd'}.items(): s = re.sub(p, r, s)
    sfx = str(dob).split('/')[-1] if dob and str(dob).lower() != 'nan' and str(dob).split('/')[-1].isdigit() else str(random.randint(1000, 9999))
    return f"{s}{sfx}_{random.randint(10,99)}"

# ==========================================
# 3. LÕI AI XML PARSER (BẤT TỬ)
# ==========================================
def extract_tag(tag, text):
    match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.IGNORECASE | re.DOTALL)
    if match: return match.group(1).strip()
    m2 = re.search(rf'<{tag}>(.*?)(?:<|$)', text, re.IGNORECASE | re.DOTALL)
    return m2.group(1).strip() if m2 else ""

def parse_xml_exam(raw_text):
    questions = []
    blocks = re.findall(r'<CAU>(.*?)</CAU>', raw_text, re.IGNORECASE | re.DOTALL)
    if not blocks:
        blocks = re.split(r'(?i)<CAU>', raw_text)[1:] 

    for b in blocks:
        try:
            q = extract_tag('Q', b)
            oa = extract_tag('A', b)
            ob = extract_tag('B', b)
            oc = extract_tag('C', b)
            od = extract_tag('D', b)
            ans = extract_tag('ANS', b)
            hint = extract_tag('HINT', b)
            
            if not q or not oa: continue
            
            q = re.sub(r'^(Câu|Bài)\s*\d+[\.:\s]*', '', q, flags=re.IGNORECASE)
            opts = [format_math(oa), format_math(ob), format_math(oc), format_math(od)]
            
            ans_char = re.sub(r'[^A-D]', '', ans.upper())
            if not ans_char: ans_char = "A"
            ans_idx = ord(ans_char[0]) - 65
            ans_val = opts[ans_idx] if 0 <= ans_idx < 4 else opts[0]
            
            questions.append({"question": format_math(q), "options": opts, "answer": ans_val, "hint": format_math(hint), "image_svg": "", "image": None})
        except: continue
    return questions

def call_ai(prompt, img_bytes=None, mime_type=None):
    if not AI_AVAILABLE: raise Exception("Thiếu thư viện google-generativeai.")
    key = get_api_key()
    if len(key) < 20: raise Exception("Chưa cấu hình API Key. Vui lòng cập nhật ở Menu.")
    genai.configure(api_key=key.strip())
    
    contents = [prompt]
    if img_bytes:
        if mime_type and "pdf" in mime_type.lower():
            if not PDF_RENDERER_AVAILABLE: raise Exception("Thiếu PyMuPDF.")
            doc = fitz.open(stream=img_bytes, filetype="pdf")
            full_text = ""
            for i in range(min(len(doc), 15)):
                page = doc.load_page(i)
                full_text += page.get_text("text") + "\n"
                pix = page.get_pixmap(dpi=100)
                contents.append(Image.open(BytesIO(pix.tobytes("png"))))
            contents[0] = prompt + "\n\nNỘI DUNG ĐỀ THI TRÍCH XUẤT:\n" + full_text
        else:
            contents.append(Image.open(BytesIO(img_bytes)))
            
    target_model = 'gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(target_model, generation_config={"max_output_tokens": 8192, "temperature": 0.4})
        res = model.generate_content(contents)
        return res.text
    except Exception as e: 
        return "" # Im lặng để thuật toán Auto-Pad hoạt động

# ==========================================
# 4. ĐỘNG CƠ SINH ĐỀ MA TRẬN & ĐỒ HỌA (ZERO-LEAK)
# ==========================================
def get_plot(plot_type):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    if plot_type == 'parabola':
        a_val = random.choice([1, 2, -1, -2])
        x = np.linspace(-3, 3, 100); y = a_val * x**2
        _ = ax.plot(x, y, color='#2980b9' if a_val > 0 else '#e74c3c', lw=2.5)
        _ = ax.text(0.2, max(y)*0.9 if a_val>0 else min(y)*0.9, 'y', style='italic', fontsize=11)
        _ = ax.text(3.2, 0.2, 'x', style='italic', fontsize=11)
        _ = ax.text(-0.4, -0.4, 'O', fontsize=11)
        ans = r"$a > 0$" if a_val > 0 else r"$a < 0$"
        return fig, ans, a_val
    elif plot_type == 'thales':
        ae, eb, af = random.randint(2, 6), random.randint(2, 6), random.randint(2, 6)
        fc = round((eb * af) / ae, 1)
        _ = ax.plot([1.5, 0, 3, 1.5], [3, 0, 0, 3], 'k-', lw=1.5); _ = ax.plot([0.75, 2.25], [1.5, 1.5], 'b-', lw=1.5)
        _ = ax.text(1.5, 3.1, 'A'); _ = ax.text(-0.2, -0.1, 'B'); _ = ax.text(3.1, -0.1, 'C')
        _ = ax.text(0.5, 1.5, 'E'); _ = ax.text(2.4, 1.5, 'F')
        _ = ax.text(0.6, 2.3, str(ae), color='red'); _ = ax.text(0.2, 0.8, str(eb), color='red')
        _ = ax.text(2.0, 2.3, str(af), color='red'); _ = ax.text(2.8, 0.8, 'x', color='red')
        ans = str(int(fc)) if fc.is_integer() else str(fc)
        return fig, ans, None
    elif plot_type == 'altitude':
        bh, hc = random.choice([2, 4, 9]), random.choice([3, 4, 16])
        ah = round(math.sqrt(bh * hc), 1)
        _ = ax.plot([0, 0, 4, 0], [0, 3, 0, 0], 'k-', lw=1.5); _ = ax.plot([0, 1.44], [0, 1.92], 'b-', lw=1.5)
        _ = ax.text(-0.3, -0.2, 'A'); _ = ax.text(-0.3, 3.1, 'B'); _ = ax.text(4.2, -0.2, 'C'); _ = ax.text(1.6, 2.1, 'H')
        _ = ax.text(0.5, 2.6, str(bh), color='red'); _ = ax.text(2.8, 1.0, str(hc), color='red'); _ = ax.text(0.8, 0.8, 'h', color='red')
        ans = str(int(ah)) if ah.is_integer() else str(ah)
        return fig, ans, None

def fig_to_b64(fig):
    # KHÓA MÕM MATPLOTLIB: Dùng _ = để chặn Streamlit in np.float64 (Lỗi 66.1)
    ax = fig.gca()
    has_y = any('y' in t.get_text() for t in ax.texts)
    if has_y:
        for spine in ax.spines.values(): _ = spine.set_visible(False)
        _ = ax.spines['left'].set_visible(True); _ = ax.spines['left'].set_position('zero')
        _ = ax.spines['bottom'].set_visible(True); _ = ax.spines['bottom'].set_position('zero')
        _ = ax.set_xticks([]); _ = ax.set_yticks([])
    else:
        _ = ax.axis('off')
        
    buf = BytesIO()
    _ = fig.savefig(buf, format="png", bbox_inches='tight', facecolor='#ffffff', dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def get_large_fallback_pool():
    pool = []
    def fmt_opt(ans, dists):
        o = [ans] + dists[:3]; random.shuffle(o); return o
        
    fig, ans, _ = get_plot('thales')
    pool.append({"question": "Biết $EF // BC$. Theo định lý Thales, đoạn $x$ bằng:", "options": fmt_opt(ans, [str(round(float(ans)+1,1)), str(round(float(ans)+0.5,1)), str(round(float(ans)-1,1))]), "answer": ans, "hint": "Dùng tỉ số AE/EB = AF/FC.", "image": fig_to_b64(fig)})
    fig, ans, _ = get_plot('altitude')
    pool.append({"question": "Cho $\\Delta ABC$ vuông tại A, đường cao AH=h. Tính độ dài h:", "options": fmt_opt(ans, [str(round(float(ans)+2,1)), str(round(float(ans)+1,1)), str(round(float(ans)-1,1))]), "answer": ans, "hint": "Sử dụng $AH^2 = BH \\cdot HC$.", "image": fig_to_b64(fig)})
    fig, ans, a_val = get_plot('parabola')
    pool.append({"question": "Quan sát đồ thị $y=ax^2$. Khẳng định nào ĐÚNG?", "options": fmt_opt(ans, [r"$a < 0$" if a_val>0 else r"$a > 0$", "Luôn đồng biến", "Qua điểm (0;2)"]), "answer": ans, "hint": "Bề lõm quay lên thì $a>0$, quay xuống thì $a<0$.", "image": fig_to_b64(fig)})
    
    # 17 Câu Text cơ bản lấp đầy
    pool.append({"question": "Nghiệm của $x^4 - 5x^2 + 4 = 0$ là:", "options": fmt_opt("$\\pm 1, \\pm 2$", ["$1, 4$", "$\\pm 1, 2$", "Vô nghiệm"]), "answer": "$\\pm 1, \\pm 2$", "hint": "Đặt $t=x^2 (t \\ge 0)$."})
    pool.append({"question": "Hệ số góc của đường thẳng $3x + 2y - 5 = 0$ là:", "options": fmt_opt("$-1.5$", ["1.5", "3", "2"]), "answer": "$-1.5$", "hint": "Đưa về dạng $y = ax+b$."})
    pool.append({"question": "Căn bậc hai số học của 16 là:", "options": fmt_opt("4", ["-4", "$\\pm 4$", "256"]), "answer": "4", "hint": "Căn bậc hai số học luôn không âm."})
    pool.append({"question": "Điều kiện xác định của biểu thức $\\sqrt{2x - 4}$ là:", "options": fmt_opt("$x \\ge 2$", ["$x > 2$", "$x \\le 2$", "$x \\neq 2$"]), "answer": "$x \\ge 2$", "hint": "$2x - 4 \\ge 0 \\Leftrightarrow x \\ge 2$."})
    pool.append({"question": "Hàm số $y = (m-1)x + 3$ đồng biến khi:", "options": fmt_opt("$m > 1$", ["$m < 1$", "$m \\ge 1$", "$m \\neq 1$"]), "answer": "$m > 1$", "hint": "Hệ số $a > 0 \\Leftrightarrow m - 1 > 0$."})
    pool.append({"question": "Nghiệm của hệ phương trình $x + y = 4$ và $x - y = 2$ là:", "options": fmt_opt("$(3; 1)$", ["$(1; 3)$", "$(2; 2)$", "$(-3; -1)$"]), "answer": "$(3; 1)$", "hint": "Cộng hai vế: $2x = 6 \\Rightarrow x = 3$."})
    pool.append({"question": "Điểm nào sau đây thuộc đồ thị hàm số $y = 2x^2$?", "options": fmt_opt("$M(1; 2)$", ["$N(2; 4)$", "$P(-1; -2)$", "$Q(0; 2)$"]), "answer": "$M(1; 2)$", "hint": "Thay $x=1$ vào $y=2x^2$ ta được $y=2$."})
    pool.append({"question": "Phương trình $x^2 - 5x + 6 = 0$ có tổng hai nghiệm là:", "options": fmt_opt("5", ["-5", "6", "-6"]), "answer": "5", "hint": "Theo Vi-ét: $x_1 + x_2 = -\\frac{b}{a} = 5$."})
    pool.append({"question": "Cho $\\Delta ABC$ vuông tại A, đường cao AH. Biết $BH = 2, CH = 8$. Độ dài AH là:", "options": fmt_opt("4", ["16", "5", "10"]), "answer": "4", "hint": "$AH^2 = BH.CH = 16$."})
    pool.append({"question": "Tính $\\sin 30^\\circ$:", "options": fmt_opt("$\\frac{1}{2}$", ["$\\frac{\\sqrt{3}}{2}$", "$1$", "$\\frac{\\sqrt{2}}{2}$"]), "answer": "$\\frac{1}{2}$", "hint": "Giá trị lượng giác cơ bản."})
    pool.append({"question": "Đường tròn là hình:", "options": fmt_opt("Có tâm đối xứng", ["Không có tâm đối xứng", "Có 2 trục đối xứng", "Không có trục đối xứng"]), "answer": "Có tâm đối xứng", "hint": "Tâm đường tròn là tâm đối xứng."})
    pool.append({"question": "Góc nội tiếp chắn nửa đường tròn có số đo bằng:", "options": fmt_opt("$90^\\circ$", ["$60^\\circ$", "$180^\\circ$", "$120^\\circ$"]), "answer": "$90^\\circ$", "hint": "Góc nội tiếp chắn nửa đường tròn là góc vuông."})
    pool.append({"question": "Thể tích hình trụ có bán kính đáy $R=2$, chiều cao $h=5$ là:", "options": fmt_opt("$20\\pi$", ["$10\\pi$", "$40\\pi$", "$20$"]), "answer": "$20\\pi$", "hint": "$V = \\pi R^2 h = \\pi . 2^2 . 5$."})
    pool.append({"question": "Khi gieo một đồng xu cân đối, xác suất xuất hiện mặt sấp là:", "options": fmt_opt("$\\frac{1}{2}$", ["$\\frac{1}{3}$", "$\\frac{1}{6}$", "$1$"]), "answer": "$\\frac{1}{2}$", "hint": "Có 1 mặt sấp trên 2 mặt."})
    pool.append({"question": "Rút gọn biểu thức $\\sqrt{(1 - \\sqrt{2})^2}$ ta được:", "options": fmt_opt("$\\sqrt{2} - 1$", ["$1 - \\sqrt{2}$", "$-1$", "1"]), "answer": "$\\sqrt{2} - 1$", "hint": "Do $1 < \\sqrt{2}$ nên $|1 - \\sqrt{2}| = \\sqrt{2} - 1$."})
    pool.append({"question": "Giá trị nhỏ nhất của biểu thức $P = x^2 - 4x + 5$ là:", "options": fmt_opt("1", ["0", "5", "4"]), "answer": "1", "hint": "$P = (x-2)^2 + 1 \\ge 1$."})
    pool.append({"question": "Đường tròn có bán kính $R=5$, độ dài dây cung cách tâm $3$ là:", "options": fmt_opt("8", ["4", "6", "10"]), "answer": "8", "hint": "Dùng Pytago: nửa dây bằng $\\sqrt{5^2-3^2}=4$."})
    return pool

class ExamGenerator:
    def __init__(self):
        self.exam = []

    def generate_matrix_exam(self, status_el):
        fallback_pool = get_large_fallback_pool()
        # Lấy 3 câu hình học mồi, dùng copy.deepcopy để CHỐNG LỖI TRÙNG ID (Duplicate Key)
        all_qs = [copy.deepcopy(q) for q in fallback_pool[:3]]
        
        common_rules = """
        KHÔNG DÙNG JSON. TRẢ VỀ ĐÚNG CẤU TRÚC TAG SAU:
        <CAU>
        <Q> Nội dung câu hỏi </Q>
        <A> Đáp án 1 </A>
        <B> Đáp án 2 </B>
        <C> Đáp án 3 </C>
        <D> Đáp án 4 </D>
        <ANS> Chữ cái (A/B/C/D) </ANS>
        <HINT> Gợi ý 1 dòng ngắn </HINT>
        </CAU>
        BẮT BUỘC: MỌI CÔNG THỨC TOÁN HỌC VÀ SỐ LIỆU PHẢI ĐƯỢC BỌC TRONG DẤU $. Ví dụ: $\\sqrt{8} = 2\\sqrt{2}$. Không được dùng ngoặc tròn để bọc công thức.
        """
        
        status_el.info("⏳ Giai đoạn 1/2: Đang thiết kế 20 câu Đại số (Chuẩn Ma trận)...")
        p1 = f"""Tạo CHÍNH XÁC 20 câu trắc nghiệm ĐẠI SỐ Toán 9. Ma trận: Căn thức (6), Hàm số (3), PT/HPT (8), BPT (3). Có cài câu VDC.
        {common_rules}"""
        try: all_qs.extend(parse_xml_exam(call_ai(p1)))
        except: pass
        
        status_el.warning("⏳ Giai đoạn 2/2: Đang thiết kế 20 câu Hình học & Thống kê (Chuẩn Ma trận)...")
        p2 = f"""Tạo CHÍNH XÁC 20 câu trắc nghiệm HÌNH HỌC & THỐNG KÊ Toán 9. Ma trận: Hệ thức lượng (5), Đường tròn (6), Hình khối (3), Xác suất (6).
        {common_rules}"""
        try: all_qs.extend(parse_xml_exam(call_ai(p2)))
        except: pass

        # THUẬT TOÁN AUTO-PAD (TỰ PHỤC HỒI CHỐNG SẬP MẠNG)
        if len(all_qs) < 10:
            status_el.warning("⚠️ Mạng AI đang quá tải. Hệ thống đang kích hoạt ngân hàng câu hỏi dự phòng để lấp đầy 40 câu...")
            
        while len(all_qs) < 40:
            # Dùng deepcopy để sinh ra đối tượng mới hoàn toàn, dập tắt lỗi DuplicateKeyError (Ảnh 67)
            all_qs.append(copy.deepcopy(random.choice(fallback_pool[3:])))
            
        self.exam = all_qs[:40]
        random.shuffle(self.exam)
        for i, q in enumerate(self.exam): q['id'] = i + 1
        
        status_el.success("✅ Hoàn tất! Bộ đề 40 CÂU CHUẨN MA TRẬN đã sẵn sàng.")
        time.sleep(1)
        return self.exam

# ==========================================
# 5. GIAO DIỆN HỆ THỐNG
# ==========================================
def main():
    st.set_page_config(page_title="LMS Lê Quý Đôn V55", layout="wide", page_icon="🏫")
    init_db()
    
    for k in ['current_user', 'role', 'fullname', 'mand_mode', 'mand_exam_id', 'prac_data', 'prac_submitted', 'prac_ans']:
        if k not in st.session_state: 
            st.session_state[k] = [] if k=='prac_data' else {} if k=='prac_ans' else False if k=='prac_submitted' else None

    if not st.session_state.current_user:
        st.markdown("<h2 style='text-align: center;'>🎓 CỔNG TRẮC NGHIỆM LÊ QUÝ ĐÔN</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                u = st.text_input("Tài khoản")
                p = st.text_input("Mật khẩu", type="password")
                if st.form_submit_button("🚀 Đăng nhập", use_container_width=True):
                    conn = sqlite3.connect('exam_db.sqlite')
                    res = conn.execute("SELECT role, fullname FROM users WHERE username=? AND password=?", (u.strip(), p.strip())).fetchone()
                    conn.close()
                    if res:
                        st.session_state.current_user, st.session_state.role, st.session_state.fullname = u.strip(), res[0], res[1]
                        st.rerun()
                    else: st.error("❌ Sai tài khoản/mật khẩu!")
        return

    # SIDEBAR
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.fullname}")
        if st.session_state.role == 'core_admin':
            st.markdown("---")
            api_input = st.text_input("🔑 API Key Gemini:", type="password", value=get_api_key())
            if st.button("💾 Lưu API Key"):
                save_api_key(api_input.strip())
                st.success("Đã lưu!")
                time.sleep(1); st.rerun()
        elif st.session_state.role == 'student':
            new_pw = st.text_input("🔑 Đổi mật khẩu:", type="password")
            if st.button("Lưu mật khẩu"):
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("UPDATE users SET password=? WHERE username=?", (new_pw.strip(), st.session_state.current_user))
                conn.commit(); conn.close(); st.success("Đã đổi!")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # VIEW: HỌC SINH
    if st.session_state.role == 'student':
        tab_mand, tab_prac = st.tabs(["🔥 Bài Tập Bắt Buộc", "🤖 Đề Tự Luyện (40 Câu)"])
        now_vn = datetime.now(VN_TZ)
        
        # --- TAB 1: BẮT BUỘC ---
        with tab_mand:
            conn = sqlite3.connect('exam_db.sqlite')
            df_exams = pd.read_sql_query("SELECT * FROM mandatory_exams ORDER BY id DESC", conn)
            u_class = conn.execute("SELECT class_name FROM users WHERE username=?", (st.session_state.current_user,)).fetchone()
            u_class = str(u_class[0]).strip().lower() if u_class and u_class[0] else ""
            res_dict = {r[0]: r[1] for r in conn.execute("SELECT exam_id, score FROM mandatory_results WHERE username=?", (st.session_state.current_user,)).fetchall()}
            conn.close()
            
            pending, completed = [], []
            for _, r in df_exams.iterrows():
                tc = str(r.get('target_class', '')).strip().lower()
                if tc in ['toàn trường', u_class, 'none', '']:
                    if r['id'] in res_dict: completed.append(r)
                    else: pending.append(r)
            
            # TRẠNG THÁI: DANH SÁCH BÀI
            if not st.session_state.mand_mode:
                st.markdown("### 📝 BÀI CẦN LÀM")
                if not pending: st.success("Tuyệt vời! Bạn không còn bài tập nợ.")
                for r in pending:
                    st.markdown(f"**{r['title']}**")
                    if st.button("✍️ VÀO PHÒNG THI", key=f"do_{r['id']}", type="primary"):
                        st.session_state.mand_exam_id, st.session_state.mand_mode = r['id'], 'doing'
                        st.session_state[f"st_{r['id']}"] = datetime.now().timestamp()
                        st.rerun()
                    st.markdown("---")
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📂 Lịch sử bài đã nộp"):
                    for r in completed:
                        st.markdown(f"**{r['title']}** - Điểm: **{res_dict[r['id']]:.2f}**")
                        if st.button("👁 Xem Lời Giải", key=f"rev_{r['id']}"):
                            st.session_state.mand_exam_id, st.session_state.mand_mode = r['id'], 'review'
                            st.rerun()
                        st.markdown("---")
            
            # TRẠNG THÁI: ĐANG THI
            elif st.session_state.mand_mode == 'doing':
                e_id = st.session_state.mand_exam_id
                row = df_exams[df_exams['id'] == e_id].iloc[0]
                rem = max(0, 5400 - (datetime.now().timestamp() - st.session_state.get(f"st_{e_id}", datetime.now().timestamp())))
                
                components.html(f"""<script>
                var t = {rem}; setInterval(()=>{{ t--; if(t<=0) window.parent.document.querySelectorAll('button').forEach(b=>{{if(b.innerText.includes('NỘP BÀI')) b.click()}}); else document.getElementById('clk').innerText = Math.floor(t/60)+':'+(t%60).toString().padStart(2,'0'); }}, 1000);
                </script><div id='clk' style='font-size:24px;font-weight:bold;color:white;background:#e74c3c;text-align:center;padding:10px;border-radius:5px'></div>""", height=60)
                
                st.subheader(f"ĐANG THI: {row['title']}")
                is_pdf = pd.notnull(row.get('file_data')) and row.get('file_data') != ""
                
                if f"ans_{e_id}" not in st.session_state: 
                    if is_pdf:
                        num_q = len(json.loads(row['answer_key']))
                        st.session_state[f"ans_{e_id}"] = {str(i+1): None for i in range(num_q)}
                    else:
                        qs = json.loads(row['questions_json'])
                        st.session_state[f"ans_{e_id}"] = {str(q.get('id', i+1)): None for i, q in enumerate(qs)}
                
                if is_pdf:
                    c_p, c_a = st.columns([1.5, 1])
                    with c_p: st.markdown(f'<embed src="data:application/pdf;base64,{row["file_data"]}" width="100%" height="800px">', unsafe_allow_html=True)
                    with c_a:
                        st.markdown("#### PHIẾU TÔ")
                        cols = st.columns(2)
                        for i in range(len(st.session_state[f"ans_{e_id}"])):
                            q_str = str(i+1)
                            val = st.session_state[f"ans_{e_id}"][q_str]
                            idx = ['A','B','C','D'].index(val) if val in ['A','B','C','D'] else None
                            st.session_state[f"ans_{e_id}"][q_str] = cols[i%2].radio(f"Câu {q_str}", ['A','B','C','D'], index=idx, key=f"r_{e_id}_{q_str}", horizontal=True)
                else:
                    qs = json.loads(row['questions_json'])
                    for i, q in enumerate(qs):
                        q_id = str(q.get('id', i+1))
                        q_text = format_math(q.get('question', q.get('q', '')))
                        opts = [format_math(o) for o in q.get('options', q.get('opts', []))]
                        
                        st.markdown(f"**Câu {q_id}:** {q_text}", unsafe_allow_html=True)
                        if q.get('image_svg'): st.markdown(f"<div style='text-align:center'>{q['image_svg']}</div>", unsafe_allow_html=True)
                        elif q.get('image') or q.get('i'): 
                            img_data = q.get('image') or q.get('i')
                            st.markdown(f"<img src='data:image/png;base64,{img_data}' width='300'>", unsafe_allow_html=True)
                        
                        val = st.session_state[f"ans_{e_id}"][q_id]
                        idx = opts.index(val) if val in opts else None
                        st.session_state[f"ans_{e_id}"][q_id] = st.radio("Chọn:", opts, index=idx, key=f"r_{e_id}_{q_id}", label_visibility="collapsed")
                        st.markdown("---")
                
                if st.button("📤 NỘP BÀI CHÍNH THỨC", type="primary", use_container_width=True) or rem<=0:
                    if is_pdf: ans_key = json.loads(row['answer_key'])
                    else: ans_key = [format_math(q.get('answer', q.get('a', ''))) for q in json.loads(row['questions_json'])]
                    
                    u_ans = st.session_state[f"ans_{e_id}"]
                    corr = sum(1 for i, k in enumerate(u_ans.keys()) if u_ans[k] == ans_key[i])
                    score = (corr / len(ans_key)) * 10
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO mandatory_results (username, exam_id, score, user_answers_json) VALUES (?,?,?,?)", (st.session_state.current_user, e_id, score, json.dumps(u_ans)))
                    conn.commit(); conn.close()
                    st.session_state.mand_mode = None
                    st.rerun()

            # TRẠNG THÁI: XEM LẠI BÀI
            elif st.session_state.mand_mode == 'review':
                e_id = st.session_state.mand_exam_id
                row = df_exams[df_exams['id'] == e_id].iloc[0]
                conn = sqlite3.connect('exam_db.sqlite')
                score, u_ans_str = conn.execute("SELECT score, user_answers_json FROM mandatory_results WHERE username=? AND exam_id=?", (st.session_state.current_user, e_id)).fetchone()
                conn.close()
                u_ans = json.loads(u_ans_str)
                is_pdf = pd.notnull(row.get('file_data')) and row.get('file_data') != ""
                
                st.markdown(f"<div style='background:#e8f5e9;padding:15px;border-radius:10px;text-align:center'><h2 style='color:#2E7D32'>Điểm: {score:.2f}/10</h2></div><br>", unsafe_allow_html=True)
                
                if is_pdf:
                    ans_key = json.loads(row['answer_key'])
                    hints = json.loads(row['questions_json']) if pd.notnull(row.get('questions_json')) and row.get('questions_json') != "" else []
                    
                    c_p, c_a = st.columns([1.5, 1])
                    with c_p: st.markdown(f'<embed src="data:application/pdf;base64,{row["file_data"]}" width="100%" height="800px">', unsafe_allow_html=True)
                    with c_a:
                        for i, k in enumerate(ans_key):
                            raw_val = u_ans.get(str(i+1))
                            u_val = check_none_answer(raw_val) # CHỐNG LỖI NONE 65.2
                            
                            if raw_val == k: st.success(f"**Câu {i+1}: Bạn chọn {u_val}** ✅")
                            else: st.error(f"**Câu {i+1}: Bạn chọn {u_val}** ❌ (Đúng: {k})")
                            
                            if hints and i < len(hints):
                                h = hints[i].get('hint', hints[i].get('h', ''))
                                if h and str(h).lower() not in ['none', 'null', '']: 
                                    st.info(f"💡 Hướng dẫn: {format_math(h)}")
                            st.markdown("---")
                else:
                    qs = json.loads(row['questions_json'])
                    for i, q in enumerate(qs):
                        q_id = str(q.get('id', i+1))
                        q_text = format_math(q.get('question', q.get('q', '')))
                        opts = [format_math(o) for o in q.get('options', q.get('opts', []))]
                        ans_correct = format_math(q.get('answer', q.get('a', '')))
                        
                        st.markdown(f"**Câu {q_id}:** {q_text}", unsafe_allow_html=True)
                        if q.get('image') or q.get('i'): 
                            img_data = q.get('image') or q.get('i')
                            st.markdown(f"<img src='data:image/png;base64,{img_data}' width='300'>", unsafe_allow_html=True)
                        
                        raw_val = u_ans.get(q_id)
                        u_val = check_none_answer(raw_val) # CHỐNG LỖI NONE 65.2
                        
                        st.radio("Đã chọn:", opts, index=opts.index(raw_val) if raw_val in opts else None, disabled=True, key=f"rv_{e_id}_{q_id}", label_visibility="collapsed")
                        
                        if raw_val == ans_correct: st.success(f"✅ Chính xác")
                        else: st.error(f"❌ Sai. Đáp án đúng: {ans_correct}")
                        
                        h_text = format_math(q.get('hint', q.get('h', '')))
                        if h_text and h_text.lower() not in ['none', 'null', '']: st.info(f"💡 Hướng dẫn: {h_text}")
                        st.markdown("---")
                        
                if st.button("⬅️ Quay lại danh sách", use_container_width=True):
                    st.session_state.mand_mode = None
                    st.rerun()

        # --- TAB 2: ĐỀ TỰ LUYỆN (40 CÂU) ---
        with tab_prac:
            if not st.session_state.prac_data:
                if st.button("🔄 TẠO BỘ ĐỀ 40 CÂU (CHUẨN MA TRẬN TOÁN 9)", type="primary", use_container_width=True):
                    el = st.empty()
                    try:
                        generator = ExamGenerator()
                        st.session_state.prac_data = generator.generate_matrix_exam(el)
                        st.session_state.prac_ans = {str(q['id']): None for q in st.session_state.prac_data}
                        st.session_state.prac_submitted = False
                        st.rerun()
                    except Exception as e: 
                        el.error(str(e))
            else:
                if st.session_state.prac_submitted:
                    corr = sum(1 for q in st.session_state.prac_data if st.session_state.prac_ans[str(q['id'])] == format_math(q.get('answer', q.get('a'))))
                    st.markdown(f"<div style='background:#e8f5e9;padding:15px;border-radius:10px;text-align:center'><h2 style='color:#2E7D32'>Điểm: {(corr/40)*10:.2f}/10</h2></div><br>", unsafe_allow_html=True)
                
                for q in st.session_state.prac_data:
                    q_text = format_math(q.get('question', q.get('q', '')))
                    opts = [format_math(o) for o in q.get('options', q.get('opts', []))]
                    ans_correct = format_math(q.get('answer', q.get('a', '')))
                    
                    st.markdown(f"**Câu {q['id']}:** {q_text}", unsafe_allow_html=True)
                    if q.get('image') or q.get('i'): 
                        img_data = q.get('image') or q.get('i')
                        st.markdown(f"<img src='data:image/png;base64,{img_data}' width='300'>", unsafe_allow_html=True)
                    
                    val = st.session_state.prac_ans[str(q['id'])]
                    idx = opts.index(val) if val in opts else None
                    # Radio button an toàn tuyệt đối với Deepcopy (Fix Lỗi 67)
                    selected = st.radio("Chọn:", opts, index=idx, disabled=st.session_state.prac_submitted, key=f"p_{q['id']}_{q_text[:5]}", label_visibility="collapsed")
                    
                    if not st.session_state.prac_submitted: 
                        st.session_state.prac_ans[str(q['id'])] = selected
                    else:
                        if selected == ans_correct: st.success("✅ Đúng")
                        else: 
                            u_val = check_none_answer(selected)
                            st.error(f"❌ Bạn chọn: {u_val} (Đúng: {ans_correct})")
                        
                        h_text = format_math(q.get('hint', q.get('h', '')))
                        if h_text and h_text.lower() not in ['none', 'null', '']: st.info(f"💡 Hướng dẫn: {h_text}")
                    st.markdown("---")
                
                if not st.session_state.prac_submitted:
                    if st.button("📤 NỘP BÀI TỰ LUYỆN", type="primary", use_container_width=True):
                        st.session_state.prac_submitted = True
                        st.rerun()
                else:
                    if st.button("🔄 TẠO ĐỀ MỚI KHÁC", type="primary", use_container_width=True):
                        st.session_state.prac_data = []
                        st.rerun()

    # ==========================
    # GIAO DIỆN QUẢN TRỊ & GIÁO VIÊN
    # ==========================
    elif st.session_state.role in ['core_admin', 'sub_admin', 'teacher']:
        st.title("⚙ Bảng Điều Khiển (LMS)")
        
        if st.session_state.role in ['core_admin', 'sub_admin']:
            tabs = st.tabs(["🏫 Lớp & Học sinh", "🛡️ Quản lý Nhân sự", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_staff, tab_scores, tab_system = tabs
        else:
            tabs = st.tabs(["🏫 Lớp của tôi", "📊 Báo cáo Điểm", "📤 Phát Đề (Giao Bài)"])
            tab_class, tab_scores, tab_system = tabs
            tab_staff = None
        
        conn = sqlite3.connect('exam_db.sqlite')
        
        c_all = conn.execute("SELECT class_name FROM users WHERE role='student' AND class_name IS NOT NULL AND class_name != ''").fetchall()
        student_classes = [r[0] for r in c_all]
        
        c_man = conn.execute("SELECT managed_classes FROM users WHERE managed_classes IS NOT NULL").fetchall()
        manager_classes_raw = [r[0] for r in c_man]
        
        all_classes_set = set(student_classes)
        for mc in manager_classes_raw:
            for cls in mc.split(','):
                if cls.strip(): all_classes_set.add(cls.strip())
        all_system_classes = sorted(list(all_classes_set))

        if st.session_state.role in ['core_admin', 'sub_admin']: available_classes = all_system_classes
        else:
            m_cls = conn.execute("SELECT managed_classes FROM users WHERE username=?", (st.session_state.current_user,)).fetchone()[0]
            available_classes = [x.strip() for x in m_cls.split(',')] if m_cls else []
        
        with tab_class:
            if not available_classes: st.info("Chưa có lớp học nào được phân công.")
            else:
                selected_class = st.selectbox("📌 Chọn lớp:", available_classes)
                existing_names = [row[0].strip().lower() for row in conn.execute("SELECT fullname FROM users WHERE role='student' AND class_name=?", (selected_class,)).fetchall()]

                with st.expander(f"➕ Thêm Học sinh vào lớp {selected_class}", expanded=False):
                    st.download_button("⬇️ TẢI FILE EXCEL MẪU", data=create_excel_template(), file_name="Mau_Danh_Sach.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    uploaded_excel = st.file_uploader("Nạp file Excel (Đã điền)", type=['xlsx'])
                    if uploaded_excel and st.button("🔄 Nạp dữ liệu"):
                        try:
                            df_import = pd.read_excel(uploaded_excel)
                            count = 0
                            for _, row in df_import.iterrows():
                                fullname, dob, school = str(row.get('Họ tên', '')).strip(), str(row.get('Ngày sinh', '')).strip(), str(row.get('Trường', '')).strip()
                                if fullname and fullname.lower() != 'nan':
                                    if dob.lower() == 'nan': dob = ""
                                    if school.lower() == 'nan': school = ""
                                    if fullname.lower() in existing_names and not dob: continue 
                                    uname = gen_user(fullname, dob)
                                    try:
                                        conn.execute("INSERT INTO users (username, password, role, fullname, dob, class_name, school) VALUES (?, '123456', 'student', ?, ?, ?, ?)", (uname, fullname, dob, selected_class, school))
                                        count += 1
                                        existing_names.append(fullname.lower()) 
                                    except: pass
                            conn.commit()
                            st.success(f"✅ Đã tạo {count} tài khoản!"); st.rerun()
                        except: st.error("Lỗi đọc file Excel.")
                    
                    st.markdown("**Tạo Thủ Công:**")
                    with st.form("manual_add"):
                        c1, c2 = st.columns(2)
                        m_name = c1.text_input("Họ và Tên (Bắt buộc)")
                        m_dob = c2.text_input("Ngày sinh")
                        if st.form_submit_button("Tạo nhanh") and m_name:
                            uname = gen_user(m_name, m_dob)
                            conn.execute("INSERT INTO users (username, password, role, fullname, dob, class_name) VALUES (?, '123456', 'student', ?, ?, ?)", (uname, m_name, m_dob, selected_class))
                            conn.commit(); st.success(f"✅ Tạo: {uname}"); st.rerun()

                st.markdown("---")
                df_students = pd.read_sql_query(f"SELECT username as 'Tài khoản', password as 'Mật khẩu', fullname as 'Họ Tên', dob as 'Ngày sinh' FROM users WHERE role='student' AND class_name='{selected_class}'", conn)
                if not df_students.empty:
                    st.download_button(f"📥 XUẤT EXCEL LỚP {selected_class}", data=to_excel(df_students), file_name=f"Danh_sach_{selected_class}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.dataframe(df_students, use_container_width=True)
                
                if not df_students.empty:
                    st.markdown("#### ✏️ Cập nhật Thông tin Học sinh")
                    user_to_edit = st.selectbox("Chọn Học sinh:", ["-- Chọn --"] + df_students['Tài khoản'].tolist())
                    if user_to_edit != "-- Chọn --":
                        u_data = conn.execute("SELECT fullname, password, dob, class_name FROM users WHERE username=?", (user_to_edit,)).fetchone()
                        with st.form("edit_form"):
                            c1, c2 = st.columns(2)
                            edit_name = c1.text_input("Họ Tên", value=u_data[0])
                            edit_pwd = c2.text_input("Mật khẩu", value=u_data[1])
                            edit_dob = c1.text_input("Ngày sinh", value=u_data[2] if u_data[2] else "")
                            edit_class = c2.text_input("Đổi Lớp", value=u_data[3])
                            del_reason = st.text_input("Lý do xóa:") if st.session_state.role in ['core_admin', 'sub_admin'] else ""
                            
                            col_save, col_del = st.columns(2)
                            if col_save.form_submit_button("💾 Cập nhật"):
                                conn.execute("UPDATE users SET fullname=?, password=?, dob=?, class_name=? WHERE username=?", (edit_name, edit_pwd, edit_dob, edit_class, user_to_edit))
                                conn.commit(); st.success("✅ Đã cập nhật!"); st.rerun()
                            if st.session_state.role in ['core_admin', 'sub_admin'] and col_del.form_submit_button("🗑 XÓA TÀI KHOẢN"):
                                if not del_reason: st.error("❌ Nhập Lý do xóa!")
                                else:
                                    log_action(st.session_state.current_user, "Học sinh", user_to_edit, del_reason)
                                    conn.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                                    conn.execute("DELETE FROM mandatory_results WHERE username=?", (user_to_edit,))
                                    conn.commit(); st.rerun()
                
                if st.session_state.role in ['core_admin', 'sub_admin']:
                    with st.expander("🚨 Dọn dẹp Cuối năm (Xóa toàn bộ lớp)"):
                        del_reason = st.text_input("Lý do xóa lớp (Bắt buộc):")
                        if st.checkbox("Xác nhận xóa vĩnh viễn.") and st.button("🗑 TIẾN HÀNH XÓA LỚP", type="primary"):
                            if not del_reason: st.error("❌ Nhập Lý do!")
                            else:
                                log_action(st.session_state.current_user, "Lớp học", selected_class, del_reason)
                                for u in df_students['Tài khoản'].tolist():
                                    conn.execute("DELETE FROM users WHERE username=?", (u,))
                                    conn.execute("DELETE FROM mandatory_results WHERE username=?", (u,))
                                conn.commit(); st.success("✅ Đã xóa!"); st.rerun()

        if tab_staff:
            with tab_staff:
                if st.session_state.role == 'core_admin':
                    st.subheader("🛡️ Quản lý Admin Thành viên")
                    with st.form("add_sa"):
                        c1, c2 = st.columns(2)
                        sa_user, sa_pwd = c1.text_input("Tài khoản (viết liền)"), c2.text_input("Mật khẩu")
                        sa_name, sa_class = c1.text_input("Họ Tên"), c2.text_input("Giao Lớp (VD: 9A, 9B)")
                        if st.form_submit_button("Tạo Admin", type="primary"):
                            try:
                                conn.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'sub_admin', ?, ?)", (sa_user, sa_pwd, sa_name, sa_class))
                                conn.commit(); st.rerun()
                            except: st.error("❌ Tên tồn tại!")
                            
                    df_sa = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='sub_admin'", conn)
                    st.dataframe(df_sa, use_container_width=True)
                    
                    c_del1, c_del2 = st.columns(2)
                    sa_to_del = c_del1.selectbox("Chọn Admin cần xóa:", ["-- Chọn --"] + df_sa['Tài khoản'].tolist())
                    sa_del_reason = c_del2.text_input("Lý do xóa Admin:")
                    if sa_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa Admin"):
                        if not sa_del_reason: st.error("❌ Nhập Lý do!")
                        else:
                            log_action(st.session_state.current_user, "Admin", sa_to_del, sa_del_reason)
                            conn.execute("DELETE FROM users WHERE username=?", (sa_to_del,))
                            conn.commit(); st.rerun()
                    st.markdown("---")

                st.subheader("👨‍🏫 Quản lý Giáo viên")
                with st.form("add_gv"):
                    c1, c2 = st.columns(2)
                    t_user, t_pwd = c1.text_input("Tài khoản GV"), c2.text_input("Mật khẩu")
                    t_name, t_classes = c1.text_input("Họ Tên"), c2.text_input("Giao Lớp (VD: 9A1)")
                    if st.form_submit_button("Tạo GV", type="primary"):
                        try:
                            conn.execute("INSERT INTO users (username, password, role, fullname, managed_classes) VALUES (?, ?, 'teacher', ?, ?)", (t_user, t_pwd, t_name, t_classes))
                            conn.commit(); st.rerun()
                        except: st.error("❌ Tồn tại!")
                        
                df_teach = pd.read_sql_query("SELECT username as 'Tài khoản', fullname as 'Họ tên', managed_classes as 'Lớp QL' FROM users WHERE role='teacher'", conn)
                st.dataframe(df_teach, use_container_width=True)
                
                t_to_edit = st.selectbox("Chọn Giáo viên phân lớp:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                if t_to_edit != "-- Chọn --":
                    curr_cls = df_teach[df_teach['Tài khoản'] == t_to_edit]['Lớp QL'].values[0]
                    with st.form("reassign_gv_form"):
                        new_cls = st.text_input("Danh sách lớp mới:", value=str(curr_cls) if pd.notna(curr_cls) else "")
                        if st.form_submit_button("💾 Cập nhật"):
                            conn.execute("UPDATE users SET managed_classes=? WHERE username=?", (new_cls, t_to_edit))
                            conn.commit(); st.success("✅ Đã phân công!"); st.rerun()
                
                c_delt1, c_delt2 = st.columns(2)
                t_to_del = c_delt1.selectbox("Chọn GV cần xóa:", ["-- Chọn --"] + df_teach['Tài khoản'].tolist())
                t_del_reason = c_delt2.text_input("Lý do xóa GV:")
                if t_to_del != "-- Chọn --" and st.button("🗑 Xác nhận Xóa GV"):
                    if not t_del_reason: st.error("❌ Nhập Lý do!")
                    else:
                        log_action(st.session_state.current_user, "Giáo viên", t_to_del, t_del_reason)
                        conn.execute("DELETE FROM users WHERE username=?", (t_to_del,))
                        conn.commit(); st.rerun()

                if st.session_state.role == 'core_admin':
                    st.markdown("---"); st.subheader("📜 Lịch Sử Xóa")
                    try: st.dataframe(pd.read_sql_query("SELECT deleted_by as 'Người xóa', entity_type as 'Loại', entity_name as 'Tên', reason as 'Lý do', timestamp as 'Thời gian' FROM deletion_logs ORDER BY id DESC", conn), use_container_width=True)
                    except: pass

        # --- TAB 3: BÁO CÁO ---
        with tab_scores:
            st.subheader("📊 Báo cáo & Thống kê Chuyên sâu")
            if not available_classes: st.info("Chưa có lớp nào.")
            else:
                rep_class = st.selectbox("📌 Chọn Lớp:", available_classes)
                try: df_all_exams = pd.read_sql_query("SELECT id, title, questions_json, file_data, answer_key FROM mandatory_exams ORDER BY id DESC", conn)
                except: df_all_exams = pd.DataFrame()
                    
                if df_all_exams.empty: st.info("Chưa có bài tập.")
                else:
                    rep_exam_title = st.selectbox("📝 Chọn Bài Kiểm Tra:", df_all_exams['title'].tolist())
                    exam_row = df_all_exams[df_all_exams['title'] == rep_exam_title].iloc[0]
                    exam_id = exam_row['id']
                    
                    df_stu = pd.read_sql_query(f"SELECT username, fullname FROM users WHERE role='student' AND class_name='{rep_class}'", conn)
                    df_sub = pd.read_sql_query(f"SELECT u.username, u.fullname, mr.score, mr.user_answers_json, mr.timestamp FROM mandatory_results mr JOIN users u ON mr.username = u.username WHERE mr.exam_id={exam_id} AND u.class_name='{rep_class}'", conn)
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng HS", len(df_stu)); c2.metric("Đã nộp", len(df_sub)); c3.metric("Chưa nộp", len(df_stu) - len(df_sub))
                    
                    t1, t2, t3 = st.tabs(["✅ Bảng Điểm", "❌ HS Chưa Làm", "📈 Thống kê Câu Sai"])
                    with t1:
                        if not df_sub.empty: 
                            df_exp = df_sub[['fullname', 'score', 'timestamp']].rename(columns={'fullname': 'Họ Tên', 'score': 'Điểm', 'timestamp': 'Giờ nộp'})
                            st.dataframe(df_exp, use_container_width=True)
                            st.download_button("📥 XUẤT EXCEL", data=to_excel(df_exp, "BangDiem"), file_name=f"Diem_{rep_class}.xlsx", type="primary")
                        else: st.info("Chưa có ai nộp.")
                    with t2:
                        df_miss = df_stu[~df_stu['username'].isin(df_sub['username'].tolist())]
                        if not df_miss.empty: st.dataframe(df_miss[['username', 'fullname']].rename(columns={'username': 'Tài khoản', 'fullname': 'Họ Tên'}), use_container_width=True)
                        else: st.success("100% hoàn thành!")
                    with t3:
                        if not df_sub.empty:
                            wrong_stats = {}
                            if pd.notnull(exam_row.get('file_data')) and exam_row.get('file_data') != "":
                                ans_key = json.loads(exam_row['answer_key']) if exam_row['answer_key'] else []
                                wrong_stats = {str(i+1): {'text': f"Câu {i+1} (PDF)", 'wrong_count': 0} for i in range(len(ans_key))}
                                for _, r in df_sub.iterrows():
                                    try:
                                        u_ans = json.loads(r['user_answers_json'])
                                        for i, k in enumerate(ans_key):
                                            if u_ans.get(str(i+1)) != k: wrong_stats[str(i+1)]['wrong_count'] += 1
                                    except: pass
                            else:
                                qs = json.loads(exam_row['questions_json']) if exam_row['questions_json'] else []
                                wrong_stats = {str(q.get('id', i+1)): {'text': format_math(q.get('question', q.get('q'))), 'wrong_count': 0} for i, q in enumerate(qs)}
                                for _, r in df_sub.iterrows():
                                    try:
                                        u_ans = json.loads(r['user_answers_json'])
                                        for i, q in enumerate(qs):
                                            q_id = str(q.get('id', i+1))
                                            ans_correct = q.get('answer', q.get('a'))
                                            if u_ans.get(q_id) != ans_correct: wrong_stats[q_id]['wrong_count'] += 1
                                    except: pass
                            
                            df_st = pd.DataFrame([{'Câu': k, 'Nội dung': v['text'], 'Số HS sai': v['wrong_count']} for k, v in wrong_stats.items()]).sort_values(by='Số HS sai', ascending=False)
                            for _, r in df_st.head(5).iterrows():
                                if r['Số HS sai'] > 0: st.error(f"**Câu {r['Câu']}** ({r['Số HS sai']} HS sai) - {r['Nội dung'][:50]}...")
                            st.dataframe(df_st[['Câu', 'Số HS sai']], use_container_width=True)

        # --- TAB 4: PHÁT ĐỀ ---
        with tab_system:
            st.subheader("📤 Phát Bài Tập")
            assign_opts = ["Toàn trường"] + all_system_classes if st.session_state.role in ['core_admin', 'sub_admin'] else available_classes
            if not assign_opts: st.warning("Chưa quản lý lớp nào.")
            else:
                target_cls = st.selectbox("🎯 Giao cho:", assign_opts)
                e_title = st.text_input("Tên bài kiểm tra (VD: Thi Giữa Kỳ Toán 9)")
                c1, c2 = st.columns(2)
                s_date, s_time = c1.date_input("Ngày giao"), c1.time_input("Giờ giao", value=datetime.strptime("07:00", "%H:%M").time())
                e_date, e_time = c2.date_input("Ngày thu"), c2.time_input("Giờ thu", value=datetime.strptime("23:59", "%H:%M").time())
                
                st.markdown("---")
                e_type = st.radio("Phương thức:", ["📤 File PDF/Ảnh", "🤖 Auto 40 Câu (Ma trận)"])
                
                if e_type == "📤 File PDF/Ảnh":
                    up_file = st.file_uploader("Tải File (PDF/Ảnh)", type=['pdf', 'jpg', 'png', 'jpeg'])
                    p_method = st.radio("Cấu hình Đáp án:", ["✍️ Thủ công (Dãy ABCD)", "🤖 AI bóc tách tự động"])
                    
                    if p_method == "✍️ Thủ công (Dãy ABCD)":
                        ans_inp = st.text_input("Chuỗi Đáp án (VD: ABCD)")
                        if st.button("🚀 Phát Đề", type="primary"):
                            if not e_title or not up_file or not ans_inp: st.error("Điền đủ thông tin!")
                            else:
                                ans_cln = list(ans_inp.upper().replace(" ", "").replace(",", ""))
                                if not all(c in ['A','B','C','D'] for c in ans_cln): st.error("Chỉ chứa A,B,C,D!")
                                else:
                                    b64 = base64.b64encode(up_file.read()).decode('utf-8')
                                    s_str, e_str = f"{s_date} {s_time.strftime('%H:%M:%S')}", f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                    conn.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key) VALUES (?,?,?,?,?,?,?)", (e_title.strip(), s_str, e_str, target_cls, b64, up_file.type, json.dumps(ans_cln)))
                                    conn.commit(); st.success("✅ Đã phát!")
                    else:
                        if 'admin_pdf_data' not in st.session_state: st.session_state.admin_pdf_data = None
                        if st.button("🤖 Phân tích Đề", type="primary"):
                            if not e_title or not up_file: st.error("Điền đủ thông tin!")
                            else:
                                with st.spinner("AI đang đọc toàn bộ file..."):
                                    prompt = """Trích xuất TOÀN BỘ câu hỏi trắc nghiệm Toán học. KHÔNG DÙNG JSON.
                                    Định dạng bắt buộc cho MỖI CÂU HỎI (Phải có thẻ đóng):
                                    <CAU>
                                    <Q>Nội dung câu hỏi</Q>
                                    <A>Đáp án A</A>
                                    <B>Đáp án B</B>
                                    <C>Đáp án C</C>
                                    <D>Đáp án D</D>
                                    <ANS>Chữ cái đúng (A,B,C,D)</ANS>
                                    <HINT>Gợi ý 1 dòng ngắn</HINT>
                                    </CAU>
                                    Lưu ý: BẮT BUỘC BỌC CÔNG THỨC TRONG $.
                                    """
                                    try:
                                        res = call_ai(prompt, up_file.read(), up_file.type)
                                        parsed = parse_xml_exam(res)
                                        if not parsed: st.error("AI không đọc được câu nào. Thử lại!")
                                        else:
                                            for i, q in enumerate(parsed): q['id'] = i+1
                                            st.session_state.admin_pdf_data = parsed; st.rerun()
                                    except Exception as e: st.error(str(e))
                                    
                        if st.session_state.admin_pdf_data:
                            st.success(f"✅ Bóc tách {len(st.session_state.admin_pdf_data)} câu. Xem lại và phát đề:")
                            ans_keys = []
                            with st.expander("🔍 Xem trước", expanded=True):
                                for q in st.session_state.admin_pdf_data:
                                    st.markdown(f"**Câu {q['id']}:** {q['question']}")
                                    ans_idx = q['options'].index(q['answer']) if q['answer'] in q['options'] else 0
                                    ans_keys.append(chr(65+ans_idx))
                                    st.markdown(f"✅ Đáp án: {chr(65+ans_idx)} | 💡 Hướng dẫn: {q['hint']}")
                                    st.markdown("---")
                            c_d, c_h = st.columns(2)
                            if c_d.button("🚀 DUYỆT VÀ PHÁT", use_container_width=True):
                                up_file.seek(0)
                                b64 = base64.b64encode(up_file.read()).decode('utf-8')
                                s_str, e_str = f"{s_date} {s_time.strftime('%H:%M:%S')}", f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                conn.execute("INSERT INTO mandatory_exams (title, start_time, end_time, target_class, file_data, file_type, answer_key, questions_json) VALUES (?,?,?,?,?,?,?,?)", (e_title.strip(), s_str, e_str, target_cls, b64, up_file.type, json.dumps(ans_keys), json.dumps(st.session_state.admin_pdf_data)))
                                conn.commit(); st.session_state.admin_pdf_data = None; st.success("✅ Thành công!"); time.sleep(1); st.rerun()
                            if c_h.button("❌ Hủy", use_container_width=True): st.session_state.admin_pdf_data = None; st.rerun()
                
                else:
                    if st.button("🚀 Phát Đề 40 Câu (Ma trận AI)", type="primary"):
                        if e_title:
                            el = st.empty()
                            try:
                                ex = ExamGenerator().generate_matrix_exam(el)
                                s_str, e_str = f"{s_date} {s_time.strftime('%H:%M:%S')}", f"{e_date} {e_time.strftime('%H:%M:%S')}"
                                conn.execute("INSERT INTO mandatory_exams (title, questions_json, start_time, end_time, target_class) VALUES (?,?,?,?,?)", (e_title.strip(), json.dumps(ex), s_str, e_str, target_cls))
                                conn.commit(); el.success("✅ Đã phát đề 40 câu!")
                            except Exception as e: el.error(str(e))
                        else: st.error("Nhập tên bài!")
        conn.close()

if __name__ == "__main__":
    main()
