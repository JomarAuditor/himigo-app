"""database/db.py - SQLite connection, 5 tables, helper functions. (Week 14)

Tables: users, playlists, playlist_tracks, favorites, history
(see Section 6 of the progress report). Always use ? placeholders in SQL.
"""
# import sqlite3


class Database:
    def __init__(self, path):
        # TODO: connect, enable foreign keys, create tables
        pass

    def create_tables(self): pass            # TODO Week 14

    # users
    def create_user(self, username, email, password_hash, salt): pass
    def get_user_by_username(self, username): pass

    # playlists (Week 17)
    def create_playlist(self, user_id, name): pass
    def list_playlists(self, user_id): pass
    def rename_playlist(self, playlist_id, name): pass
    def delete_playlist(self, playlist_id): pass
    def add_track_to_playlist(self, playlist_id, track): pass
    def playlist_tracks(self, playlist_id): pass
    def move_playlist_track(self, row_id, direction): pass
    def remove_playlist_track(self, row_id): pass

    # favorites (Week 17)
    def add_favorite(self, user_id, track): pass
    def remove_favorite(self, user_id, track_id): pass
    def list_favorites(self, user_id): pass

    # history (Week 17)
    def add_history(self, user_id, track): pass
    def list_history(self, user_id, limit=20): pass
