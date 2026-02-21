# backend/routes/login.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from backend import db
from backend.utils import (
    hash_password,
    verify_password,
    create_access_token,
    send_welcome_email,
    send_otp_email
)

router = APIRouter(prefix="/auth", tags=["auth"])


# -------------------- Models --------------------

class RegisterUser(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: str | None = None
    phone: str | None = None


class LoginUser(BaseModel):
    email: EmailStr
    password: str


# -------------------- Register --------------------

@router.post("/register")
async def register(user: RegisterUser):

    existing = await db.get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)

    created = await db.create_user(
        user.name,
        user.email,
        user.company or "",
        user.phone or "",
        hashed_pw
    )

    if not created:
        raise HTTPException(status_code=400, detail="User already exists")

    await db.update_user_settings(user.email, {"role": "engineer"})

    print(f"[MOCK] Welcome email sent to {user.email}")

    return {"message": "User registered successfully"}


# -------------------- Login --------------------

@router.post("/login")
async def login(user: LoginUser):

    db_user = await db.get_user_by_email(user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")

    stored_password = db_user.get("password")

    if not stored_password:
        raise HTTPException(
            status_code=401,
            detail="Password not set for user. Please reset your password."
        )

    if not verify_password(user.password, stored_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token({
        "sub": db_user["email"],
        "email": db_user["email"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user["email"],
        "email": db_user["email"],
        "name": db_user.get("name", "Engineer"),
        "company": db_user.get("company", ""),
        "role": db_user.get("role", "engineer")
    }


# -------------------- Forgot Password --------------------

import random

class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


otp_store = {}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordReq):

    db_user = await db.get_user_by_email(req.email)

    if not db_user:
        return {"message": "If that email is registered, we have sent an OTP."}

    otp = str(random.randint(100000, 999999))
    otp_store[req.email] = otp

    print(f"[MOCK] Sending OTP {otp} to {req.email}")
    send_otp_email(req.email, db_user.get("name", "User"), otp)

    return {"message": "If that email is registered, we have sent an OTP."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordReq):

    valid_otp = otp_store.get(req.email)

    if not valid_otp or valid_otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    db_user = await db.get_user_by_email(req.email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(req.new_password)

    await db.update_user_settings(req.email, {"password": hashed_pw})

    del otp_store[req.email]

    return {"message": "Password updated successfully"}