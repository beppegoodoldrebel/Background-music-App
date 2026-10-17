"""Schermata d'avvio: icona e nome dell'app al centro dello schermo per un
paio di secondi, poi sfuma. Non prende il focus."""
import ctypes
import tkinter as tk

from PIL import ImageTk

from . import icon, theme

DURATION_MS = 2000
FADE_MS = 250
FADE_STEPS = 10
ICON_SIZE = 96  # px a 100% di scala

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000


def show(root, pal):
    win = tk.Toplevel(root)
    win.withdraw()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=pal.bg)

    scale = theme.ui_scale(win)
    px = lambda v: round(v * scale)  # noqa: E731
    image = ImageTk.PhotoImage(icon.render(px(ICON_SIZE)), master=win)
    win._image = image  # tenuta in vita finché esiste la finestra

    body = tk.Frame(win, bg=pal.bg)
    body.pack(padx=px(48), pady=(px(36), px(30)))
    tk.Label(body, image=image, bg=pal.bg).pack()
    font = theme.font_family(win, "Segoe UI Variable Display Semibold", "Segoe UI Semibold")
    tk.Label(body, text="Music Overlay", font=(font, 18), bg=pal.bg, fg=pal.fg).pack(pady=(px(14), 0))

    theme.center_on_screen(win)
    win.deiconify()
    win.update_idletasks()
    hwnd = int(win.wm_frame(), 16)
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
    theme.style_popup(hwnd, pal.border)  # angoli arrotondati e bordo sottile

    def fade(step=FADE_STEPS):
        if step <= 0:
            win.destroy()
            return
        win.attributes("-alpha", step / FADE_STEPS)
        win.after(FADE_MS // FADE_STEPS, fade, step - 1)

    win.after(DURATION_MS - FADE_MS, fade)
