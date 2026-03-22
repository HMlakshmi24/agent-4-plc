from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any
from backend.core.openai_client import generate_layout
from backend.core.validator import validate_layout
from backend.core.enhanced_html_exporter_fixed import generate_enhanced_html_from_json, generate_pid_html_from_json
from backend.core.prompts import SYSTEM_PROMPT
from backend.engine.hmi_agentic_pipeline import run_hmi_agentic_pipeline
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
    user_api_key = None
    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(status_code=403, detail="You have reached the 50k quota. Please continue with renewal.")
            
        from backend.db import get_user_by_email
        user = await get_user_by_email(email)
        if user and user.get("api_key"):
            user_api_key = user.get("api_key")

    try:
        print("------- IN HMI ROUTE ----------")
        print("Using Agentic Pipeline V3 for HMI generation")
        print("-------------------------------")
        validated = run_hmi_agentic_pipeline(req.prompt, api_key=user_api_key)

        # Use real token count embedded by pipeline — never estimate
        real_tokens = validated.pop("_tokens_used", 0)
        if email and real_tokens > 0:
            from backend.token_manager import check_and_update_tokens
            check_and_update_tokens(email, real_tokens, "/api/hmi/generate")

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
async def modify(req: ModifyRequest, request: Request):
    email = request.headers.get("X-User-Email")
    user_api_key = None
    if email:
        from backend.db import get_user_by_email
        user = await get_user_by_email(email)
        if user and user.get("api_key"):
            user_api_key = user.get("api_key")
            
    try:
        modify_prompt = f"""
Modify this layout:

{json.dumps(req.previous_layout)}

Instruction:
{req.instruction}

Return full updated JSON only.
"""
        raw = generate_layout(SYSTEM_PROMPT, modify_prompt, api_key=user_api_key)
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
            # Check if this is a P&ID diagram
            mode = req.layout.get('mode', req.layout.get('view_mode', req.layout.get('style', 'normal')))
            if mode == 'pid' or req.layout.get('style') == 'pid':
                html = generate_pid_html_from_json(req.layout)
            else:
                html = generate_enhanced_html_from_json(req.layout)
            
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
