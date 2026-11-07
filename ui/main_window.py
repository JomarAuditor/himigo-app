"""Authenticated application shell: sidebar, content frame, player bar."""

import importlib
import tkinter as tk

from ui import theme
from ui.widgets import (
    Divider,
    InitialTile,
    RoundedButton,
    Toast,
    clip_text,
    make_label,
    parent_bg,
)

PAGE_META = {
    "home":      ("Home",      "Fresh picks and what is trending right now"),
    "genres":    ("Genres",    "Explore music by sound and style"),
    "search":    ("Search",    "Find artists, albums and tracks"),
    "playlists": ("Playlists", "Your saved collections"),
}

NAV_ITEMS = [
    ("home",      "Home"),
    ("genres",    "Genres"),
    ("search",    "Search"),
    ("playlists", "Playlists"),
]

PAGE_MODULES = {
    "home":      ("ui.home_page",      "HomePage"),
    "genres":    ("ui.genres_page",    "GenresPage"),
    "search":    ("ui.search_page",    "SearchPage"),
    "playlists": ("ui.playlists_page", "PlaylistsPage"),
}


def _load_class(module_name, class_name):
    try:
        mod = importlib.import_module(module_name)
        return getattr(mod, class_name, None)
    except Exception:
        return None


def read_field(source, key, default=""):
    if isinstance(source, dict):
        return source.get(key, default) or default
    return getattr(source, key, default) or default


class NavItem(tk.Frame):
    def __init__(self, parent, text, command):
        super().__init__(parent, bg=theme.SURFACE, cursor="hand2")
        self._command = command
        self._active = False
        self._hover = False

        self._indicator = tk.Frame(self, bg=theme.SURFACE, width=4)
        self._indicator.pack(side="left", fill="y")

        self._label = tk.Label(
            self, text=text, font=theme.font(11),
            fg=theme.SUBTEXT, bg=theme.SURFACE,
            anchor="w", padx=16, pady=11, cursor="hand2",
        )
        self._label.pack(side="left", fill="x", expand=True)

        for w in (self, self._label, self._indicator):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", lambda _e: self._command())

    def set_active(self, active):
        self._active = active
        self._paint()

    def _on_enter(self, _e):
        self._hover = True
        self._paint()

    def _on_leave(self, _e):
        self._hover = False
        self._paint()

    def _paint(self):
        if self._active:
            bg, fg, weight = theme.PRIMARY_SOFT, theme.PRIMARY, "bold"
        elif self._hover:
            bg, fg, weight = theme.CANVAS, theme.TEXT, "normal"
        else:
            bg, fg, weight = theme.SURFACE, theme.SUBTEXT, "normal"
        self.configure(bg=bg)
        self._label.configure(bg=bg, fg=fg, font=theme.font(11, weight))
        self._indicator.configure(bg=theme.PRIMARY if self._active else bg)


class PlaceholderPage(tk.Frame):
    def __init__(self, parent, shell, name):
        super().__init__(parent, bg=theme.CANVAS)
        title = PAGE_META[name][0]
        make_label(self, title, 20, "bold", theme.TEXT, bg=theme.CANVAS, anchor="w").pack(
            anchor="w", padx=40, pady=(40, 8)
        )
        make_label(self, "This section is coming soon.", 11, "normal", theme.SUBTEXT,
                   bg=theme.CANVAS, anchor="w").pack(anchor="w", padx=40)
        RoundedButton(self, "Back to Home", lambda: shell.show_page("home"),
                      height=42, padx=28).pack(anchor="w", padx=40, pady=20)


