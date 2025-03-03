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

def force_refresh():
    """Force refresh the dashboard data for Alex"""
    conn = get_db_connection()
    
    try:
        # Get Alex's ID
        alex = conn.execute("SELECT id FROM children WHERE name = 'Alex'").fetchone()
        
        if not alex:
            print("ERROR: Alex not found in the database!")
            return
        
        child_id = alex['id']
        
        # Update the current session with the latest data from your update_alex_data.py run
        conn.execute(
            """
            UPDATE current_sessions
            SET app_name = ?, start_time = ?, duration_minutes = ?
            WHERE child_id = ?
            """,
            ('Terminal', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 30, child_id)
        )
        
        # If no rows were updated, insert a new record
        if conn.total_changes == 0:
            conn.execute(
                """
                INSERT INTO current_sessions (child_id, app_name, start_time, duration_minutes)
                VALUES (?, ?, ?, ?)
                """,
                (child_id, 'Terminal', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 30)
            )
        
        # Update Alex's status
        try:
            conn.execute(
                """
                UPDATE children
                SET status = ?
                WHERE id = ?
                """,
                ('Online', child_id)
            )
        except sqlite3.OperationalError:
            print("Note: Could not update status (column may not exist)")
        
        conn.commit()
        print("Database updated successfully!")
        print("Please refresh your dashboard to see the changes.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    force_refresh() 