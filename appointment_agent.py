from datetime import datetime, timedelta
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from typing import Dict, List, Optional

class AppointmentAgent:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.hostinger.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.available_slots = self._load_available_slots()

    def _load_available_slots(self) -> Dict[str, List[str]]:
        """Load or initialize available appointment slots"""
        if os.path.exists('appointments.json'):
            with open('appointments.json', 'r') as f:
                return json.load(f)
        else:
            # Initialize next 14 days of appointments
            slots = {}
            for i in range(14):
                date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                slots[date] = [
                    "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"
                ]
            with open('appointments.json', 'w') as f:
                json.dump(slots, f)
            return slots

    def _save_available_slots(self):
        """Save current appointment slots to file"""
        with open('appointments.json', 'w') as f:
            json.dump(self.available_slots, f)

    def get_available_slots(self, date: str) -> List[str]:
        """Get available slots for a specific date"""
        return self.available_slots.get(date, [])

    def book_appointment(self, date: str, time: str, lead_info: dict) -> bool:
        """Book an appointment and remove the slot from available slots"""
        if date in self.available_slots and time in self.available_slots[date]:
            self.available_slots[date].remove(time)
            self._save_available_slots()
            self._send_confirmation_emails(date, time, lead_info)
            return True
        return False

    def _send_confirmation_emails(self, date: str, time: str, lead_info: dict):
        """Send confirmation emails to both the lead and the business"""
        # Email to lead
        lead_subject = "Your Chromapages Consultation Appointment Confirmation"
        lead_body = f"""
        Dear {lead_info.get('name', 'Valued Customer')},

        Thank you for scheduling a consultation with Chromapages! Your appointment details:

        Date: {date}
        Time: {time}

        We'll discuss your web design and development needs and create a plan tailored to your business.

        Location: Video call (link will be sent 24 hours before the appointment)

        If you need to reschedule, please contact us at {self.email_address}.

        Best regards,
        The Chromapages Team
        """
        self._send_email(lead_info['email'], lead_subject, lead_body)

        # Email to business
        business_subject = "New Consultation Appointment"
        business_body = f"""
        New appointment scheduled:

        Date: {date}
        Time: {time}

        Lead Information:
        Name: {lead_info.get('name', 'Not provided')}
        Email: {lead_info.get('email')}
        Phone: {lead_info.get('phone', 'Not provided')}
        
        Conversation History:
        {lead_info.get('conversation_history', 'No conversation history available')}

        Requirements/Notes:
        {lead_info.get('requirements', 'No specific requirements noted')}
        """
        self._send_email(self.email_address, business_subject, business_body)

    def _send_email(self, to_email: str, subject: str, body: str):
        """Send an email using SMTP with SSL"""
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            # Create a secure SSL/TLS context
            context = ssl.create_default_context()
            
            # Connect to Hostinger SMTP server using SSL
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise

    def qualify_lead(self, conversation_history: List[str]) -> bool:
        """
        Determine if a lead is qualified based on conversation history
        Returns True if the lead meets qualification criteria
        """
        # Basic qualification criteria (can be expanded)
        qualifiers = [
            "budget",
            "timeline",
            "business",
            "website",
            "redesign",
            "development",
            "ecommerce"
        ]
        
        # Join all conversation messages
        full_conversation = " ".join(conversation_history).lower()
        
        # Check for presence of qualifying terms
        qualifier_count = sum(1 for term in qualifiers if term in full_conversation)
        
        # Lead is qualified if they mention at least 3 qualifying terms
        return qualifier_count >= 3 