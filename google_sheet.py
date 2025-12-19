import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List, Dict, Optional
import os
import json


class GoogleSheetManager:
    def __init__(self, credentials_path: str = None, sheet_name: str = "Dailymotion Videos", token_path: str = None):
        """
        Khởi tạo Google Sheet Manager
        
        Args:
            credentials_path: Đường dẫn đến file credentials JSON (OAuth hoặc Service Account)
            sheet_name: Tên sheet để lưu dữ liệu
            token_path: Đường dẫn đến file token.json (cho OAuth, mặc định: tokens/token.json)
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.token_path = token_path or "tokens/token.json"
        self.client = None
        self.worksheet = None
        self.SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
    def authenticate(self, credentials_path: str = None):
        """Xác thực với Google Sheets API
        
        Hỗ trợ cả Service Account và OAuth Client Credentials (Installed App)
        """
        if credentials_path:
            self.credentials_path = credentials_path
        
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                "Không tìm thấy file credentials. "
                "Vui lòng tạo service account hoặc OAuth client credentials từ Google Cloud Console."
            )
        
        try:
            # Đọc file để kiểm tra loại credentials
            with open(self.credentials_path, 'r', encoding='utf-8') as f:
                creds_data = json.load(f)
            
            # Kiểm tra xem là Service Account hay OAuth Client
            if 'type' in creds_data and creds_data['type'] == 'service_account':
                # Service Account credentials
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES
                )
                self.client = gspread.authorize(creds)
            elif 'installed' in creds_data or 'web' in creds_data:
                # OAuth Client Credentials - sử dụng OAuth flow
                creds = None
                
                # Kiểm tra xem đã có token chưa
                if os.path.exists(self.token_path):
                    try:
                        creds = OAuthCredentials.from_authorized_user_file(
                            self.token_path, self.SCOPES
                        )
                    except Exception:
                        pass
                
                # Nếu token không hợp lệ hoặc hết hạn, refresh hoặc lấy mới
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        # Refresh token
                        creds.refresh(Request())
                    else:
                        # Chạy OAuth flow để lấy token mới
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    
                    # Lưu token để dùng lần sau
                    os.makedirs(os.path.dirname(self.token_path) if os.path.dirname(self.token_path) else '.', exist_ok=True)
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                
                self.client = gspread.authorize(creds)
            else:
                # Thử dùng Service Account format
                try:
                    creds = ServiceAccountCredentials.from_service_account_file(
                        self.credentials_path, scopes=self.SCOPES
                    )
                    self.client = gspread.authorize(creds)
                except Exception:
                    raise Exception(
                        "Không thể xác định loại credentials. "
                        "Vui lòng sử dụng Service Account hoặc OAuth Client credentials JSON."
                    )
        except json.JSONDecodeError:
            raise Exception("File credentials không phải định dạng JSON hợp lệ")
        except Exception as e:
            raise Exception(f"Lỗi khi xác thực Google Sheets: {str(e)}")
    
    def create_or_get_sheet(self, spreadsheet_name: str = None):
        """Tạo hoặc lấy sheet nếu đã tồn tại
        
        Nếu sheet chưa tồn tại, sẽ tự động tạo mới với tên được chỉ định.
        Tự động tạo header với các cột:
        - Tên Bộ Phim, Số Tập, Video ID, Tiêu Đề, Embed URL, Video URL, 
          Thumbnail URL, Trạng Thái, Ngày Upload, Mô Tả
        """
        if not self.client:
            raise Exception("Chưa xác thực. Gọi authenticate() trước.")
        
        if spreadsheet_name:
            self.sheet_name = spreadsheet_name
        
        try:
            # Tìm sheet đã tồn tại
            try:
                spreadsheet = self.client.open(self.sheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                # Tạo sheet mới nếu chưa có
                spreadsheet = self.client.create(self.sheet_name)
                # Chia sẻ với service account email để có quyền truy cập
                # Lưu ý: Cần chia sẻ với email của service account trong Google Drive
            
            # Lấy worksheet đầu tiên (sheet1 luôn tồn tại)
            self.worksheet = spreadsheet.sheet1
            
            # Kiểm tra và tạo header nếu chưa có
            self._ensure_headers()
            
            return self.worksheet
        except Exception as e:
            raise Exception(f"Lỗi khi tạo/lấy sheet: {str(e)}")
    
    def open_by_id(self, spreadsheet_id: str, worksheet_name: str = None):
        """Mở sheet bằng ID (cho sheet có sẵn)"""
        if not self.client:
            raise Exception("Chưa xác thực. Gọi authenticate() trước.")
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            if worksheet_name:
                # Mở worksheet theo tên
                try:
                    self.worksheet = spreadsheet.worksheet(worksheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    # Nếu không tìm thấy, dùng sheet đầu tiên
                    self.worksheet = spreadsheet.sheet1
            else:
                # Dùng worksheet đầu tiên
                self.worksheet = spreadsheet.sheet1
            
            # Đảm bảo có header
            self._ensure_headers()
            
            return self.worksheet
        except Exception as e:
            raise Exception(f"Lỗi khi mở sheet bằng ID: {str(e)}")
    
    def _ensure_headers(self):
        """Đảm bảo worksheet có header, nếu chưa có thì tạo mới
        
        Cấu trúc cột:
        A: Tên Bộ Phim
        B: Số Tập
        C: Tiêu Đề Phim
        D: Link Dailymotion (private link - ai có link xem được)
        E: Embed URL (để nhúng website)
        F: Ngày Upload
        G: Tên Phim Việt
        H: Tóm tắt phim
        I: TOP
        J: Poster URL
        K: Năm
        L: Thể loại
        M: Quốc gia
        N: Xem PC
        O: Banner
        P: Shopee Link
        """
        headers = [
            'Tên Bộ Phim',        # Cột A
            'Số Tập',             # Cột B
            'Tiêu Đề Phim',       # Cột C
            'Link Dailymotion',   # Cột D (private link)
            'Embed URL',          # Cột E
            'Ngày Upload',        # Cột F
            'Tên Phim Việt',      # Cột G
            'Tóm tắt phim',       # Cột H
            'TOP',                # Cột I
            'Poster URL',         # Cột J
            'Năm',                # Cột K
            'Thể loại',           # Cột L
            'Quốc gia',           # Cột M
            'Xem PC',             # Cột N
            'Banner',             # Cột O
            'Shopee Link'         # Cột P
        ]
        
        try:
            first_cell = self.worksheet.get('A1')
            if not first_cell or first_cell == []:
                # Chưa có header, tạo mới
                self.worksheet.append_row(headers)
            else:
                # Kiểm tra xem header có đúng không (tùy chọn)
                existing_headers = self.worksheet.row_values(1)
                if not existing_headers or len(existing_headers) < len(headers):
                    # Header không đầy đủ, có thể cần cập nhật (tùy chọn)
                    pass
        except Exception as e:
            # Nếu lỗi khi đọc, thử tạo header
            try:
                self.worksheet.append_row(headers)
            except:
                pass
    
    def add_video_record(self, film_name: str, episode_number: int, 
                        video_data: Dict, description: str = ""):
        """Thêm record video vào sheet
        
        Cấu trúc:
        - Cột A: Tên Bộ Phim
        - Cột B: Số Tập
        - Cột C: Tiêu Đề Phim
        - Cột D: Link Dailymotion (private link)
        - Cột E: Embed URL
        - Cột F: Ngày Upload
        """
        if not self.worksheet:
            self.create_or_get_sheet()
        
        from datetime import datetime
        
        # Lấy các thông tin cần thiết
        title = video_data.get('title', '')
        video_url = video_data.get('url', '')  # Private link (ai có link xem được)
        embed_url = video_data.get('embed_url', '')
        upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        row = [
            film_name,                    # Cột A: Tên Bộ Phim
            f"Tập {episode_number}",      # Cột B: Số Tập
            title,                        # Cột C: Tiêu Đề Phim
            video_url,                    # Cột D: Link Dailymotion (private)
            embed_url,                    # Cột E: Embed URL
            upload_date                   # Cột F: Ngày Upload
        ]
        
        try:
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            raise Exception(f"Lỗi khi thêm record vào sheet: {str(e)}")
    
    def add_playlist_record(self, film_name: str, playlist_id: str, 
                           playlist_title: str, total_episodes: int,
                           playlist_url: str = '', playlist_embed_url: str = ''):
        """Thêm record playlist vào sheet
        
        Cấu trúc:
        - Cột A: Tên Bộ Phim
        - Cột B: "Playlist"
        - Cột C: Tiêu Đề (Playlist title)
        - Cột D: Link Dailymotion (playlist URL)
        - Cột E: Embed URL
        - Cột F: Ngày Upload
        """
        if not self.worksheet:
            self.create_or_get_sheet()
        
        from datetime import datetime
        
        row = [
            film_name,                    # Cột A: Tên Bộ Phim
            'Playlist',                   # Cột B: Loại (Playlist)
            playlist_title,                # Cột C: Tiêu Đề
            playlist_url,                 # Cột D: Link Dailymotion
            playlist_embed_url,           # Cột E: Embed URL
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Cột F: Ngày Upload
        ]
        
        try:
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            raise Exception(f"Lỗi khi thêm playlist record vào sheet: {str(e)}")
    
    def add_channel_video_record(self, film_name: str, episode_number: int,
                                 video_url: str, embed_url: str,
                                 channel_id: str, upload_date: str):
        """Thêm record video (cho chế độ quét kênh) vào sheet.
        
        Cấu trúc sheet (6 cột đầu):
        - Cột A: Tên Bộ Phim
        - Cột B: Số Tập (số nguyên: 1, 2, 3, ...)
        - Cột C: Link Dailymotion (URL video)
        - Cột D: Embed URL
        - Cột E: ID Kênh
        - Cột F: Ngày Lấy / Ngày Upload
        """
        if not self.worksheet:
            self.create_or_get_sheet()
        
        try:
            ep_int = int(episode_number)
        except Exception:
            ep_int = episode_number

        row = [
            film_name,       # A: Tên Bộ Phim
            ep_int,          # B: Số Tập (1, 2, 3, ...)
            video_url,       # C: Link Dailymotion
            embed_url,       # D: Embed URL
            channel_id,      # E: ID Kênh
            upload_date,     # F: Ngày lấy
        ]
        
        try:
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            raise Exception(f"Lỗi khi thêm channel video record vào sheet: {str(e)}")
    
    def get_all_records(self) -> List[Dict]:
        """Lấy tất cả records từ sheet"""
        if not self.worksheet:
            self.create_or_get_sheet()
        
        try:
            records = self.worksheet.get_all_records()
            return records
        except Exception as e:
            raise Exception(f"Lỗi khi lấy records: {str(e)}")

