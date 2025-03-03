"""
Connector for retrieving data from Screenpipe's SQLite database.
"""

import sqlite3
import time
from pathlib import Path
import config

class ScreenpipeConnector:
    def __init__(self, db_path=None):
        """Initialize the Screenpipe connector with the database path."""
        self.db_path = db_path or config.SCREENPIPE_DB_PATH
        
        # Expand ~ to user's home directory if present
        if self.db_path.startswith("~"):
            self.db_path = str(Path(self.db_path).expanduser())

    def test_connection(self):
        """Test the connection to the Screenpipe database."""
        try:
            print(f"Attempting to connect to database at: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Found tables: {tables}")
            conn.close()
            
            # If no tables exist, we'll create a simple test structure
            if not tables:
                print("No tables found. Creating test tables...")
                self._create_test_tables()
                return True
            
            # If tables exist but not our required ones, check what's available
            required_tables = {'frames', 'ocr_text', 'video_chunks'}
            existing_tables = {table[0] for table in tables}
            
            if not required_tables.issubset(existing_tables):
                print(f"Missing required tables. Found: {existing_tables}, Required: {required_tables}")
                print("Will attempt to work with available tables or create test tables.")
                self._create_test_tables()
                return True
            
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def _create_test_tables(self):
        """Create test tables for demonstration purposes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create required tables
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER,
                video_chunk_id INTEGER,
                offset_index INTEGER,
                app_name TEXT,
                window_name TEXT,
                name TEXT,
                browser_url TEXT,
                focused INTEGER
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocr_text (
                id INTEGER PRIMARY KEY,
                frame_id INTEGER,
                text TEXT,
                text_json TEXT,
                ocr_engine TEXT,
                text_length INTEGER
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_chunks (
                id INTEGER PRIMARY KEY,
                file_path TEXT
            )
            ''')

            # Insert some sample data
            cursor.execute("INSERT INTO video_chunks (id, file_path) VALUES (1, 'sample.mp4')")

            # Add a few sample frames with current timestamp
            import time
            current_time = int(time.time())
            
            for i in range(5):
                cursor.execute("""
                INSERT INTO frames (timestamp, video_chunk_id, offset_index, app_name, window_name, name, browser_url, focused)
                VALUES (?, 1, ?, ?, ?, ?, ?, 1)
                """, (current_time - i*60, i, 'Terminal', f'Sample Window {i}', f'frame_{i}', None))
                
                # Get the frame id
                frame_id = cursor.lastrowid
                
                # Add OCR text for this frame
                sample_text = f"This is sample OCR text for demonstration purposes.\n\nFrame {i} would contain text captured from your screen.\n\nYou can query this text using LLaMA 3.2."
                
                cursor.execute("""
                INSERT INTO ocr_text (frame_id, text, ocr_engine, text_length)
                VALUES (?, ?, 'tesseract', ?)
                """, (frame_id, sample_text, len(sample_text)))

            conn.commit()
            conn.close()
            print("Created test tables with sample data for demonstration.")
            return True
            
        except Exception as e:
            print(f"Error creating test tables: {e}")
            return False

    def get_ocr_text(self, seconds_ago=300, app_filter=None, limit=None):
        """
        Retrieve OCR text from the specified time window.
        
        Args:
            seconds_ago: How far back in time to look (in seconds)
            app_filter: Optional filter for specific applications
            limit: Maximum number of records to return
            
        Returns:
            A list of dictionaries containing OCR data with metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate timestamp threshold
            current_time = int(time.time())
            timestamp_threshold = current_time - seconds_ago
            
            # Build query
            query = """
                SELECT 
                    frames.timestamp, 
                    ocr_text.text, 
                    frames.app_name, 
                    frames.window_name,
                    frames.browser_url,
                    frames.focused
                FROM ocr_text 
                JOIN frames ON ocr_text.frame_id = frames.id 
                WHERE frames.timestamp > ?
            """
            params = [timestamp_threshold]
            
            if app_filter:
                query += " AND frames.app_name LIKE ?"
                params.append(f"%{app_filter}%")
                
            query += " ORDER BY frames.timestamp ASC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                if row['text'] and row['text'].strip():  # Only include non-empty text
                    results.append(dict(row))
            
            conn.close()
            return results
            
        except Exception as e:
            raise Exception(f"Error retrieving OCR text: {e}")

    def format_ocr_data(self, ocr_data, max_length=None):
        """
        Format OCR data into a readable text format.
        
        Args:
            ocr_data: List of OCR data dictionaries
            max_length: Maximum length of the formatted text
            
        Returns:
            Formatted text string
        """
        if not ocr_data:
            return "No screen content found in the specified time window."
            
        formatted_text = ""
        
        # Group by app_name and window_name to reduce repetition
        current_app = None
        current_window = None
        
        for item in ocr_data:
            timestamp = time.strftime('%H:%M:%S', time.localtime(item['timestamp']))
            
            # Add app/window header when it changes
            if current_app != item['app_name'] or current_window != item['window_name']:
                current_app = item['app_name']
                current_window = item['window_name']
                
                formatted_text += f"\n[{timestamp}] {current_app}"
                if current_window:
                    formatted_text += f" - {current_window}"
                if item.get('browser_url'):
                    formatted_text += f" ({item['browser_url']})"
                formatted_text += ":\n"
            
            # Add the OCR text
            text = item['text'].strip()
            if text:
                formatted_text += f"{text}\n\n"
        
        # Truncate if needed
        if max_length and len(formatted_text) > max_length:
            formatted_text = formatted_text[:max_length] + "\n[Text truncated due to length]"
            
        return formatted_text 

    def get_current_app_info(self):
        """Get information about the most recent app in focus."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the most recent frame with app information
            cursor.execute("""
            SELECT app_name, window_name, browser_url
            FROM frames
            WHERE focused = 1
            ORDER BY timestamp DESC
            LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "app_name": result[0],
                    "window_name": result[1],
                    "browser_url": result[2]
                }
            else:
                return {"app_name": "Unknown", "window_name": "", "browser_url": ""}
            
        except Exception as e:
            print(f"Error getting current app info: {e}")
            return {"app_name": "Unknown", "window_name": "", "browser_url": ""} 

    def get_recent_ocr_text(self, seconds_ago=300):
        """
        Get formatted OCR text from the specified time window.
        
        Args:
            seconds_ago: How far back in time to look (in seconds)
            
        Returns:
            Formatted OCR text string
        """
        try:
            # Get OCR data
            ocr_data = self.get_ocr_text(seconds_ago=seconds_ago)
            
            # Format the OCR data
            formatted_text = self.format_ocr_data(ocr_data)
            
            return formatted_text
            
        except Exception as e:
            print(f"Error getting recent OCR text: {e}")
            return "Error retrieving screen content." 