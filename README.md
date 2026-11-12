# Himigo - Genre & Music Discovery App

Himigo (from the Filipino word *himig*, "melody") is a desktop music discovery app built with Python and Tkinter. Users sign in, browse trending music and genres from the Deezer catalog, search for songs, and play 30-second previews inside the app.

Course: ITL313-18 (SIA 2 LAB) - Final Term Mini Project, Option 3A.2 Music and Audio.
Status as of November 12, 2026: Week 2 of the project.

## Quick start

1. Install Python 3.12 or newer (tick "Add Python to PATH").
2. Open a terminal INSIDE the project folder (the one that contains `main.py`).
3. Install dependencies and run:

```
pip install -r requirements.txt
py main.py
```

## Progress

### Week 1 - Foundation (done)
- Chose the project and planned the folder structure.
- Built the design system (colors, fonts, spacing) in `ui/theme.py`.
- Built reusable widgets in `ui/widgets.py` (cards, buttons, form fields, toast).
- Set up the SQLite database layer and the authentication service (salted password hashing).

### Week 2 - Screens and API (in progress)
- Done: Login page, Registration page with validation and password strength meter.
- Done: Main window (sidebar, top search bar, page area, player bar) and Home page (greeting, quick links, genre tiles, trending tracks).
- Done: Fixed layout and widget bugs found when running on Python 3.14.
- Done: Deezer API client (genres, charts, search).
- Done: Audio player for previews, album cover loading with disk cache, working search.

### Next steps Week 3:
- Genres page: click a genre to see and play its top tracks.
- Playlists: create, rename, delete, add and remove songs (SQLite).
- Favorites (heart button) and listening history.

## Folder and file guide

| Path | What it does |
|------|--------------|
| `main.py` | Entry point. Creates the window, sets up services and switches between Login, Register and the Main window. |
| `config.py` | Constants: app name, window size, API base URL, cache folder. |
| `requirements.txt` | Python packages the app needs (requests, Pillow, pygame). |

### `database/`
| File | Purpose |
|------|---------|
| `db.py` | Opens the SQLite connection, creates tables, provides helper functions for users, playlists, songs, favorites and history. |

### `auth/`
| File | Purpose |
|------|---------|
| `auth_service.py` | `register()` validates input, creates a random salt and stores a hashed password. `login()` re-hashes the typed password and compares it. |

### `api/`
| File | Purpose |
|------|---------|
| `deezer_client.py` | Talks to the public Deezer API. Methods: `get_genres`, `get_top_tracks`, `get_genre_tracks`, `search_tracks`. |

### `audio/`
| File | Purpose |
|------|---------|
| `player.py` | `AudioPlayer`: downloads a preview in a background thread and plays it with pygame. Methods: `play`, `pause`, `resume`, `stop`, `set_volume`, `get_position`. |

### `ui/`
| File | Purpose |
|------|---------|
| `theme.py` | Colors, fonts and ttk styles. |
| `widgets.py` | Shared building blocks: Card, RoundedButton, FormField, ScrollableFrame, Toast, BackgroundTask. |
| `images.py` | Loads album covers in the background, caches them in `cache/covers/`, provides the `CoverImage` widget. |
| `login_page.py` | Sign-in form with show/hide password and remember username. |
| `register_page.py` | Account creation with live validation and password strength meter. |
| `main_window.py` | Layout shell: sidebar navigation, top search bar, page area, player bar. |
| `home_page.py` | Greeting, quick links, genre tiles, trending tracks with covers. |
| `genres_page.py` | All genres (top tracks per genre coming in Week 3). |
| `search_page.py` | Deezer search results with play buttons. |
| `playlists_page.py` | User playlists (full feature coming in Week 3). |
| `player_bar.py` | Bottom bar: cover, title, play/pause, progress bar, volume slider. |

## Troubleshooting
- `py main.py` does nothing: you are in the outer folder. `cd himigo-app` first.
- No sound: run `pip install pygame` and check your system volume.
- No covers or tracks: check your internet connection (Deezer needs it).

## Team
Group of 2. Data source: Deezer public API. Previews are 30 seconds by Deezer's design.
