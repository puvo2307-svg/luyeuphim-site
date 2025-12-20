import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from datetime import datetime

from dailymotion_api import DailymotionAPI
from google_sheet import GoogleSheetManager


class DailymotionHelperGUI:
    """
    GUI đơn giản để:
    - Nhập API Key/Secret của Dailymotion
    - (Tùy chọn) Kết nối Google Sheet
    - Lấy embed code từ:
        + 1 video URL/ID (upload thủ công)
        + Playlist URL (nhiều video)
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Dailymotion Helper - Lấy Embed Code")
        self.root.geometry("900x700")

        # Biến cấu hình
        self.api_key = tk.StringVar()
        self.api_secret = tk.StringVar()
        self.film_title = tk.StringVar()

        self.google_credentials_path = tk.StringVar()
        self.sheet_id = tk.StringVar()
        self.sheet_name = tk.StringVar(value="Sheet1")
        # Quét kênh
        self.channel_ids_text = None  # sẽ gán ở _build_ui
        self.scan_interval_minutes = tk.IntVar(value=60)
        self.scan_thread: threading.Thread | None = None
        self.scan_stop_event = threading.Event()

        # Quản lý API / Google Sheet
        self.dm_api: DailymotionAPI | None = None
        self.sheet_manager: GoogleSheetManager | None = None

        self.config_file = "config.json"

        self._build_ui()
        self._load_config()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # 1. API frame
        api_frame = ttk.LabelFrame(main, text="Dailymotion API", padding=10)
        api_frame.pack(fill=tk.X, pady=5)

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_key, width=50).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(api_frame, text="API Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_secret, show="*", width=50).grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(api_frame, text="💾 Lưu cấu hình", command=self._save_config).grid(
            row=0, column=2, padx=5, pady=2, rowspan=2, sticky=tk.NS
        )

        # 2. Google Sheet
        sheet_frame = ttk.LabelFrame(main, text="Google Sheet (tuỳ chọn)", padding=10)
        sheet_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sheet_frame, text="Credentials JSON:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(sheet_frame, textvariable=self.google_credentials_path, width=50).grid(
            row=0, column=1, padx=5, pady=2
        )
        ttk.Button(sheet_frame, text="Browse", command=self._browse_credentials).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(sheet_frame, text="Sheet ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(sheet_frame, textvariable=self.sheet_id, width=50).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(sheet_frame, text="Sheet Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(sheet_frame, textvariable=self.sheet_name, width=50).grid(row=2, column=1, padx=5, pady=2)

        ttk.Button(sheet_frame, text="🔗 Kết nối Google Sheet", command=self._connect_sheet).grid(
            row=1, column=2, padx=5, pady=2, rowspan=2, sticky=tk.NS
        )

        # 3. Channel scan settings
        scan_frame = ttk.LabelFrame(main, text="Quét kênh Dailymotion", padding=10)
        scan_frame.pack(fill=tk.X, pady=5)

        ttk.Label(scan_frame, text="Danh sách ID kênh (mỗi dòng 1 ID hoặc username):").grid(
            row=0, column=0, columnspan=2, sticky=tk.W
        )
        self.channel_ids_text = scrolledtext.ScrolledText(scan_frame, width=50, height=4)
        self.channel_ids_text.grid(row=1, column=0, columnspan=2, pady=5, sticky=tk.W)

        ttk.Label(scan_frame, text="Thời gian lặp quét (phút):").grid(row=0, column=2, sticky=tk.W, padx=10)
        ttk.Entry(scan_frame, textvariable=self.scan_interval_minutes, width=8).grid(
            row=0, column=3, sticky=tk.W, padx=5
        )

        ttk.Button(scan_frame, text="📺 Quét kênh 1 lần", command=self._scan_channels_once).grid(
            row=1, column=2, padx=5, pady=5
        )
        ttk.Button(scan_frame, text="🔁 Bắt đầu quét lặp", command=self._toggle_auto_scan).grid(
            row=1, column=3, padx=5, pady=5
        )

        # 4. Log
        log_frame = ttk.LabelFrame(main, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=100, height=20, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ---------------------------------------------------------------------
    # Config
    # ---------------------------------------------------------------------

    def _save_config(self):
        cfg = {
            "api_key": self.api_key.get(),
            "api_secret": self.api_secret.get(),
            "film_title": self.film_title.get(),
            "google_credentials_path": self.google_credentials_path.get(),
            "sheet_id": self.sheet_id.get(),
            "sheet_name": self.sheet_name.get(),
            "channel_ids": self._get_channel_ids(),
            "scan_interval_minutes": self.scan_interval_minutes.get(),
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self._log("✅ Đã lưu cấu hình.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")
            self._log(f"❌ Lỗi khi lưu cấu hình: {e}")

    def _load_config(self):
        if not os.path.exists(self.config_file):
            return
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.api_key.set(cfg.get("api_key", ""))
            self.api_secret.set(cfg.get("api_secret", ""))
            self.film_title.set(cfg.get("film_title", ""))
            self.google_credentials_path.set(cfg.get("google_credentials_path", ""))
            self.sheet_id.set(cfg.get("sheet_id", ""))
            self.sheet_name.set(cfg.get("sheet_name", "Dailymotion Videos"))
            # Channel scan config
            channel_ids = cfg.get("channel_ids", [])
            if isinstance(channel_ids, list) and self.channel_ids_text:
                self.channel_ids_text.delete("1.0", tk.END)
                for cid in channel_ids:
                    self.channel_ids_text.insert(tk.END, cid + "\n")
            self.scan_interval_minutes.set(cfg.get("scan_interval_minutes", 60))
            self._log("Đã tải cấu hình.")
        except Exception as e:
            self._log(f"❌ Không thể tải cấu hình: {e}")

    # ---------------------------------------------------------------------
    # Google Sheet
    # ---------------------------------------------------------------------

    def _browse_credentials(self):
        path = filedialog.askopenfilename(
            title="Chọn Google Credentials JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.google_credentials_path.set(path)

    def _connect_sheet(self):
        if not self.google_credentials_path.get() or not os.path.exists(self.google_credentials_path.get()):
            messagebox.showerror("Lỗi", "Vui lòng chọn file credentials JSON hợp lệ.")
            return
        if not self.sheet_id.get():
            messagebox.showerror("Lỗi", "Vui lòng nhập Sheet ID.")
            return
        try:
            self._log("Đang kết nối Google Sheet...")
            self.sheet_manager = GoogleSheetManager(
                credentials_path=self.google_credentials_path.get(),
                token_path="tokens/token.json",
            )
            self.sheet_manager.authenticate()
            # Mở sheet theo ID + name
            self.sheet_manager.open_by_id(self.sheet_id.get(), self.sheet_name.get())
            self._log(f"✅ Đã kết nối Google Sheet: ID={self.sheet_id.get()}, Name={self.sheet_name.get()}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối Google Sheet: {e}")
            self._log(f"❌ Lỗi khi kết nối Google Sheet: {e}")
            self.sheet_manager = None

    # ---------------------------------------------------------------------
    # Dailymotion API helper
    # ---------------------------------------------------------------------

    def _ensure_dm_api(self) -> bool:
        if self.dm_api:
            return True
        if not self.api_key.get() or not self.api_secret.get():
            messagebox.showerror("Lỗi", "Vui lòng nhập API Key và API Secret.")
            return False
        try:
            self.dm_api = DailymotionAPI(
                self.api_key.get(),
                self.api_secret.get(),
                log_callback=self._log,
            )
            # Test token
            token = self.dm_api.get_access_token()
            self._log("✅ Lấy token Dailymotion thành công.")
            self._log(f"[DEBUG] Token preview: {token[:10]}...")
            return True
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi tạo Dailymotion API: {e}")
            self._log(f"❌ Lỗi khi khởi tạo Dailymotion API: {e}")
            self.dm_api = None
            return False
    
    def _get_channel_ids(self):
        """Lấy danh sách ID kênh từ text box (mỗi dòng 1 ID)."""
        if not self.channel_ids_text:
            return []
        raw = self.channel_ids_text.get("1.0", tk.END)
        ids = [line.strip() for line in raw.splitlines() if line.strip()]
        return ids

    # ---------------------------------------------------------------------
    # Dialogs
    # ---------------------------------------------------------------------

    def _open_video_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Lấy Embed Code từ Video URL/ID")
        dialog.geometry("650x500")

        ttk.Label(dialog, text="Video URL hoặc ID:").pack(pady=(10, 5))
        url_entry = ttk.Entry(dialog, width=70)
        url_entry.pack(padx=10, pady=5)
        url_entry.insert(0, "https://www.dailymotion.com/video/x...")

        ttk.Label(dialog, text="Số tập (tùy chọn):").pack(pady=(10, 5))
        episode_entry = ttk.Entry(dialog, width=20)
        episode_entry.pack(padx=10, pady=5)

        result_text = scrolledtext.ScrolledText(dialog, width=80, height=18, state=tk.DISABLED)
        result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        def handle():
            video_url = url_entry.get().strip()
            if not video_url or video_url.startswith("https://www.dailymotion.com/video/x..."):
                messagebox.showerror("Lỗi", "Vui lòng nhập Video URL hoặc ID.")
                return
            film_title = self.film_title.get().strip() or "Không tên"
            episode = episode_entry.get().strip() or "1"

            if not self._ensure_dm_api():
                return

            try:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, "Đang lấy thông tin video...\n")
                dialog.update()

                info = self.dm_api.get_video_info(video_url)
                vid = info.get("id")
                embed = info.get("embed_url")
                url = info.get("url")
                thumb = info.get("thumbnail_url")
                title = info.get("title", "")
                created = info.get("created_time", "")

                # Format upload date
                upload_date = ""
                if created:
                    try:
                        ts = int(created)
                        upload_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    except Exception:
                        upload_date = str(created)

                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"✅ Đã lấy thông tin video.\n\n")
                result_text.insert(tk.END, f"Video ID: {vid}\n")
                result_text.insert(tk.END, f"Tiêu đề: {title}\n")
                result_text.insert(tk.END, f"Embed URL: {embed}\n")
                result_text.insert(tk.END, f"Video URL: {url}\n")
                result_text.insert(tk.END, f"Thumbnail: {thumb}\n")
                result_text.insert(tk.END, f"Ngày upload: {upload_date}\n\n")

                # Lưu Google Sheet
                if self.sheet_manager:
                    new_title = f"Tập {episode} - {film_title}"
                    record = {
                        "video_id": vid,
                        "title": new_title,
                        "embed_url": embed,
                        "url": url,
                        "thumbnail_url": thumb,
                        "private": info.get("private", True),
                    }
                    try:
                        self.sheet_manager.add_video_record(
                            film_name=film_title,
                            episode_number=str(episode),
                            video_data=record,
                            description=title,
                        )
                        result_text.insert(tk.END, "✅ Đã lưu vào Google Sheet.\n")
                        self._log(f"Đã lưu video {vid} (Tập {episode}) vào Google Sheet.")
                    except Exception as e:
                        result_text.insert(tk.END, f"⚠️ Lỗi khi lưu Sheet: {e}\n")
                        self._log(f"Lỗi khi lưu Sheet: {e}")
                else:
                    result_text.insert(tk.END, "ℹ️ Chưa kết nối Google Sheet.\n")

                result_text.config(state=tk.DISABLED)
            except Exception as e:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"❌ Lỗi: {e}\n")
                result_text.config(state=tk.DISABLED)
                self._log(f"Lỗi khi lấy embed từ video: {e}")

        ttk.Button(dialog, text="Lấy Embed Code", command=handle).pack(pady=5)

    def _open_playlist_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Lấy Embed Code từ Playlist")
        dialog.geometry("750x600")

        ttk.Label(dialog, text="Playlist URL:").pack(pady=(10, 5))
        pl_entry = ttk.Entry(dialog, width=80)
        pl_entry.pack(padx=10, pady=5)
        pl_entry.insert(0, "https://www.dailymotion.com/playlist/x...")

        ttk.Label(dialog, text="Tên phim gốc (tiếng Trung):").pack(pady=(10, 5))
        title_entry = ttk.Entry(dialog, width=80)
        title_entry.pack(padx=10, pady=5)
        title_entry.insert(0, self.film_title.get())

        result_text = scrolledtext.ScrolledText(dialog, width=90, height=22, state=tk.DISABLED)
        result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        def handle():
            pl_url = pl_entry.get().strip()
            film_title = title_entry.get().strip() or self.film_title.get().strip() or "Không tên"

            if not pl_url or pl_url.startswith("https://www.dailymotion.com/playlist/x..."):
                messagebox.showerror("Lỗi", "Vui lòng nhập Playlist URL.")
                return
            if not self._ensure_dm_api():
                return

            try:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, "Đang lấy video trong playlist...\n")
                dialog.update()

                videos = self.dm_api.get_playlist_videos(pl_url)
                if not videos:
                    result_text.insert(tk.END, "❌ Không tìm thấy video nào trong playlist.\n")
                    result_text.config(state=tk.DISABLED)
                    return

                result_text.insert(tk.END, f"✅ Tìm thấy {len(videos)} video.\n\n")
                saved = 0

                import re as _re

                patterns = [
                    r"part\s*(\d+)",
                    r"part(\d+)",
                    r"tập\s*(\d+)",
                    r"episode\s*(\d+)",
                    r"ep\s*(\d+)",
                    r"第\s*(\d+)\s*集",
                    r"(\d+)\s*集",
                ]

                for idx, v in enumerate(videos, 1):
                    vid = v.get("id")
                    original_title = v.get("title", "")
                    embed = v.get("embed_url")
                    url = v.get("url")
                    thumb = v.get("thumbnail_url")
                    created = v.get("created_time", "")

                    # Extract episode
                    episode = None
                    for p in patterns:
                        m = _re.search(p, original_title, _re.IGNORECASE)
                        if m:
                            try:
                                episode = int(m.group(1))
                            except Exception:
                                episode = None
                            break
                    if episode is None:
                        episode = idx

                    new_title = f"Tập {episode} - {film_title}"

                    # Format date
                    upload_date = ""
                    if created:
                        try:
                            ts = int(created)
                            upload_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        except Exception:
                            upload_date = str(created)

                    result_text.insert(
                        tk.END,
                        f"[{idx}/{len(videos)}] {vid}\n"
                        f"  Gốc : {original_title}\n"
                        f"  Mới : {new_title}\n"
                        f"  Tập : {episode}\n"
                        f"  Embed: {embed}\n\n",
                    )
                    dialog.update()

                    if self.sheet_manager:
                        record = {
                            "video_id": vid,
                            "title": new_title,
                            "embed_url": embed,
                            "url": url,
                            "thumbnail_url": thumb,
                            "private": v.get("private", True),
                        }
                        try:
                            self.sheet_manager.add_video_record(
                                film_name=film_title,
                                episode_number=str(episode),
                                video_data=record,
                                description=f"Tập {episode}\n{original_title}",
                            )
                            saved += 1
                            self._log(f"Đã lưu video {vid} (Tập {episode}) vào Sheet.")
                        except Exception as e:
                            result_text.insert(tk.END, f"  ⚠️ Lỗi khi lưu Sheet: {e}\n\n")
                            self._log(f"Lỗi khi lưu video {vid}: {e}")

                result_text.insert(tk.END, "\nHoàn thành.\n")
                if self.sheet_manager:
                    result_text.insert(tk.END, f"✅ Đã lưu {saved}/{len(videos)} video vào Google Sheet.\n")

                result_text.config(state=tk.DISABLED)
            except Exception as e:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"❌ Lỗi: {e}\n")
                result_text.config(state=tk.DISABLED)
                self._log(f"Lỗi khi lấy embed từ playlist: {e}")

        ttk.Button(dialog, text="Lấy Embed từ Playlist", command=handle).pack(pady=5)

    # ---------------------------------------------------------------------
    # Quét kênh Dailymotion
    # ---------------------------------------------------------------------

    def _scan_channels_once(self):
        """Quét tất cả kênh đã cấu hình và lưu embed vào Google Sheet."""
        if not self._ensure_dm_api():
            return
        if not self.sheet_manager:
            messagebox.showerror("Lỗi", "Vui lòng kết nối Google Sheet trước khi quét kênh.")
            return

        channel_ids = self._get_channel_ids()
        if not channel_ids:
            messagebox.showerror("Lỗi", "Vui lòng nhập ít nhất 1 ID kênh.")
            return

        from datetime import datetime as _dt
        import re as _re

        # Lấy toàn bộ record hiện có để tránh trùng (dựa trên Link Dailymotion)
        # Lưu ý: tên header trên sheet có thể khác nhau, hoặc người dùng đã chỉnh sửa,
        # nên ta sẽ:
        # 1) Thử lấy theo key chuẩn 'Link Dailymotion' (và vài biến thể)
        # 2) Nếu không có, quét tất cả value trong hàng, lấy cell nào là URL (bắt đầu bằng http)
        existing_urls = set()
        try:
            records = self.sheet_manager.get_all_records()
            for r in records:
                url = (
                    r.get("Link Dailymotion")
                    or r.get("Link Dailymotio")  # phòng khi thiếu chữ 'n'
                    or r.get("Link")             # fallback rất lỏng
                )
                if not url:
                    # Fallback: kiếm bất kỳ value nào là URL
                    for v in r.values():
                        if isinstance(v, str) and v.strip().startswith("http"):
                            url = v
                            break
                if url:
                    existing_urls.add(str(url).strip())
        except Exception as e:
            self._log(f"⚠️ Không thể lấy records hiện có từ Sheet: {e}")

        self._log(f"🚀 Bắt đầu quét {len(channel_ids)} kênh...")

        for cid in channel_ids:
            cid = cid.strip()
            if not cid:
                continue
            try:
                self._log(f"🔍 Đang quét kênh: {cid}")
                videos = self.dm_api.get_user_videos(cid, max_videos=1000)
                self._log(f"   → Tìm thấy {len(videos)} video (PUBLIC)")

                # Gom tất cả entry mới rồi sort theo (Tên phim, Tập) trước khi ghi sheet
                entries = []  # mỗi entry: (film_name, episode, video_url, embed_url, upload_date, vid)

                for v in videos:
                    vid = v.get("id")
                    title = v.get("title", "")

                    # Chỉ lấy video có pattern: final-<tên phim>-partX hoặc final-<tên phim>-partX-daily.mp4
                    # Pattern match cả 2 format: final-*-part* và final-*-part*-daily.mp4
                    m = _re.search(r"^final-(.+?)-part(\d+)(?:-daily)?(?:\.mp4)?$", title, _re.IGNORECASE)
                    if not m:
                        # Log video không match pattern để debug
                        self._log(f"  ⏭️  Bỏ qua video {vid}: không match pattern (title: {title[:50]}...)")
                        continue

                    film_name = m.group(1).strip()
                    try:
                        episode = int(m.group(2))
                    except Exception:
                        episode = 0

                    # Lấy thông tin chi tiết để có embed URL
                    try:
                        info = self.dm_api.get_video_info(vid)
                    except Exception as e:
                        self._log(f"  ❌ Lỗi lấy info video {vid}: {e}")
                        continue

                    video_url = info.get("url") or v.get("url", "")
                    embed_url = info.get("embed_url", "")
                    created_time = info.get("created_time") or v.get("created_time", "")

                    # Bỏ qua nếu video đã tồn tại trong sheet
                    if video_url and video_url.strip() in existing_urls:
                        self._log(f"  ⏭️  Bỏ qua video {vid}: đã có trong Sheet")
                        continue

                    # Format ngày
                    upload_date = ""
                    if created_time:
                        try:
                            dt = _dt.fromtimestamp(int(created_time))
                            upload_date = dt.strftime("%Y-%m-%d")
                        except Exception:
                            upload_date = str(created_time)

                    entries.append(
                        (film_name, episode, video_url, embed_url, upload_date, vid)
                    )

                # Sort theo tên phim + số tập
                entries.sort(key=lambda x: (x[0], x[1]))

                # Ghi vào sheet theo thứ tự đã sort
                for film_name, episode, video_url, embed_url, upload_date, vid in entries:
                    self._log(f"  ➕ {film_name} - Tập {episode} ({vid})")
                    try:
                        self.sheet_manager.add_channel_video_record(
                            film_name=film_name,
                            episode_number=episode,
                            video_url=video_url,
                            embed_url=embed_url,
                            channel_id=cid,
                            upload_date=upload_date or _dt.now().strftime("%Y-%m-%d"),
                        )
                        if video_url:
                            existing_urls.add(video_url.strip())
                    except Exception as e:
                        self._log(f"  ⚠️ Lỗi khi lưu video {vid} vào sheet: {e}")
                        continue

            except Exception as e:
                self._log(f"❌ Lỗi khi quét kênh {cid}: {e}")

        self._log("✅ Quét kênh hoàn tất.")

    def _scan_worker(self):
        """Thread quét kênh định kỳ."""
        interval = max(1, int(self.scan_interval_minutes.get()))
        self._log(f"🕒 Bắt đầu quét định kỳ mỗi {interval} phút")
        while not self.scan_stop_event.is_set():
            self._scan_channels_once()
            # Chờ interval phút hoặc tới khi stop
            for _ in range(interval * 60):
                if self.scan_stop_event.is_set():
                    break
                self.scan_stop_event.wait(1)
        self._log("⏹ Đã dừng quét định kỳ")

    def _toggle_auto_scan(self):
        """Bật / tắt quét kênh định kỳ."""
        if self.scan_thread and self.scan_thread.is_alive():
            # stop
            self.scan_stop_event.set()
            self._log("Đang dừng quét định kỳ...")
            return

        if not self._ensure_dm_api():
            return
        if not self.sheet_manager:
            messagebox.showerror("Lỗi", "Vui lòng kết nối Google Sheet trước khi quét kênh.")
            return
        if not self._get_channel_ids():
            messagebox.showerror("Lỗi", "Vui lòng nhập ít nhất 1 ID kênh.")
            return

        self.scan_stop_event.clear()
        self.scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        self.scan_thread.start()

    # ---------------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------------

    def _log(self, msg: str):
        self.log_text.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = DailymotionHelperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


