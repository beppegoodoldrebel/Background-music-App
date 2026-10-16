"""Mini pannello sempre in primo piano con i pulsanti di controllo.

Non prende il focus quando lo clicchi (WS_EX_NOACTIVATE), così il gioco resta
la finestra attiva."""
import ctypes
import io
import logging
import tkinter as tk
from tkinter import font as tkfont

from PIL import Image, ImageDraw, ImageTk

from . import theme
from .i18n import t

log = logging.getLogger(__name__)

ORDER = ["previous", "play", "pause", "next"]
# Glifi di Segoe Fluent Icons / Segoe MDL2 Assets (font di sistema di Windows).
GLYPHS = {
    "previous": "", "play": "", "pause": "", "next": "",
    "volume_down": "", "volume_up": "", "music": "",
}
FALLBACK = {
    "previous": "|◀", "play": "▶", "pause": "❚❚", "next": "▶|",
    "volume_down": "−", "volume_up": "+", "music": "♪",
}

# Dimensioni in px a 100% di scala.
ART_SIZE = 96
ART_RADIUS = 10
CONTENT_WIDTH = 262
VOLUME_BAR_WIDTH = 150

# Contorno di 1 px attorno ai testi quando lo sfondo è trasparente.
OUTLINE_OFFSETS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 76, 77, 78, 79

user32 = ctypes.windll.user32


def _rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kw)


class _OutlinedText:
    """Testo su Canvas con un contorno che si può mostrare o nascondere."""

    def __init__(self, canvas, x, y, **kw):
        self._canvas = canvas
        self._outline = [canvas.create_text(x + dx, y + dy, **kw) for dx, dy in OUTLINE_OFFSETS]
        self._main = canvas.create_text(x, y, **kw)

    def set_text(self, text):
        for item in (*self._outline, self._main):
            self._canvas.itemconfigure(item, text=text)

    def style(self, fg, outline_color, outlined):
        self._canvas.itemconfigure(self._main, fill=fg)
        for item in self._outline:
            self._canvas.itemconfigure(item, fill=outline_color, state="normal" if outlined else "hidden")


class TextLine(tk.Canvas):
    """Testo a larghezza fissa: una riga accorciata con "…" se non ci sta,
    oppure (lines > 1) testo che va a capo."""

    def __init__(self, parent, font, width, anchor="center", text="", lines=1):
        self._font = tkfont.Font(parent, font=font)
        height = self._font.metrics("linespace") * lines + 2
        super().__init__(parent, width=width, height=height, highlightthickness=0, bd=0)
        self._width = width
        self._wrap = lines > 1
        x = {"center": width / 2, "w": 1, "e": width - 1}[anchor]
        wrap = {"width": width - 2, "justify": "left"} if self._wrap else {}
        self._text = _OutlinedText(self, x, height / 2, font=font, anchor=anchor, **wrap)
        self.set_text(text)

    def set_text(self, text):
        limit = self._width - 2
        if not self._wrap and self._font.measure(text) > limit:
            while text and self._font.measure(text + "…") > limit:
                text = text[:-1]
            text = text.rstrip() + "…"
        self._text.set_text(text)

    def apply_theme(self, pal, fg, outlined):
        self.configure(bg=pal.bg)
        self._text.style(fg, pal.outline, outlined)


class IconButton(tk.Canvas):
    """Pulsante piatto con sfondo arrotondato al passaggio del mouse, stile Windows 11."""

    def __init__(self, parent, glyph, font, size, command, radius=6):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self._size = size
        self._pal = None
        self._outlined = False
        self._inside = False
        self._pressed = False
        self._shape = _rounded_rect(self, 1, 1, size - 1, size - 1, radius, fill="", outline="")
        self._glyph = _OutlinedText(self, size / 2, size / 2, text=glyph, font=font)
        self.bind("<Enter>", lambda e: self._set(inside=True))
        self.bind("<Leave>", lambda e: self._set(inside=False))
        self.bind("<ButtonPress-1>", lambda e: self._set(pressed=True))
        self.bind("<ButtonRelease-1>", self._release)

    def apply_theme(self, pal, outlined):
        self._pal = pal
        self._outlined = outlined
        self.configure(bg=pal.bg)
        self.set_fg(pal.fg)
        self._redraw()

    def set_fg(self, color):
        self._glyph.style(color, self._pal.outline, self._outlined)

    def _set(self, inside=None, pressed=None):
        if inside is not None:
            self._inside = inside
        if pressed is not None:
            self._pressed = pressed
        self._redraw()

    def _release(self, event):
        clicked = self._pressed and 0 <= event.x < self._size and 0 <= event.y < self._size
        self._set(pressed=False)
        if clicked:
            self._command()

    def _redraw(self):
        if self._pal is None:
            return
        if self._inside and self._pressed:
            fill = self._pal.press
        elif self._inside:
            fill = self._pal.hover
        else:
            fill = ""
        self.itemconfigure(self._shape, fill=fill)


