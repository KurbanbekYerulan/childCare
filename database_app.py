from flask import Flask, jsonify, send_from_directory, request
import os
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['DEBUG'] = True

# Set up the frontend path
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
print(f"Frontend path: {frontend_path}")
print(f"Does frontend path exist? {os.path.exists(frontend_path)}")

# Database connection
def get_db_connection():
    """Connect to the database"""
    db_dir = os.path.join(os.path.dirname(__file__), 'Dashboard/data')
    db_path = os.path.join(db_dir, 'database.db')
    print(f"Connecting to database at: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Serve static files
@app.route('/')
def index():
    return send_from_directory(frontend_path, 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory(os.path.join(frontend_path, 'css'), path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory(os.path.join(frontend_path, 'js'), path)

# API endpoints using database
@app.route('/api/dashboard/summary')
def dashboard_summary():
    print("Dashboard summary requested")
    try:
        conn = get_db_connection()
        
        # Get total screen time
        total_screen_time = conn.execute(
            """
            SELECT SUM(duration) as total_minutes
            FROM app_usage
            WHERE date(start_time) = date('now')
            """
        ).fetchone()
        
        # Get productive screen time
        productive_time = conn.execute(
            """
            SELECT SUM(duration) as productive_minutes
            FROM app_usage
            WHERE date(start_time) = date('now') AND is_productive = 1
            """
        ).fetchone()
        
        # Get active alerts
        active_alerts = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM alerts
            WHERE resolved = 0
            """
        ).fetchone()
        
        conn.close()
        
        return jsonify({
            'total_screen_time': total_screen_time['total_minutes'] if total_screen_time['total_minutes'] else 0,
            'productive_time': productive_time['productive_minutes'] if productive_time['productive_minutes'] else 0,
            'active_alerts': active_alerts['count']
        })
    except Exception as e:
        print(f"Error in dashboard summary: {e}")
        # Return hardcoded data as fallback
        return jsonify({
            'total_screen_time': 120,
            'productive_time': 45,
            'active_alerts': 3,
            'error': str(e)
        })

@app.route('/api/children')
def get_children():
    print("Children data requested")
    try:
        conn = get_db_connection()
        
        # Check if current_sessions table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='current_sessions'"
        ).fetchone()
        
        if not table_exists:
            print("Creating current_sessions table...")
            conn.execute("""
                CREATE TABLE current_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    child_id INTEGER,
                    app_name TEXT,
                    start_time TEXT,
                    duration_minutes INTEGER,
                    FOREIGN KEY (child_id) REFERENCES children (id)
                )
            """)
            conn.commit()
        
        # Check if status column exists in children table
        cursor = conn.execute("PRAGMA table_info(children)")
        columns = [column[1] for column in cursor.fetchall()]
        has_status_column = 'status' in columns
        
        # Get all children
        if has_status_column:
            children_data = conn.execute(
                """
                SELECT c.id, c.name, c.age, c.device_type, c.status
                FROM children c
                """
            ).fetchall()
        else:
            children_data = conn.execute(
                """
                SELECT c.id, c.name, c.age, c.device_type
                FROM children c
                """
            ).fetchall()
        
        # Get current sessions
        current_sessions = {}
        sessions = conn.execute(
            """
            SELECT child_id, app_name, start_time, duration_minutes
            FROM current_sessions
            """
        ).fetchall()
        
        for session in sessions:
            current_sessions[session['child_id']] = {
                'app': session['app_name'],
                'start_time': session['start_time'],
                'duration': session['duration_minutes']
            }
        
        # Get current app from most recent app_usage
        recent_apps = {}
        for child in children_data:
            recent_app = conn.execute(
                """
                SELECT app_name
                FROM app_usage
                WHERE child_id = ?
                ORDER BY start_time DESC
                LIMIT 1
                """,
                (child['id'],)
            ).fetchone()
            
            if recent_app:
                recent_apps[child['id']] = recent_app['app_name']
        
        # Format children data
        children = []
        for child in children_data:
            child_dict = {
                'id': child['id'],
                'name': child['name'],
                'age': child['age'],
                'device_type': child['device_type'],
                'status': child['status'] if has_status_column else 'Unknown',
                'current_app': recent_apps.get(child['id'], None),
                'current_session': current_sessions.get(child['id'], None)
            }
            children.append(child_dict)
        
        conn.close()
        return jsonify(children)
    except Exception as e:
        print(f"Error getting children: {e}")
        import traceback
        traceback.print_exc()
        
        # Return hardcoded data as fallback
        return jsonify([
            {
                'id': 1,
                'name': 'Alex',
                'age': 10,
                'device_type': 'Tablet',
                'status': 'Online',
                'current_app': 'Terminal',
                'current_session': {
                    'app': 'Terminal',
                    'duration': 30,
                    'start_time': (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
                },
                'error': str(e)
            },
            {
                'id': 2,
                'name': 'Emma',
                'age': 8,
                'device_type': 'iPad',
                'status': 'Offline',
                'current_app': None,
                'current_session': None
            },
            {
                'id': 3,
                'name': 'Noah',
                'age': 12,
                'device_type': 'Laptop',
                'status': 'Online',
                'current_app': 'Minecraft',
                'current_session': {
                    'app': 'Minecraft',
                    'duration': 45,
                    'start_time': (datetime.now() - timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            {
                'id': 4,
                'name': 'Sophia',
                'age': 9,
                'device_type': 'Smartphone',
                'status': 'Online',
                'current_app': 'YouTube Kids',
                'current_session': {
                    'app': 'YouTube Kids',
                    'duration': 15,
                    'start_time': (datetime.now() - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        ])

@app.route('/api/alerts')
def get_alerts():
    print("Alerts data requested")
    try:
        conn = get_db_connection()
        
        # Get all unresolved alerts with child names
        alerts_data = conn.execute(
            """
            SELECT a.id, a.child_id, c.name as child_name, a.app_name, a.message, 
                   a.severity, a.timestamp, a.resolved
            FROM alerts a
            JOIN children c ON a.child_id = c.id
            WHERE a.resolved = 0
            ORDER BY a.timestamp DESC
            """
        ).fetchall()
        
        # Format alerts data
        alerts = []
        for alert in alerts_data:
            alerts.append({
                'id': alert['id'],
                'child_id': alert['child_id'],
                'child_name': alert['child_name'],
                'app_name': alert['app_name'],
                'message': alert['message'],
                'severity': alert['severity'],
                'timestamp': alert['timestamp']
            })
        
        conn.close()
        return jsonify(alerts)
    except Exception as e:
        print(f"Error getting alerts: {e}")
        
        # Return hardcoded data as fallback
        return jsonify([
            {
                'id': 1,
                'child_id': 1,
                'child_name': 'Alex',
                'app_name': 'Terminal',
                'message': 'Excessive screen time detected: Alex has used Terminal multiple times today',
                'severity': 'MEDIUM',
                'timestamp': (datetime.now() - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e)
            },
            {
                'id': 2,
                'child_id': 3,
                'child_name': 'Noah',
                'app_name': 'Minecraft',
                'message': 'Extended gaming session: Noah has been playing Minecraft for over 45 minutes',
                'severity': 'LOW',
                'timestamp': (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'id': 3,
                'child_id': 4,
                'child_name': 'Sophia',
                'app_name': 'YouTube Kids',
                'message': 'Content warning: Some videos may not be age-appropriate',
                'severity': 'HIGH',
                'timestamp': (datetime.now() - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ])

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    print(f"Resolve alert requested for alert ID: {alert_id}")
    try:
        conn = get_db_connection()
        
        # Update the alert to mark it as resolved
        conn.execute(
            """
            UPDATE alerts
            SET resolved = 1, resolved_at = ?
            WHERE id = ?
            """,
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), alert_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Alert {alert_id} resolved'})
    except Exception as e:
        print(f"Error resolving alert: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/debug')
def debug_info():
    """Return debug information about the app"""
    try:
        conn = get_db_connection()
        
        # Get database tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table['name']
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_names = [column[1] for column in columns]
            
            # Get row count
            row_count = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
            
            table_info[table_name] = {
                'columns': column_names,
                'row_count': row_count
            }
        
        conn.close()
        
        return jsonify({
            'frontend_path': frontend_path,
            'frontend_exists': os.path.exists(frontend_path),
            'database_info': {
                'tables': table_info
            }
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'frontend_path': frontend_path,
            'frontend_exists': os.path.exists(frontend_path)
        })

@app.route('/api/update-data', methods=['POST'])
def update_data():
    try:
        # Import your update script
        import update_alex_data
        
        # Run the update function
        update_alex_data.update_alex_data()
        
        return jsonify({'success': True, 'message': 'Data updated successfully'})
    except Exception as e:
        print(f"Error updating data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-alerts', methods=['POST'])
def check_alerts():
    try:
        # Import your modules
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))
        from screenpipe_connector import ScreenpipeConnector
        from llama_client import LlamaClient
        from query_engine import QueryEngine
        
        # Initialize components
        screenpipe = ScreenpipeConnector()
        llama = LlamaClient()
        query_engine = QueryEngine(screenpipe, llama)
        
        # Get current app info
        app_info = screenpipe.get_current_app_info()
        app_name = app_info.get('app_name', 'Unknown App')
        
        # Get OCR text
        ocr_text = screenpipe.get_recent_ocr_text()
        
        # Analyze content
        analysis_query = """
        Analyze this content and determine if it's appropriate for children.
        Is it appropriate? (Yes/No)
        Any potential concerns?
        """
        
        analysis_result = llama.query(ocr_text, analysis_query)
        
        # Check if inappropriate
        is_inappropriate = "not appropriate" in analysis_result.lower() or "inappropriate" in analysis_result.lower()
        
        # Extract concerns
        concerns = []
        if "concern" in analysis_result.lower():
            concerns_section = analysis_result.lower().split("concern")[1].split("\n")[0]
            concerns = [concerns_section.strip()]
        
        # Connect to database
        conn = get_db_connection()
        
        new_alerts = 0
        
        # Create alert if inappropriate
        if is_inappropriate:
            print(f"Creating alert for inappropriate content in {app_name}")
            conn.execute(
                """
                INSERT INTO alerts 
                (child_id, app_name, message, severity, timestamp, resolved) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    1,  # Assuming child_id 1 is Alex
                    app_name, 
                    f"Potentially inappropriate content detected in {app_name}: {', '.join(concerns) if concerns else 'Content may not be suitable for children'}", 
                    "HIGH", 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    0
                )
            )
            new_alerts += 1
        
        # Check for excessive screen time
        today = datetime.now().strftime('%Y-%m-%d')
        usage_count = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM app_usage
            WHERE child_id = ? AND date(start_time) = ?
            """,
            (1, today)  # Assuming child_id 1 is Alex
        ).fetchone()['count']
        
        if usage_count >= 3:
            print("Creating alert for excessive screen time")
            conn.execute(
                """
                INSERT INTO alerts 
                (child_id, app_name, message, severity, timestamp, resolved) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    1,  # Assuming child_id 1 is Alex
                    app_name, 
                    f"Excessive screen time detected: Alex has used {app_name} multiple times today, totaling over {usage_count * 15} minutes", 
                    "MEDIUM", 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    0
                )
            )
            new_alerts += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'new_alerts': new_alerts,
            'message': f'Check complete. {new_alerts} new alert(s) created.'
        })
    except Exception as e:
        print(f"Error checking for alerts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e), 'new_alerts': 0}), 500

if __name__ == '__main__':
    app.run(debug=True) 