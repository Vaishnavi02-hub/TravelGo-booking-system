"""
TravelGo - Complete Travel Booking Application
A full-stack Flask application for booking buses, trains, flights, and hotels
Integrated with AWS DynamoDB and SNS
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# AWS Configuration
USE_AWS = os.environ.get('USE_AWS', 'False').lower() == 'true'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
USERS_TABLE_NAME = os.environ.get('USERS_TABLE', 'TravelGo_Users')
BOOKINGS_TABLE_NAME = os.environ.get('BOOKINGS_TABLE', 'TravelGo_Bookings')

# Initialize AWS services if enabled
dynamodb = None
sns_client = None
users_table = None
bookings_table = None

if USE_AWS:
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        sns_client = boto3.client('sns', region_name=AWS_REGION)
        users_table = dynamodb.Table(USERS_TABLE_NAME)
        bookings_table = dynamodb.Table(BOOKINGS_TABLE_NAME)
        print("✓ AWS services initialized successfully")
    except Exception as e:
        print(f"⚠ AWS initialization failed: {e}")
        print("✓ Falling back to local in-memory storage")
        USE_AWS = False

# In-memory storage (fallback when AWS is not available)
if not USE_AWS:
    users_db = {}
    bookings_db = {}
    print("✓ Using local in-memory storage")


# ============================================================================
# DEMO DATA - Travel Options
# ============================================================================

BUS_OPTIONS = [
    {'id': 'bus1', 'name': 'Express Travels', 'from': 'Mumbai', 'to': 'Pune', 'price': 800, 'date': '2026-03-15', 'time': '08:00 AM', 'seats': ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']},
    {'id': 'bus2', 'name': 'City Connect', 'from': 'Bangalore', 'to': 'Chennai', 'price': 1200, 'date': '2026-03-16', 'time': '09:30 AM', 'seats': ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']},
    {'id': 'bus3', 'name': 'Metro Express', 'from': 'Hyderabad', 'to': 'Kolkata', 'price': 1500, 'date': '2026-03-17', 'time': '07:00 AM', 'seats': ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']},
]

TRAIN_OPTIONS = [
    {'id': 'train1', 'name': 'Rajdhani Express', 'from': 'Mumbai', 'to': 'Delhi', 'price': 2500, 'date': '2026-03-15', 'time': '10:00 AM', 'class': 'Economy'},
    {'id': 'train2', 'name': 'Shatabdi Express', 'from': 'Ahmedabad', 'to': 'Bangalore', 'price': 3500, 'date': '2026-03-16', 'time': '11:30 AM', 'class': 'Business'},
    {'id': 'train3', 'name': 'Duronto Express', 'from': 'Hyderabad', 'to': 'Chennai', 'price': 4200, 'date': '2026-03-17', 'time': '02:00 PM', 'class': 'First Class'},
]

FLIGHT_OPTIONS = [
    {'id': 'flight1', 'name': 'Air India', 'from': 'Mumbai', 'to': 'Goa', 'price': 4500, 'date': '2026-03-15', 'time': '06:00 AM', 'class': 'Economy'},
    {'id': 'flight2', 'name': 'IndiGo', 'from': 'Bangalore', 'to': 'Delhi', 'price': 6500, 'date': '2026-03-16', 'time': '08:30 AM', 'class': 'Business'},
    {'id': 'flight3', 'name': 'SpiceJet', 'from': 'Hyderabad', 'to': 'Jaipur', 'price': 3800, 'date': '2026-03-17', 'time': '12:00 PM', 'class': 'Economy'},
]

HOTEL_OPTIONS = [
    {'id': 'hotel1', 'name': 'Taj Hotel', 'location': 'Mumbai', 'price': 8000, 'rating': 4.5, 'category': 'luxury', 'amenities': ['WiFi', 'Pool', 'Spa', 'Restaurant']},
    {'id': 'hotel2', 'name': 'Budget Inn', 'location': 'Bangalore', 'price': 2500, 'rating': 3.5, 'category': 'budget', 'amenities': ['WiFi', 'Parking']},
    {'id': 'hotel3', 'name': 'Seaside Resort', 'location': 'Goa', 'price': 12000, 'rating': 5.0, 'category': 'luxury', 'amenities': ['WiFi', 'Beach Access', 'Pool', 'Spa', 'Restaurant']},
    {'id': 'hotel4', 'name': 'City Center Lodge', 'location': 'Delhi', 'price': 3500, 'rating': 3.8, 'category': 'budget', 'amenities': ['WiFi', 'Breakfast']},
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def send_sns_notification(email, subject, message):
    """Send email notification via AWS SNS"""
    if USE_AWS and sns_client and SNS_TOPIC_ARN:
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=f"To: {email}\n\n{message}"
            )
            print(f"✓ SNS notification sent to {email}")
            return True
        except Exception as e:
            print(f"⚠ SNS notification failed: {e}")
            return False
    else:
        print(f"✓ [Mock] Email sent to {email}: {subject}")
        return True


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def create_user(email, password, name):
    """Create a new user in DynamoDB or local storage"""
    password_hash = generate_password_hash(password)
    user_data = {
        'email': email,
        'password': password_hash,
        'name': name,
        'created_at': datetime.now().isoformat()
    }
    
    if USE_AWS:
        try:
            users_table.put_item(Item=user_data)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    else:
        users_db[email] = user_data
        return True


def get_user(email):
    """Retrieve user from DynamoDB or local storage"""
    if USE_AWS:
        try:
            response = users_table.get_item(Key={'email': email})
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    else:
        return users_db.get(email)


def create_booking(booking_data):
    """Create a new booking in DynamoDB or local storage"""
    if USE_AWS:
        try:
            bookings_table.put_item(Item=booking_data)
            return True
        except Exception as e:
            print(f"Error creating booking: {e}")
            return False
    else:
        bookings_db[booking_data['booking_id']] = booking_data
        return True


def get_user_bookings(email):
    """Retrieve all bookings for a user"""
    if USE_AWS:
        try:
            response = bookings_table.scan(
                FilterExpression='user_email = :email',
                ExpressionAttributeValues={':email': email}
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting bookings: {e}")
            return []
    else:
        return [b for b in bookings_db.values() if b['user_email'] == email]


def delete_booking(booking_id):
    """Delete a booking"""
    if USE_AWS:
        try:
            bookings_table.delete_item(Key={'booking_id': booking_id})
            return True
        except Exception as e:
            print(f"Error deleting booking: {e}")
            return False
    else:
        if booking_id in bookings_db:
            del bookings_db[booking_id]
            return True
        return False


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def home():
    """Home page route"""
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('register'))
        
        # Check if user already exists
        if get_user(email):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        if create_user(email, password, name):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user(email)
        
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    return render_template('dashboard.html')


@app.route('/book/bus')
@login_required
def book_bus():
    """Bus booking page"""
    return render_template('booking.html', 
                         booking_type='bus',
                         options=BUS_OPTIONS,
                         title='Book Bus')


@app.route('/book/train')
@login_required
def book_train():
    """Train booking page"""
    return render_template('booking.html',
                         booking_type='train',
                         options=TRAIN_OPTIONS,
                         title='Book Train')


@app.route('/book/flight')
@login_required
def book_flight():
    """Flight booking page"""
    return render_template('booking.html',
                         booking_type='flight',
                         options=FLIGHT_OPTIONS,
                         title='Book Flight')


@app.route('/book/hotel')
@login_required
def book_hotel():
    """Hotel booking page"""
    category = request.args.get('category', 'all')
    
    if category == 'all':
        filtered_hotels = HOTEL_OPTIONS
    else:
        filtered_hotels = [h for h in HOTEL_OPTIONS if h['category'] == category]
    
    return render_template('booking.html',
                         booking_type='hotel',
                         options=filtered_hotels,
                         title='Book Hotel',
                         show_filter=True)


@app.route('/confirm-booking', methods=['POST'])
@login_required
def confirm_booking():
    """Confirm and process booking"""
    booking_type = request.form.get('booking_type')
    option_id = request.form.get('option_id')
    
    # Find the selected option
    all_options = {
        'bus': BUS_OPTIONS,
        'train': TRAIN_OPTIONS,
        'flight': FLIGHT_OPTIONS,
        'hotel': HOTEL_OPTIONS
    }
    
    selected_option = None
    for option in all_options.get(booking_type, []):
        if option['id'] == option_id:
            selected_option = option
            break
    
    if not selected_option:
        flash('Invalid booking option', 'danger')
        return redirect(url_for('dashboard'))
    
    # Generate booking ID
    booking_id = str(uuid.uuid4())[:8].upper()
    
    # Prepare booking data
    booking_data = {
        'booking_id': booking_id,
        'user_email': session['user_email'],
        'booking_type': booking_type,
        'option_id': option_id,
        'option_name': selected_option['name'],
        'price': selected_option['price'],
        'booking_date': datetime.now().isoformat(),
        'status': 'confirmed'
    }
    
    # Add type-specific data
    if booking_type == 'bus':
        booking_data['seat'] = request.form.get('seat')
        booking_data['from'] = selected_option['from']
        booking_data['to'] = selected_option['to']
        booking_data['travel_date'] = selected_option['date']
        booking_data['travel_time'] = selected_option['time']
    elif booking_type == 'train':
        booking_data['from'] = selected_option['from']
        booking_data['to'] = selected_option['to']
        booking_data['travel_date'] = selected_option['date']
        booking_data['travel_time'] = selected_option['time']
        booking_data['class'] = selected_option['class']
    elif booking_type == 'flight':
        booking_data['from'] = selected_option['from']
        booking_data['to'] = selected_option['to']
        booking_data['travel_date'] = selected_option['date']
        booking_data['travel_time'] = selected_option['time']
        booking_data['class'] = selected_option['class']
    elif booking_type == 'hotel':
        booking_data['location'] = selected_option['location']
        booking_data['check_in'] = request.form.get('check_in')
        booking_data['check_out'] = request.form.get('check_out')
        booking_data['guests'] = request.form.get('guests', '1')
    
    # Save booking
    if create_booking(booking_data):
        # Send confirmation notification
        send_sns_notification(
            session['user_email'],
            f'TravelGo Booking Confirmation - {booking_id}',
            f"""Dear {session['user_name']},

