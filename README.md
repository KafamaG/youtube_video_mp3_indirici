# YouTube Video & MP3 İndirici

Modern arayüzlü, paralel indirme destekli YouTube video / MP3 indirici masaüstü uygulaması.

[![Windows](https://img.shields.io/badge/Windows-blue?style=flat-square&logo=windows&logoColor=white)](https://github.com/KafamaG/youtube_video_mp3_indirici/releases/latest)
![Python](https://img.shields.io/badge/Python-3.10%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## Özellikler

- **Paralel indirme** — Eş zamanlı 1 / 3 / 5 / 10 / 20 / Limitsiz video indirme. Dönüşüm (ffmpeg) de paralel çalışır.
- **MP4 Video** — 360p / 480p / 720p / 1080p / 1440p / 2160p (4K) kalite seçenekleri.
- **MP3 Ses** — 128 / 192 / 256 / 320 kbps bitrate seçenekleri.
- **Playlist + Tekli video + Manuel toplu liste** — Bir URL listesini topluca yapıştırarak liste oluşturma.
- **Liste içi arama** — Yüzlerce videoluk playlistlerde anlık başlık filtreleme.
- **Per-video ilerleme** — Her video için ayrı progress bar, anlık MB/s hızı ve dönüşüm sayacı.
- **Aydınlık / Karanlık tema** — Tek tıkla mod değişimi.
- **Otomatik ffmpeg kurulumu** — ffmpeg yoksa uygulama içinden tek tıkla indirilir.
- **Chrome çerez desteği** — Yaş kısıtlamalı videolar için.

## Kurulum

### Hazır EXE İndir

[![Windows İndir](https://img.shields.io/badge/⬇_İndir-Windows_EXE-blue?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/KafamaG/youtube_video_mp3_indirici/releases/latest)

### Kaynaktan Çalıştırma

```bash
git clone https://github.com/KafamaG/youtube_video_mp3_indirici.git
cd youtube_video_mp3_indirici
pip install -r requirements.txt
python app.py
```

## Gereksinimler

- Python 3.10+
- ffmpeg (uygulama içinden otomatik kurulabilir)

## Kullanılan Kütüphaneler

| Kütüphane | Açıklama |
|-----------|----------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube indirme motoru |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern GUI arayüzü |

## Kullanım

1. **URL yapıştırın** — Tek video, playlist veya `Manuel` ile birden çok link.
2. **Liste alın** — `Listele` butonu ile video başlıklarını çekin.
3. **Ayarları seçin** — Format (MP4/MP3), kalite, eş zamanlı indirme adedi.
4. **Kayıt yerini belirleyin** — Varsayılan: `~/Downloads`.
5. **(Opsiyonel)** Listede arama kutusu ile filtreleyin, gereksizleri seçim dışı bırakın.
6. **İndirin** — `Seçilenleri İndir`. Her video kendi ilerlemesini, dönüşüm süresini gösterir.

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
