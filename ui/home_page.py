"""Home dashboard: hero, quick start cards, genre grid and trending tracks."""

import datetime
import tkinter as tk

from ui import theme
from ui.images import CoverImage
from ui.widgets import (
    BackgroundTask,
    Card,
    Divider,
    RoundedButton,
    ScrollableFrame,
    SectionHeader,
    clip_text,
    make_label,
    parent_bg,
    round_rect,
)

GENRE_LIMIT = 12
GENRE_COLUMNS = 4
TRACK_LIMIT = 10


def greeting_for_now():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def format_duration(seconds):
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "--:--"
    return "%d:%02d" % (seconds // 60, seconds % 60)


def normalize_genre(raw):
    if not isinstance(raw, dict):
        return None
    name = raw.get("name") or raw.get("title")
    genre_id = raw.get("id")
    if not name or genre_id == 0:
        return None
    return {"id": genre_id, "name": str(name), "raw": raw}


def normalize_track(raw):
    if not isinstance(raw, dict):
        return None
    artist = raw.get("artist")
    if isinstance(artist, dict):
        artist = artist.get("name")
    album = raw.get("album") if isinstance(raw.get("album"), dict) else {}
    return {
        "id": raw.get("id"),
        "title": raw.get("title") or raw.get("title_short") or "Untitled",
        "artist": artist or raw.get("artist_name") or "Unknown artist",
        "album": album.get("title") or raw.get("album_title") or "",
        "duration": raw.get("duration") or 0,
        "preview": raw.get("preview") or raw.get("preview_url") or "",
        "cover": album.get("cover_medium") or raw.get("cover") or "",
        "raw": raw,
    }


class GenreTile(tk.Frame):
    """Clickable genre tile — Frame wrapper so grid() works on Python 3.14."""

    def __init__(self, parent, genre, command):
        super().__init__(parent, bg=theme.CANVAS, cursor="hand2",
                         bd=0, highlightthickness=0)
        self._genre = genre
        self._command = command
        self._base = theme.accent_for(genre["name"])
        self._hover = False

        self._canvas = tk.Canvas(self, width=1, height=92,
                                 bg=theme.CANVAS, highlightthickness=0, bd=0,
                                 cursor="hand2")
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._draw)
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def _on_enter(self, _e):
        self._hover = True
        self._draw()

    def _on_leave(self, _e):
        self._hover = False
        self._draw()

    def _on_click(self, _e):
        self._command(self._genre)

    def _draw(self, _e=None):
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 10 or h < 10:
            return
        fill = theme.mix(self._base, theme.WHITE, 0.12) if self._hover else self._base
        self._canvas.delete("all")
        round_rect(self._canvas, 1, 1, w - 1, h - 1, 16, fill=fill, outline=fill)
        self._canvas.create_oval(w - 72, 14, w - 16, 70,
                                 fill=theme.mix(fill, theme.WHITE, 0.16), outline="")
        self._canvas.create_text(
            18, h / 2 - 8,
            text=clip_text(self._genre["name"], 22), anchor="w",
            width=max(60, w - 100), font=theme.font(13, "bold"), fill=theme.WHITE,
        )
        self._canvas.create_text(
            18, h - 20, text="Explore", anchor="w",
            font=theme.font(9), fill=theme.mix(fill, theme.WHITE, 0.75),
        )


class TrackRow(tk.Frame):
    def __init__(self, parent, index, track, on_play):
        super().__init__(parent, bg=theme.SURFACE)
        self._track = track
        self._on_play = on_play

        row = tk.Frame(self, bg=theme.SURFACE)
        row.pack(fill="x", padx=8, pady=10)

        make_label(
            row, str(index), 11, "bold", theme.MUTED,
            bg=theme.SURFACE, width=3, anchor="e",
        ).pack(side="left")
        CoverImage(row, track["cover"], 44, track["title"], radius=8,
                   bg=theme.SURFACE).pack(side="left", padx=(10, 14))

        info = tk.Frame(row, bg=theme.SURFACE)
        info.pack(side="left", fill="x", expand=True)
        make_label(info, clip_text(track["title"], 54), 11, "bold",
                   theme.TEXT, bg=theme.SURFACE, anchor="w").pack(fill="x")
        make_label(info, clip_text(track["artist"], 54), 10, "normal",
                   theme.SUBTEXT, bg=theme.SURFACE, anchor="w").pack(fill="x")

        RoundedButton(
            row, "Play", lambda: on_play(track),
            variant="soft", width=76, height=34, size=10, radius=10,
            backdrop=theme.SURFACE,
        ).pack(side="right", padx=(12, 0))
        make_label(
            row, format_duration(track["duration"]), 10, "normal",
            theme.SUBTEXT, bg=theme.SURFACE, width=6, anchor="e",
        ).pack(side="right")

        for widget in (self, row, info):
            widget.bind("<Double-Button-1>", lambda _e: on_play(track))


