"""
Token Manager — Accurate Usage Tracking
========================================
Rules:
1. Token counts come ONLY from response.usage.total_tokens (never estimated).
2. MongoDB is the single source of truth — re-fetched on every request.
3. Manual DB reset (used_tokens = 0) is reflected immediately on next request.
4. Every AI call is logged to the 'usage_logs' collection for auditing.
5. No caching — always re-read the user record before checking limits.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

MONGO_URI   = os.getenv("MONGO_URI")
DB_NAME     = os.getenv("MONGO_DB", "agent4plc")
TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", "50000"))

# Synchronous pymongo client (used from sync FastAPI routes)
_sync_client    = MongoClient(MONGO_URI)
_sync_db        = _sync_client[DB_NAME]
_users_col      = _sync_db["users"]
_usage_logs_col = _sync_db["usage_logs"]


# ── Public API ────────────────────────────────────────────────────────────────

def get_token_usage(email: str) -> dict | None:
    """
    Fetch current token usage directly from MongoDB.
    Returns None if user not found.
    Always re-reads from DB — no in-memory cache.
    """
    user = _users_col.find_one({"email": email})
    if not user:
        return None

    used    = user.get("tokens_used", 0)
    limit   = user.get("token_limit", TOKEN_LIMIT)
    blocked = user.get("is_blocked", False)

    # Auto-unblock if admin reset tokens below limit
    if blocked and used < limit:
        _users_col.update_one({"email": email}, {"$set": {"is_blocked": False}})
        blocked = False

    return {
        "email":       email,
        "tokens_used": used,
        "token_limit": limit,
        "remaining":   max(0, limit - used),
        "is_blocked":  blocked,
    }


def check_and_update_tokens(email: str, tokens_consumed: int,
                             endpoint: str = "") -> dict:
    """
    Core gatekeeper called before (check) and after (update) every AI request.

    Args:
        email:           User email address.
        tokens_consumed: Exact count from response.usage.total_tokens.
                         Pass 0 to only check quota without updating.
        endpoint:        Route name for audit log (e.g. '/generate').

    Returns dict with keys: blocked, tokens_used, token_limit, remaining, reason(opt)
    """
    # Always re-fetch from DB — no cache, so manual resets work instantly
    user = _users_col.find_one({"email": email})

    if not user:
        user = {
            "name":         "User",
            "email":        email,
            "company":      "Guest",
            "phone_number": "",
            "password":     "",
            "tokens_used":  0,
            "token_limit":  TOKEN_LIMIT,
            "is_blocked":   False,
            "license_type": "Trial",
        }
        try:
            _users_col.insert_one(user)
        except Exception:
            pass  # Concurrent insert — already created

    current_used = user.get("tokens_used", 0)
    limit        = user.get("token_limit", TOKEN_LIMIT)
    is_blocked   = user.get("is_blocked", False)

    # Auto-unblock if admin manually reset tokens in MongoDB
    if is_blocked and current_used < limit:
        _users_col.update_one({"email": email}, {"$set": {"is_blocked": False}})
        is_blocked = False

    # Quota check
    if is_blocked:
        return {
            "blocked":     True,
            "reason":      "LIMIT_REACHED",
            "tokens_used": current_used,
            "token_limit": limit,
            "remaining":   0,
        }

    # Read-only check (pass 0 to just verify quota without consuming)
    if tokens_consumed == 0:
        return {
            "blocked":     False,
            "tokens_used": current_used,
            "token_limit": limit,
            "remaining":   max(0, limit - current_used),
        }

    # Update usage with real token count
    new_total   = current_used + tokens_consumed
    now_blocked = new_total >= limit

    _users_col.update_one(
        {"email": email},
        {"$set": {
            "tokens_used": min(new_total, limit),
            "is_blocked":  now_blocked,
        }}
    )

    # Audit log — never blocks the main flow
    _log_usage(email, tokens_consumed, endpoint, new_total)

    if now_blocked:
        return {
            "blocked":     True,
            "reason":      "LIMIT_REACHED",
            "tokens_used": min(new_total, limit),
            "token_limit": limit,
            "remaining":   0,
        }

    return {
        "blocked":     False,
        "tokens_used": new_total,
        "token_limit": limit,
        "remaining":   max(0, limit - new_total),
    }


def reset_token_usage(email: str) -> bool:
    """Admin helper: reset tokens_used to 0 and unblock user."""
    result = _users_col.update_one(
        {"email": email},
        {"$set": {"tokens_used": 0, "is_blocked": False}}
    )
    return result.modified_count > 0


# ── Internal helpers ──────────────────────────────────────────────────────────

def _log_usage(email: str, tokens: int, endpoint: str, running_total: int):
    """Write one audit record per AI call to usage_logs collection."""
    try:
        _usage_logs_col.insert_one({
            "email":         email,
            "tokens_used":   tokens,
            "running_total": running_total,
            "endpoint":      endpoint or "unknown",
            "timestamp":     datetime.now(timezone.utc),
        })
    except Exception as e:
        print(f"[WARN] usage_logs write failed: {e}")
