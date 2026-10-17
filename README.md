<img src="assets/icon.png" width="96" alt="Music Overlay icon">

# Music Overlay

Control Spotify while you play: play, pause, next/previous track, shuffle and volume, from
the keyboard, a controller or gaming devices (button boxes, wheels, shifters…), with
a small overlay that shows the cover art and the track title.

The app sits in the notification area and turns on by itself when you open one of
the programs you picked.

## Installation

Download `MusicOverlay-<version>-Setup.exe` from the
[Releases](https://github.com/beppegoodoldrebel/Background-music-App/releases) page and run it.
No administrator rights and no Python needed. Requires Windows 10 or 11 (64-bit) and
Spotify for desktop (Premium not required: no account or login needed).

The installer isn't digitally signed, so Windows SmartScreen may warn you:
click **More info → Run anyway**.

During setup you can add a desktop icon and start Music Overlay with Windows.
Uninstall it from **Settings → Apps**; your settings are kept.

## Getting started

Open **Music Overlay** from the Start menu. A splash screen with the app's icon and name shows for
two seconds, then the app lives in the notification area:
right-click the icon → **Settings**, **Show overlay**, **Quit**.
The icon is green while the controls are active and grey while the app is waiting.

The settings open on first launch. The default language is English: change it in
the **General → Language** tab.

## Features

**Automatic activation**
- Pick the games' exe files with "Browse .exe…" or, with the game running, with
  "From running apps…" (needed for Microsoft Store / Game Pass games).
  The list shows each application's icon and name.
- When one of these programs is open, hotkeys and overlay turn on; when it closes,
  they turn off. Alternatively: "Always active".
- Option to pause Spotify when you close the game or Music Overlay.

**Overlay**
- Spotify's cover art, title, artist, buttons and volume. Drag it to move it.
- Clicking it doesn't take focus away from the game.
- Can hide after X seconds and reappear on every new song or command.
- Transparent background and adjustable opacity, with a live preview.
- Light or dark theme to match Windows (read at startup).
- Hides itself when a game is in exclusive fullscreen.

**Controls**
- Global hotkeys, recorded by pressing the key combination.
- Xbox controllers (XInput) and any device Windows lists under
  "Game Controllers": button boxes, wheels, shifters, joysticks.
- Hold the combination down and the volume keeps changing.
- **Presets**: one general preset plus, if you want, one per exe, with different
  keys and buttons for each game.

**Languages**: English, Italian, French, Spanish, German.

### Default controls

| Action | Keyboard | Xbox controller |
|---|---|---|
| Volume up / down | Ctrl+Alt+↑ / ↓ | View + D-pad ↑ / ↓ |
| Next / previous track | Ctrl+Alt+→ / ← | View + D-pad → / ← |
| Pause | Ctrl+Alt+Space | View + X |
| Play | Ctrl+Alt+Enter | View + A |
| Toggle shuffle | Ctrl+Alt+S | View + Y |

## Notes and limitations

- The volume being changed is Spotify's in the Windows volume mixer, not the system
  volume. Spotify shows up in the mixer only after it has played something at least once.
- The overlay can't be shown over exclusive fullscreen; hotkeys and controllers still
  work. Use borderless windowed mode to see it.
- If the game runs as administrator, run Music Overlay as administrator too,
  otherwise Windows blocks the hotkeys.
- PlayStation controllers work through Steam Input or DS4Windows.
- For non-Xbox devices, buttons and the D-pad are read (up to 32 buttons), not
  the analog axes.
- Settings: `%APPDATA%\MusicOverlay\config.json`.

## Structure

| File | Contents |
|---|---|
| `music_overlay/app.py` | Coordination: activation, overlay, presets, tray icon |
| `music_overlay/spotify.py` | Spotify commands and status (Windows media APIs) |
| `music_overlay/overlay.py` | Overlay |
| `music_overlay/settings_window.py` | Settings window |
| `music_overlay/hotkeys.py` | Hotkeys |
| `music_overlay/controller.py` | Controllers and gaming devices |
| `music_overlay/watcher.py` | Running programs and exclusive fullscreen |
| `music_overlay/appinfo.py` | Name and icon of exe files |
| `music_overlay/theme.py` | Light/dark theme and window helpers |
| `music_overlay/icon.py` | App icon, drawn in code (`assets/icon.ico` is generated from it) |
| `music_overlay/splash.py` | Splash screen shown at startup |
| `packaging/build.py` | Builds the exe (PyInstaller) and the installer (Inno Setup) |
| `packaging/MusicOverlay.iss` | Installer script |
| `music_overlay/i18n.py` | Texts in the 5 languages |
| `music_overlay/config.py` | Saved settings |

Every input source calls `App.trigger(action)` with one of the actions in
`actions.ACTIONS`: to add a new kind of control, a module that does the same is all
it takes.

## Development

Requires Python 3.12.

```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m music_overlay
```

`Avvia.bat` starts it without a terminal window.

### Building the installer

Needs PyInstaller (`.venv\Scripts\pip install pyinstaller`) and Inno Setup 6
(`winget install JRSoftware.InnoSetup`). The version comes from
`music_overlay/__init__.py`.

```
.venv\Scripts\python packaging\build.py
```

The result is `build\installer\MusicOverlay-<version>-Setup.exe`.
