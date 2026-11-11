"""Search page: type a query in the top bar and play results from Deezer."""

import tkinter as tk

from ui import theme
from ui.home_page import TrackRow, normalize_track
from ui.widgets import BackgroundTask, Card, Divider, ScrollableFrame, make_label

RESULT_LIMIT = 25


class SearchPage(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.CANVAS)
        self.shell = shell
        self._tasks = BackgroundTask(self)
        self._query = ""

        self.scroll = ScrollableFrame(self, bg=theme.CANVAS)
        self.scroll.pack(fill="both", expand=True)
        self.wrap = tk.Frame(self.scroll.body, bg=theme.CANVAS)
        self.wrap.pack(fill="both", expand=True, padx=(32, 28), pady=(8, 32))
        self._message("Search for an artist, album or track using the box above.")

    def on_show(self, **_kwargs):
        return

    def _clear(self):
        for child in self.wrap.winfo_children():
            child.destroy()

    def _message(self, text):
        self._clear()
        make_label(
            self.wrap,
            text,
            11,
            "normal",
            theme.SUBTEXT,
            bg=theme.CANVAS,
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(anchor="w", pady=8)

    def run_search(self, query):
        catalog = self.shell.app.catalog
        if not hasattr(catalog, "search_tracks"):
            self._message("Search is not available in this build.")
            return
        self._query = query
        self._message('Searching for "%s"...' % query)
        self._tasks.run(
            lambda: catalog.search_tracks(query, RESULT_LIMIT),
            lambda raw: self._render(query, raw),
            self._on_error,
        )

    def _on_error(self, error):
        self._message(str(error).strip() or "Search failed. Please try again.")

    def _render(self, query, raw_tracks):
        if query != self._query:
            return
        tracks = [t for t in (normalize_track(item) for item in raw_tracks or []) if t]
        if not tracks:
            self._message('No results for "%s". Try another artist or song.' % query)
            return
        self._clear()
        make_label(
            self.wrap,
            'Results for "%s"' % query,
            15,
            "bold",
            theme.TEXT,
            bg=theme.CANVAS,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))
        card = Card(self.wrap, padding=12)
        card.pack(fill="x")
        for index, track in enumerate(tracks, start=1):
            if index > 1:
                Divider(card.body).pack(fill="x", padx=8)
            TrackRow(card.body, index, track, self.shell.play_track).pack(fill="x")
