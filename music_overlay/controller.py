"""Controller e periferiche di gioco.

- Controller Xbox e compatibili: XInput. Pulsanti con nomi fissi ("view", "a"…),
  validi per qualsiasi controller Xbox collegato.
- Tutto il resto (button box, cambi, volanti, joystick…): API joystick di
  Windows (winmm), cioè gli stessi dispositivi di "Controller di gioco" nel
  Pannello di controllo. Pulsanti legati al modello: "36e6_8001.b5" =
  pulsante 5 del dispositivo VID 36E6 / PID 8001.

Nessuna libreria aggiuntiva: entrambe le API fanno parte di Windows.

Un'azione scatta quando tutti i pulsanti della combinazione sono premuti e uno
di essi è appena stato premuto. Così funzionano anche i dispositivi con
pulsanti sempre "premuti" (marcia inserita, interruttori a levetta).
"""
import ctypes
import logging
import re
import threading
import time
import winreg
from ctypes import wintypes
from dataclasses import dataclass

from .i18n import t

log = logging.getLogger(__name__)

# --- XInput -------------------------------------------------------------------

# Ordine usato per salvare e mostrare le combinazioni.
BUTTONS = {
    "view": 0x0020, "menu": 0x0010,
    "lb": 0x0100, "rb": 0x0200, "lt": None, "rt": None,
    "a": 0x1000, "b": 0x2000, "x": 0x4000, "y": 0x8000,
    "up": 0x0001, "down": 0x0002, "left": 0x0004, "right": 0x0008,
    "ls": 0x0040, "rs": 0x0080,
}
LABELS = {
    "view": "View", "menu": "Menu", "lb": "LB", "rb": "RB", "lt": "LT", "rt": "RT",
    "a": "A", "b": "B", "x": "X", "y": "Y", "ls": "L3", "rs": "R3",
}
ARROWS = {"up": "↑", "down": "↓", "left": "←", "right": "→"}  # croce, Xbox e altri dispositivi
TRIGGER_THRESHOLD = 100  # su 255: evita attivazioni sfiorando i grilletti


class _Gamepad(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),  # wintypes.BYTE è con segno
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", wintypes.SHORT),
        ("sThumbLY", wintypes.SHORT),
        ("sThumbRX", wintypes.SHORT),
        ("sThumbRY", wintypes.SHORT),
    ]


class _XInputState(ctypes.Structure):
    _fields_ = [("dwPacketNumber", wintypes.DWORD), ("Gamepad", _Gamepad)]


def _load_xinput():
    for name in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            return ctypes.WinDLL(name)
        except OSError:
            continue
    log.warning("XInput non disponibile")
    return None


_xinput = _load_xinput()


def _read_xinput(slot):
    """Pulsanti premuti sul controller Xbox `slot` (0-3), o None se non collegato."""
    state = _XInputState()
    if _xinput is None or _xinput.XInputGetState(slot, ctypes.byref(state)) != 0:
        return None
    pad = state.Gamepad
    pressed = {name for name, mask in BUTTONS.items() if mask and pad.wButtons & mask}
    if pad.bLeftTrigger >= TRIGGER_THRESHOLD:
        pressed.add("lt")
    if pad.bRightTrigger >= TRIGGER_THRESHOLD:
        pressed.add("rt")
    return frozenset(pressed)


# --- Joystick di Windows (winmm) ----------------------------------------------

MICROSOFT_VID = 0x045E  # controller Xbox: già letti da XInput
JOYCAPS_HASPOV = 0x10
JOY_RETURNPOV = 0x40
JOY_RETURNBUTTONS = 0x80
POV_CENTERED = 0xFFFF
POV_DIRECTIONS = {"up": 0, "right": 9000, "down": 18000, "left": 27000}  # centesimi di grado
JOY_TOKEN = re.compile(r"^([0-9a-f]{4}_[0-9a-f]{4})\.(?:b(\d{1,2})|pov_(up|down|left|right))$")
OEM_KEY = r"System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM"


