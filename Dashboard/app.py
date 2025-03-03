from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
import sys
from datetime import datetime, timedelta
import threading
import time

# Add App directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'App'))

# Now import modules from App directory
try:
    from screenpipe_connector import ScreenpipeConnector
    from llama_client import LlamaClient
    from query_engine import QueryEngine
    import config
    SCREENPIPE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Screenpipe modules: {e}")
    SCREENPIPE_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# Disable CSRF protection for testing
app.config['WTF_CSRF_ENABLED'] = False

# Database setup
DB_PATH = 'dashboard.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Initializing database...")
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Define the monitoring function
def monitoring_function():
    """Background thread function to monitor screen activity and generate alerts."""
    try:
        while True:
            print("Monitoring thread running...")
            
            # Get database connection
            conn = get_db_connection()
            
            # Get all children
            children = conn.execute('SELECT id FROM children').fetchall()
            
            if not children:
                print("No children found in database.")
                conn.close()
                time.sleep(60)  # Sleep for 1 minute before checking again
                continue
            
            # Initialize components
            try:
                screenpipe = ScreenpipeConnector(config.SCREENPIPE_DB_PATH)
                llama = LlamaClient()
                query_engine = QueryEngine(screenpipe, llama, config.DEFAULT_TIME_WINDOW)
                
                # Get current app info
                app_info = screenpipe.get_current_app_info()
                
                if not app_info or not app_info.get('app_name'):
                    print("No active app detected.")
                    conn.close()
                    time.sleep(30)  # Sleep for 30 seconds before checking again
                    continue
                
                print(f"Detected app: {app_info['app_name']}")
                
                # Get app analysis
                analysis_result = query_engine.analyze_current_app()
                
                # Parse analysis to determine if app is appropriate
                is_appropriate = True
                if "not suitable for minors" in analysis_result.lower() or "not appropriate" in analysis_result.lower():
                    is_appropriate = False
                
                # For each child, record app usage and generate alerts if needed
                for child in children:
                    child_id = child['id']
                    
                    # Record app usage
                    conn.execute('''
                    INSERT INTO app_usage (
                        child_id, app_name, window_name, browser_url, 
                        start_time, category, is_appropriate
                    ) VALUES (?, ?, ?, ?, datetime('now'), ?, ?)
                    ''', (
                        child_id,
                        app_info['app_name'],
                        app_info.get('window_name', ''),
                        app_info.get('browser_url', ''),
                        'Unknown',  # Category - would come from analysis
                        1 if is_appropriate else 0
                    ))
                    
                    # Generate alert if app is not appropriate
                    if not is_appropriate:
                        conn.execute('''
                        INSERT INTO alerts (
                            child_id, app_name, window_name, browser_url, 
                            alert_type, severity, description, 
                            is_notified, is_resolved, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, datetime('now'))
                        ''', (
                            child_id,
                            app_info['app_name'],
                            app_info.get('window_name', ''),
                            app_info.get('browser_url', ''),
                            'inappropriate_content',
                            'high',
                            f"Child accessed inappropriate app: {app_info['app_name']}. Analysis: {analysis_result[:100]}..."
                        ))
                
                conn.commit()
                
            except Exception as e:
                print(f"Error in monitoring process: {e}")
            
            conn.close()
            time.sleep(60)  # Sleep for 1 minute before checking again
            
    except Exception as e:
        print(f"Error in monitoring thread: {e}")

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        # Get form data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract user data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        whatsapp_number = data.get('whatsapp_number')
        child_name = data.get('child_name')
        child_age = data.get('child_age')
        
        # Validate required fields
        if not all([username, password, email, whatsapp_number, child_name, child_age]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check if username already exists
        conn = get_db_connection()
        user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        
        if user:
            conn.close()
            return jsonify({'error': 'Username already exists'}), 400
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Insert the new user
        cursor = conn.execute(
            'INSERT INTO users (username, password_hash, email, whatsapp_number) VALUES (?, ?, ?, ?)',
            (username, password_hash, email, whatsapp_number)
        )
        user_id = cursor.lastrowid
        
        # Insert the child
        conn.execute(
            'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
            (user_id, child_name, child_age)
        )
        
        conn.commit()
        conn.close()
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'success': True, 'message': 'Registration successful'})
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    conn = get_db_connection()
    
    user = conn.execute(
        'SELECT id, username, password_hash FROM users WHERE username = ?',
        (data['username'],)
    ).fetchone()
    
    conn.close()
    
    if user and check_password_hash(user['password_hash'], data['password']):
        session['user_id'] = user['id']
        return jsonify({'success': True, 'user_id': user['id']})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Get children for this parent
    children = conn.execute(
        'SELECT id, name, age FROM children WHERE parent_id = ?',
        (user_id,)
    ).fetchall()
    
    result = {'children': []}
    
    for child in children:
        child_data = {
            'id': child['id'],
            'name': child['name'],
            'age': child['age'],
            'current_app': {},
            'daily_usage': [],
            'alerts': []
        }
        
        # Get current app
        current_app = conn.execute(
            '''SELECT au.*, aa.category, aa.is_appropriate, aa.age_rating, 
                      aa.educational_value, aa.potential_concerns, aa.alternatives
               FROM app_usage au
               LEFT JOIN app_analysis aa ON au.app_name = aa.app_name
               WHERE au.child_id = ? AND au.end_time IS NULL
               ORDER BY au.start_time DESC LIMIT 1''',
            (child['id'],)
        ).fetchone()
        
        if current_app:
            child_data['current_app'] = dict(current_app)
        
        # Get daily usage summary
        today = datetime.now().date().isoformat()
        
        daily_usage = conn.execute(
            '''SELECT app_name, SUM(duration) as total_duration
               FROM app_usage
               WHERE child_id = ? AND date(start_time) = ?
               AND duration IS NOT NULL
               GROUP BY app_name
               ORDER BY total_duration DESC''',
            (child['id'], today)
        ).fetchall()
        
        child_data['daily_usage'] = [dict(app) for app in daily_usage]
        
        # Get recent alerts
        alerts = conn.execute(
            '''SELECT * FROM alerts
               WHERE child_id = ?
               ORDER BY created_at DESC LIMIT 10''',
            (child['id'],)
        ).fetchall()
        
        child_data['alerts'] = [dict(alert) for alert in alerts]
        
        result['children'].append(child_data)
    
    conn.close()
    
    return jsonify(result)

