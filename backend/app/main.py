# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.chat.routes import router as chat_router
from app.core.kb import load_kb, set_kb

app = FastAPI(title="Tae Resume Chatbot API")

# CORS (Cross-Origin Resource Sharing) middleware configuration
# Purpose: Allows the frontend (running on different port/domain) to make API requests
# 
# Why this is needed:
# - Frontend runs on Vite dev server (typically localhost:5173)
# - Backend runs on FastAPI server (typically localhost:8000)
# - Browsers block cross-origin requests by default (same-origin policy)
# - CORS middleware tells browser it's safe to allow these requests
#
# Design decisions:
# - allow_origins: List of allowed origins (frontend URLs)
#   - In development: Allow localhost with any port (Vite uses random ports sometimes)
#   - In production: Restrict to specific domain from FRONTEND_URL env var
# - allow_credentials: True allows cookies/auth headers (not needed now, but future-proof)
# - allow_methods: Restrict to needed methods (GET, POST) in production
# - allow_headers: Restrict to needed headers in production
#
# Security: In production, only allow your actual frontend domain.
# Set FRONTEND_URL environment variable to your deployed frontend URL.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# Configure allowed origins based on environment
if ENVIRONMENT == "production" and FRONTEND_URL:
    # Production: Only allow the specified frontend URL
    allowed_origins = [FRONTEND_URL]
    # Include OPTIONS for CORS preflight requests
    allowed_methods = ["GET", "POST", "OPTIONS"]
    # Allow headers needed for CORS preflight and actual requests
    allowed_headers = ["Content-Type", "Accept", "Authorization", "Origin", "X-Requested-With"]
else:
    # Development: Allow localhost for local development
    allowed_origins = [
        "http://localhost:5173",  # Default Vite dev server port
        "http://localhost:3000",  # Alternative common dev port
        "http://127.0.0.1:5173",  # Alternative localhost format
        "http://127.0.0.1:3000",
    ]
    allowed_methods = ["*"]  # Allow all methods in dev
    allowed_headers = ["*"]  # Allow all headers in dev

# Store for debug endpoint
CORS_CONFIG = {
    "allowed_origins": allowed_origins,
    "allowed_methods": allowed_methods,
    "allowed_headers": allowed_headers,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
)

@app.on_event("startup")
def startup() -> None:
    """
    Startup event handler.
    
    Purpose: Loads the knowledge base into memory when the server starts.
    
    Why this approach:
    - Knowledge base is loaded once at startup, not on every request
    - Faster response times (no file I/O on each request)
    - Memory-efficient: single instance shared across all requests
    
    Design decision: Using FastAPI's startup event ensures KB is ready
    before any requests are processed, preventing race conditions.
    """
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)

# Include the chat router
# Purpose: Registers all chat-related endpoints (e.g., POST /chat)
# 
# Why this approach:
# - Keeps route definitions organized in separate modules
# - Router prefix "/chat" means endpoints are at /chat, /chat/health, etc.
# - Makes it easy to add more routers later (e.g., /admin, /analytics)
app.include_router(chat_router)

@app.get("/")
def root():
    """
    Root endpoint.
    
    Purpose: Provides basic API information and prevents 404 errors on root path.
    """
    return {
        "message": "Tae Resume Chatbot API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "chat": "/chat"
        }
    }

@app.get("/health")
def health():
    """
    Health check endpoint.
    
    Purpose: Allows frontend and monitoring tools to verify backend is running.
    
    Why this exists:
    - Simple endpoint that doesn't require authentication
    - Can be used for load balancer health checks
    - Frontend can check connection status before making requests
    
    Design decision: Separate from chat router because it's a system endpoint,
    not a chat feature. Keeps concerns separated.
    """
    return {"status": "ok"}

@app.get("/debug/cors")
def debug_cors():
    """
    Debug endpoint to check CORS configuration.
    
    Purpose: Helps diagnose CORS issues by showing current configuration.
    Only use this in development or temporarily for debugging.
    """
    return {
        "environment": ENVIRONMENT,
        "frontend_url": FRONTEND_URL,
        "allowed_origins": CORS_CONFIG["allowed_origins"],
        "allowed_methods": CORS_CONFIG["allowed_methods"],
        "allowed_headers": CORS_CONFIG["allowed_headers"],
    }
