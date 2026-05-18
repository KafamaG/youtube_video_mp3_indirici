import customtkinter as ctk
import threading
import shutil
import subprocess
import os
import sys
import zipfile
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import yt_dlp


def is_playlist_url(url):
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.path.lower().startswith("/playlist"):
        return True
    qs = parse_qs(p.query)
    if "list" in qs and "v" not in qs:
        return True
    return False


def clean_video_url(url):
    """Strip playlist/index/radio params; keep only the v= parameter for watch URLs."""
    try:
        p = urlparse(url)
    except Exception:
        return url
    qs = parse_qs(p.query)
    if "v" in qs:
        new_qs = urlencode({"v": qs["v"][0]})
        return urlunparse((p.scheme, p.netloc, "/watch", "", new_qs, ""))
    if "youtu.be" in p.netloc:
        return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))
    return url

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FFMPEG_DIR = r"C:\ffmpeg"
FFMPEG_EXE = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFMPEG_URL = "https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-essentials_build.zip"


def find_ffmpeg():
    if os.path.isfile(FFMPEG_EXE):
        return FFMPEG_DIR
    path_ffmpeg = shutil.which("ffmpeg")
    if path_ffmpeg:
        return os.path.dirname(path_ffmpeg)
    return None


def add_ffmpeg_to_path():
    current_path = os.environ.get("PATH", "")
    if FFMPEG_DIR not in current_path:
        os.environ["PATH"] = FFMPEG_DIR + os.pathsep + current_path
        try:
            subprocess.run(
                ["setx", "PATH", FFMPEG_DIR + os.pathsep + current_path],
                capture_output=True, check=False
            )
        except Exception:
            pass


