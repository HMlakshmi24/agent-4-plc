from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# Temporary in-memory storage
users = {}

class User(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[user.username] = user.password
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: User):
    if user.username not in users or users[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}
