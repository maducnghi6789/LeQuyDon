# ==========================================
# LÕI HỆ THỐNG LMS - PHIÊN BẢN CORE TỐI ƯU
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
import unicodedata # Thư viện xử lý tiếng Việt không dấu
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))

# --- HÀM HỖ TRỢ EXCEL ---
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

# --- KHỞI TẠO DATABASE ---
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    for col in ["fullname", "dob", "class_name", "school", "province", "managed_classes"]:
        try: c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score REAL, correct_count INTEGER, wrong_count INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_exams (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, questions_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cols = [("start_time", "TEXT"), ("end_time", "TEXT"), ("target_class", "TEXT DEFAULT 'Toàn trường'"),
            ("file_data", "TEXT"), ("file_type", "TEXT"), ("answer_key", "TEXT")]
    for col, dtype in cols:
        try: c.execute(f"ALTER TABLE mandatory_exams ADD COLUMN {col} {dtype}")
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS mandatory_results (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exam_id INTEGER, score REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try: c.execute("ALTER TABLE mandatory_results ADD COLUMN user_answers_json TEXT")
    except: pass
    
    c.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('maducnghi6789@gmail.com', 'admin123', 'core_admin', 'Giám Đốc Hệ Thống')")
    conn.commit()
    conn.close()

# --- THUẬT TOÁN TẠO USERNAME CHUẨN QUỐC TẾ (KHÔNG DẤU, VIẾT LIỀN) ---
def generate_username(fullname, dob):
    # 1. Chuyển đổi tiếng Việt có dấu thành không dấu
    s = str(fullname)
    s = re.sub(r'[đĐ]', 'd', s) # Xử lý riêng chữ đ/Đ
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    
    # 2. Xóa ký tự đặc biệt, dấu cách và in thường
    clean_name = re.sub(r'[^\w\s]', '', s).lower().replace(" ", "")
    
    # 3. Nối với năm sinh và đuôi ngẫu nhiên
    if not dob or str(dob).lower() == 'nan': 
        suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
        
    return f"{clean_name}{suffix}_{random.randint(10,99)}"

# --- HỆ THỐNG VẼ HÌNH MATPLOTLIB ---
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
    ax.plot([x1, x2], [y1, y2], 'k--', lw=0.8); ax.plot([x3, x3], [y3_1, y3_2], 'b--', lw=0.8)
    ax.set_xlim(-3.5, 3); ax.set_ylim(-2.5, 2.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_right_triangle(a, b):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([0, b, 0, 0], [0, 0, a, 0], color='#2c3e50', lw=2)
    ax.plot([0, 0.3, 0.3], [0.3, 0.3, 0], color='red', lw=1)
    ax.text(-0.3, -0.3, 'A', fontweight='bold', ha='center', va='center')
    ax.text(b + 0.3, -0.3, 'B', fontweight='bold', ha='center', va='center')
    ax.text(-0.3, a + 0.3, 'C', fontweight='bold', ha='center', va='center')
    ax.text(b/2, -0.6, f'{b} cm', color='blue', ha='center')
    ax.text(-0.8, a/2, f'{a} cm', color='blue', va='center')
    ax.set_xlim(-1.5, b + 1.5); ax.set_ylim(-1.5, a + 1.5); ax.axis('off')
    return fig_to_base64(fig)

def draw_pie_chart():
    fig, ax = plt.subplots(figsize=(3, 3))
    labels = ['Giỏi', 'Khá', 'TB', 'Yếu']; sizes = [25, 45, 20, 10]; colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']
    ax.pie(sizes, explode=(0.1, 0, 0, 0), labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    ax.axis('equal') 
    return fig_to_base64(fig)

def draw_histogram():
    fig, ax = plt.subplots(figsize=(4, 2.5))
    bins = ['[5;6)', '[6;7)', '[7;8)', '[8;9)', '[9;10]']; percents = [10, 25, 40, 15, 10]
    bars = ax.bar(bins, percents, color=['#3498db']*5, edgecolor='black'); bars[2].set_color('#e74c3c') 
    ax.set_title("Phổ điểm môn Toán", fontsize=9); ax.set_ylabel('% Học sinh', fontsize=8); ax.set_ylim(0, 50)
    return fig_to_base64(fig)

def draw_tower_shadow(bong):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_aspect('equal')
    ax.plot([-1, 4], [0, 0], color='#27ae60', lw=3); ax.plot([0, 0], [0, 3], color='#7f8c8d', lw=4)
    ax.plot([2.5, 0], [0, 3], color='#f39c12', lw=1.5, linestyle='--')
    ax.text(-0.8, 1.5, 'Tháp', rotation=90, fontsize=8); ax.text(0.5, -0.5, f'Bóng: {bong}m', fontsize=8)
    ax.text(1.8, 0.1, r'$\alpha$', fontsize=10, color='blue')
    ax.set_xlim(-1, 3); ax.set_ylim(-1, 3.5); ax.axis('off')
    return fig_to_base64(fig)

# --- BỘ MÁY ĐỀ TỰ LUYỆN (CORE) ---
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def format_options(self, correct, distractors):
        opts = [correct] + distractors[:3]
        random.shuffle(opts)
        return opts

    def generate_all(self):
        pool = []
        pool.append({"q": r"Điều kiện xác định của biểu thức $\sqrt{2x - 4}$ là:", "a": r"$x \ge 2$", "d": [r"$x > 2$", r"$x \le 2$", r"$x < 2$"], "h": "💡 HD: Biểu thức dưới căn $\ge 0$.", "i": None})
        pool.append({"q": r"Giá trị của biểu thức $\sqrt{12} - 2\sqrt{3}$ bằng:", "a
