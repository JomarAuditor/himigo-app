"""Audio playback for 30-second Deezer previews using the pygame mixer."""

import io
import threading

import requests

try:
    import pygame
except ImportError:
    pygame = None


class AudioPlayer:
    """Plays preview URLs. play() returns at once; poll .state from the UI.

    state is one of: idle, loading, playing, paused, finished, error.
    """

    duration = 30.0

    def __init__(self):
        self.state = "idle"
        self.error = ""
        self._token = 0
        self._ready = False
        self._volume = 0.7
        self._session = requests.Session()

    def _ensure_mixer(self):
        if pygame is None:
            raise RuntimeError("pygame is not installed. Run: py -m pip install pygame")
        if not self._ready:
            pygame.mixer.init()
            self._ready = True

    def play(self, url):
        self._ensure_mixer()
        self._token += 1
        token = self._token
        pygame.mixer.music.stop()
        self.state = "loading"
        self.error = ""
        threading.Thread(target=self._load, args=(url, token), daemon=True).start()

    def _load(self, url, token):
        try:
            response = self._session.get(url, timeout=15)
            response.raise_for_status()
            if token != self._token:
                return
            pygame.mixer.music.load(io.BytesIO(response.content), "mp3")
            pygame.mixer.music.set_volume(self._volume)
            if token != self._token:
                return
            pygame.mixer.music.play()
            self.state = "playing"
        except Exception as exc:
            if token == self._token:
                self.state = "error"
                self.error = "Could not play this preview: %s" % exc

    def pause(self):
        if self._ready and self.state == "playing":
            pygame.mixer.music.pause()
            self.state = "paused"

    def resume(self):
        if self._ready and self.state == "paused":
            pygame.mixer.music.unpause()
            self.state = "playing"

    def stop(self):
        self._token += 1
        if self._ready:
            pygame.mixer.music.stop()
        self.state = "idle"

    def set_volume(self, value):
        self._volume = min(1.0, max(0.0, float(value)))
        if self._ready:
            pygame.mixer.music.set_volume(self._volume)

    def get_position(self):
        if not self._ready or self.state not in ("playing", "paused"):
            return 0.0
        return max(0.0, pygame.mixer.music.get_pos() / 1000.0)

    def poll(self):
        """Call regularly from the UI thread to detect the end of a preview."""
        if self._ready and self.state == "playing" and not pygame.mixer.music.get_busy():
            self.state = "finished"
