import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

class EmailService:
    def __init__(self, smtp_server, port, email, password):
        self.smtp_server = smtp_server
        self.port = port
        self.email = email
        self.password = password
    
    def send_invitation(self, guest_email, guest_name, event_name, event_date, 
                       event_location, invitation_link, event_password):
        """Send an invitation email to a guest"""
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email
            message["To"] = guest_email
            message["Subject"] = f"Invitation: {event_name}"
            
            # Email body
            body = f"""
            Dear {guest_name},
            
            You are invited to attend: {event_name}
            
            Event Details:
            - Date: {event_date}
            - Location: {event_location}
            
            To accept this invitation, please use the following link:
            {invitation_link}
            
            Event Access Password: {event_password}
            
            We look forward to seeing you there!
            
            Best regards,
            Event Planner Team
            """
            
            message.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email to {guest_email}: {str(e)}")
            return False