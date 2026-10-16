"""Tasti rapidi globali: funzionano anche quando in primo piano c'è un'altra app."""
import logging

import keyboard

log = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self, on_action):
        self._on_action = on_action
        self._handles = []

    def apply(self, hotkeys):
        self.clear()
        for action, combo in hotkeys.items():
            if not combo:
                continue
            try:
                self._handles.append(keyboard.add_hotkey(combo, self._on_action, args=(action,)))
            except ValueError:
                log.warning("Combinazione non valida per %s: %r", action, combo)

    def clear(self):
        for handle in self._handles:
            keyboard.remove_hotkey(handle)
        self._handles.clear()


def record():
    """Blocca finché l'utente non preme e rilascia una combinazione.
    Restituisce None se è stato premuto Esc."""
    combo = keyboard.read_hotkey(suppress=False)
    return None if combo in ("esc", "escape") else combo


def is_valid(combo):
    try:
        keyboard.parse_hotkey(combo)
    except ValueError:
        return False
    return True
