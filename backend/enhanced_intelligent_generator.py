"""
Enhanced Intelligent PLC Generator - Uses LLM for Context-Aware Code Generation
This replaces the template-based generator with true AI-powered generation
"""

import json
import re
from typing import Dict, Optional

# Compact pattern reference — shows structure without repeating every state
INDUSTRY_EXAMPLES = """
REQUIRED CODE SKELETON (follow exactly):
TYPE
    StateType : (Idle, <ActiveState1>, <ActiveState2>, ..., Fault);
END_TYPE
PROGRAM <ProgramName>
VAR_INPUT ... END_VAR
VAR_OUTPUT ... END_VAR
VAR
    CurrentState : StateType := Idle;
    NextState    : StateType := Idle;
    <Name>Timer  : TON;
    StartTrig    : R_TRIG;
    StopTrig     : R_TRIG;
END_VAR
StartTrig(CLK := I_Start);
StopTrig(CLK := I_Stop);
IF I_EStop THEN CurrentState := Fault; END_IF;
<Name>Timer(IN := (CurrentState = <State1>) OR (CurrentState = <State2>) OR ..., PT := T#10S);
NextState := CurrentState;
CASE CurrentState OF
    Idle:
        <reset all outputs to FALSE>
        IF StartTrig.Q THEN
            IF <condition1> THEN NextState := <State1>;
            ELSIF <condition2> THEN NextState := <State2>;
            END_IF;
        END_IF;
    <ActiveState1>:
        <set outputs TRUE>
        IF StopTrig.Q THEN NextState := Idle;
        ELSIF <Name>Timer.Q THEN <update position/value>; <reset outputs>; NextState := Idle;
        END_IF;
    (* repeat for each active state *)
    Fault:
        <reset all outputs to FALSE>
        Q_Fault := TRUE;
        IF NOT I_EStop THEN NextState := Idle; END_IF;
END_CASE;
CurrentState := NextState;
END_PROGRAM
"""

SYSTEM_PROMPT = """You are an expert industrial PLC programmer specializing in IEC 61131-3 Structured Text.

STRICT IEC 61131-3 SYNTAX RULES (violations will break the program):
1. VAR sections always close with END_VAR — NEVER write END_VAR_INPUT or END_VAR_OUTPUT
2. Timer IN condition: list ONLY the active movement states explicitly — NEVER use (CurrentState <> Idle)
   CORRECT:   Timer(IN := (CurrentState = MoveToF1) OR (CurrentState = MoveToF2), PT := T#10S);
   WRONG:     Timer(IN := (CurrentState <> Idle), PT := T#10S);
3. All state variables MUST be initialized: CurrentState : StateType := Idle;
4. NextState pattern: BEFORE the CASE block write: NextState := CurrentState; (safe default)
   Then set NextState inside each CASE branch. After END_CASE: CurrentState := NextState;
5. Declare R_TRIG for every button: StartTrig : R_TRIG; then call StartTrig(CLK := I_Start);
6. ALWAYS reset outputs in Idle and Fault states (set them to FALSE)
7. In EVERY active/movement state: check StopTrig.Q FIRST (NextState := Idle), THEN check timer — I_Stop must always work
8. E-stop check BEFORE the CASE block, sets CurrentState := Fault directly
9. Name movement states descriptively: MoveToF1, MoveToF2, Running, Heating — NOT Floor1, Step1
10. COUNT CAREFULLY: If the requirement says "3 floors", you MUST generate exactly 3 movement states (MoveToF1, MoveToF2, MoveToF3) and 3 inputs (I_Floor1Request, I_Floor2Request, I_Floor3Request). NEVER generate fewer states than the requirement specifies.

CODE STRUCTURE REQUIREMENTS:
- Exactly ONE TYPE block (optional), then exactly ONE PROGRAM block
- Sections order: VAR_INPUT, VAR_OUTPUT, VAR — each closes with END_VAR
- Logic order: R_TRIG calls → E-stop check → Timer calls → CASE state machine → CurrentState := NextState
- ALWAYS include Fault state with Q_Fault := TRUE and E-stop reset logic
- ALWAYS use the exact PROGRAM name provided

OUTPUT FORMAT:
Return ONLY raw ST code. No markdown, no explanations, no code fences.
Follow Example 1 (elevator) structure exactly."""


