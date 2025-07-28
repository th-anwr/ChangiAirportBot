from fastapi import FastAPI, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import subprocess

from app.chatbot import setup_and_build_advanced_chatbot, final_agent_executor

API_KEY = os.environ.get("CHATBOT_API_KEY", "your-secret-api-key")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

class ChatRequest(BaseModel):
    question: str
    api_key: str

class ChatResponse(BaseModel):
    answer: str

@app.on_event("startup")
def startup_event():
    # Pull the Llama model if not present
    try:
        print(f"Checking if model '{OLLAMA_MODEL}' is available...")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if OLLAMA_MODEL not in result.stdout:
            print(f"Model '{OLLAMA_MODEL}' not found. Pulling...")
            subprocess.run(["ollama", "pull", OLLAMA_MODEL], check=True)
        else:
            print(f"Model '{OLLAMA_MODEL}' is already available.")
    except Exception as e:
        print(f"Error checking/pulling model: {e}")
    setup_and_build_advanced_chatbot(ollama_base_url=OLLAMA_BASE_URL, ollama_model=OLLAMA_MODEL)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "answer": None})

@app.post("/dashboard", response_class=HTMLResponse)
def dashboard_post(request: Request, question: str = Form(...)):
    if final_agent_executor is None:
        return templates.TemplateResponse("dashboard.html", {"request": request, "answer": "Chatbot not initialized."})
    try:
        answer = final_agent_executor.invoke({"question": question})
        return templates.TemplateResponse("dashboard.html", {"request": request, "answer": answer, "question": question})
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {"request": request, "answer": str(e), "question": question})

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if request.api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if final_agent_executor is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    try:
        answer = final_agent_executor.invoke({"question": request.question})
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 