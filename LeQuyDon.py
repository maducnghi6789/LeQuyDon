import unicodedata
import re
import random

def generate_username(fullname, dob):
    # 1. Ép kiểu về chuỗi và xử lý riêng chữ Đ/đ của tiếng Việt
    s = str(fullname)
    s = re.sub(r'[đĐ]', 'd', s)
    
    # 2. Lột sạch các dấu thanh và ký tự đặc biệt
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    
    # 3. Ép thành chữ in thường và xóa toàn bộ khoảng trắng (dấu cách)
    clean_name = re.sub(r'[^\w\s]', '', s).lower().replace(" ", "")
    
    # 4. Ghép nối với Năm sinh (hoặc số ngẫu nhiên) và 2 số bảo mật
    if not dob or str(dob).lower() == 'nan': 
        suffix = str(random.randint(1000, 9999))
    else:
        suffix = str(dob).split('/')[-1]
        if not suffix.isdigit(): suffix = str(random.randint(1000, 9999))
        
    # Kết quả trả về luôn có dạng: tenhocsinh + namsinh + _ + 2sốngẫunhiên
    return f"{clean_name}{suffix}_{random.randint(10,99)}"
