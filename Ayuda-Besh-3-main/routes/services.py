# routes/services.py

from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from datetime import datetime
from bson.objectid import ObjectId

services_bp = Blueprint('services', __name__)

@services_bp.route('/services', methods=['GET'])
def get_services():
    """Get all available service categories"""
    db = get_database()
    services = list(db.services.find({}, {'_id': 0}))
    if not services:
        # Initialize default services if empty
        default_services = [
            {"name": "Domestic Cleaning", "category": "cleaning", "description": "Home cleaning services"},
            {"name": "Plumbing", "category": "plumbing", "description": "Pipe and fixture repairs"},
            {"name": "Electrical Work", "category": "electrical", "description": "Wiring and electrical installations"},
            {"name": "Pest Control", "category": "pest_control", "description": "Insect and rodent removal"},
            {"name": "Appliance Installation", "category": "appliance", "description": "Installation of household appliances"},
            {"name": "General Maintenance", "category": "maintenance", "description": "General home repair services"},
            {"name": "Online Services", "category": "online_services", "description": "Remote and digital services"}
        ]
        db.services.insert_many(default_services)
        services = default_services
    return jsonify(services), 200

@services_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get available providers with filtering (including location-based filtering)"""
    db = get_database()
    service_type = request.args.get('service')
    location = request.args.get('location')
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    radius_km = request.args.get('radius', type=float, default=50)  # Default 50km radius
    
    query = {
        'role': 'provider',
        'is_verified': True,
        'account_disabled': {'$ne': True}  # Exclude disabled accounts
    }
    
    if service_type:
        query['services_offered'] = {'$in': [service_type]}
    
    # Location filtering - can be by city name or coordinates
    if location:
        # Simple text-based location matching
        query['location'] = {'$regex': location, '$options': 'i'}
    
    providers = list(db.users.find(query, {
        'password': 0,
        'is_verified': 0
    }))
    
    # If coordinates provided, filter by distance
    if latitude and longitude:
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            """Calculate distance between two points on Earth in km"""
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            return c * r
        
        # Filter providers by distance (if they have coordinates)
        filtered_providers = []
        for provider in providers:
            provider_lat = provider.get('latitude')
            provider_lon = provider.get('longitude')
            
            if provider_lat and provider_lon:
                distance = haversine(longitude, latitude, provider_lon, provider_lat)
                provider['distance_km'] = round(distance, 2)
                
                # Check if within service radius
                service_radius = provider.get('service_radius', 50)
                if distance <= service_radius:
                    filtered_providers.append(provider)
            else:
                # If provider doesn't have coordinates, include them anyway
                provider['distance_km'] = None
                filtered_providers.append(provider)
        
        providers = filtered_providers
        # Sort by distance
        providers.sort(key=lambda x: x.get('distance_km') or float('inf'))
    
    # Convert ObjectId to string and add rating
    for provider in providers:
        provider['_id'] = str(provider['_id'])
        # Get average rating from bookings
        provider_bookings = list(db.bookings.find({
            'provider_id': ObjectId(provider['_id']),
            'status': 'completed',
            'rating': {'$exists': True, '$ne': None}
        }))
        if provider_bookings:
            avg_rating = sum(b.get('rating', 0) for b in provider_bookings) / len(provider_bookings)
            provider['rating'] = round(avg_rating, 2)
        else:
            provider['rating'] = 0
    
    return jsonify(providers), 200

@services_bp.route('/book', methods=['POST'])
@token_required
def book_service():
    """Customer books a service"""
    try:
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'Request body is missing or invalid JSON'})
            response.headers['Content-Type'] = 'application/json'
            return response, 400
        
        # Validate required fields
        required_fields = ['provider_id', 'service_type', 'booking_time', 'price']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            response = jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'})
            response.headers['Content-Type'] = 'application/json'
            return response, 400
        
        # Get user ID from token
        user_id = request.current_user.get('user_id')
        if not user_id:
            response = jsonify({'error': 'User ID not found in token'})
            response.headers['Content-Type'] = 'application/json'
            return response, 401
        
        db = get_database()
        
        # Parse booking time
        try:
            booking_time = datetime.fromisoformat(data['booking_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            response = jsonify({'error': f'Invalid booking_time format: {str(e)}'})
            response.headers['Content-Type'] = 'application/json'
            return response, 400
        
        booking = {
            'customer_id': ObjectId(user_id),
            'customer_name': data.get('customer_name', ''),
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'provider_id': ObjectId(data['provider_id']),
            'service_type': data['service_type'],
            'booking_time': booking_time,
            'service_address': data.get('service_address', ''),
            'special_instructions': data.get('special_instructions', ''),
            'status': 'pending',
            'price': float(data.get('price', 0)),
            'final_price': None,  # Will be set by provider
            'created_at': datetime.utcnow()
        }
        
        result = db.bookings.insert_one(booking)
        booking_id = str(result.inserted_id)
        
        # Create notification for provider
        try:
            notification = {
                'user_id': ObjectId(data['provider_id']),
                'title': 'New Booking Request',
                'message': f'You have a new booking request for {data["service_type"]} from {data.get("customer_name", "a customer")}.',
                'type': 'info',
                'read': False,
                'created_at': datetime.utcnow(),
                'booking_id': ObjectId(booking_id)
            }
            db.notifications.insert_one(notification)
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        response = jsonify({'booking_id': booking_id, 'message': 'Booking created successfully'})
        response.headers['Content-Type'] = 'application/json'
        return response, 201
    
    except ValueError as e:
        response = jsonify({'error': f'Invalid data format: {str(e)}'})
        response.headers['Content-Type'] = 'application/json'
        return response, 400
    except Exception as e:
        print(f"Error creating booking: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': f'Failed to create booking: {str(e)}'})
        response.headers['Content-Type'] = 'application/json'
        return response, 500

@services_bp.route('/update-profile', methods=['GET', 'POST'])
@token_required
def update_provider_profile():
    """Get or update user profile (works for both customer and provider)"""
    db = get_database()
    user_id = ObjectId(request.current_user['user_id'])
    role = request.current_user.get('role')
    
    if request.method == 'GET':
        # Return current user profile
        user = db.users.find_one(
            {'_id': user_id},
            {'password': 0}
        )
        if user:
            user['_id'] = str(user['_id'])
        return jsonify({'user': user}), 200
    
    # POST method - update profile (works for both customer and provider)
    update_data = {}
    
    # Handle file upload (profile picture)
    if 'profile_picture' in request.files:
        from werkzeug.utils import secure_filename
        import os
        import base64
        
        file = request.files['profile_picture']
        if file and file.filename:
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in allowed_extensions:
                return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
            
            # Check file size (5MB limit)
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > 5 * 1024 * 1024:
                return jsonify({'error': 'File size must be less than 5MB'}), 400
            
            # Read file and convert to base64 for storage (or save to filesystem)
            # For simplicity, we'll store as base64 data URL
            file_data = file.read()
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            mime_type = file.content_type or 'image/jpeg'
            profile_picture_url = f'data:{mime_type};base64,{file_base64}'
            
            update_data['profile_picture'] = profile_picture_url
    
    # Handle JSON data (for non-file updates)
    if request.is_json:
        data = request.get_json()
        
        # Service-related fields (for providers)
        if role == 'provider':
            if 'services' in data:
                update_data['services_offered'] = data.get('services', [])
            if 'hourly_rate' in data:
                update_data['hourly_rate'] = data.get('hourly_rate', 500)
            if 'service_radius' in data:
                update_data['service_radius'] = data.get('service_radius', 0)
            if 'equipment' in data:
                update_data['equipment'] = data.get('equipment', '')
    
        # Common fields
        if 'location' in data:
            update_data['location'] = data.get('location', '')
        if 'description' in data:
            update_data['description'] = data.get('description', '')
        
    # Personal information fields
    if 'fullName' in data:
        update_data['fullName'] = data.get('fullName', '')
    if 'email' in data:
        # Check if email is already in use by another user
        existing_user = db.users.find_one({
            'email': data.get('email'),
                '_id': {'$ne': user_id}
        })
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 400
        update_data['email'] = data.get('email', '')
        if 'phone' in data:
            # Check if phone is already in use by another user
            phone = data.get('phone', '').strip()
            if phone:
                existing_user = db.users.find_one({
                    'phone': phone,
                    '_id': {'$ne': user_id}
                })
                if existing_user:
                    return jsonify({'error': 'Phone number already in use'}), 400
                update_data['phone'] = phone
        if 'password' in data and data.get('password'):
            # Update password if provided
            from lib.auth import hash_password
            update_data['password'] = hash_password(data.get('password'))
            update_data['password_updated_at'] = datetime.utcnow()
    
    if not update_data:
        return jsonify({'error': 'No fields to update'}), 400
    
    result = db.users.update_one(
        {'_id': user_id},
        {'$set': update_data}
    )
    
    if result.matched_count > 0:
        # Return updated user data
        updated_user = db.users.find_one(
            {'_id': user_id},
            {'password': 0}
        )
        if updated_user:
            updated_user['_id'] = str(updated_user['_id'])
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user
        }), 200
    return jsonify({'error': 'Failed to update profile'}), 500

@services_bp.route('/available-services', methods=['GET'])
def get_available_services():
    """Get all services from verified providers for customer dashboard"""
    db = get_database()
    
    # Get all verified providers
    providers = list(db.users.find(
        {'role': 'provider', 'is_verified': True},
        {'password': 0}
    ))
    
    # Get service categories for descriptions
    service_categories = {}
    for service in db.services.find({}):
        service_categories[service.get('category', '')] = {
            'name': service.get('name', ''),
            'description': service.get('description', '')
        }
    
    # Build list of available services (one entry per provider-service combination)
    available_services = []
    for provider in providers:
        provider_id = str(provider['_id'])
        services_offered = provider.get('services_offered', [])
        location = provider.get('location', 'Not specified')
        description = provider.get('description', '')
        hourly_rate = provider.get('hourly_rate', 500)
        company_name = provider.get('username', 'Unknown Company')  # Company name (username)
        owner_name = provider.get('fullName', 'Unknown Owner')  # Owner's full name
        rating = provider.get('rating', 0)
        
        # If provider has services_offered, create entry for each service
        if services_offered and len(services_offered) > 0:
            for service_type in services_offered:
                service_info = service_categories.get(service_type, {})
                service_name = service_info.get('name', service_type.replace('_', ' ').title())
                service_description = service_info.get('description', description or 'Professional service provider')
                
                available_services.append({
                    'provider_id': provider_id,
                    'company_name': company_name,
                    'owner_name': owner_name,
                    'service_type': service_type,
                    'service_name': service_name,
                    'description': description or service_description,
                    'location': location,
                    'hourly_rate': hourly_rate,
                    'rating': rating
                })
        else:
            # If provider has no services specified, show them as "General Services"
            available_services.append({
                'provider_id': provider_id,
                'company_name': company_name,
                'owner_name': owner_name,
                'service_type': 'general',
                'service_name': 'General Services',
                'description': description or 'Professional service provider',
                'location': location,
                'hourly_rate': hourly_rate,
                'rating': rating
            })
    
    return jsonify(available_services), 200

@services_bp.route('/delete-account', methods=['POST'])
@token_required
def delete_account():
    """Request account deletion (requires admin approval)"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        role = request.current_user.get('role')
        data = request.get_json() or {}
        deletion_reason = data.get('reason', 'User requested account deletion')
        
        # Check if user has any active bookings
        if role == 'customer':
            active_bookings = db.bookings.count_documents({
                'customer_id': user_id,
                'status': {'$in': ['pending', 'accepted']}
            })
        elif role == 'provider':
            active_bookings = db.bookings.count_documents({
                'provider_id': user_id,
                'status': {'$in': ['pending', 'accepted']}
            })
        else:
            active_bookings = 0
        
        if active_bookings > 0:
            return jsonify({
                'error': f'Cannot delete account with {active_bookings} active booking(s). Please cancel or complete them first.'
            }), 400
        
        # Get user info before updating
        user = db.users.find_one({'_id': user_id})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Mark account for deletion (soft delete - requires admin approval)
        result = db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'deletion_requested': True,
                    'deletion_reason': deletion_reason,
                    'deletion_requested_at': datetime.utcnow(),
                    'account_disabled': True  # Disable account immediately
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Failed to update account'}), 500
        
        # Create notification for all admins about account deletion request
        def create_notification(user_id, title, message, type='info'):
            """Helper to create notifications"""
            try:
                notification = {
                    'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
                    'title': title,
                    'message': message,
                    'type': type,
                    'read': False,
                    'created_at': datetime.utcnow()
                }
                db.notifications.insert_one(notification)
            except Exception as e:
                print(f"Error creating notification: {e}")
        
        admins = list(db.users.find({'role': 'admin'}))
        user_name = user.get('fullName', user.get('username', 'Unknown'))
        user_role = user.get('role', 'user')
        for admin in admins:
            create_notification(
                admin['_id'],
                'Account Deletion Request',
                f'User {user_name} ({user_role}) has requested account deletion. Reason: {deletion_reason}',
                'warning'
            )
        
        return jsonify({
            'message': 'Account deletion requested. Your account has been disabled and is pending admin approval.',
            'status': 'pending_approval'
        }), 200
    except Exception as e:
        print(f"Error requesting account deletion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to request account deletion: {str(e)}'}), 500