# Vercel entrypoint - imports the FastAPI app from backend
import sys
import os
from pathlib import Path

# Get the backend directory path
backend_path = Path(__file__).parent.parent / "backend"
backend_path = backend_path.resolve()

# Add backend directory to Python path so imports work correctly
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Change working directory to backend for relative path resolution
# This ensures paths like "index/chunks.json" in main.py resolve correctly
original_cwd = os.getcwd()
try:
    os.chdir(str(backend_path))
    # Import the FastAPI app
    from app.main import app
finally:
    # Restore original working directory (though Vercel may not need this)
    os.chdir(original_cwd)

# Export the app for Vercel
__all__ = ["app"]