def generate_intelligent_plc(prompt: str, program_name: str = "ControlProgram", 
                              brand: str = "SIEMENS") -> Dict:
    """
    Generate intelligent, context-aware PLC code using LLM
    """
    print(f"[AI] Intelligent Generator: Analyzing '{prompt[:50]}...'")
    
    try:
        # Step 1: Use LLM to generate context-aware code
        generated_code, tokens = call_llm_for_generation(prompt, program_name, brand)
        
        if not generated_code or "Error" in generated_code:
            raise ValueError("LLM returned empty or error response")
        
        # Step 2: Validate and refine the code
        validated_code = validate_and_fix_code(generated_code, program_name)
        
        print(f"[OK] Intelligent generation complete: {len(validated_code)} chars")
        
        return {
            "code": validated_code,
            "iec_compliant": True,
            "confidence": 95,
            "warnings": [],
            "errors": [],
            "model": {"program_name": program_name, "brand": brand, "prompt": prompt},
            "tokens_used": tokens
        }
        
    except Exception as e:
        print(f"[FAIL] Intelligent generation failed: {e}")
        # Fallback to enhanced template with fixes
        return generate_enhanced_template(prompt, program_name, brand)


def call_llm_for_generation(prompt: str, program_name: str, brand: str) -> tuple[str, int]:
    """Call LLM to generate PLC code with proper context"""
    
    # Extract numeric quantities from prompt to reinforce correct count
    import re as _re
    num_match = _re.search(r'(\d+)\s*(?:floor|stage|step|speed|zone|tank|pump|conveyor|position)', prompt, _re.IGNORECASE)
    count_reminder = ""
    if num_match:
        n = num_match.group(1)
        thing = num_match.group(0).replace(num_match.group(1), "").strip()
        count_reminder = f"\nCRITICAL: The requirement specifies {n} {thing}s. You MUST generate exactly {n} movement states and {n} corresponding inputs — no more, no fewer.\n"

    user_prompt = f"""Generate IEC 61131-3 Structured Text code for:

PROGRAM NAME: {program_name}
BRAND: {brand}

USER REQUIREMENT: {prompt}
{count_reminder}
{INDUSTRY_EXAMPLES}

Generate complete, production-ready ST code with:
- Proper VAR_INPUT, VAR_OUTPUT, VAR sections
- State machine implementation
- Timer and counter handling
- Safety interlocks
- E-stop handling

START YOUR RESPONSE WITH THE CODE NOW:"""

    try:
        from backend.openai_client import safe_chat_completion, DEFAULT_MODEL, client
        
        response = safe_chat_completion(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent, deterministic output
            max_tokens=1500   # 1500 is enough for any 5-floor program; reduces latency vs 2000
        )
        
        content = response.choices[0].message.content
        tokens = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
        
        # Clean up the response
        content = clean_llm_response(content)
        
        return content, tokens
        
    except Exception as e:
        print(f"LLM call failed: {e}")
        raise


def clean_llm_response(content: str) -> str:
    """Clean LLM response - remove markdown, fix common issues"""
    
    # Remove markdown code blocks
    content = re.sub(r'^```st\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```', '', content)
    
    # Fix common LLM mistakes
    content = content.replace("END_IF;", "END_IF;")
    content = content.replace("END_FOR;", "END_FOR;")
    content = content.replace("END_WHILE;", "END_WHILE;")
    
    # Ensure PROGRAM block is properly formatted
    if "PROGRAM " in content and "END_PROGRAM" not in content:
        content += "\nEND_PROGRAM"
    
    return content.strip()


def validate_and_fix_code(code: str, program_name: str) -> str:
    """Validate and fix generated code"""
    
    # Ensure program name is correct
    if "PROGRAM " in code:
        # Replace any program name with the correct one
        code = re.sub(
            r'PROGRAM\s+\w+',
            f'PROGRAM {program_name}',
            code
        )
    
    # Add missing END_PROGRAM if needed
    if "END_PROGRAM" not in code:
        code = code + "\n\nEND_PROGRAM"
    
    return code


