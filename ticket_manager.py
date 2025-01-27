from datetime import datetime
import json
import os
from typing import Dict, List, Optional
from enum import Enum
import uuid

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketManager:
    def __init__(self):
        self.tickets_file = 'tickets.json'
        self.tickets = self._load_tickets()
        self.email_address = os.getenv("EMAIL_ADDRESS")

    def _load_tickets(self) -> Dict:
        """Load tickets from file or initialize empty ticket store"""
        if os.path.exists(self.tickets_file):
            with open(self.tickets_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_tickets(self):
        """Save tickets to file"""
        with open(self.tickets_file, 'w') as f:
            json.dump(self.tickets, f, indent=2)

    def create_ticket(self, subject: str, description: str, customer_email: str, 
                     priority: TicketPriority = TicketPriority.MEDIUM,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Create a new support ticket"""
        ticket_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        ticket = {
            'id': ticket_id,
            'subject': subject,
            'description': description,
            'customer_email': customer_email,
            'status': TicketStatus.OPEN.value,
            'priority': priority.value,
            'created_at': timestamp,
            'updated_at': timestamp,
            'conversation_history': conversation_history or [],
            'updates': [{
                'timestamp': timestamp,
                'type': 'creation',
                'message': 'Ticket created'
            }]
        }

        self.tickets[ticket_id] = ticket
        self._save_tickets()
        self._notify_ticket_creation(ticket)
        return ticket_id

    def update_ticket_status(self, ticket_id: str, status: TicketStatus, note: Optional[str] = None) -> bool:
        """Update the status of a ticket"""
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]
        old_status = ticket['status']
        ticket['status'] = status.value
        ticket['updated_at'] = datetime.now().isoformat()

        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'status_change',
            'from_status': old_status,
            'to_status': status.value
        }
        if note:
            update['note'] = note

        ticket['updates'].append(update)
        self._save_tickets()
        self._notify_ticket_update(ticket, update)
        return True

    def add_comment(self, ticket_id: str, comment: str, is_customer: bool = False) -> bool:
        """Add a comment to a ticket"""
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]
        timestamp = datetime.now().isoformat()

        update = {
            'timestamp': timestamp,
            'type': 'comment',
            'comment': comment,
            'is_customer': is_customer
        }

        ticket['updates'].append(update)
        ticket['updated_at'] = timestamp
        self._save_tickets()
        self._notify_ticket_comment(ticket, update)
        return True

    def update_priority(self, ticket_id: str, priority: TicketPriority) -> bool:
        """Update the priority of a ticket"""
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]
        old_priority = ticket['priority']
        ticket['priority'] = priority.value
        ticket['updated_at'] = datetime.now().isoformat()

        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'priority_change',
            'from_priority': old_priority,
            'to_priority': priority.value
        }

        ticket['updates'].append(update)
        self._save_tickets()
        self._notify_ticket_update(ticket, update)
        return True

    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get a specific ticket by ID"""
        return self.tickets.get(ticket_id)

    def get_tickets_by_status(self, status: TicketStatus) -> List[Dict]:
        """Get all tickets with a specific status"""
        return [ticket for ticket in self.tickets.values() 
                if ticket['status'] == status.value]

    def get_tickets_by_customer(self, customer_email: str) -> List[Dict]:
        """Get all tickets for a specific customer"""
        return [ticket for ticket in self.tickets.values() 
                if ticket['customer_email'] == customer_email]

    def get_open_tickets(self) -> List[Dict]:
        """Get all open and in-progress tickets"""
        return [ticket for ticket in self.tickets.values() 
                if ticket['status'] in [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]]

    def _notify_ticket_creation(self, ticket: Dict):
        """Send notification for new ticket creation"""
        subject = f"New Support Ticket Created - {ticket['subject']}"
        body = f"""
        New support ticket created:

        Ticket ID: {ticket['id']}
        Subject: {ticket['subject']}
        Priority: {ticket['priority']}
        Customer: {ticket['customer_email']}

        Description:
        {ticket['description']}

        Status: {ticket['status']}
        Created: {ticket['created_at']}
        """
        self._send_notification(subject, body)

    def _notify_ticket_update(self, ticket: Dict, update: Dict):
        """Send notification for ticket updates"""
        subject = f"Support Ticket Updated - {ticket['subject']}"
        body = f"""
        Support ticket updated:

        Ticket ID: {ticket['id']}
        Subject: {ticket['subject']}
        Customer: {ticket['customer_email']}

        Update Type: {update['type']}
        Timestamp: {update['timestamp']}
        """

        if 'from_status' in update:
            body += f"\nStatus changed from {update['from_status']} to {update['to_status']}"
        if 'from_priority' in update:
            body += f"\nPriority changed from {update['from_priority']} to {update['to_priority']}"
        if 'note' in update:
            body += f"\n\nNote: {update['note']}"

        self._send_notification(subject, body)

    def _notify_ticket_comment(self, ticket: Dict, update: Dict):
        """Send notification for new comments"""
        commenter = "Customer" if update['is_customer'] else "Support"
        subject = f"New Comment on Support Ticket - {ticket['subject']}"
        body = f"""
        New comment added to support ticket:

        Ticket ID: {ticket['id']}
        Subject: {ticket['subject']}
        Added by: {commenter}
        Timestamp: {update['timestamp']}

        Comment:
        {update['comment']}
        """
        self._send_notification(subject, body)

    def _send_notification(self, subject: str, body: str):
        """Send email notification"""
        # Import here to avoid circular imports
        from appointment_agent import AppointmentAgent
        email_sender = AppointmentAgent()
        try:
            email_sender._send_email(self.email_address, subject, body)
        except Exception as e:
            print(f"Error sending ticket notification: {str(e)}") 