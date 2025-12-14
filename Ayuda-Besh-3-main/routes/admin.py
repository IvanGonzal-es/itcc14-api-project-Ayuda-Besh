# routes/admin.py
from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import admin_required, token_required
from datetime import datetime, timedelta
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__)

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

@admin_bp.route('/providers/pending', methods=['GET'])
@token_required
@admin_required
def get_pending_providers():
    """Get all pending (unverified) providers"""
    try:
        db = get_database()
        # Get providers that are not verified and not rejected
        # This query finds all providers where is_verified is not True and is_rejected is not True
        providers = list(db.users.find({
            'role': 'provider',
            '$and': [
                {
                    '$or': [
                        {'is_verified': {'$exists': False}},
                        {'is_verified': False},
                        {'is_verified': None}
                    ]
                },
                {
                    '$or': [
                        {'is_rejected': {'$exists': False}},
                        {'is_rejected': False},
                        {'is_rejected': None}
                    ]
                }
            ]
        }, {'password': 0}).sort('createdAt', -1))  # Sort by newest first
        
        # Convert ObjectId to string and format response
        for provider in providers:
            provider['_id'] = str(provider['_id'])
            provider['services_offered'] = provider.get('services_offered', [])
            provider['location'] = provider.get('location', 'Not specified')
            provider['description'] = provider.get('description', 'No description')
            provider['hourly_rate'] = provider.get('hourly_rate', 0)
            # Ensure createdAt is serializable
            if 'createdAt' in provider and provider['createdAt']:
                provider['createdAt'] = provider['createdAt'].isoformat() if hasattr(provider['createdAt'], 'isoformat') else str(provider['createdAt'])
        
        return jsonify(providers), 200
    except Exception as e:
        print(f"Error fetching pending providers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch pending providers: {str(e)}'}), 500

@admin_bp.route('/providers/verified', methods=['GET'])
@token_required
@admin_required
def get_verified_providers():
    """Get all verified providers"""
    try:
        db = get_database()
        providers = list(db.users.find({
            'role': 'provider',
            'is_verified': True
        }, {'password': 0}).sort('verified_at', -1))  # Sort by verification date
        
        # Convert ObjectId to string and calculate stats
        for provider in providers:
            provider_id = provider['_id']  # Keep as ObjectId for query
            provider['_id'] = str(provider_id)  # Convert to string for JSON
            provider['services_offered'] = provider.get('services_offered', [])
            provider['location'] = provider.get('location', 'Not specified')
            
            # Calculate rating from completed bookings (use ObjectId for query)
            bookings = list(db.bookings.find({
                'provider_id': provider_id,
                'status': 'completed',
                'rating': {'$exists': True, '$ne': None}
            }))
            
            if bookings:
                total_rating = sum(b.get('rating', 0) for b in bookings)
                provider['rating'] = round(total_rating / len(bookings), 1)
                provider['total_jobs'] = len(bookings)
            else:
                provider['rating'] = 0
                provider['total_jobs'] = 0
            
            # Ensure dates are serializable
            if 'verified_at' in provider and provider['verified_at']:
                provider['verified_at'] = provider['verified_at'].isoformat() if hasattr(provider['verified_at'], 'isoformat') else str(provider['verified_at'])
        
        return jsonify(providers), 200
    except Exception as e:
        print(f"Error fetching verified providers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch verified providers: {str(e)}'}), 500

@admin_bp.route('/providers/<provider_id>', methods=['GET'])
@token_required
@admin_required
def get_provider_details(provider_id):
    """Get detailed information about a specific provider"""
    try:
        db = get_database()
        provider = db.users.find_one(
            {'_id': ObjectId(provider_id), 'role': 'provider'},
            {'password': 0}
        )
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Convert ObjectId to string
        provider['_id'] = str(provider['_id'])
        provider['services_offered'] = provider.get('services_offered', [])
        provider['location'] = provider.get('location', 'Not specified')
        provider['description'] = provider.get('description', 'No description provided')
        provider['hourly_rate'] = provider.get('hourly_rate', 0)
        
        # Format dates
        if 'createdAt' in provider and provider['createdAt']:
            provider['createdAt'] = provider['createdAt'].isoformat() if hasattr(provider['createdAt'], 'isoformat') else str(provider['createdAt'])
        if 'verified_at' in provider and provider['verified_at']:
            provider['verified_at'] = provider['verified_at'].isoformat() if hasattr(provider['verified_at'], 'isoformat') else str(provider['verified_at'])
        
        return jsonify(provider), 200
    except Exception as e:
        print(f"Error fetching provider details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch provider details: {str(e)}'}), 500

@admin_bp.route('/verify-provider/<provider_id>', methods=['POST'])
@token_required
@admin_required
def verify_provider(provider_id):
    """Admin verifies a provider"""
    try:
        db = get_database()
        result = db.users.update_one(
            {'_id': ObjectId(provider_id), 'role': 'provider'},
            {'$set': {'is_verified': True, 'verified_at': datetime.utcnow(), 'rejection_reason': None}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Provider not found'}), 404
        return jsonify({'message': 'Provider verified'}), 200
    except Exception as e:
        print(f"Error verifying provider: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to verify provider: {str(e)}'}), 500

@admin_bp.route('/reject-provider/<provider_id>', methods=['POST'])
@token_required
@admin_required
def reject_provider(provider_id):
    """Admin rejects a provider with a reason"""
    try:
        data = request.get_json()
        rejection_reason = data.get('reason', 'No reason provided')
        
        if not rejection_reason or rejection_reason.strip() == '':
            return jsonify({'error': 'Rejection reason is required'}), 400
        
        db = get_database()
        result = db.users.update_one(
            {'_id': ObjectId(provider_id), 'role': 'provider'},
            {'$set': {
                'is_verified': False,
                'is_rejected': True,
                'rejection_reason': rejection_reason,
                'rejected_at': datetime.utcnow()
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Provider not found'}), 404
        return jsonify({'message': 'Provider rejected'}), 200
    except Exception as e:
        print(f"Error rejecting provider: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to reject provider: {str(e)}'}), 500

@admin_bp.route('/delete-provider/<provider_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_provider(provider_id):
    """Admin deletes a provider account"""
    try:
        db = get_database()
        
        # Check if provider has any bookings
        bookings_count = db.bookings.count_documents({
            'provider_id': ObjectId(provider_id)
        })
        
        if bookings_count > 0:
            return jsonify({
                'error': f'Cannot delete provider with {bookings_count} booking(s). Please handle bookings first.'
            }), 400
        
        # Delete the provider
        result = db.users.delete_one({
            '_id': ObjectId(provider_id),
            'role': 'provider'
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Provider not found'}), 404
        
        return jsonify({'message': 'Provider deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting provider: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete provider: {str(e)}'}), 500

@admin_bp.route('/disputes', methods=['GET', 'POST'])
@token_required
def manage_disputes():
    """Get or create disputes"""
    db = get_database()
    if request.method == 'POST':
        # Allow customers to create disputes without admin_required
        data = request.get_json()
        dispute = {
            'booking_id': ObjectId(data['booking_id']),
            'customer_id': ObjectId(data['customer_id']),
            'provider_id': ObjectId(data['provider_id']),
            'description': data['description'],
            'status': 'open',
            'created_at': datetime.utcnow()
        }
        result = db.disputes.insert_one(dispute)
        return jsonify({'dispute_id': str(result.inserted_id), 'message': 'Dispute submitted successfully'}), 201
    else:
        # GET - admin sees all, provider sees only their own
        role = request.current_user.get('role')
        user_id = request.current_user.get('user_id')
        
        if role == 'admin':
            disputes = list(db.disputes.find().sort('created_at', -1))
        elif role == 'provider':
            disputes = list(db.disputes.find({'provider_id': ObjectId(user_id)}).sort('created_at', -1))
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        for dispute in disputes:
            dispute['_id'] = str(dispute['_id'])
            dispute['booking_id'] = str(dispute['booking_id'])
            dispute['customer_id'] = str(dispute['customer_id'])
            dispute['provider_id'] = str(dispute['provider_id'])
            # Add user names
            customer = db.users.find_one({'_id': ObjectId(dispute['customer_id'])})
            provider = db.users.find_one({'_id': ObjectId(dispute['provider_id'])})
            dispute['customer_name'] = customer['fullName'] if customer else 'Unknown'
            dispute['provider_name'] = provider['fullName'] if provider else 'Unknown'
        return jsonify(disputes), 200

@admin_bp.route('/reports', methods=['GET', 'POST'])
@token_required
def manage_reports():
    """Get or create reports"""
    db = get_database()
    if request.method == 'POST':
        # Allow customers to create reports without admin_required
        data = request.get_json()
        report = {
            'booking_id': ObjectId(data['booking_id']),
            'customer_id': ObjectId(data['customer_id']),
            'provider_id': ObjectId(data['provider_id']),
            'description': data.get('description', data.get('details', '')),  # Support both 'description' and 'details'
            'details': data.get('details', data.get('description', '')),  # Keep both for compatibility
            'type': data.get('type', 'service_report'),
            'status': 'pending',
            'checked': False,
            'created_at': datetime.utcnow()
        }
        result = db.reports.insert_one(report)
        return jsonify({'report_id': str(result.inserted_id), 'message': 'Report submitted successfully'}), 201
    else:
        # GET - admin sees all, provider sees only their own
        role = request.current_user.get('role')
        user_id = request.current_user.get('user_id')
        
        if role == 'admin':
            reports = list(db.reports.find().sort('created_at', -1))
        elif role == 'provider':
            reports = list(db.reports.find({'provider_id': ObjectId(user_id)}).sort('created_at', -1))
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        for report in reports:
            report['_id'] = str(report['_id'])
            report['booking_id'] = str(report['booking_id'])
            report['customer_id'] = str(report['customer_id'])
            report['provider_id'] = str(report['provider_id'])
            # Ensure description field exists (use details if description not present)
            if 'description' not in report and 'details' in report:
                report['description'] = report['details']
            if 'details' not in report and 'description' in report:
                report['details'] = report['description']
            # Ensure checked field exists
            if 'checked' not in report:
                report['checked'] = False
            # Add user names
            customer = db.users.find_one({'_id': ObjectId(report['customer_id'])})
            provider = db.users.find_one({'_id': ObjectId(report['provider_id'])})
            report['customer_name'] = customer['fullName'] if customer else 'Unknown'
            report['customer_email'] = customer.get('email', '') if customer else ''
            report['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
            report['provider_company_name'] = provider.get('username', 'Unknown') if provider else 'Unknown'
            report['provider_owner_name'] = provider.get('fullName', 'Unknown') if provider else 'Unknown'
            # Format dates
            if 'created_at' in report and report['created_at']:
                report['created_at'] = report['created_at'].isoformat() if hasattr(report['created_at'], 'isoformat') else str(report['created_at'])
        return jsonify(reports), 200

@admin_bp.route('/disputes/<dispute_id>', methods=['GET'])
@token_required
def get_dispute(dispute_id):
    """Get dispute details"""
    try:
        db = get_database()
        role = request.current_user.get('role')
        user_id = request.current_user.get('user_id')
        
        dispute = db.disputes.find_one({'_id': ObjectId(dispute_id)})
        if not dispute:
            return jsonify({'error': 'Dispute not found'}), 404
        
        # Check access: admin can see all, provider can only see their own
        if role == 'provider' and str(dispute['provider_id']) != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        dispute['_id'] = str(dispute['_id'])
        dispute['booking_id'] = str(dispute['booking_id'])
        dispute['customer_id'] = str(dispute['customer_id'])
        dispute['provider_id'] = str(dispute['provider_id'])
        
        # Add user names and booking details
        customer = db.users.find_one({'_id': ObjectId(dispute['customer_id'])})
        provider = db.users.find_one({'_id': ObjectId(dispute['provider_id'])})
        booking = db.bookings.find_one({'_id': ObjectId(dispute['booking_id'])})
        
        dispute['customer_name'] = customer['fullName'] if customer else 'Unknown'
        dispute['customer_email'] = customer.get('email', '') if customer else ''
        dispute['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
        dispute['provider_company_name'] = provider.get('username', 'Unknown') if provider else 'Unknown'
        dispute['provider_owner_name'] = provider.get('fullName', 'Unknown') if provider else 'Unknown'
        
        if booking:
            dispute['booking_details'] = {
                'service_type': booking.get('service_type', ''),
                'booking_time': booking.get('booking_time', '').isoformat() if booking.get('booking_time') else '',
                'service_address': booking.get('service_address', ''),
                'price': booking.get('price', 0),
                'final_price': booking.get('final_price', 0)
            }
        
        return jsonify(dispute), 200
    except Exception as e:
        print(f"Error fetching dispute: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch dispute: {str(e)}'}), 500

@admin_bp.route('/reports/<report_id>', methods=['GET'])
@token_required
def get_report(report_id):
    """Get report details"""
    try:
        db = get_database()
        role = request.current_user.get('role')
        user_id = request.current_user.get('user_id')
        
        report = db.reports.find_one({'_id': ObjectId(report_id)})
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access: admin can see all, provider can only see their own
        if role == 'provider' and str(report['provider_id']) != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        report['_id'] = str(report['_id'])
        report['booking_id'] = str(report['booking_id'])
        report['customer_id'] = str(report['customer_id'])
        report['provider_id'] = str(report['provider_id'])
        
        # Add user names and booking details
        customer = db.users.find_one({'_id': ObjectId(report['customer_id'])})
        provider = db.users.find_one({'_id': ObjectId(report['provider_id'])})
        booking = db.bookings.find_one({'_id': ObjectId(report['booking_id'])})
        
        report['customer_name'] = customer['fullName'] if customer else 'Unknown'
        report['customer_email'] = customer.get('email', '') if customer else ''
        report['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
        report['provider_company_name'] = provider.get('username', 'Unknown') if provider else 'Unknown'
        report['provider_owner_name'] = provider.get('fullName', 'Unknown') if provider else 'Unknown'
        
        if booking:
            report['booking_details'] = {
                'service_type': booking.get('service_type', ''),
                'booking_time': booking.get('booking_time', '').isoformat() if booking.get('booking_time') else '',
                'service_address': booking.get('service_address', ''),
                'price': booking.get('price', 0),
                'final_price': booking.get('final_price', 0)
            }
        
        # Ensure checked fields are properly serialized
        if 'checked_at' in report and report['checked_at']:
            report['checked_at'] = report['checked_at'].isoformat()
        if 'created_at' in report and report['created_at']:
            report['created_at'] = report['created_at'].isoformat()
        
        # Ensure checked field exists (default to False)
        if 'checked' not in report:
            report['checked'] = False
        
        return jsonify(report), 200
    except Exception as e:
        print(f"Error fetching report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch report: {str(e)}'}), 500

@admin_bp.route('/reports/<report_id>/check', methods=['POST'])
@token_required
@admin_required
def check_report(report_id):
    """Admin marks a report as checked/reviewed"""
    try:
        db = get_database()
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        result = db.reports.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': {
                'checked': True,
                'checked_at': datetime.utcnow(),
                'checked_by': request.current_user['user_id'],
                'check_notes': notes
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Report not found'}), 404
        return jsonify({'message': 'Report marked as checked successfully'}), 200
    except Exception as e:
        print(f"Error checking report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to check report: {str(e)}'}), 500

@admin_bp.route('/disputes/<dispute_id>/resolve', methods=['POST'])
@token_required
@admin_required
def resolve_dispute(dispute_id):
    """Admin resolves a dispute"""
    try:
        db = get_database()
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        
        result = db.disputes.update_one(
            {'_id': ObjectId(dispute_id)},
            {'$set': {
                'status': 'resolved',
                'resolved_at': datetime.utcnow(),
                'resolved_by': request.current_user['user_id'],
                'resolution_notes': resolution_notes
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Dispute not found'}), 404
        return jsonify({'message': 'Dispute resolved successfully'}), 200
    except Exception as e:
        print(f"Error resolving dispute: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to resolve dispute: {str(e)}'}), 500

@admin_bp.route('/disputes/<dispute_id>/response', methods=['POST'])
@token_required
def add_dispute_response(dispute_id):
    """Provider adds response to a dispute"""
    try:
        db = get_database()
        data = request.get_json()
        response_text = data.get('response', '')
        
        if not response_text:
            return jsonify({'error': 'Response text is required'}), 400
        
        role = request.current_user.get('role')
        user_id = request.current_user.get('user_id')
        
        dispute = db.disputes.find_one({'_id': ObjectId(dispute_id)})
        if not dispute:
            return jsonify({'error': 'Dispute not found'}), 404
        
        # Only provider can respond to their own disputes
        if role != 'provider' or str(dispute['provider_id']) != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Add response to dispute
        result = db.disputes.update_one(
            {'_id': ObjectId(dispute_id)},
            {'$push': {
                'responses': {
                    'text': response_text,
                    'responded_by': user_id,
                    'responded_at': datetime.utcnow()
                }
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Dispute not found'}), 404
        return jsonify({'message': 'Response added successfully'}), 200
    except Exception as e:
        print(f"Error adding dispute response: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to add response: {str(e)}'}), 500

@admin_bp.route('/reports/daily-bookings', methods=['GET'])
@token_required
@admin_required
def daily_bookings_report():
    """Generate daily bookings report"""
    try:
        db = get_database()
        
        # Get date from query parameter or use today
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            target_date = datetime.utcnow()
        
        # Set to start of day
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        bookings = list(db.bookings.find({
            'created_at': {
                '$gte': start_date,
                '$lt': end_date
            }
        }).sort('created_at', -1))
        
        # Enhance with customer/provider names and calculate totals
        total_revenue = 0
        status_counts = {'pending': 0, 'accepted': 0, 'completed': 0, 'rejected': 0, 'cancelled': 0}
        
        for booking in bookings:
            customer = db.users.find_one({'_id': booking['customer_id']})
            provider = db.users.find_one({'_id': booking['provider_id']})
            booking['customer_name'] = customer['fullName'] if customer else 'Unknown'
            booking['customer_email'] = customer.get('email', '') if customer else ''
            booking['provider_name'] = provider.get('username', provider.get('fullName', 'Unknown')) if provider else 'Unknown'
            booking['provider_company'] = provider.get('username', 'Unknown') if provider else 'Unknown'
            booking['_id'] = str(booking['_id'])
            booking['customer_id'] = str(booking['customer_id'])
            booking['provider_id'] = str(booking['provider_id'])
            
            # Format dates
            if 'created_at' in booking and booking['created_at']:
                booking['created_at'] = booking['created_at'].isoformat() if hasattr(booking['created_at'], 'isoformat') else str(booking['created_at'])
            if 'booking_time' in booking and booking['booking_time']:
                booking['booking_time'] = booking['booking_time'].isoformat() if hasattr(booking['booking_time'], 'isoformat') else str(booking['booking_time'])
            
            # Calculate revenue (use final_price if available, else price)
            price = booking.get('final_price') or booking.get('price', 0)
            if booking.get('status') == 'completed':
                total_revenue += price
            
            # Count by status
            status = booking.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1
        
        return jsonify({
            'date': date_str or target_date.strftime('%Y-%m-%d'),
            'total_bookings': len(bookings),
            'total_revenue': total_revenue,
            'status_breakdown': status_counts,
            'bookings': bookings
        }), 200
    except Exception as e:
        print(f"Error generating daily bookings report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@admin_bp.route('/reports/provider-activity', methods=['GET'])
@token_required
@admin_required
def provider_activity_report():
    """Provider activity report"""
    try:
        db = get_database()
        providers = list(db.users.find({'role': 'provider'}))
        
        report = []
        for provider in providers:
            provider_id = provider['_id']
            
            # Get all bookings for this provider
            all_bookings = list(db.bookings.find({'provider_id': provider_id}))
            completed_bookings = [b for b in all_bookings if b.get('status') == 'completed']
            pending_bookings = [b for b in all_bookings if b.get('status') == 'pending']
            accepted_bookings = [b for b in all_bookings if b.get('status') == 'accepted']
            
            # Calculate metrics
            total_jobs = len(completed_bookings)
            total_earnings = sum(b.get('final_price') or b.get('price', 0) for b in completed_bookings)
            
            # Calculate average rating
            rated_bookings = [b for b in completed_bookings if b.get('rating')]
            if rated_bookings:
                avg_rating = sum(b.get('rating', 0) for b in rated_bookings) / len(rated_bookings)
            else:
                avg_rating = 0
            
            # Get verification status
            is_verified = provider.get('is_verified', False)
            verification_date = provider.get('verified_at')
            if verification_date and hasattr(verification_date, 'isoformat'):
                verification_date = verification_date.isoformat()
            
            report.append({
                'provider_id': str(provider_id),
                'provider_name': provider.get('fullName', 'Unknown'),
                'company_name': provider.get('username', 'Unknown'),
                'location': provider.get('location', 'Not specified'),
                'is_verified': is_verified,
                'verified_at': verification_date,
                'total_jobs': total_jobs,
                'pending_jobs': len(pending_bookings),
                'accepted_jobs': len(accepted_bookings),
                'total_earnings': round(total_earnings, 2),
                'avg_rating': round(avg_rating, 2),
                'total_ratings': len(rated_bookings),
                'services_offered': provider.get('services_offered', [])
            })
        
        # Sort by total jobs (most active first)
        report.sort(key=lambda x: x['total_jobs'], reverse=True)
        
        return jsonify({
            'total_providers': len(report),
            'verified_providers': len([p for p in report if p['is_verified']]),
            'providers': report
        }), 200
    except Exception as e:
        print(f"Error generating provider activity report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@admin_bp.route('/reports/customer-history', methods=['GET'])
@token_required
@admin_required
def customer_history_report():
    """Generate customer history report"""
    try:
        db = get_database()
        
        # Get optional filters
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = {}
        if customer_id:
            try:
                query['customer_id'] = ObjectId(customer_id)
            except:
                return jsonify({'error': 'Invalid customer_id'}), 400
        
        if start_date or end_date:
            query['created_at'] = {}
            if start_date:
                try:
                    query['created_at']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
                except:
                    return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    query['created_at']['$lte'] = end_dt
                except:
                    return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Get customers
        if customer_id:
            customers = [db.users.find_one({'_id': ObjectId(customer_id), 'role': 'customer'})]
            customers = [c for c in customers if c]
        else:
            customers = list(db.users.find({'role': 'customer'}))
        
        report = []
        for customer in customers:
            customer_id_obj = customer['_id']
            
            # Get bookings for this customer
            customer_query = query.copy()
            customer_query['customer_id'] = customer_id_obj
            bookings = list(db.bookings.find(customer_query).sort('created_at', -1))
            
            # Calculate metrics
            total_bookings = len(bookings)
            completed_bookings = [b for b in bookings if b.get('status') == 'completed']
            total_spent = sum(b.get('final_price') or b.get('price', 0) for b in completed_bookings)
            
            # Get unique providers
            provider_ids = set(b['provider_id'] for b in bookings)
            
            # Get reviews given
            reviews = list(db.reviews.find({'customer_id': customer_id_obj}))
            
            report.append({
                'customer_id': str(customer_id_obj),
                'customer_name': customer.get('fullName', 'Unknown'),
                'email': customer.get('email', ''),
                'total_bookings': total_bookings,
                'completed_bookings': len(completed_bookings),
                'pending_bookings': len([b for b in bookings if b.get('status') == 'pending']),
                'total_spent': round(total_spent, 2),
                'unique_providers': len(provider_ids),
                'reviews_given': len(reviews),
                'registration_date': customer.get('createdAt').isoformat() if customer.get('createdAt') and hasattr(customer.get('createdAt'), 'isoformat') else None,
                'recent_bookings': [
                    {
                        'booking_id': str(b['_id']),
                        'service_type': b.get('service_type', ''),
                        'status': b.get('status', ''),
                        'created_at': b.get('created_at').isoformat() if b.get('created_at') and hasattr(b.get('created_at'), 'isoformat') else None,
                        'price': b.get('final_price') or b.get('price', 0)
                    }
                    for b in bookings[:5]  # Last 5 bookings
                ]
            })
        
        # Sort by total bookings (most active first)
        report.sort(key=lambda x: x['total_bookings'], reverse=True)
        
        return jsonify({
            'total_customers': len(report),
            'customers': report
        }), 200
    except Exception as e:
        print(f"Error generating customer history report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@admin_bp.route('/reports/provider-earnings', methods=['GET'])
@token_required
@admin_required
def provider_earnings_report():
    """Generate provider earnings report"""
    try:
        db = get_database()
        
        # Get optional filters
        provider_id = request.args.get('provider_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = {'status': 'completed'}
        if provider_id:
            try:
                query['provider_id'] = ObjectId(provider_id)
            except:
                return jsonify({'error': 'Invalid provider_id'}), 400
        
        if start_date or end_date:
            query['completed_at'] = {}
            if start_date:
                try:
                    query['completed_at']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
                except:
                    return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    query['completed_at']['$lte'] = end_dt
                except:
                    return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Get providers
        if provider_id:
            providers = [db.users.find_one({'_id': ObjectId(provider_id), 'role': 'provider'})]
            providers = [p for p in providers if p]
        else:
            providers = list(db.users.find({'role': 'provider', 'is_verified': True}))
        
        report = []
        total_platform_earnings = 0
        
        for provider in providers:
            provider_id_obj = provider['_id']
            
            # Get completed bookings for this provider
            provider_query = query.copy()
            provider_query['provider_id'] = provider_id_obj
            bookings = list(db.bookings.find(provider_query).sort('completed_at', -1))
            
            # Calculate earnings
            earnings = []
            total_earnings = 0
            for booking in bookings:
                price = booking.get('final_price') or booking.get('price', 0)
                total_earnings += price
                earnings.append({
                    'booking_id': str(booking['_id']),
                    'service_type': booking.get('service_type', ''),
                    'customer_name': db.users.find_one({'_id': booking['customer_id']}).get('fullName', 'Unknown') if db.users.find_one({'_id': booking['customer_id']}) else 'Unknown',
                    'amount': price,
                    'completed_at': booking.get('completed_at').isoformat() if booking.get('completed_at') and hasattr(booking.get('completed_at'), 'isoformat') else None
                })
            
            total_platform_earnings += total_earnings
            
            report.append({
                'provider_id': str(provider_id_obj),
                'provider_name': provider.get('fullName', 'Unknown'),
                'company_name': provider.get('username', 'Unknown'),
                'location': provider.get('location', 'Not specified'),
                'total_earnings': round(total_earnings, 2),
                'total_jobs': len(bookings),
                'avg_earnings_per_job': round(total_earnings / len(bookings), 2) if bookings else 0,
                'earnings_breakdown': earnings[:10]  # Last 10 earnings
            })
        
        # Sort by total earnings (highest first)
        report.sort(key=lambda x: x['total_earnings'], reverse=True)
        
        return jsonify({
            'total_providers': len(report),
            'total_platform_earnings': round(total_platform_earnings, 2),
            'providers': report
        }), 200
    except Exception as e:
        print(f"Error generating provider earnings report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@admin_required
def dashboard_stats():
    """Get dashboard statistics for admin with analytics"""
    try:
        db = get_database()
        
        # Total bookings (all time)
        total_bookings = db.bookings.count_documents({})
        
        # Bookings by status
        bookings_by_status = {
            'pending': db.bookings.count_documents({'status': 'pending'}),
            'accepted': db.bookings.count_documents({'status': 'accepted'}),
            'completed': db.bookings.count_documents({'status': 'completed'}),
            'rejected': db.bookings.count_documents({'status': 'rejected'}),
            'cancelled': db.bookings.count_documents({'status': 'cancelled'})
        }
        
        # Calculate total revenue from completed bookings
        completed_bookings = list(db.bookings.find({'status': 'completed'}))
        total_revenue = sum(b.get('final_price') or b.get('price', 0) for b in completed_bookings)
        
        # Today's bookings
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_bookings = db.bookings.count_documents({'created_at': {'$gte': today}})
        today_revenue = sum(
            (b.get('final_price') or b.get('price', 0)) 
            for b in db.bookings.find({'status': 'completed', 'completed_at': {'$gte': today}})
        )
        
        # This month's bookings
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_bookings = db.bookings.count_documents({'created_at': {'$gte': month_start}})
        month_revenue = sum(
            (b.get('final_price') or b.get('price', 0)) 
            for b in db.bookings.find({'status': 'completed', 'completed_at': {'$gte': month_start}})
        )
        
        # Active providers (verified providers)
        active_providers = db.users.count_documents({'role': 'provider', 'is_verified': True})
        pending_providers = db.users.count_documents({'role': 'provider', 'is_verified': {'$ne': True}})
        
        # Total customers
        total_customers = db.users.count_documents({'role': 'customer'})
        
        # Open disputes
        open_disputes = db.disputes.count_documents({'status': 'open'})
        total_disputes = db.disputes.count_documents({})
        
        # Average rating
        rated_bookings = list(db.bookings.find({
            'status': 'completed',
            'rating': {'$exists': True, '$ne': None}
        }))
        avg_rating = sum(b.get('rating', 0) for b in rated_bookings) / len(rated_bookings) if rated_bookings else 0
        
        return jsonify({
            'total_bookings': total_bookings,
            'bookings_by_status': bookings_by_status,
            'total_revenue': round(total_revenue, 2),
            'today_bookings': today_bookings,
            'today_revenue': round(today_revenue, 2),
            'month_bookings': month_bookings,
            'month_revenue': round(month_revenue, 2),
            'active_providers': active_providers,
            'pending_providers': pending_providers,
            'total_customers': total_customers,
            'open_disputes': open_disputes,
            'total_disputes': total_disputes,
            'average_rating': round(avg_rating, 2),
            'total_ratings': len(rated_bookings)
        }), 200
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@admin_bp.route('/accounts/<user_id>/disable', methods=['POST'])
@token_required
@admin_required
def disable_account(user_id):
    """Admin disables a user account for a specified duration"""
    try:
        db = get_database()
        data = request.get_json() or {}
        duration_days = data.get('duration_days', 0)  # 0 means permanent until manually enabled
        reason = data.get('reason', 'Account disabled by admin')
        
        if duration_days < 0:
            return jsonify({'error': 'Duration must be 0 (permanent) or positive number of days'}), 400
        
        # Calculate disable until date
        disable_until = None
        if duration_days > 0:
            disable_until = datetime.utcnow() + timedelta(days=duration_days)
        
        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'account_disabled': True,
                    'disabled_at': datetime.utcnow(),
                    'disabled_until': disable_until,
                    'disabled_reason': reason,
                    'disabled_by': request.current_user['user_id']
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404
        
        # Create notification for the user
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            duration_text = f' until {disable_until.strftime("%Y-%m-%d")}' if disable_until else ' permanently'
            create_notification(
                user_id,
                'Account Disabled',
                f'Your account has been disabled{duration_text} by an administrator. Reason: {reason}',
                'warning'
            )
        
        return jsonify({
            'message': f'Account disabled successfully{" until " + disable_until.isoformat() if disable_until else " permanently"}',
            'disabled_until': disable_until.isoformat() if disable_until else None
        }), 200
    except Exception as e:
        print(f"Error disabling account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to disable account: {str(e)}'}), 500

@admin_bp.route('/accounts/<user_id>/enable', methods=['POST'])
@token_required
@admin_required
def enable_account(user_id):
    """Admin re-enables a disabled user account"""
    try:
        db = get_database()
        
        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'account_disabled': False
                },
                '$unset': {
                    'disabled_at': '',
                    'disabled_until': '',
                    'disabled_reason': '',
                    'disabled_by': ''
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'Account enabled successfully'}), 200
    except Exception as e:
        print(f"Error enabling account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to enable account: {str(e)}'}), 500

@admin_bp.route('/accounts/deletion-requests', methods=['GET'])
@token_required
@admin_required
def get_deletion_requests():
    """Get all pending account deletion requests"""
    try:
        db = get_database()
        users = list(db.users.find({
            'deletion_requested': True,
            'account_disabled': True
        }, {'password': 0}).sort('deletion_requested_at', -1))
        
        for user in users:
            user['_id'] = str(user['_id'])
            if 'deletion_requested_at' in user and user['deletion_requested_at']:
                user['deletion_requested_at'] = user['deletion_requested_at'].isoformat() if hasattr(user['deletion_requested_at'], 'isoformat') else str(user['deletion_requested_at'])
        
        return jsonify(users), 200
    except Exception as e:
        print(f"Error fetching deletion requests: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch deletion requests: {str(e)}'}), 500

@admin_bp.route('/accounts/<user_id>/approve-deletion', methods=['POST'])
@token_required
@admin_required
def approve_account_deletion(user_id):
    """Admin approves and permanently deletes a user account"""
    try:
        db = get_database()
        
        # Check if user has any bookings
        bookings_count = db.bookings.count_documents({
            '$or': [
                {'customer_id': ObjectId(user_id)},
                {'provider_id': ObjectId(user_id)}
            ]
        })
        
        if bookings_count > 0:
            return jsonify({
                'error': f'Cannot delete account with {bookings_count} booking(s). Please handle bookings first or archive the account instead.'
            }), 400
        
        # Permanently delete the user
        result = db.users.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'User not found or already deleted'}), 404
        
        return jsonify({'message': 'Account deleted permanently'}), 200
    except Exception as e:
        print(f"Error approving account deletion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete account: {str(e)}'}), 500

@admin_bp.route('/accounts/<user_id>/reject-deletion', methods=['POST'])
@token_required
@admin_required
def reject_account_deletion(user_id):
    """Admin rejects account deletion request and re-enables the account"""
    try:
        db = get_database()
        data = request.get_json() or {}
        rejection_reason = data.get('reason', 'Deletion request rejected by admin')
        
        # Get user info before updating
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'account_disabled': False,
                    'deletion_rejected': True,
                    'deletion_rejection_reason': rejection_reason,
                    'deletion_rejected_at': datetime.utcnow()
                },
                '$unset': {
                    'deletion_requested': '',
                    'deletion_reason': '',
                    'deletion_requested_at': ''
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Failed to update account'}), 500
        
        # Create notification for the user about rejection
        create_notification(
            user_id,
            'Account Deletion Request Rejected',
            f'Your account deletion request has been rejected by an administrator. Your account has been re-enabled. Reason: {rejection_reason}',
            'info'
        )
        
        return jsonify({'message': 'Account deletion request rejected. Account has been re-enabled.'}), 200
    except Exception as e:
        print(f"Error rejecting account deletion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to reject deletion: {str(e)}'}), 500