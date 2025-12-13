# lib/auth.py

import os
import random
import string
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from lib.mongodb import get_database
from bson.objectid import ObjectId

SECRET_KEY = os.getenv('SECRET_KEY', 'JesmundIvanClariceGailMayeoh!')

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, password)

def generate_token(user_id: str, role: str, expires_in: int = None) -> str:
    """Generate a JWT token that includes user role"""
    if expires_in is None:
        expires_str = os.getenv('JWT_EXPIRATION', '3600')
        try:
            expires_in = int(expires_str)
        except (ValueError, TypeError):
            expires_in = 3600

    payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
   
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_user_from_token(token: str) -> dict:
    payload = verify_token(token)
    if not payload:
        return None
    
    try:
        db = get_database()
        user_id = payload.get('user_id')
        if not user_id:
            return None
        user = db.users.find_one({'_id': ObjectId(user_id)})
        return user
    except Exception as e:
        print(f"Error getting user from token: {e}")
        return None

def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))

def generate_reset_token(user_id: str) -> str:
    """Generate a password reset token"""
    payload = {
        'user_id': str(user_id),
        'type': 'password_reset',
        'exp': datetime.utcnow() + timedelta(hours=1),  # 1 hour expiration
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # Ensure token is always a string
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def verify_reset_token(token: str) -> dict:
    """Verify a password reset token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != 'password_reset':
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None