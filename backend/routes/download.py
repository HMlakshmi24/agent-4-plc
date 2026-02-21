from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv

# Load env to get PLC_OUTPUT_DIR
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
PLC_OUTPUT_DIR = os.getenv("PLC_OUTPUT_DIR", "backend/plc")

router = APIRouter(prefix="/download", tags=["download"])

PLC_OUTPUT_FILE = os.path.join(PLC_OUTPUT_DIR, "generated_code.st")
HMI_OUTPUT_FILE = os.path.join(PLC_OUTPUT_DIR, "generated_hmi.html")

@router.get("/plc")
async def download_plc_file():
    """Download the generated PLC Structured Text (.st) file."""
    if not os.path.exists(PLC_OUTPUT_FILE):
        return {"error": "No PLC file generated yet"}
    return FileResponse(
        PLC_OUTPUT_FILE,
        filename="plc_code.st",
        media_type="application/octet-stream"
    )

@router.get("/hmi")
async def download_hmi_file():
    """Download the generated HMI HTML (.html) file."""
    if not os.path.exists(HMI_OUTPUT_FILE):
        return {"error": "No HMI file generated yet"}
    return FileResponse(
        HMI_OUTPUT_FILE,
        filename="hmi_interface.html",
        media_type="text/html"
    )
