import sqlite3
import os
from datetime import datetime

def get_db_connection():
    """Connect to the database"""
    db_dir = os.path.join(os.path.dirname(__file__), 'Dashboard/data')
    db_path = os.path.join(db_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_database():
    """Check the database for Aina's current data"""
    conn = get_db_connection()
    
    try:
        # Check if current_sessions table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='current_sessions'"
        ).fetchone()
        
        if not table_exists:
            print("ERROR: current_sessions table does not exist!")
            return
        
        # Get Aina's data
        aina = conn.execute(
            """
            SELECT c.id, c.name, c.age, c.device_type, c.status
            FROM children c
            WHERE c.name = 'aina'
            """
        ).fetchone()
        
        if not aina:
            print("ERROR: Aina not found in the database!")
            return
        
        print(f"Aina found in database (ID: {aina['id']})")
        print(f"Age: {aina['age']}")
        print(f"Device: {aina['device_type']}")
        print(f"Status: {aina['status'] if 'status' in aina else 'No status column'}")
        
        # Get current session
        current_session = conn.execute(
            """
            SELECT app_name, start_time, duration_minutes
            FROM current_sessions
            WHERE child_id = ?
            """,
            (aina['id'],)
        ).fetchone()
        
        if not current_session:
            print("ERROR: No current session found for Aina!")
        else:
            print(f"Current App: {current_session['app_name']}")
            print(f"Session Start: {current_session['start_time']}")
            print(f"Duration: {current_session['duration_minutes']} minutes")
        
        # Check recent app usage
        recent_usage = conn.execute(
            """
            SELECT app_name, start_time, end_time, duration
            FROM app_usage
            WHERE child_id = ?
            ORDER BY start_time DESC
            LIMIT 5
            """,
            (aina['id'],)
        ).fetchall()
        
        print("\nRecent app usage:")
        for usage in recent_usage:
            print(f"- {usage['app_name']} ({usage['duration']} min) from {usage['start_time']} to {usage['end_time']}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database() 