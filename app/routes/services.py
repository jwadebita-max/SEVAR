from flask import Blueprint

from ..models import ServiceCategory
from ..utils.responses import success

services_bp = Blueprint("services", __name__, url_prefix="/api/v1/services")


@services_bp.get("")
def list_services():
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.id).all()
    return success("Services loaded", {"services": [item.to_dict() for item in categories]})


@services_bp.get("/<int:service_id>")
def get_service(service_id):
    category = ServiceCategory.query.filter_by(id=service_id, is_active=True).first_or_404()
    return success("Service loaded", {"service": category.to_dict()})
