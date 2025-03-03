import sqlite3
import os
from datetime import datetime, timedelta
import random

def get_db_connection():
    """Connect to the database"""
    db_dir = os.path.join(os.path.dirname(__file__), 'Dashboard/data')
    db_path = os.path.join(db_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def add_children():
    """Add multiple children to the database"""
    print("Adding children to the database...")
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Check if status column exists in children table
        cursor = conn.execute("PRAGMA table_info(children)")
        columns = [column[1] for column in cursor.fetchall()]
        has_status_column = 'status' in columns
        
        # Add status column if it doesn't exist
        if not has_status_column:
            try:
                conn.execute("ALTER TABLE children ADD COLUMN status TEXT DEFAULT 'Offline'")
                print("Added status column to children table")
            except sqlite3.OperationalError:
                print("Could not add status column (may already exist)")
        
        # Define children to add
        children = [
            {
                'name': 'Emma',
                'age': 8,
                'device_type': 'iPad',
                'status': 'Online'
            },
            {
                'name': 'Noah',
                'age': 12,
                'device_type': 'Laptop',
                'status': 'Offline'
            },
            {
                'name': 'Sophia',
                'age': 9,
                'device_type': 'Android Phone',
                'status': 'Online'
            }
        ]
        
        # Add each child
        for child in children:
            # Check if child already exists
            existing = conn.execute(
                "SELECT id FROM children WHERE name = ?",
                (child['name'],)
            ).fetchone()
            
            if existing:
                print(f"{child['name']} already exists, updating...")
                if has_status_column:
                    conn.execute(
                        """
                        UPDATE children 
                        SET age = ?, device_type = ?, status = ?
                        WHERE name = ?
                        """,
                        (child['age'], child['device_type'], child['status'], child['name'])
                    )
                else:
                    conn.execute(
                        """
                        UPDATE children 
                        SET age = ?, device_type = ?
                        WHERE name = ?
                        """,
                        (child['age'], child['device_type'], child['name'])
                    )
                child_id = existing['id']
            else:
                print(f"Adding new child: {child['name']}")
                if has_status_column:
                    conn.execute(
                        """
                        INSERT INTO children (parent_id, name, age, device_type, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (1, child['name'], child['age'], child['device_type'], child['status'])
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO children (parent_id, name, age, device_type)
                        VALUES (?, ?, ?, ?)
                        """,
                        (1, child['name'], child['age'], child['device_type'])
                    )
                child_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Add app usage data for each child
            add_app_usage(conn, child_id, child['name'])
            
            # Add alerts for each child
            add_alerts(conn, child_id, child['name'])
        
        # Create current_sessions table if it doesn't exist
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
        
        # Add current sessions for online children
        for child in children:
            if child['status'] == 'Online':
                child_id = conn.execute(
                    "SELECT id FROM children WHERE name = ?",
                    (child['name'],)
                ).fetchone()['id']
                
                # Delete any existing current session
                conn.execute("DELETE FROM current_sessions WHERE child_id = ?", (child_id,))
                
                # Add a new current session
                app_name = 'Minecraft' if child['name'] == 'Emma' else 'Khan Academy'
                start_time = datetime.now() - timedelta(minutes=random.randint(15, 60))
                duration = int((datetime.now() - start_time).total_seconds() / 60)
                
                conn.execute(
                    """
                    INSERT INTO current_sessions 
                    (child_id, app_name, start_time, duration_minutes) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        child_id, 
                        app_name, 
                        start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                        duration
                    )
                )
        
        # Commit all changes
        conn.commit()
        print("Successfully added children to the database!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error adding children: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_app_usage(conn, child_id, child_name):
    """Add app usage data for a child"""
    print(f"Adding app usage data for {child_name}...")
    
    # Define apps based on child
    if child_name == 'Emma':
        apps = [
            {"name": "Minecraft", "category": "Games", "productive": 1, "appropriate": 1},
            {"name": "YouTube Kids", "category": "Entertainment", "productive": 0, "appropriate": 1},
            {"name": "PBS Kids", "category": "Education", "productive": 1, "appropriate": 1}
        ]
    elif child_name == 'Noah':
        apps = [
            {"name": "Chrome", "category": "Productivity", "productive": 1, "appropriate": 1},
            {"name": "Roblox", "category": "Games", "productive": 0, "appropriate": 1},
            {"name": "Discord", "category": "Social Media", "productive": 0, "appropriate": 0}
        ]
    else:  # Sophia
        apps = [
            {"name": "Khan Academy", "category": "Education", "productive": 1, "appropriate": 1},
            {"name": "Netflix", "category": "Entertainment", "productive": 0, "appropriate": 1},
            {"name": "Duolingo", "category": "Education", "productive": 1, "appropriate": 1}
        ]
    
    # Add historical app usage
    for i in range(5):
        app = random.choice(apps)
        hist_start = datetime.now() - timedelta(hours=random.randint(1, 24))
        hist_end = hist_start + timedelta(minutes=random.randint(15, 60))
        hist_duration = int((hist_end - hist_start).total_seconds() / 60)
        
        conn.execute(
            """
            INSERT INTO app_usage 
            (child_id, app_name, category, is_productive, is_appropriate, start_time, end_time, duration) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                child_id, 
                app["name"], 
                app["category"], 
                app["productive"], 
                app["appropriate"], 
                hist_start.strftime('%Y-%m-%d %H:%M:%S'), 
                hist_end.strftime('%Y-%m-%d %H:%M:%S'), 
                hist_duration
            )
        )

def add_alerts(conn, child_id, child_name):
    """Add alerts for a child"""
    print(f"Adding alerts for {child_name}...")
    
    # Define alerts based on child
    if child_name == 'Emma':
        alerts = [
            {
                "app_name": "Minecraft", 
                "message": f"{child_name} has been playing Minecraft for over 45 minutes", 
                "severity": "LOW"
            }
        ]
    elif child_name == 'Noah':
        alerts = [
            {
                "app_name": "Discord", 
                "message": f"Potentially inappropriate chat detected in {child_name}'s Discord usage", 
                "severity": "MEDIUM"
            }
        ]
    else:  # Sophia
        alerts = [
            {
                "app_name": "Browser", 
                "message": f"{child_name} attempted to access a blocked website", 
                "severity": "HIGH"
            }
        ]
    
    # Add alerts
    for alert in alerts:
        conn.execute(
            """
            INSERT INTO alerts 
            (child_id, app_name, message, severity, timestamp, resolved) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                child_id, 
                alert["app_name"], 
                alert["message"], 
                alert["severity"], 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                0
            )
        )

if __name__ == "__main__":
    add_children() 