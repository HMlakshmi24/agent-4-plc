import sys
import io
from pathlib import Path
from contextlib import asynccontextmanager

# ──────────────────────────────────────────────────────────────
# UTF-8 fix (prevents UnicodeEncodeError on Windows terminals)
# ──────────────────────────────────────────────────────────────
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

if hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# ──────────────────────────────────────────────────────────────
# sys.path fix (allows `from backend.xxx import` when run directly)
# ──────────────────────────────────────────────────────────────
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ──────────────────────────────────────────────────────────────
# FastAPI & App Imports
# ──────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.db import init_db

# Routers
from backend.routes.generate import router as generate_router
from backend.routes.history import router as history_router
from backend.routes.hmi import router as hmi_router
from backend.routes.ld_api import router as ld_api_router
from backend.routes.login import router as auth_router
from backend.routes.profile import router as profile_router
from backend.routes.tokens import router as tokens_router, user_router as user_usage_router
from backend.routes.ai_help import router as ai_help_router
from backend.routes.support import router as support_router
from backend.routes.perfect_plc_api import router as perfect_plc_router
from backend.routes.pid_generator import router as pid_router
from backend.routes.export import router as export_router

# ──────────────────────────────────────────────────────────────
# Lifespan (Modern Startup / Shutdown)
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Industrial PLC Backend...")
    await init_db()
    print("✅ MongoDB Initialized")
    yield
    print("🛑 Shutting down backend...")


# ──────────────────────────────────────────────────────────────
# FastAPI App Initialization
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Industrial PLC Code Generator",
    version="2.0",
    lifespan=lifespan
)

# ──────────────────────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(generate_router)
app.include_router(history_router)
app.include_router(hmi_router, prefix="/api/hmi", tags=["hmi"])
app.include_router(ld_api_router)
app.include_router(tokens_router)
app.include_router(ai_help_router)
app.include_router(support_router)
app.include_router(perfect_plc_router)
app.include_router(pid_router, prefix="/api/pid", tags=["pid"])
app.include_router(export_router, prefix="/api/export", tags=["export"])
app.include_router(user_usage_router)  # GET /api/user/usage, GET /api/user/usage/logs

# ──────────────────────────────────────────────────────────────
# Root Health Check
# ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "Industrial PLC Backend Ready",
        "version": "2.0-Production",
        "mode": "AI with IEC Validation & Retry"
    }

# ──────────────────────────────────────────────────────────────
# Local Development Runner
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )