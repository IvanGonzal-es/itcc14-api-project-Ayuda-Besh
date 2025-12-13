# routes/frontend.py

from flask import Blueprint, render_template, redirect, url_for
from lib.decorators import token_required, admin_required

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def home():
    return render_template('home.html')

@frontend_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@frontend_bp.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@frontend_bp.route('/forgot-password', methods=['GET'])
def forgot_password():
    return render_template('forgot_password.html')

@frontend_bp.route('/reset-password', methods=['GET'])
def reset_password():
    return render_template('reset_password.html')

@frontend_bp.route('/customer/dashboard')
@token_required
def customer_dashboard():
    return render_template('customer/dashboard.html')

@frontend_bp.route('/provider/dashboard')
@token_required
def provider_dashboard():
    return render_template('provider/dashboard.html')

# ✅ CUSTOMER ROUTES
@frontend_bp.route('/customer/book-service')
@token_required
def book_service():
    return render_template('customer/book_service.html')

@frontend_bp.route('/customer/booking-history')
@token_required
def booking_history():
    return render_template('customer/booking_history.html')

# ✅ PROVIDER ROUTES  
@frontend_bp.route('/provider/job-requests')
@token_required
def job_requests():
    return render_template('provider/job_request.html')

@frontend_bp.route('/provider/manage-services')
@token_required
def manage_services():
    return render_template('provider/manage_services.html')

@frontend_bp.route('/provider/availability')
@token_required
def availability_calendar():
    return render_template('provider/availability.html')

# ✅ ADMIN ROUTES
@frontend_bp.route('/admin/dashboard')
@token_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@frontend_bp.route('/admin/provider-verification')
@token_required
@admin_required
def provider_verification():
    return render_template('admin/provider_verification.html')

@frontend_bp.route('/admin/dispute-management')
@token_required
@admin_required
def dispute_management():
    return render_template('admin/dispute_management.html')

@frontend_bp.route('/admin/reports')
@token_required
@admin_required
def reports():
    return render_template('admin/reports.html')