class FFmpegInstaller(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self.title("ffmpeg Kurulumu")
        self.geometry("460x200")
        self.resizable(False, False)
        self.grab_set()

        self.label = ctk.CTkLabel(self, text="ffmpeg bulunamadı. İndirmek ister misiniz?", font=("Segoe UI", 14))
        self.label.pack(pady=(24, 8))

        self.progress = ctk.CTkProgressBar(self, height=14, corner_radius=6)
        self.progress.pack(padx=32, fill="x", pady=(8, 4))
        self.progress.set(0)

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color="gray")
        self.status.pack(pady=(0, 8))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(4, 16))

        self.install_btn = ctk.CTkButton(btn_frame, text="Kur", width=120, command=self._start_install)
        self.install_btn.pack(side="left", padx=8)

        self.cancel_btn = ctk.CTkButton(btn_frame, text="İptal", width=120, fg_color="gray", command=self._cancel)
        self.cancel_btn.pack(side="left", padx=8)

    def _cancel(self):
        self.destroy()

    def _start_install(self):
        self.install_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.status.configure(text="İndiriliyor...", text_color="#00aaff")
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        zip_path = os.path.join(os.environ.get("TEMP", "."), "ffmpeg_download.zip")
        try:
            def report(block_num, block_size, total_size):
                if total_size > 0:
                    pct = min(block_num * block_size / total_size, 1.0)
                    self.progress.set(pct * 0.7)
                    mb_done = (block_num * block_size) / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    self.status.configure(text=f"İndiriliyor... {mb_done:.0f}/{mb_total:.0f} MB")

            urllib.request.urlretrieve(FFMPEG_URL, zip_path, reporthook=report)

            self.status.configure(text="Çıkartılıyor...", text_color="orange")
            self.progress.set(0.75)

            os.makedirs(FFMPEG_DIR, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    filename = os.path.basename(member)
                    if filename.lower() in ("ffmpeg.exe", "ffprobe.exe", "ffplay.exe"):
                        with zf.open(member) as src, open(os.path.join(FFMPEG_DIR, filename), "wb") as dst:
                            dst.write(src.read())

            self.progress.set(0.9)
            self.status.configure(text="PATH'e ekleniyor...")
            add_ffmpeg_to_path()

            os.remove(zip_path)

            self.progress.set(1.0)
            self.status.configure(text="ffmpeg başarıyla kuruldu!", text_color="#00cc66")
            self.after(1200, self._done)

        except Exception as e:
            self.status.configure(text=f"Hata: {str(e)[:50]}", text_color="#ff4444")
            self.install_btn.configure(state="normal")
            self.cancel_btn.configure(state="normal")

    def _done(self):
        self.on_complete()
        self.destroy()


class ManualLinksDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_submit):
        super().__init__(parent)
        self.on_submit = on_submit
        self.title("Manuel Link Ekle")
        self.geometry("560x420")
        self.resizable(False, False)
        self.grab_set()
        self.after(100, self.lift)

        ctk.CTkLabel(self, text="YouTube Linklerini Yapıştır", font=("Segoe UI", 16, "bold")).pack(pady=(18, 2))
        ctk.CTkLabel(
            self, text="Her satıra bir link yapıştırın. Sıralı şekilde indirilecekler.",
            font=("Segoe UI", 11), text_color="gray"
        ).pack(pady=(0, 10))

        self.textbox = ctk.CTkTextbox(self, height=240, font=("Consolas", 12), corner_radius=8)
        self.textbox.pack(padx=20, fill="both", expand=True)
        self.textbox.focus_set()

        self.info_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color="gray")
        self.info_label.pack(pady=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(8, 16))

        self.add_btn = ctk.CTkButton(btn_row, text="Listeye Ekle", width=140, height=36, command=self._submit)
        self.add_btn.pack(side="left", padx=6)

        self.cancel_btn = ctk.CTkButton(
            btn_row, text="İptal", width=110, height=36,
            fg_color="gray", hover_color="#555555", command=self.destroy
        )
        self.cancel_btn.pack(side="left", padx=6)

    def _submit(self):
        raw = self.textbox.get("1.0", "end").strip()
        if not raw:
            self.info_label.configure(text="Önce link yapıştırın.", text_color="#ff8844")
            return

        lines = [ln.strip() for ln in raw.splitlines()]
        candidates = [ln for ln in lines if ln and ("youtube.com" in ln or "youtu.be" in ln)]
        if not candidates:
            self.info_label.configure(text="Geçerli YouTube linki bulunamadı.", text_color="#ff4444")
            return

        playlist_count = sum(1 for u in candidates if is_playlist_url(u))
        if playlist_count:
            self.info_label.configure(
                text=f"{playlist_count} playlist link'i atlandı (manuel mod tekil video içindir, playlist için 'Listele' kullanın).",
                text_color="#ff8844"
            )

        clean = []
        seen = set()
        for u in candidates:
            if is_playlist_url(u):
                continue
            cu = clean_video_url(u)
            if cu in seen:
                continue
            seen.add(cu)
            clean.append(cu)

        if not clean:
            self.info_label.configure(text="Yalnız playlist link'i bulundu — tekil video link'i yapıştırın.", text_color="#ff4444")
            return

        self.on_submit(clean)
        self.destroy()


class VideoItem(ctk.CTkFrame):
    def __init__(self, parent, index, title, video_url, duration=None):
        super().__init__(parent, fg_color="#1f1f1f", corner_radius=8)
        self.video_url = video_url
        self.title_text = title
        self.var = ctk.BooleanVar(value=True)
        self.status_var = ctk.StringVar(value="")

        self.check = ctk.CTkCheckBox(self, text="", variable=self.var, width=24)
        self.check.pack(side="left", padx=(10, 4), pady=8)

        idx_lbl = ctk.CTkLabel(self, text=f"{index:>2}.", font=("Segoe UI", 12, "bold"), text_color="gray", width=28)
        idx_lbl.pack(side="left", padx=(0, 6))

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=4)

        display = title if len(title) <= 70 else title[:67] + "..."
        self.title_lbl = ctk.CTkLabel(info_frame, text=display, font=("Segoe UI", 12), anchor="w", justify="left")
        self.title_lbl.pack(anchor="w", fill="x")

        meta_parts = []
        if duration:
            meta_parts.append(self._format_duration(duration))
        meta_text = "  •  ".join(meta_parts) if meta_parts else ""
        self.meta_lbl = ctk.CTkLabel(info_frame, textvariable=self.status_var, font=("Segoe UI", 10), text_color="gray", anchor="w", justify="left")
        self.meta_lbl.pack(anchor="w", fill="x")
        if meta_text:
            self.status_var.set(meta_text)

        self._base_meta = meta_text

    @staticmethod
    def _format_duration(seconds):
        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            return ""
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def is_selected(self):
        return self.var.get()

    def set_status(self, text, color="gray"):
        self.status_var.set(text)
        self.meta_lbl.configure(text_color=color)

    def reset_status(self):
        self.status_var.set(self._base_meta)
        self.meta_lbl.configure(text_color="gray")


