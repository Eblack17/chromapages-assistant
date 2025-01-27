from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from rag_agent import ChromapagesRAGAgent
from appointment_agent import AppointmentAgent
import os

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["POST", "OPTIONS", "GET"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize agents lazily
rag_agent = None
appointment_agent = None
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
        
        # Get agent instance and process message
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