from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.openai_client import generate_hmi_layout
from backend.engine.validator import validate_layout
from backend.engine.prompt import SYSTEM_PROMPT

router = APIRouter()

class HMIRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate(req: HMIRequest):
    try:
        # 1. Generate Raw JSON from LLM (Strict Mode)
        raw_json = generate_hmi_layout(SYSTEM_PROMPT, req.prompt)
        
        # 2. Validate
        validated_layout = validate_layout(raw_json)
        
        # 3. Return Direct JSON (No nesting)
        return validated_layout 
        
    except Exception as e:
        print(f"HMI Generation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
