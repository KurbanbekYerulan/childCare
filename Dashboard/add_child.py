import sqlite3

def add_child():
    conn = sqlite3.connect('data/dashboard.db')  # Adjust the path if necessary
    cursor = conn.cursor()
    
    # Replace with the actual parent ID you are testing
    parent_id = 1  # Change this to the correct parent ID
    child_name = 'Test Child'
    child_age = 10
    
    cursor.execute('INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)', (parent_id, child_name, child_age))
    conn.commit()
    print("Child added successfully.")
    
    conn.close()

if __name__ == "__main__":
    add_child() 