class HomePage(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.CANVAS)
        self.shell = shell
        self._tasks = BackgroundTask(self)
        self._loaded = False

        self.scroll = ScrollableFrame(self, bg=theme.CANVAS)
        self.scroll.pack(fill="both", expand=True)

        self.wrap = tk.Frame(self.scroll.body, bg=theme.CANVAS)
        self.wrap.pack(fill="both", expand=True, padx=(32, 28), pady=(8, 32))

        self._build_hero()
        self._build_quick_start()
        self._build_genre_section()
        self._build_tracks_section()

    @property
    def catalog(self):
        return self.shell.app.catalog

    def on_show(self, **_kwargs):
        if not self._loaded:
            self._loaded = True
            self._load_genres()
            self._load_tracks()

    def refresh(self):
        self._load_genres()
        self._load_tracks()

    def _build_hero(self):
        hero = Card(self.wrap, padding=32, fill=theme.PRIMARY, outline=theme.PRIMARY)
        hero.pack(fill="x")
        body = hero.body

        decor = tk.Canvas(body, width=220, height=150,
                          bg=theme.PRIMARY, highlightthickness=0, bd=0)
        decor.pack(side="right", padx=(24, 0))
        decor.create_oval(20, 0, 200, 180,
                          fill=theme.mix(theme.PRIMARY, theme.WHITE, 0.08), outline="")
        heights = (40, 78, 58, 110, 86, 124, 70, 96, 50)
        for index, height in enumerate(heights):
            x1 = 14 + index * 22
            color = theme.WHITE if index % 3 else theme.SECONDARY
            round_rect(decor, x1, 140 - height, x1 + 12, 140, 5, fill=color, outline="")

        text_col = tk.Frame(body, bg=theme.PRIMARY)
        text_col.pack(side="left", fill="both", expand=True)
        make_label(text_col, "DISCOVER", 9, "bold",
                   theme.INDIGO_200, bg=theme.PRIMARY, anchor="w").pack(fill="x")
        make_label(
            text_col,
            "%s, %s" % (greeting_for_now(), self.shell.display_name),
            24, "bold", theme.WHITE, bg=theme.PRIMARY, anchor="w",
        ).pack(fill="x", pady=(6, 0))
        make_label(
            text_col,
            "Dive into genres, find new artists and keep the music that moves you close at hand.",
            11, "normal", theme.INDIGO_100, bg=theme.PRIMARY,
            anchor="w", justify="left", wraplength=460,
        ).pack(fill="x", pady=(8, 20))

        actions = tk.Frame(text_col, bg=theme.PRIMARY)
        actions.pack(anchor="w")
        RoundedButton(
            actions, "Browse genres", lambda: self.shell.show_page("genres"),
            variant="outline", height=42, padx=26, backdrop=theme.PRIMARY,
        ).pack(side="left")
        RoundedButton(
            actions, "Search music", lambda: self.shell.show_page("search"),
            variant="secondary", height=42, padx=26, backdrop=theme.PRIMARY,
        ).pack(side="left", padx=(12, 0))

    def _build_quick_start(self):
        row = tk.Frame(self.wrap, bg=theme.CANVAS)
        row.pack(fill="x", pady=(24, 0))
        items = (
            ("Pick a genre",
             "Explore curated sounds from pop to jazz and everything between.",
             "Open genres", "genres", theme.PRIMARY),
            ("Find any track",
             "Search artists, albums and songs from the full catalog.",
             "Open search", "search", theme.SECONDARY),
            ("Build playlists",
             "Collect the tracks you love into playlists of your own.",
             "Open playlists", "playlists", theme.PRIMARY),
        )
        for index, (title, description, action, page, color) in enumerate(items):
            row.columnconfigure(index, weight=1, uniform="quick")
            card = Card(row, padding=20)
            card.grid(row=0, column=index, sticky="ew",
                      padx=(0, 12 if index < len(items) - 1 else 0))
            body = card.body
            tk.Frame(body, bg=color, width=28, height=4).pack(anchor="w")
            make_label(body, title, 12, "bold", theme.TEXT,
                       bg=theme.SURFACE, anchor="w").pack(fill="x", pady=(12, 4))
            make_label(body, description, 10, "normal", theme.SUBTEXT,
                       bg=theme.SURFACE, anchor="w", justify="left",
                       wraplength=230).pack(fill="x", pady=(0, 14))
            RoundedButton(
                body, action, lambda name=page: self.shell.show_page(name),
                variant="soft", height=34, size=10, padx=18, radius=10,
                backdrop=theme.SURFACE,
            ).pack(anchor="w")

    def _build_genre_section(self):
        SectionHeader(
            self.wrap, "Browse by genre", "Jump straight into a sound",
            action_text="View all", action=lambda: self.shell.show_page("genres"),
        ).pack(fill="x", pady=(32, 12))
        self.genre_box = tk.Frame(self.wrap, bg=theme.CANVAS)
        self.genre_box.pack(fill="x")
        self._render_message(self.genre_box, "Loading genres...")

    def _build_tracks_section(self):
        SectionHeader(
            self.wrap, "Trending now", "The most played tracks right now",
        ).pack(fill="x", pady=(32, 12))
        self.tracks_card = Card(self.wrap, padding=12)
        self.tracks_card.pack(fill="x")
        self.tracks_box = self.tracks_card.body
        self._render_message(self.tracks_box, "Loading trending tracks...")

    @staticmethod
    def _clear(container):
        for child in container.winfo_children():
            child.destroy()

    def _render_message(self, container, message, retry=None):
        self._clear(container)
        background = parent_bg(container)
        make_label(
            container, message, 11, "normal", theme.SUBTEXT,
            bg=background, anchor="w", justify="left", wraplength=560,
        ).pack(anchor="w", padx=8, pady=(6, 10 if retry else 6))
        if retry:
            RoundedButton(
                container, "Try again", retry,
                variant="outline", height=36, size=10, padx=18, radius=10,
                backdrop=background,
            ).pack(anchor="w", padx=8, pady=(0, 6))

    def _load_genres(self):
        self._render_message(self.genre_box, "Loading genres...")
        self._tasks.run(self.catalog.get_genres, self._render_genres, self._on_genres_error)

    def _load_tracks(self):
        self._render_message(self.tracks_box, "Loading trending tracks...")
        self._tasks.run(
            lambda: self.catalog.get_top_tracks(TRACK_LIMIT),
            self._render_tracks, self._on_tracks_error,
        )

    def _on_genres_error(self, error):
        message = str(error).strip() or "Genres could not be loaded."
        self._render_message(self.genre_box, message, retry=self._load_genres)

    def _on_tracks_error(self, error):
        message = str(error).strip() or "Trending tracks could not be loaded."
        self._render_message(self.tracks_box, message, retry=self._load_tracks)

    def _render_genres(self, raw_genres):
        genres = [g for g in (normalize_genre(item) for item in raw_genres or []) if g]
        genres = genres[:GENRE_LIMIT]
        if not genres:
            self._render_message(self.genre_box, "No genres available.",
                                 retry=self._load_genres)
            return
        self._clear(self.genre_box)
        for column in range(GENRE_COLUMNS):
            self.genre_box.columnconfigure(column, weight=1, uniform="genre")
        for index, genre in enumerate(genres):
            tile = GenreTile(self.genre_box, genre, self.shell.open_genre)
            tile.grid(
                row=index // GENRE_COLUMNS,
                column=index % GENRE_COLUMNS,
                sticky="ew",
                padx=(0 if index % GENRE_COLUMNS == 0 else 6,
                      0 if index % GENRE_COLUMNS == GENRE_COLUMNS - 1 else 6),
                pady=6,
            )

    def _render_tracks(self, raw_tracks):
        tracks = [t for t in (normalize_track(item) for item in raw_tracks or []) if t]
        if not tracks:
            self._render_message(self.tracks_box, "No trending tracks available.",
                                 retry=self._load_tracks)
            return
        self._clear(self.tracks_box)
        for index, track in enumerate(tracks[:TRACK_LIMIT], start=1):
            if index > 1:
                Divider(self.tracks_box).pack(fill="x", padx=8)
            TrackRow(self.tracks_box, index, track, self.shell.play_track).pack(fill="x")
