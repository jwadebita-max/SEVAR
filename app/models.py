from datetime import datetime

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(32), unique=True, index=True)
    email = db.Column(db.String(255), unique=True)
    firebase_uid = db.Column(db.String(255), unique=True)
    auth_method = db.Column(db.String(20), default="phone", nullable=False)
    full_name = db.Column(db.String(160))
    user_type = db.Column(db.String(20))
    location = db.Column(db.String(255))
    city = db.Column(db.String(120))
    birthdate = db.Column(db.Date)
    gender = db.Column(db.String(20))
    citizenship = db.Column(db.String(80))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    seller_profile = db.relationship("SellerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def onboarding_complete(self):
        if not self.full_name or not self.user_type:
            return False
        if self.user_type == "buyer":
            return bool(self.location or self.city)
        if self.user_type == "seller":
            return bool(self.seller_profile and self.seller_profile.service_category_id and self.seller_profile.primary_language)
        return False

    def to_dict(self, private=False):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "user_type": self.user_type,
            "location": self.location,
            "city": self.city,
            "gender": self.gender,
            "citizenship": self.citizenship,
            "is_verified": self.is_verified,
            "onboarding_complete": self.onboarding_complete(),
        }
        if private:
            data.update({"phone_number": self.phone_number, "email": self.email, "birthdate": self.birthdate.isoformat() if self.birthdate else None})
        if self.seller_profile:
            data["seller_profile"] = self.seller_profile.to_dict(private=private)
        return data


class SellerProfile(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    service_category_id = db.Column(db.Integer, db.ForeignKey("service_category.id"))
    years_experience = db.Column(db.Integer)
    service_description = db.Column(db.Text)
    primary_language = db.Column(db.String(10))
    cin_number = db.Column(db.String(80), unique=True)
    cin_front_image_url = db.Column(db.String(255))
    cin_back_image_url = db.Column(db.String(255))
    profile_photo_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=False, nullable=False)
    rating = db.Column(db.Float, default=0.0, nullable=False)
    completed_jobs = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="seller_profile")
    category = db.relationship("ServiceCategory")

    def to_dict(self, private=False):
        data = {
            "id": self.id,
            "service_category_id": self.service_category_id,
            "service_category": self.category.to_dict() if self.category else None,
            "years_experience": self.years_experience,
            "service_description": self.service_description,
            "primary_language": self.primary_language,
            "profile_photo_url": self.profile_photo_url,
            "is_available": self.is_available,
            "rating": self.rating,
            "completed_jobs": self.completed_jobs,
        }
        if private:
            data.update({"cin_number": self.cin_number, "cin_front_image_url": self.cin_front_image_url, "cin_back_image_url": self.cin_back_image_url})
        return data


class OtpCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(32), index=True, nullable=False)
    otp_code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    attempt_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    session_token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(80))
    user_agent = db.Column(db.String(255))
    revoked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User")


class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    name_ar = db.Column(db.String(120), nullable=False)
    name_fr = db.Column(db.String(120))
    description_ar = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "name_ar": self.name_ar,
            "name_fr": self.name_fr,
            "description_ar": self.description_ar,
            "image_url": self.image_url,
        }


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    service_category_id = db.Column(db.Integer, db.ForeignKey("service_category.id"), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default="open", nullable=False)
    accepted_seller_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    buyer = db.relationship("User", foreign_keys=[buyer_id])
    accepted_seller = db.relationship("User", foreign_keys=[accepted_seller_id])
    category = db.relationship("ServiceCategory")
    matches = db.relationship("RequestMatch", back_populates="service_request", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "buyer": self.buyer.to_dict() if self.buyer else None,
            "service_category": self.category.to_dict() if self.category else None,
            "budget": self.budget,
            "address": self.address,
            "city": self.city,
            "description": self.description,
            "status": self.status,
            "accepted_seller_id": self.accepted_seller_id,
            "created_at": self.created_at.isoformat(),
        }


class RequestMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_request.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    match_score = db.Column(db.Float, default=0, nullable=False)
    status = db.Column(db.String(30), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    viewed_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)

    service_request = db.relationship("ServiceRequest", back_populates="matches")
    seller = db.relationship("User")

    __table_args__ = (db.UniqueConstraint("service_request_id", "seller_id", name="uq_request_seller_match"),)

    def to_dict(self):
        return {
            "id": self.id,
            "match_score": self.match_score,
            "status": self.status,
            "request": self.service_request.to_dict(),
        }


def seed_service_categories():
    defaults = [
        ("auto-mechanics", "ميكانيكي السيارات", "Mecanique auto", "فحص وإصلاح أعطال السيارات.", "https://images.unsplash.com/photo-1486006920555-c77dce18193b?q=80&w=400"),
        ("painting", "الصباغة", "Peinture", "صباغة المنازل والواجهات.", "https://images.unsplash.com/photo-1562259949-e8e7689d7828?q=80&w=400"),
        ("electricity", "الكهرباء", "Electricite", "تركيب وإصلاح الأنظمة الكهربائية.", "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?q=80&w=400"),
        ("plumbing", "السباكة", "Plomberie", "إصلاح تسربات المياه والصرف الصحي.", "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?q=80&w=400"),
    ]
    for slug, name_ar, name_fr, desc, image in defaults:
        if not ServiceCategory.query.filter_by(slug=slug).first():
            db.session.add(ServiceCategory(slug=slug, name_ar=name_ar, name_fr=name_fr, description_ar=desc, image_url=image))
    db.session.commit()
