# backend/db.py
import os
from backend.local_db import AsyncJsonDatabase
from dotenv import load_dotenv

# load .env from same folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

MONGO_DB = os.getenv("MONGO_DB", "agent4plc")

# Switch to Local JSON Database
print(f"[OK] Using Local File Database: {MONGO_DB}")
db = AsyncJsonDatabase(MONGO_DB)

# collections
users_collection = db["users"]
