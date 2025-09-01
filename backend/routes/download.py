from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/download", tags=["download"])

OUTPUT_FILE = "generated_code.st"

@router.get("/")
async def download_file():
    if not os.path.exists(OUTPUT_FILE):
        return {"error": "No ST file generated yet"}
    return FileResponse(OUTPUT_FILE, filename="plc_code.st", media_type="application/octet-stream")
