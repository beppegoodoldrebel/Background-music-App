import ctypes
import logging

from . import config, i18n

ERROR_ALREADY_EXISTS = 183


def main():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    mutex = kernel32.CreateMutexW(None, False, "MusicOverlay.SingleInstance")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        i18n.set_language(config.load()["language"])
        ctypes.windll.user32.MessageBoxW(None, i18n.t("app.already_running"), "Music Overlay", 0x40)
        return

    # Nessun file di log: i messaggi di log nel codice vengono scartati.
    logging.disable(logging.CRITICAL)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # testo nitido su schermi ad alta risoluzione

    from .app import App

    try:
        App().run()
    finally:
        kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
