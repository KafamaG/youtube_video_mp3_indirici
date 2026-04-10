[Setup]
AppName=YouTube Indirici
AppVersion=1.0.0
AppVerName=YouTube Indirici 1.0
AppPublisher=YouTube Indirici
AppPublisherURL=https://github.com/KafamaG/youtube_video_mp3_indirici
AppCopyright=Copyright (C) 2026 YouTube Indirici
DefaultDirName={autopf}\YouTubeIndirici
DefaultGroupName=YouTube Indirici
UninstallDisplayIcon={app}\YouTubeIndirici.exe
UninstallDisplayName=YouTube Indirici
OutputDir=installer_output
OutputBaseFilename=YouTubeIndirici_Setup
SetupIconFile=app_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
VersionInfoVersion=1.0.0.0
VersionInfoCompany=YouTube Indirici
VersionInfoDescription=YouTube Video ve MP3 Indirici Kurulumu
VersionInfoCopyright=Copyright (C) 2026 YouTube Indirici
VersionInfoProductName=YouTube Indirici
VersionInfoProductVersion=1.0.0.0

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "dist\YouTubeIndirici.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\YouTube Indirici"; Filename: "{app}\YouTubeIndirici.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\YouTube Indirici"; Filename: "{app}\YouTubeIndirici.exe"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek simgeler:"

[Run]
Filename: "{app}\YouTubeIndirici.exe"; Description: "YouTube Indirici'yi başlat"; Flags: nowait postinstall skipifsilent
