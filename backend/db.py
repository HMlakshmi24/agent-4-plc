# backend/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# load .env from same folder
load_dotenv(dotenv_path=".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

if not MONGO_URI or not MONGO_DB:
    raise RuntimeError("❌ MongoDB config missing. Check your .env file!")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

# collections
users_collection = db["users"]