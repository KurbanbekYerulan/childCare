# ScreenPipe Parental Control Dashboard
A comprehensive monitoring and analysis solution for parents to track and manage their children's digital activities.

# Project Overview
ScreenPipe Parental Control Dashboard integrates with the ScreenPipe screen monitoring system to provide parents with insights into their children's app usage, detect potentially inappropriate content, and send real-time alerts. The system uses AI to analyze screen content and provide age-appropriate recommendations.

# Current Progress
✅ Backend API fully implemented and tested
✅ Database schema designed and implemented
✅ Integration with ScreenPipe for screen monitoring
✅ AI-powered content analysis
✅ Real-time alert system
⏳ Frontend development (in progress)

# Project Structure
ScreenPipe_Visionify/
├── App/                   # Core application logic
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── llama_client.py    # AI model integration
│   ├── main.py            # Main application entry point
│   ├── query_engine.py    # Data query and analysis
│   └── screenpipe_connector.py  # ScreenPipe integration
│
├── Dashboard/             # Web dashboard backend
│   ├── app.py             # Flask application
│   ├── dashboard.db       # SQLite database
│   ├── email_service.py   # Email notification service
│   ├── schema.sql         # Database schema
│   └── whatsapp_service.py  # WhatsApp notification service
│
├── test_api.py            # API testing script
└── README.md              # This file

# Features
User Authentication: Secure login and registration system
Dashboard: Overview of children's digital activities
App Usage Monitoring: Track which applications are being used and for how long
Content Analysis: AI-powered analysis of screen content for age-appropriateness
Real-time Alerts: Notifications for potentially inappropriate content
Reporting: Detailed usage reports and trends

# API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/register | POST | Register a new user |
| /api/login | POST | User login |
| /api/logout | POST | User logout |
| /api/dashboard/summary | GET | Get dashboard summary data |
| /api/dashboard/app_usage/:childId | GET | Get app usage data for a child |
| /api/alerts | GET | Get alerts for user's children |
| /api/current_app | GET | Get information about currently active app |
| /api/debug | GET | Debug endpoint to verify API is working |

# Setup and Installation
Prerequisites
Python 3.8+
Flask
SQLite
ScreenPipe installation (for full functionality)

Installation
Clone the repository:
   git clone https://github.com/yourusername/ScreenPipe_Visionify.git
   cd ScreenPipe_Visionify
Install Python dependencies:
   pip install flask flask-cors requests twilio
Initialize the database:
   cd Dashboard
   python app.py
Run the API tests to verify functionality:
   python test_api.py

# Testing
The project includes a comprehensive test suite for the API endpoints. Run the tests with:
    python test_api.py

All tests should pass, indicating that the backend is functioning correctly.

# Next Steps
- Develop React frontend components
- Implement real-time notifications
- Enhance AI analysis capabilities
- Add user preference settings
- Implement detailed reporting features

# License
MIT License

# Contributors

# Acknowledgments
ScreenPipe for the screen monitoring technology
Gemini for content analysis capabilities