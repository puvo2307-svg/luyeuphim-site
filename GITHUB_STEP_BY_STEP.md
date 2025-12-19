# 📋 HƯỚNG DẪN TỪNG BƯỚC - Setup GitHub

## ✅ BƯỚC 1: Tạo Repository (ĐÃ XONG)
- Đã tạo repo `xemfulltap-site` trên GitHub
- Bấm **"Create repository"** → Chuyển sang bước 2

---

## 📤 BƯỚC 2: Push code lên GitHub

### Cách 1: Dùng Git Command (Khuyến nghị)

1. **Mở PowerShell hoặc Command Prompt** trong thư mục `C:\DAILYMONTION`

2. **Chạy lần lượt các lệnh sau:**

```bash
# Khởi tạo git (nếu chưa có)
git init

# Thêm tất cả file
git add .

# Commit
git commit -m "Initial commit - Add auto-export Sheet to JSON"

# Thêm remote GitHub (THAY USERNAME bằng tên GitHub của bạn, ví dụ: puvo2307-svg)
git remote add origin https://github.com/puvo2307-svg/xemfulltap-site.git

# Đổi branch thành main
git branch -M main

# Push lên GitHub
git push -u origin main
```

3. **Nhập username và password/token** khi được hỏi

### Cách 2: Dùng GitHub Desktop (Dễ hơn)

1. Tải GitHub Desktop: https://desktop.github.com/
2. Đăng nhập GitHub
3. File → Add Local Repository → Chọn folder `C:\DAILYMONTION`
4. Bấm **"Publish repository"** → Chọn repo `xemfulltap-site`
5. Bấm **"Publish repository"**

---

## 🔐 BƯỚC 3: Thêm Google Credentials vào GitHub Secrets

1. **Vào repo trên GitHub** → https://github.com/puvo2307-svg/xemfulltap-site

2. **Vào Settings** (tab trên cùng, bên cạnh Code/Pull requests)

3. **Vào Secrets and variables** → **Actions** (menu bên trái)

4. **Bấm "New repository secret"**

5. **Điền:**
   - **Name**: `GOOGLE_CREDENTIALS_JSON`
   - **Secret**: 
     - Mở file `C:\DAILYMONTION\drive_client_secret.json` bằng Notepad
     - Copy **TOÀN BỘ** nội dung (Ctrl+A, Ctrl+C)
     - Paste vào ô Secret

6. **Bấm "Add secret"**

---

## ▶️ BƯỚC 4: Chạy workflow lần đầu

1. **Vào tab "Actions"** (trên cùng, bên cạnh Settings)

2. **Bạn sẽ thấy workflow "Export Sheet to JSON"** → Bấm vào

3. **Bấm "Run workflow"** (góc phải trên)

4. **Chọn branch "main"** → Bấm **"Run workflow"** (nút xanh)

5. **Đợi 1-2 phút** → Workflow sẽ chạy và tạo file `movies.json`

6. **Kiểm tra:**
   - Vào tab **"Code"** → Xem có file `movies.json` chưa
   - Bấm vào file `movies.json` → Xem nội dung có đúng không

---

## 🌐 BƯỚC 5: Cập nhật URL trong index.html (Nếu cần)

### Nếu dùng GitHub Pages:
1. Vào repo → **Settings** → **Pages**
2. Chọn branch `main` → Save
3. Đợi 5 phút → GitHub sẽ cung cấp URL: `https://puvo2307-svg.github.io/xemfulltap-site/`
4. Sửa trong `index.html`:
```javascript
var MOVIES_JSON_URL = "https://raw.githubusercontent.com/puvo2307-svg/xemfulltap-site/main/movies.json";
```

### Nếu dùng Netlify/Vercel:
- File `movies.json` sẽ tự động có tại domain của bạn
- Ví dụ: `https://xemfulltap.live/movies.json`
- Không cần sửa gì trong `index.html`

---

## ✅ KIỂM TRA HOẠT ĐỘNG

1. **Workflow tự động chạy mỗi 10 phút:**
   - Vào tab **Actions** → Xem có workflow chạy không

2. **File `movies.json` tự động update:**
   - Vào tab **Code** → Xem file `movies.json` → Xem "Last commit" có mới không

3. **Web load từ JSON:**
   - Mở website → Mở DevTools (F12) → Tab Network
   - Tìm request `movies.json` → Xem có load được không

---

## 🐛 NẾU GẶP LỖI

### Lỗi: "Cannot find credentials"
→ Kiểm tra Secret `GOOGLE_CREDENTIALS_JSON` đã thêm chưa (Bước 3)

### Lỗi: "Permission denied" khi push
→ Kiểm tra username/password GitHub đúng chưa

### Lỗi: "Service account không có quyền"
→ Share Google Sheet với email trong `drive_client_secret.json` (email có dạng `xxx@xxx.iam.gserviceaccount.com`)

### Workflow không chạy
→ Vào tab Actions → Xem log lỗi → Gửi lỗi cho tôi

---

**Chúc bạn thành công! 🎉**

