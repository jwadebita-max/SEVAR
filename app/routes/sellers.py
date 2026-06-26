from flask import Blueprint, g, request

from ..decorators import role_required
from ..extensions import db
from ..models import RequestMatch, SellerProfile, ServiceRequest
from ..utils.responses import error, success

sellers_bp = Blueprint("sellers", __name__, url_prefix="/api/v1/sellers")


@sellers_bp.put("/availability")
@role_required("seller")
def update_availability():
    profile = g.current_user.seller_profile
    if not profile:
        profile = SellerProfile(user=g.current_user)
        db.session.add(profile)
    data = request.get_json(silent=True) or {}
    if "is_available" not in data:
        return error("is_available is required", 422)
    profile.is_available = bool(data.get("is_available"))
    db.session.commit()
    return success("Availability updated", {"is_available": profile.is_available})


@sellers_bp.get("/dashboard")
@role_required("seller")
def dashboard():
    user = g.current_user
    profile = user.seller_profile
    pending_matches = RequestMatch.query.filter_by(seller_id=user.id, status="pending").count()
    accepted_requests = ServiceRequest.query.filter_by(accepted_seller_id=user.id, status="accepted").count()
    completed = ServiceRequest.query.filter_by(accepted_seller_id=user.id, status="completed").all()
    recent = RequestMatch.query.filter_by(seller_id=user.id).order_by(RequestMatch.created_at.desc()).limit(10).all()
    return success("Dashboard loaded", {
        "is_available": bool(profile and profile.is_available),
        "pending_matches": pending_matches,
        "accepted_requests": accepted_requests,
        "completed_requests": len(completed),
        "total_revenue": sum(row.budget for row in completed),
        "rating": profile.rating if profile else 0,
        "recent_matches": [match.to_dict() for match in recent],
        "seller_profile": profile.to_dict(private=True) if profile else None,
    })
