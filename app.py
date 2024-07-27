from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import google.generativeai as genai
import docx
import time
from google.api_core.exceptions import ResourceExhausted

app = Flask(__name__)
socketio = SocketIO(app)

# Configure API key
api_key = os.getenv('GOOGLE_API_KEY')  # Use environment variable for API key
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')
chat = model.start_chat(history=[])

# Function to read docx file
def read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

# Prepare context from document
context_file_path = 'static/document.docx'
context = read_docx(context_file_path)

# Function to answer question based on context
def answer_question(question, context):
    retry_count = 0
    max_retries = 5
    retry_delay = 2  # seconds

    while retry_count < max_retries:
        try:
            prompt = f"""Context: {context}

Question: {question}

Please provide a concise and accurate answer based on the given context. If the information is not available in the context, respond with "I'm sorry, I don't have enough information to answer that question."

Answer:"""
            response = chat.send_message(prompt)
            return response.text
        except ResourceExhausted:
            retry_count += 1
            print(f"Quota exceeded. Retrying {retry_count}/{max_retries}...")
            time.sleep(retry_delay)
    
    return "An error occurred: Resource has been exhausted. Please try again later."

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
