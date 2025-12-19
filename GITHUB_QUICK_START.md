# 🚀 HƯỚNG DẪN NHANH - Setup GitHub Auto-Export JSON

## 📝 Các bước cần làm:

### 1️⃣ Tạo GitHub Repository
- Vào https://github.com/new
- Tạo repo mới (ví dụ: `xemfulltap-site`)
- **KHÔNG** tích "Add a README file" (nếu repo trống)

### 2️⃣ Push code lên GitHub

```bash
# Nếu chưa có git init
git init
git add .
git commit -m "Initial commit"

# Thêm remote GitHub
git remote add origin https://github.com/USERNAME/xemfulltap-site.git
git branch -M main
git push -u origin main
```

**Hoặc dùng GitHub Desktop/Git GUI**

### 3️⃣ Thêm Google Credentials vào GitHub Secrets

1. Vào repo trên GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Bấm **New repository secret**
3. Điền:
   - **Name**: `GOOGLE_CREDENTIALS_JSON`
   - **Value**: Copy toàn bộ nội dung file `drive_client_secret.json` (mở bằng Notepad)
4. Bấm **Add secret**

### 4️⃣ Chạy workflow lần đầu

1. Vào tab **Actions** trong GitHub repo
2. Bạn sẽ thấy workflow **"Export Sheet to JSON"**
3. Bấm vào workflow → **Run workflow** → **Run workflow** (để chạy thủ công)
4. Đợi 1-2 phút → Kiểm tra file `movies.json` đã được tạo chưa

### 5️⃣ Cập nhật URL trong index.html (nếu cần)

Nếu dùng **GitHub Pages**:
```javascript
var MOVIES_JSON_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/movies.json";
```

Nếu dùng **Netlify/Vercel**: File `movies.json` sẽ tự động có tại domain của bạn.

---

## ✅ Kiểm tra

- Workflow chạy mỗi 10 phút tự động
- File `movies.json` tự động update
- Web load từ JSON thay vì Sheet trực tiếp

---

## 🐛 Lỗi thường gặp

**"Cannot find credentials"**
→ Kiểm tra Secret `GOOGLE_CREDENTIALS_JSON` đã thêm chưa

**"Permission denied"**
→ Kiểm tra Service Account có quyền đọc Sheet chưa (share Sheet với email trong `drive_client_secret.json`)

**Workflow không chạy**
→ Vào tab Actions → Kiểm tra có lỗi gì không

---

**Xong! 🎉**

