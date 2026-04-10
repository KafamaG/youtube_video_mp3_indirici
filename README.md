# YouTube Video & MP3 İndirici

YouTube videolarını MP4 veya MP3 formatında indirmenizi sağlayan masaüstü uygulaması.

## Özellikler

- **MP4 Video İndirme** — 360p, 480p, 720p, 1080p, 1440p, 2160p (4K) kalite seçenekleri
- **MP3 Ses İndirme** — 128, 192, 256, 320 kbps kalite seçenekleri
- **Otomatik ffmpeg Kurulumu** — ffmpeg yoksa uygulama içinden tek tıkla kurulum
- **İlerleme Çubuğu** — İndirme yüzdesi ve hız göstergesi (MB/s)
- **Kayıt Yeri Seçimi** — İndirilen dosyaların kaydedileceği klasörü seçebilme
- **Koyu Tema** — Modern ve şık arayüz

## Ekran Görüntüsü

![YouTube İndirici](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## Kurulum

### Hazır Kurulum Dosyası (Önerilen)

[Releases](https://github.com/KafamaG/youtube_video_mp3_indirici/releases) sayfasından `YouTubeIndirici_Setup.exe` dosyasını indirip çalıştırın.

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
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube video indirme motoru |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern GUI arayüzü |

## Kullanım

1. Uygulamayı açın
2. YouTube video URL'sini yapıştırın
3. Format seçin (MP4 Video veya MP3 Ses)
4. Kalite seçin
5. **İndir** butonuna tıklayın

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