Your booking has been confirmed!

Booking ID: {booking_id}
Type: {booking_type.capitalize()}
Service: {selected_option['name']}
Price: ${selected_option['price']}

Thank you for choosing TravelGo!
"""
        )
        
        flash(f'Booking confirmed! Your booking ID is {booking_id}', 'success')
        return redirect(url_for('booking_history'))
    else:
        flash('Booking failed. Please try again.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/history')
@login_required
def booking_history():
    """View booking history"""
    bookings = get_user_bookings(session['user_email'])
    # Sort by booking date (newest first)
    bookings.sort(key=lambda x: x.get('booking_date', ''), reverse=True)
    return render_template('history.html', bookings=bookings)


@app.route('/cancel-booking/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    bookings = get_user_bookings(session['user_email'])
    booking = next((b for b in bookings if b['booking_id'] == booking_id), None)
    
    if not booking:
        flash('Booking not found', 'danger')
        return redirect(url_for('booking_history'))
    
    if delete_booking(booking_id):
        # Send cancellation notification
        send_sns_notification(
            session['user_email'],
            f'TravelGo Booking Cancellation - {booking_id}',
            f"""Dear {session['user_name']},

Your booking has been cancelled.

Booking ID: {booking_id}
Type: {booking['booking_type'].capitalize()}
Service: {booking['option_name']}

Refund will be processed within 5-7 business days.

Thank you for using TravelGo!
"""
        )
        
        flash('Booking cancelled successfully', 'success')
    else:
        flash('Cancellation failed. Please try again.', 'danger')
    
    return redirect(url_for('booking_history'))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('home.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500 error handler"""
    return render_template('home.html'), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("TravelGo Application Starting...")
    print(f"AWS Integration: {'Enabled' if USE_AWS else 'Disabled'}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
