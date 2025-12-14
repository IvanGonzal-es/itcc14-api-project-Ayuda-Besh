#!/usr/bin/env python3
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from lib.mongodb import init_db

# Import blueprints (order matters for URL prefix conflicts)
from routes.frontend import frontend_bp  # No prefix - must be first
from routes.auth import auth_bp
from routes.services import services_bp
from routes.bookings import bookings_bp
from routes.admin import admin_bp
from routes.requests import requests_bp
from routes.reviews import reviews_bp
from routes.availability import availability_bp
from routes.notifications import notifications_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins="*", supports_credentials=True)
    
    # Initialize database first
    try:
        init_db(app)
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        # Don't raise here - let app start but with limited functionality
    
    # Register blueprints in order (frontend first to avoid prefix conflicts)
    app.register_blueprint(frontend_bp)  # No URL prefix - handles /, /login, /dashboard
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(services_bp, url_prefix='/api')
    app.register_blueprint(bookings_bp, url_prefix='/api')
    app.register_blueprint(requests_bp, url_prefix='/api/requests')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(availability_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'ok', 
            'message': 'AyudaBesh API is running',
            'database': 'connected' if os.getenv("MONGODB_URI") else 'disconnected'
        }), 200
        
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors gracefully"""
        # Return JSON for API routes, HTML for frontend routes
        if request.path.startswith('/api/'):
            response = jsonify({'error': 'Endpoint not found'})
            response.headers['Content-Type'] = 'application/json'
            return response, 404
        from flask import render_template_string
        return render_template_string('<h1>404 - Page Not Found</h1>'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors gracefully"""
        # Return JSON for API routes, HTML for frontend routes
        if request.path.startswith('/api/'):
            response = jsonify({'error': 'Internal server error'})
            response.headers['Content-Type'] = 'application/json'
            return response, 500
        from flask import render_template_string
        return render_template_string('<h1>500 - Internal Server Error</h1>'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions"""
        # Return JSON for API routes
        if request.path.startswith('/api/'):
            import traceback
            print(f"Unhandled exception in API route: {e}")
            traceback.print_exc()
            # Ensure Content-Type is set to JSON
            response = jsonify({'error': f'Internal server error: {str(e)}'})
            response.headers['Content-Type'] = 'application/json'
            return response, 500
        # Re-raise for Flask's default handling for non-API routes
        raise e
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"[STARTING] Starting AyudaBesh server on http://{os.getenv('FLASK_HOST', '127.0.0.1')}:{os.getenv('FLASK_PORT', 5000)}")
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )