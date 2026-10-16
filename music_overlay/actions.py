"""Azioni disponibili. Ogni sorgente di input (tastiera, overlay, controller)
invia una di queste chiavi a App.trigger()."""
from .i18n import t

ACTIONS = ("volume_up", "volume_down", "next", "previous", "pause", "play")


def action_label(action):
    return t(f"action.{action}")
