from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/download", tags=["download"])

PLC_OUTPUT_FILE = "generated_code.st"
HMI_OUTPUT_FILE = "generated_hmi.html"

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
