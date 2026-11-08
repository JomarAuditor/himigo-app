"""api/deezer_client.py - Deezer public API client. (Week 15)

Base URL: https://api.deezer.com  (no key). Use one requests.Session,
timeouts and friendly errors. Do NOT store preview URLs; store track id only
and call get_track(id) right before playing.
"""
# import requests


class DeezerError(Exception):
    """Error message that is safe to show the user."""


def get_genres(): pass                       # /genre
def get_chart(genre_id=0, limit=25): pass    # /chart/{id}/tracks
def get_new_releases(limit=12): pass         # /editorial/0/releases
def search_tracks(query, limit=25): pass     # /search?q=
def get_track(track_id): pass                # /track/{id} (fresh preview)
def download_preview(url): pass              # MP3 bytes in memory
