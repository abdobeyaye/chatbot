from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
import docx
import time
import logging
from groq import Groq

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
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
doc_text = read_docx(context_file_path)

# Function to retrieve context based on query
def simple_retrieve(query, text, n=500):
    start_index = text.lower().find(query.lower())
    if start_index == -1:
        return "No relevant information found."
    end_index = start_index + n
    return text[start_index:end_index]

# Function to generate response using Groq API
def generate_response(context, question):
    prompt = f"Based on the following context: {context}\nAnswer the question: {question}"
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            timeout=10
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send_message(data):
    if 'message' in data:
        question = data['message']
        context = simple_retrieve(question, doc_text)
        answer = generate_response(context, question)
        emit('receive_message', {'message': answer})

if __name__ == '__main__':
    socketio.run(app, debug=True)
