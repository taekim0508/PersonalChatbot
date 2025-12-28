# backend/app/main.py
from fastapi import FastAPI
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
