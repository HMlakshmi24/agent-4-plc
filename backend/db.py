# backend/db.py

import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo import ASCENDING

# ------------------------------------------------------------------
# Load .env from project root (safe regardless of cwd)
# ------------------------------------------------------------------
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "agent4plc")
COLLECTION_NAME = "users"

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI not found in environment variables!")

# ------------------------------------------------------------------
# Mongo Client (Async)
# ------------------------------------------------------------------
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[COLLECTION_NAME]


# ------------------------------------------------------------------
# Init DB (Create Unique Index)
# ------------------------------------------------------------------
async def init_db():
    await users_collection.create_index(
        [("email", ASCENDING)],
        unique=True
    )
    print("[OK] MongoDB initialized with unique email index.")


# ------------------------------------------------------------------
# CRUD OPERATIONS
# ------------------------------------------------------------------

async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    if not user:
        return None

    return {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone_number": user.get("phone_number", ""),
        "password": user.get("password", ""),
        "company": user.get("company", ""),
        "tokens_used": user.get("tokens_used", 0),
        "is_blocked": user.get("is_blocked", False),
        "designation": user.get("designation", ""),
        "department": user.get("department", ""),
        "experience": user.get("experience", 0),
        "license_type": user.get("license_type", "Trial"),
        "industry_type": user.get("industry_type", ""),
        "default_plc": user.get("default_plc", "Siemens"),
        "default_language": user.get("default_language", "ST"),
        "strict_mode": user.get("strict_mode", True),
        "deterministic_mode": user.get("deterministic_mode", True),
        "auto_validation": user.get("auto_validation", True),
        "api_key": user.get("api_key", "")
    }


async def create_user(name, email, company, phone_number="", password=""):
    try:
        user_data = {
            "name": name,
            "email": email,
            "company": company,
            "phone_number": phone_number,
            "password": password,
            "tokens_used": 0,
            "is_blocked": False,
            "license_type": "Trial"
        }
        await users_collection.insert_one(user_data)
        return True
    except Exception as e:
        if "duplicate key" in str(e).lower():
            return False
        raise e


async def update_tokens(email: str, tokens: int):
    # Enforce global 50k token limit
    blocked = tokens >= 50000

    await users_collection.update_one(
        {"email": email},
        {"$set": {
            "tokens_used": tokens,
            "is_blocked": blocked
        }}
    )


async def update_user_settings(email: str, settings: dict):

    valid_cols = [
        "name", "company", "phone_number", "password",
        "designation", "department", "experience",
        "industry_type", "default_plc", "default_language",
        "strict_mode", "deterministic_mode",
        "auto_validation", "api_key"
    ]

    update_data = {k: v for k, v in settings.items() if k in valid_cols}

    if update_data:
        await users_collection.update_one(
            {"email": email},
            {"$set": update_data}
        )