class NowPlayingBar(tk.Frame):
    def __init__(self, parent, shell):
        super().__init__(parent, bg=theme.SURFACE, height=72, bd=0, highlightthickness=0)
        self.shell = shell
        self._track = None
        self._playing = False
        self.pack_propagate(False)

        tk.Frame(self, bg=theme.BORDER, height=1).pack(side="top", fill="x")
        row = tk.Frame(self, bg=theme.SURFACE)
        row.pack(fill="both", expand=True, padx=24)

        self._tile = InitialTile(row, "H", size=44, color=theme.MUTED, backdrop=theme.SURFACE)
        self._tile.pack(side="left")

        info = tk.Frame(row, bg=theme.SURFACE)
        info.pack(side="left", padx=12)
        self._title_lbl = make_label(info, "Nothing playing", 11, "bold",
                                     theme.TEXT, bg=theme.SURFACE, anchor="w")
        self._title_lbl.pack(anchor="w")
        self._sub_lbl = make_label(info, "Choose a track to start listening", 10,
                                   "normal", theme.SUBTEXT, bg=theme.SURFACE, anchor="w")
        self._sub_lbl.pack(anchor="w")

        self._btn = RoundedButton(row, "Play", self._toggle,
                                  width=88, height=36, backdrop=theme.SURFACE)
        self._btn.pack(side="right")
        self._btn.set_state("disabled")

    def set_track(self, track):
        self._track = track
        self._title_lbl.configure(text=clip_text(track.get("title", "Untitled"), 60))
        artist = track.get("artist", "")
        album = track.get("album", "")
        sub = artist + (" — " + album if album else "")
        self._sub_lbl.configure(text=clip_text(sub, 70))
        self._tile.set_text(track.get("title", "?"))
        self._btn.set_state("normal")
        self._do_play()

    def _player(self):
        return getattr(self.shell.app, "player", None)

    def _do_play(self):
        url = (self._track or {}).get("preview", "")
        player = self._player()
        if not url:
            self._playing = False
            self._btn.set_text("Play")
            self.shell.show_toast("No preview available for this track.", "info")
            return
        if player is None:
            self._playing = False
            self._btn.set_text("Play")
            self.shell.show_toast("Audio not connected in this build.", "info")
            return
        try:
            player.play(url)
            self._playing = True
            self._btn.set_text("Pause")
        except Exception as exc:
            self._playing = False
            self._btn.set_text("Play")
            self.shell.show_toast("Playback failed: %s" % exc, "error")

    def _toggle(self):
        if not self._track:
            return
        player = self._player()
        if self._playing:
            try:
                if player:
                    player.pause()
            except Exception:
                pass
            self._playing = False
            self._btn.set_text("Play")
        else:
            self._do_play()

    def stop(self):
        player = self._player()
        if player and self._playing:
            try:
                player.stop()
            except Exception:
                pass
        self._playing = False


