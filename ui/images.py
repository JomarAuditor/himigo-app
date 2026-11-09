"""Album cover loading: downloads in the background, caches on disk, shows in Tk."""

import hashlib
import io
import queue
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageTk

from ui import theme
from ui.widgets import parent_bg

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "covers"


class ImageLoader:
    def __init__(self, root):
        self.root = root
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._done = queue.Queue()
        self._photos = {}
        self._session = requests.Session()
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self.root.after(100, self._poll)

    def request(self, url, size, radius, callback):
        key = (url, size, radius)
        photo = self._photos.get(key)
        if photo is not None:
            callback(photo)
            return
        self._pool.submit(self._work, key, callback)

    def _fetch_bytes(self, url):
        path = CACHE_DIR / (hashlib.md5(url.encode("utf-8")).hexdigest() + ".img")
        if path.exists():
            return path.read_bytes()
        response = self._session.get(url, timeout=10)
        response.raise_for_status()
        try:
            path.write_bytes(response.content)
        except OSError:
            pass
        return response.content

    def _work(self, key, callback):
        url, size, radius = key
        try:
            image = Image.open(io.BytesIO(self._fetch_bytes(url))).convert("RGBA")
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, size - 1, size - 1), radius=radius, fill=255
            )
            image.putalpha(mask)
            self._done.put((key, image, callback))
        except Exception:
            return

    def _poll(self):
        try:
            while True:
                try:
                    key, image, callback = self._done.get_nowait()
                except queue.Empty:
                    break
                photo = ImageTk.PhotoImage(image, master=self.root)
                self._photos[key] = photo
                try:
                    callback(photo)
                except tk.TclError:
                    pass
            self.root.after(100, self._poll)
        except tk.TclError:
            return

    def placeholder(self, size, radius, color):
        key = ("placeholder", size, radius, color)
        photo = self._photos.get(key)
        if photo is None:
            image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            ImageDraw.Draw(image).rounded_rectangle(
                (0, 0, size - 1, size - 1), radius=radius, fill=color
            )
            photo = ImageTk.PhotoImage(image, master=self.root)
            self._photos[key] = photo
        return photo


_loader = None


def get_loader(widget):
    global _loader
    root = widget.winfo_toplevel()
    if _loader is None or _loader.root is not root:
        _loader = ImageLoader(root)
    return _loader


class CoverImage(tk.Label):
    """Square album cover. Shows a colored tile with an initial until the image loads."""

    def __init__(self, parent, url, size=44, label="", radius=10, bg=None):
        super().__init__(
            parent,
            bd=0,
            highlightthickness=0,
            bg=bg if bg is not None else parent_bg(parent, theme.SURFACE),
            compound="center",
            fg=theme.WHITE,
            font=theme.font(max(9, int(size * 0.3)), "bold"),
        )
        self._size = size
        self._radius = radius
        self._token = None
        self._photo = None
        self.set_cover(url, label)

    @staticmethod
    def _initial(text):
        for char in str(text or ""):
            if char.isalnum():
                return char.upper()
        return "?"

    def set_cover(self, url, label=""):
        loader = get_loader(self)
        token = object()
        self._token = token
        self._photo = loader.placeholder(
            self._size, self._radius, theme.accent_for(label or url or "H")
        )
        self.configure(image=self._photo, text=self._initial(label))
        if url:
            loader.request(
                url, self._size, self._radius,
                lambda photo, t=token: self._apply(photo, t)
            )

    def _apply(self, photo, token):
        if token is not self._token or not self.winfo_exists():
            return
        self._photo = photo
        self.configure(image=photo, text="")
