"""Bottom player bar: cover, track info, play/pause, progress and volume."""

import tkinter as tk

from ui import theme
from ui.images import CoverImage
from ui.widgets import RoundedButton, clip_text, make_label

POLL_MS = 250
BUTTON_TEXT = {"loading": "Loading...", "playing": "Pause", "paused": "Resume"}


def format_time(seconds):
    minutes, secs = divmod(int(max(0, seconds)), 60)
    return "%d:%02d" % (minutes, secs)


class ProgressBar(tk.Frame):
    """Progress bar as tk.Frame wrapper — safe for Python 3.14."""

    def __init__(self, parent, bg=theme.SURFACE):
        super().__init__(parent, height=6, bg=bg, bd=0, highlightthickness=0)
        self._fraction = 0.0
        self._canvas = tk.Canvas(self, height=6, bg=bg, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda _e: self._draw())

    def set_fraction(self, fraction):
        self._fraction = min(1.0, max(0.0, fraction))
        self._draw()

    def _draw(self):
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 2:
            return
        self._canvas.delete("all")
        self._canvas.create_rectangle(0, 1, w, h - 1, fill=theme.BORDER, outline="")
        self._canvas.create_rectangle(
            0, 1, int(w * self._fraction), h - 1, fill=theme.PRIMARY, outline=""
        )


class PlayerBar(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.SURFACE, height=92, bd=0, highlightthickness=0)
        self.shell = shell
        self._track = None
        self._job = None
        self._last_error = ""
        self._button_text = "Play"
        self.pack_propagate(False)

        tk.Frame(self, bg=theme.BORDER, height=1).pack(side="top", fill="x")
        row = tk.Frame(self, bg=theme.SURFACE)
        row.pack(fill="both", expand=True, padx=24)

        # Left — cover + track info
        left = tk.Frame(row, bg=theme.SURFACE, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._cover = CoverImage(left, "", 56, "Himigo", radius=12, bg=theme.SURFACE)
        self._cover.pack(side="left", pady=14)
        info = tk.Frame(left, bg=theme.SURFACE)
        info.pack(side="left", padx=14)
        self._title = make_label(info, "Nothing playing", 11, "bold",
                                 theme.TEXT, bg=theme.SURFACE, anchor="w")
        self._title.pack(anchor="w")
        self._subtitle = make_label(
            info, "Choose a track to start listening", 10, "normal",
            theme.SUBTEXT, bg=theme.SURFACE, anchor="w"
        )
        self._subtitle.pack(anchor="w")

        # Right — volume
        right = tk.Frame(row, bg=theme.SURFACE, width=190)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        volume_row = tk.Frame(right, bg=theme.SURFACE)
        volume_row.pack(expand=True)
        make_label(volume_row, "Volume", 9, "bold", theme.SUBTEXT,
                   bg=theme.SURFACE).pack(side="left", padx=(0, 8))
        self._volume = tk.Scale(
            volume_row, from_=0, to=100, orient="horizontal",
            showvalue=False, length=110, bg=theme.SURFACE,
            troughcolor=theme.BORDER, activebackground=theme.PRIMARY,
            highlightthickness=0, bd=0, sliderrelief="flat",
            command=self._on_volume,
        )
        self._volume.set(70)
        self._volume.pack(side="left")

        # Center — play button + progress
        center = tk.Frame(row, bg=theme.SURFACE)
        center.pack(side="left", fill="both", expand=True, padx=16)
        inner = tk.Frame(center, bg=theme.SURFACE)
        inner.pack(expand=True, fill="x")
        self._button = RoundedButton(inner, "Play", self._toggle,
                                     width=110, height=36, backdrop=theme.SURFACE)
        self._button.pack()
        self._button.set_state("disabled")
        timeline = tk.Frame(inner, bg=theme.SURFACE)
        timeline.pack(fill="x", pady=(8, 0))
        self._elapsed = make_label(timeline, "0:00", 9, "normal",
                                   theme.SUBTEXT, bg=theme.SURFACE, width=5)
        self._elapsed.pack(side="left")
        self._total = make_label(timeline, "0:30", 9, "normal",
                                 theme.SUBTEXT, bg=theme.SURFACE, width=5)
        self._total.pack(side="right")
        self._progress = ProgressBar(timeline)
        self._progress.pack(side="left", fill="x", expand=True, padx=8)

        self.bind("<Destroy>", self._on_destroy)
        self._job = self.after(POLL_MS, self._poll)

    def _player(self):
        return getattr(self.shell.app, "player", None)

    def _on_destroy(self, event):
        if event.widget is self and self._job is not None:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def _on_volume(self, value):
        player = self._player()
        if player is not None and hasattr(player, "set_volume"):
            player.set_volume(float(value) / 100.0)

    def _set_button(self, text):
        if text != self._button_text:
            self._button_text = text
            self._button.set_text(text)

    def set_track(self, track):
        self._track = track
        title = track.get("title") or "Untitled"
        artist = track.get("artist") or "Unknown artist"
        album = track.get("album") or ""
        self._title.configure(text=clip_text(title, 34))
        self._subtitle.configure(
            text=clip_text(artist + (" - " + album if album else ""), 40)
        )
        self._cover.set_cover(track.get("cover") or "", title)
        self._button.set_state("normal")
        self._start()

    def _start(self):
        url = (self._track or {}).get("preview") or ""
        player = self._player()
        if not url:
            self.shell.show_toast("No audio preview available for this track.", "info")
            return
        if player is None:
            self.shell.show_toast("Audio not available. Run: pip install pygame", "error")
            return
        try:
            player.play(url)
        except Exception as exc:
            self.shell.show_toast(str(exc), "error")

    def _toggle(self):
        player = self._player()
        if self._track is None or player is None:
            return
        state = getattr(player, "state", "idle")
        if state == "playing":
            player.pause()
        elif state == "paused":
            player.resume()
        elif state != "loading":
            self._start()

    def _poll(self):
        try:
            player = self._player()
            if player is not None and self._track is not None:
                if hasattr(player, "poll"):
                    player.poll()
                state = player.state
                error = getattr(player, "error", "")
                if state == "error" and error and error != self._last_error:
                    self._last_error = error
                    self.shell.show_toast(error, "error")
                self._set_button(BUTTON_TEXT.get(state, "Play"))
                position = player.get_position()
                total = getattr(player, "duration", 30.0)
                self._progress.set_fraction(position / total if total else 0)
                self._elapsed.configure(text=format_time(position))
            self._job = self.after(POLL_MS, self._poll)
        except tk.TclError:
            self._job = None

    def stop(self):
        player = self._player()
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass
        self._set_button("Play")
        self._progress.set_fraction(0)
