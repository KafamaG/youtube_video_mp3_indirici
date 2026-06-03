import customtkinter as ctk
import threading
import shutil
import subprocess
import os
import sys
import re
import time
import zipfile
import urllib.request
import concurrent.futures
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import yt_dlp


YOUTUBE_URL_RE = re.compile(
    r'https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/[^\s,;<>"\']+',
    re.IGNORECASE,
)


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

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=COLOR_MUTED)
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
        self.status.configure(text="İndiriliyor...", text_color=COLOR_INFO)
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

            self.status.configure(text="Çıkartılıyor...", text_color=COLOR_WARNING)
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
            self.status.configure(text="ffmpeg başarıyla kuruldu!", text_color=COLOR_SUCCESS)
            self.after(1200, self._done)

        except Exception as e:
            self.status.configure(text=f"Hata: {str(e)[:50]}", text_color=COLOR_DANGER)
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
            font=("Segoe UI", 11), text_color=COLOR_MUTED
        ).pack(pady=(0, 10))

        self.textbox = ctk.CTkTextbox(self, height=240, font=("Consolas", 12), corner_radius=8)
        self.textbox.pack(padx=20, fill="both", expand=True)
        self.textbox.focus_set()

        self.info_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=COLOR_MUTED)
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
            self.info_label.configure(text="Önce link yapıştırın.", text_color=COLOR_WARNING)
            return

        candidates = YOUTUBE_URL_RE.findall(raw)
        if not candidates:
            self.info_label.configure(text="Geçerli YouTube linki bulunamadı.", text_color=COLOR_DANGER)
            return

        playlist_count = sum(1 for u in candidates if is_playlist_url(u))
        if playlist_count:
            self.info_label.configure(
                text=f"{playlist_count} playlist link'i atlandı (manuel mod tekil video içindir, playlist için 'Listele' kullanın).",
                text_color=COLOR_WARNING
            )

        clean = []
        seen = set()
        dup_in_paste = 0
        for u in candidates:
            if is_playlist_url(u):
                continue
            cu = clean_video_url(u)
            if cu in seen:
                dup_in_paste += 1
                continue
            seen.add(cu)
            clean.append(cu)

        if not clean:
            self.info_label.configure(text="Yalnız playlist link'i bulundu — tekil video link'i yapıştırın.", text_color=COLOR_DANGER)
            return

        self.on_submit(clean, dup_in_paste, playlist_count)
        self.destroy()


# All palette entries are (light_mode, dark_mode) tuples — customtkinter
# auto-selects the right one based on the current appearance mode.
COLOR_BG = ("#f4f4f6", "#0d0d0f")
COLOR_CARD = ("#ffffff", "#17171b")
COLOR_CARD_ALT = ("#eeeef1", "#1e1e23")
COLOR_BORDER = ("#dcdce0", "#2a2a30")
COLOR_TEXT = ("#1a1a1c", "#e6e6ea")
COLOR_MUTED = ("#6b6b73", "#8a8a93")
COLOR_ACCENT = ("#2563eb", "#3b82f6")
COLOR_ACCENT_HOVER = ("#1d4ed8", "#2563eb")
COLOR_SUCCESS = ("#16a34a", "#22c55e")
COLOR_WARNING = ("#d97706", "#f59e0b")
COLOR_DANGER = ("#dc2626", "#ef4444")
COLOR_INFO = ("#0284c7", "#38bdf8")
COLOR_HOVER_SUBTLE = ("#e3e3e7", "#2a2a30")


