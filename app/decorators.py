from functools import wraps

from flask import g, redirect, request, session, url_for

from .models import User, UserSession
from .utils.responses import error
from .utils.security import verify_secret
from datetime import datetime


def current_user():
    token = session.get("session_token")
    user_id = session.get("user_id")
    if not token or not user_id:
        return None
    sessions = UserSession.query.filter_by(user_id=user_id, revoked_at=None).all()
    now = datetime.utcnow()
    for stored in sessions:
        if stored.expires_at > now and verify_secret(stored.session_token_hash, token):
            return User.query.get(user_id)
    return None


def login_required(api=True):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            user = current_user()
            if not user:
                if api:
                    return error("Authentication required", 401)
                return redirect(url_for("pages.login"))
            g.current_user = user
            return fn(*args, **kwargs)
        return inner
    return wrapper


def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            user = current_user()
            if not user:
                return error("Authentication required", 401)
            if user.user_type != role:
                return error(f"{role.capitalize()} account required", 403)
            g.current_user = user
            return fn(*args, **kwargs)
        return inner
    return wrapper
