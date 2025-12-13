# routes/notifications.py
from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from datetime import datetime
from bson.objectid import ObjectId

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications():
    """Get all notifications for current user"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        
        # Get notifications for this user, sorted by newest first
        notifications = list(db.notifications.find({
            'user_id': user_id
        }).sort('created_at', -1).limit(100))
        
        # Convert ObjectId to string
        for notification in notifications:
            notification['_id'] = str(notification['_id'])
            notification['user_id'] = str(notification['user_id'])
            if 'booking_id' in notification:
                notification['booking_id'] = str(notification['booking_id'])
            if 'created_at' in notification and notification['created_at']:
                notification['created_at'] = notification['created_at'].isoformat() if hasattr(notification['created_at'], 'isoformat') else str(notification['created_at'])
        
        # Count unread notifications
        unread_count = db.notifications.count_documents({
            'user_id': user_id,
            'read': False
        })
        
        return jsonify({
            'notifications': notifications,
            'unread_count': unread_count
        }), 200
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch notifications: {str(e)}'}), 500

@notifications_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@token_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        
        result = db.notifications.update_one(
            {
                '_id': ObjectId(notification_id),
                'user_id': user_id
            },
            {'$set': {'read': True, 'read_at': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify({'message': 'Notification marked as read'}), 200
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'error': f'Failed to mark notification as read: {str(e)}'}), 500

@notifications_bp.route('/notifications/read-all', methods=['POST'])
@token_required
def mark_all_read():
    """Mark all notifications as read for current user"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        
        result = db.notifications.update_many(
            {
                'user_id': user_id,
                'read': False
            },
            {'$set': {'read': True, 'read_at': datetime.utcnow()}}
        )
        
        return jsonify({
            'message': f'{result.modified_count} notifications marked as read'
        }), 200
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'error': f'Failed to mark all as read: {str(e)}'}), 500

def create_notification(user_id, title, message, type='info', booking_id=None, link=None):
    """Helper function to create a notification"""
    try:
        db = get_database()
        notification = {
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'title': title,
            'message': message,
            'type': type,  # 'info', 'success', 'warning', 'error'
            'read': False,
            'created_at': datetime.utcnow(),
            'booking_id': ObjectId(booking_id) if booking_id else None,
            'link': link
        }
        result = db.notifications.insert_one(notification)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None
