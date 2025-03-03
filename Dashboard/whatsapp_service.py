from twilio.rest import Client
import os

class WhatsAppService:
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Twilio credentials not set. WhatsApp notifications will be simulated.")
    
    def send_message(self, to_number, message):
        """Send a WhatsApp message using Twilio."""
        if not self.client:
            print(f"SIMULATED WHATSAPP: To {to_number}: {message}")
            return True
        
        try:
            # Format the 'to' number for WhatsApp
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Format the 'from' number for WhatsApp
            from_number = self.from_number
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            message = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"WhatsApp message sent: {message.sid}")
            return True
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return False 