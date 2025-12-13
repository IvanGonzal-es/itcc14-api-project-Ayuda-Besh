# routes/bookings.py
from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from datetime import datetime
from bson.objectid import ObjectId

bookings_bp = Blueprint('bookings', __name__)

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

@bookings_bp.route('/payment-transactions', methods=['GET'])
@token_required
def get_payment_transactions():
    """Get payment transaction history for current user"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        role = request.current_user.get('role')
        
        # Get bookings that have payments (completed bookings or any with final_price)
        if role == 'customer':
            query = {'customer_id': user_id}
        else:  # provider
            query = {'provider_id': user_id}
        
        # Get all bookings and create transaction records
        bookings = list(db.bookings.find(query).sort('created_at', -1))
        
        transactions = []
        for booking in bookings:
            # Only include bookings with payments (completed or with final_price)
            if booking.get('status') == 'completed' or booking.get('final_price'):
                transaction = {
                    'transaction_id': str(booking['_id']),
                    'booking_id': str(booking['_id']),
                    'date': booking.get('completed_at', booking.get('created_at', datetime.utcnow())),
                    'amount': booking.get('final_price') or booking.get('price', 0),
                    'status': booking.get('status', 'pending'),
                    'payment_method': booking.get('payment_method', 'face_to_face'),  # Default to face-to-face
                    'service_type': booking.get('service_type', ''),
                }
                
                # Add provider/customer info
                if role == 'customer':
                    provider = db.users.find_one({'_id': booking['provider_id']})
                    transaction['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
                    transaction['type'] = 'payment_out'
                else:
                    customer = db.users.find_one({'_id': booking['customer_id']})
                    transaction['customer_name'] = customer.get('fullName', 'Unknown') if customer else 'Unknown'
                    transaction['type'] = 'payment_in'
                
                transactions.append(transaction)
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Format dates
        for transaction in transactions:
            if isinstance(transaction['date'], datetime):
                transaction['date'] = transaction['date'].isoformat()
        
        return jsonify(transactions), 200
    except Exception as e:
        print(f"Error fetching payment transactions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch transactions: {str(e)}'}), 500

@bookings_bp.route('/my-bookings', methods=['GET'])
@token_required
def get_my_bookings():
    """Get bookings for current user (customer or provider)"""
    db = get_database()
    user_id = ObjectId(request.current_user['user_id'])
    role = request.current_user['role']
    
    if role == 'customer':
        query = {'customer_id': user_id}
    else:  # provider
        query = {'provider_id': user_id}
    
    bookings = list(db.bookings.find(query).sort('created_at', -1))
    
    # Enhance bookings with user information
    for booking in bookings:
        # Store original ObjectId before converting to string
        provider_id_obj = booking['provider_id']
        customer_id_obj = booking['customer_id']
        
        booking['_id'] = str(booking['_id'])
        booking['customer_id'] = str(booking['customer_id'])
        booking['provider_id'] = str(booking['provider_id'])
        
        # Get provider/customer names if not already included
        if role == 'customer' and 'provider_name' not in booking:
            provider = db.users.find_one({'_id': provider_id_obj})
            # Use company name (username) for provider, fallback to fullName if username not available
            if provider:
                booking['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown'))
                booking['provider_company_name'] = provider.get('username', 'Unknown')
                booking['provider_owner_name'] = provider.get('fullName', 'Unknown')
            else:
                booking['provider_name'] = 'Unknown'
        
        if role == 'provider' and 'customer_name' not in booking:
            customer = db.users.find_one({'_id': customer_id_obj})
            booking['customer_name'] = customer['fullName'] if customer else 'Unknown'
            booking['customer_email'] = customer.get('email', '') if customer else ''
    
    return jsonify(bookings), 200

@bookings_bp.route('/<booking_id>/accept', methods=['POST'])
@token_required
def accept_booking(booking_id):
    """Provider accepts a booking"""
    try:
        db = get_database()
        result = db.bookings.update_one(
            {
                '_id': ObjectId(booking_id),
                'provider_id': ObjectId(request.current_user['user_id']),
                'status': 'pending'
            },
            {'$set': {'status': 'accepted', 'accepted_at': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Booking not found or already accepted'}), 404
        
        # Create notification for customer
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if booking:
            create_notification(
                booking['customer_id'],
                'Booking Accepted',
                f'Your booking for {booking.get("service_type", "service")} has been accepted by the provider.',
                'success',
                booking_id
            )
        
        return jsonify({'message': 'Booking accepted'}), 200
    except Exception as e:
        print(f"Error accepting booking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to accept booking: {str(e)}'}), 500

@bookings_bp.route('/<booking_id>/reject', methods=['POST'])
@token_required
def reject_booking(booking_id):
    """Provider rejects a booking"""
    try:
        data = request.get_json() or {}
        rejection_reason = data.get('reason', 'No reason provided')
        
        db = get_database()
        result = db.bookings.update_one(
            {
                '_id': ObjectId(booking_id),
                'provider_id': ObjectId(request.current_user['user_id']),
                'status': 'pending'
            },
            {
                '$set': {
                    'status': 'rejected',
                    'rejection_reason': rejection_reason,
                    'rejected_at': datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Booking not found or already processed'}), 404
        
        # Create notification for customer
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if booking:
            create_notification(
                booking['customer_id'],
                'Booking Rejected',
                f'Your booking for {booking.get("service_type", "service")} has been rejected. Reason: {rejection_reason}',
                'warning',
                booking_id
            )
        
        return jsonify({'message': 'Booking rejected'}), 200
    except Exception as e:
        print(f"Error rejecting booking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to reject booking: {str(e)}'}), 500

@bookings_bp.route('/<booking_id>/update-price', methods=['POST'])
@token_required
def update_booking_price(booking_id):
    """Provider updates the final price for a booking"""
    try:
        data = request.get_json()
        if not data or 'final_price' not in data:
            return jsonify({'error': 'Missing final_price field'}), 400
        
        final_price = float(data['final_price'])
        if final_price < 0:
            return jsonify({'error': 'Price must be positive'}), 400
        
        db = get_database()
        result = db.bookings.update_one(
            {
                '_id': ObjectId(booking_id),
                'provider_id': ObjectId(request.current_user['user_id']),
                'status': {'$in': ['pending', 'accepted']}
            },
            {'$set': {'final_price': final_price, 'price_updated_at': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Booking not found or cannot update price'}), 404
        return jsonify({'message': 'Price updated successfully'}), 200
    except Exception as e:
        print(f"Error updating booking price: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to update price: {str(e)}'}), 500

@bookings_bp.route('/<booking_id>/complete', methods=['POST'])
@token_required
def complete_booking(booking_id):
    """Provider marks booking as completed"""
    try:
        db = get_database()
        # Check if user is provider
        if request.current_user['role'] != 'provider':
            return jsonify({'error': 'Only providers can complete bookings'}), 403
        
        result = db.bookings.update_one(
            {
                '_id': ObjectId(booking_id),
                'provider_id': ObjectId(request.current_user['user_id']),
                'status': 'accepted'
            },
            {'$set': {'status': 'completed', 'completed_at': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Booking not found or not in accepted state'}), 404
        
        # Create notification for customer
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if booking:
            create_notification(
                booking['customer_id'],
                'Booking Completed',
                f'Your booking for {booking.get("service_type", "service")} has been marked as completed. Please rate your provider!',
                'success',
                booking_id
            )
        
        return jsonify({'message': 'Booking completed'}), 200
    except Exception as e:
        print(f"Error completing booking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to complete booking: {str(e)}'}), 500

@bookings_bp.route('/<booking_id>/rate', methods=['POST'])
@token_required
def rate_provider(booking_id):
    """Customer rates and reviews provider after completed booking"""
    try:
        db = get_database()
        data = request.get_json()
        
        # Validate input
        if not data or 'rating' not in data:
            return jsonify({'error': 'Rating is required'}), 400
        
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Optional review text
        review_text = data.get('review', '').strip() if data.get('review') else ''
        if review_text and len(review_text) > 1000:
            return jsonify({'error': 'Review text must be 1000 characters or less'}), 400
        
        # Check if user is customer and booking belongs to them
        user_id = ObjectId(request.current_user['user_id'])
        if request.current_user['role'] != 'customer':
            return jsonify({'error': 'Only customers can rate providers'}), 403
        
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking['customer_id'] != user_id:
            return jsonify({'error': 'You can only rate your own bookings'}), 403
        
        if booking['status'] != 'completed':
            return jsonify({'error': 'Can only rate completed bookings'}), 400
        
        # Get customer info for review
        customer = db.users.find_one({'_id': user_id})
        customer_name = customer.get('fullName', 'Anonymous') if customer else 'Anonymous'
        
        # Prepare update data
        update_data = {
            'rating': rating,
            'rated_at': datetime.utcnow()
        }
        
        # Add review if provided
        if review_text:
            update_data['review'] = review_text
            update_data['reviewed_at'] = datetime.utcnow()
        
        # Update booking with rating and optional review
        result = db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Failed to update rating'}), 500
        
        # Create or update review document in reviews collection
        provider_id = booking['provider_id']
        review_doc = {
            'booking_id': ObjectId(booking_id),
            'provider_id': provider_id,
            'customer_id': user_id,
            'customer_name': customer_name,
            'rating': rating,
            'review': review_text if review_text else None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Check if review already exists for this booking
        existing_review = db.reviews.find_one({'booking_id': ObjectId(booking_id)})
        if existing_review:
            # Update existing review
            db.reviews.update_one(
                {'booking_id': ObjectId(booking_id)},
                {'$set': {
                    'rating': rating,
                    'review': review_text if review_text else existing_review.get('review'),
                    'updated_at': datetime.utcnow()
                }}
            )
        else:
            # Create new review
            db.reviews.insert_one(review_doc)
        
        # Calculate and update provider's average rating
        provider_bookings = list(db.bookings.find({
            'provider_id': provider_id,
            'rating': {'$exists': True, '$ne': None}
        }))
        
        avg_rating = rating
        if provider_bookings:
            total_rating = sum(b.get('rating', 0) for b in provider_bookings)
            avg_rating = total_rating / len(provider_bookings)
            
            # Update provider's rating
            db.users.update_one(
                {'_id': provider_id},
                {'$set': {'rating': round(avg_rating, 2)}}
            )
        
        # Create notification for provider about the review
        create_notification(
            provider_id,
            'New Review Received',
            f'You received a {rating}-star rating{" with a review" if review_text else ""} from {customer_name}.',
            'success',
            booking_id
            )
        
        return jsonify({
            'message': 'Rating and review submitted successfully',
            'average_rating': round(avg_rating, 2),
            'review_added': bool(review_text)
        }), 200
    except Exception as e:
        print(f"Error rating provider: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to submit rating: {str(e)}'}), 500

@bookings_bp.route('/<booking_id>/cancel', methods=['POST'])
@token_required
def cancel_booking(booking_id):
    """Customer cancels a booking"""
    try:
        db = get_database()
        user_id = ObjectId(request.current_user['user_id'])
        role = request.current_user['role']
        
        # Find the booking
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check permissions: customer can cancel their own bookings, provider can cancel their bookings
        if role == 'customer':
            if booking['customer_id'] != user_id:
                return jsonify({'error': 'You can only cancel your own bookings'}), 403
        elif role == 'provider':
            if booking['provider_id'] != user_id:
                return jsonify({'error': 'You can only cancel bookings assigned to you'}), 403
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if booking can be cancelled (only pending or accepted bookings can be cancelled)
        if booking['status'] not in ['pending', 'accepted']:
            return jsonify({'error': f'Cannot cancel booking with status: {booking["status"]}'}), 400
        
        # Get cancellation reason if provided
        data = request.get_json() or {}
        cancellation_reason = data.get('reason', 'Cancelled by user')
        
        # Update booking status
        result = db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'cancelled_at': datetime.utcnow(),
                    'cancelled_by': str(user_id),
                    'cancellation_reason': cancellation_reason
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Failed to cancel booking'}), 500
        
        # Create notification for the other party
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        if booking:
            if role == 'customer':
                # Notify provider
                create_notification(
                    booking['provider_id'],
                    'Booking Cancelled',
                    f'A customer has cancelled their booking for {booking.get("service_type", "service")}.',
                    'warning',
                    booking_id
                )
            else:
                # Notify customer
                create_notification(
                    booking['customer_id'],
                    'Booking Cancelled',
                    f'Your booking for {booking.get("service_type", "service")} has been cancelled by the provider.',
                    'warning',
                    booking_id
                )
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
    except Exception as e:
        print(f"Error cancelling booking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to cancel booking: {str(e)}'}), 500