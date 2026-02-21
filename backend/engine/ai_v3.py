import json
from backend.openai_client import client
from backend.models.iec_models import ProgramModel

SYSTEM_PROMPT = """
You are a Deterministic IEC 61131-3 Engineer.
Your output must be ONLY a valid JSON object matching this schema:

{
  "name": "ProgramName",
  "inputs": [{"name": "Start", "type": "BOOL", "comment": "Start Button"}],
  "outputs": [{"name": "Motor", "type": "BOOL"}],
  "internals": [
    {"name": "State", "type": "INT", "initial_value": "0"},
    {"name": "Timer1", "type": "TON"}
  ],
  "logic": [
    "(* State Machine *)",
    "CASE State OF",
    "  0: IF Start THEN State := 10; END_IF;",
    "  10: Motor := TRUE;",
    "END_CASE"
  ]
}

RULES:
1. Do NOT generate 'PROGRAM ... END_PROGRAM' strings. Only JSON.
2. Logic must be a list of strings (lines of code).
3. Use 'internals' for all internal variables, timers (TON/TOF), and counters (CTU/CTD).
4. Strictly follow the user's description.
"""

def generate_iec_model(description: str) -> ProgramModel:
    """
    Asks AI to generate a structured ProgramModel JSON.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or make dynamic
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create an IEC ST program for:\n{description}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Validation by Pydantic
        model = ProgramModel(**data)
        return model
        
    except Exception as e:
        print(f"V3 AI Generation Error: {e}")
        # Fallback empty model to prevent crash, or raise? Raise to trigger retry logic if we had one.
        # For now, return a basic error model
        return ProgramModel(
            name="ErrorProgram",
            inputs=[],
            outputs=[],
            internals=[],
            logic=[f"(* Error generating model: {str(e)} *)"]
        )
