from werkzeug.security import check_password_hash

# Replace with the actual hash from your database
password_hash = 'pbkdf2:sha256:260000$qO6zXGfMQMwFSTPO$8bb000dbe88b025cd4e7333c29948bcd83e269feb4e360fdfc5b06834ebb4e8d'
password_to_check = 'testpassword'  # The password you want to check

if check_password_hash(password_hash, password_to_check):
    print("Password is correct.")
else:
    print("Password is incorrect.")
