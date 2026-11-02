"""config.py - Constants used across the app."""

APP_NAME = "Himigo"
TAGLINE = "Find the sound that moves you"
WINDOW_SIZE = (1180, 740)
MIN_SIZE = (1000, 660)

DB_PATH = "himigo.db"            # auto-created on first run
LOGO_PATH = "assets/logo.png"
CACHE_DIR = "cache/covers"

API_BASE_URL = "https://api.deezer.com"   # no key needed
API_TIMEOUT = 10
CHART_LIMIT = 25
SEARCH_LIMIT = 25
HISTORY_LIMIT = 20

MIN_PASSWORD_LENGTH = 8
PBKDF2_ITERATIONS = 100_000
