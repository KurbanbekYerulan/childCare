import requests
import json
import time
from pprint import pprint

# Configuration
BASE_URL = "http://127.0.0.1:5000/api"
TEST_USER = {
    "username": "testuser",
    "password": "testpassword",
    "confirmPassword": "testpassword",
    "email": "test@example.com",
    "whatsapp_number": "+1234567890",
    "child_name": "Test Child",
    "child_age": "10"
}

# Create a session to maintain cookies
session = requests.Session()

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def test_register():
    """Test user registration."""
    print_separator("TESTING REGISTRATION")
    
    try:
        print("Sending registration request with data:")
        pprint(TEST_USER)
        
        # Use requests directly instead of a session
        response = requests.post(
            f"{BASE_URL}/register",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Registration successful")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("⚠️ User already exists (this is okay for repeated tests)")
            return True
        else:
            print("❌ Registration failed")
            return False
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False

def test_login():
    """Test user login."""
    print_separator("TESTING LOGIN")
    
    try:
        response = session.post(
            f"{BASE_URL}/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            return True
        else:
            print("❌ Login failed")
            return False
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False

def test_dashboard_summary():
    """Test dashboard summary endpoint."""
    print_separator("TESTING DASHBOARD SUMMARY")
    
    try:
        response = session.get(f"{BASE_URL}/dashboard/summary")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Dashboard summary retrieved successfully")
            return True
        else:
            print("❌ Failed to retrieve dashboard summary")
            return False
    except Exception as e:
        print(f"❌ Error retrieving dashboard summary: {e}")
        return False

def test_alerts():
    """Test alerts endpoint."""
    print_separator("TESTING ALERTS")
    
    try:
        response = session.get(f"{BASE_URL}/alerts")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Alerts retrieved successfully")
            return True
        else:
            print("❌ Failed to retrieve alerts")
            return False
    except Exception as e:
        print(f"❌ Error retrieving alerts: {e}")
        return False

def test_app_usage():
    """Test app usage endpoint."""
    print_separator("TESTING APP USAGE")
    
    try:
        # First get child ID from dashboard summary
        summary_response = session.get(f"{BASE_URL}/dashboard/summary")
        if summary_response.status_code != 200:
            print("❌ Could not get child ID from dashboard summary")
            return False
        
        summary_data = summary_response.json()
        if not summary_data.get('children') or len(summary_data['children']) == 0:
            print("❌ No children found in dashboard summary")
            return False
        
        child_id = summary_data['children'][0]['id']
        print(f"Using child ID: {child_id}")
        
        # Now get app usage for this child
        response = session.get(f"{BASE_URL}/dashboard/app_usage/{child_id}?days=7")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ App usage retrieved successfully")
            return True
        else:
            print("❌ Failed to retrieve app usage")
            return False
    except Exception as e:
        print(f"❌ Error retrieving app usage: {e}")
        return False

def test_current_app():
    """Test current app endpoint."""
    print_separator("TESTING CURRENT APP")
    
    try:
        response = session.get(f"{BASE_URL}/current_app")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Current app info retrieved successfully")
            return True
        else:
            print("❌ Failed to retrieve current app info")
            return False
    except Exception as e:
        print(f"❌ Error retrieving current app info: {e}")
        return False

def test_logout():
    """Test logout endpoint."""
    print_separator("TESTING LOGOUT")
    
    try:
        response = session.post(f"{BASE_URL}/logout")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Logout successful")
            
            # Verify we're logged out by trying to access dashboard
            test_response = session.get(f"{BASE_URL}/dashboard/summary")
            if test_response.status_code == 401 or test_response.status_code == 403:
                print("✅ Verified logout - dashboard access denied")
                return True
            else:
                print("❌ Still able to access dashboard after logout")
                return False
        else:
            print("❌ Logout failed")
            return False
    except Exception as e:
        print(f"❌ Error during logout: {e}")
        return False

def test_debug():
    """Test debug endpoint to verify server is running."""
    print_separator("TESTING DEBUG ENDPOINT")
    
    try:
        response = requests.get(f"{BASE_URL}/debug")
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Debug endpoint working")
            return True
        else:
            print("❌ Debug endpoint not working")
            return False
    except Exception as e:
        print(f"❌ Error accessing debug endpoint: {e}")
        return False

def run_all_tests():
    """Run all API tests in sequence."""
    print_separator("STARTING API TESTS")
    
    # First check if server is running
    if not test_debug():
        print("⚠️ Server may not be running correctly. Check Flask app.")
        return
    
    # Registration and authentication tests
    if not test_register():
        print("⚠️ Skipping remaining tests due to registration failure")
        return
    
    if not test_login():
        print("⚠️ Skipping remaining tests due to login failure")
        return
    
    # Data retrieval tests
    test_dashboard_summary()
    test_alerts()
    test_app_usage()
    test_current_app()
    
    # Logout test
    test_logout()
    
    print_separator("ALL TESTS COMPLETED")

if __name__ == "__main__":
    run_all_tests()