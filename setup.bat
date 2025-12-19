@echo off
chcp 65001 >nul
echo ========================================
echo   DAILYMOTION HELPER - SETUP AUTOMATIC
echo ========================================
echo.

REM Kiểm tra Python
echo [1/4] Đang kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ KHÔNG TÌM THẤY PYTHON!
    echo.
    echo Vui lòng cài đặt Python từ: https://www.python.org/downloads/
    echo QUAN TRỌNG: Khi cài, nhớ tick vào "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
python --version
echo ✅ Python đã được cài đặt
echo.

REM Tạo virtual environment
echo [2/4] Đang tạo virtual environment...
if exist venv (
    echo ⚠️  Thư mục venv đã tồn tại, bỏ qua...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Lỗi khi tạo virtual environment!
        pause
        exit /b 1
    )
    echo ✅ Đã tạo virtual environment
)
echo.

REM Kích hoạt venv và cài dependencies
echo [3/4] Đang cài đặt thư viện...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Không thể kích hoạt virtual environment!
    pause
    exit /b 1
)

REM Upgrade pip
python -m pip install --upgrade pip --quiet

REM Cài dependencies
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Lỗi khi cài đặt thư viện!
    pause
    exit /b 1
)
echo ✅ Đã cài đặt tất cả thư viện
echo.

REM Tạo thư mục tokens nếu chưa có
echo [4/4] Đang kiểm tra cấu trúc thư mục...
if not exist tokens mkdir tokens
if not exist tokens\token.json (
    echo ℹ️  Thư mục tokens đã sẵn sàng (sẽ tạo token.json khi kết nối Google Sheet)
)
echo.

echo ========================================
echo   ✅ CÀI ĐẶT HOÀN TẤT!
echo ========================================
echo.
echo 📝 Các bước tiếp theo:
echo    1. Double-click vào RUN-DAILY.vbs để chạy ứng dụng
echo    2. Nhập Dailymotion API Key/Secret
echo    3. (Tùy chọn) Kết nối Google Sheet
echo.
echo 📖 Xem hướng dẫn chi tiết trong file: SETUP_INSTRUCTIONS.md
echo.
pause

