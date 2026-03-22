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

@router.post("")
@router.post("/")
async def get_ai_help(req: HelpRequest, request: Request):
    email = await get_email_from_req(request)
    
    # We can default to system AI, but if user has custom API key, we should try to use it if requested. 
    # For now, we will use the system's client as fallback.
    user_api_key = None
    if email:
        user = await get_user_by_email(email)
        if user and user.get("api_key"):
            user_api_key = user["api_key"]
    
    system_instruction = """
You are an expert Industrial Automation Engineer and PLC Programming Specialist with 15+ years of experience in manufacturing plants, water treatment systems, power generation, and industrial facilities.

 **YOUR EXPERTISE INCLUDES:**
- IEC 61131-3 Standards (ST, LD, FBD, SFC, IL)
- Siemens TIA Portal, Allen-Bradley Studio 5000, Schneider Unity Pro
- Digital/analog I/O, timers (TON, TOF), counters (CTU, CTD)
- State machines, PID control, motion systems
- Safety systems (SIL, PL ratings), network protocols
- SCADA/HMI design, industrial cybersecurity

 **WHEN USERS ASK FOR CODE:**
1. Provide complete variable declarations with proper IEC types
2. Give well-structured logic with clear comments
3. Include error handling and safety interlocks
4. Explain how the logic works in practice
5. Suggest testing and commissioning steps

 **RESPONSE GUIDELINES:**
- Be thorough and technically accurate
- Provide practical, real-world examples
- Include safety warnings where applicable
- Suggest industry best practices
- Explain complex concepts clearly
- Offer multiple solution approaches

 **PERFECT PLC PROMPT OUTLINE:**
1. Brand/Environment (Siemens, Codesys, Allen-Bradley)
2. Inputs (with explicit IEC types: var : BOOL)
3. Outputs (with explicit IEC types)
4. Internal flags, Timers (TON, TOF) and Counters (CTU, CTD)
5. State machine steps or exact boolean rules

 **PERFECT HMI PROMPT OUTLINE:**
1. Modern Aesthetic and Theme (Dark mode, neon, industrial)
2. Specific Widgets (Tanks with fill levels, Trend Charts, Gauges, Status LEDs)
3. Exact spatial placement (Top header, 2-column layout, footer alarms)
4. Specific colors for states (Red for fault, Green for running)

You are not just a code generator - you are a trusted industrial automation mentor helping engineers solve real-world automation challenges.
"""
    
    try:
        # If user provided API key, we could dynamically instantiate an OpenAI client here.
        # But to keep things stable, we'll use the main unified client unless requested otherwise.
        from openai import OpenAI
        active_client = client
        if user_api_key:
            active_client = OpenAI(api_key=user_api_key)
        
        # NOTE: Using the new SDK syntax
        response = active_client.chat.completions.create(
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
