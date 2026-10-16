import logging
import queue
import tkinter as tk

import keyboard
import pystray
from PIL import ImageTk

from . import appinfo, config, i18n, icon, theme
from .i18n import t
from .controller import ControllerManager
from .hotkeys import HotkeyManager
from .overlay import Overlay
from .settings_window import SettingsWindow
from .spotify import SpotifyController
from .watcher import ProcessWatcher, exclusive_fullscreen_active

log = logging.getLogger(__name__)

POLL_MS = 2000  # stato di Spotify


TRAY_ICON_SIZE = 64      # Windows la riduce alla misura dell'area di notifica
WINDOW_ICON_SIZES = (16, 32, 48, 256)


def _tray_image(active):
    """Verde con i controlli attivi, grigia in attesa."""
    return icon.render(TRAY_ICON_SIZE, active)


class App:
    """Tkinter gira sul thread principale; tastiera, tray, watcher e Spotify su
    thread propri. Tutto ciò che tocca la UI passa da call_in_ui()."""

    def __init__(self):
        self._first_run = not config.CONFIG_PATH.exists()
        self.cfg = config.load()
        i18n.set_language(self.cfg["language"])
        self.active = False
        self._matched = []
        self._overlay_dismissed = False
        self._hide_job = None
        self._last_track = None
        self._exclusive = False                 # un gioco è in fullscreen esclusivo
        self._restore_after_exclusive = False   # l'overlay era visibile prima
        self._settings = None
        self._ui = queue.Queue()

        self.root = tk.Tk()
        self.root.withdraw()
        # Più misure: Windows sceglie quella giusta per barra del titolo e Alt+Tab.
        self._window_icons = [ImageTk.PhotoImage(icon.render(size), master=self.root)
                              for size in sorted(WINDOW_ICON_SIZES, reverse=True)]
        self.root.iconphoto(True, *self._window_icons)  # vale per tutte le finestre
        # Il tema di Windows viene letto solo all'avvio.
        self.pal = theme.apply(self.root, theme.system_is_dark())

        self.spotify = SpotifyController(lambda: self.cfg["volume_step"])
        self.hotkeys = HotkeyManager(self._on_hotkey)
        self.controller = ControllerManager(self._on_hotkey)
        self.overlay = Overlay(self.root, self.trigger, self._overlay_moved)
        self.overlay.apply_theme(self.pal)
        self.overlay.set_appearance(self.cfg["transparent_bg"], self.cfg["overlay_opacity"])
        self.watcher = ProcessWatcher(lambda: list(self.cfg["targets"]),
                                      lambda matched: self.call_in_ui(self._targets_changed, matched))
        # Testi del menu come funzioni: seguono la lingua anche se cambia.
        self.tray = pystray.Icon(
            "MusicOverlay",
            _tray_image(False),
            t("tray.idle"),
            menu=pystray.Menu(
                pystray.MenuItem(lambda item: t("tray.settings"), lambda: self.call_in_ui(self.open_settings),
                                 default=True),
                pystray.MenuItem(lambda item: t("tray.show_overlay"), lambda: self.call_in_ui(self._toggle_overlay),
                                 checked=lambda item: self.overlay.visible),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda item: t("tray.quit"), lambda: self.call_in_ui(self.quit)),
            ),
        )

    def run(self):
        self.tray.run_detached()
        self.watcher.start()
        self.controller.start()
        self.root.after(50, self._pump)
        self.root.after(POLL_MS, self._poll)
        if self._first_run:
            config.save(self.cfg)
            self.open_settings()
        self.root.mainloop()

    def call_in_ui(self, fn, *args):
        self._ui.put((fn, args))

    def _pump(self):
        while not self._ui.empty():
            fn, args = self._ui.get_nowait()
            try:
                fn(*args)
            except Exception:
                log.exception("Errore nella UI")
        self.root.after(50, self._pump)

    # --- Azioni --------------------------------------------------------------
    def trigger(self, action):
        """Punto d'ingresso unico per tutte le sorgenti di input."""
        self.spotify.submit(action, self._status_ready)

    def _on_hotkey(self, action):
        """Da tastiera o controller (chiamato dai loro thread)."""
        self.trigger(action)
        # Con l'overlay a scomparsa, un tasto rapido lo fa ricomparire per un attimo.
        self.call_in_ui(self._peek_overlay)

    def _status_ready(self, status):
        self.call_in_ui(self._on_status, status)

    def _on_status(self, status):
        self.overlay.update_status(status)
        track = (status.artist, status.title) if status.running and status.title else None
        if track and track != self._last_track:
            self._peek_overlay()
        self._last_track = track

    def _poll(self):
        # Anche a overlay nascosto, per accorgersi quando inizia una nuova canzone.
        if self.active or self.overlay.visible:
            self.spotify.submit(None, self._status_ready)
        self._check_exclusive_fullscreen()
        self.root.after(POLL_MS, self._poll)

    # --- Fullscreen esclusivo ------------------------------------------------
    def _exclusive_fullscreen(self):
        return self.cfg["hide_on_exclusive"] and exclusive_fullscreen_active()

    def _check_exclusive_fullscreen(self):
        """Nasconde l'overlay quando un gioco entra in fullscreen esclusivo e lo
        rimette com'era quando ne esce."""
        exclusive = self._exclusive_fullscreen()
        if exclusive == self._exclusive:
            return
        self._exclusive = exclusive
        log.info("Fullscreen esclusivo: %s", exclusive)
        if exclusive:
            self._restore_after_exclusive = self.overlay.visible
            self._hide_overlay()
        elif self._restore_after_exclusive:
            self._restore_after_exclusive = False
            self._show_overlay()

    # --- Attivazione ---------------------------------------------------------
    def _targets_changed(self, matched):
        if self._matched and not matched and self.cfg["pause_on_exit"]:
            log.info("App associate chiuse: pausa")
            self.trigger("pause")
        self._matched = matched
        self._remember_paths(matched)
        self._refresh()

    def _remember_paths(self, matched):
        """Salva il percorso degli exe aggiunti senza (servono per nome e icona)."""
        paths = self.cfg["target_paths"]
        found = {exe: appinfo.find_running_path(exe) for exe in matched if exe not in paths}
        found = {exe: path for exe, path in found.items() if path}
        if found:
            paths.update(found)
            config.save(self.cfg)

    def _refresh(self):
        active = self.cfg["always_active"] or bool(self._matched)
        if active and not self.active:
            self._overlay_dismissed = False
        self.active = active

        bindings, preset = self._active_preset()
        if active and self._settings is None:
            self.hotkeys.apply(bindings["hotkeys"])
            if self.cfg["controller_enabled"]:
                self.controller.apply(bindings["controller"])
            else:
                self.controller.clear()
        else:
            self.hotkeys.clear()
            self.controller.clear()

        if active and self.cfg["show_overlay"] and not self._overlay_dismissed:
            self._show_overlay()
        else:
            self._hide_overlay()

        if active:
            reason = ", ".join(self._matched) if self._matched else t("tray.always_active")
            self.tray.title = t("tray.active", reason=reason, preset=preset or t("tray.general"))
        else:
            self.tray.title = t("tray.idle")
        self.tray.icon = _tray_image(active)
        log.info("Attivo=%s app=%s preset=%s", active, self._matched, preset or "generale")

    def _active_preset(self):
        """Il preset del primo exe aperto (nell'ordine della lista) che ne ha uno,
        altrimenti quello generale. Restituisce (combinazioni, nome exe o None)."""
        presets = self.cfg["presets"]
        for exe in self.cfg["targets"]:
            if exe in self._matched and exe in presets:
                return presets[exe], exe
        return {kind: self.cfg[kind] for kind in config.BINDING_KINDS}, None

    # --- Overlay -------------------------------------------------------------
    def _show_overlay(self):
        if self._exclusive_fullscreen():
            # Non si vedrebbe e potrebbe far minimizzare il gioco.
            return
        if not self.overlay.visible:
            self.overlay.show(self.cfg["overlay_pos"])
            self.trigger(None)
            self.tray.update_menu()
        if self.cfg["auto_hide"] and self._settings is None:
            self._schedule_hide()

    def _hide_overlay(self):
        self._cancel_hide()
        if self.overlay.visible:
            self.overlay.hide()
            self.tray.update_menu()

    def _peek_overlay(self):
        if self.active and self.cfg["show_overlay"] and self.cfg["auto_hide"] and not self._overlay_dismissed:
            self._show_overlay()

    def _schedule_hide(self):
        self._cancel_hide()
        self._hide_job = self.root.after(self.cfg["auto_hide_seconds"] * 1000, self._auto_hide)

    def _cancel_hide(self):
        if self._hide_job:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None

    def _auto_hide(self):
        self._hide_job = None
        if not self.cfg["auto_hide"] or self._settings is not None:
            return
        if self.overlay.pointer_inside():
            # Non sparire mentre l'utente ci sta usando il mouse.
            self._hide_job = self.root.after(1000, self._auto_hide)
        else:
            self._hide_overlay()

    def _toggle_overlay(self):
        if self.overlay.visible:
            self._overlay_closed()
        else:
            self._overlay_dismissed = False
            self._show_overlay()

    def _overlay_closed(self):
        # Dal menu dell'icona. A scomparsa lo nasconde fino alla prossima canzone;
        # altrimenti resta chiuso fino alla prossima attivazione.
        if not self.cfg["auto_hide"]:
            self._overlay_dismissed = True
        self._hide_overlay()

    def _overlay_moved(self, pos):
        self.cfg["overlay_pos"] = list(pos)
        config.save(self.cfg)

    # --- Impostazioni --------------------------------------------------------
    def open_settings(self):
        if self._settings:
            self._settings.lift()
            return
        # Altrimenti scatterebbero mentre registri tasti e pulsanti.
        self.hotkeys.clear()
        self.controller.clear()
        self._settings = SettingsWindow(self.root, self.cfg, self.pal, self._settings_saved,
                                        self._settings_closed, self._preview_appearance, self.call_in_ui)
        # Overlay sempre visibile con le impostazioni aperte, per vedere l'anteprima.
        self._cancel_hide()
        self._show_overlay()

    def _preview_appearance(self, transparent_bg, opacity):
        self.overlay.set_appearance(transparent_bg, opacity)

    def _settings_saved(self, cfg):
        cfg["overlay_pos"] = self.cfg["overlay_pos"]
        # Percorsi trovati mentre le impostazioni erano aperte.
        cfg["target_paths"] = {exe: path for exe, path in {**self.cfg["target_paths"], **cfg["target_paths"]}.items()
                               if exe in cfg["targets"]}
        self.cfg = cfg
        config.save(cfg)
        i18n.set_language(cfg["language"])
        self.tray.update_menu()
        if self.overlay.visible:
            self.trigger(None)  # ridisegna i testi dell'overlay nella nuova lingua
        self.watcher.poke()

    def _settings_closed(self):
        self._settings = None
        # Dopo «Annulla» toglie l'anteprima; dopo «Salva» applica i nuovi valori.
        self.overlay.set_appearance(self.cfg["transparent_bg"], self.cfg["overlay_opacity"])
        self._refresh()

    def quit(self):
        if self.cfg["pause_on_exit"]:
            log.info("Chiusura di Music Overlay: pausa")
            self.spotify.run_blocking("pause")
        self.hotkeys.clear()
        keyboard.unhook_all()
        self.controller.stop()
        self.watcher.stop()
        self.tray.stop()
        self.root.quit()
