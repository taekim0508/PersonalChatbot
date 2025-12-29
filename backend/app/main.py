# backend/app/main.py
from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.chat.routes import router as chat_router
from app.core.kb import load_kb, set_kb

app = FastAPI(title="Tae Resume Chatbot API")

@app.on_event("startup")
def startup() -> None:
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)

app.include_router(chat_router)

@app.get("/health")
def health():
    return {"status": "ok"}
