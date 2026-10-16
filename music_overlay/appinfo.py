"""Nome e icona dei programmi, per mostrarli nelle impostazioni.

Il nome viene cercato, in ordine:
1. tra i programmi installati (Impostazioni > App);
2. nella descrizione contenuta nell'exe (FileDescription / ProductName),
   senza etichette di compilazione come "(master@eeeeff1cd)";
3. altrimenti è il nome del file.
"""
import ctypes
import functools
import logging
import os
import re
import winreg
from ctypes import wintypes

import psutil
from PIL import Image

log = logging.getLogger(__name__)

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_version = ctypes.windll.version

UNINSTALL_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _norm(path):
    return os.path.normcase(os.path.normpath(path.strip().strip('"'))) if path else ""


# --- Percorso di un exe ------------------------------------------------------

def find_running_path(exe_name):
    """Percorso completo di un processo aperto con quel nome, se accessibile."""
    for proc in psutil.process_iter(["name", "exe"]):
        if (proc.info["name"] or "").lower() == exe_name.lower() and proc.info["exe"]:
            return proc.info["exe"]
    return None


def running_programs():
    """{nome exe in minuscolo: percorso o None} dei processi aperti."""
    programs = {}
    for proc in psutil.process_iter(["name", "exe"]):
        name = (proc.info["name"] or "").lower()
        if name.endswith(".exe") and not programs.get(name):
            programs[name] = proc.info["exe"]
    return programs


# --- Nome dell'applicazione --------------------------------------------------

@functools.lru_cache(maxsize=1)
def _installed_programs():
    """[(cartella di installazione, icona, nome)] dal registro dei programmi installati."""
    programs = []
    for hive, path in UNINSTALL_KEYS:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue
        with root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, i)) as key:
                        name = winreg.QueryValueEx(key, "DisplayName")[0].strip()
                        values = {}
                        for value in ("InstallLocation", "DisplayIcon"):
                            try:
                                values[value] = winreg.QueryValueEx(key, value)[0]
                            except OSError:
                                values[value] = ""
                except OSError:
                    continue
                icon = values["DisplayIcon"].split(",")[0]
                if name:
                    programs.append((_norm(values["InstallLocation"]), _norm(icon), name))
    return programs


def _installed_name(path):
    exe = _norm(path)
    best, best_len = None, 0
    for location, icon, name in _installed_programs():
        if icon == exe:
            return name
        # La cartella di installazione più specifica che contiene l'exe.
        if location and exe.startswith(location + os.sep) and len(location) > best_len:
            best, best_len = name, len(location)
    return best


def _version_string(path, field):
    size = _version.GetFileVersionInfoSizeW(path, None)
    if not size:
        return None
    data = ctypes.create_string_buffer(size)
    if not _version.GetFileVersionInfoW(path, 0, size, data):
        return None
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    translations = [(0x0409, 0x04B0)]  # inglese / Unicode, se l'exe non ne dichiara
    if _version.VerQueryValueW(data, r"\VarFileInfo\Translation", ctypes.byref(pointer), ctypes.byref(length)):
        words = ctypes.cast(pointer, ctypes.POINTER(wintypes.WORD))
        translations = [(words[i], words[i + 1]) for i in range(0, length.value // 2, 2)] + translations
    for lang, codepage in translations:
        query = rf"\StringFileInfo\{lang:04x}{codepage:04x}\{field}"
        if _version.VerQueryValueW(data, query, ctypes.byref(pointer), ctypes.byref(length)) and length.value:
            # La lunghezza restituita non è affidabile (a volte in byte): legge fino al \0.
            text = ctypes.wstring_at(pointer).strip()
            if text:
                return text
    return None


# Etichette di compilazione in fondo al nome: "(master@eeeeff1cd)", "(a1b2c3d4)", "(v1.2.3)"
_BUILD_TAG = re.compile(r"\s*\((?:[^()]*@[^()]*|[0-9a-f]{7,40}|v?\d+(?:\.\d+)+)\)\s*$", re.IGNORECASE)


def _clean(name):
    return _BUILD_TAG.sub("", name).strip() if name else name


@functools.lru_cache(maxsize=256)
def app_name(exe_name, path=None):
    if path and os.path.isfile(path):
        try:
            name = (_installed_name(path)
                    or _clean(_version_string(path, "FileDescription"))
                    or _clean(_version_string(path, "ProductName")))
            if name:
                return name
        except OSError:
            log.warning("Nome non leggibile per %s", path, exc_info=True)
    return os.path.splitext(exe_name)[0]


# --- Icona -------------------------------------------------------------------

class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


DI_NORMAL = 0x0003

_user32.PrivateExtractIconsW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.UINT),
                                         wintypes.UINT, wintypes.UINT]
_user32.DrawIconEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.HICON, ctypes.c_int,
                               ctypes.c_int, wintypes.UINT, wintypes.HBRUSH, wintypes.UINT]
_user32.DestroyIcon.argtypes = [wintypes.HICON]
_gdi32.CreateCompatibleDC.restype = wintypes.HDC
_gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
_gdi32.CreateDIBSection.restype = wintypes.HBITMAP
_gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ
_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteDC.argtypes = [wintypes.HDC]


@functools.lru_cache(maxsize=256)
def exe_icon(path, size):
    """Icona dell'exe come immagine PIL RGBA, o None."""
    if not path or not os.path.isfile(path):
        return None
    icon = wintypes.HICON()
    if _user32.PrivateExtractIconsW(path, 0, size, size, ctypes.byref(icon), None, 1, 0) != 1 or not icon:
        return None
    dc = _gdi32.CreateCompatibleDC(None)
    header = _BitmapInfoHeader(biSize=ctypes.sizeof(_BitmapInfoHeader), biWidth=size,
                               biHeight=-size, biPlanes=1, biBitCount=32)  # altezza negativa: dall'alto
    bits = ctypes.c_void_p()
    bitmap = _gdi32.CreateDIBSection(dc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
    try:
        old = _gdi32.SelectObject(dc, bitmap)
        _user32.DrawIconEx(dc, 0, 0, icon, size, size, 0, None, DI_NORMAL)
        _gdi32.SelectObject(dc, old)
        data = ctypes.string_at(bits, size * size * 4)
    finally:
        _gdi32.DeleteObject(bitmap)
        _gdi32.DeleteDC(dc)
        _user32.DestroyIcon(icon)
    image = Image.frombuffer("RGBA", (size, size), data, "raw", "BGRA", 0, 1)
    if image.getextrema()[3][1] == 0:  # icone vecchie senza canale alfa
        image.putalpha(255)
    return image