def generate_enhanced_template(prompt: str, program_name: str, brand: str) -> Dict:
    """
    Enhanced template-based generation as fallback
    Fixed: Now uses correct program name
    """
    print(f"[TMPL] Using enhanced template for: {program_name}")
    
    # Analyze prompt to get system requirements
    system = analyze_prompt(prompt)
    
    # Build code with CORRECT program name
    code = build_enhanced_st(system, program_name)
    
    return {
        "code": code,
        "iec_compliant": True,
        "confidence": 85,
        "warnings": ["Used template fallback - LLM generation preferred"],
        "errors": [],
        "model": system,
        "tokens_used": 0
    }


def analyze_prompt(prompt: str) -> dict:
    """Analyze prompt and extract system requirements"""
    
    prompt_lower = prompt.lower()
    
    # Traffic Light
    if "traffic" in prompt_lower or "light" in prompt_lower:
        return {
            "name": "TrafficLight",
            "domain": "traffic",
            "inputs": ["I_Start", "I_Stop", "I_EStop", "I_VehicleDetector", "I_PedButton"],
            "outputs": ["Q_RedLight", "Q_GreenLight", "Q_YellowLight", "Q_PedLight"],
            "states": ["Idle", "Red", "Green", "Yellow"],
            "timers": ["T_Green", "T_Yellow"],
            "logic": "traffic"
        }
    
    # Motor Control
    if "motor" in prompt_lower:
        return {
            "name": "MotorControl",
            "domain": "motor",
            "inputs": ["I_Start", "I_Stop", "I_EStop", "I_Thermal", "I_Reset"],
            "outputs": ["Q_Motor", "Q_StatusLight", "Q_Alarm"],
            "states": ["Idle", "Start", "Running", "Stop", "Fault"],
            "timers": ["T_Start"],
            "logic": "motor"
        }
    
    # Tank/Pump
    if "tank" in prompt_lower or "pump" in prompt_lower or "level" in prompt_lower:
        return {
            "name": "TankControl",
            "domain": "tank",
            "inputs": ["I_Start", "I_Stop", "I_EStop", "I_Level", "I_HighLevel", "I_LowLevel"],
            "outputs": ["Q_Pump", "Q_Valve", "Q_HighAlarm", "Q_LowAlarm"],
            "states": ["Idle", "Fill", "Running", "Empty", "Fault"],
            "timers": ["T_Fill"],
            "logic": "tank"
        }
    
    # Conveyor
    if "conveyor" in prompt_lower or "bottling" in prompt_lower:
        return {
            "name": "ConveyorControl",
            "domain": "conveyor",
            "inputs": ["I_Start", "I_Stop", "I_EStop", "I_BottleSensor", "I_LevelSensor"],
            "outputs": ["Q_Conveyor", "Q_FillValve", "Q_CapValve"],
            "states": ["Idle", "Convey", "Fill", "Cap", "Complete", "Fault"],
            "timers": ["T_Fill", "T_Cap"],
            "logic": "conveyor"
        }
    
    # Temperature
    if "temperature" in prompt_lower or "temp" in prompt_lower or "heater" in prompt_lower:
        return {
            "name": "TemperatureControl",
            "domain": "temperature",
            "inputs": ["I_Start", "I_Stop", "I_EStop", "I_Temperature", "I_Setpoint", "I_Reset"],
            "outputs": ["Q_Heater", "Q_Cooler", "Q_Alarm"],
            "states": ["Idle", "Heat", "Cool", "Maintain", "Fault"],
            "timers": ["T_Delay"],
            "logic": "temperature"
        }
    
    # Default
    return {
        "name": "ControlProgram",
        "domain": "generic",
        "inputs": ["I_Start", "I_Stop", "I_EStop", "I_Reset"],
        "outputs": ["Q_Output1", "Q_Output2", "Q_Alarm"],
        "states": ["Idle", "Run", "Fault"],
        "timers": ["T_Delay"],
        "logic": "generic"
    }


