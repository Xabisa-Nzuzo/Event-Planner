from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import json
import os
import random
import string
import re
from datetime import datetime
from functools import wraps

import os
print("Current working directory:", os.getcwd())
print("Templates directory exists:", os.path.exists('Templates'))
if os.path.exists('Templates'):
    print("Files in Templates directory:", os.listdir('Templates'))
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Data storage files
USERS_FILE = "users.json"
EVENTS_FILE = "events.json"

def initialize_data_files():
    """Initialize JSON files for data storage"""
    for file in [USERS_FILE, EVENTS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump([], f)

def load_data(filename):
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return False

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_password(length=12):
    """Generate a strong random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login')
        
        users = load_data(USERS_FILE)
        
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['user'] = user
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form['email'].strip()
        
        if not all([username, password, email]):
            flash('Please fill in all fields', 'error')
            return render_template('register')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('register')
        
        users = load_data(USERS_FILE)
        
        if any(user['username'] == username for user in users):
            flash('Username already exists', 'error')
            return render_template('register')
        
        new_user = {
            'username': username,
            'password': password,
            'email': email
        }
        
        users.append(new_user)
        
        if save_data(USERS_FILE, users):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register')

@app.route('/dashboard')
@login_required
def dashboard():
    events = load_data(EVENTS_FILE)
    user_events = [e for e in events if e['creator'] == session['user']['username']]
    
    # Get recent events (last 5)
    recent_events = user_events[-5:] if user_events else []
    
    return render_template('dashboard.html', 
                         user=session['user'],
                         events=recent_events,
                         total_events=len(user_events))

@app.route('/events')
@login_required
def events():
    events_list = load_data(EVENTS_FILE)
    user_events = [e for e in events_list if e['creator'] == session['user']['username']]
    return render_template('events.html', events=user_events)

@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        name = request.form['name'].strip()
        date = request.form['date'].strip()
        location = request.form['location'].strip()
        description = request.form['description'].strip()
        
        if not all([name, date, location]):
            flash('Please fill in all required fields', 'error')
            return render_template('create_event.html')
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            flash('Please enter date in YYYY-MM-DD format', 'error')
            return render_template('create_event.html')
        
        event_password = generate_password()
        
        events = load_data(EVENTS_FILE)
        new_event = {
            'id': len(events) + 1,
            'name': name,
            'date': date,
            'location': location,
            'description': description,
            'creator': session['user']['username'],
            'password': event_password,
            'guests': [],
            'created_at': datetime.now().isoformat()
        }
        
        events.append(new_event)
        
        if save_data(EVENTS_FILE, events):
            flash(f'Event created successfully! Event Password: {event_password}', 'success')
            return redirect(url_for('events'))
        else:
            flash('Failed to create event', 'error')
    
    return render_template('create_event.html')

@app.route('/events/<int:event_id>/guests', methods=['GET', 'POST'])
@login_required
def manage_guests(event_id):
    events_list = load_data(EVENTS_FILE)
    event = next((e for e in events_list if e['id'] == event_id), None)
    
    if not event or event['creator'] != session['user']['username']:
        flash('Event not found or access denied', 'error')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        if 'add_guest' in request.form:
            name = request.form['guest_name'].strip()
            email = request.form['guest_email'].strip()
            
            if not all([name, email]):
                flash('Please fill in all guest fields', 'error')
            elif not validate_email(email):
                flash('Please enter a valid email address', 'error')
            elif any(g['email'] == email for g in event['guests']):
                flash('Guest with this email already exists', 'error')
            else:
                event['guests'].append({
                    'name': name,
                    'email': email,
                    'invited_at': datetime.now().isoformat()
                })
                
                # Update events data
                for e in events_list:
                    if e['id'] == event_id:
                        e['guests'] = event['guests']
                        break
                
                if save_data(EVENTS_FILE, events_list):
                    flash('Guest added successfully', 'success')
                else:
                    flash('Failed to add guest', 'error')
        
        elif 'remove_guest' in request.form:
            guest_email = request.form['guest_email']
            event['guests'] = [g for g in event['guests'] if g['email'] != guest_email]
            
            # Update events data
            for e in events_list:
                if e['id'] == event_id:
                    e['guests'] = event['guests']
                    break
            
            if save_data(EVENTS_FILE, events_list):
                flash('Guest removed successfully', 'success')
            else:
                flash('Failed to remove guest', 'error')
    
    return render_template('manage_guests.html', event=event)

@app.route('/events/<int:event_id>/send_invitations')
@login_required
def send_invitations(event_id):
    events_list = load_data(EVENTS_FILE)
    event = next((e for e in events_list if e['id'] == event_id), None)
    
    if not event or event['creator'] != session['user']['username']:
        flash('Event not found or access denied', 'error')
        return redirect(url_for('events'))
    
    if not event['guests']:
        flash('No guests to send invitations to', 'warning')
        return redirect(url_for('manage_guests', event_id=event_id))
    
    # Simulate sending invitations
    invitation_summary = []
    for guest in event['guests']:
        invitation_link = f"http://yourapp.com/events/{event_id}/join?token={generate_password(16)}"
        invitation_summary.append({
            'name': guest['name'],
            'email': guest['email'],
            'link': invitation_link
        })
    
    flash('Invitations prepared successfully! In a real application, these would be sent via email.', 'success')
    return render_template('invitation_summary.html', 
                         event=event, 
                         invitations=invitation_summary)

@app.route('/events/<int:event_id>/delete')
@login_required
def delete_event(event_id):
    events_list = load_data(EVENTS_FILE)
    events_list = [e for e in events_list if e['id'] != event_id]
    
    if save_data(EVENTS_FILE, events_list):
        flash('Event deleted successfully', 'success')
    else:
        flash('Failed to delete event', 'error')
    
    return redirect(url_for('events'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    initialize_data_files()
   
    app.run(host='0.0.0.0', port=0, debug=True)