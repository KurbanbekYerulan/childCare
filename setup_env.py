import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Define the path to the .env file
env_path = Path('.') / '.env'

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_hex(32)

def setup_environment():
    """Set up the environment variables"""
    # Check if .env file exists
    if env_path.exists():
        print("Loading existing .env file...")
        load_dotenv(env_path)
    else:
        print("Creating new .env file...")
    
    # Create or update the .env file
    env_vars = {}
    
    # Read existing variables if the file exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Check if JWT_SECRET_KEY exists, generate if not
    if 'JWT_SECRET_KEY' not in env_vars:
        env_vars['JWT_SECRET_KEY'] = generate_secret_key()
        print("Generated new JWT_SECRET_KEY")
    
    # Add other required variables with placeholders if they don't exist
    if 'TWILIO_ACCOUNT_SID' not in env_vars:
        env_vars['TWILIO_ACCOUNT_SID'] = 'your_twilio_sid'
    
    if 'TWILIO_AUTH_TOKEN' not in env_vars:
        env_vars['TWILIO_AUTH_TOKEN'] = 'your_twilio_token'
    
    if 'TWILIO_WHATSAPP_NUMBER' not in env_vars:
        env_vars['TWILIO_WHATSAPP_NUMBER'] = 'your_twilio_whatsapp_number'
    
    # Write the variables to the .env file
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(".env file has been created/updated successfully!")
    print("You can now run your Flask application.")

if __name__ == "__main__":
    setup_environment() 