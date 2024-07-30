from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import docx
import time
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Groq API key
api_key = os.getenv('GROQ_API_KEY')  # Use environment variable for API key
groq_client = Groq(api_key=api_key)

# Function to read docx file
def read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = [para.text for para in doc.paragraphs if para.text]
    return '\n'.join(full_text)

# Prepare context from document
context_file_path = 'static/document.docx'
context = read_docx(context_file_path)

# Function to answer question based on context using Groq API
def answer_question(question, context):
    retry_count = 0
    max_retries = 3
    retry_delay = 2  # seconds

    while retry_count < max_retries:
        try:
            prompt = f"""Context: {context}

Question: {question}

Please provide a concise and accurate answer based on the given context. If the information is not available in the context, respond with "I'm sorry, I don't have enough information to answer that question."

Answer:"""
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant"
            )
            return response.choices[0].message['content']
        except Exception as e:
            logger.warning(f"Error: {e}. Retrying {retry_count}/{max_retries}...")
            time.sleep(retry_delay)
            retry_count += 1
    
    logger.error("Failed to get a response after multiple retries.")
    return "An error occurred: Unable to process your request. Please try again later."

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send_message(data):
    if 'message' in data:
        question = data['message']
        answer = answer_question(question, context)
        emit('receive_message', {'message': answer})

if __name__ == '__main__':
    socketio.run(app, debug=True)
