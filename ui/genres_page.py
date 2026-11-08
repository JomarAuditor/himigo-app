"""Genres page."""

import tkinter as tk
from ui import theme
from ui.widgets import (
    BackgroundTask, ScrollableFrame, SectionHeader,
    make_label, clip_text, round_rect, parent_bg,
)


def normalize_genre(raw):
    if not isinstance(raw, dict):
        return None
    name = raw.get("name") or raw.get("title")
    genre_id = raw.get("id")
    if not name or genre_id == 0:
        return None
    return {"id": genre_id, "name": str(name), "raw": raw}


class GenreTile(tk.Frame):
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
        self._canvas.create_text(18, h / 2 - 8,
                                 text=clip_text(self._genre["name"], 22), anchor="w",
                                 width=max(60, w - 100),
                                 font=theme.font(13, "bold"), fill=theme.WHITE)
        self._canvas.create_text(18, h - 20, text="Explore", anchor="w",
                                 font=theme.font(9),
                                 fill=theme.mix(fill, theme.WHITE, 0.75))


class GenresPage(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.CANVAS, bd=0, highlightthickness=0)
        self.shell = shell
        self._tasks = BackgroundTask(self)
        self._loaded = False

        self.scroll = ScrollableFrame(self, bg=theme.CANVAS)
        self.scroll.pack(fill="both", expand=True)
        self.wrap = tk.Frame(self.scroll.body, bg=theme.CANVAS)
        self.wrap.pack(fill="both", expand=True, padx=32, pady=(8, 32))

        SectionHeader(self.wrap, "All Genres", "Pick a sound and dive in").pack(
            fill="x", pady=(8, 16))
        self._grid = tk.Frame(self.wrap, bg=theme.CANVAS)
        self._grid.pack(fill="x")
        make_label(self._grid, "Loading genres…", 11, "normal",
                   theme.SUBTEXT, bg=theme.CANVAS).pack(anchor="w", pady=8)

    @property
    def catalog(self):
        return self.shell.app.catalog

    def on_show(self, **_kw):
        if not self._loaded:
            self._loaded = True
            self._load()

    def _load(self):
        self._tasks.run(self.catalog.get_genres, self._render, self._error)

    def _error(self, exc):
        for w in self._grid.winfo_children():
            w.destroy()
        make_label(self._grid, str(exc) or "Could not load genres.", 11,
                   "normal", theme.DANGER, bg=theme.CANVAS).pack(anchor="w", pady=8)

    def _render(self, raw):
        genres = [g for g in (normalize_genre(r) for r in (raw or [])) if g]
        for w in self._grid.winfo_children():
            w.destroy()
        if not genres:
            make_label(self._grid, "No genres available.", 11, "normal",
                       theme.SUBTEXT, bg=theme.CANVAS).pack(anchor="w", pady=8)
            return
        cols = 4
        for i in range(cols):
            self._grid.columnconfigure(i, weight=1, uniform="g")
        for i, genre in enumerate(genres):
            tile = GenreTile(self._grid, genre, self.shell.open_genre)
            tile.grid(row=i // cols, column=i % cols, sticky="ew",
                      padx=(0 if i % cols == 0 else 6, 0 if i % cols == cols - 1 else 6),
                      pady=6)

    def open_genre(self, genre):
        pass  # could drill down to tracks