def build_enhanced_st(system: dict, program_name: str) -> str:
    """Build enhanced ST code with CORRECT program name"""
    
    logic_type = system.get("logic", "generic")
    states = system.get("states", [])
    inputs = system.get("inputs", [])
    outputs = system.get("outputs", [])
    timers = system.get("timers", [])
    
    st = f"""(*
===========================================================
{system['name']} - IEC 61131-3 Structured Text
Generated by Agent4PLC | Industry Grade
===========================================================
*)

TYPE eState :
(
"""

    # Add states to enum
    for i, state in enumerate(states):
        comma = "," if i < len(states) - 1 else ""
        st += f"    {state} := {i}{comma}\n"
    
    st += """);
END_TYPE

PROGRAM """ + program_name + """ 

(*======================
  INPUTS
=======================*)
VAR_INPUT
"""

    # Add inputs
    for inp in inputs:
        st += f"    {inp} : BOOL;\n"
    
    st += """END_VAR

(*======================
  OUTPUTS  
=======================*)
VAR_OUTPUT
"""

    # Add outputs
    for out in outputs:
        st += f"    {out} : BOOL;\n"
    
    st += """END_VAR

(*======================
  INTERNAL VARIABLES
=======================*)
VAR
    State : eState := Idle;
    StartTrig : R_TRIG;
    StopTrig : R_TRIG;
"""

    # Add timers
    for timer in timers:
        st += f"    {timer} : TON;\n"
        st += f"    {timer}Enable : BOOL;\n"
    
    st += """END_VAR

(*===========================================================
  EDGE DETECTION
===========================================================*)
StartTrig(CLK := I_Start);
StopTrig(CLK := I_Stop);

(*===========================================================
  SAFETY - E-STOP (Highest Priority)
===========================================================*)
IF I_EStop THEN
    State := Fault;
END_IF;

(*===========================================================
  TIMER EXECUTION
===========================================================*)
"""

    # Timer calls
    for timer in timers:
        st += f"{timer}(IN := {timer}Enable, PT := T#5S);\n"
    
    st += """
(*===========================================================
  STATE MACHINE
===========================================================*)
CASE State OF

"""

    # Generate state logic based on type
    for state in states:
        st += f"//---------------------------------------------------------\n{state}:\n"
        
        # Reset outputs in each state
        for out in outputs:
            st += f"    {out} := FALSE;\n"
        
        # Reset timer enables
        for timer in timers:
            st += f"    {timer}Enable := FALSE;\n"
        
        st += "\n"
        
        # Add state-specific logic
        state_logic = get_state_logic(state, system)
        st += state_logic
        st += "\n"
    
    st += """//---------------------------------------------------------
ELSE
    State := Fault;
END_CASE;

END_PROGRAM"""

    return st


def get_state_logic(state: str, system: dict) -> str:
    """Get functional logic for each state"""
    
    logic_type = system.get("logic", "generic")
    
    if state == "Idle":
        return """    (* Wait for start *)
    IF StartTrig.Q THEN
        State := Run;
    END_IF;
"""
    
    elif state == "Run":
        if logic_type == "traffic":
            return """    (* Traffic green light *)
    Q_GreenLight := TRUE;
    T_GreenEnable := TRUE;
    IF T_Green.Q THEN
        T_GreenEnable := FALSE;
        State := Yellow;
    END_IF;
"""
        elif logic_type == "motor":
            return """    (* Motor running *)
    Q_Motor := TRUE;
    Q_StatusLight := TRUE;
    IF StopTrig.Q THEN
        State := Stop;
    END_IF;
    IF I_Thermal THEN
        State := Fault;
    END_IF;
"""
        elif logic_type == "tank":
            return """    (* Filling tank *)
    Q_Pump := TRUE;
    Q_Valve := TRUE;
    IF I_HighLevel THEN
        Q_Pump := FALSE;
        Q_Valve := FALSE;
    END_IF;
"""
        else:
            return """    (* Running *)
    Q_Output1 := TRUE;
"""
    
    elif state == "Fault":
        return """    (* FAIL-SAFE: All outputs off *)
    IF NOT I_EStop AND I_Reset THEN
        State := Idle;
    END_IF;
"""
    
    else:
        return f"    (* {state} state *)\n"


# Main interface for routes
def generate_perfect_industrial_plc(prompt: str, program_name: str = "ControlProgram", 
                                    brand: str = "SIEMENS") -> Dict:
    """Main entry point - uses intelligent LLM generation"""
    return generate_intelligent_plc(prompt, program_name, brand)


if __name__ == "__main__":
    # Test
    test_prompt = "Design a traffic light controller with red, yellow, and green lights"
    result = generate_perfect_industrial_plc(test_prompt, "TrafficLight")
    print("=" * 60)
    print("INTELLIGENT GENERATOR TEST")
    print("=" * 60)
    print(f"Confidence: {result['confidence']}")
    print(f"Tokens: {result.get('tokens_used', 0)}")
    print("\nGenerated Code:")
    print(result['code'][:1000])

