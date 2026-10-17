"""Crea l'exe (PyInstaller) e l'installer (Inno Setup) della versione in music_overlay/__init__.py.

Uso:  .venv\\Scripts\\python packaging\\build.py
Risultato: build\\installer\\MusicOverlay-<versione>-Setup.exe
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from music_overlay import __version__  # noqa: E402

APP_NAME = "Music Overlay"
BUILD = ROOT / "build"
ISCC_CANDIDATES = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
]

VERSION_INFO = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={t}, prodvers={t}),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'beppegoodoldrebel'),
      StringStruct('FileDescription', '{name}'),
      StringStruct('FileVersion', '{v}'),
      StringStruct('InternalName', '{name}'),
      StringStruct('OriginalFilename', '{name}.exe'),
      StringStruct('ProductName', '{name}'),
      StringStruct('ProductVersion', '{v}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def build_exe():
    """Cartella build/dist/Music Overlay con l'exe e tutto ciò che gli serve."""
    numbers = tuple(int(n) for n in __version__.split(".")) + (0,) * (4 - len(__version__.split(".")))
    version_file = BUILD / "version_info.txt"
    BUILD.mkdir(exist_ok=True)
    version_file.write_text(VERSION_INFO.format(t=numbers, v=__version__, name=APP_NAME), encoding="utf-8")

    PyInstaller.__main__.run([
        str(ROOT / "packaging" / "launcher.py"),
        "--name", APP_NAME,
        "--windowed",            # nessuna finestra del terminale
        "--onedir",              # cartella invece di file unico: avvio immediato, meno falsi allarmi
        "--noconfirm", "--clean",
        "--icon", str(ROOT / "assets" / "icon.ico"),
        "--version-file", str(version_file),
        "--collect-data", "sv_ttk",         # file del tema delle impostazioni
        "--collect-submodules", "winrt",    # API di Windows usate per Spotify
        "--hidden-import", "pystray._win32",
        "--distpath", str(BUILD / "dist"),
        "--workpath", str(BUILD / "work"),
        "--specpath", str(BUILD),
    ])


def build_installer():
    iscc = next((p for p in ISCC_CANDIDATES if p.is_file()), None) or shutil.which("ISCC")
    if not iscc:
        sys.exit("Inno Setup non trovato: installalo con  winget install JRSoftware.InnoSetup")
    subprocess.run([str(iscc), f"/DAppVersion={__version__}", str(ROOT / "packaging" / "MusicOverlay.iss")],
                   check=True)


if __name__ == "__main__":
    print(f"Build di {APP_NAME} {__version__}")
    build_exe()
    build_installer()
    print(f"Fatto: {BUILD / 'installer' / f'MusicOverlay-{__version__}-Setup.exe'}")
