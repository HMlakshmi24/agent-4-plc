# main.py
import sys
import os
from pathlib import Path

# Add project root to sys.path to allow 'backend' imports
# This fixes "ModuleNotFoundError: No module named 'backend'" when running from backend/ dir
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import home, login, plc_to_st, download, profile, plc_code_generator
import os

app = FastAPI(title="Agent4PLC Backend")

# =========================================================================
# CORS CONFIGURATION - LOCALHOST ONLY (SECURITY)
# =========================================================================
# Development: Allow localhost only
# Production: Specify exact frontend URL
ALLOWED_ORIGINS = [
    "http://localhost:5173",      # Vite frontend default
    "http://127.0.0.1:5173",
    "http://localhost:5174",      # Vite frontend alt port
    "http://127.0.0.1:5174",
    "http://localhost:3000",      # Alternative port
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home.router)
app.include_router(login.router)
app.include_router(plc_to_st.router)
app.include_router(plc_code_generator.router)  # New improved PLC generator
app.include_router(download.router)
app.include_router(profile.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "Agent4PLC Backend Running on Localhost", "version": "2.0"}

if __name__ == "__main__":
    import uvicorn
    # Run on localhost only (0.0.0.0 for all interfaces is NOT secure for production)
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # Localhost only
        port=8001,
        reload=False
    )