class VideoItem(ctk.CTkFrame):
    def __init__(self, parent, index, title, video_url, duration=None):
        super().__init__(parent, fg_color=COLOR_CARD_ALT, corner_radius=10,
                         border_width=1, border_color=COLOR_BORDER)
        self.video_url = video_url
        self.title_text = title
        self.var = ctk.BooleanVar(value=True)
        self.status_var = ctk.StringVar(value="")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        self.check = ctk.CTkCheckBox(top, text="", variable=self.var, width=22,
                                     checkbox_width=20, checkbox_height=20,
                                     corner_radius=4)
        self.check.pack(side="left", padx=(0, 8))

        idx_lbl = ctk.CTkLabel(top, text=f"{index:02d}", font=("Segoe UI", 11, "bold"),
                               text_color=COLOR_MUTED, width=26)
        idx_lbl.pack(side="left", padx=(0, 8))

        info_frame = ctk.CTkFrame(top, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        display = title if len(title) <= 70 else title[:67] + "..."
        self.title_lbl = ctk.CTkLabel(info_frame, text=display, font=("Segoe UI", 12, "bold"),
                                      anchor="w", justify="left", text_color=COLOR_TEXT)
        self.title_lbl.pack(anchor="w", fill="x")

        meta_parts = []
        if duration:
            meta_parts.append(self._format_duration(duration))
        meta_text = "  •  ".join(meta_parts) if meta_parts else ""
        self.meta_lbl = ctk.CTkLabel(info_frame, textvariable=self.status_var,
                                     font=("Segoe UI", 10), text_color=COLOR_MUTED,
                                     anchor="w", justify="left")
        self.meta_lbl.pack(anchor="w", fill="x")
        if meta_text:
            self.status_var.set(meta_text)

        self.item_progress = ctk.CTkProgressBar(self, height=4, corner_radius=2,
                                                progress_color=COLOR_ACCENT,
                                                fg_color="#0f0f12")
        self.item_progress.pack(fill="x", padx=12, pady=(2, 10))
        self.item_progress.set(0)

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

    def set_status(self, text, color=None):
        self.status_var.set(text)
        self.meta_lbl.configure(text_color=color or COLOR_MUTED)

    def set_progress(self, value, color=None):
        try:
            self.item_progress.set(max(0.0, min(1.0, value)))
            if color:
                self.item_progress.configure(progress_color=color)
        except Exception:
            pass

    def reset_status(self):
        self.status_var.set(self._base_meta)
        self.meta_lbl.configure(text_color=COLOR_MUTED)
        self.set_progress(0, COLOR_ACCENT)


class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Video/MP3 İndirici")
        self.geometry("760x840")
        self.minsize(700, 640)

        try:
            if getattr(sys, "frozen", False):
                base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            else:
                base = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base, "app_icon.ico")
            if os.path.isfile(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.ffmpeg_path = find_ffmpeg()
        self.video_items = []
        self._stop_flag = False
        self._theme = "dark"
        self._upper_collapsed = False

        self._build_ui()
        self._check_dependencies()

    def _toggle_upper_panels(self):
        self._upper_collapsed = not self._upper_collapsed
        if self._upper_collapsed:
            self.source_card.pack_forget()
            self.settings_card.pack_forget()
            self.expand_btn.configure(text="▾  Daralt")
        else:
            self.source_card.pack(padx=20, fill="x", pady=(10, 0),
                                  before=self.list_card)
            self.settings_card.pack(padx=20, fill="x", pady=(10, 0),
                                    before=self.list_card)
            self.expand_btn.configure(text="▴  Genişlet")

    def _toggle_theme(self):
        self._theme = "light" if self._theme == "dark" else "dark"
        ctk.set_appearance_mode(self._theme)
        if self._theme == "dark":
            self.theme_btn.configure(text="☀  Aydınlık")
        else:
            self.theme_btn.configure(text="🌙  Karanlık")

    def _check_dependencies(self):
        missing = []
        if self.ffmpeg_path is None:
            missing.append("ffmpeg")
        if missing:
            self.dep_label.configure(
                text=f"⚠  Eksik bağımlılık: {', '.join(missing)}",
                text_color=COLOR_DANGER
            )
            self.install_btn.pack(side="right")
            self.download_btn.configure(state="disabled")
        else:
            add_ffmpeg_to_path()
            self.dep_label.configure(text="●  Tüm bağımlılıklar hazır", text_color=COLOR_SUCCESS)
            self.install_btn.pack_forget()
            self.download_btn.configure(state="normal")

    def _make_card(self, parent, **pack_opts):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12,
                            border_width=1, border_color=COLOR_BORDER)
        card.pack(padx=20, fill="x", **pack_opts)
        return card

    def _build_ui(self):
        self.configure(fg_color=COLOR_BG)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(16, 4), padx=20)

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        title = ctk.CTkLabel(title_col, text="YouTube İndirici",
                             font=("Segoe UI", 22, "bold"), text_color=COLOR_TEXT)
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(title_col, text="Tek video, playlist veya manuel liste — paralel indirme destekli",
                                font=("Segoe UI", 11), text_color=COLOR_MUTED)
        subtitle.pack(anchor="w", pady=(2, 0))

        self.theme_btn = ctk.CTkButton(
            header, text="☀  Aydınlık", width=104, height=34,
            font=("Segoe UI", 11, "bold"), corner_radius=8,
            fg_color=COLOR_CARD, hover_color=COLOR_HOVER_SUBTLE,
            text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="right", anchor="n", pady=(4, 0))

        dep_card = self._make_card(self, pady=(10, 0))
        dep_inner = ctk.CTkFrame(dep_card, fg_color="transparent")
        dep_inner.pack(fill="x", padx=14, pady=8)

        self.dep_label = ctk.CTkLabel(dep_inner, text="Kontrol ediliyor...",
                                       font=("Segoe UI", 12), text_color=COLOR_MUTED)
        self.dep_label.pack(side="left")

        self.install_btn = ctk.CTkButton(
            dep_inner, text="ffmpeg Kur", width=110, height=28,
            font=("Segoe UI", 11, "bold"),
            fg_color=COLOR_WARNING, hover_color="#d97706", text_color="#1a1a1a",
            corner_radius=8, command=self._install_ffmpeg
        )

        self.source_card = self._make_card(self, pady=(10, 0))
        src_inner = ctk.CTkFrame(self.source_card, fg_color="transparent")
        src_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(src_inner, text="KAYNAK",
                     font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w")

        url_row = ctk.CTkFrame(src_inner, fg_color="transparent")
        url_row.pack(fill="x", pady=(6, 0))

        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="https://www.youtube.com/watch?v=... veya playlist?list=...",
            height=40, font=("Segoe UI", 12),
            fg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, corner_radius=8,
            text_color=COLOR_TEXT, placeholder_text_color=COLOR_MUTED,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self._start_fetch())

        self.fetch_btn = ctk.CTkButton(
            url_row, text="Listele", width=96, height=40,
            font=("Segoe UI", 12, "bold"), corner_radius=8,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            command=self._start_fetch
        )
        self.fetch_btn.pack(side="right")

        self.manual_btn = ctk.CTkButton(
            url_row, text="Manuel", width=84, height=40,
            font=("Segoe UI", 12), corner_radius=8,
            fg_color=COLOR_CARD_ALT, hover_color=COLOR_HOVER_SUBTLE,
            text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            command=self._open_manual_dialog
        )
        self.manual_btn.pack(side="right", padx=(0, 6))

        self.settings_card = self._make_card(self, pady=(10, 0))
        set_inner = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        set_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(set_inner, text="İNDİRME AYARLARI",
                     font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w")

        format_frame = ctk.CTkFrame(set_inner, fg_color="transparent")
        format_frame.pack(fill="x", pady=(8, 0))

        def _col(label_text, var, values, command=None):
            col = ctk.CTkFrame(format_frame, fg_color="transparent")
            ctk.CTkLabel(col, text=label_text, font=("Segoe UI", 11),
                         text_color=COLOR_MUTED).pack(anchor="w")
            menu = ctk.CTkOptionMenu(
                col, variable=var, values=values, command=command,
                height=36, font=("Segoe UI", 12), corner_radius=8,
                fg_color=COLOR_CARD_ALT, button_color=COLOR_ACCENT,
                button_hover_color=COLOR_ACCENT_HOVER,
                text_color=COLOR_TEXT, dropdown_fg_color=COLOR_CARD,
                dropdown_text_color=COLOR_TEXT,
                dropdown_hover_color=COLOR_HOVER_SUBTLE,
            )
            menu.pack(fill="x", pady=(4, 0))
            return col, menu

        self.format_var = ctk.StringVar(value="MP4 Video")
        col1, self.format_menu = _col("Format", self.format_var,
                                       ["MP4 Video", "MP3 Ses"], self._on_format_change)
        col1.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.quality_var = ctk.StringVar(value="1080p")
        col2, self.quality_menu = _col("Kalite", self.quality_var,
                                        ["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p"])
        col2.pack(side="left", fill="x", expand=True, padx=6)

        self.concurrency_var = ctk.StringVar(value="3")
        col3, self.concurrency_menu = _col("Eş Zamanlı", self.concurrency_var,
                                            ["1", "3", "5", "10", "20", "Limitsiz"])
        col3.pack(side="left", fill="x", expand=True, padx=(6, 0))

        folder_row = ctk.CTkFrame(set_inner, fg_color="transparent")
        folder_row.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(folder_row, text="Kayıt Yeri",
                     font=("Segoe UI", 11), text_color=COLOR_MUTED).pack(anchor="w")

        folder_inner = ctk.CTkFrame(folder_row, fg_color="transparent")
        folder_inner.pack(fill="x", pady=(4, 0))

        self.folder_var = ctk.StringVar(value=self.download_folder)
        self.folder_entry = ctk.CTkEntry(
            folder_inner, textvariable=self.folder_var, height=36,
            font=("Segoe UI", 11), state="disabled",
            fg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, corner_radius=8,
            text_color=COLOR_TEXT,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            folder_inner, text="Gözat", width=80, height=36,
            font=("Segoe UI", 11), corner_radius=8,
            fg_color=COLOR_CARD_ALT, hover_color=COLOR_HOVER_SUBTLE,
            text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            command=self._browse_folder
        )
        browse_btn.pack(side="right")

        self.list_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12,
                                       border_width=1, border_color=COLOR_BORDER)

        list_header = ctk.CTkFrame(self.list_card, fg_color="transparent")
        list_header.pack(padx=16, fill="x", pady=(12, 6))

        title_frame = ctk.CTkFrame(list_header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        self.list_title = ctk.CTkLabel(title_frame, text="Liste",
                                        font=("Segoe UI", 13, "bold"),
                                        text_color=COLOR_TEXT)
        self.list_title.pack(side="left")

        self.list_count = ctk.CTkLabel(title_frame, text="",
                                        font=("Segoe UI", 11),
                                        text_color=COLOR_MUTED)
        self.list_count.pack(side="left", padx=(8, 2))

        self.select_all_var = ctk.BooleanVar(value=True)
        self.select_all_check = ctk.CTkCheckBox(
            list_header, text="Tümünü seç",
            variable=self.select_all_var, font=("Segoe UI", 11),
            text_color=COLOR_TEXT, checkbox_width=18, checkbox_height=18,
            corner_radius=4, command=self._toggle_select_all
        )
        self.select_all_check.pack(side="right", padx=(0, 8))

        self.expand_btn = ctk.CTkButton(
            list_header, text="▴  Genişlet", width=96, height=26,
            font=("Segoe UI", 11), corner_radius=6,
            fg_color=COLOR_CARD_ALT, hover_color=COLOR_HOVER_SUBTLE,
            text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            command=self._toggle_upper_panels,
        )
        self.expand_btn.pack(side="right", padx=(0, 8))

        search_row = ctk.CTkFrame(self.list_card, fg_color="transparent")
        search_row.pack(padx=16, fill="x", pady=(0, 6))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Listede ara... (başlığa göre filtrele)",
            height=32, font=("Segoe UI", 11),
            textvariable=self.search_var,
            fg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, corner_radius=8,
            text_color=COLOR_TEXT, placeholder_text_color=COLOR_MUTED,
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        self.search_clear_btn = ctk.CTkButton(
            search_row, text="✕", width=32, height=32,
            font=("Segoe UI", 13), corner_radius=8,
            fg_color=COLOR_CARD_ALT, hover_color=COLOR_HOVER_SUBTLE,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            command=lambda: self.search_var.set("")
        )
        self.search_clear_btn.pack(side="right", padx=(6, 0))

        self.search_var.trace_add("write", lambda *_: self._filter_list())

        self.list_frame = ctk.CTkScrollableFrame(
            self.list_card, height=140, fg_color="transparent", corner_radius=0
        )
        self.list_frame.pack(padx=10, pady=(0, 12), fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="URL girip 'Listele' butonuna basın\nveya 'Manuel' ile birden çok link yapıştırın.",
            font=("Segoe UI", 12), text_color=COLOR_MUTED, justify="center"
        )
        self.empty_label.pack(pady=50)

        progress_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12,
                                      border_width=1, border_color=COLOR_BORDER)
        progress_card.pack(side="bottom", padx=20, pady=(8, 14), fill="x")

        self.cookie_var = ctk.BooleanVar(value=False)
        self.cookie_check = ctk.CTkCheckBox(
            self, text="Chrome çerezlerini kullan (yaş kısıtlamalı videolar için)",
            variable=self.cookie_var, font=("Segoe UI", 11),
            text_color=COLOR_TEXT, checkbox_width=18, checkbox_height=18,
            corner_radius=4
        )
        self.cookie_check.pack(side="bottom", padx=24, pady=(6, 0), anchor="w")

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(side="bottom", padx=20, fill="x", pady=(8, 0))

        self.download_btn = ctk.CTkButton(
            action_row, text="↓  Seçilenleri İndir", height=46,
            font=("Segoe UI", 14, "bold"), corner_radius=10,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            command=self._start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            action_row, text="Temizle", height=46, width=110,
            font=("Segoe UI", 12), corner_radius=10,
            fg_color=COLOR_CARD_ALT, hover_color=COLOR_HOVER_SUBTLE,
            text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            command=self._clear_list
        )
        self.clear_btn.pack(side="right")

        self.list_card.pack(padx=20, pady=(10, 0), fill="both", expand=True)

        prog_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=14, pady=10)

        info_row = ctk.CTkFrame(prog_inner, fg_color="transparent")
        info_row.pack(fill="x")

        self.status_label = ctk.CTkLabel(info_row, text="Hazır",
                                          font=("Segoe UI", 12),
                                          text_color=COLOR_MUTED)
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(info_row, text="",
                                           font=("Segoe UI", 13, "bold"),
                                           text_color=COLOR_TEXT)
        self.percent_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            prog_inner, height=10, corner_radius=5,
            progress_color=COLOR_ACCENT, fg_color=COLOR_CARD_ALT
        )
        self.progress_bar.pack(fill="x", pady=(8, 0))
        self.progress_bar.set(0)

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
            if item.winfo_ismapped():
                item.var.set(state)

    def _filter_list(self):
        q = self.search_var.get().strip().lower()
        for item in self.video_items:
            item.pack_forget()
        visible = 0
        for item in self.video_items:
            if not q or q in item.title_text.lower():
                item.pack(fill="x", padx=6, pady=3)
                visible += 1
        total = len(self.video_items)
        if total:
            if q:
                self.list_count.configure(text=f"({visible}/{total} görünür)")
            else:
                self.list_count.configure(text=f"({total} video)")

    def _clear_list(self):
        for item in self.video_items:
            item.destroy()
        self.video_items = []
        self.search_var.set("")
        self.list_count.configure(text="")
        self.list_title.configure(text="Liste")
        self.progress_bar.configure(progress_color=COLOR_ACCENT)
        self.status_label.configure(text="Hazır", text_color=COLOR_MUTED)
        if not self.empty_label.winfo_exists():
            self.empty_label = ctk.CTkLabel(
                self.list_frame,
                text="URL girip 'Listele' butonuna basın.\nTek video veya playlist link'i çalışır.",
                font=("Segoe UI", 12), text_color=COLOR_MUTED
            )
        self.empty_label.pack(pady=40)
        self.percent_label.configure(text="")
        self.progress_bar.set(0)

    def _open_manual_dialog(self):
        ManualLinksDialog(self, on_submit=self._add_manual_urls)

    def _add_manual_urls(self, urls, dup_in_paste=0, playlist_skipped=0):
        if self.empty_label.winfo_exists():
            self.empty_label.destroy()

        existing = {clean_video_url(it.video_url) for it in self.video_items}
        new_urls = [u for u in urls if u not in existing]
        already_in_list = len(urls) - len(new_urls)

        if not new_urls:
            self.status_label.configure(text="Tüm linkler zaten listede.", text_color=COLOR_WARNING)
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
        self._filter_list()

        parts = [f"{len(new_urls)} link eklendi"]
        skipped_notes = []
        if dup_in_paste:
            skipped_notes.append(f"{dup_in_paste} mükerrer")
        if already_in_list:
            skipped_notes.append(f"{already_in_list} zaten listede")
        if playlist_skipped:
            skipped_notes.append(f"{playlist_skipped} playlist")
        if skipped_notes:
            parts.append("(" + ", ".join(skipped_notes) + " atlandı)")
        parts.append("— başlıklar çekiliyor...")
        self.status_label.configure(text=" ".join(parts), text_color=COLOR_INFO)

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

        self.after(0, lambda: self.status_label.configure(text="Hazır — seçim yapıp indirin", text_color=COLOR_SUCCESS))
        self.after(0, self._filter_list)

    def _start_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Lütfen bir URL girin!", text_color=COLOR_DANGER)
            return

        self.fetch_btn.configure(state="disabled", text="...")
        self.status_label.configure(text="Liste alınıyor...", text_color=COLOR_INFO)
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
        self.status_label.configure(text=f"Liste alınamadı: {err[:80]}", text_color=COLOR_DANGER)

    def _populate_list(self, entries, playlist_title):
        for item in self.video_items:
            item.destroy()
        self.video_items = []
        if self.empty_label.winfo_exists():
            self.empty_label.destroy()

        if not entries:
            self.empty_label = ctk.CTkLabel(self.list_frame, text="Video bulunamadı.", font=("Segoe UI", 12), text_color=COLOR_WARNING)
            self.empty_label.pack(pady=40)
            self.fetch_btn.configure(state="normal", text="Listele")
            self.status_label.configure(text="", text_color=COLOR_MUTED)
            return

        for i, (title, video_url, duration) in enumerate(entries, 1):
            item = VideoItem(self.list_frame, i, title, video_url, duration)
            item.pack(fill="x", padx=6, pady=3)
            self.video_items.append(item)

        if playlist_title:
            self.list_title.configure(text=playlist_title[:50])
        else:
            self.list_title.configure(text="Tekli Video")
        self._filter_list()
        self.select_all_var.set(True)
        self.fetch_btn.configure(state="normal", text="Listele")
        self.status_label.configure(text="Hazır — seçim yapıp indirin", text_color=COLOR_SUCCESS)

    def _start_download(self):
        if not self.video_items:
            self.status_label.configure(text="Önce listele!", text_color=COLOR_DANGER)
            return

        selected = [it for it in self.video_items if it.is_selected()]
        if not selected:
            self.status_label.configure(text="Hiçbir video seçilmedi!", text_color=COLOR_DANGER)
            return

        self.download_btn.configure(state="disabled", text="İndiriliyor...")
        self.fetch_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.percent_label.configure(text="")
        self._stop_flag = False

        threading.Thread(target=self._download_all, args=(selected,), daemon=True).start()

    def _progress_hook_parallel(self, item):
        def hook(d):
            if d["status"] == "downloading":
                tb = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / tb) if tb > 0 else 0.0
                with self._progress_lock:
                    self._progress_state[item] = min(pct * 0.9, 0.9)
                speed = d.get("speed")
                if speed:
                    mb_speed = speed / (1024 * 1024)
                    text = f"İndiriliyor  •  %{pct * 100:.0f}  •  {mb_speed:.1f} MB/s"
                else:
                    text = f"İndiriliyor  •  %{pct * 100:.0f}"
                self.after(0, lambda t=text, p=pct: (
                    item.set_status(t, COLOR_INFO),
                    item.set_progress(p, COLOR_INFO),
                ))
                self._refresh_overall_progress()
            elif d["status"] == "finished":
                with self._progress_lock:
                    self._progress_state[item] = 0.9
                self.after(0, lambda: item.set_progress(1.0, COLOR_INFO))
                self._refresh_overall_progress()
        return hook

    def _postproc_hook(self, item):
        def hook(d):
            status = d.get("status")
            if status == "started":
                with self._progress_lock:
                    self._convert_start[item] = time.time()
                self.after(0, lambda: (
                    item.set_status("Dönüştürülüyor... 0s", COLOR_WARNING),
                    item.set_progress(1.0, COLOR_WARNING),
                ))
                self._refresh_overall_progress()
            elif status == "finished":
                with self._progress_lock:
                    self._convert_start.pop(item, None)
                    self._progress_state[item] = 0.98
                self._refresh_overall_progress()
        return hook

    def _tick_converting(self):
        if not getattr(self, "_ticking", False):
            return
        now = time.time()
        with self._progress_lock:
            snapshot = dict(self._convert_start)
        for it, start in snapshot.items():
            elapsed = int(now - start)
            it.set_status(f"Dönüştürülüyor... {elapsed}s", COLOR_WARNING)
        self._refresh_overall_progress()
        self.after(1000, self._tick_converting)

    def _refresh_overall_progress(self):
        with self._progress_lock:
            if not self._progress_state or not self._total:
                return
            overall = sum(self._progress_state.values()) / self._total
            done = self._completed + self._failed
            downloading = sum(1 for it, v in self._progress_state.items()
                              if 0 < v < 0.9 and it not in self._convert_start)
            converting = len(self._convert_start)
            total = self._total
        self.after(0, lambda o=overall, d=done, dl=downloading, cv=converting, t=total: (
            self.progress_bar.set(o),
            self.percent_label.configure(
                text=f"{d}/{t}   ↓ {dl}   ⚙ {cv}"
            ),
        ))

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

    def _download_one(self, item, is_mp3, quality):
        opts = self._build_opts(is_mp3, quality)
        opts["progress_hooks"] = [self._progress_hook_parallel(item)]
        opts["postprocessor_hooks"] = [self._postproc_hook(item)]
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

            with self._progress_lock:
                self._progress_state[item] = 1.0
                self._completed += 1
                self._convert_start.pop(item, None)
            self.after(0, lambda: (
                item.set_status("✓  Tamamlandı", COLOR_SUCCESS),
                item.set_progress(1.0, COLOR_SUCCESS),
            ))
        except Exception as e:
            with self._progress_lock:
                self._progress_state[item] = 1.0
                self._failed += 1
                self._convert_start.pop(item, None)
            err = str(e)[:40]
            self.after(0, lambda er=err: (
                item.set_status(f"✕  Hata: {er}", COLOR_DANGER),
                item.set_progress(1.0, COLOR_DANGER),
            ))

        self._refresh_overall_progress()

    def _download_all(self, selected):
        is_mp3 = self.format_var.get() == "MP3 Ses"
        quality = self.quality_var.get()
        total = len(selected)

        conc_str = self.concurrency_var.get()
        if conc_str == "Limitsiz":
            max_workers = max(1, total)
        else:
            try:
                max_workers = max(1, int(conc_str))
            except ValueError:
                max_workers = 1
        max_workers = min(max_workers, total)

        self._progress_state = {it: 0.0 for it in selected}
        self._convert_start = {}
        self._completed = 0
        self._failed = 0
        self._progress_lock = threading.Lock()
        self._total = total
        self._ticking = True

        self.after(0, lambda mw=max_workers: self.status_label.configure(
            text=f"İndiriliyor — eş zamanlı: {mw} (toplam {total})", text_color=COLOR_INFO
        ))
        self.after(0, self._tick_converting)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self._download_one, it, is_mp3, quality) for it in selected]
            concurrent.futures.wait(futures)

        self._ticking = False
        self.after(0, self._download_finished_ui)

    def _download_finished_ui(self):
        success = self._completed
        failed = self._failed
        total = self._total
        self.percent_label.configure(text=f"{success}/{total}")
        self.progress_bar.set(1.0 if total else 0)
        if failed == 0:
            self.status_label.configure(text=f"✓  {success} video başarıyla indirildi", text_color=COLOR_SUCCESS)
            self.progress_bar.configure(progress_color=COLOR_SUCCESS)
        else:
            self.status_label.configure(text=f"{success} başarılı, {failed} başarısız", text_color=COLOR_WARNING)
            self.progress_bar.configure(progress_color=COLOR_WARNING)

        self.download_btn.configure(state="normal", text="↓  Seçilenleri İndir")
        self.fetch_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
