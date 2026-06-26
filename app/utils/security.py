import secrets

from werkzeug.security import check_password_hash, generate_password_hash


def generate_token():
    return secrets.token_urlsafe(48)


def hash_secret(value):
    return generate_password_hash(value, method="pbkdf2:sha256:30000")


def verify_secret(stored_hash, value):
    return check_password_hash(stored_hash, value)
