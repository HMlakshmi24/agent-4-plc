from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Welcome to Agent4PLC API"}
