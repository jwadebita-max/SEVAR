import re
from datetime import date, datetime


class ValidationError(ValueError):
    pass


def normalize_phone_number(phone):
    if not phone:
        raise ValidationError("Phone number is required")
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("00212"):
        digits = digits[2:]
    if digits.startswith("212"):
        local = digits[3:]
    elif digits.startswith("0"):
        local = digits[1:]
    else:
        local = digits
    if not re.fullmatch(r"[5-7]\d{8}", local):
        raise ValidationError("Use a valid Moroccan phone number")
    return f"+212{local}"


def validate_otp(otp):
    if not re.fullmatch(r"\d{6}", str(otp or "")):
        raise ValidationError("OTP must be 6 digits")
    return str(otp)


def required(value, field):
    if value is None or str(value).strip() == "":
        raise ValidationError(f"{field} is required")
    return str(value).strip()


def validate_role(value):
    value = required(value, "User type")
    if value not in {"buyer", "seller"}:
        raise ValidationError("User type must be buyer or seller")
    return value


def validate_language(value):
    value = required(value, "Language").upper()
    if value not in {"AR", "FR", "EN", "ES", "DE", "BER"}:
        raise ValidationError("Unsupported language")
    return value


def validate_gender(value):
    value = required(value, "Gender")
    if value not in {"male", "female"}:
        raise ValidationError("Gender must be male or female")
    return value


def validate_birthdate(value):
    value = required(value, "Birthdate")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError("Birthdate must be YYYY-MM-DD") from exc
    if parsed >= date.today():
        raise ValidationError("Birthdate must be in the past")
    return parsed


def validate_positive_number(value, field):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number") from exc
    if number <= 0:
        raise ValidationError(f"{field} must be positive")
    return number


def validate_int(value, field, minimum=None):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number") from exc
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} must be at least {minimum}")
    return number
