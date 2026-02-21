from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from backend import db
import sqlite3
import datetime

router = APIRouter(prefix="/history", tags=["history"])

class HistoryItem(BaseModel):
    program_name: str
    description: str
    code: str
    language: str
    brand: str
    timestamp: Optional[str] = None
    type: Optional[str] = "plc"  # Add type to distinguish plc vs hmi

async def get_email_from_req(request: Request):
    # Try custom header first for mock cached users
    email = request.headers.get("X-User-Email")
    if email:
        return email
    try:
        from backend.utils import get_current_user
        user = await get_current_user(request)
        return user["email"]
    except:
        return None

def _get_history_connection():
    # Make sure we use the same SQLite file as token routing
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "token_users.db")
    return sqlite3.connect(db_path)

def _init_history_table():
    conn = _get_history_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            program_name TEXT,
            description TEXT,
            code TEXT,
            language TEXT,
            brand TEXT,
            type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_init_history_table()

@router.get("/")
async def get_history(request: Request):
    email = await get_email_from_req(request)
    if not email:
        return []
        
    conn = _get_history_connection()
    c = conn.cursor()
    c.execute("SELECT id, program_name, description, code, language, brand, type, created_at FROM history WHERE user_email=? ORDER BY id DESC LIMIT 100", (email,))
    rows = c.fetchall()
    conn.close()
    
    items = []
    for r in rows:
        items.append({
            "_id": str(r[0]),
            "program_name": r[1],
            "description": r[2],
            "code": r[3],
            "language": r[4],
            "brand": r[5],
            "type": r[6],
            "created_at": r[7]
        })
    return items

@router.post("/")
async def save_history(item: HistoryItem, request: Request):
    email = await get_email_from_req(request)
    if not email:
        return {"message": "Not authenticated"}
        
    conn = _get_history_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (user_email, program_name, description, code, language, brand, type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email, item.program_name, item.description, item.code, item.language, item.brand, item.type))
    conn.commit()
    conn.close()
    
    return {"message": "History saved"}
