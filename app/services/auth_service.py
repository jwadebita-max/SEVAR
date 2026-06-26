from datetime import datetime, timedelta

from flask import current_app, session

from ..extensions import db
from ..models import User, UserSession
from ..utils.security import generate_token, hash_secret


class AuthService:
    @staticmethod
    def get_or_create_phone_user(phone_number):
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            user = User(phone_number=phone_number, auth_method="phone", is_verified=True)
            db.session.add(user)
        user.is_verified = True
        user.last_login = datetime.utcnow()
        db.session.flush()
        return user

    @staticmethod
    def create_session(user, ip_address=None, user_agent=None):
        raw_token = generate_token()
        expires_at = datetime.utcnow() + timedelta(days=current_app.config["SESSION_EXPIRY_DAYS"])
        stored = UserSession(
            user_id=user.id,
            session_token_hash=hash_secret(raw_token),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:255],
        )
        db.session.add(stored)
        db.session.commit()
        session.permanent = True
        session["user_id"] = user.id
        session["session_token"] = raw_token
        return stored

    @staticmethod
    def logout_current():
        token = session.get("session_token")
        user_id = session.get("user_id")
        if user_id and token:
            from ..utils.security import verify_secret
            for stored in UserSession.query.filter_by(user_id=user_id, revoked_at=None).all():
                if verify_secret(stored.session_token_hash, token):
                    stored.revoked_at = datetime.utcnow()
        session.clear()
        db.session.commit()