class _JoyCaps(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("szPname", wintypes.WCHAR * 32),
        ("wXmin", wintypes.UINT), ("wXmax", wintypes.UINT), ("wYmin", wintypes.UINT),
        ("wYmax", wintypes.UINT), ("wZmin", wintypes.UINT), ("wZmax", wintypes.UINT),
        ("wNumButtons", wintypes.UINT), ("wPeriodMin", wintypes.UINT), ("wPeriodMax", wintypes.UINT),
        ("wRmin", wintypes.UINT), ("wRmax", wintypes.UINT), ("wUmin", wintypes.UINT),
        ("wUmax", wintypes.UINT), ("wVmin", wintypes.UINT), ("wVmax", wintypes.UINT),
        ("wCaps", wintypes.UINT), ("wMaxAxes", wintypes.UINT), ("wNumAxes", wintypes.UINT),
        ("wMaxButtons", wintypes.UINT), ("szRegKey", wintypes.WCHAR * 32),
        ("szOEMVxD", wintypes.WCHAR * 260),
    ]


class _JoyInfoEx(ctypes.Structure):
    _fields_ = [(name, wintypes.DWORD) for name in (
        "dwSize", "dwFlags", "dwXpos", "dwYpos", "dwZpos", "dwRpos", "dwUpos", "dwVpos",
        "dwButtons", "dwButtonNumber", "dwPOV", "dwReserved1", "dwReserved2")]


_winmm = ctypes.WinDLL("winmm")
_names = {}


def device_name(key):
    """Nome mostrato in "Controller di gioco" (es. "PXN-CB1"), dal registro."""
    vid, pid = key.upper().split("_")
    if key not in _names:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{OEM_KEY}\VID_{vid}&PID_{pid}") as k:
                _names[key] = winreg.QueryValueEx(k, "OEMName")[0].strip()
        except OSError:
            _names[key] = None
    return _names[key] or t("pad.unknown_device", id=f"{vid}:{pid}")


@dataclass(frozen=True)
class _Joystick:
    index: int
    key: str  # "vid_pid" in esadecimale minuscolo
    has_pov: bool


def _scan_joysticks():
    found = []
    for index in range(16):
        caps = _JoyCaps()
        if _winmm.joyGetDevCapsW(index, ctypes.byref(caps), ctypes.sizeof(caps)) != 0:
            continue
        if caps.wMid == MICROSOFT_VID:
            continue
        joystick = _Joystick(index, f"{caps.wMid:04x}_{caps.wPid:04x}", bool(caps.wCaps & JOYCAPS_HASPOV))
        if _read_joystick(joystick) is not None:
            found.append(joystick)
    return found


def _pov_near(angle, target):
    distance = abs(angle - target) % 36000
    return min(distance, 36000 - distance) <= 4500  # le diagonali valgono per due direzioni


def _read_joystick(joystick):
    info = _JoyInfoEx(dwSize=ctypes.sizeof(_JoyInfoEx), dwFlags=JOY_RETURNBUTTONS | JOY_RETURNPOV)
    if _winmm.joyGetPosEx(joystick.index, ctypes.byref(info)) != 0:
        return None
    pressed = {f"{joystick.key}.b{n + 1}" for n in range(32) if info.dwButtons & (1 << n)}
    if joystick.has_pov and info.dwPOV != POV_CENTERED:
        pressed.update(f"{joystick.key}.pov_{d}" for d, target in POV_DIRECTIONS.items()
                       if _pov_near(info.dwPOV, target))
    return frozenset(pressed)


# --- Lettura di tutti i dispositivi -------------------------------------------

RESCAN_INTERVAL = 2.0  # cercare dispositivi nuovi è lento: lo fa di rado
POLL_INTERVAL = 1 / 60


class _Devices:
    def __init__(self):
        self._xinput_slots = []
        self._joysticks = []
        self._next_scan = 0.0

    def read(self):
        now = time.monotonic()
        if now >= self._next_scan:
            self._xinput_slots = [s for s in range(4) if _read_xinput(s) is not None]
            self._joysticks = _scan_joysticks()
            self._next_scan = now + RESCAN_INTERVAL
        states = [_read_xinput(s) for s in self._xinput_slots]
        states += [_read_joystick(j) for j in self._joysticks]
        return frozenset().union(*(s for s in states if s))

    @property
    def any_connected(self):
        return bool(self._xinput_slots or self._joysticks)


