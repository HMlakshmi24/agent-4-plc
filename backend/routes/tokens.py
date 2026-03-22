"""
Token Usage API
================
Endpoints:
  GET /api/tokens/          — legacy (kept for backwards compat)
  GET /api/user/usage       — primary endpoint the frontend should use
  GET /api/user/usage/logs  — last N audit log entries for the user
"""

from fastapi import APIRouter, Request, HTTPException
from backend.token_manager import get_token_usage, TOKEN_LIMIT

# ── Legacy router ─────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/tokens", tags=["tokens"])

# ── New user router (also imported in main.py) ────────────────────────────────
user_router = APIRouter(prefix="/api/user", tags=["usage"])


# ── Shared helper ─────────────────────────────────────────────────────────────

async def _get_email(request: Request) -> str | None:
    email = request.headers.get("X-User-Email")
    if email:
        return email
    try:
        from backend.utils import get_current_user
        user = await get_current_user(request)
        return user.get("email")
    except Exception:
        return None


# ── Legacy endpoint (unchanged — keeps existing frontend working) ─────────────

@router.get("/")
async def get_tokens(request: Request):
    """
    Returns token usage. Re-reads MongoDB on every call — no cache.
    Admin DB resets are reflected immediately.
    """
    email = await _get_email(request)
    if not email:
        return {"used": 0, "limit": TOKEN_LIMIT, "blocked": False}

    usage = get_token_usage(email)
    if not usage:
        return {"used": 0, "limit": TOKEN_LIMIT, "blocked": False}

    return {
        "used":      usage["tokens_used"],
        "limit":     usage["token_limit"],
        "blocked":   usage["is_blocked"],
        "remaining": usage["remaining"],
    }


# ── Primary usage endpoint ────────────────────────────────────────────────────

@user_router.get("/usage")
async def get_usage(request: Request):
    """
    Primary endpoint — frontend must use this to show used / limit.
    Always fetches from MongoDB so manual resets show immediately.

    Response:
        {
          "email":       "user@example.com",
          "used_tokens": 2000,
          "token_limit": 50000,
          "remaining":   48000,
          "is_blocked":  false
        }
    """
    email = await _get_email(request)
    if not email:
        raise HTTPException(status_code=401, detail="Authentication required")

    usage = get_token_usage(email)
    if not usage:
        return {
            "email":       email,
            "used_tokens": 0,
            "token_limit": TOKEN_LIMIT,
            "remaining":   TOKEN_LIMIT,
            "is_blocked":  False,
        }

    return {
        "email":       usage["email"],
        "used_tokens": usage["tokens_used"],
        "token_limit": usage["token_limit"],
        "remaining":   usage["remaining"],
        "is_blocked":  usage["is_blocked"],
    }


@user_router.get("/usage/logs")
async def get_usage_logs(request: Request, limit: int = 50):
    """
    Returns the last N audit log entries from usage_logs collection.
    Useful for debugging token consumption or showing activity history.

    Response: { email, logs: [{ endpoint, tokens_used, running_total, timestamp }] }
    """
    email = await _get_email(request)
    if not email:
        raise HTTPException(status_code=401, detail="Authentication required")

    import os
    from pymongo import MongoClient
    from dotenv import load_dotenv
    from pathlib import Path

    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path, override=True)

    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db     = client[os.getenv("MONGO_DB", "agent4plc")]
        logs   = list(
            db["usage_logs"]
            .find({"email": email}, {"_id": 0, "email": 0})
            .sort("timestamp", -1)
            .limit(min(limit, 200))
        )
        for log in logs:
            ts = log.get("timestamp")
            if hasattr(ts, "isoformat"):
                log["timestamp"] = ts.isoformat()
        return {"email": email, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch logs: {e}")
