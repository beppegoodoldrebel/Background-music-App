"""Icona dell'app: un controller bianco con una nota al posto della croce.

Disegnata con Pillow su una griglia di 64 unità, a risoluzione 4x e poi
ridotta, per avere bordi lisci a ogni dimensione.
"""
from PIL import Image, ImageChops, ImageDraw

SUPERSAMPLE = 4
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]

# Fondo: gradiente diagonale. Grigio quando l'app è in attesa.
ACTIVE_COLORS = ("#34d399", "#15803d")
IDLE_COLORS = ("#9ca3af", "#4b5563")

# Contorno del controller (coordinate su 64): segmenti dritti e curve di Bézier cubiche.
_PAD_START = (12, 30)
_PAD_PATH = [
    ((12, 23.9), (16.9, 19), (23, 19)),
    ((41, 19),),
    ((47.1, 19), (52, 23.9), (52, 30)),
    ((52, 35.5),),
    ((52, 43), (49, 49), (45, 49)),
    ((41.8, 49), (39.8, 46.3), (38, 43)),
    ((26, 43),),
    ((24.2, 46.3), (22.2, 49), (19, 49)),
    ((15, 49), (12, 43), (12, 35.5)),
]
# Bandierina della nota.
_FLAG_START = (25.8, 24)
_FLAG_PATH = [
    ((28.4, 24.6), (30.4, 26.2), (30.8, 28.6)),
    ((29.4, 27.5), (27.8, 27.0), (25.8, 26.9)),
]


def _hex(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _outline(start, segments, steps=24):
    """Punti di un percorso fatto di linee e curve di Bézier cubiche."""
    points = [start]
    for segment in segments:
        if len(segment) == 1:
            points.append(segment[0])
            continue
        p0, (c1, c2, p3) = points[-1], segment
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            points.append(tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                                for a, b, c, d in zip(p0, c1, c2, p3)))
    return points


def render(size, active=True):
    """Icona RGBA di size x size pixel."""
    big = size * SUPERSAMPLE
    k = big / 64  # unità della griglia -> pixel
    scale = lambda points: [(x * k, y * k) for x, y in points]  # noqa: E731
    box = lambda x1, y1, x2, y2: (x1 * k, y1 * k, x2 * k, y2 * k)  # noqa: E731

    start, end = map(_hex, ACTIVE_COLORS if active else IDLE_COLORS)
    dark = end

    # Gradiente diagonale (media di uno verticale e uno orizzontale), ritagliato
    # dal quadrato arrotondato.
    vertical = Image.linear_gradient("L").resize((big, big))
    gradient = ImageChops.add(vertical, vertical.transpose(Image.Transpose.ROTATE_90).transpose(
        Image.Transpose.FLIP_TOP_BOTTOM), scale=2)
    background = Image.composite(Image.new("RGB", (big, big), end), Image.new("RGB", (big, big), start), gradient)
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box(2, 2, 62, 62), radius=15 * k, fill=255)
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    image.paste(background, (0, 0), mask)

    draw = ImageDraw.Draw(image)
    draw.polygon(scale(_outline(_PAD_START, _PAD_PATH)), fill="white")
    # Nota musicale: testa, gambo e bandierina.
    draw.ellipse(box(21.5 - 3.6, 36 - 3.6, 21.5 + 3.6, 36 + 3.6), fill=dark)
    draw.rounded_rectangle(box(23.6, 24, 25.8, 36.4), radius=1 * k, fill=dark)
    draw.polygon(scale(_outline(_FLAG_START, _FLAG_PATH)), fill=dark)
    # Due pulsanti a destra.
    for cx, cy in ((41, 29), (46, 34)):
        draw.ellipse(box(cx - 2.6, cy - 2.6, cx + 2.6, cy + 2.6), fill=dark)

    return image.resize((size, size), Image.LANCZOS)


def save_ico(path):
    """File .ico con tutte le dimensioni usate da Windows (per exe o installer)."""
    largest = render(ICO_SIZES[-1])
    largest.save(path, format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                 append_images=[render(s) for s in ICO_SIZES[:-1]])
