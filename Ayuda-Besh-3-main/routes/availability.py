# routes/availability.py

from flask import Blueprint, request, jsonify
from lib.mongodb import get_database
from lib.decorators import token_required
from datetime import datetime, timedelta
from bson.objectid import ObjectId

availability_bp = Blueprint('availability', __name__)

@availability_bp.route('/availability', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def manage_availability():
    """Get or update provider availability schedule"""
    try:
        db = get_database()
        provider_id = ObjectId(request.current_user['user_id'])
        
        if request.current_user.get('role') != 'provider':
            return jsonify({'error': 'Only providers can manage availability'}), 403
        
        if request.method == 'GET':
            # Get current availability
            availability = db.availability.find_one({'provider_id': provider_id})
            
            if not availability:
                # Return default availability (all days available, 9 AM - 6 PM)
                default_schedule = {
                    'monday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'tuesday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'wednesday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'thursday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'friday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'saturday': {'available': True, 'start': '09:00', 'end': '18:00', 'breaks': []},
                    'sunday': {'available': False, 'start': '09:00', 'end': '18:00', 'breaks': []}
                }
                return jsonify({
                    'provider_id': str(provider_id),
                    'schedule': default_schedule,
                    'specific_dates': [],
                    'timezone': 'Asia/Manila'
                }), 200
            
            availability['_id'] = str(availability['_id'])
            availability['provider_id'] = str(availability['provider_id'])
            
            # Format dates
            if 'specific_dates' in availability:
                for date_entry in availability['specific_dates']:
                    if 'date' in date_entry and date_entry['date']:
                        date_entry['date'] = date_entry['date'].isoformat() if hasattr(date_entry['date'], 'isoformat') else str(date_entry['date'])
            
            return jsonify(availability), 200
        
        elif request.method == 'POST' or request.method == 'PUT':
            # Create or update availability
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body must be valid JSON'}), 400
            
            schedule = data.get('schedule', {})
            specific_dates = data.get('specific_dates', [])
            timezone = data.get('timezone', 'Asia/Manila')
            
            # Validate schedule format
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                if day in schedule:
                    day_schedule = schedule[day]
                    if 'available' not in day_schedule:
                        return jsonify({'error': f'Missing "available" field for {day}'}), 400
                    if day_schedule.get('available') and ('start' not in day_schedule or 'end' not in day_schedule):
                        return jsonify({'error': f'Missing start/end time for {day}'}), 400
            
            # Convert specific dates to datetime objects
            formatted_specific_dates = []
            for date_entry in specific_dates:
                if 'date' in date_entry:
                    try:
                        if isinstance(date_entry['date'], str):
                            date_entry['date'] = datetime.fromisoformat(date_entry['date'].replace('Z', '+00:00'))
                        formatted_specific_dates.append(date_entry)
                    except:
                        return jsonify({'error': f'Invalid date format: {date_entry.get("date")}'}), 400
            
            # Check if availability exists
            existing = db.availability.find_one({'provider_id': provider_id})
            
            availability_doc = {
                'provider_id': provider_id,
                'schedule': schedule,
                'specific_dates': formatted_specific_dates,
                'timezone': timezone,
                'updated_at': datetime.utcnow()
            }
            
            if existing:
                # Update existing
                result = db.availability.update_one(
                    {'provider_id': provider_id},
                    {'$set': availability_doc}
                )
                message = 'Availability updated successfully'
            else:
                # Create new
                availability_doc['created_at'] = datetime.utcnow()
                result = db.availability.insert_one(availability_doc)
                message = 'Availability created successfully'
            
            return jsonify({
                'message': message,
                'availability': {
                    'provider_id': str(provider_id),
                    'schedule': schedule,
                    'specific_dates': specific_dates,
                    'timezone': timezone
                }
            }), 200
        
        elif request.method == 'DELETE':
            # Delete availability (reset to defaults)
            result = db.availability.delete_one({'provider_id': provider_id})
            return jsonify({'message': 'Availability deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error managing availability: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to manage availability: {str(e)}'}), 500

@availability_bp.route('/availability/check', methods=['POST'])
def check_availability():
    """Check if provider is available at a specific date/time"""
    try:
        db = get_database()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be valid JSON'}), 400
        
        provider_id = data.get('provider_id')
        requested_datetime = data.get('datetime')
        
        if not provider_id or not requested_datetime:
            return jsonify({'error': 'provider_id and datetime are required'}), 400
        
        try:
            provider_obj_id = ObjectId(provider_id)
            if isinstance(requested_datetime, str):
                requested_dt = datetime.fromisoformat(requested_datetime.replace('Z', '+00:00'))
            else:
                requested_dt = requested_datetime
        except:
            return jsonify({'error': 'Invalid provider_id or datetime format'}), 400
        
        # Get provider availability
        availability = db.availability.find_one({'provider_id': provider_obj_id})
        
        if not availability:
            # Default: available during weekdays 9 AM - 6 PM
            day_name = requested_dt.strftime('%A').lower()
            if day_name in ['saturday', 'sunday']:
                return jsonify({'available': False, 'reason': 'Provider not available on weekends'}), 200
            
            hour = requested_dt.hour
            if hour < 9 or hour >= 18:
                return jsonify({'available': False, 'reason': 'Outside working hours (9 AM - 6 PM)'}), 200
            
            return jsonify({'available': True}), 200
        
        # Check specific dates first (overrides regular schedule)
        specific_dates = availability.get('specific_dates', [])
        requested_date = requested_dt.date()
        
        for date_entry in specific_dates:
            if date_entry.get('date') and date_entry['date'].date() == requested_date:
                if not date_entry.get('available', True):
                    return jsonify({
                        'available': False,
                        'reason': date_entry.get('reason', 'Provider marked this date as unavailable')
                    }), 200
                # If available on specific date, check time
                if 'start' in date_entry and 'end' in date_entry:
                    requested_time = requested_dt.time()
                    start_time = datetime.strptime(date_entry['start'], '%H:%M').time()
                    end_time = datetime.strptime(date_entry['end'], '%H:%M').time()
                    
                    if requested_time < start_time or requested_time >= end_time:
                        return jsonify({
                            'available': False,
                            'reason': f'Outside working hours ({date_entry["start"]} - {date_entry["end"]})'
                        }), 200
                
                # Check breaks
                breaks = date_entry.get('breaks', [])
                requested_time = requested_dt.time()
                for break_period in breaks:
                    break_start = datetime.strptime(break_period['start'], '%H:%M').time()
                    break_end = datetime.strptime(break_period['end'], '%H:%M').time()
                    if break_start <= requested_time < break_end:
                        return jsonify({
                            'available': False,
                            'reason': 'During break time'
                        }), 200
                
                return jsonify({'available': True}), 200
        
        # Check regular schedule
        day_name = requested_dt.strftime('%A').lower()
        schedule = availability.get('schedule', {})
        
        if day_name not in schedule:
            return jsonify({'available': False, 'reason': 'Day not in schedule'}), 200
        
        day_schedule = schedule[day_name]
        if not day_schedule.get('available', False):
            return jsonify({'available': False, 'reason': f'Provider not available on {day_name}'}), 200
        
        # Check working hours
        requested_time = requested_dt.time()
        start_time = datetime.strptime(day_schedule['start'], '%H:%M').time()
        end_time = datetime.strptime(day_schedule['end'], '%H:%M').time()
        
        if requested_time < start_time or requested_time >= end_time:
            return jsonify({
                'available': False,
                'reason': f'Outside working hours ({day_schedule["start"]} - {day_schedule["end"]})'
            }), 200
        
        # Check breaks
        breaks = day_schedule.get('breaks', [])
        for break_period in breaks:
            break_start = datetime.strptime(break_period['start'], '%H:%M').time()
            break_end = datetime.strptime(break_period['end'], '%H:%M').time()
            if break_start <= requested_time < break_end:
                return jsonify({
                    'available': False,
                    'reason': 'During break time'
                }), 200
        
        return jsonify({'available': True}), 200
        
    except Exception as e:
        print(f"Error checking availability: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to check availability: {str(e)}'}), 500

@availability_bp.route('/availability/calendar', methods=['GET'])
@token_required
def get_calendar_view():
    """Get calendar view of availability for a month"""
    try:
        db = get_database()
        provider_id = ObjectId(request.current_user['user_id'])
        
        if request.current_user.get('role') != 'provider':
            return jsonify({'error': 'Only providers can view calendar'}), 403
        
        # Get month and year from query params
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        
        # Get availability
        availability = db.availability.find_one({'provider_id': provider_id})
        
        # Get existing bookings for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        bookings = list(db.bookings.find({
            'provider_id': provider_id,
            'booking_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }))
        
        # Build calendar
        calendar_data = []
        current_date = start_date
        
        while current_date < end_date:
            day_name = current_date.strftime('%A').lower()
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Check if available
            is_available = True
            reason = None
            
            if availability:
                # Check specific dates first
                specific_dates = availability.get('specific_dates', [])
                date_match = next((d for d in specific_dates if d.get('date') and d['date'].date() == current_date.date()), None)
                
                if date_match:
                    is_available = date_match.get('available', True)
                    if not is_available:
                        reason = date_match.get('reason', 'Marked as unavailable')
                else:
                    # Check regular schedule
                    schedule = availability.get('schedule', {})
                    if day_name in schedule:
                        is_available = schedule[day_name].get('available', False)
                        if not is_available:
                            reason = f'Not available on {day_name}'
            
            # Count bookings for this day
            day_bookings = [b for b in bookings if b['booking_time'].date() == current_date.date()]
            
            calendar_data.append({
                'date': date_str,
                'day_name': day_name,
                'available': is_available,
                'reason': reason,
                'bookings_count': len(day_bookings),
                'bookings': [
                    {
                        'id': str(b['_id']),
                        'time': b['booking_time'].isoformat() if hasattr(b['booking_time'], 'isoformat') else str(b['booking_time']),
                        'service_type': b.get('service_type', ''),
                        'status': b.get('status', ''),
                        'customer_name': b.get('customer_name', 'Unknown')
                    }
                    for b in day_bookings
                ]
            })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'month': month,
            'year': year,
            'calendar': calendar_data
        }), 200
        
    except Exception as e:
        print(f"Error getting calendar view: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get calendar view: {str(e)}'}), 500
