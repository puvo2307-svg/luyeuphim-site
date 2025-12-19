# 📋 HƯỚNG DẪN CÀI ĐẶT - Dailymotion Helper GUI

## 🎯 Yêu cầu hệ thống

- **Windows 10/11** (hoặc Windows 7+)
- **Python 3.8 trở lên** (khuyến nghị Python 3.10+)
- **Kết nối Internet** để cài đặt thư viện và kết nối API

---

## 📦 BƯỚC 1: Cài đặt Python

### Kiểm tra Python đã cài chưa:
Mở **Command Prompt** hoặc **PowerShell**, gõ:
```bash
python --version
```

### Nếu chưa có Python:
1. Tải Python từ: https://www.python.org/downloads/
2. **QUAN TRỌNG**: Khi cài đặt, **tick vào ô "Add Python to PATH"**
3. Chọn "Install Now" hoặc "Customize installation" → Next → **tick "Add Python to PATH"** → Install

---

## 🚀 BƯỚC 2: Cài đặt tự động (Khuyến nghị)

### Cách 1: Dùng file `setup.bat` (Dễ nhất)
1. **Double-click** vào file `setup.bat`
2. Đợi script chạy xong (tự động tạo virtual environment và cài dependencies)
3. Xong!

### Cách 2: Cài đặt thủ công
Mở **Command Prompt** hoặc **PowerShell** trong thư mục `C:\DAILYMONTION`, chạy:

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
```

---

## ⚙️ BƯỚC 3: Cấu hình Google Sheets (Tùy chọn)

### Nếu muốn dùng Google Sheet để lưu dữ liệu:

1. **Tạo Service Account**:
   - Vào https://console.cloud.google.com/
   - Tạo project mới (hoặc dùng project có sẵn)
   - Vào **APIs & Services** → **Credentials**
   - Bấm **Create Credentials** → **Service Account**
   - Tạo xong, vào Service Account → **Keys** → **Add Key** → **JSON**
   - Tải file JSON về, đổi tên thành `drive_client_secret.json`
   - **Copy file này vào thư mục `C:\DAILYMONTION`**

2. **Chia sẻ Google Sheet**:
   - Mở Google Sheet của bạn
   - Bấm **Share** (Chia sẻ)
   - Thêm email của Service Account (tìm trong file JSON, dòng `client_email`)
   - Cấp quyền **Editor**

---

## 🎬 BƯỚC 4: Chạy ứng dụng

### Cách 1: Dùng file VBS (Không hiện CMD)
- **Double-click** vào file `RUN-DAILY.vbs`
- GUI sẽ mở, không hiện cửa sổ CMD

### Cách 2: Chạy từ Command Prompt
```bash
# Kích hoạt virtual environment (nếu chưa kích hoạt)
venv\Scripts\activate

# Chạy ứng dụng
python main.py
```

---

## 📝 BƯỚC 5: Cấu hình lần đầu

1. **Nhập Dailymotion API**:
   - Vào https://www.dailymotion.com/partner/settings/access-tokens
   - Tạo API Key và Secret
   - Nhập vào GUI: **API Key** và **API Secret**
   - Bấm **💾 Lưu cấu hình**

2. **Kết nối Google Sheet** (nếu cần):
   - Chọn file `drive_client_secret.json` (Browse)
   - Nhập **Sheet ID** (lấy từ URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`)
   - Nhập **Sheet Name** (ví dụ: `Sheet1`, `Sheet4`)
   - Bấm **🔗 Kết nối Google Sheet**

3. **Cấu hình quét kênh**:
   - Nhập **ID kênh Dailymotion** (mỗi dòng 1 ID, ví dụ: `luyeuphim`)
   - Nhập **Thời gian lặp quét** (phút, ví dụ: `60`)
   - Bấm **📺 Quét kênh 1 lần** để test, hoặc **🔁 Bắt đầu quét lặp** để tự động

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Virtual Environment
- **Luôn kích hoạt venv** trước khi chạy: `venv\Scripts\activate`
- Hoặc dùng file `setup.bat` để tự động

### 2. Dailymotion API
- Cần **Private API Key** (không phải Public) để upload video
- Nếu chỉ quét kênh (scan), Public API Key cũng được

### 3. Google Sheet
- File `drive_client_secret.json` phải đúng định dạng Service Account
- Không dùng OAuth Client Credentials (file `client_secret.json` khác)

### 4. Lỗi thường gặp:
- **"python is not recognized"**: Chưa cài Python hoặc chưa thêm vào PATH
- **"No module named 'xxx'"**: Chưa cài dependencies → chạy `pip install -r requirements.txt`
- **"403 Forbidden"**: API Key không có quyền hoặc sai username/channel ID

---

## 📁 CẤU TRÚC THƯ MỤC

```
C:\DAILYMONTION\
├── main.py                    # File chính (GUI)
├── dailymotion_api.py         # API Dailymotion
├── google_sheet.py            # Google Sheets API
├── requirements.txt           # Danh sách thư viện
├── config.json                # Cấu hình đã lưu (tự động tạo)
├── drive_client_secret.json   # Google Service Account (bạn tự thêm)
├── RUN-DAILY.vbs              # Script chạy ẩn CMD
├── setup.bat                  # Script cài đặt tự động
├── venv\                      # Virtual environment (tự động tạo)
└── tokens\                    # Token Google (tự động tạo)
    └── token.json
```

---

## 🔄 CẬP NHẬT ỨNG DỤNG

Khi có phiên bản mới:
1. **Backup** file `config.json` (lưu cấu hình)
2. **Download** code mới
3. Chạy lại `setup.bat` để cài dependencies mới
4. **Restore** file `config.json` (nếu cần)

---

## 📞 HỖ TRỢ

Nếu gặp lỗi, kiểm tra:
1. Python version: `python --version` (phải >= 3.8)
2. Virtual environment đã kích hoạt chưa
3. Dependencies đã cài đủ chưa: `pip list`
4. File `config.json` có đúng format không
5. Google Service Account có quyền truy cập Sheet không

---

**Chúc bạn sử dụng thành công! 🎉**

