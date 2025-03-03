import sqlite3

def check_children():
    conn = sqlite3.connect('data/dashboard.db')  # Adjust the path if necessary
    cursor = conn.cursor()
    
    # Replace with the actual parent ID you are testing
    parent_id = 1  # Change this to the correct parent ID
    
    cursor.execute('SELECT * FROM children WHERE parent_id = ?', (parent_id,))
    children = cursor.fetchall()
    
    if children:
        print("Children found:")
        for child in children:
            print(child)
    else:
        print("No children found for this parent ID.")
    
    conn.close()

if __name__ == "__main__":
    check_children() 