@app.route('/api/dashboard/app_usage/<int:child_id>', methods=['GET'])
def app_usage(child_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Verify this child belongs to the logged-in parent
    conn = get_db_connection()
    child = conn.execute(
        'SELECT id FROM children WHERE id = ? AND parent_id = ?',
        (child_id, user_id)
    ).fetchone()
    
    if not child:
        conn.close()
        return jsonify({'error': 'Child not found'}), 404
    
    # Get date range from query parameters
    days = request.args.get('days', 7, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get app usage data
    usage_data = conn.execute(
        '''SELECT app_name, date(start_time) as date, SUM(duration) as total_duration
           FROM app_usage
           WHERE child_id = ? AND start_time >= ? AND duration IS NOT NULL
           GROUP BY app_name, date(start_time)
           ORDER BY date(start_time), total_duration DESC''',
        (child_id, start_date.isoformat())
    ).fetchall()
    
    # Format data for chart display
    result = {
        'labels': [],  # Dates
        'datasets': []  # One dataset per app
    }
    
    # Create a dictionary to organize data by app and date
    app_data = {}
    dates = set()
    
    for row in usage_data:
        app_name = row['app_name']
        date = row['date']
        duration = row['total_duration']
        
        if app_name not in app_data:
            app_data[app_name] = {}
        
        app_data[app_name][date] = duration
        dates.add(date)
    
    # Sort dates
    sorted_dates = sorted(list(dates))
    result['labels'] = sorted_dates
    
    # Create datasets
    for app_name, date_data in app_data.items():
        dataset = {
            'label': app_name,
            'data': [date_data.get(date, 0) / 60 for date in sorted_dates]  # Convert to minutes
        }
        result['datasets'].append(dataset)
    
    conn.close()
    
    return jsonify(result)

@app.route('/api/alerts/<int:child_id>', methods=['GET'])
def get_alerts(child_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Verify this child belongs to the logged-in parent
    conn = get_db_connection()
    child = conn.execute(
        'SELECT id FROM children WHERE id = ? AND parent_id = ?',
        (child_id, user_id)
    ).fetchone()
    
    if not child:
        conn.close()
        return jsonify({'error': 'Child not found'}), 404
    
    # Get alerts
    alerts = conn.execute(
        '''SELECT * FROM alerts
           WHERE child_id = ?
           ORDER BY created_at DESC''',
        (child_id,)
    ).fetchall()
    
    result = [dict(alert) for alert in alerts]
    
    conn.close()
    
    return jsonify(result)

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Verify this alert belongs to a child of the logged-in parent
    alert = conn.execute(
        '''SELECT a.id
           FROM alerts a
           JOIN children c ON a.child_id = c.id
           WHERE a.id = ? AND c.parent_id = ?''',
        (alert_id, user_id)
    ).fetchone()
    
    if not alert:
        conn.close()
        return jsonify({'error': 'Alert not found'}), 404
    
    # Mark alert as resolved
    conn.execute(
        'UPDATE alerts SET is_resolved = 1 WHERE id = ?',
        (alert_id,)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/debug', methods=['GET'])
def debug():
    """Simple endpoint to verify API is working."""
    return jsonify({
        'status': 'ok',
        'message': 'API server is running',
        'time': str(datetime.now())
    })

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Screenpipe Parental Control Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                ul { list-style-type: none; padding: 0; }
                li { margin-bottom: 10px; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Screenpipe Parental Control Dashboard API</h1>
            <p>Welcome to the Screenpipe Parental Control Dashboard API. Below are the available endpoints:</p>
            <ul>
                <li><a href="/api/login">/api/login</a> - Login endpoint (POST)</li>
                <li><a href="/api/register">/api/register</a> - Registration endpoint (POST)</li>
                <li><a href="/api/dashboard/summary">/api/dashboard/summary</a> - Dashboard summary (GET)</li>
                <li><a href="/api/alerts">/api/alerts</a> - Alerts list (GET)</li>
            </ul>
            <p>Note: This is the API server. The frontend application will be served separately.</p>
        </body>
    </html>
    """

@app.before_request
def log_request_info():
    """Log details about each request."""
    print(f"Request: {request.method} {request.path}")
    print(f"Headers: {dict(request.headers)}")
    if request.is_json:
        print(f"JSON Data: {request.json}")
    elif request.form:
        print(f"Form Data: {dict(request.form)}")

@app.after_request
def log_response_info(response):
    """Log details about each response."""
    print(f"Response: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    return response

@app.route('/api/alerts', methods=['GET'])
def get_all_alerts():
    """Get alerts for the logged-in user's children."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        
        # Get all children for this user
        children = conn.execute(
            'SELECT id FROM children WHERE parent_id = ?', 
            (session['user_id'],)
        ).fetchall()
        
        if not children:
            conn.close()
            return jsonify({'alerts': []})
        
        # Get alerts for all children
        child_ids = [child['id'] for child in children]
        placeholders = ','.join(['?'] * len(child_ids))
        
        alerts = conn.execute(
            f'SELECT * FROM alerts WHERE child_id IN ({placeholders}) ORDER BY created_at DESC',
            child_ids
        ).fetchall()
        
        # Convert to list of dicts
        alerts_list = []
        for alert in alerts:
            alerts_list.append({
                'id': alert['id'],
                'child_id': alert['child_id'],
                'app_name': alert['app_name'],
                'window_name': alert['window_name'],
                'browser_url': alert['browser_url'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                'description': alert['description'],
                'is_notified': bool(alert['is_notified']),
                'is_resolved': bool(alert['is_resolved']),
                'created_at': alert['created_at']
            })
        
        conn.close()
        return jsonify({'alerts': alerts_list})
        
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/current_app', methods=['GET'])
def get_active_app():
    """Get information about the currently active app."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Check if Screenpipe is available
        if not SCREENPIPE_AVAILABLE:
            return jsonify({
                'app_info': {
                    'app_name': 'Sample App',
                    'window_name': 'Sample Window',
                    'browser_url': 'https://example.com',
                    'is_appropriate': True,
                    'category': 'Education',
                    'age_rating': '7+',
                    'educational_value': 'High',
                    'potential_concerns': 'None',
                    'alternatives': 'N/A',
                    'last_updated': datetime.now().isoformat()
                }
            })
        
        # Initialize components
        screenpipe = ScreenpipeConnector(config.SCREENPIPE_DB_PATH)
        llama = LlamaClient()
        query_engine = QueryEngine(screenpipe, llama, config.DEFAULT_TIME_WINDOW)
        
        # Get current app info
        app_info = screenpipe.get_current_app_info()
        
        if not app_info or not app_info.get('app_name'):
            return jsonify({
                'app_info': {}
            })
        
        # Get app analysis
        analysis_result = query_engine.analyze_current_app()
        
        # Parse analysis to determine if app is appropriate
        is_appropriate = True
        if "not suitable for minors" in analysis_result.lower() or "not appropriate" in analysis_result.lower():
            is_appropriate = False
        
        # Check if we have cached analysis
        conn = get_db_connection()
        cached_analysis = conn.execute(
            'SELECT * FROM app_analysis WHERE app_name = ? AND window_name = ?',
            (app_info['app_name'], app_info.get('window_name', ''))
        ).fetchone()
        
        if cached_analysis:
            # Use cached analysis
            app_info.update({
                'is_appropriate': bool(cached_analysis['is_appropriate']),
                'category': cached_analysis['category'],
                'age_rating': cached_analysis['age_rating'],
                'educational_value': cached_analysis['educational_value'],
                'potential_concerns': cached_analysis['potential_concerns'],
                'alternatives': cached_analysis['alternatives'],
                'last_updated': cached_analysis['last_updated']
            })
        else:
            # Extract information from analysis
            app_info.update({
                'is_appropriate': is_appropriate,
                'category': 'Unknown',  # Would extract from analysis
                'age_rating': 'Unknown',  # Would extract from analysis
                'educational_value': 'Unknown',  # Would extract from analysis
                'potential_concerns': analysis_result[:100] if not is_appropriate else 'None',
                'alternatives': 'None',  # Would extract from analysis
                'last_updated': datetime.now().isoformat()
            })
            
            # Cache the analysis
            conn.execute('''
            INSERT INTO app_analysis (
                app_name, window_name, browser_url, category, is_appropriate,
                age_rating, educational_value, potential_concerns, alternatives,
                analysis_json, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (
                app_info['app_name'],
                app_info.get('window_name', ''),
                app_info.get('browser_url', ''),
                app_info['category'],
                1 if app_info['is_appropriate'] else 0,
                app_info['age_rating'],
                app_info['educational_value'],
                app_info['potential_concerns'],
                app_info['alternatives'],
                json.dumps(analysis_result)
            ))
            conn.commit()
        
        conn.close()
        return jsonify({'app_info': app_info})
        
    except Exception as e:
        print(f"Error getting current app: {e}")
        return jsonify({
            'error': str(e),
            'app_info': {}
        }), 500

if __name__ == '__main__':
    # Check if database exists, if not initialize it
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}, creating it...")
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        # Initialize the database
        init_db()
    else:
        # Check if tables exist
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='children';")
        if not cursor.fetchone():
            print("Database exists but tables are missing. Initializing tables...")
            init_db()
        conn.close()
    
    # Start the monitoring thread
    monitoring_thread = threading.Thread(target=monitoring_function, daemon=True)
    monitoring_thread.start()
    
    app.run(debug=True) 