class VolumeBar(tk.Canvas):
    HEIGHT = 16
    THICKNESS = 4

    def __init__(self, parent, width):
        super().__init__(parent, width=width, height=self.HEIGHT, highlightthickness=0, bd=0)
        self._width = width
        y, pad = self.HEIGHT / 2, self.THICKNESS
        self._track = self.create_line(pad, y, width - pad, y, width=self.THICKNESS, capstyle="round")
        self._fill = self.create_line(pad, y, pad, y, width=self.THICKNESS, capstyle="round")

    def apply_theme(self, pal):
        self.configure(bg=pal.bg)
        self.itemconfigure(self._track, fill=pal.track)
        self.itemconfigure(self._fill, fill=pal.accent)

    def set(self, value):
        y, pad = self.HEIGHT / 2, self.THICKNESS
        end = pad + (self._width - 2 * pad) * (value or 0)
        self.coords(self._fill, pad, y, end, y)
        self.itemconfigure(self._fill, state="normal" if value else "hidden")


class Overlay:
    def __init__(self, root, on_action, on_moved):
        self._on_moved = on_moved
        self._hwnd = None
        self._drag = None
        self._pal = None
        self._status = None
        self._art_bytes = None
        self._art_photo = None  # va tenuto in vita, altrimenti Tk mostra un riquadro vuoto
        self._transparent = False
        self.visible = False

        win = self.win = tk.Toplevel(root)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)

        # 1.333 = scala di Tk a 96 DPI (100%)
        scale = float(root.tk.call("tk", "scaling")) / (96 / 72)
        px = lambda v: round(v * scale)  # noqa: E731

        icons = theme.font_family(root, "Segoe Fluent Icons", theme.font_family(root, "Segoe MDL2 Assets", ""))
        glyphs = GLYPHS if icons else FALLBACK
        icon_font = (lambda size: (icons, size)) if icons else (lambda size: ("Segoe UI", size, "bold"))
        text = theme.font_family(root, "Segoe UI Variable Text")
        strong = theme.font_family(root, "Segoe UI Variable Text Semibold", "Segoe UI Semibold")
        small = theme.font_family(root, "Segoe UI Variable Small")

        body = tk.Frame(win)
        body.pack(fill="both", expand=True, padx=px(14), pady=(px(10), px(12)))

        header = tk.Frame(body)
        header.pack(fill="x")
        self._logo = TextLine(header, icon_font(10), px(18), anchor="w", text=glyphs["music"])
        self._logo.pack(side="left")
        self._source = TextLine(header, (small, 9), px(80), anchor="w", text="Spotify")
        self._source.pack(side="left", padx=(px(4), 0))

        self._art_size = px(ART_SIZE)
        self._music_glyph = glyphs["music"]
        self._music_font = icon_font(20)
        self._art = tk.Canvas(body, width=self._art_size, height=self._art_size, highlightthickness=0, bd=0)
        self._art.pack(pady=(px(8), 0))
        self._title = TextLine(body, (strong, 12), px(CONTENT_WIDTH), text="Spotify")
        self._title.pack(pady=(px(8), 0))
        self._artist = TextLine(body, (text, 10), px(CONTENT_WIDTH))
        self._artist.pack()

        controls = tk.Frame(body)
        controls.pack(pady=(px(8), px(4)))
        self._buttons = {}
        for action in ORDER:
            button = IconButton(controls, glyphs[action], icon_font(16), px(44),
                                lambda a=action: on_action(a), radius=px(8))
            button.pack(side="left", padx=px(3))
            self._buttons[action] = button

        volume = tk.Frame(body)
        volume.pack(fill="x")
        self._vol_down = IconButton(volume, glyphs["volume_down"], icon_font(11), px(30),
                                    lambda: on_action("volume_down"))
        self._vol_down.pack(side="left")
        self._bar = VolumeBar(volume, px(VOLUME_BAR_WIDTH))
        self._bar.pack(side="left", padx=px(4))
        self._vol_up = IconButton(volume, glyphs["volume_up"], icon_font(11), px(30),
                                  lambda: on_action("volume_up"))
        self._vol_up.pack(side="left")
        self._percent = TextLine(volume, (small, 9), px(44), anchor="e", text="—")
        self._percent.pack(side="right")

        self._message = TextLine(body, (small, 9), px(CONTENT_WIDTH), anchor="w", lines=2)

        self._frames = [body, header, controls, volume]
        self._icon_buttons = [self._vol_down, self._vol_up, *self._buttons.values()]

        # Non su `win`: i binding della toplevel valgono anche per tutti i figli.
        for widget in (body, header, self._art, self._logo, self._source, self._title, self._artist):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<ButtonRelease-1>", self._drag_end)

    def apply_theme(self, pal):
        self._pal = pal
        outlined = self._transparent
        self.win.configure(bg=pal.bg)
        for frame in self._frames:
            frame.configure(bg=pal.bg)
        self._logo.apply_theme(pal, pal.accent, outlined)
        self._title.apply_theme(pal, pal.fg, outlined)
        for line in (self._source, self._artist, self._percent):
            line.apply_theme(pal, pal.muted, outlined)
        self._message.apply_theme(pal, pal.warn, outlined)
        for button in self._icon_buttons:
            button.apply_theme(pal, outlined)
        self._bar.apply_theme(pal)
        self._render_art()
        self._apply_transparency()
        if self._status:
            self.update_status(self._status)

    def set_appearance(self, transparent_bg, opacity):
        """transparent_bg: lo sfondo sparisce, restano copertina, testi e pulsanti
        (con un contorno per leggerli su qualsiasi sfondo).
        opacity: 30-100, vale per tutto l'overlay."""
        self._transparent = transparent_bg
        self.win.attributes("-alpha", opacity / 100)
        self.apply_theme(self._pal)

    def _apply_transparency(self):
        # Il colore dello sfondo diventa invisibile (e lascia passare i clic).
        self.win.attributes("-transparentcolor", self._pal.bg if self._transparent else "")
        if self._hwnd:
            theme.style_popup(self._hwnd, None if self._transparent else self._pal.border)

    def show(self, pos=None):
        win = self.win
        win.update_idletasks()
        x, y = pos if pos else (win.winfo_screenwidth() - win.winfo_reqwidth() - 24, 24)
        x, y = self._clamp(x, y)
        win.geometry(f"+{x}+{y}")
        win.deiconify()
        if self._hwnd is None:
            self._hwnd = int(win.wm_frame(), 16)
            style = user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
            self._apply_transparency()
        win.attributes("-topmost", True)
        win.lift()
        self.visible = True

    def hide(self):
        self.win.withdraw()
        self.visible = False

    def pointer_inside(self):
        if not self.visible:
            return False
        x, y = self.win.winfo_pointerxy()
        left, top = self.win.winfo_rootx(), self.win.winfo_rooty()
        return left <= x < left + self.win.winfo_width() and top <= y < top + self.win.winfo_height()

    def update_status(self, status):
        self._status = status
        pal = self._pal
        art = status.art if status.running else None
        if art != self._art_bytes:
            self._art_bytes = art
            self._render_art()
        if status.running:
            self._title.set_text(status.title or "Spotify")
            self._artist.set_text(status.artist)
        else:
            self._title.set_text(t("msg.spotify_closed"))
            self._artist.set_text(t("msg.open_spotify"))
        self._buttons["play"].set_fg(pal.accent if status.playing else pal.fg)
        self._buttons["pause"].set_fg(pal.accent if status.running and not status.playing else pal.fg)

        self._bar.set(status.volume)
        self._percent.set_text("—" if status.volume is None else f"{round(status.volume * 100)}%")

        if status.message:
            self._message.set_text(t(f"msg.{status.message}"))
            self._message.pack(pady=(6, 0))
        else:
            self._message.pack_forget()

    def _render_art(self):
        canvas, size, pal = self._art, self._art_size, self._pal
        canvas.delete("all")
        canvas.configure(bg=pal.bg)
        cover = None
        if self._art_bytes:
            try:
                cover = Image.open(io.BytesIO(self._art_bytes)).convert("RGB")
            except OSError:
                log.warning("Copertina non leggibile")
        if cover is None:
            _rounded_rect(canvas, 0, 0, size, size, ART_RADIUS, fill=pal.hover, outline="")
            canvas.create_text(size / 2, size / 2, text=self._music_glyph, font=self._music_font, fill=pal.muted)
            self._art_photo = None
            return
        # Angoli arrotondati: maschera disegnata a 4x e ridotta, per bordi lisci.
        big = size * 4
        mask = Image.new("L", (big, big), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), ART_RADIUS * 4, fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        framed = Image.new("RGB", (size, size), pal.bg)
        framed.paste(cover.resize((size, size), Image.LANCZOS), (0, 0), mask)
        self._art_photo = ImageTk.PhotoImage(framed, master=canvas)
        canvas.create_image(0, 0, image=self._art_photo, anchor="nw")

    def _clamp(self, x, y):
        # Schermo virtuale: comprende tutti i monitor, anche a coordinate negative.
        left, top = user32.GetSystemMetrics(SM_XVIRTUALSCREEN), user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        right = left + user32.GetSystemMetrics(SM_CXVIRTUALSCREEN) - self.win.winfo_reqwidth()
        bottom = top + user32.GetSystemMetrics(SM_CYVIRTUALSCREEN) - self.win.winfo_reqheight()
        return min(max(int(x), left), right), min(max(int(y), top), bottom)

    def _drag_start(self, event):
        self._drag = (event.x_root - self.win.winfo_x(), event.y_root - self.win.winfo_y())

    def _drag_move(self, event):
        if self._drag:
            dx, dy = self._drag
            self.win.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _drag_end(self, event):
        if self._drag:
            self._drag = None
            self._on_moved((self.win.winfo_x(), self.win.winfo_y()))
