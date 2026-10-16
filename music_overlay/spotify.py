"""Controllo di Spotify tramite le API di Windows: nessun account, login o Web API.

- Riproduzione: System Media Transport Controls (la stessa interfaccia usata dai
  tasti multimediali), filtrando la sessione di Spotify.
- Volume: il volume di Spotify nel mixer di Windows, non quello di sistema.
"""
import asyncio
import logging
import threading
from dataclasses import dataclass

import comtypes
from pycaw.pycaw import AudioUtilities
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winrt.windows.storage.streams import DataReader

log = logging.getLogger(__name__)

SPOTIFY_EXE = "spotify.exe"

COMMANDS = {
    "play": lambda s: s.try_play_async(),
    "pause": lambda s: s.try_pause_async(),
    "next": lambda s: s.try_skip_next_async(),
    "previous": lambda s: s.try_skip_previous_async(),
}


@dataclass
class Status:
    running: bool = False
    playing: bool = False
    artist: str = ""
    title: str = ""
    volume: float | None = None
    message: str = ""  # codice tradotto dall'overlay: "no_audio", "spotify_closed", "error"
    art: bytes | None = None  # copertina (PNG/JPEG)


class SpotifyController:
    """Esegue i comandi su un thread dedicato: le API WinRT sono asincrone e COM
    va inizializzato nel thread che lo usa."""

    def __init__(self, volume_step):
        self._volume_step = volume_step  # callable -> percentuale (int)
        self._manager = None
        self._art_track = None
        self._art = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._run, name="spotify", daemon=True).start()

    def _run(self):
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def submit(self, action, on_done):
        """action: una chiave di ACTIONS, oppure None per leggere solo lo stato.
        on_done(Status) viene chiamato dal thread di Spotify."""
        future = asyncio.run_coroutine_threadsafe(self._perform(action), self._loop)
        future.add_done_callback(lambda f: on_done(f.result()))

    def run_blocking(self, action, timeout=3.0):
        """Come submit(), ma aspetta la fine del comando (usato in chiusura)."""
        future = asyncio.run_coroutine_threadsafe(self._perform(action), self._loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            log.warning("Comando %r scaduto", action)
            return None

    async def _perform(self, action):
        message = ""
        try:
            if action in ("volume_up", "volume_down"):
                step = self._volume_step() / 100
                if not self._change_volume(step if action == "volume_up" else -step):
                    message = "no_audio"
            elif action:
                session = await self._session()
                if session is None:
                    message = "spotify_closed"
                else:
                    await COMMANDS[action](session)
                    # Lascia a Spotify il tempo di aggiornare titolo e stato.
                    await asyncio.sleep(0.3)
            status = await self._status()
        except Exception:
            log.exception("Comando %r fallito", action)
            return Status(message="error")
        status.message = message
        return status

    async def _session(self):
        if self._manager is None:
            self._manager = await SessionManager.request_async()
        for session in self._manager.get_sessions():
            if "spotify" in session.source_app_user_model_id.lower():
                return session
        return None

    async def _status(self):
        volumes = self._spotify_volumes()
        volume = volumes[0].GetMasterVolume() if volumes else None
        session = await self._session()
        if session is None:
            return Status(volume=volume)
        props = await session.try_get_media_properties_async()
        playing = session.get_playback_info().playback_status == PlaybackStatus.PLAYING
        art = await self._cover(props)
        return Status(True, playing, props.artist, props.title, volume, art=art)

    async def _cover(self, props):
        """Legge la copertina solo quando cambia canzone."""
        track = (props.artist, props.title)
        if track != self._art_track:
            self._art = await self._read_thumbnail(props.thumbnail)
            # Se Spotify non l'ha ancora pubblicata, riprova al prossimo aggiornamento.
            self._art_track = track if self._art else None
        return self._art

    @staticmethod
    async def _read_thumbnail(reference):
        if reference is None:
            return None
        try:
            stream = await reference.open_read_async()
            reader = DataReader(stream.get_input_stream_at(0))
            await reader.load_async(stream.size)
            data = bytearray(stream.size)
            reader.read_bytes(data)
            return bytes(data)
        except OSError:
            log.warning("Copertina non disponibile", exc_info=True)
            return None

    @staticmethod
    def _spotify_volumes():
        # Windows crea la sessione audio solo dopo che Spotify ha riprodotto qualcosa.
        return [
            s.SimpleAudioVolume
            for s in AudioUtilities.GetAllSessions()
            if s.Process and s.Process.name().lower() == SPOTIFY_EXE
        ]

    def _change_volume(self, delta):
        volumes = self._spotify_volumes()
        if not volumes:
            return False
        new = min(1.0, max(0.0, volumes[0].GetMasterVolume() + delta))
        for v in volumes:
            v.SetMasterVolume(new, None)
        return True