def connected_devices():
    """Nomi dei dispositivi collegati, per l'interfaccia."""
    xbox = sum(_read_xinput(s) is not None for s in range(4))
    names = [t("pad.xbox")] * xbox
    names += [device_name(j.key) for j in _scan_joysticks()]
    return names


# --- Combinazioni -------------------------------------------------------------

def _valid_token(token):
    return token in BUTTONS or JOY_TOKEN.match(token) is not None


def parse_combo(text):
    parts = frozenset(p.strip() for p in text.lower().split("+") if p.strip())
    return parts if parts and all(map(_valid_token, parts)) else None


def combo_to_str(buttons):
    xbox = [b for b in BUTTONS if b in buttons]
    others = sorted(b for b in buttons if b not in BUTTONS)
    return "+".join(xbox + others)


def _token_label(token):
    if token in LABELS:
        return LABELS[token]
    if token in ARROWS:
        return t("pad.dpad", arrow=ARROWS[token])
    key, button, pov = JOY_TOKEN.match(token).groups()
    if button:
        return t("pad.device_button", device=device_name(key), n=button)
    return t("pad.device_dpad", device=device_name(key), arrow=ARROWS[pov])


def format_combo(text):
    """'view+up' -> 'View + D-pad ↑' (per l'interfaccia, nella lingua scelta)."""
    buttons = parse_combo(text) if text else None
    return " + ".join(_token_label(token) for token in combo_to_str(buttons).split("+")) if buttons else ""


def record(cancel, timeout=10.0):
    """Aspetta che l'utente prema e rilasci una combinazione. I pulsanti già
    premuti all'inizio (marcia inserita, levette) sono ignorati. Restituisce la
    stringa (es. 'view+up') o None se annullato o scaduto."""
    devices = _Devices()
    baseline = devices.read()
    end = time.monotonic() + timeout
    best = frozenset()
    while not cancel.is_set() and time.monotonic() < end:
        pressed = devices.read() - baseline
        if pressed:
            if len(pressed) >= len(best):
                best = pressed
        elif best:
            return combo_to_str(best)
        time.sleep(POLL_INTERVAL)
    return None


# --- Esecuzione delle azioni --------------------------------------------------

REPEAT_ACTIONS = {"volume_up", "volume_down"}
REPEAT_DELAY = 0.4
REPEAT_INTERVAL = 0.12


class ControllerManager(threading.Thread):
    def __init__(self, on_action):
        super().__init__(name="controller", daemon=True)
        self._on_action = on_action
        self._bindings = {}
        self._wake = threading.Event()
        self._stopped = False

    def apply(self, bindings):
        parsed = {a: parse_combo(c) for a, c in bindings.items() if c}
        self._bindings = {a: c for a, c in parsed.items() if c}
        self._wake.set()

    def clear(self):
        self._bindings = {}

    def stop(self):
        self._stopped = True
        self._wake.set()

    def run(self):
        devices = _Devices()
        previous = None  # None = prima lettura: nessuna pressione è "nuova"
        held = {}        # azione -> istante della prossima ripetizione (None = non ripete)
        while not self._stopped:
            bindings = self._bindings
            if not bindings:
                previous = None
                held.clear()
                self._wake.wait(0.5)
                self._wake.clear()
                continue

            now = time.monotonic()
            pressed = devices.read()
            if previous is None:
                previous = pressed

            satisfied = {a: c for a, c in bindings.items() if c <= pressed}
            # Se più combinazioni sono soddisfatte (es. "a" e "view+a"), vince la più specifica.
            winners = {a for a, c in satisfied.items() if not any(c < other for other in satisfied.values())}
            for action in list(held):
                if action not in winners:
                    del held[action]
            for action in winners:
                combo = bindings[action]
                if action not in held:
                    if combo <= previous:
                        held[action] = None  # era già premuta: non è una nuova pressione
                    else:
                        self._fire(action)
                        held[action] = now + REPEAT_DELAY
                elif held[action] is not None and action in REPEAT_ACTIONS and now >= held[action]:
                    self._fire(action)
                    held[action] = now + REPEAT_INTERVAL

            previous = pressed
            time.sleep(POLL_INTERVAL if devices.any_connected else 0.5)

    def _fire(self, action):
        try:
            self._on_action(action)
        except Exception:
            log.exception("Azione dal controller fallita: %s", action)
