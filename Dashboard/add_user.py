import sqlite3
from werkzeug.security import generate_password_hash

def add_user(username, password, email, whatsapp_number):
    conn = sqlite3.connect('data/dashboard.db')  # Adjust the path if necessary
    cursor = conn.cursor()
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, whatsapp_number)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, email, whatsapp_number))
        
        conn.commit()
        print("User created successfully!")
    except sqlite3.IntegrityError:
        print("User already exists.")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Change these values as needed
    add_user('testuser', 'testpassword', 'test@example.com', '+1234567890') 