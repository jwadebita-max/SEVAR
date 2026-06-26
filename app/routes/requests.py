from datetime import datetime

from flask import Blueprint, g, request

from ..decorators import login_required, role_required
from ..extensions import db
from ..models import RequestMatch, ServiceCategory, ServiceRequest
from ..services.matching_service import MatchingService
from ..utils.responses import error, success
from ..utils.validators import ValidationError, required, validate_int, validate_positive_number

requests_bp = Blueprint("requests", __name__, url_prefix="/api/v1/requests")


@requests_bp.post("")
@role_required("buyer")
def create_request():
    data = request.get_json(silent=True) or {}
    try:
        category_id = validate_int(data.get("service_category_id") or data.get("serviceCategoryId"), "Service category", 1)
        category = ServiceCategory.query.filter_by(id=category_id, is_active=True).first()
        if not category:
            return error("Service category not found", 404)
        budget = validate_positive_number(data.get("budget"), "Budget")
        address = required(data.get("address"), "Address")
        city = required(data.get("city") or address.split(",")[-1], "City")
    except ValidationError as exc:
        return error(str(exc), 422)
    service_request = ServiceRequest(
        buyer_id=g.current_user.id,
        service_category_id=category.id,
        budget=budget,
        address=address,
        city=city,
        description=data.get("description"),
    )
    db.session.add(service_request)
    db.session.flush()
    matches = MatchingService.create_matches(service_request)
    db.session.commit()
    return success("Request created successfully", {"request": service_request.to_dict(), "matches_created": len(matches)}, 201)


@requests_bp.get("/my")
@login_required()
def my_requests():
    user = g.current_user
    if user.user_type == "buyer":
        rows = ServiceRequest.query.filter_by(buyer_id=user.id).order_by(ServiceRequest.created_at.desc()).all()
    else:
        rows = ServiceRequest.query.filter_by(accepted_seller_id=user.id).order_by(ServiceRequest.created_at.desc()).all()
    return success("Requests loaded", {"requests": [row.to_dict() for row in rows]})


@requests_bp.get("/matches")
@role_required("seller")
def seller_matches():
    matches = (
        RequestMatch.query.join(ServiceRequest)
        .filter(RequestMatch.seller_id == g.current_user.id, RequestMatch.status.in_(["pending", "viewed"]))
        .order_by(RequestMatch.match_score.desc(), RequestMatch.created_at.desc())
        .all()
    )
    return success("Matches loaded", {"matches": [match.to_dict() for match in matches]})


@requests_bp.get("/<int:request_id>")
@login_required()
def get_request(request_id):
    row = ServiceRequest.query.get_or_404(request_id)
    if row.buyer_id != g.current_user.id and row.accepted_seller_id != g.current_user.id:
        if not RequestMatch.query.filter_by(service_request_id=row.id, seller_id=g.current_user.id).first():
            return error("Not allowed", 403)
    return success("Request loaded", {"request": row.to_dict()})


@requests_bp.put("/<int:request_id>/cancel")
@role_required("buyer")
def cancel_request(request_id):
    row = ServiceRequest.query.get_or_404(request_id)
    if row.buyer_id != g.current_user.id:
        return error("Not allowed", 403)
    if row.status != "open":
        return error("Only open requests can be cancelled", 409)
    row.status = "cancelled"
    row.cancelled_at = datetime.utcnow()
    for match in row.matches:
        if match.status == "pending":
            match.status = "expired"
    db.session.commit()
    return success("Request cancelled", {"request": row.to_dict()})


@requests_bp.post("/<int:request_id>/accept")
@role_required("seller")
def accept_request(request_id):
    row = ServiceRequest.query.get_or_404(request_id)
    match = RequestMatch.query.filter_by(service_request_id=row.id, seller_id=g.current_user.id).first()
    if not match:
        return error("No match found for this seller", 403)
    if row.status != "open":
        return error("Request is no longer available", 409)
    now = datetime.utcnow()
    row.status = "accepted"
    row.accepted_seller_id = g.current_user.id
    row.accepted_at = now
    for existing in row.matches:
        existing.responded_at = now
        existing.status = "accepted" if existing.id == match.id else "expired"
    db.session.commit()
    return success("Request accepted", {"request": row.to_dict()})


@requests_bp.post("/<int:request_id>/reject")
@role_required("seller")
def reject_request(request_id):
    match = RequestMatch.query.filter_by(service_request_id=request_id, seller_id=g.current_user.id).first_or_404()
    if match.status == "pending":
        match.status = "rejected"
        match.responded_at = datetime.utcnow()
        db.session.commit()
    return success("Request rejected", {"match": match.to_dict()})