class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Video/MP3 İndirici")
        self.geometry("720x820")
        self.minsize(680, 700)

        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.ffmpeg_path = find_ffmpeg()
        self.video_items = []
        self._stop_flag = False

        self._build_ui()
        self._check_dependencies()

    def _check_dependencies(self):
        missing = []
        if self.ffmpeg_path is None:
            missing.append("ffmpeg")
        if missing:
            self.dep_label.configure(
                text=f"Eksik: {', '.join(missing)}",
                text_color="#ff4444"
            )
            self.install_btn.pack(side="left", padx=(8, 0))
            self.download_btn.configure(state="disabled")
        else:
            add_ffmpeg_to_path()
            self.dep_label.configure(text="Tüm bağımlılıklar hazır", text_color="#00cc66")
            self.install_btn.pack_forget()
            self.download_btn.configure(state="normal")

    def _build_ui(self):
        title = ctk.CTkLabel(self, text="YouTube İndirici", font=("Segoe UI", 24, "bold"))
        title.pack(pady=(20, 2))

        subtitle = ctk.CTkLabel(self, text="Tek video veya playlist — MP4 video / MP3 ses", font=("Segoe UI", 13), text_color="gray")
        subtitle.pack(pady=(0, 10))

        dep_frame = ctk.CTkFrame(self, fg_color="transparent")
        dep_frame.pack(padx=28, fill="x")

        self.dep_label = ctk.CTkLabel(dep_frame, text="Kontrol ediliyor...", font=("Segoe UI", 12))
        self.dep_label.pack(side="left")

        self.install_btn = ctk.CTkButton(
            dep_frame, text="ffmpeg Kur", width=110, height=30,
            font=("Segoe UI", 11), fg_color="#cc6600", hover_color="#aa5500",
            command=self._install_ffmpeg
        )

        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(padx=28, fill="x", pady=(10, 0))

        ctk.CTkLabel(url_frame, text="Video / Playlist URL:", font=("Segoe UI", 13)).pack(anchor="w")

        url_row = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_row.pack(fill="x", pady=(4, 0))

        self.url_entry = ctk.CTkEntry(url_row, placeholder_text="https://www.youtube.com/watch?v=... veya playlist?list=...", height=40, font=("Segoe UI", 13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self._start_fetch())

        self.fetch_btn = ctk.CTkButton(
            url_row, text="Listele", width=100, height=40,
            font=("Segoe UI", 13, "bold"),
            command=self._start_fetch
        )
        self.fetch_btn.pack(side="right")

        self.manual_btn = ctk.CTkButton(
            url_row, text="Manuel", width=90, height=40,
            font=("Segoe UI", 12), fg_color="#444444", hover_color="#555555",
            command=self._open_manual_dialog
        )
        self.manual_btn.pack(side="right", padx=(0, 6))

        format_frame = ctk.CTkFrame(self, fg_color="transparent")
        format_frame.pack(padx=28, fill="x", pady=(12, 0))

        left_col = ctk.CTkFrame(format_frame, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(left_col, text="Format:", font=("Segoe UI", 13)).pack(anchor="w")
        self.format_var = ctk.StringVar(value="MP4 Video")
        self.format_menu = ctk.CTkOptionMenu(
            left_col, variable=self.format_var,
            values=["MP4 Video", "MP3 Ses"],
            height=36, font=("Segoe UI", 12),
            command=self._on_format_change
        )
        self.format_menu.pack(fill="x", pady=(4, 0))

        right_col = ctk.CTkFrame(format_frame, fg_color="transparent")
        right_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

        ctk.CTkLabel(right_col, text="Kalite:", font=("Segoe UI", 13)).pack(anchor="w")
        self.quality_var = ctk.StringVar(value="1080p")
        self.quality_menu = ctk.CTkOptionMenu(
            right_col, variable=self.quality_var,
            values=["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p"],
            height=36, font=("Segoe UI", 12)
        )
        self.quality_menu.pack(fill="x", pady=(4, 0))

        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(padx=28, fill="x", pady=(12, 0))

        ctk.CTkLabel(folder_frame, text="Kayıt Yeri:", font=("Segoe UI", 13)).pack(anchor="w")

        folder_row = ctk.CTkFrame(folder_frame, fg_color="transparent")
        folder_row.pack(fill="x", pady=(4, 0))

        self.folder_var = ctk.StringVar(value=self.download_folder)
        self.folder_entry = ctk.CTkEntry(folder_row, textvariable=self.folder_var, height=40, font=("Segoe UI", 12), state="disabled")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(folder_row, text="Gözat", width=80, height=40, command=self._browse_folder)
        browse_btn.pack(side="right")

        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(padx=28, fill="x", pady=(14, 4))

        self.list_title = ctk.CTkLabel(list_header, text="Liste", font=("Segoe UI", 13, "bold"))
        self.list_title.pack(side="left")

        self.list_count = ctk.CTkLabel(list_header, text="", font=("Segoe UI", 11), text_color="gray")
        self.list_count.pack(side="left", padx=(8, 0))

        self.select_all_var = ctk.BooleanVar(value=True)
        self.select_all_check = ctk.CTkCheckBox(
            list_header, text="Tümünü seç",
            variable=self.select_all_var, font=("Segoe UI", 11),
            command=self._toggle_select_all
        )
        self.select_all_check.pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, height=200, fg_color="#181818", corner_radius=8)
        self.list_frame.pack(padx=28, fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="URL girip 'Listele' butonuna basın.\nTek video veya playlist link'i çalışır.",
            font=("Segoe UI", 12), text_color="gray"
        )
        self.empty_label.pack(pady=40)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(padx=28, fill="x", pady=(12, 0))

        self.download_btn = ctk.CTkButton(
            action_row, text="Seçilenleri İndir", height=44, font=("Segoe UI", 15, "bold"),
            corner_radius=10, command=self._start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            action_row, text="Temizle", height=44, width=110,
            font=("Segoe UI", 13), fg_color="gray", hover_color="#555555",
            command=self._clear_list
        )
        self.clear_btn.pack(side="right")

        self.cookie_var = ctk.BooleanVar(value=False)
        self.cookie_check = ctk.CTkCheckBox(
            self, text="Chrome çerezlerini kullan (yaş kısıtlamalı videolar için)",
            variable=self.cookie_var, font=("Segoe UI", 11),
            text_color="gray"
        )
        self.cookie_check.pack(padx=32, pady=(8, 0), anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self, height=14, corner_radius=6)
        self.progress_bar.pack(padx=28, pady=(12, 0), fill="x")
        self.progress_bar.set(0)

        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.pack(padx=28, fill="x", pady=(6, 12))

        self.status_label = ctk.CTkLabel(bottom_row, text="", font=("Segoe UI", 12), text_color="gray")
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(bottom_row, text="", font=("Segoe UI", 13, "bold"))
        self.percent_label.pack(side="right")

    def _on_format_change(self, value):
        if value == "MP3 Ses":
            self.quality_menu.configure(values=["320 kbps", "256 kbps", "192 kbps", "128 kbps"])
            self.quality_var.set("320 kbps")
        else:
            self.quality_menu.configure(values=["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p"])
            self.quality_var.set("1080p")

    def _install_ffmpeg(self):
        FFmpegInstaller(self, on_complete=self._on_ffmpeg_installed)

    def _on_ffmpeg_installed(self):
        self.ffmpeg_path = find_ffmpeg()
        self._check_dependencies()

    def _browse_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_var.set(folder)

    def _toggle_select_all(self):
        state = self.select_all_var.get()
        for item in self.video_items:
            item.var.set(state)

    def _clear_list(self):
        for item in self.video_items:
            item.destroy()
        self.video_items = []
        self.list_count.configure(text="")
        self.list_title.configure(text="Liste")
        if not self.empty_label.winfo_exists():
            self.empty_label = ctk.CTkLabel(
                self.list_frame,
                text="URL girip 'Listele' butonuna basın.\nTek video veya playlist link'i çalışır.",
                font=("Segoe UI", 12), text_color="gray"
            )
        self.empty_label.pack(pady=40)
        self.status_label.configure(text="", text_color="gray")
        self.percent_label.configure(text="")
        self.progress_bar.set(0)

    def _open_manual_dialog(self):
        ManualLinksDialog(self, on_submit=self._add_manual_urls)

    def _add_manual_urls(self, urls):
        if self.empty_label.winfo_exists():
            self.empty_label.destroy()

        existing = {clean_video_url(it.video_url) for it in self.video_items}
        new_urls = [u for u in urls if u not in existing]
        skipped = len(urls) - len(new_urls)

        if not new_urls:
            self.status_label.configure(text="Tüm linkler zaten listede.", text_color="#ff8844")
            return

        start_index = len(self.video_items) + 1
        placeholders = []
        for i, url in enumerate(new_urls):
            item = VideoItem(self.list_frame, start_index + i, url, url, None)
            item.set_status("Bilgi alınıyor...", "#00aaff")
            item.pack(fill="x", padx=6, pady=3)
            self.video_items.append(item)
            placeholders.append(item)

        if not self.list_title.cget("text") or self.list_title.cget("text") == "Liste":
            self.list_title.configure(text="Manuel Liste")
        self.list_count.configure(text=f"({len(self.video_items)} video)")
        msg = f"{len(new_urls)} link eklendi"
        if skipped:
            msg += f" ({skipped} mükerrer atlandı)"
        msg += ", başlıklar çekiliyor..."
        self.status_label.configure(text=msg, text_color="#00aaff")

        threading.Thread(target=self._enrich_manual, args=(placeholders,), daemon=True).start()

    def _enrich_manual(self, items):
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": True}
        if self.cookie_var.get():
            opts["cookiesfrombrowser"] = ("chrome",)

        for item in items:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(item.video_url, download=False)
                title = info.get("title") or item.video_url
                duration = info.get("duration")
                item.title_text = title
                display = title if len(title) <= 70 else title[:67] + "..."
                self.after(0, lambda it=item, d=display: it.title_lbl.configure(text=d))
                meta = VideoItem._format_duration(duration) if duration else ""
                self.after(0, lambda it=item, m=meta: (setattr(it, "_base_meta", m), it.reset_status()))
            except Exception:
                self.after(0, lambda it=item: it.set_status("Bilgi alınamadı (yine de denenecek)", "#ff8844"))

        self.after(0, lambda: self.status_label.configure(text="Hazır — seçim yapıp indirin", text_color="#00cc66"))

    def _start_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Lütfen bir URL girin!", text_color="#ff4444")
            return

        self.fetch_btn.configure(state="disabled", text="...")
        self.status_label.configure(text="Liste alınıyor...", text_color="#00aaff")
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _fetch(self, url):
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }
        if self.cookie_var.get():
            opts["cookiesfrombrowser"] = ("chrome",)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._fetch_failed(msg))
            return

        entries = []
        seen_ids = set()
        if info.get("_type") == "playlist" or "entries" in info:
            playlist_title = info.get("title", "Playlist")
            for e in info.get("entries", []) or []:
                if not e:
                    continue
                vid = e.get("id") or ""
                if vid and vid in seen_ids:
                    continue
                if vid:
                    seen_ids.add(vid)
                title = e.get("title") or "Bilinmeyen"
                video_url = f"https://www.youtube.com/watch?v={vid}" if vid else (e.get("url") or e.get("webpage_url"))
                if not video_url:
                    continue
                video_url = clean_video_url(video_url)
                entries.append((title, video_url, e.get("duration")))
        else:
            title = info.get("title") or "Bilinmeyen"
            vid = info.get("id")
            video_url = f"https://www.youtube.com/watch?v={vid}" if vid else (info.get("webpage_url") or url)
            video_url = clean_video_url(video_url)
            entries.append((title, video_url, info.get("duration")))
            playlist_title = None

        self.after(0, lambda: self._populate_list(entries, playlist_title))

    def _fetch_failed(self, err):
        self.fetch_btn.configure(state="normal", text="Listele")
        self.status_label.configure(text=f"Liste alınamadı: {err[:80]}", text_color="#ff4444")

    def _populate_list(self, entries, playlist_title):
        for item in self.video_items:
            item.destroy()
        self.video_items = []
        if self.empty_label.winfo_exists():
            self.empty_label.destroy()

        if not entries:
            self.empty_label = ctk.CTkLabel(self.list_frame, text="Video bulunamadı.", font=("Segoe UI", 12), text_color="#ff8844")
            self.empty_label.pack(pady=40)
            self.fetch_btn.configure(state="normal", text="Listele")
            self.status_label.configure(text="", text_color="gray")
            return

        for i, (title, video_url, duration) in enumerate(entries, 1):
            item = VideoItem(self.list_frame, i, title, video_url, duration)
            item.pack(fill="x", padx=6, pady=3)
            self.video_items.append(item)

        if playlist_title:
            self.list_title.configure(text=playlist_title[:50])
        else:
            self.list_title.configure(text="Tekli Video")
        self.list_count.configure(text=f"({len(entries)} video)")
        self.select_all_var.set(True)
        self.fetch_btn.configure(state="normal", text="Listele")
        self.status_label.configure(text="Hazır — seçim yapıp indirin", text_color="#00cc66")

    def _start_download(self):
        if not self.video_items:
            self.status_label.configure(text="Önce listele!", text_color="#ff4444")
            return

        selected = [it for it in self.video_items if it.is_selected()]
        if not selected:
            self.status_label.configure(text="Hiçbir video seçilmedi!", text_color="#ff4444")
            return

        self.download_btn.configure(state="disabled", text="İndiriliyor...")
        self.fetch_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.percent_label.configure(text="")
        self._stop_flag = False

        threading.Thread(target=self._download_all, args=(selected,), daemon=True).start()

    def _progress_hook_factory(self, item, index, total):
        def hook(d):
            if d["status"] == "downloading":
                tb = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if tb > 0:
                    pct = downloaded / tb
                    overall = ((index - 1) + pct) / total
                    self.progress_bar.set(overall)
                    self.percent_label.configure(text=f"{index}/{total} — %{pct * 100:.1f}")
                speed = d.get("speed")
                if speed:
                    mb_speed = speed / (1024 * 1024)
                    self.status_label.configure(
                        text=f"[{index}/{total}] {item.title_text[:50]} — {mb_speed:.1f} MB/s",
                        text_color="#00aaff"
                    )
                item.set_status("İndiriliyor...", "#00aaff")
            elif d["status"] == "finished":
                item.set_status("Birleştiriliyor...", "orange")
        return hook

    def _build_opts(self, is_mp3, quality):
        opts = {
            "outtmpl": os.path.join(self.download_folder, "%(title)s.%(ext)s"),
            "ffmpeg_location": self.ffmpeg_path,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "ignoreerrors": False,
        }
        if is_mp3:
            bitrate = quality.replace(" kbps", "")
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }]
        else:
            height = quality.replace("p", "").replace(" (4K)", "")
            opts["format"] = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]"
            )
            opts["merge_output_format"] = "mp4"
        return opts

    def _download_all(self, selected):
        is_mp3 = self.format_var.get() == "MP3 Ses"
        quality = self.quality_var.get()
        total = len(selected)
        success = 0
        failed = 0

        for idx, item in enumerate(selected, 1):
            opts = self._build_opts(is_mp3, quality)
            opts["progress_hooks"] = [self._progress_hook_factory(item, idx, total)]

            try:
                if self.cookie_var.get():
                    opts["cookiesfrombrowser"] = ("chrome",)
                    try:
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([item.video_url])
                    except Exception as cookie_err:
                        if "cookie" in str(cookie_err).lower():
                            opts.pop("cookiesfrombrowser", None)
                            with yt_dlp.YoutubeDL(opts) as ydl:
                                ydl.download([item.video_url])
                        else:
                            raise
                else:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([item.video_url])

                item.set_status("Tamamlandı", "#00cc66")
                success += 1
            except Exception as e:
                item.set_status(f"Hata: {str(e)[:40]}", "#ff4444")
                failed += 1

            self.progress_bar.set(idx / total)

        self.percent_label.configure(text=f"{success}/{total}")
        if failed == 0:
            self.status_label.configure(text=f"{success} video başarıyla indirildi!", text_color="#00cc66")
        else:
            self.status_label.configure(text=f"{success} başarılı, {failed} başarısız.", text_color="#ff8844")

        self.download_btn.configure(state="normal", text="Seçilenleri İndir")
        self.fetch_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
