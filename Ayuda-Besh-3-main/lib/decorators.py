# lib/decorators.py (updated)

from functools import wraps
from flask import request, jsonify, redirect, url_for
from lib.auth import verify_token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(" ")[1]
            if not token:
                token = request.cookies.get('token')
                
            if not token:
                if not request.path.startswith('/api/'):
                    return redirect(url_for('frontend.login'))
                return jsonify({'error': 'Token is missing!'}), 401

            payload = verify_token(token)
            if not payload:
                if not request.path.startswith('/api/'):
                    return redirect(url_for('frontend.login'))
                return jsonify({'error': 'Token is invalid or expired!'}), 401

            request.current_user = payload
            return f(*args, **kwargs)
        except Exception as e:
            # Ensure all exceptions return JSON for API routes
            if request.path.startswith('/api/'):
                import traceback
                print(f"Error in token_required decorator: {e}")
                traceback.print_exc()
                return jsonify({'error': f'Authentication error: {str(e)}'}), 500
            # Re-raise for non-API routes to use default error handling
            raise
    return decorated

# ADMIN DECORATOR
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Ensure token decorator ran first
        user = getattr(request, "current_user", None)
        
        if not user:
            # For frontend routes, redirect to login; for API routes, return JSON error
            if not request.path.startswith('/api/'):
                return redirect(url_for('frontend.login'))
            return jsonify({"error": "Authentication required"}), 401

        if user.get("role") != "admin":
            # For frontend routes, redirect to login; for API routes, return JSON error
            if not request.path.startswith('/api/'):
                return redirect(url_for('frontend.login'))
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)
    return decorated