class MainWindow(tk.Frame):
    def __init__(self, parent, app, user):
        super().__init__(parent, bg=theme.CANVAS, bd=0, highlightthickness=0)
        self.app = app
        self.user = user
        self.toast = Toast(self)
        self._pages = {}
        self._nav_items = {}
        self._current = None

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()
        self._build_player()

        self.show_page("home")

    @property
    def display_name(self):
        return read_field(self.user, "username", "Listener")

    @property
    def email(self):
        return read_field(self.user, "email", "")

    def _build_sidebar(self):
        outer = tk.Frame(self, bg=theme.SURFACE, width=theme.SIDEBAR_WIDTH + 1,
                         bd=0, highlightthickness=0)
        outer.grid(row=0, column=0, sticky="ns")
        outer.pack_propagate(False)

        tk.Frame(outer, bg=theme.BORDER, width=1).pack(side="right", fill="y")
        sidebar = tk.Frame(outer, bg=theme.SURFACE, bd=0, highlightthickness=0)
        sidebar.pack(side="left", fill="both", expand=True)

        # Brand
        brand = tk.Frame(sidebar, bg=theme.SURFACE)
        brand.pack(fill="x", padx=20, pady=(24, 20))
        InitialTile(brand, "H", size=38, color=theme.PRIMARY,
                    backdrop=theme.SURFACE).pack(side="left")
        brand_text = tk.Frame(brand, bg=theme.SURFACE)
        brand_text.pack(side="left", padx=10)
        make_label(brand_text, "Himigo", 16, "bold",
                   theme.TEXT, bg=theme.SURFACE).pack(anchor="w")
        make_label(brand_text, "Music discovery", 9, "normal",
                   theme.SUBTEXT, bg=theme.SURFACE).pack(anchor="w")

        make_label(sidebar, "MENU", 9, "bold", theme.MUTED,
                   bg=theme.SURFACE, anchor="w").pack(fill="x", padx=24, pady=(0, 6))

        for key, text in NAV_ITEMS:
            item = NavItem(sidebar, text, lambda k=key: self.show_page(k))
            item.pack(fill="x", padx=10, pady=1)
            self._nav_items[key] = item

        # Footer
        footer = tk.Frame(sidebar, bg=theme.SURFACE)
        footer.pack(side="bottom", fill="x")
        Divider(footer).pack(fill="x")

        profile = tk.Frame(footer, bg=theme.SURFACE)
        profile.pack(fill="x", padx=16, pady=(14, 8))
        InitialTile(profile, self.display_name, size=38, shape="circle",
                    color=theme.SECONDARY, backdrop=theme.SURFACE).pack(side="left")
        identity = tk.Frame(profile, bg=theme.SURFACE)
        identity.pack(side="left", padx=10)
        make_label(identity, clip_text(self.display_name, 18), 10, "bold",
                   theme.TEXT, bg=theme.SURFACE, anchor="w").pack(anchor="w")
        if self.email:
            make_label(identity, clip_text(self.email, 24), 9, "normal",
                       theme.SUBTEXT, bg=theme.SURFACE, anchor="w").pack(anchor="w")

        RoundedButton(footer, "Sign out", self.app.logout,
                      variant="outline", height=36, size=10,
                      backdrop=theme.SURFACE).pack(fill="x", padx=16, pady=(0, 16))

    def _build_content(self):
        content = tk.Frame(self, bg=theme.CANVAS, bd=0, highlightthickness=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        top = tk.Frame(content, bg=theme.CANVAS)
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 6))
        heading = tk.Frame(top, bg=theme.CANVAS)
        heading.pack(side="left")
        self._title_lbl = make_label(heading, "", 22, "bold",
                                     theme.TEXT, bg=theme.CANVAS, anchor="w")
        self._title_lbl.pack(anchor="w")
        self._sub_lbl = make_label(heading, "", 10, "normal",
                                   theme.SUBTEXT, bg=theme.CANVAS, anchor="w")
        self._sub_lbl.pack(anchor="w")
        self._build_search(top).pack(side="right")

        self._host = tk.Frame(content, bg=theme.CANVAS, bd=0, highlightthickness=0)
        self._host.grid(row=1, column=0, sticky="nsew")
        self._host.rowconfigure(0, weight=1)
        self._host.columnconfigure(0, weight=1)

    def _build_search(self, parent):
        ring = tk.Frame(parent, bg=theme.BORDER)
        inner = tk.Frame(ring, bg=theme.SURFACE)
        inner.pack(fill="x", padx=1, pady=1)
        self._search_var = tk.StringVar()
        RoundedButton(inner, "Search", self._do_search,
                      height=32, size=10, padx=16, radius=8,
                      backdrop=theme.SURFACE).pack(side="right", padx=4, pady=4)
        entry = tk.Entry(inner, textvariable=self._search_var, width=28,
                         relief="flat", bd=0, highlightthickness=0,
                         bg=theme.SURFACE, fg=theme.TEXT,
                         insertbackground=theme.PRIMARY, font=theme.font(11))
        entry.pack(side="left", fill="x", expand=True, padx=(12, 4), ipady=8)
        entry.bind("<FocusIn>",  lambda _e: ring.configure(bg=theme.PRIMARY))
        entry.bind("<FocusOut>", lambda _e: ring.configure(bg=theme.BORDER))
        entry.bind("<Return>",   lambda _e: self._do_search())
        return ring

    def _build_player(self):
        bar_cls = _load_class("ui.player_bar", "PlayerBar") or NowPlayingBar
        self.player_bar = bar_cls(self, self)
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _get_page(self, name):
        if name in self._pages:
            return self._pages[name]
        mod, cls = PAGE_MODULES[name]
        page_cls = _load_class(mod, cls)
        if page_cls is None:
            page = PlaceholderPage(self._host, self, name)
        else:
            page = page_cls(self._host, self)
        page.grid(row=0, column=0, sticky="nsew")
        self._pages[name] = page
        return page

    def show_page(self, name, **kwargs):
        if name not in PAGE_META:
            return
        page = self._get_page(name)
        page.tkraise()
        self._current = name
        for k, item in self._nav_items.items():
            item.set_active(k == name)
        title, subtitle = PAGE_META[name]
        self._title_lbl.configure(text=title)
        self._sub_lbl.configure(text=subtitle)
        if hasattr(page, "on_show"):
            page.on_show(**kwargs)

    def open_genre(self, genre):
        self.show_page("genres")
        page = self._pages.get("genres")
        if page and hasattr(page, "open_genre"):
            page.open_genre(genre)

    def run_search(self, query):
        query = query.strip()
        if not query:
            self.show_toast("Type something to search.", "info")
            return
        self.show_page("search")
        page = self._pages.get("search")
        if page and hasattr(page, "run_search"):
            page.run_search(query)

    def _do_search(self):
        self.run_search(self._search_var.get())

    def play_track(self, track):
        if hasattr(self.player_bar, "set_track"):
            self.player_bar.set_track(track)

    def show_toast(self, message, kind="info"):
        self.toast.show(message, kind)

    def shutdown(self):
        if hasattr(self.player_bar, "stop"):
            try:
                self.player_bar.stop()
            except Exception:
                pass
        self.toast.dismiss()
