
import asyncio
import os
from backend.local_db import AsyncJsonDatabase

async def test_db():
    print("Testing AsyncJsonDatabase...")
    db_name = "test_db"
    db = AsyncJsonDatabase(db_name)
    users = db["users"]
    
    print(f"File path: {users.file_path}")
    
    # Clean up
    if os.path.exists(users.file_path):
        os.remove(users.file_path)
    
    # Insert
    doc = {"name": "Test User", "email": "test@example.com"}
    print(f"Inserting: {doc}")
    res = await users.insert_one(doc)
    print(f"Inserted ID: {res.inserted_id}")
    
    # Find
    print("Finding...")
    found = await users.find_one({"email": "test@example.com"})
    print(f"Found: {found}")
    
    if found and found["name"] == "Test User":
        print("✅ Insert & Find Success")
    else:
        print("❌ Insert & Find Failed")

if __name__ == "__main__":
    asyncio.run(test_db())
