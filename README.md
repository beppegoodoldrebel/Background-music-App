# Music Overlay

Controlla Spotify mentre giochi: play, pausa, canzone avanti/indietro e volume, da
tastiera, controller o periferiche di gioco (button box, volanti, cambi…), con un
piccolo overlay che mostra copertina e titolo.

L'app resta nell'area di notifica e si attiva da sola quando apri uno dei programmi
che hai scelto.

## Requisiti

- Windows 10 o 11
- Python 3.12
- Spotify per desktop (anche senza Premium: non serve alcun account o login)

## Installazione

```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Avvio

Doppio clic su `Avvia.bat`. Compare un'icona nell'area di notifica:
clic destro → **Impostazioni**, **Mostra overlay**, **Esci**.

Al primo avvio si aprono le impostazioni. La lingua predefinita è l'inglese:
si cambia nella scheda **General → Language**.

## Funzioni

**Attivazione automatica**
- Scegli gli exe dei giochi con «Sfoglia .exe…» oppure, a gioco aperto, con
  «Dai processi aperti…» (serve per i giochi Microsoft Store / Game Pass).
  L'elenco mostra icona e nome dell'applicazione.
- Quando uno di questi programmi è aperto si attivano tasti e overlay; quando si
  chiude si disattivano. In alternativa: «Sempre attivo».
- Opzione per mettere in pausa Spotify alla chiusura del gioco o di Music Overlay.

**Overlay**
- Copertina, titolo, artista, pulsanti e volume di Spotify. Si sposta trascinandolo.
- Non toglie il focus al gioco quando lo clicchi.
- Può nascondersi dopo X secondi e ricomparire a ogni nuova canzone o comando.
- Sfondo trasparente e opacità regolabile, con anteprima dal vivo.
- Tema chiaro o scuro come Windows (letto all'avvio).
- Si nasconde da solo quando un gioco è in fullscreen esclusivo.

**Comandi**
- Tasti rapidi globali, registrabili premendo la combinazione.
- Controller Xbox (XInput) e qualsiasi periferica vista da Windows in
  "Controller di gioco": button box, volanti, cambi, joystick.
- Tenendo premuto, il volume continua a cambiare.
- **Preset**: un preset generale più, se vuoi, uno per ogni exe, con tasti e
  pulsanti diversi per ogni gioco.

**Lingue**: inglese, italiano, francese, spagnolo, tedesco.

### Comandi predefiniti

| Azione | Tastiera | Controller Xbox |
|---|---|---|
| Volume su / giù | Ctrl+Alt+↑ / ↓ | View + Croce ↑ / ↓ |
| Canzone avanti / indietro | Ctrl+Alt+→ / ← | View + Croce → / ← |
| Pausa | Ctrl+Alt+Spazio | View + X |
| Riproduci | Ctrl+Alt+Invio | View + A |

## Note e limiti

- Il volume regolato è quello di Spotify nel mixer di Windows, non quello di sistema.
  Spotify compare nel mixer solo dopo aver riprodotto qualcosa almeno una volta.
- In fullscreen esclusivo l'overlay non si può mostrare; tasti e controller
  funzionano comunque. Usa la modalità finestra senza bordi (borderless) per vederlo.
- Se il gioco è avviato come amministratore, avvia anche Music Overlay come
  amministratore, altrimenti Windows blocca i tasti rapidi.
- I controller PlayStation funzionano tramite Steam Input o DS4Windows.
- Delle periferiche non Xbox si leggono pulsanti e croce (fino a 32 pulsanti),
  non gli assi analogici.
- Impostazioni: `%APPDATA%\MusicOverlay\config.json`.

## Struttura

| File | Contenuto |
|---|---|
| `music_overlay/app.py` | Coordinamento: attivazione, overlay, preset, icona |
| `music_overlay/spotify.py` | Comandi e stato di Spotify (API multimediali di Windows) |
| `music_overlay/overlay.py` | Overlay |
| `music_overlay/settings_window.py` | Finestra delle impostazioni |
| `music_overlay/hotkeys.py` | Tasti rapidi |
| `music_overlay/controller.py` | Controller e periferiche di gioco |
| `music_overlay/watcher.py` | Programmi aperti e fullscreen esclusivo |
| `music_overlay/appinfo.py` | Nome e icona degli exe |
| `music_overlay/theme.py` | Tema chiaro/scuro e utilità per le finestre |
| `music_overlay/i18n.py` | Testi nelle 5 lingue |
| `music_overlay/config.py` | Impostazioni salvate |

Ogni sorgente di input chiama `App.trigger(azione)` con una delle azioni di
`actions.ACTIONS`: per aggiungere un nuovo tipo di comando basta un modulo che
faccia lo stesso.

Per avviarla da terminale: `.venv\Scripts\python -m music_overlay`.
