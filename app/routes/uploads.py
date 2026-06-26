from flask import Blueprint, g, request

from ..decorators import login_required
from ..extensions import db
from ..models import SellerProfile
from ..services.upload_service import save_upload
from ..utils.responses import error, success

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/v1/uploads")


@uploads_bp.post("/avatar")
@login_required()
def upload_avatar():
    try:
        relative, public_url = save_upload(request.files.get("file"), "avatars")
    except ValueError as exc:
        return error(str(exc), 422)
    if g.current_user.user_type == "seller":
        profile = g.current_user.seller_profile or SellerProfile(user=g.current_user)
        profile.profile_photo_url = relative
        db.session.add(profile)
        db.session.commit()
    return success("Avatar uploaded", {"path": relative, "url": public_url})


@uploads_bp.post("/cin")
@login_required()
def upload_cin():
    if g.current_user.user_type != "seller":
        return error("Seller account required", 403)
    side = request.form.get("side")
    if side not in {"front", "back"}:
        return error("side must be front or back", 422)
    try:
        relative, public_url = save_upload(request.files.get("file"), "cin")
    except ValueError as exc:
        return error(str(exc), 422)
    profile = g.current_user.seller_profile or SellerProfile(user=g.current_user)
    if side == "front":
        profile.cin_front_image_url = relative
    else:
        profile.cin_back_image_url = relative
    db.session.add(profile)
    db.session.commit()
    return success("CIN image uploaded", {"path": relative, "url": public_url, "side": side})
