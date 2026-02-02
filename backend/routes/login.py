# backend/routes/login.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.db import users_collection
from backend.utils import hash_password, verify_password, create_access_token, send_welcome_email

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterUser(BaseModel):
    email: EmailStr
    password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(user: RegisterUser):
    # check if user exists
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)
    new_user = {"email": user.email, "hashed_password": hashed_pw}
    await users_collection.insert_one(new_user)

    # send welcome email
    send_welcome_email(user.email, user.email, user.password)

    return {"message": "User registered successfully"}

@router.post("/login")
async def login(user: LoginUser):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user["_id"]), "email": db_user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(db_user["_id"]),
        "email": db_user["email"]
    }
