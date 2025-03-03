import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        
        if not all([self.smtp_username, self.smtp_password]):
            print("SMTP credentials not set. Email notifications will be simulated.")
    
    def send_email(self, to_email, subject, message):
        """Send an email notification."""
        if not all([self.smtp_username, self.smtp_password]):
            print(f"SIMULATED EMAIL: To {to_email}, Subject: {subject}, Message: {message}")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False 