from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
from backend.models import User, OTPRequest, FailedLoginAttempt
from backend.extensions import db
from backend.config import Config
from backend.services.otp_service import OTPService
from backend.services.email_service import EmailService
from backend.security import require_firewall, validate_request_data, SecurityFirewall, SecurityLogger
from backend.services.audit_service import log_audit
from backend.utils.validation import (
    ValidationError,
    normalize_phone,
    validate_address,
    validate_city_or_state,
    validate_date_of_birth,
    validate_gender,
    validate_name,
    validate_pincode,
)
from backend.utils.roles import has_any_role

auth_bp = Blueprint('auth', __name__)

def auth_error(message, code='auth_error', status=401):
    """Consistent auth error payload."""
    error_label = 'Unauthorized' if status == 401 else 'Forbidden'
    return jsonify({
        'error': error_label,
        'message': message,
        'code': code
    }), status

def create_token(user_id, token_type='access', expires_delta=None):
    """Create JWT token with explicit token type and expiry."""
    now = datetime.utcnow()
    token_expiry = expires_delta
    if token_expiry is None:
        token_expiry = Config.JWT_ACCESS_TOKEN_EXPIRES if token_type == 'access' else Config.JWT_RESET_TOKEN_EXPIRES
    expires_at = now + token_expiry

    payload = {
        'user_id': user_id,
        'token_type': token_type,
        'iat': now,
        'exp': expires_at,
        'issued_at': now.isoformat() + 'Z',
        'expires_at': expires_at.isoformat() + 'Z'
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def create_access_token(user_id):
    """Create access token."""
    return create_token(user_id, token_type='access', expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)

def create_refresh_token(user_id):
    """Create refresh token."""
    return create_token(user_id, token_type='refresh', expires_delta=Config.JWT_REFRESH_TOKEN_EXPIRES)

def create_reset_token(user_id):
    """Create password reset token."""
    return create_token(user_id, token_type='password_reset', expires_delta=Config.JWT_RESET_TOKEN_EXPIRES)

def decode_token(token, expected_type='access'):
    """Decode and validate token type."""
    payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
    token_type = payload.get('token_type')
    if expected_type:
        expected_types = {expected_type} if isinstance(expected_type, str) else set(expected_type)
        # Backward compatibility: old tokens without token_type are treated as access tokens.
        if token_type and token_type not in expected_types:
            raise jwt.InvalidTokenError('Invalid token type')
        if not token_type and 'access' not in expected_types:
            raise jwt.InvalidTokenError('Invalid token type')
    return payload

def verify_token(token, expected_type='access'):
    """Verify JWT token and return user_id."""
    try:
        payload = decode_token(token, expected_type=expected_type)
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_bp.route('/register', methods=['POST'])
@require_firewall(max_requests=5, window_minutes=10)  # Max 5 registration attempts per 10 minutes
def register():
    """
    Register a new user
    Required: name, email, phone, password
    Optional: aadhaar_last4, consent
    """
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'password', 'date_of_birth', 'gender']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email
        is_valid_email, normalized_email, email_error = SecurityFirewall.validate_email_address(data['email'])
        if not is_valid_email:
            return jsonify({'error': f'Invalid email: {email_error}'}), 400
        data['email'] = normalized_email
        
        # Validate password strength
        is_strong, password_error = SecurityFirewall.check_password_strength(data['password'])
        if not is_strong:
            return jsonify({'error': password_error}), 400

        try:
            data['name'] = validate_name(data['name'])
            phone = normalize_phone(data['phone'])
            data['date_of_birth'] = validate_date_of_birth(data['date_of_birth'], min_age=18, max_age=120)
            data['gender'] = validate_gender(data['gender'])
            if not data['gender']:
                return jsonify({'error': 'gender is required'}), 400
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            return jsonify({'error': 'Phone number already registered'}), 400
        
        # Create new user
        user = User(
            name=data['name'],
            email=data['email'],
            phone=phone,
            date_of_birth=data['date_of_birth'],
            gender=data['gender'],
            role='CITIZEN'
        )
        user.set_password(data['password'])
        
        # Handle Aadhaar (optional)
        if data.get('aadhaar_last4'):
            user.aadhaar_last4 = data['aadhaar_last4']
            # Hash provided Aadhaar suffix before persistence.
            user.aadhaar_hash = hashlib.sha256(data['aadhaar_last4'].encode()).hexdigest()
        
        db.session.add(user)
        db.session.commit()
        log_audit(user.id, 'register', 'user', user.id)
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user_id': user.id,
            'email': user.email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/send-otp', methods=['POST'])
