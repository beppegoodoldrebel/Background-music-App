; Installer di Music Overlay (Inno Setup 6).
; Si compila con packaging\build.py, che passa la versione: ISCC /DAppVersion=0.5.0 MusicOverlay.iss

#ifndef AppVersion
  #error Passa la versione: ISCC /DAppVersion=x.y.z MusicOverlay.iss
#endif

#define AppName "Music Overlay"
#define AppExe "Music Overlay.exe"

[Setup]
; AppId fisso: le versioni future aggiornano questa installazione invece di crearne un'altra.
AppId={{6D22D095-43F6-4077-BAEC-6A945958F391}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=beppegoodoldrebel
AppPublisherURL=https://github.com/beppegoodoldrebel/Background-music-App
VersionInfoVersion={#AppVersion}
; Installazione per l'utente corrente: nessuna richiesta di amministratore.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Lo stesso nome usato dall'app per l'istanza unica: se è aperta, l'installer chiede di chiuderla.
AppMutex=MusicOverlay.SingleInstance
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
OutputDir=..\build\installer
OutputBaseFilename=MusicOverlay-{#AppVersion}-Setup
ShowLanguageDialog=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
english.StartWithWindows=Start Music Overlay when Windows starts
italian.StartWithWindows=Avvia Music Overlay all'avvio di Windows
french.StartWithWindows=Lancer Music Overlay au démarrage de Windows
spanish.StartWithWindows=Iniciar Music Overlay al iniciar Windows
german.StartWithWindows=Music Overlay beim Windows-Start starten

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "{cm:StartWithWindows}"; Flags: unchecked

[Files]
Source: "..\build\dist\{#AppName}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
