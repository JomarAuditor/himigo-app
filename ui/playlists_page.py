"""Playlists page."""

import tkinter as tk
from ui import theme
from ui.widgets import (
    Card, Divider, InitialTile, RoundedButton,
    SectionHeader, make_label, clip_text,
)


class PlaylistsPage(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.CANVAS, bd=0, highlightthickness=0)
        self.shell = shell

        wrap = tk.Frame(self, bg=theme.CANVAS)
        wrap.pack(fill="both", expand=True, padx=32, pady=16)

        SectionHeader(wrap, "Your Playlists", "Collections you have saved").pack(
            fill="x", pady=(0, 20))

        card = Card(wrap, padding=32)
        card.pack(fill="x")
        body = card.body

        InitialTile(body, "P", size=56, color=theme.PRIMARY,
                    backdrop=theme.SURFACE).pack(pady=(8, 16))
        make_label(body, "No playlists yet", 15, "bold",
                   theme.TEXT, bg=theme.SURFACE).pack()
        make_label(body, "Go to Search or Home, find a track you like\nand add it to a new playlist.",
                   11, "normal", theme.SUBTEXT, bg=theme.SURFACE,
                   justify="center").pack(pady=(8, 20))
        RoundedButton(body, "Browse music", lambda: shell.show_page("home"),
                      height=42, padx=28).pack()

    def on_show(self, **_kw):
        pass
