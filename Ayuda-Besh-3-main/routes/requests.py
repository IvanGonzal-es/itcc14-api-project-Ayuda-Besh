from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from bson import ObjectId
from datetime import datetime

requests_bp = Blueprint('requests', __name__)

# Note: This file contains legacy service_requests endpoints
# The application primarily uses bookings instead of service_requests
# These endpoints are kept for backward compatibility but may not be actively used

@requests_bp.route('/create', methods=['POST'])
@token_required
def create_request():
    """Create a new service request"""
    try:
        data = request.get_json()
        service_id = data.get('serviceId')
        status = data.get('status', 'pending')
        
        user_id = request.current_user['user_id']
        user_name = request.current_user.get('fullName', '')
        
        if not service_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        db = get_database()
        requests_collection = db['service_requests']
        
        result = requests_collection.insert_one({
            'customerId': user_id,
            'customerName': user_name,
            'serviceId': service_id,
            'serviceName': 'Service',  # This would normally come from a services collection
            'status': status,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        })
        
        return jsonify({
            'id': str(result.inserted_id),
            'message': 'Request created'
        }), 201
        
    except Exception as error:
        print(f"Create request error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

@requests_bp.route('/my-requests', methods=['GET'])
@token_required
def get_my_requests():
    """Get all requests for the current user"""
    try:
        user_id = request.current_user['user_id']
        db = get_database()
        requests_collection = db['service_requests']
        
        requests = list(requests_collection.find(
            {'customerId': user_id}
        ).sort('createdAt', -1))
        
        # Convert ObjectId to string for JSON serialization
        for req in requests:
            req['_id'] = str(req['_id'])
            if 'createdAt' in req:
                req['createdAt'] = req['createdAt'].isoformat() if hasattr(req['createdAt'], 'isoformat') else str(req['createdAt'])
            if 'updatedAt' in req:
                req['updatedAt'] = req['updatedAt'].isoformat() if hasattr(req['updatedAt'], 'isoformat') else str(req['updatedAt'])
        
        return jsonify(requests), 200
        
    except Exception as error:
        print(f"Fetch requests error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

@requests_bp.route('/pending', methods=['GET'])
def get_pending_requests():
    """Get all pending service requests"""
    try:
        db = get_database()
        requests_collection = db['service_requests']
        
        requests = list(requests_collection.find(
            {'status': 'pending'}
        ).sort('createdAt', -1))
        
        # Convert ObjectId to string for JSON serialization
        for req in requests:
            req['_id'] = str(req['_id'])
            if 'createdAt' in req:
                req['createdAt'] = req['createdAt'].isoformat() if hasattr(req['createdAt'], 'isoformat') else str(req['createdAt'])
            if 'updatedAt' in req:
                req['updatedAt'] = req['updatedAt'].isoformat() if hasattr(req['updatedAt'], 'isoformat') else str(req['updatedAt'])
        
        return jsonify(requests), 200
        
    except Exception as error:
        print(f"Fetch pending requests error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

@requests_bp.route('/<request_id>', methods=['PATCH'])
@token_required
def update_request(request_id):
    """Update a service request status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Missing status field'}), 400
        
        db = get_database()
        requests_collection = db['service_requests']
        
        try:
            result = requests_collection.update_one(
                {'_id': ObjectId(request_id)},
                {
                    '$set': {
                        'status': status,
                        'updatedAt': datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            return jsonify({'error': 'Invalid request ID'}), 400
        
        if result.matched_count == 0:
            return jsonify({'error': 'Request not found'}), 404
        
        return jsonify({'message': 'Request updated'}), 200
        
    except Exception as error:
        print(f"Update request error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

