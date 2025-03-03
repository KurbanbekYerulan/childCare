import sqlite3

def check_user():
    conn = sqlite3.connect('data/dashboard.db')  # Adjust the path if necessary
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('testuser',))
    user = cursor.fetchone()
    
    if user:
        print("User found:")
        print(f"Username: {user[0]}")
        print(f"Password Hash: {user[1]}")
    else:
        print("User 'testuser' not found in database")
    
    conn.close()

if __name__ == "__main__":
    check_user() 