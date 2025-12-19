import requests
import time
import os
import re
from typing import Dict, List, Optional
import json


class DailymotionAPI:
    def __init__(self, api_key: str, api_secret: str, log_callback=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = "https://api.dailymotion.com"  # Cho OAuth token
        # Thử cả Partner API và Public API endpoints
        self.partner_api_url = "https://partner.api.dailymotion.com/rest"  # Cho Partner API (Private Key)
        self.public_api_url = "https://api.dailymotion.com"  # Cho Public API (Public Key)
        self.upload_base_url = "https://upload-XXX.dailymotion.com"
        self.log_callback = log_callback  # Callback để log vào GUI
        
    def get_access_token(self) -> str:
        """Lấy access token với scope manage_videos
        
        Hỗ trợ cả Private API Key (client_credentials) và Public API Key (cần OAuth)
        """
        # Kiểm tra nếu token còn hợp lệ (còn ít nhất 5 phút)
        current_time = time.time()
        if self.access_token and self.token_expires_at > current_time + 300:
            return self.access_token
        
        # Lấy token mới - Thử client_credentials trước (cho Private API Key)
        # Thử request với nhiều scopes để có đủ quyền cho upload
        url = f"{self.base_url}/oauth/token"
        
        # Chỉ dùng scope hợp lệ: manage_videos (file_upload không tồn tại trong Dailymotion API)
        scopes_to_try = ['manage_videos']
        last_error = None
        
        for scope in scopes_to_try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'scope': scope
            }
            
            try:
                response = requests.post(url, data=data)
                response.raise_for_status()
                token_data = response.json()
                
                # Debug: Log vào GUI nếu có callback
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Token request URL: {url}")
                    self.log_callback(f"[DEBUG] Token request scope: {scope}")
                    self.log_callback(f"[DEBUG] Token response status: {response.status_code}")
                
                self.access_token = token_data.get('access_token')
                
                if not self.access_token:
                    error_msg = "Không lấy được access_token từ response"
                    if self.log_callback:
                        self.log_callback(f"❌ {error_msg}")
                        self.log_callback(f"📋 Token response: {json.dumps(token_data, indent=2, ensure_ascii=False)[:500]}")
                    raise Exception(error_msg)
                
                # Lưu lại danh sách quyền (scopes) thực tế được cấp
                # Kiểm tra nhiều cách để lấy scope
                scope_value = token_data.get('scope') or token_data.get('scopes') or token_data.get('granted_scopes') or ''
                if isinstance(scope_value, list):
                    scope_value = ' '.join(scope_value)
                if isinstance(scope_value, dict):
                    scope_value = ' '.join(scope_value.keys()) if scope_value else ''
                if not scope_value or scope_value == '':
                    scope_value = 'Không có quyền nào'
                    # Log cảnh báo ngay lập tức
                    if self.log_callback:
                        self.log_callback(f"⚠️ CẢNH BÁO: Token response không có scope field!")
                        self.log_callback(f"⚠️ Có thể API Key chưa được cấp quyền trong Dailymotion Organization")
                        # Log full response để debug
                        try:
                            full_response = json.dumps(token_data, indent=2, ensure_ascii=False)
                            # Chỉ log 500 ký tự đầu để không quá dài
                            if len(full_response) > 500:
                                full_response = full_response[:500] + "..."
                            self.log_callback(f"📋 Token response: {full_response}")
                        except Exception as e:
                            self.log_callback(f"📋 Token response: {str(token_data)[:500]}")
                            self.log_callback(f"📋 Error logging response: {str(e)}")
                
                self.granted_scopes = scope_value
                
                # LUÔN log scope để debug - đảm bảo được gọi NGAY LẬP TỨC
                log_msg = f"[DEBUG] Token Scopes được cấp: {self.granted_scopes}"
                if self.log_callback:
                    try:
                        self.log_callback(log_msg)
                    except Exception as e:
                        print(f"Error in log_callback: {e}")
                        print(log_msg)
                else:
                    print(log_msg)
                
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = current_time + expires_in
                return self.access_token
            except requests.exceptions.HTTPError as e:
                last_error = e
                last_response = response
                # Nếu scope đầu tiên lỗi, thử scope tiếp theo
                if scope == scopes_to_try[-1]:  # Đã thử hết các scope
                    # Nếu lỗi 400, có thể là Public API Key cần OAuth flow
                    if last_response.status_code == 400:
                        error_data = last_response.json() if last_response.content else {}
                        error_msg = error_data.get('error_description', '')
                        if 'authorization_code' in error_msg.lower() or 'redirect_uri' in error_msg.lower():
                            raise Exception(
                                "Public API Key cần OAuth flow. "
                                "Vui lòng sử dụng Private API Key hoặc implement OAuth flow."
                            )
                    raise Exception(f"Lỗi khi lấy access token: {str(last_error)}")
                # Tiếp tục thử scope tiếp theo
                continue
            except requests.exceptions.RequestException as e:
                raise Exception(f"Lỗi khi lấy access token: {str(e)}")
    
    def get_user_id(self) -> str:
        """Lấy user ID từ token (Thử nhiều cách để tương thích Private Key)"""
        token = self.get_access_token()
        
        # Cách 1: Thử endpoint /me
        try:
            url = f"{self.base_url}/me"
            params = {'fields': 'id,username'}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get('id') or user_data.get('username', '')
        except:
            pass

        # Cách 2: Lấy từ chính thông tin Token (nếu có uid)
        # Thường Private Key gắn với Organization, cần lấy ID của Owner
        return None
    
    def get_upload_url(self, username: str = None) -> Dict[str, str]:
        """Lấy upload URL từ Dailymotion
        
        Thử cả Partner API và Public API endpoints:
        - Partner API: https://partner.api.dailymotion.com/rest/file/upload (cho Private Key)
        - Public API: https://api.dailymotion.com/file/upload (cho Public Key)
        
        Args:
            username: Username/Partner ID (có thể cần để xác định channel)
        """
        token = self.get_access_token()
        
        # Chỉ dùng Partner API endpoint (Public API không có endpoint /file/upload)
        urls_to_try = [
            f"{self.partner_api_url}/file/upload"
        ]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
        
        last_error = None
        last_response = None
        for url in urls_to_try:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                last_error = e
                last_response = response
                # Nếu lỗi 401 và còn endpoint khác, thử tiếp
                if response.status_code == 401 and url != urls_to_try[-1]:
                    if self.log_callback:
                        self.log_callback(f"⚠️ Thử endpoint khác: {url} -> 401, thử endpoint tiếp theo...")
                    continue
                # Nếu đã thử hết, xử lý lỗi
                if url == urls_to_try[-1]:
                    # Nếu lỗi 401, invalidate token để lấy token mới ở lần gọi tiếp theo
                    if response.status_code == 401:
                        self.access_token = None
                        self.token_expires_at = 0
                    
                    # Thêm thông tin chi tiết về lỗi
                    error_detail = ""
                    if response.status_code == 401:
                        error_detail = "\n💡 Lỗi 401 Unauthorized: Token không có quyền truy cập endpoint /file/upload"
                        error_detail += f"\n   - Token scopes hiện tại: {getattr(self, 'granted_scopes', 'Không rõ')}"
                        error_detail += "\n   - Đã invalidate token, sẽ lấy token mới ở lần gọi tiếp theo"
                        error_detail += "\n   ⚠️ QUAN TRỌNG: Endpoint /file/upload chỉ dành cho Private API Key!"
                        error_detail += "\n   💡 Bạn cần:"
                        error_detail += "\n      1. Đảm bảo API Key là Private API Key (không phải Public)"
                        error_detail += "\n      2. API Key có quyền manage_videos"
                        error_detail += "\n      3. Nếu vẫn lỗi, có thể cần liên hệ Dailymotion support để kiểm tra"
                        if response.content:
                            try:
                                error_data = response.json()
                                error_detail += f"\n   - Chi tiết: {error_data}"
                            except:
                                error_detail += f"\n   - Response: {response.text[:200]}"
                    else:
                        if response.content:
                            try:
                                error_data = response.json()
                                error_detail = f" - {error_data}"
                            except:
                                error_detail = f" - {response.text[:200]}"
                    raise Exception(f"Lỗi khi lấy upload URL: {str(last_error)}{error_detail}")
            except requests.exceptions.RequestException as e:
                last_error = e
                if url == urls_to_try[-1]:
                    raise Exception(f"Lỗi khi lấy upload URL: {str(e)}")
                continue
        
        # Nếu đến đây mà không có lỗi, có vấn đề logic
        if last_error:
            raise Exception(f"Lỗi khi lấy upload URL: {str(last_error)}")
    
    def upload_video_file(self, file_path: str, progress_callback=None, username: str = None) -> Dict:
        """Upload video file lên Dailymotion
        
        Theo tài liệu: URL upload cần thêm /-1 vào cuối
        Format: https://{upload_server}.dailymotion.com/{path}/-1
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        # Lấy upload URL (truyền username nếu có)
        upload_info = self.get_upload_url(username=username)
        upload_url = upload_info.get('upload_url')
        
        if not upload_url:
            raise Exception("Không lấy được upload URL")
        
        # Thêm /-1 vào cuối upload URL theo tài liệu
        if not upload_url.endswith('/-1'):
            upload_url = upload_url.rstrip('/') + '/-1'
        
        # Upload file với headers đúng format và retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
                    headers = {
                        "accept": "application/json"
                    }
                    # requests sẽ tự động set content-type: multipart/form-data khi dùng files=
                    
                    # Upload với progress tracking nếu có callback
                    # Tăng timeout cho upload file lớn
                    response = requests.post(
                        upload_url, 
                        files=files, 
                        headers=headers, 
                        stream=True,
                        timeout=(30, 300)  # Connect timeout: 30s, Read timeout: 5 phút
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return result
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    if self.log_callback:
                        self.log_callback(f"⚠️ Lỗi connection/timeout, thử lại lần {attempt + 2}/{max_retries}...")
                    time.sleep(2)  # Đợi 2 giây trước khi retry
                    continue
                else:
                    raise Exception(f"Lỗi khi upload file sau {max_retries} lần thử: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Lỗi khi upload file: {str(e)}")
    
    def create_video(self, video_url: str, title: str, description: str, 
                     channel_id: str = None, username: str = None, private: bool = True, 
                     is_created_for_kids: bool = False) -> Dict:
        """Tạo video trên Dailymotion
        
        Args:
            video_url: URL của video đã upload
            title: Tiêu đề video
            description: Mô tả video
            channel_id: Channel ID (category như "entertainment")
            username: Username/Partner ID (như "x44ibi8") - ưu tiên hơn channel_id
            private: Video ở chế độ private
            is_created_for_kids: Video dành cho trẻ em
        """
        token = self.get_access_token()
        
        # Trim whitespace từ username và channel_id
        username = username.strip() if username else None
        channel_id = channel_id.strip() if channel_id else None
        
        # Ưu tiên dùng username, sau đó channel_id
        # Sử dụng Partner API endpoint
        if username:
            url = f"{self.partner_api_url}/user/{username}/videos"
        elif channel_id:
            url = f"{self.partner_api_url}/user/{channel_id}/videos"
        else:
            raise Exception(
                "Cần cung cấp username hoặc channel_id. "
                "Token client_credentials không hỗ trợ /me/videos."
            )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Theo tài liệu Dailymotion: url, title, channel, published, private, is_created_for_kids là bắt buộc
        data = {
            'url': video_url,
            'title': title,
            'description': description,
            'published': 'true',
            'private': 'true' if private else 'false',
            'is_created_for_kids': 'true' if is_created_for_kids else 'false',
            'channel': 'entertainment'  # Category bắt buộc
        }
        
        # Loại bỏ description nếu rỗng (không bắt buộc)
        if not description:
            data.pop('description', None)
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Hiển thị lỗi chi tiết hơn
            error_detail = ""
            if response.content:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {})
                    if isinstance(error_msg, dict):
                        error_detail = f" - {error_msg.get('message', error_msg.get('type', ''))}"
                    else:
                        error_detail = f" - {error_data}"
                except:
                    error_detail = f" - {response.text[:200]}"
            
            # Thêm thông tin về URL đã dùng
            url_info = f" (URL: {url})"
            raise Exception(f"Lỗi khi tạo video: {str(e)}{error_detail}{url_info}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi tạo video: {str(e)}")
    
    def extract_video_id(self, video_url_or_id: str) -> str:
        """Extract video ID từ URL hoặc trả về ID nếu đã là ID
        
        Hỗ trợ các format:
        - https://www.dailymotion.com/video/x123456
        - https://dailymotion.com/video/x123456
        - x123456
        - 123456
        """
        video_url_or_id = video_url_or_id.strip()
        
        # Nếu đã là ID (bắt đầu bằng 'x' hoặc chỉ có số/chữ)
        if not video_url_or_id.startswith('http'):
            # Nếu không có 'x' ở đầu, thêm vào
            if not video_url_or_id.startswith('x'):
                video_id = 'x' + video_url_or_id
            else:
                video_id = video_url_or_id
            return video_id
        
        # Extract từ URL
        # Format: https://www.dailymotion.com/video/x123456
        patterns = [
            r'dailymotion\.com/video/([a-zA-Z0-9]+)',
            r'dailymotion\.com/embed/video/([a-zA-Z0-9]+)',
            r'/video/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url_or_id)
            if match:
                video_id = match.group(1)
                # Đảm bảo có 'x' ở đầu
                if not video_id.startswith('x'):
                    video_id = 'x' + video_id
                return video_id
        
        raise Exception(f"Không thể extract video ID từ URL: {video_url_or_id}")
    
    def get_video_info(self, video_id: str) -> Dict:
        """Lấy thông tin video bao gồm embed URL
        
        Args:
            video_id: Video ID hoặc URL (sẽ tự động extract ID)
        
        Ghi chú:
            - Dùng PUBLIC API endpoint: https://api.dailymotion.com/video/{id}
            - Endpoint này hoạt động với PUBLIC API KEY cho các thao tác đọc.
        """
        # Extract video ID nếu là URL
        if video_id.startswith('http'):
            video_id = self.extract_video_id(video_id)
        
        token = self.get_access_token()
        # Dùng public API cho thao tác đọc thông tin video
        url = f"{self.base_url}/video/{video_id}"
        params = {
            'fields': 'id,title,description,embed_url,url,thumbnail_url,private,created_time'
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")
    
    def create_playlist(self, username: str = None, channel_id: str = None, 
                       title: str = "", description: str = "", 
                       video_ids: List[str] = None) -> Dict:
        """Tạo playlist với danh sách video
        
        Args:
            username: Username/Partner ID (ưu tiên)
            channel_id: Channel ID (backup)
            title: Tiêu đề playlist
            description: Mô tả playlist
            video_ids: Danh sách video IDs
        
        Returns:
            Dict chứa thông tin playlist bao gồm id, name, embed_url, url
        """
        token = self.get_access_token()
        
        # Trim whitespace từ username và channel_id
        username = username.strip() if username else None
        channel_id = channel_id.strip() if channel_id else None
        
        # Ưu tiên dùng username, sau đó channel_id
        # Sử dụng Partner API endpoint
        if username:
            url = f"{self.partner_api_url}/user/{username}/playlists"
        elif channel_id:
            url = f"{self.partner_api_url}/user/{channel_id}/playlists"
        else:
            raise Exception(
                "Cần cung cấp username hoặc channel_id để tạo playlist. "
                "Token client_credentials không hỗ trợ /me/playlists."
            )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Tạo playlist
        data = {
            'name': title,
            'description': description,
            'published': 'true',
            'private': 'true'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            playlist_data = response.json()
            playlist_id = playlist_data.get('id')
            
            # Thêm videos vào playlist
            if playlist_id and video_ids:
                self.add_videos_to_playlist(playlist_id, video_ids, username=username, channel_id=channel_id)
                
                # Lấy thông tin đầy đủ của playlist sau khi thêm videos
                try:
                    full_info = self.get_playlist_info(playlist_id)
                    playlist_data.update(full_info)
                except Exception as e:
                    print(f"Cảnh báo: Không thể lấy thông tin đầy đủ playlist: {str(e)}")
            
            return playlist_data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi tạo playlist: {str(e)}")
    
    def add_videos_to_playlist(self, playlist_id: str, video_ids: List[str], 
                               username: str = None, channel_id: str = None):
        """Thêm videos vào playlist
        
        Args:
            playlist_id: ID của playlist
            video_ids: Danh sách video IDs
            username: Username/Partner ID (ưu tiên)
            channel_id: Channel ID (backup)
        """
        token = self.get_access_token()
        
        # Trim whitespace từ username và channel_id
        username = username.strip() if username else None
        channel_id = channel_id.strip() if channel_id else None
        
        # Ưu tiên dùng username, sau đó channel_id
        # Sử dụng Partner API endpoint
        if username:
            url = f"{self.partner_api_url}/user/{username}/playlists/{playlist_id}/videos"
        elif channel_id:
            url = f"{self.partner_api_url}/user/{channel_id}/playlists/{playlist_id}/videos"
        else:
            raise Exception(
                "Cần cung cấp username hoặc channel_id để thêm video vào playlist. "
                "Token client_credentials không hỗ trợ /me/playlists."
            )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Thêm từng video
        for video_id in video_ids:
            data = {'video': video_id}
            try:
                response = requests.post(url, headers=headers, data=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Cảnh báo: Không thể thêm video {video_id} vào playlist: {str(e)}")
    
    def get_playlist_info(self, playlist_id: str) -> Dict:
        """Lấy thông tin playlist bao gồm embed URL và link
        
        Args:
            playlist_id: Playlist ID hoặc URL (sẽ tự động extract ID)
        """
        # Extract playlist ID nếu là URL
        if playlist_id.startswith('http'):
            playlist_id = self.extract_playlist_id(playlist_id)
        
        token = self.get_access_token()
        # Dùng PUBLIC API endpoint cho thao tác đọc thông tin playlist
        url = f"{self.base_url}/playlist/{playlist_id}"
        params = {
            'fields': 'id,name,description,embed_url,url,thumbnail_url,private,videos_total'
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi lấy thông tin playlist: {str(e)}")
    
    def extract_playlist_id(self, playlist_url: str) -> str:
        """Extract playlist ID từ URL
        
        Hỗ trợ các format:
        - https://www.dailymotion.com/playlist/x123456
        - x123456
        """
        playlist_url = playlist_url.strip()
        
        # Nếu đã là ID
        if not playlist_url.startswith('http'):
            if not playlist_url.startswith('x'):
                return 'x' + playlist_url
            return playlist_url
        
        # Extract từ URL
        patterns = [
            r'dailymotion\.com/playlist/([a-zA-Z0-9]+)',
            r'/playlist/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, playlist_url)
            if match:
                playlist_id = match.group(1)
                if not playlist_id.startswith('x'):
                    playlist_id = 'x' + playlist_id
                return playlist_id
        
        raise Exception(f"Không thể extract playlist ID từ URL: {playlist_url}")
    
    def get_playlist_videos(self, playlist_id: str, limit: int = 100) -> List[Dict]:
        """Lấy danh sách tất cả video trong playlist
        
        Args:
            playlist_id: Playlist ID hoặc URL
            limit: Số lượng video tối đa (mặc định 100)
        
        Returns:
            List các video dict với thông tin đầy đủ
        """
        # Extract playlist ID nếu là URL
        if playlist_id.startswith('http'):
            playlist_id = self.extract_playlist_id(playlist_id)
        
        token = self.get_access_token()
        # Dùng PUBLIC API endpoint cho thao tác đọc danh sách video từ playlist
        url = f"{self.base_url}/playlist/{playlist_id}/videos"
        params = {
            'fields': 'id,title,description,embed_url,url,thumbnail_url,private,created_time',
            'limit': limit
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            if self.log_callback:
                self.log_callback(f"[DEBUG] Đang lấy video từ playlist: {playlist_id}")
                self.log_callback(f"[DEBUG] URL: {url}")
            
            response = requests.get(url, headers=headers, params=params)
            
            # Log response để debug
            if self.log_callback:
                self.log_callback(f"[DEBUG] Response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            # Log response data để debug
            if self.log_callback:
                self.log_callback(f"[DEBUG] Response data keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            
            # Trả về list videos
            if 'list' in data:
                videos = data['list']
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Tìm thấy {len(videos)} video trong playlist")
                return videos
            elif isinstance(data, list):
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Tìm thấy {len(data)} video trong playlist (direct list)")
                return data
            else:
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Response không phải list, keys: {list(data.keys()) if isinstance(data, dict) else 'unknown'}")
                return []
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            if response.content:
                try:
                    error_data = response.json()
                    error_detail = f" - {error_data}"
                    if self.log_callback:
                        self.log_callback(f"[DEBUG] Error response: {error_data}")
                except:
                    error_detail = f" - {response.text[:200]}"
            raise Exception(f"Lỗi khi lấy danh sách video từ playlist (HTTP {response.status_code}): {str(e)}{error_detail}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi lấy danh sách video từ playlist: {str(e)}")
    
    def get_user_videos(self, user_id: str, max_videos: int = 1000) -> List[Dict]:
        """Lấy danh sách video PUBLIC của một kênh/user.
        
        Args:
            user_id: Username hoặc user ID (ví dụ: 'luyeuphim')
            max_videos: Số video tối đa muốn lấy
        
        Lưu ý:
            - Chỉ trả về các video không private (public / unlisted)
            - Sử dụng PUBLIC API endpoint: /user/{id}/videos
        """
        token = self.get_access_token()
        url = f"{self.base_url}/user/{user_id}/videos"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        all_videos: List[Dict] = []
        page = 1
        limit = 100
        
        while len(all_videos) < max_videos:
            params = {
                "fields": "id,title,url,thumbnail_url,created_time,private",
                "page": page,
                "limit": limit,
                "sort": "recent"  # video mới nhất trước
            }
            try:
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Đang lấy videos của user {user_id}, page {page}")
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                videos = data.get("list", [])
                all_videos.extend(videos)
                
                if self.log_callback:
                    self.log_callback(f"[DEBUG] Page {page}: lấy {len(videos)} video (tổng {len(all_videos)})")
                
                # Dừng nếu hết hoặc đạt max_videos
                has_more = data.get("has_more", False)
                if not has_more or not videos or len(all_videos) >= max_videos:
                    break
                
                page = data.get("page", page) + 1
            except requests.exceptions.RequestException as e:
                raise Exception(f"Lỗi khi lấy danh sách video của user {user_id}: {str(e)}")
        
        return all_videos[:max_videos]
    
    def upload_and_publish(self, file_path: str, title: str, description: str,
                          username: str = None, channel_id: str = None, private: bool = True,
                          progress_callback=None) -> Dict:
        """Upload video và publish trong một bước
        
        Args:
            file_path: Đường dẫn file video
            title: Tiêu đề video
            description: Mô tả video
            username: Username/Partner ID (ưu tiên)
            channel_id: Channel ID (backup)
            private: Video ở chế độ private
            progress_callback: Callback để hiển thị tiến trình
        """
        # Bước 1: Upload file
        if progress_callback:
            progress_callback("Đang upload file...")
        upload_result = self.upload_video_file(file_path, progress_callback, username=username)
        video_url = upload_result.get('url')
        
        if not video_url:
            raise Exception("Không lấy được video URL sau khi upload")
        
        # Bước 2: Tạo và publish video
        if progress_callback:
            progress_callback("Đang tạo video...")
        video_data = self.create_video(
            video_url=video_url,
            title=title,
            description=description,
            username=username,
            channel_id=channel_id,
            private=private
        )
        
        video_id = video_data.get('id')
        if not video_id:
            raise Exception("Không tạo được video")
        
        # Bước 3: Lấy thông tin đầy đủ bao gồm embed URL
        if progress_callback:
            progress_callback("Đang lấy thông tin video...")
        video_info = self.get_video_info(video_id)
        
        return {
            'video_id': video_id,
            'title': video_info.get('title'),
            'embed_url': video_info.get('embed_url'),
            'url': video_info.get('url'),
            'thumbnail_url': video_info.get('thumbnail_url'),
            'private': video_info.get('private')
        }