@require_firewall(max_requests=10, window_minutes=10)  # Max 10 OTP requests per 10 minutes
def send_otp():
    """
    Send OTP to email or phone
    Required: identifier (email or phone), channel ('email' or 'phone')
    """
    try:
        data = request.get_json() or {}
        identifier = data.get('identifier')
        channel = data.get('channel', 'email')
        
        if not identifier:
            return jsonify({'error': 'identifier is required'}), 400
        
        # Validate identifier
        is_valid, sanitized, error = SecurityFirewall.validate_input(identifier, 'identifier')
        if not is_valid:
            SecurityLogger.log_suspicious_activity(request.remote_addr, f"Invalid OTP identifier: {error}")
            return jsonify({'error': error}), 400
        
        if channel not in ['email', 'phone']:
            return jsonify({'error': 'channel must be email or phone'}), 400
        
        # Generate and send OTP
        otp, error = OTPService.create_otp_request(identifier, channel)
        
        if error:
            status = 429 if 'Too many OTP requests' in error else 400
            return jsonify({'error': error}), status
        
        return jsonify({
            'message': f'OTP sent to {identifier} via {channel}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and mark user as verified
    Required: identifier, otp
    """
    try:
        data = request.get_json() or {}
        identifier = data.get('identifier')
        otp = data.get('otp')
        
        if not identifier or not otp:
            return jsonify({'error': 'identifier and otp are required'}), 400
        
        # Verify OTP
        success, message = OTPService.verify_otp(identifier, otp)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Find user and mark as verified
        user = User.query.filter_by(email=identifier).first()
        if not user:
            user = User.query.filter_by(phone=identifier).first()
        
        if user:
            if '@' in identifier:
                user.email_verified = True
            else:
                user.phone_verified = True
            db.session.commit()
            
            # Send welcome email
            EmailService.send_welcome_email(user.email, user.name)
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCKOUT_HOURS = 24


@auth_bp.route('/login', methods=['POST'])
@require_firewall(max_requests=10, window_minutes=5)
def login():
    """
    Login user
    Required: email, password
    Server-side lockout: 3 failed attempts = 24-hour lockout per email
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        is_valid_email, normalized_email, email_error = SecurityFirewall.validate_email_address(email)
        if not is_valid_email:
            SecurityLogger.log_authentication_failure(request.remote_addr, email)
            return jsonify({'error': 'Invalid email format'}), 400
        
        attempt = FailedLoginAttempt.query.filter_by(identifier=normalized_email).first()
        if attempt and attempt.lockout_until and datetime.utcnow() < attempt.lockout_until:
            remaining = (attempt.lockout_until - datetime.utcnow()).total_seconds()
            return jsonify({
                'error': 'Account temporarily locked',
                'message': f'Too many failed attempts. Try again in {int(remaining // 3600)} hours.',
                'lockout_until': attempt.lockout_until.isoformat(),
                'code': 'auth_locked_out'
            }), 429
        
        user = User.query.filter_by(email=normalized_email).first()
        
        if not user or not user.check_password(password):
            if not attempt:
                attempt = FailedLoginAttempt(identifier=normalized_email, attempt_count=0)
                db.session.add(attempt)
            attempt.attempt_count += 1
            if attempt.attempt_count >= LOGIN_MAX_ATTEMPTS:
                attempt.lockout_until = datetime.utcnow() + timedelta(hours=LOGIN_LOCKOUT_HOURS)
            attempt.updated_at = datetime.utcnow()
            db.session.commit()
            SecurityLogger.log_authentication_failure(request.remote_addr, normalized_email)
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid email or password',
                'code': 'auth_invalid_credentials'
            }), 401
        
        if attempt:
            attempt.attempt_count = 0
            attempt.lockout_until = None
            db.session.commit()
        
        # Check if account is suspended
        if user.account_suspended:
            SecurityLogger.log_blocked_attempt(request.remote_addr, f"Suspended account login attempt: {normalized_email}")
            return auth_error(
                f'Your account has been suspended. Reason: {user.suspension_reason}',
                code='auth_account_suspended',
                status=403
            )
        
        # Create token
        token = create_access_token(user.id)
        response_payload = {
            'message': 'Login successful',
            'token_type': 'Bearer',
            'token': token,
            'user': user.to_dict(),
            'expires_in_seconds': int(Config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
        }
        if Config.ENABLE_REFRESH_TOKENS:
            response_payload['refresh_token'] = create_refresh_token(user.id)

        log_audit(user.id, 'login', 'user', user.id)
        return jsonify(response_payload), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_access_token():
    """Issue a new access token using refresh token."""
    if not Config.ENABLE_REFRESH_TOKENS:
        return jsonify({'error': 'Refresh tokens are disabled'}), 404

    try:
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return auth_error('refresh_token is required', code='auth_missing_refresh_token', status=401)

        try:
            payload = decode_token(refresh_token, expected_type='refresh')
            user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return auth_error('Refresh token has expired', code='auth_refresh_expired', status=401)
        except jwt.InvalidTokenError:
            return auth_error('Invalid refresh token', code='auth_invalid_refresh_token', status=401)

        user = User.query.get(user_id)
        if not user:
            return auth_error('User not found', code='auth_user_not_found', status=401)

        if user.account_suspended:
            return auth_error(
                f'Your account has been suspended. Reason: {user.suspension_reason}',
                code='auth_account_suspended',
                status=403
            )

        response_payload = {
            'token_type': 'Bearer',
            'token': create_access_token(user.id),
            'expires_in_seconds': int(Config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
        }
        if Config.ENABLE_REFRESH_TOKENS:
            response_payload['refresh_token'] = create_refresh_token(user.id)
        return jsonify(response_payload), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiate password reset process
    Required: email
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        is_valid_email, normalized_email, email_error = SecurityFirewall.validate_email_address(email)
        if not is_valid_email:
            return jsonify({'error': f'Invalid email: {email_error}'}), 400
        email = normalized_email
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if user exists or not (security)
            return jsonify({
                'message': 'If this email is registered, you will receive a verification code',
                'email': email
            }), 200
        
        # Send OTP to email
        otp, error = OTPService.create_otp_request(email, 'email')
        
        if error:
            return jsonify({'error': error}), 429
        
        return jsonify({
            'message': 'Verification code sent to your email',
            'email': email,
            'phone_last4': user.phone[-4:] if user.phone else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """
    Verify OTP for password reset
    Required: email, otp
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'error': 'Email and OTP are required'}), 400

        is_valid_email, normalized_email, email_error = SecurityFirewall.validate_email_address(email)
        if not is_valid_email:
            return jsonify({'error': f'Invalid email: {email_error}'}), 400
        email = normalized_email
        
        # Verify OTP
        success, message = OTPService.verify_otp(email, otp)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Generate reset token (valid for 15 minutes)
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        reset_token = create_reset_token(user.id)
        
        return jsonify({
            'message': 'OTP verified successfully',
            'reset_token': reset_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password with verified token
    Required: reset_token, new_password
    """
    try:
        data = request.get_json() or {}
        reset_token = data.get('reset_token')
        new_password = data.get('new_password')
        
        if not reset_token or not new_password:
            return jsonify({'error': 'Reset token and new password are required'}), 400
        
        # Validate password strength
        is_strong, password_error = SecurityFirewall.check_password_strength(new_password)
        if not is_strong:
            return jsonify({'error': password_error}), 400
        
        # Verify reset token
        try:
            payload = decode_token(reset_token, expected_type='password_reset')
            user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Reset token has expired. Please request a new one.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid reset token'}), 401
        
        # Find user and update password
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.set_password(new_password)
        db.session.commit()
        
        # Send confirmation email
        EmailService.send_password_reset_confirmation(user.email, user.name)
        
        return jsonify({
            'message': 'Password reset successfully. You can now login with your new password.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current user info from token
    Requires: Authorization header with Bearer token
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile/update', methods=['PUT'])
def update_profile():
    """
    Update user profile
    Requires: Authorization header with Bearer token
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        try:
            # Update allowed fields with strict server-side validation.
            if 'name' in data:
                user.name = validate_name(data['name'])
            if 'phone' in data:
                phone = normalize_phone(data['phone'])
                existing_phone = User.query.filter(User.id != user.id, User.phone == phone).first()
                if existing_phone:
                    return jsonify({'error': 'Phone number already registered'}), 400
                user.phone = phone
            if 'profile_photo' in data:
                profile_photo = data['profile_photo']
                if profile_photo is not None and not isinstance(profile_photo, str):
                    raise ValidationError('profile_photo must be a string')
                if profile_photo and len(profile_photo) > 2_000_000:
                    raise ValidationError('profile_photo payload is too large')
                user.profile_photo = profile_photo

            if 'address' in data:
                user.address = validate_address(data['address'], 'address')
            if 'city' in data:
                user.city = validate_city_or_state(data['city'], 'city')
            if 'state' in data:
                user.state = validate_city_or_state(data['state'], 'state')
            if 'pincode' in data:
                user.pincode = validate_pincode(data['pincode'], 'pincode')

            if 'residential_address' in data:
                user.residential_address = validate_address(data['residential_address'], 'residential_address')
            if 'residential_city' in data:
                user.residential_city = validate_city_or_state(data['residential_city'], 'residential_city')
            if 'residential_state' in data:
                user.residential_state = validate_city_or_state(data['residential_state'], 'residential_state')
            if 'residential_pincode' in data:
                user.residential_pincode = validate_pincode(data['residential_pincode'], 'residential_pincode')

            if 'date_of_birth' in data:
                user.date_of_birth = validate_date_of_birth(data['date_of_birth'], min_age=18, max_age=120)
            if 'gender' in data:
                user.gender = validate_gender(data['gender'])
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_current_user_from_token(return_error=False, required_roles=None, allow_suspended=False):
    """Get current user from bearer token with optional structured auth errors."""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            error_response = auth_error('Authorization token required', code='auth_missing_token', status=401)
            return (None, error_response) if return_error else None

        if not auth_header.startswith('Bearer '):
            error_response = auth_error(
                'Authorization header must use Bearer token',
                code='auth_bad_header',
                status=401
            )
            return (None, error_response) if return_error else None
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token, expected_type='access')
        
        if not user_id:
            error_response = auth_error('Invalid or expired token', code='auth_invalid_token', status=401)
            return (None, error_response) if return_error else None
        
        user = User.query.get(user_id)
        if not user:
            error_response = auth_error('User not found', code='auth_user_not_found', status=401)
            return (None, error_response) if return_error else None

        if user.account_suspended and not allow_suspended:
            error_response = auth_error(
                f'Your account has been suspended. Reason: {user.suspension_reason}',
                code='auth_account_suspended',
                status=403
            )
            return (None, error_response) if return_error else None

        if required_roles and not has_any_role(user.role, required_roles):
            error_response = auth_error(
                'You do not have permission to access this resource',
                code='auth_forbidden',
                status=403
            )
            return (None, error_response) if return_error else None

        return (user, None) if return_error else user
        
    except Exception:
        if return_error:
            return None, auth_error('Invalid or expired token', code='auth_invalid_token', status=401)
        return None
