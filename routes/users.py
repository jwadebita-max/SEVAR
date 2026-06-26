"""
User profile routes for SEVAR application
"""
from flask import Blueprint, request, jsonify, current_app
from models import User, db
from utils.auth_service import AuthService
from utils.validators import (
    ValidationError, validate_name, validate_user_type, validate_birthdate,
    validate_cin, validate_experience_years, validate_service_description,
    validate_gender, validate_language
)
import logging
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "status": "error",
                "message": "رمز الجلسة مطلوب"
            }), 401
        
        session_token = auth_header.split(' ')[1]
        is_valid, user = AuthService.verify_session_token(session_token)
        
        if not is_valid or not user:
            return jsonify({
                "status": "error",
                "message": "انتهت صلاحية الجلسة"
            }), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


@users_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
    try:
        user = request.current_user
        
        return jsonify({
            "status": "success",
            "user": user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in get_profile: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@users_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile
    
    Expects JSON with any of:
    {
        "fullName": "الاسم الكامل",
        "userType": "buyer|seller",
        "location": "الموقع",
        "birthdate": "YYYY-MM-DD",
        "gender": "male|female",
        "citizenship": "البلد"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "المحتوى يجب أن يكون JSON"
            }), 400
        
        user = request.current_user
        data = request.get_json(silent=True) or {}
        
        # Update full name
        if 'fullName' in data:
            full_name = data.get('fullName')
            try:
                validate_name(full_name)
                user.full_name = full_name
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update user type
        if 'userType' in data:
            user_type = data.get('userType')
            try:
                validate_user_type(user_type)
                user.user_type = user_type
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update location
        if 'location' in data:
            user.location = data.get('location')
        
        # Update birthdate
        if 'birthdate' in data:
            try:
                birthdate = validate_birthdate(data.get('birthdate'))
                user.birthdate = birthdate
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update gender
        if 'gender' in data:
            try:
                gender = validate_gender(data.get('gender'))
                user.gender = gender
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update citizenship
        if 'citizenship' in data:
            user.citizenship = data.get('citizenship')
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'User {user.id} updated profile')
        
        return jsonify({
            "status": "success",
            "message": "تم تحديث الملف الشخصي",
            "user": user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in update_profile: {str(e)}')
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@users_bp.route('/seller-info', methods=['PUT'])
@require_auth
def update_seller_info():
    """
    Update seller specific information
    
    Expects JSON:
    {
        "yearsExperience": 5,
        "serviceDescription": "وصف الخدمة",
        "primaryLanguage": "AR|FR|EN|ES|DE|BER",
        "cinNumber": "AB123456"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "المحتوى يجب أن يكون JSON"
            }), 400
        
        user = request.current_user
        
        # Check if user is seller
        if user.user_type != 'seller':
            return jsonify({
                "status": "error",
                "message": "هذه المعلومات مخصصة للبائعين فقط"
            }), 403
        
        data = request.get_json(silent=True) or {}
        
        # Update years of experience
        if 'yearsExperience' in data:
            try:
                years = validate_experience_years(data.get('yearsExperience'))
                user.years_experience = years
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update service description
        if 'serviceDescription' in data:
            try:
                description = validate_service_description(data.get('serviceDescription'))
                user.service_description = description
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update primary language
        if 'primaryLanguage' in data:
            try:
                language = validate_language(data.get('primaryLanguage'))
                user.primary_language = language
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        # Update CIN
        if 'cinNumber' in data:
            try:
                cin = validate_cin(data.get('cinNumber'))
                user.cin_number = cin
            except ValidationError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Seller {user.id} updated seller information')
        
        return jsonify({
            "status": "success",
            "message": "تم تحديث معلومات البائع",
            "user": user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in update_seller_info: {str(e)}')
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get public user profile (for sellers)"""
    try:
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({
                "status": "error",
                "message": "المستخدم غير موجود"
            }), 404
        
        return jsonify({
            "status": "success",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in get_user: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500

