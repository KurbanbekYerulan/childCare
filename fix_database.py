import sqlite3
import os

def get_db_connection():
    # Get the database path
    db_dir = os.path.join(os.path.dirname(__file__), 'Dashboard/data')
    db_path = os.path.join(db_dir, 'database.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    return conn

def check_and_fix_schema():
    """Check and fix the database schema"""
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if app_usage table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_usage'")
        app_usage_exists = cursor.fetchone() is not None
        
        if app_usage_exists:
            # Check if duration_minutes column exists
            cursor.execute("PRAGMA table_info(app_usage)")
            columns = cursor.fetchall()
            has_duration_minutes = any(col[1] == 'duration_minutes' for col in columns)
            
            if not has_duration_minutes:
                print("Adding duration_minutes column to app_usage table...")
                cursor.execute("ALTER TABLE app_usage ADD COLUMN duration_minutes INTEGER DEFAULT 30")
                conn.commit()
                print("Column added successfully")
            else:
                print("duration_minutes column already exists")
        else:
            print("Creating app_usage table...")
            cursor.execute('''
            CREATE TABLE app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER,
                app_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                duration_minutes INTEGER DEFAULT 30,
                FOREIGN KEY (child_id) REFERENCES children (id),
                FOREIGN KEY (app_id) REFERENCES apps (id)
            )
            ''')
            conn.commit()
            print("app_usage table created successfully")
        
        # Insert some sample app usage data if the table is empty
        cursor.execute("SELECT COUNT(*) as count FROM app_usage")
        app_usage_count = cursor.fetchone()[0]
        
        if app_usage_count == 0:
            print("Inserting sample app usage data...")
            
            # Get all children
            cursor.execute("SELECT id FROM children")
            children = cursor.fetchall()
            
            # Get all apps
            cursor.execute("SELECT id FROM apps")
            apps = cursor.fetchall()
            
            if children and apps:
                from datetime import datetime, timedelta
                import random
                
                now = datetime.now()
                
                # Generate usage data for the past 7 days
                for day in range(7):
                    date = now - timedelta(days=day)
                    date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Generate 3-5 app usage entries per child per day
                    for child in children:
                        child_id = child[0]
                        num_entries = random.randint(3, 5)
                        
                        for _ in range(num_entries):
                            app_id = random.choice(apps)[0]
                            duration = random.randint(15, 120)  # 15 minutes to 2 hours
                            
                            cursor.execute(
                                "INSERT INTO app_usage (child_id, app_id, timestamp, duration_minutes) VALUES (?, ?, ?, ?)",
                                (child_id, app_id, date_str, duration)
                            )
                
                conn.commit()
                print("Sample app usage data inserted successfully")
        
        # Print database tables and their schemas
        print("\nDatabase Tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name} table schema:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_fix_schema() 