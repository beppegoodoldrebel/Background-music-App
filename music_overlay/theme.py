"""Tema chiaro/scuro sincronizzato con Windows.

- Finestre ttk: tema Sun Valley (sv-ttk), lo stile Fluent di Windows 11.
- Overlay: palette propria, perché è disegnato a mano.
- Barra del titolo e angoli: attributi DWM di Windows 11.
"""
import ctypes
import winreg
from ctypes import wintypes
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk

import sv_ttk


@dataclass(frozen=True)
class Palette:
    dark: bool
    window: str  # sfondo delle finestre ttk (coincide con sv-ttk)
    field: str   # sfondo di liste e campi
    bg: str      # sfondo dell'overlay
    hover: str
    press: str
    fg: str
    muted: str
    border: str
    accent: str
    warn: str
    track: str    # parte vuota della barra del volume
    outline: str  # contorno dei testi con sfondo trasparente


DARK = Palette(
    dark=True, window="#1c1c1c", field="#2b2b2b",
    bg="#202020", hover="#2d2d2d", press="#383838",
    fg="#ffffff", muted="#a0a0a0", border="#3b3b3b",
    accent="#1ed760", warn="#fce100", track="#4a4a4a", outline="#000000",
)
LIGHT = Palette(
    dark=False, window="#fafafa", field="#ffffff",
    bg="#f9f9f9", hover="#ebebeb", press="#dedede",
    fg="#1b1b1b", muted="#5d5d5d", border="#dcdcdc",
    accent="#16a34a", warn="#9d5d00", track="#d0d0d0", outline="#ffffff",
)

# Dimensioni in punti, così scalano con le impostazioni DPI di Windows
# (sv-ttk le definisce in pixel).
SV_FONT_POINTS = {
    "SunValleyCaptionFont": 9,
    "SunValleyBodyFont": 10,
    "SunValleyBodyStrongFont": 10,
    "SunValleyBodyLargeFont": 13,
    "SunValleySubtitleFont": 15,
}

_PERSONALIZE_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWA_COLOR_NONE = 0xFFFFFFFE
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2
SWP_FRAMECHANGED_NOMOVE = 0x0020 | 0x0001 | 0x0002 | 0x0004 | 0x0010

_dwm = ctypes.windll.dwmapi
_user32 = ctypes.windll.user32


def system_is_dark():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _PERSONALIZE_KEY) as key:
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except OSError:
        return False


def palette(dark):
    return DARK if dark else LIGHT


def apply(root, dark):
    """Applica il tema a tutte le finestre ttk e restituisce la palette."""
    pal = palette(dark)
    sv_ttk.set_theme("dark" if dark else "light", root)
    for name, points in SV_FONT_POINTS.items():
        tkfont.nametofont(name, root).configure(size=points)
    style = ttk.Style(root)
    style.configure("Muted.TLabel", foreground=pal.muted, font="SunValleyCaptionFont")
    style.configure("Section.TLabel", font="SunValleyBodyStrongFont")
    style.configure("Title.TLabel", font="SunValleySubtitleFont")
    return pal


def font_family(root, preferred, fallback="Segoe UI"):
    return preferred if preferred in tkfont.families(root) else fallback


def _set_dwm_int(hwnd, attribute, value):
    v = ctypes.c_uint(value)
    _dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(v), ctypes.sizeof(v))


def _hex_to_colorref(color):
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    return r | (g << 8) | (b << 16)


def style_title_bar(win, dark):
    """Barra del titolo chiara o scura (Windows 10 20H1+ / 11)."""
    win.update_idletasks()
    hwnd = int(win.wm_frame(), 16)
    _set_dwm_int(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, int(dark))
    # Forza il ridisegno della cornice quando il tema cambia a finestra aperta.
    _user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FRAMECHANGED_NOMOVE)


def style_popup(hwnd, border_color):
    """Angoli arrotondati, ombra e bordo sottile per una finestra senza cornice
    (Windows 11). border_color=None toglie tutto: serve con lo sfondo trasparente,
    dove l'ombra resterebbe visibile come un alone."""
    corners = DWMWCP_DONOTROUND if border_color is None else DWMWCP_ROUND
    _set_dwm_int(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, corners)
    color = DWMWA_COLOR_NONE if border_color is None else _hex_to_colorref(border_color)
    _set_dwm_int(hwnd, DWMWA_BORDER_COLOR, color)


class _MonitorInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


MONITOR_DEFAULTTONEAREST = 2


DWMWA_EXTENDED_FRAME_BOUNDS = 9


def _visible_frame(win):
    """(sinistra, alto, destra, basso) della parte visibile della finestra e lo
    scarto dalla posizione Tk, dovuto al bordo invisibile di Windows 10/11.
    None se la finestra non è visibile."""
    if not win.winfo_viewable():
        return None
    hwnd = int(win.wm_frame(), 16)
    frame, outer = wintypes.RECT(), wintypes.RECT()
    if _dwm.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(frame), ctypes.sizeof(frame)):
        return None
    _user32.GetWindowRect(hwnd, ctypes.byref(outer))
    return frame, frame.left - outer.left, frame.top - outer.top


def center_on_screen(win):
    """Centra la finestra nell'area utile (senza barra delle applicazioni) del
    monitor su cui si trova il mouse. Precisa se la finestra è già visibile,
    altrimenti stima la barra del titolo: va richiamata dopo deiconify()."""
    win.update_idletasks()
    cursor = wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(cursor))
    _user32.MonitorFromPoint.restype = wintypes.HMONITOR
    _user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    monitor = _user32.MonitorFromPoint(cursor, MONITOR_DEFAULTTONEAREST)
    info = _MonitorInfo(cbSize=ctypes.sizeof(_MonitorInfo))
    _user32.GetMonitorInfoW(monitor, ctypes.byref(info))
    work = info.rcWork

    visible = _visible_frame(win)
    if visible:
        frame, dx, dy = visible
        width, height = frame.right - frame.left, frame.bottom - frame.top
    else:
        dx = dy = 0
        width, height = win.winfo_reqwidth(), win.winfo_reqheight() + round(32 * ui_scale(win))
    x = work.left + max(0, (work.right - work.left - width) // 2) - dx
    y = work.top + max(0, (work.bottom - work.top - height) // 2) - dy
    win.geometry(f"+{x}+{y}")


def ui_scale(widget):
    """Scala di Windows (1.0 = 100%). 1.333 è la scala di Tk a 96 DPI."""
    return float(widget.tk.call("tk", "scaling")) / (96 / 72)
