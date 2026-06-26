from flask import Blueprint, current_app, g, request

from ..decorators import current_user, login_required
from ..extensions import db
from ..services.auth_service import AuthService
from ..services.otp_service import OTPService
from ..utils.responses import error, success
from ..utils.validators import ValidationError, normalize_phone_number, validate_otp

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.post("/phone/request-otp")
def request_otp():
    data = request.get_json(silent=True) or {}
    try:
        phone = normalize_phone_number(data.get("phone_number") or data.get("phoneNumber"))
    except ValidationError as exc:
        return error(str(exc), 422)
    code, message = OTPService.create_otp(phone)
    if not code:
        return error(message, 429)
    payload = {"phone_number": phone}
    if current_app.config["DEBUG"] and current_app.config["DEV_SHOW_OTP"]:
        payload["development_otp"] = code
    return success("OTP generated", payload)


@auth_bp.post("/phone/verify-otp")
def verify_phone_otp():
    data = request.get_json(silent=True) or {}
    try:
        phone = normalize_phone_number(data.get("phone_number") or data.get("phoneNumber"))
        otp = validate_otp(data.get("otp"))
    except ValidationError as exc:
        return error(str(exc), 422)
    valid, message = OTPService.verify_otp(phone, otp)
    if not valid:
        return error(message, 401)
    user = AuthService.get_or_create_phone_user(phone)
    db.session.commit()
    AuthService.create_session(user, request.remote_addr, request.headers.get("User-Agent"))
    return success("OTP verified", {"user": user.to_dict(private=True), "onboarding_complete": user.onboarding_complete()})


@auth_bp.post("/logout")
@login_required()
def logout():
    AuthService.logout_current()
    return success("Logged out")


@auth_bp.get("/me")
def me():
    user = current_user()
    if not user:
        return error("Authentication required", 401)
    return success("Current user", {"user": user.to_dict(private=True)})
