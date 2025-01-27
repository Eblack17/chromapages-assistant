from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from rag_agent import ChromapagesRAGAgent
from appointment_agent import AppointmentAgent
from ticket_manager import TicketManager, TicketStatus, TicketPriority
import os
import re

app = Flask(__name__)

# Configure CORS - Allow all origins for development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS", "GET"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize agents lazily
rag_agent = None
appointment_agent = None
ticket_manager = None
conversation_history = []

def get_rag_agent():
    global rag_agent
    if rag_agent is None:
        rag_agent = ChromapagesRAGAgent()
    return rag_agent

def get_appointment_agent():
    global appointment_agent
    if appointment_agent is None:
        appointment_agent = AppointmentAgent()
    return appointment_agent

def get_ticket_manager():
    global ticket_manager
    if ticket_manager is None:
        ticket_manager = TicketManager()
    return ticket_manager

def get_direct_response(message: str) -> str:
    """Get direct response based on message content"""
    message_lower = message.lower()
    
    # Pricing related queries
    if any(word in message_lower for word in ['pricing', 'cost', 'price', 'expensive', 'cheap']):
        return "Our pricing varies based on project requirements. For a website, prices typically start at $2,000. Would you like to discuss your specific project needs?"
    
    # Contact related queries
    if any(word in message_lower for word in ['contact', 'reach', 'email', 'phone']):
        return "You can reach us at contact@chromapages.com or fill out our contact form. Would you like me to guide you to the contact form?"
    
    # Services related queries
    if any(word in message_lower for word in ['services', 'offer', 'provide', 'do you']):
        return "We offer web design, development, and digital marketing services. This includes custom website development, e-commerce solutions, SEO optimization, and brand development. What specific service are you interested in?"
    
    # Timeline related queries
    if any(word in message_lower for word in ['time', 'long', 'duration', 'timeline', 'when']):
        return "Project timelines vary based on complexity. A typical website takes 4-8 weeks from start to finish. Would you like to discuss your project timeline?"
    
    # If no direct match, return None to fallback to RAG
    return None

@app.route('/_ah/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Try to get a direct response first
        direct_response = get_direct_response(message)
        
        if direct_response:
            response = direct_response
        else:
            # Fallback to RAG agent for more complex queries
            current_agent = get_rag_agent()
            response = current_agent.chat(message)
        
        # Store conversation history
        conversation_history.append({
            'user': message,
            'assistant': response
        })
        
        # Check if lead is qualified after a few messages
        if len(conversation_history) >= 3:
            appointment_agent = get_appointment_agent()
            messages = [msg['user'] for msg in conversation_history]
            if appointment_agent.qualify_lead(messages):
                response += "\n\nI notice you're interested in our services. Would you like to schedule a free consultation? I can help you book an appointment with our team."
        
        return jsonify({'response': response})
    except Exception as e:
        app.logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tickets', methods=['POST'])
def create_ticket():
    """Create a new support ticket"""
    try:
        data = request.json
        required_fields = ['subject', 'description', 'customer_email']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        priority = TicketPriority[data.get('priority', 'MEDIUM').upper()]
        ticket_manager = get_ticket_manager()
        
        ticket_id = ticket_manager.create_ticket(
            subject=data['subject'],
            description=data['description'],
            customer_email=data['customer_email'],
            priority=priority,
            conversation_history=conversation_history
        )
        
        return jsonify({'ticket_id': ticket_id, 'message': 'Ticket created successfully'})
    except Exception as e:
        app.logger.error(f"Error creating ticket: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a specific ticket"""
    try:
        ticket_manager = get_ticket_manager()
        ticket = ticket_manager.get_ticket(ticket_id)
        if ticket:
            return jsonify(ticket)
        return jsonify({'error': 'Ticket not found'}), 404
    except Exception as e:
        app.logger.error(f"Error getting ticket: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tickets/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """Update ticket status"""
    try:
        data = request.json
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400

        status = TicketStatus[data['status'].upper()]
        note = data.get('note')
        
        ticket_manager = get_ticket_manager()
        if ticket_manager.update_ticket_status(ticket_id, status, note):
            return jsonify({'message': 'Status updated successfully'})
        return jsonify({'error': 'Ticket not found'}), 404
    except Exception as e:
        app.logger.error(f"Error updating ticket status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tickets/<ticket_id>/comments', methods=['POST'])
def add_ticket_comment(ticket_id):
    """Add a comment to a ticket"""
    try:
        data = request.json
        if 'comment' not in data:
            return jsonify({'error': 'Comment is required'}), 400

        is_customer = data.get('is_customer', False)
        ticket_manager = get_ticket_manager()
        
        if ticket_manager.add_comment(ticket_id, data['comment'], is_customer):
            return jsonify({'message': 'Comment added successfully'})
        return jsonify({'error': 'Ticket not found'}), 404
    except Exception as e:
        app.logger.error(f"Error adding comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tickets/customer/<email>', methods=['GET'])
def get_customer_tickets(email):
    """Get all tickets for a customer"""
    try:
        ticket_manager = get_ticket_manager()
        tickets = ticket_manager.get_tickets_by_customer(email)
        return jsonify({'tickets': tickets})
    except Exception as e:
        app.logger.error(f"Error getting customer tickets: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments/available', methods=['GET'])
def get_available_slots():
    """Get available appointment slots for a specific date"""
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({'error': 'Date parameter is required'}), 400
            
        appointment_agent = get_appointment_agent()
        slots = appointment_agent.get_available_slots(date)
        return jsonify({'slots': slots})
    except Exception as e:
        app.logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/appointments/book', methods=['POST'])
def book_appointment():
    """Book an appointment slot"""
    try:
        data = request.json
        date = data.get('date')
        time = data.get('time')
        lead_info = data.get('lead_info', {})
        
        if not all([date, time, lead_info.get('email')]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Add conversation history to lead info
        lead_info['conversation_history'] = "\n".join([
            f"User: {msg['user']}\nAssistant: {msg['assistant']}"
            for msg in conversation_history
        ])
        
        appointment_agent = get_appointment_agent()
        success = appointment_agent.book_appointment(date, time, lead_info)
        
        if success:
            return jsonify({'message': 'Appointment booked successfully'})
        else:
            return jsonify({'error': 'Slot no longer available'}), 409
    except Exception as e:
        app.logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 