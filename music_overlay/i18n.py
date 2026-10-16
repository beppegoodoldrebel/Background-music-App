"""Testi dell'interfaccia in più lingue. Uso: t("chiave", parametro=valore)."""
import logging

log = logging.getLogger(__name__)

# Codice -> nome nella lingua stessa (come appare nel selettore).
LANGUAGES = {"en": "English", "it": "Italiano", "fr": "Français", "es": "Español", "de": "Deutsch"}
DEFAULT_LANGUAGE = "en"

_language = DEFAULT_LANGUAGE


def set_language(code):
    global _language
    _language = code if code in LANGUAGES else DEFAULT_LANGUAGE


def get_language():
    return _language


def t(key, **values):
    texts = STRINGS.get(key)
    if texts is None:
        log.warning("Testo mancante: %s", key)
        return key
    text = texts.get(_language) or texts[DEFAULT_LANGUAGE]
    return text.format(**values) if values else text


# Ogni voce: {codice lingua: testo}. L'inglese è obbligatorio (fa da ripiego).
STRINGS = {
    # --- Avvio e icona nell'area di notifica ------------------------------
    "app.already_running": {
        "en": "Music Overlay is already running (icon in the notification area).",
        "it": "Music Overlay è già in esecuzione (icona nella barra delle applicazioni).",
        "fr": "Music Overlay est déjà en cours d'exécution (icône dans la zone de notification).",
        "es": "Music Overlay ya se está ejecutando (icono en el área de notificación).",
        "de": "Music Overlay läuft bereits (Symbol im Infobereich).",
    },
    "tray.settings": {"en": "Settings", "it": "Impostazioni", "fr": "Paramètres", "es": "Configuración",
                      "de": "Einstellungen"},
    "tray.show_overlay": {"en": "Show overlay", "it": "Mostra overlay", "fr": "Afficher l'overlay",
                          "es": "Mostrar overlay", "de": "Overlay anzeigen"},
    "tray.quit": {"en": "Quit", "it": "Esci", "fr": "Quitter", "es": "Salir", "de": "Beenden"},
    "tray.idle": {"en": "Music Overlay - waiting", "it": "Music Overlay - in attesa",
                  "fr": "Music Overlay - en attente", "es": "Music Overlay - en espera",
                  "de": "Music Overlay - wartet"},
    "tray.active": {
        "en": "Music Overlay - active ({reason}) - preset {preset}",
        "it": "Music Overlay - attivo ({reason}) - preset {preset}",
        "fr": "Music Overlay - actif ({reason}) - préréglage {preset}",
        "es": "Music Overlay - activo ({reason}) - preset {preset}",
        "de": "Music Overlay - aktiv ({reason}) - Profil {preset}",
    },
    "tray.always_active": {"en": "always active", "it": "sempre attivo", "fr": "toujours actif",
                           "es": "siempre activo", "de": "immer aktiv"},
    "tray.general": {"en": "general", "it": "generale", "fr": "général", "es": "general", "de": "allgemein"},

    # --- Azioni -----------------------------------------------------------
    "action.volume_up": {"en": "Volume up", "it": "Volume su", "fr": "Monter le volume",
                         "es": "Subir volumen", "de": "Lauter"},
    "action.volume_down": {"en": "Volume down", "it": "Volume giù", "fr": "Baisser le volume",
                           "es": "Bajar volumen", "de": "Leiser"},
    "action.next": {"en": "Next track", "it": "Canzone avanti", "fr": "Piste suivante",
                    "es": "Canción siguiente", "de": "Nächster Titel"},
    "action.previous": {"en": "Previous track", "it": "Canzone indietro", "fr": "Piste précédente",
                        "es": "Canción anterior", "de": "Vorheriger Titel"},
    "action.pause": {"en": "Pause", "it": "Pausa", "fr": "Pause", "es": "Pausa", "de": "Pause"},
    "action.play": {"en": "Play", "it": "Riproduci", "fr": "Lecture", "es": "Reproducir", "de": "Wiedergabe"},

    # --- Overlay e messaggi di Spotify --------------------------------------
    "msg.spotify_closed": {"en": "Spotify isn't open", "it": "Spotify non è aperto",
                           "fr": "Spotify n'est pas ouvert", "es": "Spotify no está abierto",
                           "de": "Spotify ist nicht geöffnet"},
    "msg.open_spotify": {"en": "Open it to control the music", "it": "Aprilo per controllare la musica",
                         "fr": "Ouvrez-le pour contrôler la musique", "es": "Ábrelo para controlar la música",
                         "de": "Öffne es, um die Musik zu steuern"},
    "msg.no_audio": {
        "en": "Start playback in Spotify to adjust its volume",
        "it": "Avvia la musica su Spotify per regolarne il volume",
        "fr": "Lancez la lecture dans Spotify pour régler son volume",
        "es": "Inicia la reproducción en Spotify para ajustar su volumen",
        "de": "Starte die Wiedergabe in Spotify, um die Lautstärke zu ändern",
    },
    "msg.error": {"en": "Spotify didn't respond", "it": "Spotify non ha risposto", "fr": "Spotify n'a pas répondu",
                  "es": "Spotify no respondió", "de": "Spotify hat nicht reagiert"},

    # --- Controller -------------------------------------------------------
    "pad.xbox": {"en": "Xbox controller", "it": "Controller Xbox", "fr": "Manette Xbox",
                 "es": "Mando de Xbox", "de": "Xbox-Controller"},
    "pad.dpad": {"en": "D-pad {arrow}", "it": "Croce {arrow}", "fr": "Croix {arrow}",
                 "es": "Cruceta {arrow}", "de": "Steuerkreuz {arrow}"},
    "pad.device_button": {"en": "{device} button {n}", "it": "{device} pulsante {n}",
                          "fr": "{device} bouton {n}", "es": "{device} botón {n}", "de": "{device} Taste {n}"},
    "pad.device_dpad": {"en": "{device} D-pad {arrow}", "it": "{device} croce {arrow}",
                        "fr": "{device} croix {arrow}", "es": "{device} cruceta {arrow}",
                        "de": "{device} Steuerkreuz {arrow}"},
    "pad.unknown_device": {"en": "Device {id}", "it": "Dispositivo {id}", "fr": "Périphérique {id}",
                           "es": "Dispositivo {id}", "de": "Gerät {id}"},

    # --- Impostazioni: struttura ------------------------------------------
    "s.window_title": {"en": "Music Overlay - Settings", "it": "Music Overlay - Impostazioni",
                       "fr": "Music Overlay - Paramètres", "es": "Music Overlay - Configuración",
                       "de": "Music Overlay - Einstellungen"},
    "s.title": {"en": "Settings", "it": "Impostazioni", "fr": "Paramètres", "es": "Configuración",
                "de": "Einstellungen"},
    "s.tab_general": {"en": "General", "it": "Generale", "fr": "Général", "es": "General", "de": "Allgemein"},
    "s.tab_keyboard": {"en": "Keyboard", "it": "Tastiera", "fr": "Clavier", "es": "Teclado", "de": "Tastatur"},
    "s.tab_controller": {"en": "Controller", "it": "Controller", "fr": "Manette", "es": "Mando",
                         "de": "Controller"},
    "s.save": {"en": "Save", "it": "Salva", "fr": "Enregistrer", "es": "Guardar", "de": "Speichern"},
    "s.cancel": {"en": "Cancel", "it": "Annulla", "fr": "Annuler", "es": "Cancelar", "de": "Abbrechen"},

    # --- Impostazioni: Generale -------------------------------------------
    "s.apps": {"en": "Linked apps", "it": "App associate", "fr": "Applications associées",
               "es": "Aplicaciones asociadas", "de": "Verknüpfte Apps"},
    "s.apps_desc": {
        "en": "The controls turn on when one of these apps is open.",
        "it": "I controlli si attivano quando una di queste app è aperta.",
        "fr": "Les commandes s'activent quand l'une de ces applications est ouverte.",
        "es": "Los controles se activan cuando una de estas aplicaciones está abierta.",
        "de": "Die Steuerung wird aktiv, wenn eine dieser Apps geöffnet ist.",
    },
    "s.browse": {"en": "Browse .exe…", "it": "Sfoglia .exe…", "fr": "Parcourir .exe…", "es": "Examinar .exe…",
                 "de": ".exe durchsuchen…"},
    "s.from_running": {"en": "From running apps…", "it": "Dai processi aperti…", "fr": "Depuis les processus…",
                       "es": "Desde procesos abiertos…", "de": "Aus laufenden Prozessen…"},
    "s.remove": {"en": "Remove", "it": "Rimuovi", "fr": "Retirer", "es": "Quitar", "de": "Entfernen"},
    "s.always_active": {
        "en": "Always active, even when these apps aren't open",
        "it": "Sempre attivo, anche senza queste app aperte",
        "fr": "Toujours actif, même sans ces applications ouvertes",
        "es": "Siempre activo, aunque estas aplicaciones no estén abiertas",
        "de": "Immer aktiv, auch wenn diese Apps nicht geöffnet sind",
    },
    "s.show_overlay": {
        "en": "Show the overlay when the controls are active",
        "it": "Mostra l'overlay quando i controlli sono attivi",
        "fr": "Afficher l'overlay quand les commandes sont actives",
        "es": "Mostrar el overlay cuando los controles están activos",
        "de": "Overlay anzeigen, wenn die Steuerung aktiv ist",
    },
    "s.auto_hide": {"en": "Hide the overlay after", "it": "Nascondi l'overlay dopo",
                    "fr": "Masquer l'overlay après", "es": "Ocultar el overlay después de",
                    "de": "Overlay ausblenden nach"},
    "s.auto_hide_suffix": {"en": "seconds from the start of the song", "it": "secondi dall'inizio della canzone",
                           "fr": "secondes après le début du morceau",
                           "es": "segundos desde el inicio de la canción", "de": "Sekunden ab Titelbeginn"},
    "s.pause_on_exit": {
        "en": "Pause Spotify when you close the linked app or Music Overlay",
        "it": "Metti in pausa Spotify quando chiudi l'app associata o Music Overlay",
        "fr": "Mettre Spotify en pause à la fermeture de l'application associée ou de Music Overlay",
        "es": "Pausar Spotify al cerrar la aplicación asociada o Music Overlay",
        "de": "Spotify pausieren, wenn die verknüpfte App oder Music Overlay geschlossen wird",
    },
    "s.hide_on_exclusive": {
        "en": "Hide the overlay over games in exclusive fullscreen",
        "it": "Nascondi l'overlay sui giochi in fullscreen esclusivo",
        "fr": "Masquer l'overlay sur les jeux en plein écran exclusif",
        "es": "Ocultar el overlay en juegos a pantalla completa exclusiva",
        "de": "Overlay bei Spielen im exklusiven Vollbild ausblenden",
    },
    "s.appearance": {"en": "Overlay appearance", "it": "Aspetto overlay", "fr": "Apparence de l'overlay",
                     "es": "Apariencia del overlay", "de": "Overlay-Darstellung"},
    "s.appearance_desc": {
        "en": "With a transparent background only the cover, text and buttons stay visible.",
        "it": "Con lo sfondo trasparente restano visibili solo copertina, testi e pulsanti.",
        "fr": "Avec un fond transparent, seuls la pochette, les textes et les boutons restent visibles.",
        "es": "Con el fondo transparente solo quedan visibles la portada, los textos y los botones.",
        "de": "Mit transparentem Hintergrund bleiben nur Cover, Texte und Tasten sichtbar.",
    },
    "s.transparent_bg": {"en": "Transparent background", "it": "Sfondo trasparente", "fr": "Fond transparent",
                         "es": "Fondo transparente", "de": "Transparenter Hintergrund"},
    "s.opacity": {"en": "Opacity", "it": "Opacità", "fr": "Opacité", "es": "Opacidad", "de": "Deckkraft"},
    "s.volume": {"en": "Volume", "it": "Volume", "fr": "Volume", "es": "Volumen", "de": "Lautstärke"},
    "s.volume_desc": {
        "en": "Change per press.",
        "it": "Variazione a ogni pressione.",
        "fr": "Variation à chaque appui.",
        "es": "Cambio por pulsación.",
        "de": "Änderung pro Tastendruck.",
    },
    "s.language": {"en": "Language", "it": "Lingua", "fr": "Langue", "es": "Idioma", "de": "Sprache"},
    "s.language_desc": {"en": "Applied when you save.", "it": "Si applica al salvataggio.",
                        "fr": "Appliquée à l'enregistrement.", "es": "Se aplica al guardar.",
                        "de": "Wird beim Speichern übernommen."},

    # --- Impostazioni: Tastiera e Controller ------------------------------
    "s.hotkeys": {"en": "Hotkeys", "it": "Tasti rapidi", "fr": "Raccourcis clavier", "es": "Atajos de teclado",
                  "de": "Tastenkürzel"},
    "s.hotkeys_desc": {
        "en": "Press “Record”, then the key combination (Esc cancels).\n"
              "Hotkeys are paused while this window is open.",
        "it": "Premi «Registra» e poi la combinazione (Esc annulla).\n"
              "Sono in pausa finché questa finestra è aperta.",
        "fr": "Cliquez sur « Capturer », puis appuyez sur la combinaison (Échap pour annuler).\n"
              "Les raccourcis sont en pause tant que cette fenêtre est ouverte.",
        "es": "Pulsa «Grabar» y luego la combinación (Esc cancela).\n"
              "Los atajos están en pausa mientras esta ventana esté abierta.",
        "de": "Klicke auf „Aufnehmen“ und drücke dann die Tastenkombination (Esc bricht ab).\n"
              "Die Tastenkürzel sind pausiert, solange dieses Fenster geöffnet ist.",
    },
    "s.record": {"en": "Record", "it": "Registra", "fr": "Capturer", "es": "Grabar", "de": "Aufnehmen"},
    "s.press_keys": {"en": "Press the keys…", "it": "Premi i tasti…", "fr": "Appuyez sur les touches…",
                     "es": "Pulsa las teclas…", "de": "Tasten drücken…"},
    "s.press_buttons": {"en": "Press the buttons… (10 s)", "it": "Premi i pulsanti… (10 s)",
                        "fr": "Appuyez sur les boutons… (10 s)", "es": "Pulsa los botones… (10 s)",
                        "de": "Tasten drücken… (10 s)"},
    "s.pad_title": {"en": "Controllers and gaming devices", "it": "Controller e periferiche di gioco",
                    "fr": "Manettes et périphériques de jeu", "es": "Mandos y periféricos de juego",
                    "de": "Controller und Gaming-Geräte"},
    "s.pad_desc": {
        "en": "Xbox controllers, button boxes, wheels, shifters, joysticks… Press “Record”,\n"
              "then hold the buttons of the combination and release them.",
        "it": "Controller Xbox, button box, volanti, cambi, joystick… Premi «Registra»,\n"
              "poi tieni premuti i pulsanti della combinazione e rilasciali.",
        "fr": "Manettes Xbox, button box, volants, leviers de vitesse, joysticks… Cliquez sur « Capturer »,\n"
              "puis maintenez les boutons de la combinaison et relâchez-les.",
        "es": "Mandos de Xbox, button box, volantes, palancas de cambio, joysticks… Pulsa «Grabar»,\n"
              "luego mantén pulsados los botones de la combinación y suéltalos.",
        "de": "Xbox-Controller, Button-Boxen, Lenkräder, Schaltknüppel, Joysticks… Klicke auf „Aufnehmen“,\n"
              "halte dann die Tasten der Kombination gedrückt und lass sie los.",
    },
    "s.use_pad": {"en": "Use controllers and devices", "it": "Usa controller e periferiche",
                  "fr": "Utiliser les manettes et périphériques", "es": "Usar mandos y periféricos",
                  "de": "Controller und Geräte verwenden"},
    "s.pad_connected": {"en": "● Connected: {names}", "it": "● Collegati: {names}", "fr": "● Connectés : {names}",
                        "es": "● Conectados: {names}", "de": "● Verbunden: {names}"},
    "s.pad_none": {"en": "No devices found", "it": "Nessun dispositivo trovato", "fr": "Aucun périphérique trouvé",
                   "es": "No se encontró ningún dispositivo", "de": "Keine Geräte gefunden"},
    "s.pad_tip": {
        "en": "Tip: on an Xbox controller use View (the button with two squares) together\n"
              "with another button, so a single press in game doesn't change the music.\n"
              "Buttons already held when recording starts (gear engaged, toggle switches)\n"
              "are ignored.",
        "it": "Consiglio: sul controller Xbox usa View (il tasto con i due quadrati) insieme\n"
              "a un altro pulsante, così premere un tasto da solo nel gioco non cambia la musica.\n"
              "Pulsanti già premuti all'inizio della registrazione (marcia inserita, levette)\n"
              "vengono ignorati.",
        "fr": "Astuce : sur une manette Xbox, utilisez View (le bouton aux deux carrés) avec\n"
              "un autre bouton, pour qu'un appui isolé en jeu ne change pas la musique.\n"
              "Les boutons déjà enfoncés au début de la capture (rapport engagé, interrupteurs)\n"
              "sont ignorés.",
        "es": "Consejo: en el mando de Xbox usa View (el botón de los dos cuadrados) junto con\n"
              "otro botón, así pulsar un solo botón en el juego no cambia la música.\n"
              "Los botones ya pulsados al empezar la grabación (marcha engranada, interruptores)\n"
              "se ignoran.",
        "de": "Tipp: Nutze am Xbox-Controller View (die Taste mit den zwei Quadraten) zusammen\n"
              "mit einer anderen Taste, damit ein einzelner Tastendruck im Spiel die Musik nicht ändert.\n"
              "Tasten, die beim Start der Aufnahme schon gedrückt sind (eingelegter Gang, Kippschalter),\n"
              "werden ignoriert.",
    },

    # --- Impostazioni: preset ---------------------------------------------
    "s.preset": {"en": "Preset", "it": "Preset", "fr": "Préréglage", "es": "Preset", "de": "Profil"},
    "s.preset_general": {"en": "General (default)", "it": "Generale (predefinito)", "fr": "Général (par défaut)",
                         "es": "General (predeterminado)", "de": "Allgemein (Standard)"},
    "s.preset_create": {"en": "Create preset for this exe", "it": "Crea preset per questo exe",
                        "fr": "Créer un préréglage pour cet exe", "es": "Crear preset para este exe",
                        "de": "Profil für diese exe erstellen"},
    "s.preset_delete": {"en": "Delete preset", "it": "Elimina preset", "fr": "Supprimer le préréglage",
                        "es": "Eliminar preset", "de": "Profil löschen"},
    "s.preset_used_general": {
        "en": "Used when no app with its own preset is open.",
        "it": "Usato quando nessuna app con un preset proprio è aperta.",
        "fr": "Utilisé quand aucune application avec son propre préréglage n'est ouverte.",
        "es": "Se usa cuando no hay abierta ninguna aplicación con preset propio.",
        "de": "Wird verwendet, wenn keine App mit eigenem Profil geöffnet ist.",
    },
    "s.preset_used_app": {"en": "Used when {app} is open.", "it": "Usato quando {app} è aperto.",
                          "fr": "Utilisé quand {app} est ouvert.", "es": "Se usa cuando {app} está abierto.",
                          "de": "Wird verwendet, wenn {app} geöffnet ist."},
    "s.preset_uses_general": {
        "en": "{app} uses the general preset. Create a preset to customize it.",
        "it": "{app} usa il preset generale. Crea un preset per personalizzarlo.",
        "fr": "{app} utilise le préréglage général. Créez un préréglage pour le personnaliser.",
        "es": "{app} usa el preset general. Crea un preset para personalizarlo.",
        "de": "{app} verwendet das allgemeine Profil. Erstelle ein Profil, um es anzupassen.",
    },
    "s.delete_preset_question": {
        "en": "Delete the preset for {app}?\nIt will go back to using the general preset.",
        "it": "Eliminare il preset di {app}?\nTornerà a usare il preset generale.",
        "fr": "Supprimer le préréglage de {app} ?\nIl utilisera à nouveau le préréglage général.",
        "es": "¿Eliminar el preset de {app}?\nVolverá a usar el preset general.",
        "de": "Profil für {app} löschen?\nEs wird wieder das allgemeine Profil verwendet.",
    },

    # --- Impostazioni: errori al salvataggio ------------------------------
    "s.invalid_title": {"en": "Invalid combinations", "it": "Combinazioni non valide",
                        "fr": "Combinaisons non valides", "es": "Combinaciones no válidas",
                        "de": "Ungültige Kombinationen"},
    "s.invalid_keys": {"en": "Preset {name}: invalid keys for {actions}",
                       "it": "Preset {name}: tasti non validi per {actions}",
                       "fr": "Préréglage {name} : touches non valides pour {actions}",
                       "es": "Preset {name}: teclas no válidas para {actions}",
                       "de": "Profil {name}: ungültige Tasten für {actions}"},
    "s.duplicate_keys": {"en": "Preset {name}: the same keys are used for several actions: {combos}",
                         "it": "Preset {name}: stessi tasti usati per più azioni: {combos}",
                         "fr": "Préréglage {name} : mêmes touches utilisées pour plusieurs actions : {combos}",
                         "es": "Preset {name}: las mismas teclas se usan para varias acciones: {combos}",
                         "de": "Profil {name}: dieselben Tasten für mehrere Aktionen: {combos}"},
    "s.duplicate_buttons": {"en": "Preset {name}: the same buttons are used for several actions: {combos}",
                            "it": "Preset {name}: stessi pulsanti usati per più azioni: {combos}",
                            "fr": "Préréglage {name} : mêmes boutons utilisés pour plusieurs actions : {combos}",
                            "es": "Preset {name}: los mismos botones se usan para varias acciones: {combos}",
                            "de": "Profil {name}: dieselben Tasten für mehrere Aktionen: {combos}"},

    # --- Scelta del programma ---------------------------------------------
    "s.choose_program": {"en": "Choose the program", "it": "Scegli il programma", "fr": "Choisir le programme",
                         "es": "Elegir el programa", "de": "Programm auswählen"},
    "s.programs": {"en": "Programs", "it": "Programmi", "fr": "Programmes", "es": "Programas", "de": "Programme"},
    "picker.window_title": {"en": "Choose a running app", "it": "Scegli un processo aperto",
                            "fr": "Choisir un processus en cours", "es": "Elegir un proceso abierto",
                            "de": "Laufenden Prozess auswählen"},
    "picker.title": {"en": "Running apps", "it": "Processi aperti", "fr": "Processus en cours",
                     "es": "Procesos abiertos", "de": "Laufende Prozesse"},
    "picker.desc": {"en": "Open the game first, then look for it here.", "it": "Apri prima il gioco, poi cercalo qui.",
                    "fr": "Lancez d'abord le jeu, puis cherchez-le ici.",
                    "es": "Abre primero el juego y luego búscalo aquí.",
                    "de": "Starte zuerst das Spiel und suche es dann hier."},
    "picker.add": {"en": "Add", "it": "Aggiungi", "fr": "Ajouter", "es": "Añadir", "de": "Hinzufügen"},
}
