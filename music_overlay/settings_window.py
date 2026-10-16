import copy
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from . import appinfo, controller, hotkeys, theme
from .actions import ACTIONS, action_label
from .config import BINDING_KINDS
from .i18n import LANGUAGES, t

PAD_STATUS_MS = 1500
ICON_SIZE = 20  # px a 100% di scala
RECORDING_TEXT = {"hotkeys": "s.press_keys", "controller": "s.press_buttons"}


def _int_in_range(text, low, high, default):
    try:
        return min(high, max(low, int(text)))
    except ValueError:
        return default


def _section(parent, title, description):
    ttk.Label(parent, text=title, style="Section.TLabel").pack(anchor="w")
    ttk.Label(parent, text=description, style="Muted.TLabel").pack(anchor="w", pady=(0, 8))


def _duplicates(combos):
    used = [c for c in combos.values() if c]
    return sorted({c for c in used if used.count(c) > 1})


class SettingsWindow:
    def __init__(self, root, cfg, pal, on_save, on_close, on_preview, call_in_ui):
        self._cfg = copy.deepcopy(cfg)
        self._on_save = on_save
        self._on_close = on_close
        self._on_preview = on_preview  # (sfondo_trasparente, opacità): anteprima sull'overlay
        self._call_in_ui = call_in_ui
        self._recording = None
        self._cancel_recording = threading.Event()
        self._pal = pal

        # Preset: None = generale, altrimenti il nome dell'exe.
        # Valori grezzi ("ctrl+alt+up", "view+up"); i campi mostrano la versione leggibile.
        self._presets = {None: {kind: dict(self._cfg[kind]) for kind in BINDING_KINDS}}
        for exe, preset in self._cfg["presets"].items():
            self._presets[exe] = {kind: {a: preset.get(kind, {}).get(a, "") for a in ACTIONS}
                                  for kind in BINDING_KINDS}
        self._general_preset = t("s.preset_general")
        self._preset = tk.StringVar(value=self._general_preset)
        self._preset_bars = []    # (combobox, descrizione, «Crea», «Elimina») in ogni scheda
        self._edit_buttons = []   # «Registra» e «✕»: disattivati se l'exe usa il generale
        self._vars = {kind: {} for kind in BINDING_KINDS}
        self._preset_choices = {self._general_preset: None}  # testo nel selettore -> exe
        self._paths = dict(self._cfg["target_paths"])
        self._icons = {}  # PhotoImage delle icone: vanno tenute in vita

        win = self.win = tk.Toplevel(root)
        win.withdraw()  # compare solo quando è pronta e centrata
        win.title(t("s.window_title"))
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self.close)

        page = ttk.Frame(win, padding=(24, 18, 24, 20))
        page.pack(fill="both", expand=True)
        ttk.Label(page, text=t("s.title"), style="Title.TLabel").pack(anchor="w", pady=(0, 12))

        tabs = ttk.Notebook(page)
        tabs.pack(fill="both", expand=True)
        general = ttk.Frame(tabs, padding=(16, 14))
        keyboard_tab = ttk.Frame(tabs, padding=(16, 14))
        pad_tab = ttk.Frame(tabs, padding=(16, 14))
        tabs.add(general, text=t("s.tab_general"))
        tabs.add(keyboard_tab, text=t("s.tab_keyboard"))
        tabs.add(pad_tab, text=t("s.tab_controller"))

        self._build_general(general)
        self._build_keyboard(keyboard_tab)
        self._build_controller(pad_tab)

        bottom = ttk.Frame(page)
        bottom.pack(fill="x", pady=(16, 0))
        ttk.Button(bottom, text=t("s.cancel"), command=self.close).pack(side="right")
        ttk.Button(bottom, text=t("s.save"), style="Accent.TButton", command=self._save).pack(side="right", padx=8)

        self._load_preset()
        self.apply_theme(pal)
        self._update_pad_status()
        theme.center_on_screen(win)  # stima, da nascosta
        win.deiconify()
        theme.center_on_screen(win)  # correzione con le misure reali
        win.lift()
        win.focus_force()

    # --- Schede --------------------------------------------------------------
    def _build_general(self, tab):
        _section(tab, t("s.apps"), t("s.apps_desc"))
        apps = ttk.Frame(tab)
        apps.pack(fill="x")
        self._targets = AppList(apps, self._icons, height=5)
        self._targets.pack(side="left", fill="both", expand=True)
        for exe in self._cfg["targets"]:
            # Per gli exe aggiunti senza percorso: lo cerca tra i processi aperti.
            path = self._paths.get(exe) or appinfo.find_running_path(exe)
            if path:
                self._paths[exe] = path
            self._targets.add(exe, path)
        buttons = ttk.Frame(apps)
        buttons.pack(side="left", fill="y", padx=(10, 0))
        ttk.Button(buttons, text=t("s.browse"), command=self._browse_exe).pack(fill="x")
        ttk.Button(buttons, text=t("s.from_running"), command=self._pick_process).pack(fill="x", pady=6)
        ttk.Button(buttons, text=t("s.remove"), command=self._remove_target).pack(fill="x")

        self._always = tk.BooleanVar(value=self._cfg["always_active"])
        ttk.Checkbutton(tab, text=t("s.always_active"),
                        variable=self._always, style="Switch.TCheckbutton").pack(anchor="w", pady=(12, 2))
        self._show_overlay = tk.BooleanVar(value=self._cfg["show_overlay"])
        ttk.Checkbutton(tab, text=t("s.show_overlay"),
                        variable=self._show_overlay, style="Switch.TCheckbutton").pack(anchor="w")

        auto_hide = ttk.Frame(tab)
        auto_hide.pack(anchor="w", pady=2)
        self._auto_hide = tk.BooleanVar(value=self._cfg["auto_hide"])
        ttk.Checkbutton(auto_hide, text=t("s.auto_hide"), variable=self._auto_hide,
                        style="Switch.TCheckbutton").pack(side="left")
        self._auto_hide_seconds = tk.StringVar(value=str(self._cfg["auto_hide_seconds"]))
        ttk.Spinbox(auto_hide, from_=1, to=60, textvariable=self._auto_hide_seconds, width=4).pack(side="left", padx=6)
        ttk.Label(auto_hide, text=t("s.auto_hide_suffix")).pack(side="left")

        self._hide_on_exclusive = tk.BooleanVar(value=self._cfg["hide_on_exclusive"])
        ttk.Checkbutton(tab, text=t("s.hide_on_exclusive"),
                        variable=self._hide_on_exclusive, style="Switch.TCheckbutton").pack(anchor="w")

        self._pause_on_exit = tk.BooleanVar(value=self._cfg["pause_on_exit"])
        ttk.Checkbutton(tab, text=t("s.pause_on_exit"),
                        variable=self._pause_on_exit, style="Switch.TCheckbutton").pack(anchor="w")

        ttk.Separator(tab).pack(fill="x", pady=16)

        _section(tab, t("s.appearance"), t("s.appearance_desc"))
        self._transparent_bg = tk.BooleanVar(value=self._cfg["transparent_bg"])
        ttk.Checkbutton(tab, text=t("s.transparent_bg"), variable=self._transparent_bg,
                        style="Switch.TCheckbutton", command=self._preview).pack(anchor="w")
        opacity = ttk.Frame(tab)
        opacity.pack(anchor="w", pady=(8, 0))
        ttk.Label(opacity, text=t("s.opacity")).pack(side="left")
        self._opacity = tk.IntVar(value=self._cfg["overlay_opacity"])
        self._opacity_value = ttk.Label(opacity, text=f"{self._opacity.get()}%", width=5)
        ttk.Scale(opacity, from_=30, to=100, length=220, variable=self._opacity,
                  command=self._opacity_changed).pack(side="left", padx=12)
        self._opacity_value.pack(side="left")

        ttk.Separator(tab).pack(fill="x", pady=16)

        # Volume e lingua affiancati, per non allungare la finestra.
        row = ttk.Frame(tab)
        row.pack(fill="x")
        volume = ttk.Frame(row)
        volume.pack(side="left", anchor="n")
        _section(volume, t("s.volume"), t("s.volume_desc"))
        step = ttk.Frame(volume)
        step.pack(anchor="w")
        self._step = tk.StringVar(value=str(self._cfg["volume_step"]))
        ttk.Spinbox(step, from_=1, to=25, textvariable=self._step, width=5).pack(side="left")
        ttk.Label(step, text="%").pack(side="left", padx=(6, 0))

        language = ttk.Frame(row)
        language.pack(side="left", anchor="n", padx=(48, 0))
        _section(language, t("s.language"), t("s.language_desc"))
        self._language_names = {name: code for code, name in LANGUAGES.items()}
        self._language = tk.StringVar(value=LANGUAGES.get(self._cfg["language"], LANGUAGES["en"]))
        ttk.Combobox(language, textvariable=self._language, values=list(self._language_names),
                     state="readonly", width=14).pack(anchor="w")

    def _build_keyboard(self, tab):
        self._preset_bar(tab)
        _section(tab, t("s.hotkeys"), t("s.hotkeys_desc"))
        self._binding_table(tab, "hotkeys")

    def _build_controller(self, tab):
        self._preset_bar(tab)
        _section(tab, t("s.pad_title"), t("s.pad_desc"))
        self._pad_enabled = tk.BooleanVar(value=self._cfg["controller_enabled"])
        ttk.Checkbutton(tab, text=t("s.use_pad"), variable=self._pad_enabled,
                        style="Switch.TCheckbutton").pack(anchor="w")
        self._pad_status = ttk.Label(tab, style="Muted.TLabel")
        self._pad_status.pack(anchor="w", pady=(4, 12))

        self._binding_table(tab, "controller")

        ttk.Label(tab, style="Muted.TLabel", text=t("s.pad_tip")).pack(anchor="w", pady=(14, 0))

    def _preset_bar(self, tab):
        """Selettore del preset. È in entrambe le schede, ma la scelta è condivisa."""
        bar = ttk.Frame(tab)
        bar.pack(fill="x")
        ttk.Label(bar, text=t("s.preset"), style="Section.TLabel").pack(side="left", padx=(0, 10))
        choice = ttk.Combobox(bar, textvariable=self._preset, state="readonly", width=30)
        choice.pack(side="left")
        choice.bind("<<ComboboxSelected>>", lambda e: self._load_preset())
        delete = ttk.Button(bar, text=t("s.preset_delete"), command=self._delete_preset)
        delete.pack(side="right")
        create = ttk.Button(bar, text=t("s.preset_create"), style="Accent.TButton",
                            command=self._create_preset)
        create.pack(side="right", padx=(0, 6))
        description = ttk.Label(tab, style="Muted.TLabel")
        description.pack(anchor="w", pady=(4, 0))
        ttk.Separator(tab).pack(fill="x", pady=12)
        self._preset_bars.append((choice, description, create, delete))

    def _binding_table(self, parent, kind):
        table = ttk.Frame(parent)
        table.pack(fill="x")
        table.columnconfigure(1, weight=1)
        for row, action in enumerate(ACTIONS):
            ttk.Label(table, text=action_label(action)).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=3)
            var = tk.StringVar()
            ttk.Entry(table, textvariable=var, state="readonly", width=30).grid(row=row, column=1, sticky="ew", pady=3)
            rec = ttk.Button(table, text=t("s.record"), command=lambda a=action: self._record(kind, a))
            rec.grid(row=row, column=2, padx=(8, 4), pady=3)
            clear = ttk.Button(table, text="✕", width=2, command=lambda a=action: self._set_binding(kind, a, ""))
            clear.grid(row=row, column=3, pady=3)
            self._vars[kind][action] = var
            self._edit_buttons += [rec, clear]

    # --- Preset --------------------------------------------------------------
    def _current_preset(self):
        return self._preset_choices.get(self._preset.get())

    def _app_name(self, exe):
        return appinfo.app_name(exe, self._paths.get(exe))

    def _load_preset(self):
        """Aggiorna selettori e tabelle per il preset scelto."""
        targets = self._targets.exes()
        self._preset_choices = {self._general_preset: None}
        for exe in targets:
            name = self._app_name(exe)
            # Senza nome vero, app_name restituisce il nome del file: basta l'exe.
            self._preset_choices[exe if name == os.path.splitext(exe)[0] else f"{name} ({exe})"] = exe
        if self._preset.get() not in self._preset_choices:
            self._preset.set(self._general_preset)
        exe = self._current_preset()
        own = exe in self._presets
        if exe is None:
            text = t("s.preset_used_general")
        elif own:
            text = t("s.preset_used_app", app=self._app_name(exe))
        else:
            text = t("s.preset_uses_general", app=self._app_name(exe))
        for choice, description, create, delete in self._preset_bars:
            choice.configure(values=list(self._preset_choices))
            description.configure(text=text)
            create.state(["!disabled"] if exe and not own else ["disabled"])
            delete.state(["!disabled"] if exe and own else ["disabled"])

        bindings = self._presets[exe if own else None]
        for kind in BINDING_KINDS:
            for action, var in self._vars[kind].items():
                var.set(self._display(kind, bindings[kind].get(action, "")))
        self._update_edit_buttons()

    def _update_edit_buttons(self):
        editable = self._current_preset() in self._presets and not self._recording
        for button in self._edit_buttons:
            button.state(["!disabled"] if editable else ["disabled"])

    def _create_preset(self):
        exe = self._current_preset()
        if exe and exe not in self._presets:
            self._presets[exe] = copy.deepcopy(self._presets[None])  # parte dal generale
            self._load_preset()

    def _delete_preset(self):
        exe = self._current_preset()
        if exe in self._presets and exe is not None and messagebox.askyesno(
                t("s.preset_delete"), t("s.delete_preset_question", app=self._app_name(exe)), parent=self.win):
            del self._presets[exe]
            self._load_preset()

    @staticmethod
    def _display(kind, combo):
        return controller.format_combo(combo) if kind == "controller" else combo

    def apply_theme(self, pal):
        self._pal = pal
        self.win.configure(bg=pal.window)
        theme.style_title_bar(self.win, pal.dark)

    def lift(self):
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    def close(self):
        self._cancel_recording.set()
        self.win.destroy()
        self._on_close()

    def _update_pad_status(self):
        if not self.win.winfo_exists():
            return
        names = controller.connected_devices()
        self._pad_status.configure(
            text=t("s.pad_connected", names=", ".join(names)) if names else t("s.pad_none"))
        self.win.after(PAD_STATUS_MS, self._update_pad_status)

    def _opacity_changed(self, value):
        self._opacity.set(round(float(value)))
        self._opacity_value.configure(text=f"{self._opacity.get()}%")
        self._preview()

    def _preview(self):
        self._on_preview(self._transparent_bg.get(), self._opacity.get())

    # --- App associate -------------------------------------------------------
    def _add_target(self, exe, path=None):
        exe = exe.strip().lower()
        if path:
            self._paths[exe] = os.path.normpath(path)
        if exe and exe not in self._targets.exes():
            self._targets.add(exe, self._paths.get(exe))
            self._load_preset()

    def _browse_exe(self):
        path = filedialog.askopenfilename(parent=self.win, title=t("s.choose_program"),
                                          filetypes=[(t("s.programs"), "*.exe")])
        if path:
            self._add_target(os.path.basename(path), path)

    def _pick_process(self):
        ProcessPicker(self.win, self._pal, self._icons, self._add_target)

    def _remove_target(self):
        self._targets.remove_selected()
        self._load_preset()  # il preset di un exe rimosso viene scartato al salvataggio

    # --- Registrazione tasti e pulsanti --------------------------------------
    def _set_binding(self, kind, action, combo):
        self._presets[self._current_preset()][kind][action] = combo
        self._vars[kind][action].set(self._display(kind, combo))

    def _record(self, kind, action):
        if self._recording:
            return
        preset = self._current_preset()
        self._recording = (preset, kind, action)
        self._vars[kind][action].set(t(RECORDING_TEXT[kind]))
        self._update_edit_buttons()
        for choice, *_ in self._preset_bars:
            choice.state(["disabled"])

        def worker():
            combo = hotkeys.record() if kind == "hotkeys" else controller.record(self._cancel_recording)
            self._call_in_ui(self._recorded, combo)

        threading.Thread(target=worker, name="record", daemon=True).start()

    def _recorded(self, combo):
        _, kind, action = self._recording
        self._recording = None
        if not self.win.winfo_exists():
            return
        if combo:
            self._set_binding(kind, action, combo)
        for choice, *_ in self._preset_bars:
            choice.state(["!disabled", "readonly"])
        self._load_preset()

    # --- Salvataggio ---------------------------------------------------------
    def _validate(self, targets):
        """Messaggio d'errore per il primo preset non valido, o None."""
        for exe, preset in self._presets.items():
            if exe is not None and exe not in targets:
                continue
            name = t("tray.general") if exe is None else exe
            invalid = [action_label(a) for a, c in preset["hotkeys"].items() if c and not hotkeys.is_valid(c)]
            if invalid:
                return t("s.invalid_keys", name=name, actions=", ".join(invalid))
            for kind, message in (("hotkeys", "s.duplicate_keys"), ("controller", "s.duplicate_buttons")):
                duplicates = _duplicates(preset[kind])
                if duplicates:
                    return t(message, name=name, combos=", ".join(self._display(kind, d) for d in duplicates))
        return None

    def _save(self):
        if self._recording:
            return
        targets = self._targets.exes()
        error = self._validate(targets)
        if error:
            messagebox.showerror(t("s.invalid_title"), error, parent=self.win)
            return

        self._cfg.update(
            targets=targets,
            target_paths={exe: self._paths[exe] for exe in targets if exe in self._paths},
            always_active=self._always.get(),
            show_overlay=self._show_overlay.get(),
            auto_hide=self._auto_hide.get(),
            auto_hide_seconds=_int_in_range(self._auto_hide_seconds.get(), 1, 60, self._cfg["auto_hide_seconds"]),
            pause_on_exit=self._pause_on_exit.get(),
            hide_on_exclusive=self._hide_on_exclusive.get(),
            transparent_bg=self._transparent_bg.get(),
            overlay_opacity=_int_in_range(self._opacity.get(), 30, 100, self._cfg["overlay_opacity"]),
            volume_step=_int_in_range(self._step.get(), 1, 25, self._cfg["volume_step"]),
            controller_enabled=self._pad_enabled.get(),
            language=self._language_names.get(self._language.get(), self._cfg["language"]),
            presets={exe: p for exe, p in self._presets.items() if exe is not None and exe in targets},
            **self._presets[None],
        )
        self._on_save(self._cfg)
        self.close()


