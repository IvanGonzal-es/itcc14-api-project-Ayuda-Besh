# routes/auth.py

from flask import Blueprint, request, jsonify, make_response
from lib.mongodb import get_database
from lib.auth import (
    verify_password, generate_token, hash_password,
    generate_verification_code, generate_reset_token, verify_reset_token
)
from lib.email_service import send_verification_email, send_sms_verification
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import traceback
import re

auth_bp = Blueprint('auth', __name__)

def _mask_identifier(identifier):
    """Mask email or phone for display"""
    if '@' in identifier:
        # Email: mask middle part
        parts = identifier.split('@')
        if len(parts[0]) > 2:
            masked = parts[0][0] + '***' + parts[0][-1] + '@' + parts[1]
        else:
            masked = '***@' + parts[1]
        return masked
    else:
        # Phone: show last 4 digits
        if len(identifier) > 4:
            return '***' + identifier[-4:]
        return '***'

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400

        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        
        if not all([username, password, role]):
            return jsonify({'error': 'Missing username, password, or role'}), 400
        
        db = get_database()
        users_collection = db['users']
        user = users_collection.find_one({'username': username, 'role': role})
        
        if not user or not verify_password(password, user.get('password', '')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user_data = {
            'id': str(user['_id']),
            'username': user.get('username', ''),
            'fullName': user.get('fullName', ''),
            'email': user.get('email', ''),
            'role': user.get('role', '')
        }
        
        token = generate_token(str(user['_id']), user.get('role', 'customer'))
        
        response = make_response(jsonify({
            'user': user_data,
            'token': token
        }))
        response.set_cookie(
            'token',
            token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600,
            path='/'
        )
        print(f"[OK] LOGIN SUCCESS: Token cookie set for user '{username}' (role: {role})")
        return response
        
    except Exception as error:
        print("=== LOGIN ERROR ===")
        print(f"Error type: {type(error).__name__}")
        print(f"Error message: {str(error)}")
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(error)}'}), 500

