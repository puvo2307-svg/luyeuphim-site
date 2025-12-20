#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script export Google Sheet → JSON
Chạy tự động mỗi 5-10 phút qua GitHub Actions
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os
import sys

# Config
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = "1KxEhDNIH7AdgSBSL05s4jQnPghLOo2MI8wvgBxTXv7w"
SHEET_NAME = "Sheet4"
CREDENTIALS_FILE = "drive_client_secret.json"
OUTPUT_FILE = "movies.json"

def export_sheet_to_json():
    """Export Sheet → JSON format cho web"""
    try:
        # Authenticate
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"❌ Không tìm thấy file: {CREDENTIALS_FILE}")
            sys.exit(1)
        
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        
        # Lấy tất cả records
        rows = sheet.get_all_records()
        
        # Gom theo Tên Bộ Phim (A)
        movies = {}
        banners = []
        
        for row in rows:
            film_name = row.get('Tên Bộ Phim', '').strip()
            if not film_name:
                # Có thể là dòng banner (chỉ có cột O - Banner)
                banner = row.get('Banner', '').strip()
                if banner and banner.startswith('http'):
                    # Kiểm tra xem banner này đã có chưa (tránh trùng)
                    banner_exists = False
                    for b in banners:
                        if isinstance(b, dict) and b.get('url') == banner:
                            banner_exists = True
                            break
                        elif isinstance(b, str) and b == banner:
                            banner_exists = True
                            break
                    
                    if not banner_exists:
                        # Banner không gắn với phim nào (movieId = null)
                        banners.append({
                            'url': banner,
                            'movieId': None
                        })
                continue
            
            ep = row.get('Số Tập')
            if ep is None or ep == '':
                continue
            
            embed_url = row.get('Embed URL', '').strip()
            video_url = row.get('Link Dailymotion', '').strip()
            
            # Nếu không có Embed URL và cũng không có Link Dailymotion → skip
            if not embed_url and not video_url:
                continue
            
            # Khởi tạo phim nếu chưa có
            if film_name not in movies:
                # Poster có thể nằm ở cột có tiêu đề chứa chữ \"Poster\" (Poster, Poster URL, ...)
                poster_value = ''
                for k, v in row.items():
                    if k and 'Poster' in str(k):
                        poster_value = (v or '').strip()
                        if poster_value:
                            break

                movies[film_name] = {
                    'name': film_name,
                    'vietName': row.get('Tên Phim Việt', '').strip() or film_name,
                    'summary': row.get('Tóm tắt phim', '').strip(),  # Cột H
                    'top': row.get('TOP'),
                    'poster': poster_value,
                    'year': row.get('Năm', ''),
                    'genre': row.get('Thể loại', '').strip(),
                    'country': row.get('Quốc gia', '').strip(),
                    'allowPC': False,
                    'episodes': []
                }
            
            # Cập nhật metadata từ hàng đầu tiên có đủ thông tin
            if row.get('Tên Phim Việt', '').strip():
                movies[film_name]['vietName'] = row.get('Tên Phim Việt', '').strip()
            if row.get('Tóm tắt phim', '').strip() and not movies[film_name]['summary']:
                movies[film_name]['summary'] = row.get('Tóm tắt phim', '').strip()
            # TOP (cột I) - luôn lưu dạng số để tránh lỗi so sánh str/int
            raw_top = row.get('TOP')
            if raw_top is not None and str(raw_top).strip() != "":
                # Chuyển TOP mới về int nếu có thể
                new_top = None
                try:
                    # Trường hợp là số (int/float) hoặc chuỗi số
                    new_top = int(raw_top) if isinstance(raw_top, int) else int(str(raw_top).strip())
                except Exception:
                    # Nếu parse không được thì bỏ qua TOP này
                    new_top = None

                if new_top is not None:
                    current_top = movies[film_name]['top']
                    # Convert current_top sang int nếu có
                    if current_top is None or str(current_top).strip() == "":
                        movies[film_name]['top'] = new_top
                    else:
                        try:
                            current_top_int = int(current_top) if not isinstance(current_top, int) else current_top
                        except Exception:
                            # Nếu current_top đang bị kiểu linh tinh (str không convert được)
                            current_top_int = new_top
                        # Lưu TOP nhỏ nhất (ưu tiên TOP 1, 2, 3...)
                        if current_top_int is None or new_top < current_top_int:
                            movies[film_name]['top'] = new_top
            # Poster (cột J) - chấp nhận mọi header chứa chữ \"Poster\"
            poster_raw = ''
            for k, v in row.items():
                if k and 'Poster' in str(k):
                    poster_raw = (v or '').strip()
                    if poster_raw:
                        break
            if poster_raw and not movies[film_name]['poster']:
                movies[film_name]['poster'] = poster_raw
            if row.get('Năm', ''):
                movies[film_name]['year'] = row.get('Năm', '')
            if row.get('Thể loại', '').strip():
                movies[film_name]['genre'] = row.get('Thể loại', '').strip()
            if row.get('Quốc gia', '').strip():
                movies[film_name]['country'] = row.get('Quốc gia', '').strip()
            
            # Xem PC (cột N)
            allow_pc = row.get('Xem PC', '')
            if allow_pc == True or allow_pc == 1 or str(allow_pc).upper() == 'TRUE' or str(allow_pc) == '1':
                movies[film_name]['allowPC'] = True
            
            # Banner (cột O) - gắn với phim cụ thể
            banner = row.get('Banner', '').strip()
            if banner and banner.startswith('http'):
                # Tìm banner đã tồn tại (cùng URL)
                existing_banner = None
                for i, b in enumerate(banners):
                    if isinstance(b, dict) and b.get('url') == banner:
                        existing_banner = i
                        break
                    elif isinstance(b, str) and b == banner:
                        existing_banner = i
                        break
                
                if existing_banner is not None:
                    # Banner đã tồn tại → update movieId nếu chưa có
                    if isinstance(banners[existing_banner], dict):
                        if not banners[existing_banner].get('movieId') and film_name:
                            banners[existing_banner]['movieId'] = film_name
                    elif isinstance(banners[existing_banner], str):
                        # Convert string thành dict và gắn movieId
                        banners[existing_banner] = {
                            'url': banner,
                            'movieId': film_name if film_name else None
                        }
                else:
                    # Banner mới → thêm vào
                    banners.append({
                        'url': banner,
                        'movieId': film_name  # Gắn banner với phim này
                    })
            
            # Thêm tập
            try:
                ep_num = int(ep) if isinstance(ep, (int, float)) else int(str(ep).strip())
            except:
                ep_num = 0
            
            # Cột P: Link Shopee cho từng tập
            shopee_link = row.get('Shopee Link', '').strip()
            # Tập 1 luôn không có Shopee
            if ep_num == 1:
                shopee_link = None
            
            movies[film_name]['episodes'].append({
                'ep': ep_num,
                'embedUrl': embed_url,
                'videoUrl': row.get('Link Dailymotion', '').strip(),
                'uploadDate': row.get('Ngày Upload', '').strip(),
                'shopeeLink': shopee_link if shopee_link else None
            })
        
        # Sort episodes cho mỗi phim
        for film in movies.values():
            film['episodes'].sort(key=lambda x: x['ep'])
            
            # Kế thừa shopeeLink: nếu tập không có link riêng thì dùng link của tập trước
            last_shopee_link = None
            for ep in film['episodes']:
                if ep['ep'] == 1:
                    # Tập 1 luôn không có Shopee
                    ep['shopeeLink'] = None
                    last_shopee_link = None
                else:
                    # Từ tập 2 trở đi
                    if ep['shopeeLink']:
                        # Tập này có link riêng → dùng và lưu lại
                        last_shopee_link = ep['shopeeLink']
                    elif last_shopee_link:
                        # Tập này không có link → kế thừa từ tập trước
                        ep['shopeeLink'] = last_shopee_link
                    # Nếu không có cả link riêng và link kế thừa → để null (sẽ dùng mặc định trong JS)
        
        # Convert to array và sort theo TOP
        movies_list = list(movies.values())
        movies_list.sort(key=lambda x: (x['top'] is None, x['top'] or 999))
        
        # Output JSON
        output = {
            'movies': movies_list,
            'banners': banners,
            'updated': __import__('datetime').datetime.now().isoformat()
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(movies_list)} movies, {len(banners)} banners to {OUTPUT_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    export_sheet_to_json()

