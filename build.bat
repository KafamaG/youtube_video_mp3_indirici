@echo off
REM Build script for YouTube Video/MP3 Indirici (Windows)
REM Produces a single-file portable .exe in dist\

setlocal

echo [1/3] Gerekli paketler kontrol ediliyor...
py -m pip install --quiet --upgrade pip
py -m pip install --quiet -r requirements.txt
py -m pip install --quiet pyinstaller pillow

echo [2/3] Ikon yeniden uretiliyor...
py make_icon.py

echo [3/3] PyInstaller ile EXE olusturuluyor...
py -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "YouTubeIndirici" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    app.py

if errorlevel 1 (
    echo.
    echo HATA: Build basarisiz.
    exit /b 1
)

echo.
echo Build tamamlandi: dist\YouTubeIndirici.exe
echo.
endlocal
