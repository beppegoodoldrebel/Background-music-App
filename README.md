# Music Overlay

Controlla Spotify (play, pausa, avanti, indietro, volume) con tasti rapidi globali
e un piccolo overlay, attivati automaticamente quando apri un programma scelto da te.

## Avvio

Doppio clic su `Avvia.bat`. L'app vive nell'icona nella barra delle applicazioni
(clic destro → Impostazioni / Mostra overlay / Esci).

Al primo avvio si apre la finestra Impostazioni:
- **App che attivano i controlli**: aggiungi l'.exe del gioco con «Sfoglia» oppure,
  con il gioco già aperto, con «Dai processi aperti» (necessario per i giochi del
  Microsoft Store / Game Pass).
- **Tasti rapidi**: «Registra» e premi la combinazione. Esc annulla.

## Note

- Nessun account o login: usa le API multimediali di Windows. Funziona anche senza Premium.
- Il volume regolato è quello di Spotify nel mixer di Windows, non quello di sistema.
  Spotify compare nel mixer solo dopo aver riprodotto qualcosa almeno una volta.
- L'overlay è visibile sopra i giochi in finestra/borderless, non in fullscreen esclusivo
  (i tasti rapidi funzionano comunque).
- Se il gioco è avviato come amministratore, avvia anche Music Overlay come amministratore,
  altrimenti Windows blocca i tasti rapidi.
- Impostazioni: `%APPDATA%\MusicOverlay\config.json`.

## Sviluppo

```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m music_overlay
```

Ogni sorgente di input chiama `App.trigger(azione)` con una chiave di `actions.ACTIONS`:
per aggiungere un controller basta un nuovo modulo che faccia lo stesso.
