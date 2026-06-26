"""
Authentication routes for SEVAR application
"""
from flask import Blueprint, request, jsonify, current_app
from models import User, db
from utils.auth_service import AuthService
from utils.otp_service import OTPService
from utils.validators import (
    ValidationError, validate_email, validate_phone_number,
    validate_otp, validate_name, validate_user_type
)
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/google', methods=['POST'])
def verify_google_user():
    """
    Verify Google user and create/update user in database
    
    Expects JSON:
    {
        "idToken": "firebase-id-token"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "المحتوى يجب أن يكون JSON"
            }), 400
        
        data = request.get_json(silent=True) or {}
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({
                "status": "error",
                "message": "الـ Token مطلوب"
            }), 400
        
        # Verify Firebase token
        is_valid, decoded_token, message = AuthService.verify_firebase_token(id_token)
        
        if not is_valid:
            logger.warning(f'Firebase token verification failed for: {message}')
            return jsonify({
                "status": "error",
                "message": message
            }), 401
        
        # Get or create user
        user = AuthService.get_or_create_user_from_firebase(decoded_token)
        
        # Create session
        session = AuthService.create_session(
            user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f'User {user.id} logged in via Google')
        
        return jsonify({
            "status": "success",
            "message": "تم تسجيل الدخول بنجاح",
            "user": user.to_dict(),
            "session_token": session.session_token
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in verify_google_user: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@auth_bp.route('/phone/request-otp', methods=['POST'])
def request_otp():
    """
    Request OTP for phone verification
    
    Expects JSON:
    {
        "phoneNumber": "+212600000000"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "المحتوى يجب أن يكون JSON"
            }), 400
        
        data = request.get_json(silent=True) or {}
        phone_number = data.get('phoneNumber')
        
        if not phone_number:
            return jsonify({
                "status": "error",
                "message": "رقم الهاتف مطلوب"
            }), 400
        
        # Validate phone number
        try:
            phone_number = validate_phone_number(phone_number)
        except ValidationError as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 400
        
        # Check if user exists with this phone
        existing_user = User.query.filter_by(phone_number=phone_number).first()
        
        # Create OTP
        otp_record = OTPService.create_otp(
            phone_number,
            user_id=existing_user.id if existing_user else None,
            expiration_time=current_app.config['OTP_EXPIRATION_TIME']
        )
        
        # TODO: Send OTP via SMS (integrate with Twilio or similar)
        # For development, we'll log it
        logger.info(f'OTP {otp_record.otp_code} requested for {phone_number}')
        
        return jsonify({
            "status": "success",
            "message": "تم إرسال كود التحقق",
            "otp_id": otp_record.id,
            "expires_in": current_app.config['OTP_EXPIRATION_TIME']
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in request_otp: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@auth_bp.route('/phone/verify-otp', methods=['POST'])
def verify_phone_otp():
    """
    Verify OTP code for phone number
    
    Expects JSON:
    {
        "phoneNumber": "+212600000000",
        "otp": "1234"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "المحتوى يجب أن يكون JSON"
            }), 400
        
        data = request.get_json(silent=True) or {}
        phone_number = data.get('phoneNumber')
        otp_code = data.get('otp')
        
        if not phone_number or not otp_code:
            return jsonify({
                "status": "error",
                "message": "رقم الهاتف وكود التحقق مطلوبان"
            }), 400
        
        # Validate inputs
        try:
            phone_number = validate_phone_number(phone_number)
            validate_otp(otp_code, current_app.config['OTP_LENGTH'])
        except ValidationError as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 400
        
        # Verify OTP
        is_valid, message, otp_record = OTPService.verify_otp(phone_number, otp_code)
        
        if not is_valid:
            return jsonify({
                "status": "error",
                "message": message
            }), 401
        
        # Get or create user
        user = User.query.filter_by(phone_number=phone_number).first()
        
        if user:
            user.is_verified = True
            user.last_login = db.func.now()
        else:
            user = User(
                phone_number=phone_number,
                auth_method='phone',
                is_verified=True,
                verification_date=db.func.now()
            )
            db.session.add(user)
        
        db.session.commit()
        
        # Create session
        session = AuthService.create_session(
            user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f'User {user.id} verified phone {phone_number}')
        
        return jsonify({
            "status": "success",
            "message": "تم التحقق بنجاح",
            "user": user.to_dict(),
            "session_token": session.session_token
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in verify_phone_otp: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user by invalidating session
    
    Expects header:
    Authorization: Bearer <session_token>
    """
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "status": "error",
                "message": "رمز الجلسة مطلوب"
            }), 401
        
        session_token = auth_header.split(' ')[1]
        
        # Invalidate session
        AuthService.logout_session(session_token)
        
        return jsonify({
            "status": "success",
            "message": "تم تسجيل الخروج بنجاح"
        }), 200
        
    except Exception as e:
        logger.exception(f'Error in logout: {str(e)}')
        return jsonify({
            "status": "error",
            "message": "خطأ داخلي في السيرفر"
        }), 500

