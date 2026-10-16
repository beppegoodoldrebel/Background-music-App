import ctypes
import logging
import threading

import psutil

log = logging.getLogger(__name__)

QUNS_RUNNING_D3D_FULL_SCREEN = 3


def exclusive_fullscreen_active():
    """True se un'app Direct3D è in fullscreen esclusivo: lì l'overlay non si
    vedrebbe e mostrarlo può far minimizzare il gioco."""
    state = ctypes.c_int()
    if ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state)) != 0:
        return False
    return state.value == QUNS_RUNNING_D3D_FULL_SCREEN


def running_process_names():
    return {p.info["name"].lower() for p in psutil.process_iter(["name"]) if p.info["name"]}


class ProcessWatcher(threading.Thread):
    """Controlla periodicamente quali delle app associate sono aperte e chiama
    on_change(lista) quando l'insieme cambia."""

    def __init__(self, get_targets, on_change, interval=2.0):
        super().__init__(name="watcher", daemon=True)
        self._get_targets = get_targets
        self._on_change = on_change
        self._interval = interval
        self._wake = threading.Event()
        self._stopped = False
        self._last = None

    def poke(self):
        """Forza una nuova notifica (es. dopo aver cambiato le app associate)."""
        self._last = None
        self._wake.set()

    def stop(self):
        self._stopped = True
        self._wake.set()

    def run(self):
        while not self._stopped:
            try:
                targets = {t.lower() for t in self._get_targets()}
                matched = sorted(targets & running_process_names()) if targets else []
            except Exception:
                log.exception("Controllo dei processi fallito")
                matched = self._last or []
            if matched != self._last:
                self._last = matched
                self._on_change(matched)
            self._wake.wait(self._interval)
            self._wake.clear()
