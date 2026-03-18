# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN V33 SUPREME ULTIMATE (KHÔNG DÙNG JSON)
# Đột phá: Bỏ hoàn toàn JSON, dùng thuật toán Regex cắt lớp Văn bản thô (Plain Text).
# => Miễn nhiễm 100% với các lỗi Expecting value, Delimiter, Invalid Control Char.
# Cải tiến: Ưu tiên Model PRO và 8192 tokens để ép AI quét đủ 100% câu hỏi.
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

# --- DATABASE VAULT ĐỂ LƯU API KEY ---
def get_api_key():
    try:
        conn = sqlite3.connect('exam_db.sqlite')
        c = conn.cursor()
        c.execute("SELECT setting_value FROM system_settings WHERE setting_key='GEMINI_API_KEY'")
        res = c.fetchone()
        conn.close()
        return res[0] if res else ""
    except:
        return ""

def save_api_key(key_str):
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES ('GEMINI_API_KEY', ?)", (key_str,))
    conn.commit()
    conn.close()

# --- BỘ LỌC DỊCH THUẬT TOÁN HỌC SGK ---
def format_math_text(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text)
    return text

# --- 🚀 THUẬT TOÁN REGEX "BẤT TỬ" CẮT LỚP CÂU HỎI (KHÔNG DÙNG JSON) ---
def parse_ai_text_regex(raw_text):
    questions = []
    # Tách các khối câu hỏi dựa trên thẻ [CAU]
    blocks = raw_text.split('[CAU]')
    
    for block in blocks:
        # Nếu block không chứa Q: hoặc ANS: thì bỏ qua
        if 'Q:' not in block or 'ANS:' not in block: 
            continue
            
        try:
            # Dùng Regex để chẻ từng phần tử, bất chấp ngoặc kép hay kí tự xuống dòng
            q_match = re.search(r'Q:(.*?)(?=A:|B:|C:|D:|ANS:|HINT:|$)', block, re.DOTALL)
            a_match = re.search(r'A:(.*?)(?=B:|C:|D:|ANS:|HINT:|$)', block, re.DOTALL)
            b_match = re.search(r'B:(.*?)(?=C:|D:|ANS:|HINT:|$)', block, re.DOTALL)
            c_match = re.search(r'C:(.*?)(?=D:|ANS:|HINT:|$)', block, re.DOTALL)
            d_match = re.search(r'D:(.*?)(?=ANS:|HINT:|$)', block, re.DOTALL)
            ans_match = re.search(r'ANS:(.*?)(?=HINT:|$)', block, re.DOTALL)
            hint_match = re.search(r'HINT:(.*?)(?=$)', block, re.DOTALL)

            # Lấy dữ liệu dạng text thô
            q = q_match.group(1).strip() if q_match else ""
            oa = a_match.group(1).strip() if a_match else ""
            ob = b_match.group(1).strip() if b_match else ""
            oc = c_match.group(1).strip() if c_match else ""
            od = d_match.group(1).strip() if d_match else ""
            ans = ans_match.group(1).strip() if ans_match else ""
            hint = hint_match.group(1).strip() if hint_match else ""

            # Loại bỏ chữ "Câu 1:", "Bài 1:" nếu AI lỡ viết thêm vào
            q = re.sub(r'^(Câu|Bài)\s*\d+\s*[:\.\-]?\s*', '', q, flags=re.IGNORECASE).strip()

            # Khớp đáp án đúng
            ans = re.sub(r'[^A-D]', '', ans.upper())
            if not ans: ans = 'A'
            options = [oa, ob, oc, od]
            ans_idx = ord(ans[0]) - ord('A')
            ans_val = options[ans_idx] if 0 <= ans_idx < 4 else options[0]

            questions.append({
                "id": len(questions) + 1,
                "question": format_math_text(q),
                "options": [format_math_text(o) for o in options],
                "answer": format_math_text(ans_val),
                "hint": format_math_text(hint)
            })
        except Exception:
            continue
            
    if not questions:
        raise Exception("Google AI không tuân thủ định dạng xuất dữ liệu. Vui lòng bấm Phân tích lại!")
        
    return questions

# --- 🚀 RADAR TỰ ĐỘNG DÒ TÌM MODEL VÀ ÉP OUTPUT LỚN ---
def call_ai_safely(prompt, file_bytes=None, mime_type=None):
    if not AI_AVAILABLE:
        raise Exception("Hệ thống thiếu thư viện google-generativeai. Cần thêm vào requirements.txt")
    
    current_key = get_api_key()
    if not current_key or len(current_key) < 20 or "DÁN_MÃ" in current_key:
        raise Exception("Chưa cấu hình API Key. Admin Trường vui lòng vào Menu bên trái để lưu mã API.")
        
    genai.configure(api_key=current_key.strip())
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        raise Exception(f"Google từ chối mã API của bạn. Chi tiết: {str(e)}")

    contents = [prompt]
    needs_vision = False
    
    if file_bytes and mime_type:
        needs_vision = True
        if "pdf" in mime_type.lower():
            if not PDF_RENDERER_AVAILABLE:
                raise Exception("Thiếu thư viện PyMuPDF để xử lý PDF.")
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num in range(min(len(doc), 10)): # Quét 10 trang PDF
                pix = doc.load_page(page_num).get_pixmap(dpi=100) 
                img = Image.open(BytesIO(pix.tobytes("png")))
                contents.append(img)
        else:
            img = Image.open(BytesIO(file_bytes))
            contents.append(img)

    # Ưu tiên gemini-1.5-pro để AI thông minh và chăm chỉ hơn
    if needs_vision:
        preferences = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-1.0-pro-vision-latest']
    else:
        preferences = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro']
        
    target_model = None
    for pref in preferences:
        if pref in available_models:
            target_model = pref
            break
            
    if not target_model:
        if available_models: target_model = available_models[0]
        else: raise Exception("API Key của bạn không có quyền truy cập AI.")
            
    clean_model_name = target_model.replace("models/", "")
    
    try:
        # Ép max output tokens lớn nhất để bóc trọn bộ 40-50 câu
        model = genai.GenerativeModel(clean_model_name, generation_config={"max_output_tokens": 8192})
        return model.generate_content(contents)
    except Exception as e:
        raise Exception(f"Lỗi khi AI phân tích ({clean_model_name}). Chi tiết: {str(e)}")

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
    cols = [
        ("start_time", "TEXT"), ("end_time", "TEXT"), ("target_class", "TEXT DEFAULT 'Toàn trường'"),
        ("file_data", "TEXT"), ("file_type", "TEXT"), ("answer_key", "TEXT")
    ]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} {dtype}")
