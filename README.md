# Dailymotion Auto Uploader

Ứng dụng GUI tự động upload video lên Dailymotion với các tính năng:
- Tự động lấy và làm mới token mỗi 55 phút
- Upload tự động các file part từ folder
- Tự động đặt tiêu đề theo số tập
- Tạo playlist trọn bộ phim
- Lưu embed links vào Google Sheet

## Cài Đặt

1. Cài đặt Python 3.7 trở lên

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cấu Hình

### 1. Dailymotion API Credentials

Bạn cần có:
- **API Key**: Từ Dailymotion Developer Console
- **API Secret**: Từ Dailymotion Developer Console  
- **Username/Partner ID**: Username của bạn (ví dụ: `lyeuphim`)
- **Channel ID** (tùy chọn): Category của video (ví dụ: `entertainment`)

**⚠️ QUAN TRỌNG - Yêu Cầu API Key:**
- **PHẢI DÙNG PRIVATE API KEY** (không phải Public API Key!)
- Public API Key **KHÔNG THỂ** upload video qua Partner API
- Chỉ Private API Key mới có quyền truy cập endpoint `/rest/file/upload`

**⚠️ VẤN ĐỀ: Nếu tất cả API Key đều là PUBLIC:**
- Để tạo **Private API Key**, bạn cần tài khoản **Pro Advanced** hoặc **Enterprise**
- Tài khoản Partner miễn phí (Starter) **CHỈ CÓ THỂ** tạo Public API Key
- Public API Key **KHÔNG THỂ** upload video qua Partner API

**Giải pháp:**
1. **Nâng cấp tài khoản** lên Advanced hoặc Enterprise để có quyền tạo Private API Key
2. **Hoặc liên hệ Dailymotion support**: https://www.dailymotion.com/partner/contact
3. Kiểm tra trong Organization → Settings xem có tùy chọn nâng cấp không

**Cách tạo Private API Key:**
1. Vào Dailymotion Studio: https://www.dailymotion.com/partner
2. Vào Organization → API keys
3. Nhấn "Create API key" (nút tạo mới)
4. Điền thông tin và tạo
5. **QUAN TRỌNG**: Kiểm tra xem API Key mới có label "PRIVATE" không (không phải "PUBLIC")
6. Nếu vẫn là PUBLIC, có thể cần:
   - Upgrade tài khoản Partner
   - Hoặc liên hệ Dailymotion support: https://www.dailymotion.com/partner/contact
7. Copy API Key và API Secret mới vào app

**Lưu ý**: 
- Với **Private API Key**: Có thể dùng client_credentials grant type (app này dùng cách này)
- Với **Public API Key**: Cần OAuth flow với authorization code (KHÔNG đủ cho app này)

### 2. Google Sheet (Tùy chọn)

Để lưu embed links vào Google Sheet:

1. Tạo Service Account trên Google Cloud Console
2. Download file credentials JSON
3. Chia sẻ Google Sheet với email của Service Account
4. Chọn file credentials trong ứng dụng

## Sử Dụng

1. Chạy ứng dụng:
```bash
python main.py
```

2. Nhập thông tin:
   - **API Key**: Nhập API Key của bạn
   - **API Secret**: Nhập API Secret của bạn
   - **Channel ID**: Nhập Channel ID
   - **Tiêu Đề Bộ Phim**: Tên bộ phim (ví dụ: "入职保安我能偷听美女心声")
   - **Mô Tả**: Mô tả bộ phim (sẽ tự động thêm "Tập X" vào đầu)
   - **Folder Chứa Phim**: Chọn folder chứa các file part*.mp4

3. (Tùy chọn) Cấu hình Google Sheet:
   - Chọn file credentials JSON
   - Sheet sẽ tự động được tạo nếu chưa có

4. Nhấn **"Bắt Đầu Upload"**

## Cấu Trúc Folder

Folder bạn chọn nên chứa các file video với tên:
- `part1.mp4`, `part2.mp4`, ... `partN.mp4`
- Hoặc `*-part1.mp4`, `*-part2.mp4`, ...

Ứng dụng sẽ tự động:
- Tìm tất cả file `*part*.mp4`
- Sắp xếp theo số part
- Upload từng file với tiêu đề "Tập 1 - [Tên phim]", "Tập 2 - [Tên phim]", ...

## Tính Năng

### Tự Động Làm Mới Token
- Token được tự động làm mới mỗi 55 phút
- Đảm bảo không bị hết hạn trong quá trình upload

### Upload Tự Động
- Quét folder và tìm tất cả file part
- Upload từng video với tiêu đề và mô tả tự động
- Chế độ private (không công khai)
- Lấy embed URL sau khi upload

### Tạo Playlist
- Tự động tạo playlist "Trọn Bộ - [Tên phim]"
- Thêm tất cả các tập vào playlist

### Google Sheet Integration
- Tự động lưu thông tin video vào Google Sheet
- Bao gồm: Video ID, Embed URL, Video URL, Thumbnail URL
- Dễ dàng quản lý và chia sẻ links

## Cấu Trúc Dữ Liệu Google Sheet

Sheet sẽ có các cột:
- Tên Bộ Phim
- Số Tập
- Video ID
- Tiêu Đề
- Embed URL
- Video URL
- Thumbnail URL
- Trạng Thái
- Ngày Upload
- Mô Tả

## Lưu Ý

1. **Token Expiration**: Token được làm mới tự động mỗi 55 phút
2. **Upload Limits**: Kiểm tra giới hạn upload của tài khoản Dailymotion
3. **File Format**: Chỉ hỗ trợ file .mp4
4. **Network**: Cần kết nối internet ổn định để upload
5. **Private Mode**: Tất cả video được upload ở chế độ private (không công khai)

## Xử Lý Lỗi

- Nếu lỗi authentication: Kiểm tra lại API Key và API Secret
- Nếu lỗi upload: Kiểm tra kết nối internet và quyền của channel
- Nếu lỗi Google Sheet: Kiểm tra file credentials và quyền truy cập

## Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. Log trong cửa sổ ứng dụng
2. API credentials có đúng không
3. Channel ID có đúng không
4. File video có tồn tại và đúng format không

