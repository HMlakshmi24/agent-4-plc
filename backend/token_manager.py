import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load env safely
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "agent4plc")

# Use a synchronous pymongo client to avoid async mismatches in FastAPI synchronous routes
_sync_client = MongoClient(MONGO_URI)
_sync_db = _sync_client[DB_NAME]
_users_collection = _sync_db["users"]

TOKEN_LIMIT = 50000

def get_token_usage(email: str):
    """Retrieve current token usage synchronously from MongoDB."""
    user = _users_collection.find_one({"email": email})
    if not user:
        return None
        
    return {
        "tokens_used": user.get("tokens_used", 0),
        "is_blocked": user.get("is_blocked", False)
    }

def check_and_update_tokens(email: str, tokens_used_now: int):
    """Checks token usage synchronously and auto-registers if needed."""
    user = _users_collection.find_one({"email": email})

    if not user:
        # Auto-register if not explicitly registered yet via auth
        user_data = {
            "name": "User",
            "email": email,
            "company": "Guest",
            "phone_number": "",
            "password": "",
            "tokens_used": 0,
            "is_blocked": False,
            "license_type": "Trial"
        }
        try:
            _users_collection.insert_one(user_data)
        except Exception:
            pass # Ignore duplicate key errors on race conditions
        user = user_data

    # Check if blocked
    if user.get("is_blocked", False):
        return {"blocked": True, "reason": "LIMIT_REACHED"}

    # Update tokens
    current_tokens = user.get("tokens_used", 0)
    new_total = current_tokens + tokens_used_now

    if new_total >= TOKEN_LIMIT:
        _users_collection.update_one({"email": email}, {"$set": {"tokens_used": TOKEN_LIMIT, "is_blocked": True}})
        return {"blocked": True, "reason": "LIMIT_REACHED"}

    _users_collection.update_one({"email": email}, {"$set": {"tokens_used": new_total, "is_blocked": False}})

    return {
        "blocked": False,
        "tokens_used": new_total,
        "remaining": TOKEN_LIMIT - new_total
    }
