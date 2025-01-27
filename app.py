from flask import Flask, render_template, request, jsonify
from rag_agent import ChromapagesRAGAgent
import os

app = Flask(__name__)

# Initialize the agent lazily to avoid startup timeout
agent = None

def get_agent():
    global agent
    if agent is None:
        agent = ChromapagesRAGAgent()
    return agent

@app.route('/_ah/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get agent instance
        current_agent = get_agent()
        response = current_agent.chat(message)
        return jsonify({'response': response})
    except Exception as e:
        app.logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 