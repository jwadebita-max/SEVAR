from flask import Blueprint, g, request

from ..decorators import login_required
from ..extensions import db
from ..models import SellerProfile, User
from ..utils.responses import error, success
from ..utils.validators import (
    ValidationError,
    required,
    validate_birthdate,
    validate_gender,
    validate_int,
    validate_language,
    validate_role,
)

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.get("/profile")
@login_required()
def get_profile():
    return success("Profile loaded", {"user": g.current_user.to_dict(private=True)})


@users_bp.put("/profile")
@login_required()
def update_profile():
    user = g.current_user
    data = request.get_json(silent=True) or {}
    try:
        if "full_name" in data or "fullName" in data:
            user.full_name = required(data.get("full_name") or data.get("fullName"), "Full name")
        if "user_type" in data or "userType" in data:
            user.user_type = validate_role(data.get("user_type") or data.get("userType"))
            if user.user_type == "seller" and not user.seller_profile:
                db.session.add(SellerProfile(user=user))
        if "location" in data:
            user.location = required(data.get("location"), "Location")
        if "city" in data:
            user.city = required(data.get("city"), "City")
        elif user.location and not user.city:
            user.city = user.location.split(",")[0].strip()
        if "birthdate" in data:
            user.birthdate = validate_birthdate(data.get("birthdate"))
        if "gender" in data:
            user.gender = validate_gender(data.get("gender"))
        if "citizenship" in data:
            user.citizenship = required(data.get("citizenship"), "Citizenship")
    except ValidationError as exc:
        return error(str(exc), 422)
    db.session.commit()
    return success("Profile updated", {"user": user.to_dict(private=True)})


@users_bp.put("/seller-info")
@login_required()
def update_seller_info():
    user = g.current_user
    if user.user_type != "seller":
        return error("Seller account required", 403)
    profile = user.seller_profile or SellerProfile(user=user)
    data = request.get_json(silent=True) or {}
    try:
        if "service_category_id" in data or "serviceCategoryId" in data:
            profile.service_category_id = validate_int(data.get("service_category_id") or data.get("serviceCategoryId"), "Service category", 1)
        if "years_experience" in data or "yearsExperience" in data:
            profile.years_experience = validate_int(data.get("years_experience") or data.get("yearsExperience"), "Years experience", 0)
        if "service_description" in data or "serviceDescription" in data:
            profile.service_description = required(data.get("service_description") or data.get("serviceDescription"), "Service description")
        if "primary_language" in data or "primaryLanguage" in data:
            profile.primary_language = validate_language(data.get("primary_language") or data.get("primaryLanguage"))
        if "cin_number" in data or "cinNumber" in data:
            profile.cin_number = required(data.get("cin_number") or data.get("cinNumber"), "CIN number").upper()
    except ValidationError as exc:
        return error(str(exc), 422)
    db.session.add(profile)
    db.session.commit()
    return success("Seller profile updated", {"user": user.to_dict(private=True)})


@users_bp.get("/<int:user_id>")
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_active:
        return error("User not found", 404)
    return success("User loaded", {"user": user.to_dict(private=False)})
