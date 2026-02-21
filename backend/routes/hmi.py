from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any
from backend.core.openai_client import generate_layout
from backend.core.validator import validate_layout
from backend.core.html_exporter import generate_html_from_json
from backend.core.prompts import SYSTEM_PROMPT
import json

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str

class ModifyRequest(BaseModel):
    previous_layout: Dict[str, Any]
    instruction: str

class ExportRequest(BaseModel):
    layout: Dict[str, Any]
    format: str


@router.post("/generate")
async def generate(req: GenerateRequest, request: Request):
    email = request.headers.get("X-User-Email")
    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(status_code=403, detail="You have reached the 50k quota. Please continue with renewal.")

    try:
        raw = generate_layout(SYSTEM_PROMPT, req.prompt)
        validated = validate_layout(raw)
        
        if email:
            from backend.token_manager import check_and_update_tokens
            used_tokens = (len(req.prompt) // 4) + (len(str(validated)) // 4) + 200
            check_and_update_tokens(email, used_tokens)
            
        return validated
    except Exception as e:
        print(f"Generate Error: {e}")
        # Only re-raise HTTPExceptions, else wrap in 400
        if isinstance(e, HTTPException): 
            raise e
        
        error_msg = str(e)
        if "insufficient_quota" in error_msg.lower() or "429" in error_msg:
             raise HTTPException(status_code=429, detail="Insufficient Quota: The backend OpenAI API key has run out of credits. Please update the API key in the backend/.env file.")
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/modify")
async def modify(req: ModifyRequest):
    try:
        modify_prompt = f"""
Modify this layout:

{json.dumps(req.previous_layout)}

Instruction:
{req.instruction}

Return full updated JSON only.
"""
        raw = generate_layout(SYSTEM_PROMPT, modify_prompt)
        validated = validate_layout(raw)
        return validated
    except Exception as e:
        print(f"Modify Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export")
def export(req: ExportRequest):

    if req.format == "json":
        try:
            json_str = json.dumps(req.layout, indent=2)
            return Response(
                content=json_str,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={req.layout.get('system_name', 'hmi')}.json"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if req.format == "html":
        try:
            html = generate_html_from_json(req.layout)
            return Response(
                content=html,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={req.layout.get('system_name', 'hmi')}.html"
                }
            )
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=400, detail="Unsupported export format")
