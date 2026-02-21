from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from backend.db import get_user_by_email, update_user_settings

router = APIRouter(prefix="/profile", tags=["profile"])

class UpdateProfileSettings(BaseModel):
    name: str | None = None
    phone: str | None = None
    company: str | None = None
    designation: str | None = None
    department: str | None = None
    experience: int | None = None
    industry_type: str | None = None
    default_plc: str | None = None
    default_language: str | None = None
    strict_mode: bool | None = None
    deterministic_mode: bool | None = None
    auto_validation: bool | None = None
    api_key: str | None = None

async def get_email_from_req(request: Request):
    # Support mock flow and JWT flow
    email = request.headers.get("X-User-Email")
    if email:
        return email
    try:
        from backend.utils import get_current_user
        user = await get_current_user(request)
        return user["email"]
    except:
        return None

@router.get("/me")
async def get_profile(request: Request):
    """Fetch logged-in user's profile and settings"""
    email = await get_email_from_req(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.put("/update")
async def update_profile(update: UpdateProfileSettings, request: Request):
    """Update logged-in user's profile and settings"""
    email = await get_email_from_req(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    update_dict = update.dict(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    update_user_settings(email, update_dict)
    
    updated_user = get_user_by_email(email)

    return {
        "message": "Settings updated successfully",
        "profile": updated_user
    }

@router.post("/logout")
async def logout(request: Request):
    """Logout endpoint"""
    email = await get_email_from_req(request)
    return {"message": f"User {email or 'Unknown'} logged out successfully"}