@auth_bp.route('/admin/signup', methods=['POST'])
def admin_signup():
    """Admin signup endpoint - public endpoint for creating admin accounts from Admin Portal"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400

        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone', '').strip()
        password = data.get('password')
        full_name = data.get('fullName')
        
        # Only allow admin role from this endpoint
        role = 'admin'
        
        if not all([username, email, password, full_name]):
            return jsonify({'error': 'Missing required fields: username, email, password, fullName'}), 400
        
        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400
        
        db = get_database()
        users_collection = db['users']
        
        # Check for duplicates
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already in use'}), 400
        if users_collection.find_one({'phone': phone}):
            return jsonify({'error': 'Phone number already in use'}), 400
        
        hashed_password = hash_password(password)
        
        # Create admin document
        admin_doc = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'fullName': full_name,
            'role': role,
            'createdAt': datetime.utcnow()
        }
        
        result = users_collection.insert_one(admin_doc)
        
        user = {
            'id': str(result.inserted_id),
            'username': username,
            'fullName': full_name,
            'email': email,
            'role': role
        }
        
        return jsonify({
            'message': 'Admin account created successfully',
            'user': user
        }), 201
        
    except Exception as error:
        print("=== ADMIN SIGNUP ERROR ===")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400

        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone', '').strip()
        password = data.get('password')
        full_name = data.get('fullName')
        role = data.get('role', 'customer')
        
        # SECURITY: Prevent admin role creation via public signup
        # Only allow 'customer' or 'provider' roles from public signup
        if role not in ['customer', 'provider']:
            return jsonify({'error': 'Invalid role. Only customer or provider accounts can be created through public signup.'}), 400
        
        # Force role to be customer or provider (ignore any admin role attempts)
        if role == 'admin':
            role = 'customer'  # Default to customer if admin was attempted
        
        if not all([username, email, password, full_name]):
            return jsonify({'error': 'Missing required fields: username, email, password, fullName'}), 400
        
        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400
        
        db = get_database()
        users_collection = db['users']
        
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already in use'}), 400
        if users_collection.find_one({'phone': phone}):
            return jsonify({'error': 'Phone number already in use'}), 400
        
        hashed_password = hash_password(password)
        
        # Base user document
        user_doc = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'fullName': full_name,
            'role': role,
            'createdAt': datetime.utcnow()
        }
        
        # Add provider-specific fields if role is provider
        if role == 'provider':
            user_doc['is_verified'] = False  # Explicitly set to False for pending verification
            user_doc['services_offered'] = data.get('services_offered', [])  # Services from signup form
            user_doc['location'] = data.get('location', '')  # Location from signup form
            user_doc['description'] = data.get('description', '')  # Description from signup form
            user_doc['hourly_rate'] = data.get('hourly_rate', 0)  # Hourly rate from signup form
            user_doc['service_radius'] = data.get('service_radius', 0)  # Service radius from signup form
            user_doc['equipment'] = data.get('equipment', '')  # Equipment from signup form
            user_doc['rating'] = 0  # Initialize rating
        
        result = users_collection.insert_one(user_doc)
        
        user = {
            'id': str(result.inserted_id),
            'username': username,
            'fullName': full_name,
            'email': email,
            'role': role
        }
        
        token = generate_token(str(result.inserted_id), role)
        
        response = make_response(jsonify({
            'user': user,
            'token': token
        }))
        response.set_cookie(
            'token',
            token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600,
            path='/'
        )
        print(f"[OK] SIGNUP SUCCESS: Token cookie set for user '{username}' (role: {role})")
        return response
        
    except Exception as error:
        print("=== SIGNUP ERROR ===")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

# ✅ NEW: Logout endpoint
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        response = jsonify({'message': 'Logged out successfully'})
        # Clear the token cookie by setting expiration to past date
        response.set_cookie(
            'token',
            '',
            expires=0,
            path='/',
            secure=False,
            samesite='Lax'
        )
        print("[OK] LOGOUT SUCCESS: Token cookie cleared")
        return response
    except Exception as error:
        print("=== LOGOUT ERROR ===")
        traceback.print_exc()
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset - sends verification code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400
        
        identifier = data.get('identifier', '').strip()
        role = data.get('role', 'customer')
        
        if not identifier:
            return jsonify({'error': 'Email or phone number is required'}), 400
        
        db = get_database()
        users_collection = db['users']
        
        # Determine if identifier is email or phone
        is_email = '@' in identifier
        is_phone = re.match(r'^\+?[\d\s\-\(\)]+$', identifier) is not None
        
        # Build query
        query = {'role': role}
        if is_email:
            query['email'] = identifier
        elif is_phone:
            # Normalize phone number (remove spaces, dashes, etc.)
            normalized_phone = re.sub(r'[\s\-\(\)]', '', identifier)
            # Try to find by email first (most users have email), then phone
            # Also try username as fallback
            query['$or'] = [
                {'email': identifier},
                {'username': identifier},
                {'phone': normalized_phone},
                {'phone': identifier}
            ]
        else:
            # Try username or email as fallback
            query['$or'] = [
                {'username': identifier},
                {'email': identifier}
            ]
        
        user = users_collection.find_one(query)
        
        if not user:
            # Return error - user must exist to reset password
            return jsonify({
                'error': 'No account found with the provided email/phone number and account type. Please check your information and try again.'
            }), 404
        
        # Generate verification code
        verification_code = generate_verification_code(6)
        
        # Generate reset token
        reset_token = generate_reset_token(str(user['_id']))
        
        # Store verification code in database with expiration (15 minutes)
        password_resets_collection = db['password_resets']
        password_resets_collection.delete_many({
            'user_id': user['_id'],
            'used': False
        })
        
        password_resets_collection.insert_one({
            'user_id': user['_id'],
            'verification_code': verification_code,
            'reset_token': reset_token,
            'identifier': identifier,
            'used': False,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=15)
        })
        
        # Send verification code via email or SMS
        user_email = user.get('email', '')
        user_phone = user.get('phone', '')
        user_name = user.get('fullName', '')
        
        email_sent = False
        sms_sent = False
        
        # Determine if identifier is email or phone
        is_email = '@' in identifier
        
        # Strategy: Send via the method the user requested, with fallback
        if is_email:
            # User provided email - send via email
            if user_email:
                email_sent = send_verification_email(user_email, verification_code, user_name)
            # Also try SMS if user has phone number
            if user_phone:
                sms_sent = send_sms_verification(user_phone, verification_code)
        else:
            # User provided phone/username - try to send via SMS first
            if user_phone:
                sms_sent = send_sms_verification(user_phone, verification_code)
            elif is_phone:
                # User provided phone but not in DB - try to send to provided number
                normalized_phone = re.sub(r'[\s\-\(\)]', '', identifier)
                sms_sent = send_sms_verification(normalized_phone, verification_code)
            
            # Always try email as backup if user has email
            if user_email:
                email_sent = send_verification_email(user_email, verification_code, user_name)
        
        # If neither email nor SMS was sent successfully, return code in response (for development)
        response_data = {
            'message': 'Verification code sent successfully',
            'reset_token': reset_token,
            'identifier_masked': _mask_identifier(identifier),
            'sent_via': []
        }
        
        if email_sent:
            response_data['sent_via'].append('email')
        if sms_sent:
            response_data['sent_via'].append('sms')
        
        # If email/SMS not configured, include code in response for development
        if not email_sent and not sms_sent:
            response_data['verification_code'] = verification_code
            response_data['message'] = 'Verification code (email/SMS not configured - check console or response)'
            print(f"⚠️ Email/SMS not configured. Verification code: {verification_code}")
            print(f"   Set SMTP_USERNAME/SMTP_PASSWORD in .env for email")
            print(f"   Set TWILIO credentials in .env for SMS")
        else:
            response_data['message'] = f'Verification code sent via {", ".join(response_data["sent_via"])}'
        
        return jsonify(response_data), 200
        
    except Exception as error:
        print("=== FORGOT PASSWORD ERROR ===")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with verification code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400
        
        reset_token = data.get('reset_token')
        verification_code = data.get('verification_code', '').strip()
        new_password = data.get('new_password')
        
        if not all([reset_token, verification_code, new_password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Verify reset token
        token_payload = verify_reset_token(reset_token)
        if not token_payload:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        user_id = ObjectId(token_payload['user_id'])
        
        db = get_database()
        password_resets_collection = db['password_resets']
        users_collection = db['users']
        
        # Find valid reset request
        reset_request = password_resets_collection.find_one({
            'user_id': user_id,
            'reset_token': reset_token,
            'verification_code': verification_code,
            'used': False,
            'expires_at': {'$gt': datetime.utcnow()}
        })
        
        if not reset_request:
            return jsonify({'error': 'Invalid or expired verification code'}), 400
        
        # Verify user exists
        user = users_collection.find_one({'_id': user_id})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update password
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': {'password': hashed_password, 'password_updated_at': datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update password'}), 500
        
        # Mark reset request as used
        password_resets_collection.update_one(
            {'_id': reset_request['_id']},
            {'$set': {'used': True, 'used_at': datetime.utcnow()}}
        )
        
        # Invalidate all other reset tokens for this user
        password_resets_collection.update_many(
            {
                'user_id': user_id,
                'used': False,
                '_id': {'$ne': reset_request['_id']}
            },
            {'$set': {'used': True}}
        )
        
        print(f"[OK] PASSWORD RESET SUCCESS: User {user.get('username', 'unknown')} reset their password")
        
        return jsonify({
            'message': 'Password reset successfully'
        }), 200
        
    except Exception as error:
        print("=== RESET PASSWORD ERROR ===")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500