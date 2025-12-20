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
import re

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
        
        print(f"📊 Tổng số rows trong Sheet: {len(rows)}")
        ep1_count = 0
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
            
            # Parse số tập: có thể là "1", "2", "Tập 1", "Tập 2", "FULL", v.v.
            ep_str = str(ep).strip().upper()
            
            # Kiểm tra nếu là "FULL"
            if ep_str == 'FULL' or ep_str == 'FULL TẬP' or ep_str == 'FULL TAP':
                ep_num = 'FULL'  # Dùng string "FULL" làm identifier
            else:
                # Tìm số trong chuỗi
                ep_match = re.search(r'(\d+)', ep_str)
                if not ep_match:
                    continue  # Không có số và không phải FULL → skip
                try:
                    ep_num = int(ep_match.group(1))
                except:
                    continue  # Parse lỗi → skip
            
            # Lấy embedUrl và videoUrl (có thể là string hoặc None)
            embed_url_raw = row.get('Embed URL')
            video_url_raw = row.get('Link Dailymotion')
            
            # Convert sang string và strip
            embed_url = str(embed_url_raw).strip() if embed_url_raw else ''
            video_url = str(video_url_raw).strip() if video_url_raw else ''
            
            # QUAN TRỌNG: Nếu Link Dailymotion là link Facebook/reel → đặt vào videoUrl
            # Nếu Embed URL là link Facebook/reel → cũng đặt vào videoUrl
            if video_url and ('facebook.com' in video_url.lower() or 'fb.com' in video_url.lower() or '/reel/' in video_url.lower()):
                # Link Dailymotion là Facebook → dùng làm videoUrl, embedUrl để rỗng
                if not embed_url or embed_url == video_url:
                    embed_url = ''  # Không có embed URL cho Facebook link
            elif embed_url and ('facebook.com' in embed_url.lower() or 'fb.com' in embed_url.lower() or '/reel/' in embed_url.lower()):
                # Embed URL là Facebook → chuyển sang videoUrl
                video_url = embed_url
                embed_url = ''  # Không có embed URL cho Facebook link
                if ep_num == 1:
                    print(f"      🔄 Chuyển embedUrl (Facebook) sang videoUrl: {video_url[:60]}...")
            
            # Nếu không có Embed URL và cũng không có Link Dailymotion → skip
            if not embed_url and not video_url:
                print(f"  ⏭️  Bỏ qua {film_name} - Tập {ep_num}: không có embedUrl và videoUrl")
                continue
            
            # Debug: log tập 1 - CHI TIẾT HƠN
            if ep_num == 1:
                ep1_count += 1
                embed_preview = embed_url[:80] + "..." if len(embed_url) > 80 else embed_url
                video_preview = video_url[:80] + "..." if len(video_url) > 80 else video_url
                print(f"  ✅ Tập 1 #{ep1_count}: {film_name}")
                print(f"      embedUrl: {embed_preview if embed_url else '(RỖNG)'}")
                print(f"      videoUrl: {video_preview if video_url else '(RỖNG)'}")
                print(f"      → Sẽ export: {'CÓ' if (embed_url or video_url) else 'KHÔNG'}")
            
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
            # Lấy poster từ BẤT KỲ hàng nào có poster (không chỉ hàng đầu tiên)
            poster_raw = ''
            for k, v in row.items():
                if k and 'Poster' in str(k):
                    poster_raw = (v or '').strip()
                    if poster_raw:
                        break
            # Update poster nếu có (ưu tiên poster mới nếu chưa có, hoặc nếu poster hiện tại rỗng)
            if poster_raw:
                if not movies[film_name]['poster'] or movies[film_name]['poster'].strip() == '':
                    movies[film_name]['poster'] = poster_raw
                    if ep_num == 1:
                        print(f"      📷 Poster: {poster_raw[:60]}...")
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
            
            # Cột P: Link Shopee cho từng tập
            shopee_link = row.get('Shopee Link', '').strip()
            # Tập 1 luôn không có Shopee
            if ep_num == 1:
                shopee_link = None
            
            # Kiểm tra xem episode này đã tồn tại chưa (tránh duplicate) - DÙNG DICTIONARY ĐỂ TRÁNH DUPLICATE
            # Tạo key unique cho episode: ep_num
            if 'episodes_dict' not in movies[film_name]:
                movies[film_name]['episodes_dict'] = {}  # Dict để check duplicate nhanh hơn
            
            ep_key = ep_num
            current_episode_data = {
                'ep': ep_num,
                'embedUrl': embed_url,
                'videoUrl': video_url,
                'uploadDate': str(row.get('Ngày Upload', '')).strip() if row.get('Ngày Upload') else '',
                'shopeeLink': shopee_link if shopee_link else None
            }
            
            if ep_key in movies[film_name]['episodes_dict']:
                # Episode đã tồn tại → so sánh và giữ lại episode tốt hơn
                existing_ep = movies[film_name]['episodes_dict'][ep_key]
                
                # Đặc biệt cho tập 1: ưu tiên episode có videoUrl (link fanpage)
                if ep_num == 1:
                    existing_has_video = bool(existing_ep.get('videoUrl'))
                    current_has_video = bool(video_url)
                    existing_has_embed = bool(existing_ep.get('embedUrl'))
                    current_has_embed = bool(embed_url)
                    
                    # Ưu tiên: videoUrl > embedUrl (vì tập 1 thường dùng link fanpage)
                    if current_has_video and not existing_has_video:
                        # Tập 1 mới có videoUrl → thay thế hoàn toàn
                        print(f"  🔄 Thay thế tập 1: {film_name} (có videoUrl mới: {video_url[:50]}...)")
                        movies[film_name]['episodes_dict'][ep_key] = current_episode_data
                        # Tìm và thay thế trong list
                        for i, ep in enumerate(movies[film_name]['episodes']):
                            if ep['ep'] == ep_num:
                                movies[film_name]['episodes'][i] = current_episode_data
                                break
                    elif existing_has_video and not current_has_video:
                        # Existing có videoUrl, current không có → giữ existing, chỉ merge embedUrl nếu có
                        if current_has_embed and not existing_has_embed:
                            existing_ep['embedUrl'] = embed_url
                            print(f"  ➕ Merge embedUrl vào tập 1: {film_name}")
                    else:
                        # Cả 2 đều có hoặc đều không có videoUrl → merge tất cả field
                        if embed_url and not existing_ep.get('embedUrl'):
                            existing_ep['embedUrl'] = embed_url
                        if video_url and not existing_ep.get('videoUrl'):
                            existing_ep['videoUrl'] = video_url
                        if current_episode_data.get('uploadDate') and not existing_ep.get('uploadDate'):
                            existing_ep['uploadDate'] = current_episode_data['uploadDate']
                else:
                    # Tập 2+: đếm số field có giá trị
                    existing_count = sum([
                        1 if existing_ep.get('embedUrl') else 0,
                        1 if existing_ep.get('videoUrl') else 0,
                        1 if existing_ep.get('uploadDate') else 0
                    ])
                    current_count = sum([
                        1 if current_episode_data.get('embedUrl') else 0,
                        1 if current_episode_data.get('videoUrl') else 0,
                        1 if current_episode_data.get('uploadDate') else 0
                    ])
                    
                    # Ưu tiên episode có nhiều thông tin hơn
                    if current_count > existing_count:
                        # Episode mới tốt hơn → thay thế
                        movies[film_name]['episodes_dict'][ep_key] = current_episode_data
                        # Tìm và thay thế trong list
                        for i, ep in enumerate(movies[film_name]['episodes']):
                            if ep['ep'] == ep_num:
                                movies[film_name]['episodes'][i] = current_episode_data
                                break
                    elif current_count == existing_count:
                        # Bằng nhau → merge: lấy giá trị từ episode nào có
                        if embed_url and not existing_ep.get('embedUrl'):
                            existing_ep['embedUrl'] = embed_url
                        if video_url and not existing_ep.get('videoUrl'):
                            existing_ep['videoUrl'] = video_url
                        if current_episode_data.get('uploadDate') and not existing_ep.get('uploadDate'):
                            existing_ep['uploadDate'] = current_episode_data['uploadDate']
                        if shopee_link and not existing_ep.get('shopeeLink'):
                            existing_ep['shopeeLink'] = shopee_link if shopee_link else None
            else:
                # Episode mới → thêm vào dict và list
                if ep_num == 1:
                    print(f"  ➕ Thêm tập 1 mới: {film_name} - videoUrl={bool(video_url)}, embedUrl={bool(embed_url)}")
                movies[film_name]['episodes_dict'][ep_key] = current_episode_data
                movies[film_name]['episodes'].append(current_episode_data)
        
        # Sort episodes cho mỗi phim (đã loại bỏ duplicate bằng dict ở trên)
        for film_name, film in movies.items():
            # Xóa episodes_dict (không cần nữa)
            if 'episodes_dict' in film:
                del film['episodes_dict']
            
            # Sort theo số tập
            film['episodes'].sort(key=lambda x: x['ep'])
            
            # Debug: kiểm tra tập 1 sau khi sort
            ep1_list = [ep for ep in film['episodes'] if ep.get('ep') == 1]
            if ep1_list:
                ep1 = ep1_list[0]
                print(f"  ✅ Sau khi sort - {film_name}: Tập 1 có videoUrl={bool(ep1.get('videoUrl'))}, embedUrl={bool(ep1.get('embedUrl'))}")
            else:
                print(f"  ⚠️  Sau khi sort - {film_name}: KHÔNG CÓ TẬP 1!")
            
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
        
        # Debug: đếm số tập 1 trong JSON output
        total_ep1 = 0
        for m in movies_list:
            ep1_count = sum(1 for ep in m.get('episodes', []) if ep.get('ep') == 1)
            if ep1_count > 0:
                print(f"  📺 {m['name']}: có {ep1_count} tập 1")
                total_ep1 += ep1_count
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(movies_list)} movies, {len(banners)} banners to {OUTPUT_FILE}")
        print(f"📺 Tổng số tập 1 trong JSON: {total_ep1}")
        if total_ep1 == 0:
            print("⚠️  CẢNH BÁO: Không có tập 1 nào được export!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    export_sheet_to_json()

