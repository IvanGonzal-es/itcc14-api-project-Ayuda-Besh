# routes/reviews.py

from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from datetime import datetime
from bson.objectid import ObjectId

reviews_bp = Blueprint('reviews', __name__)

def create_notification(user_id, title, message, type='info', booking_id=None):
    """Helper to create notifications"""
    try:
        db = get_database()
        notification = {
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'title': title,
            'message': message,
            'type': type,
            'read': False,
            'created_at': datetime.utcnow(),
            'booking_id': ObjectId(booking_id) if booking_id else None
        }
        db.notifications.insert_one(notification)
    except Exception as e:
        print(f"Error creating notification: {e}")

@reviews_bp.route('/provider/<provider_id>', methods=['GET'])
def get_provider_reviews(provider_id):
    """Get all reviews and ratings for a specific provider"""
    try:
        db = get_database()
        
        # Validate provider_id
        try:
            provider_obj_id = ObjectId(provider_id)
        except:
            return jsonify({'error': 'Invalid provider ID'}), 400
        
        # Check if provider exists
        provider = db.users.find_one({'_id': provider_obj_id, 'role': 'provider'})
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Get query parameters for pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        # Get reviews from reviews collection
        reviews = list(db.reviews.find(
            {'provider_id': provider_obj_id}
        ).sort('created_at', -1).skip(skip).limit(limit))
        
        # Also get ratings from bookings (for backward compatibility)
        bookings_with_ratings = list(db.bookings.find({
            'provider_id': provider_obj_id,
            'rating': {'$exists': True, '$ne': None},
            'status': 'completed'
        }).sort('rated_at', -1))
        
        # Combine and format reviews
        all_reviews = []
        booking_ids_in_reviews = {str(r['booking_id']) for r in reviews}
        
        # Add reviews from reviews collection
        for review in reviews:
            all_reviews.append({
                'review_id': str(review['_id']),
                'booking_id': str(review['booking_id']),
                'customer_id': str(review['customer_id']),
                'customer_name': review.get('customer_name', 'Anonymous'),
                'rating': review.get('rating', 0),
                'review': review.get('review'),
                'created_at': review.get('created_at').isoformat() if review.get('created_at') else None,
                'updated_at': review.get('updated_at').isoformat() if review.get('updated_at') else None
            })
        
        # Add ratings from bookings that don't have reviews yet (backward compatibility)
        for booking in bookings_with_ratings:
            booking_id_str = str(booking['_id'])
            if booking_id_str not in booking_ids_in_reviews:
                # Get customer info
                customer = db.users.find_one({'_id': booking['customer_id']})
                customer_name = customer.get('fullName', 'Anonymous') if customer else 'Anonymous'
                
                all_reviews.append({
                    'review_id': None,
                    'booking_id': booking_id_str,
                    'customer_id': str(booking['customer_id']),
                    'customer_name': customer_name,
                    'rating': booking.get('rating', 0),
                    'review': booking.get('review'),
                    'created_at': booking.get('rated_at').isoformat() if booking.get('rated_at') else None,
                    'updated_at': booking.get('rated_at').isoformat() if booking.get('rated_at') else None
                })
        
        # Sort all reviews by created_at (most recent first)
        all_reviews.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        # Calculate statistics
        total_reviews = len(all_reviews)
        ratings_only = [r['rating'] for r in all_reviews if r['rating']]
        avg_rating = round(sum(ratings_only) / len(ratings_only), 2) if ratings_only else 0
        
        # Rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings_only:
            if 1 <= rating <= 5:
                rating_distribution[int(rating)] += 1
        
        return jsonify({
            'provider_id': provider_id,
            'provider_name': provider.get('username', provider.get('fullName', 'Unknown')),
            'total_reviews': total_reviews,
            'average_rating': avg_rating,
            'rating_distribution': rating_distribution,
            'reviews': all_reviews,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_reviews
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching provider reviews: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch reviews: {str(e)}'}), 500

@reviews_bp.route('/booking/<booking_id>', methods=['GET'])
@token_required
def get_booking_review(booking_id):
    """Get review for a specific booking"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        role = request.current_user['role']
        
        # Get booking
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check access: customer can see their own, provider can see reviews for their bookings
        if role == 'customer' and booking['customer_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif role == 'provider' and booking['provider_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get review from reviews collection
        review = db.reviews.find_one({'booking_id': ObjectId(booking_id)})
        
        if review:
            return jsonify({
                'review_id': str(review['_id']),
                'booking_id': booking_id,
                'customer_id': str(review['customer_id']),
                'customer_name': review.get('customer_name', 'Anonymous'),
                'rating': review.get('rating', 0),
                'review': review.get('review'),
                'created_at': review.get('created_at').isoformat() if review.get('created_at') else None,
                'updated_at': review.get('updated_at').isoformat() if review.get('updated_at') else None
            }), 200
        else:
            # Check if booking has rating but no review document
            if booking.get('rating'):
                customer = db.users.find_one({'_id': booking['customer_id']})
                return jsonify({
                    'review_id': None,
                    'booking_id': booking_id,
                    'customer_id': str(booking['customer_id']),
                    'customer_name': customer.get('fullName', 'Anonymous') if customer else 'Anonymous',
                    'rating': booking.get('rating', 0),
                    'review': booking.get('review'),
                    'created_at': booking.get('rated_at').isoformat() if booking.get('rated_at') else None,
                    'updated_at': booking.get('rated_at').isoformat() if booking.get('rated_at') else None
                }), 200
            else:
                return jsonify({'error': 'No review found for this booking'}), 404
        
    except Exception as e:
        print(f"Error fetching booking review: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch review: {str(e)}'}), 500

@reviews_bp.route('/my-reviews', methods=['GET'])
@token_required
def get_my_reviews():
    """Get all reviews written by the current customer"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        role = request.current_user['role']
        
        if role != 'customer':
            return jsonify({'error': 'Only customers can view their reviews'}), 403
        
        # Get reviews from reviews collection
        reviews = list(db.reviews.find(
            {'customer_id': user_id}
        ).sort('created_at', -1))
        
        # Enhance with provider and booking info
        for review in reviews:
            provider = db.users.find_one({'_id': review['provider_id']})
            booking = db.bookings.find_one({'_id': review['booking_id']})
            
            review['_id'] = str(review['_id'])
            review['provider_id'] = str(review['provider_id'])
            review['customer_id'] = str(review['customer_id'])
            review['booking_id'] = str(review['booking_id'])
            review['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
            review['service_type'] = booking.get('service_type', 'Unknown') if booking else 'Unknown'
            
            # Format dates
            if review.get('created_at'):
                review['created_at'] = review['created_at'].isoformat()
            if review.get('updated_at'):
                review['updated_at'] = review['updated_at'].isoformat()
        
        return jsonify({
            'total_reviews': len(reviews),
            'reviews': reviews
        }), 200
        
    except Exception as e:
        print(f"Error fetching my reviews: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch reviews: {str(e)}'}), 500
