# backend/routes/profile.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.db import users_collection
from backend.utils import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/profile", tags=["profile"])


# Request body for updating profile
class UpdateProfile(BaseModel):
    name: str | None = None
    phone: str | None = None


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Fetch logged-in user's profile"""
    user = await users_collection.find_one({"_id": ObjectId(current_user["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user["email"],  # cannot be changed
        "name": user.get("name", ""),
        "phone": user.get("phone", "")
    }


@router.put("/update")
async def update_profile(update: UpdateProfile, current_user: dict = Depends(get_current_user)):
    """Update logged-in user's name and phone"""
    user_id = ObjectId(current_user["sub"])

    update_fields = {}
    if update.name is not None:
        update_fields["name"] = update.name
    if update.phone is not None:
        update_fields["phone"] = update.phone

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    await users_collection.update_one(
        {"_id": user_id},
        {"$set": update_fields}
    )

    updated_user = await users_collection.find_one({"_id": user_id})

    return {
        "message": "Profile updated successfully",
        "profile": {
            "email": updated_user["email"],
            "name": updated_user.get("name", ""),
            "phone": updated_user.get("phone", "")
        }
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint (frontend should clear token)"""
    return {"message": f"User {current_user['email']} logged out successfully"}
