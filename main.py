"""Himigo - Genre & Music Discovery App (entry point)."""

import contextlib
import hashlib
import hmac
import importlib
import json
import secrets
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import tkinter as tk

from ui import theme
from ui.login_page import LoginPage
from ui.main_window import MainWindow
from ui.register_page import RegisterPage
from ui.widgets import center_window

APP_TITLE = "Himigo - Genre & Music Discovery"
DATA_DIR = Path.home() / ".himigo"


class LocalSettings:
    """Tiny JSON-backed key/value store for UI preferences."""

    def __init__(self, path):
        self.path = Path(path)
        self._data = {}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self._data = loaded
        except (OSError, ValueError):
            self._data = {}

    def get(self, key, default=""):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._data), encoding="utf-8")
        except OSError:
            pass


class LocalAuthService:
    """SQLite-backed authentication used when the project auth service is unavailable.

    Contract: register(username, email, password) -> user dict,
    login(identifier, password) -> user dict. Failures raise ValueError.
    """

    ITERATIONS = 120_000

    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._session() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS users ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "username TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                "email TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                "password_hash TEXT NOT NULL, "
                "salt TEXT NOT NULL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    @contextlib.contextmanager
    def _session(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _hash(self, password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), self.ITERATIONS
        ).hex()

    def register(self, username, email, password):
        username = (username or "").strip()
        email = (email or "").strip()
        if not username or not email or not password:
            raise ValueError("Username, email and password are required.")
        salt = secrets.token_hex(16)
        password_hash = self._hash(password, salt)
        with self._session() as conn:
            taken = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if taken:
                raise ValueError("That username is already taken.")
            used = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if used:
                raise ValueError("An account with that email already exists.")
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, salt),
            )
            user_id = cursor.lastrowid
        return {"id": user_id, "username": username, "email": email}

    def login(self, identifier, password):
        identifier = (identifier or "").strip()
        with self._session() as conn:
            row = conn.execute(
                "SELECT id, username, email, password_hash, salt FROM users "
                "WHERE username = ? OR email = ?",
                (identifier, identifier),
            ).fetchone()
        if row is None:
            raise ValueError("Incorrect username or password.")
        user_id, username, email, stored_hash, salt = row
        candidate = self._hash(password or "", salt)
        if not hmac.compare_digest(candidate, stored_hash):
            raise ValueError("Incorrect username or password.")
        return {"id": user_id, "username": username, "email": email}


class DeezerCatalog:
    """Read-only client for the public Deezer API.

    Contract: get_genres() -> list of genre dicts,
    get_top_tracks(limit) -> list of track dicts.
    """

    BASE_URL = "https://api.deezer.com"

    def _get(self, path, **params):
        query = urllib.parse.urlencode(params)
        url = self.BASE_URL + path + ("?" + query if query else "")
        request = urllib.request.Request(url, headers={"User-Agent": "Himigo/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError) as exc:
            raise ConnectionError(
                "Could not reach the music catalog. Check your internet connection and try again."
            ) from exc
        if isinstance(payload, dict) and "error" in payload:
            raise ConnectionError(
                "The music catalog returned an error. Please try again."
            )
        return payload

    def get_genres(self):
        return self._get("/genre").get("data", [])

    def get_top_tracks(self, limit=10):
        return self._get("/chart/0/tracks", limit=limit).get("data", [])


def resolve_service(module_name, class_name, required_methods):
    """Instantiate a project service if it exists and exposes the expected methods."""
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    service_class = getattr(module, class_name, None)
    if service_class is None:
        return None
    try:
        instance = service_class()
    except Exception:
        return None
    if all(callable(getattr(instance, name, None)) for name in required_methods):
        return instance
    return None


class HimigoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        theme.enable_high_dpi()
        self.title(APP_TITLE)
        theme.apply_theme(self)
        center_window(self, 1200, 780)
        self.minsize(1040, 720)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.settings = LocalSettings(DATA_DIR / "settings.json")
        self.auth_service = resolve_service(
            "auth.auth_service", "AuthService", ("register", "login")
        ) or LocalAuthService(DATA_DIR / "himigo_users.db")
        self.catalog = (
            resolve_service(
                "api.deezer_client", "DeezerClient", ("get_genres", "get_top_tracks")
            )
            or DeezerCatalog()
        )
        self.player = resolve_service(
            "audio.player", "AudioPlayer", ("play", "pause", "stop")
        )
        self.current_user = None
        self._view = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_login(prefill=self.settings.get("last_username", ""))

    def _swap_view(self, factory):
        if self._view is not None:
            if hasattr(self._view, "shutdown"):
                self._view.shutdown()
            self._view.destroy()
        self._view = factory(self)
        self._view.pack(fill="both", expand=True)

    def show_login(self, prefill="", notice=""):
        self.current_user = None
        self._swap_view(
            lambda root: LoginPage(root, self, prefill=prefill, notice=notice)
        )

    def show_register(self):
        self._swap_view(lambda root: RegisterPage(root, self))

    def show_main(self, user):
        self.current_user = user
        self._swap_view(lambda root: MainWindow(root, self, user))

    def logout(self):
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
        self.show_login(
            prefill=self.settings.get("last_username", ""),
            notice="You have been signed out.",
        )

    def on_close(self):
        if self._view is not None and hasattr(self._view, "shutdown"):
            self._view.shutdown()
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
        self.destroy()


def main():
    app = HimigoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