class AppList(ttk.Frame):
    """Elenco di programmi: icona e nome dell'applicazione, nome dell'exe a destra."""

    def __init__(self, parent, icons, height):
        super().__init__(parent)
        self._icons = icons  # cache condivisa (percorso, dimensione) -> PhotoImage
        scale = theme.ui_scale(self)
        self._size = round(ICON_SIZE * scale)
        ttk.Style(self).configure("Apps.Treeview", rowheight=round(self._size * 1.6))
        self.tree = ttk.Treeview(self, columns=("exe",), show="tree", height=height,
                                 selectmode="browse", style="Apps.Treeview")
        self.tree.column("#0", width=round(230 * scale), stretch=True)
        self.tree.column("exe", width=round(185 * scale), anchor="e", stretch=False)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y", padx=(4, 0))

    def _icon(self, path):
        key = (path, self._size)
        if key not in self._icons:
            image = appinfo.exe_icon(path, self._size) if path else None
            if image is None:  # spazio vuoto, così i nomi restano allineati
                image = Image.new("RGBA", (self._size, self._size), (0, 0, 0, 0))
            self._icons[key] = ImageTk.PhotoImage(image, master=self)
        return self._icons[key]

    def add(self, exe, path):
        self.tree.insert("", "end", iid=exe, text="  " + appinfo.app_name(exe, path),
                         image=self._icon(path), values=(exe,))

    def exes(self):
        return list(self.tree.get_children())

    def selected(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def remove_selected(self):
        for exe in self.tree.selection():
            self.tree.delete(exe)

    def clear(self):
        self.tree.delete(*self.tree.get_children())


class ProcessPicker:
    """Elenco dei processi in esecuzione: utile per i giochi installati in
    cartelle protette (Microsoft Store / Game Pass) che non si possono sfogliare."""

    def __init__(self, parent, pal, icons, on_pick):
        self._on_pick = on_pick
        # Senza i processi di Windows. Restano quelli senza percorso leggibile:
        # possono essere giochi avviati come amministratore.
        windows = os.path.normcase(os.environ.get("SystemRoot", r"C:\Windows")) + os.sep
        self._paths = {exe: path for exe, path in appinfo.running_programs().items()
                       if not (path and os.path.normcase(path).startswith(windows))}
        self._rows = sorted(((appinfo.app_name(exe, path), exe) for exe, path in self._paths.items()),
                            key=lambda row: row[0].lower())

        win = self.win = tk.Toplevel(parent)
        win.title(t("picker.window_title"))
        win.transient(parent)
        win.grab_set()

        page = ttk.Frame(win, padding=(20, 16, 20, 18))
        page.pack(fill="both", expand=True)
        ttk.Label(page, text=t("picker.title"), style="Section.TLabel").pack(anchor="w")
        ttk.Label(page, text=t("picker.desc"), style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self._filter = tk.StringVar()
        self._filter.trace_add("write", lambda *_: self._refresh())
        entry = ttk.Entry(page, textvariable=self._filter, width=40)
        entry.pack(fill="x")
        entry.focus_set()

        self._list = AppList(page, icons, height=12)
        self._list.pack(fill="both", expand=True, pady=10)
        self._list.tree.bind("<Double-Button-1>", lambda e: self._choose())

        bottom = ttk.Frame(page)
        bottom.pack(fill="x")
        ttk.Button(bottom, text=t("s.cancel"), command=win.destroy).pack(side="right")
        ttk.Button(bottom, text=t("picker.add"), style="Accent.TButton", command=self._choose).pack(side="right", padx=8)
        self.apply_theme(pal)
        self._refresh()

    def apply_theme(self, pal):
        self.win.configure(bg=pal.window)
        theme.style_title_bar(self.win, pal.dark)

    def _refresh(self):
        needle = self._filter.get().lower()
        self._list.clear()
        for name, exe in self._rows:
            if needle in name.lower() or needle in exe:
                self._list.add(exe, self._paths[exe])

    def _choose(self):
        exe = self._list.selected()
        if exe:
            self._on_pick(exe, self._paths[exe])
            self.win.destroy()
