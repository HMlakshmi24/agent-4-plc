from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from backend.openai_client import client
from backend.db import get_user_by_email

router = APIRouter(prefix="/api/ai-help", tags=["ai_help"])

class HelpRequest(BaseModel):
    message: str

async def get_email_from_req(request: Request):
    email = request.headers.get("X-User-Email")
    if email:
        return email
    try:
        from backend.utils import get_current_user
        user = await get_current_user(request)
        return user["email"]
    except:
        pass
        
    return None

class ChatbotResponse(BaseModel):
    reply: str

@router.post("/")
async def get_ai_help(req: HelpRequest, request: Request):
    email = await get_email_from_req(request)
    
    # We can default to system AI, but if user has custom API key, we should try to use it if requested. 
    # For now, we will use the system's client as fallback.
    user_api_key = None
    if email:
        user = get_user_by_email(email)
        if user and user.get("api_key"):
            user_api_key = user["api_key"]
    
    system_instruction = """
    You are an expert Automation & Control Systems Prompt Engineer and Senior PLC Architect.
    Your primary goal is to assist the user meticulously with any industrial automation queries, specifically regarding IEC 61131-3 logic generation and HMI design on this platform.
    
    If the user asks a general or conceptual question about PLC logic, SCADA, or automation, you must answer it fully, providing examples, best practices, and detailed explanations.
    If the user wants to generate logic, DO NOT just give them a prompt. Give them the prompt AND explain how the logic works with a brief Structured Text example so they understand exactly what to do.
    
    A perfect PLC prompt outline for the generator:
    1. Brand/Environment (Siemens, Codesys, Allen-Bradley)
    2. Inputs (with explicit IEC types, e.g., var : BOOL)
    3. Outputs (with explicit IEC types)
    4. Internal flags, Timers (TON, TOF) and Counters (CTU, CTD)
    5. State machine steps or exact boolean rules
    
    A perfect HMI prompt outline for the generator:
    1. Modern Aesthetic and Theme (Dark mode, neon, high contrast, industrial)
    2. Specific Widgets (Tanks with fill levels, Trend Charts, Gauges, Status LEDs, Value Displays)
    3. Exact spatial placement (Top header row, 2-column layout body, footer alarms)
    4. Specific colors for states (Red for fault, Green for running)
    
    Be extremely helpful, insightful, technical, and highly professional. Do not provide brief answers. You must act as their principal engineer mentor.
    """
    
    try:
        # If user provided API key, we could dynamically instantiate an OpenAI client here.
        # But to keep things stable, we'll use the main unified client unless requested otherwise.
        
        # NOTE: Using the new SDK syntax
        response = client.chat.completions.create(
            model="gpt-4o", # Default model
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.message}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content
        return ChatbotResponse(reply=reply)
        
    except Exception as e:
        print(f"AI Help Error: {e}")
        error_msg = str(e)
        if "insufficient_quota" in error_msg.lower() or "429" in error_msg:
             return ChatbotResponse(reply="Insufficient Quota: The backend OpenAI API key has run out of credits. Please update the API key in the backend/.env file.")
             
        return ChatbotResponse(reply=f"API Connection Error: {error_msg}")
