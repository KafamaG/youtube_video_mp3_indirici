import customtkinter as ctk
import threading
import shutil
import subprocess
import os
import sys
import zipfile
import urllib.request
import yt_dlp

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


class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Video/MP3 İndirici")
        self.geometry("620x580")
        self.resizable(False, False)

        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.ffmpeg_path = find_ffmpeg()

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
        title.pack(pady=(24, 4))

        subtitle = ctk.CTkLabel(self, text="MP4 video veya MP3 ses olarak indir", font=("Segoe UI", 13), text_color="gray")
        subtitle.pack(pady=(0, 12))

        dep_frame = ctk.CTkFrame(self, fg_color="transparent")
        dep_frame.pack(padx=32, fill="x")

        self.dep_label = ctk.CTkLabel(dep_frame, text="Kontrol ediliyor...", font=("Segoe UI", 12))
        self.dep_label.pack(side="left")

        self.install_btn = ctk.CTkButton(
            dep_frame, text="ffmpeg Kur", width=110, height=30,
            font=("Segoe UI", 11), fg_color="#cc6600", hover_color="#aa5500",
            command=self._install_ffmpeg
        )

        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(padx=32, fill="x", pady=(10, 0))

        ctk.CTkLabel(url_frame, text="Video URL:", font=("Segoe UI", 13)).pack(anchor="w")
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://www.youtube.com/watch?v=...", height=40, font=("Segoe UI", 13))
        self.url_entry.pack(fill="x", pady=(4, 0))

        format_frame = ctk.CTkFrame(self, fg_color="transparent")
        format_frame.pack(padx=32, fill="x", pady=(14, 0))

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
        folder_frame.pack(padx=32, fill="x", pady=(14, 0))

        ctk.CTkLabel(folder_frame, text="Kayıt Yeri:", font=("Segoe UI", 13)).pack(anchor="w")

        folder_row = ctk.CTkFrame(folder_frame, fg_color="transparent")
        folder_row.pack(fill="x", pady=(4, 0))

        self.folder_var = ctk.StringVar(value=self.download_folder)
        self.folder_entry = ctk.CTkEntry(folder_row, textvariable=self.folder_var, height=40, font=("Segoe UI", 12), state="disabled")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(folder_row, text="Gözat", width=80, height=40, command=self._browse_folder)
        browse_btn.pack(side="right")

        self.download_btn = ctk.CTkButton(
            self, text="İndir", height=44, font=("Segoe UI", 15, "bold"),
            corner_radius=10, command=self._start_download
        )
        self.download_btn.pack(padx=32, pady=(14, 0), fill="x")

        self.progress_bar = ctk.CTkProgressBar(self, height=14, corner_radius=6)
        self.progress_bar.pack(padx=32, pady=(18, 0), fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 12), text_color="gray")
        self.status_label.pack(pady=(8, 0))

        self.percent_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 13, "bold"))
        self.percent_label.pack(pady=(2, 0))

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

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Lütfen bir URL girin!", text_color="#ff4444")
            return

        self.download_btn.configure(state="disabled", text="İndiriliyor...")
        self.progress_bar.set(0)
        self.percent_label.configure(text="")
        self.status_label.configure(text="Hazırlanıyor...", text_color="gray")

        thread = threading.Thread(target=self._download, args=(url,), daemon=True)
        thread.start()

    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = downloaded / total
                self.progress_bar.set(pct)
                self.percent_label.configure(text=f"%{pct * 100:.1f}")
            speed = d.get("speed")
            if speed:
                mb_speed = speed / (1024 * 1024)
                self.status_label.configure(text=f"İndiriliyor... ({mb_speed:.1f} MB/s)", text_color="#00aaff")
        elif d["status"] == "finished":
            self.status_label.configure(text="Birleştiriliyor...", text_color="orange")

    def _download(self, url):
        is_mp3 = self.format_var.get() == "MP3 Ses"
        quality = self.quality_var.get()

        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "ffmpeg_location": self.ffmpeg_path,
            "quiet": True,
            "no_warnings": True,
        }

        if is_mp3:
            bitrate = quality.replace(" kbps", "")
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }]
        else:
            height = quality.replace("p", "").replace(" (4K)", "")
            ydl_opts["format"] = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]"
            )
            ydl_opts["merge_output_format"] = "mp4"

        ydl_opts["cookiesfrombrowser"] = ("chrome",)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.progress_bar.set(1)
            self.percent_label.configure(text="%100")
            self.status_label.configure(text="İndirme tamamlandı!", text_color="#00cc66")
        except Exception as e:
            self.status_label.configure(text=f"Hata: {str(e)[:60]}", text_color="#ff4444")
            self.percent_label.configure(text="")
            self.progress_bar.set(0)
        finally:
            self.download_btn.configure(state="normal", text="İndir")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
