import copy
import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "MusicOverlay"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    "language": "en",
    "targets": [],
    "target_paths": {},  # exe -> percorso completo, per mostrare nome e icona
    "always_active": False,
    "show_overlay": True,
    "overlay_pos": None,
    "transparent_bg": False,
    "overlay_opacity": 97,
    "auto_hide": False,
    "auto_hide_seconds": 5,
    "pause_on_exit": False,
    "hide_on_exclusive": True,
    "volume_step": 5,
    "hotkeys": {
        "volume_up": "ctrl+alt+up",
        "volume_down": "ctrl+alt+down",
        "next": "ctrl+alt+right",
        "previous": "ctrl+alt+left",
        "pause": "ctrl+alt+space",
        "play": "ctrl+alt+enter",
        "shuffle": "ctrl+alt+s",
    },
    "controller_enabled": True,
    "controller": {
        "volume_up": "view+up",
        "volume_down": "view+down",
        "next": "view+right",
        "previous": "view+left",
        "pause": "view+x",
        "play": "view+a",
        "shuffle": "view+y",
    },
    # "hotkeys" e "controller" qui sopra sono il preset generale. Qui i preset
    # per exe: {"gioco.exe": {"hotkeys": {...}, "controller": {...}}}
    "presets": {},
}
BINDING_KINDS = ("hotkeys", "controller")


def load():
    cfg = copy.deepcopy(DEFAULTS)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    for key in cfg:
        if key not in data:
            continue
        if key in BINDING_KINDS:  # azione -> combinazione: tiene le azioni nuove
            cfg[key].update({a: c for a, c in data[key].items() if a in cfg[key]})
        else:
            cfg[key] = data[key]
    return cfg


def save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_PATH)
