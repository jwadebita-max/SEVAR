import random
from datetime import datetime, timedelta

from flask import current_app

from ..extensions import db
from ..models import OtpCode
from ..utils.security import hash_secret, verify_secret


class OTPService:
    @staticmethod
    def create_otp(phone_number):
        recent = (
            OtpCode.query.filter_by(phone_number=phone_number, used_at=None)
            .order_by(OtpCode.created_at.desc())
            .first()
        )
        if recent and (datetime.utcnow() - recent.created_at).total_seconds() < 30:
            return None, "Please wait before requesting another OTP"
        code = f"{random.randint(0, 999999):06d}"
        expires = datetime.utcnow() + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
        db.session.add(OtpCode(phone_number=phone_number, otp_code_hash=hash_secret(code), expires_at=expires))
        db.session.commit()
        print(f"SEVAR development OTP for {phone_number[-4:]}: {code}")
        return code, "OTP generated"

    @staticmethod
    def verify_otp(phone_number, otp):
        record = (
            OtpCode.query.filter_by(phone_number=phone_number, used_at=None)
            .order_by(OtpCode.created_at.desc())
            .first()
        )
        if not record:
            return False, "No active OTP"
        if record.expires_at < datetime.utcnow():
            return False, "OTP expired"
        if record.attempt_count >= 5:
            return False, "Too many OTP attempts"
        record.attempt_count += 1
        if not verify_secret(record.otp_code_hash, otp):
            db.session.commit()
            return False, "Invalid OTP"
        record.used_at = datetime.utcnow()
        db.session.commit()
        return True, "OTP verified"
