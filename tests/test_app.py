import os
import tempfile

import pytest

from app import create_app
from app.extensions import db
from app.models import SellerProfile, ServiceCategory, User


class TestConfig:
    SECRET_KEY = "test-secret"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OTP_EXPIRY_MINUTES = 5
    SESSION_EXPIRY_DAYS = 7
    DEV_SHOW_OTP = True
    MAX_UPLOAD_SIZE_MB = 5
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        from app.models import seed_service_categories
        seed_service_categories()
    return app.test_client()


def login_phone(client, phone="+212600000000"):
    res = client.post("/api/v1/auth/phone/request-otp", json={"phone_number": phone})
    otp = res.get_json()["data"]["development_otp"]
    return client.post("/api/v1/auth/phone/verify-otp", json={"phone_number": phone, "otp": otp})


def test_app_creation(client):
    res = client.get("/api/v1/services")
    assert res.status_code == 200


def test_otp_request_and_verification(client):
    res = client.post("/api/v1/auth/phone/request-otp", json={"phone_number": "0600000000"})
    assert res.status_code == 200
    otp = res.get_json()["data"]["development_otp"]
    res = client.post("/api/v1/auth/phone/verify-otp", json={"phone_number": "0600000000", "otp": otp})
    assert res.status_code == 200


def test_unauthorized_profile_access(client):
    assert client.get("/api/v1/users/profile").status_code == 401


def test_user_profile_update(client):
    login_phone(client)
    res = client.put("/api/v1/users/profile", json={"full_name": "Ali", "user_type": "buyer", "location": "Rabat", "city": "Rabat"})
    assert res.status_code == 200
    assert res.get_json()["data"]["user"]["full_name"] == "Ali"


def test_service_category_listing(client):
    res = client.get("/api/v1/services")
    assert len(res.get_json()["data"]["services"]) == 4


def test_buyer_request_creation_and_matching(client):
    with client.application.app_context():
        seller = User(phone_number="+212611111111", user_type="seller", full_name="Seller", city="Rabat", location="Rabat", is_verified=True)
        db.session.add(seller)
        db.session.flush()
        db.session.add(SellerProfile(user_id=seller.id, service_category_id=1, is_available=True, primary_language="AR"))
        db.session.commit()
    login_phone(client, "+212622222222")
    client.put("/api/v1/users/profile", json={"full_name": "Buyer", "user_type": "buyer", "location": "Rabat", "city": "Rabat"})
    res = client.post("/api/v1/requests", json={"service_category_id": 1, "budget": 300, "address": "Agdal, Rabat", "city": "Rabat"})
    assert res.status_code == 201
    assert res.get_json()["data"]["matches_created"] == 1


def test_seller_availability_update(client):
    login_phone(client)
    client.put("/api/v1/users/profile", json={"full_name": "Seller", "user_type": "seller", "location": "Rabat", "city": "Rabat"})
    client.put("/api/v1/users/seller-info", json={"service_category_id": 1, "years_experience": 1, "service_description": "Fix", "primary_language": "AR"})
    res = client.put("/api/v1/sellers/availability", json={"is_available": True})
    assert res.status_code == 200
    assert res.get_json()["data"]["is_available"] is True


def test_request_acceptance_conflict(client):
    with client.application.app_context():
        buyer = User(phone_number="+212633333333", user_type="buyer", full_name="Buyer", city="Rabat", is_verified=True)
        seller1 = User(phone_number="+212644444444", user_type="seller", full_name="S1", city="Rabat", is_verified=True)
        seller2 = User(phone_number="+212655555555", user_type="seller", full_name="S2", city="Rabat", is_verified=True)
        db.session.add_all([buyer, seller1, seller2])
        db.session.flush()
        db.session.add_all([
            SellerProfile(user_id=seller1.id, service_category_id=1, is_available=True, primary_language="AR"),
            SellerProfile(user_id=seller2.id, service_category_id=1, is_available=True, primary_language="AR"),
        ])
        db.session.commit()
    login_phone(client, "+212633333333")
    res = client.post("/api/v1/requests", json={"service_category_id": 1, "budget": 300, "address": "Agdal, Rabat", "city": "Rabat"})
    request_id = res.get_json()["data"]["request"]["id"]
    client.post("/api/v1/auth/logout")
    login_phone(client, "+212644444444")
    assert client.post(f"/api/v1/requests/{request_id}/accept", json={}).status_code == 200
    client.post("/api/v1/auth/logout")
    login_phone(client, "+212655555555")
    assert client.post(f"/api/v1/requests/{request_id}/accept", json={}).status_code == 409
