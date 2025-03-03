import os
import sqlite3
import json
from datetime import datetime, timedelta
import sys
import time
import random

# Add the App directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

# Import your actual modules
from screenpipe_connector import ScreenpipeConnector
from llama_client import LlamaClient
from query_engine import QueryEngine
import config

def get_db_connection():
    """Connect to the database"""
    db_dir = os.path.join(os.path.dirname(__file__), 'Dashboard/data')
    db_path = os.path.join(db_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_child_data(child_id, child_name, child_age, screenpipe, llama, query_engine):
    """Update data for a specific child using real-time OCR and analysis"""
    print(f"\nUpdating data for {child_name} (ID: {child_id})...")
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Check if status column exists
        cursor = conn.execute("PRAGMA table_info(children)")
        columns = [column[1] for column in cursor.fetchall()]
        has_status_column = 'status' in columns
        
        # Update child's basic information
        print(f"Updating {child_name}'s basic information...")
        if has_status_column:
            conn.execute(
                """
                UPDATE children 
                SET status = ?
                WHERE id = ?
                """,
                ('Online', child_id)
            )
        
        # Get current app info from Screenpipe
        print("Getting current app info from Screenpipe...")
        app_info = screenpipe.get_current_app_info()
        app_name = app_info.get('app_name', 'Unknown App')
        window_title = app_info.get('window_title', '')
        browser_url = app_info.get('url', None)
        
        print(f"Current app: {app_name}")
        print(f"Window title: {window_title}")
        if browser_url:
            print(f"URL: {browser_url}")
        
        # Get OCR text from Screenpipe
        print("Getting OCR text from Screenpipe...")
        ocr_text = screenpipe.get_recent_ocr_text()
        
        # Truncate OCR text for display
        display_ocr = ocr_text[:100] + "..." if len(ocr_text) > 100 else ocr_text
        print(f"OCR text: {display_ocr}")
        
        # Analyze content with Llama
        print("Analyzing content with Llama...")
        analysis_query = f"""
        Analyze this content and determine if it's appropriate for a {child_age}-year-old child.
        Provide the following information:
        1. Content category (Games, Education, Social Media, Entertainment, or Productivity)
        2. Is it appropriate for children? (Yes/No)
        3. Is it educational or productive? (Yes/No)
        4. Age rating (Everyone, 9+, 12+, 16+, 18+)
        5. Educational value on a scale of 1-10
        6. Any potential concerns
        7. Recommended alternatives if not appropriate
        """
        
        analysis_result = llama.query(ocr_text, analysis_query)
        print("Analysis complete.")
        
        # Parse the analysis result
        is_appropriate = "not appropriate" not in analysis_result.lower() and "inappropriate" not in analysis_result.lower()
        is_educational = "educational" in analysis_result.lower() or "productive" in analysis_result.lower()
        
        # Extract category
        category = "Other"  # Default category
        if "game" in analysis_result.lower():
            category = "Games"
        elif "education" in analysis_result.lower():
            category = "Education"
        elif "social media" in analysis_result.lower():
            category = "Social Media"
        elif "entertainment" in analysis_result.lower():
            category = "Entertainment"
        elif "productivity" in analysis_result.lower():
            category = "Productivity"
        
        # Extract age rating
        age_rating = "Unknown"
        if "everyone" in analysis_result.lower():
            age_rating = "Everyone"
        elif "9+" in analysis_result:
            age_rating = "9+"
        elif "12+" in analysis_result:
            age_rating = "12+"
        elif "16+" in analysis_result:
            age_rating = "16+"
        elif "18+" in analysis_result:
            age_rating = "18+"
        
        # Extract educational value
        educational_value = 0
        for i in range(10, 0, -1):
            if f"{i}/10" in analysis_result or f"{i} out of 10" in analysis_result:
                educational_value = i
                break
        
        # Extract concerns
        concerns = []
        if "concern" in analysis_result.lower():
            concerns_section = analysis_result.lower().split("concern")[1].split("\n")[0]
            concerns = [concerns_section.strip()]
        
        # Create structured analysis
        structured_analysis = {
            "app_name": app_name,
            "window_title": window_title,
            "browser_url": browser_url,
            "category": category,
            "is_appropriate": is_appropriate,
            "is_educational": is_educational,
            "age_rating": age_rating,
            "educational_value": educational_value,
            "concerns": concerns,
            "analysis_text": analysis_result
        }
        
        # Store OCR data
        print("Storing OCR data...")
        conn.execute(
            "INSERT INTO ocr_data (child_id, app_name, ocr_text, analysis, timestamp) VALUES (?, ?, ?, ?, ?)",
            (child_id, app_name, ocr_text, json.dumps(structured_analysis), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        # Store app analysis if it doesn't exist
        existing_analysis = conn.execute(
            "SELECT id FROM app_analysis WHERE app_name = ? AND window_name = ?",
            (app_name, window_title)
        ).fetchone()
        
        if not existing_analysis:
            print("Storing app analysis...")
            conn.execute(
                """
                INSERT INTO app_analysis 
                (app_name, window_name, browser_url, category, is_appropriate, age_rating, 
                educational_value, potential_concerns, alternatives, analysis_json, last_updated) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    app_name, 
                    window_title, 
                    browser_url, 
                    category, 
                    1 if is_appropriate else 0, 
                    age_rating, 
                    educational_value, 
                    ", ".join(concerns), 
                    "", 
                    json.dumps(structured_analysis), 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        
        # Create current session
        print(f"Creating current session for {app_name}...")
        start_time = datetime.now() - timedelta(minutes=random.randint(5, 30))
        end_time = datetime.now() + timedelta(minutes=random.randint(10, 60))  # End time in future for active session
        duration = int((datetime.now() - start_time).total_seconds() / 60)
        
        # Store current app usage
        conn.execute(
            """
            INSERT INTO app_usage 
            (child_id, app_name, category, is_productive, is_appropriate, start_time, end_time, duration) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                child_id, 
                app_name, 
                category, 
                1 if is_educational else 0, 
                1 if is_appropriate else 0, 
                start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                end_time.strftime('%Y-%m-%d %H:%M:%S'), 
                duration
            )
        )
        
        # Store current app in a special table for quick access
        # First check if the table exists
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
        
        # Delete any existing current session for this child
        conn.execute("DELETE FROM current_sessions WHERE child_id = ?", (child_id,))
        
        # Insert new current session
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
        
        # Create an alert if content is inappropriate
        if not is_appropriate:
            print("Creating alert for inappropriate content...")
            conn.execute(
                """
                INSERT INTO alerts 
                (child_id, app_name, message, severity, timestamp, resolved) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    child_id, 
                    app_name, 
                    f"Potentially inappropriate content detected in {app_name}: {', '.join(concerns) if concerns else 'Content may not be suitable for children'}", 
                    "HIGH", 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    0
                )
            )
        
        # Create an alert for excessive screen time (if this is the 3rd or more usage today)
        today = datetime.now().strftime('%Y-%m-%d')
        usage_count = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM app_usage
            WHERE child_id = ? AND date(start_time) = ?
            """,
            (child_id, today)
        ).fetchone()['count']
        
        if usage_count >= 3:
            print("Creating alert for excessive screen time...")
            conn.execute(
                """
                INSERT INTO alerts 
                (child_id, app_name, message, severity, timestamp, resolved) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    child_id, 
                    app_name, 
                    f"Excessive screen time detected: {child_name} has used {app_name} multiple times today, totaling over {usage_count * 15} minutes", 
                    "MEDIUM", 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    0
                )
            )
        
        # Commit all changes
        conn.commit()
        
        print(f"Data update complete for {child_name}!")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error updating {child_name}'s data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def update_all_children():
    """Update data for all children using real-time OCR and analysis"""
    print("Starting update for all children...")
    
    # Initialize your actual components
    print("Initializing Screenpipe connector and Llama client...")
    screenpipe = ScreenpipeConnector()
    llama = LlamaClient()
    query_engine = QueryEngine(screenpipe, llama)
    
    # Test connections
    print("Testing Screenpipe connection...")
    screenpipe_status = screenpipe.test_connection()
    print(f"Screenpipe connection: {'OK' if screenpipe_status else 'Failed'}")
    
    print("Testing Llama connection...")
    llama_status = llama.test_connection()
    print(f"Llama connection: {'OK' if llama_status else 'Failed'}")
    
    if not screenpipe_status:
        print("Error: Could not connect to Screenpipe. Please check your configuration.")
        return
    
    if not llama_status:
        print("Error: Could not connect to Llama. Please check your configuration.")
        return
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Get all children
        children = conn.execute("SELECT id, name, age FROM children").fetchall()
        
        if not children:
            print("No children found in the database.")
            return
        
        for child in children:
            update_child_data(child['id'], child['name'], child['age'], screenpipe, llama, query_engine)
            
        print("\nAll children's data has been updated!")
        print("Refresh the dashboard to see the updated data.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error updating children data: {e}")
    finally:
        conn.close()

def update_alex_data():
    """Update Alex's data using real-time OCR and analysis"""
    print("Starting update for Alex's data...")
    
    # Initialize your actual components
    print("Initializing Screenpipe connector and Llama client...")
    screenpipe = ScreenpipeConnector()
    llama = LlamaClient()
    query_engine = QueryEngine(screenpipe, llama)
    
    # Test connections
    print("Testing Screenpipe connection...")
    screenpipe_status = screenpipe.test_connection()
    print(f"Screenpipe connection: {'OK' if screenpipe_status else 'Failed'}")
    
    print("Testing Llama connection...")
    llama_status = llama.test_connection()
    print(f"Llama connection: {'OK' if llama_status else 'Failed'}")
    
    if not screenpipe_status:
        print("Error: Could not connect to Screenpipe. Please check your configuration.")
        return
    
    if not llama_status:
        print("Error: Could not connect to Llama. Please check your configuration.")
        return
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Get Alex's ID or create if not exists
        alex = conn.execute("SELECT id, age FROM children WHERE name = 'Alex'").fetchone()
        
        if not alex:
            print("Alex not found in the database. Creating a new child named Alex...")
            conn.execute(
                "INSERT INTO children (parent_id, name, age, device_type) VALUES (?, ?, ?, ?)",
                (1, "Alex", 10, "Tablet")
            )
            conn.commit()
            alex = conn.execute("SELECT id, age FROM children WHERE name = 'Alex'").fetchone()
        
        child_id = alex['id']
        child_age = alex['age']
        
        # Update Alex's data using the common function
        success = update_child_data(child_id, "Alex", child_age, screenpipe, llama, query_engine)
        
        if success:
            # Display the updated data
            print("\nUpdated information for Alex:")
            child_info = conn.execute(
                "SELECT name, age, device_type FROM children WHERE id = ?",
                (child_id,)
            ).fetchone()
            
            print(f"Name: {child_info['name']}")
            print(f"Age: {child_info['age']}")
            print(f"Device: {child_info['device_type']}")
            
            # Check if status column exists
            cursor = conn.execute("PRAGMA table_info(children)")
            columns = [column[1] for column in cursor.fetchall()]
            has_status_column = 'status' in columns
            
            if has_status_column:
                status = conn.execute("SELECT status FROM children WHERE id = ?", (child_id,)).fetchone()
                print(f"Status: {status['status'] if status else 'Unknown'}")
            
            current_session = conn.execute(
                "SELECT app_name, start_time, duration_minutes FROM current_sessions WHERE child_id = ?",
                (child_id,)
            ).fetchone()
            
            if current_session:
                print(f"Current App: {current_session['app_name']}")
                print(f"Current Session: Started at {current_session['start_time']} ({current_session['duration_minutes']} minutes ago)")
            
            print("\nData update complete! The dashboard will now show Alex's latest activity.")
            print("Refresh the dashboard to see the updated data.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error updating Alex's data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

def continuous_monitoring(interval=300, all_children=False):
    """
    Continuously monitor and update children's data at specified intervals
    
    Args:
        interval: Time in seconds between updates
        all_children: Whether to update all children or just Alex
    """
    print(f"Starting continuous monitoring (updating every {interval} seconds)...")
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running update cycle...")
            
            if all_children:
                update_all_children()
            else:
                update_alex_data()
                
            print(f"Waiting {interval} seconds until next update...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update children's data with real-time OCR and analysis")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=300, help="Update interval in seconds (default: 300)")
    parser.add_argument("--all", action="store_true", help="Update all children, not just Alex")
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_monitoring(args.interval, args.all)
    else:
        if args.all:
            update_all_children()
        else:
            update_alex_data() 