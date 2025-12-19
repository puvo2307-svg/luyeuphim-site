# 🚀 HƯỚNG DẪN SETUP GITHUB ACTIONS - Tự động Export Sheet → JSON

## 📋 Mục đích

Tự động export Google Sheet → `movies.json` mỗi 10 phút, giúp web load nhanh và không tốn quota Sheet API.

---

## 🔧 BƯỚC 1: Chuẩn bị Google Credentials

1. **Copy file `drive_client_secret.json`** (Service Account JSON)
2. **Mở file bằng Notepad** → Copy toàn bộ nội dung

---

## 🔧 BƯỚC 2: Thêm Secret vào GitHub

1. Vào **GitHub repo** của bạn (ví dụ: `luyeuphim-site`)
2. Vào **Settings** → **Secrets and variables** → **Actions**
3. Bấm **New repository secret**
4. Điền:
   - **Name**: `GOOGLE_CREDENTIALS_JSON`
   - **Secret**: Paste toàn bộ nội dung file `drive_client_secret.json`
5. Bấm **Add secret**

---

## 🔧 BƯỚC 3: Push code lên GitHub

1. **Commit và push** các file sau:
   - `export_sheet_to_json.py`
   - `.github/workflows/export-sheet.yml`
   - `index.html` (đã cập nhật để load từ JSON)

```bash
git add export_sheet_to_json.py .github/workflows/export-sheet.yml index.html
git commit -m "Add auto-export Sheet to JSON"
git push
```

---

## 🔧 BƯỚC 4: Kiểm tra GitHub Actions

1. Vào tab **Actions** trong GitHub repo
2. Bạn sẽ thấy workflow **"Export Sheet to JSON"**
3. Bấm **Run workflow** → **Run workflow** (để chạy thủ công lần đầu)
4. Đợi workflow chạy xong (khoảng 1-2 phút)
5. Kiểm tra file `movies.json` đã được tạo chưa

---

## 🔧 BƯỚC 5: Cập nhật URL trong index.html

Sau khi `movies.json` đã được tạo trên GitHub:

1. **Nếu dùng Netlify**: File sẽ tự động có tại `https://xemfulltap.live/movies.json`
2. **Nếu dùng GitHub Pages**: Đổi URL trong `index.html`:

```javascript
var MOVIES_JSON_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/movies.json";
```

---

## ✅ Kiểm tra hoạt động

1. **Vào tab Actions** → Xem workflow có chạy mỗi 10 phút không
2. **Mở `movies.json`** trên GitHub → Kiểm tra dữ liệu đã đúng chưa
3. **Mở website** → Kiểm tra web có load từ JSON không (mở DevTools → Network)

---

## ⚠️ Lưu ý

- **Workflow chạy mỗi 10 phút** tự động
- **Có thể chạy thủ công** từ tab Actions → Run workflow
- **Nếu lỗi**: Kiểm tra Secret `GOOGLE_CREDENTIALS_JSON` đã đúng chưa
- **File `movies.json`** sẽ tự động commit và push lên GitHub

---

## 🐛 Troubleshooting

### Lỗi: "Cannot find credentials"
→ Kiểm tra Secret `GOOGLE_CREDENTIALS_JSON` đã thêm chưa

### Lỗi: "Permission denied"
→ Kiểm tra Service Account có quyền đọc Sheet chưa

### JSON không update
→ Kiểm tra workflow có chạy không (tab Actions)

---

**Chúc bạn setup thành công! 🎉**

