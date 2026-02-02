
import json
import os
import asyncio
from bson import ObjectId

class AsyncJsonCollection:
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def _load(self):
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"DEBUG: Empty load from {self.file_path}")
            return []

    def _save(self, data):
        print(f"DEBUG: Saving {len(data)} items to {self.file_path}")
        with open(self.file_path, 'w') as f:
            # handle ObjectId serialization
            json.dump(data, f, default=str, indent=2)

    async def find_one(self, query):
        data = self._load()
        for item in data:
            match = True
            for k, v in query.items():
                # Handle _id lookups
                if k == "_id":
                    if str(item.get("_id")) != str(v):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                return item
        return None

    async def insert_one(self, document):
        data = self._load()
        if "_id" not in document:
            document["_id"] = str(ObjectId())
        
        # Check uniqueness for email
        if "email" in document:
            for item in data:
                if item.get("email") == document["email"]:
                     # Mimic DuplicateKeyError behavior slightly? or just let app handle it?
                     # App handles check before insert usually.
                     pass

        data.append(document)
        self._save(data)
        return type('InsertOneResult', (object,), {"inserted_id": document["_id"]})()

    async def update_one(self, filter_query, update_doc):
        data = self._load()
        updated = False
        for item in data:
            match = True
            for k, v in filter_query.items():
                if k == "_id":
                    if str(item.get("_id")) != str(v):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            
            if match:
                # Apply update
                if "$set" in update_doc:
                    for k, v in update_doc["$set"].items():
                        item[k] = v
                updated = True
                break
        
        if updated:
            self._save(data)
        return type('UpdateResult', (object,), {"modified_count": 1 if updated else 0})()

class AsyncJsonDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")

    def __getitem__(self, collection_name):
        return AsyncJsonCollection(os.path.join(self.data_dir, f"{collection_name}.json"))
