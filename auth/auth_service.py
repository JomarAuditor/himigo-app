"""auth/auth_service.py - Register, login, validation, salted hashing. (Week 14)

Uses hashlib.pbkdf2_hmac('sha256', ...) with a unique random salt per user.
Never store plain-text passwords.
"""
# import hashlib, os


def hash_password(password, salt=None):
    """Return (hex_hash, salt). TODO Week 14."""
    pass


def verify_password(password, stored_hash, salt):
    """Return True/False. TODO Week 14."""
    pass


def register_user(db, username, email, password, confirm):
    """Check empty fields, duplicate username, password length/match.
    Return (ok, message). TODO Week 14."""
    pass


def login_user(db, username, password):
    """Return (True, user_dict) or (False, error_message). TODO Week 14."""
    pass
