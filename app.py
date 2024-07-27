from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import google.generativeai as genai
import docx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure API key
api_key = "AIzaSyA105E6F2HVXLeGzJOJRGTarYPxd_Jdx9w"  # Replace with your API key
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
    try:
        prompt = f"""Context: {context}

Question: {question}

Please provide a concise and accurate answer based on the given context. If the information is not available in the context, respond with "I'm sorry, I don't have enough information to answer that question."

Answer:"""
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"

class Message(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send_message/")
async def handle_send_message(msg: Message):
    question = msg.message
    answer = answer_question(question, context)
    return {"message": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
