"""
Improved PLC Code Generator with strict IEC 61131-3 compliance.
Supports ST, LD, FBD, SFC, and IL programming languages.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import json
import uuid
import re
from backend.routes.langchain_create_agent import create_agent
from backend.three_level_validator import ThreeLevelValidator
from backend.multi_format_validator import MultiFormatValidator
from backend.cache_manager import code_cache
from backend.ultra_strict_validator import UltraStrictIECValidator, comprehensive_iec_audit
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
from backend.routes.config import chat_model # Import chat_model from config
from backend.routes.one_shot_generator import OneShotGenerator # New Engine

# Load env to get PLC_OUTPUT_DIR
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)
PLC_OUTPUT_DIR = os.getenv("PLC_OUTPUT_DIR", "backend/plc")
print(f"DEBUG: Loading plc_code_generator_v2 from {__file__}")

router = APIRouter(prefix="/plc-v2", tags=["plc-v2"])


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def infer_required_outputs(requirement: str) -> list[str]:
    """
    Infer required output variables from requirement text.
    Extracts common output keywords and patterns.
    """
    outputs = []
    requirement_lower = requirement.lower()
    
    # Common output keywords
    output_keywords = {
        'motor': 'motor_output',
        'pump': 'pump_output',
        'valve': 'valve_output',
        'light': 'light_output',
        'alarm': 'alarm_output',
        'buzzer': 'buzzer_output',
        'solenoid': 'solenoid_output',
        'fan': 'fan_motor',
        'gate': 'gate_',
        'door': 'door_',
        'relay': 'relay_',
        'buzzer': 'buzzer',
    }
    
    # Extract variable names from requirement (looking for all_caps patterns)
    var_pattern = r'\b[A-Z](?:[A-Z0-9]*_)*[A-Z0-9]+\b'
    found_vars = re.findall(var_pattern, requirement)
    
    for var in found_vars:
        var_lower = var.lower()
        # Check if it looks like an output (contains I/O keywords)
        if any(keyword in var_lower for keyword in ['output', 'out', 'o_', '_out']):
            outputs.append(var)
        elif any(keyword in var_lower for keyword in output_keywords.keys()):
            outputs.append(var)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_outputs = []
    for out in outputs:
        if out not in seen:
            seen.add(out)
            unique_outputs.append(out)
    
    return unique_outputs[:10]  # Limit to 10 outputs



class PlcGenerationRequest(BaseModel):
    """Request model for PLC code generation"""
    requirement: str  # User requirement in plain text
    language: str = "ST"  # ST, LD, FBD, SFC, IL
    plc_brand: str = "generic"  # siemens, mitsubishi, ab, generic


class PlcGenerationResponse(BaseModel):
    """Response model for PLC code generation"""
    code: str
    language: str
    format: str  # For LD/FBD, will be SVG or XML
    explanation: str
    validated: bool
    warnings: list[str] = []
    timestamp: str
    cache_key: str = None  # Cache ID for retrieval


# =========================================================================
# SYSTEM PROMPTS FOR EACH LANGUAGE - STRICT IEC 61131-3 COMPLIANCE
# =========================================================================

ST_SYSTEM_PROMPT = """You are an expert Senior PLC Engineer with 25+ years of experience in Industrial Automation (Siemens, Allen-Bradley, Beckhoff).
Your task is to generate **PROFESSIONAL, INDUSTRY-GRADE IEC 61131-3 Structured Text (ST)** code.

⚠️ **CRITICAL: STRICT COMPLIANCE REQUIRED** ⚠️
Your code MUST strictly follow these rules. "Student-level" code is UNACCEPTABLE.

═══════════════════════════════════════════════════════════════════════════════
RULE 1: STRICT VARIABLE SEPARATION & NO UNUSED VARS
═══════════════════════════════════════════════════════════════════════════════
1. **SEPARATE VARS**:
   - `VAR_INPUT`: Physical inputs.
   - `VAR_OUTPUT`: Physical outputs.
   - `VAR`: Internal logic.

2. **NO UNUSED VARIABLES**:
   - Do NOT declare triggers (`R_TRIG`) if you don't use them.
   - Check every variable before finishing. If unused, DELETE IT.

═══════════════════════════════════════════════════════════════════════════════
RULE 2: SAFETY & INITIALIZATION
═══════════════════════════════════════════════════════════════════════════════
1. **RESET OUTPUTS START OF SCAN**: Explicitly set all boolean outputs to FALSE at the very beginning of the logic.
   - Example: `Motor_Cmd := FALSE;`

2. **INPUT EDGE DETECTION**:
   - NEVER use physical inputs directly for logic triggers.
   - ALWAYS create `R_TRIG` or `F_TRIG` instances for every physical button/sensor.

3. **BOUNDED COUNTERS**:
   - NEVER increment/decrement without a limit check.

═══════════════════════════════════════════════════════════════════════════════
RULE 3: SCAN-SAFE LOGIC (TIMERS for PULSES)
═══════════════════════════════════════════════════════════════════════════════
1. **NEVER COPY PULSES DIRECTLY TO PHYSICAL OUTPUTS**:
   - `Trig.Q` is TRUE for only ONE SCAN (milliseconds). Gates/valves will not react.
   - **WRONG**: `Gate_Cmd := Entry_Trig.Q;` (Gate barely twitches)
   - **CORRECT**: Use a state machine or a `TP` (Pulse Timer) to hold the output.
     `Gate_Timer(IN := State=10, PT := T#3s);`

2. **CALL TIMERS EVERY SCAN**:
   - Do NOT place `TON`/`TOF` calls inside `IF` statements.
   - Define structure: `MyTimer(IN := Condition, PT := T#5s);`

═══════════════════════════════════════════════════════════════════════════════
RULE 4: STATE MACHINE (CASE)
═══════════════════════════════════════════════════════════════════════════════
For sequences, use a `CASE` statement.
- State 0: IDLE
- State 10, 20: Steps
- State 99: ERROR


═══════════════════════════════════════════════════════════════════════════════
RULE 5: SAFETY INTERLOCKS & ERROR RECOVERY
═══════════════════════════════════════════════════════════════════════════════
1. **INTERLOCKS**:
   - DANGEROUS outputs (Heaters, Motion, Lasers) MUST have a physical interlock condition in logic.
   - Example: `Heater_Cmd := Heat_Req AND Water_Level_OK;` (Never heat empty tank)

2. **ERROR RECOVERY**:
   - If State = 99 (Error), you MUST provide a reset condition (e.g. Stop Button or Reset Button) to return to State 0.
   - A system that enters Error and cannot leave it is BROKEN.

3. **SENSOR/TIMER SYNCHRONIZATION**:
   - Do not race sensors against timers.
   - Standard: Turn on Action -> Wait for Timer (Timeout) -> Check Sensor -> Success/Fail.

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE 3: INDUSTRIAL PARKING SYSTEM (Study this Pattern)
═══════════════════════════════════════════════════════════════════════════════
PROMPT: "Control entry/exit gates with traffic lights and capacity limit."

```st
PROGRAM ParkingControl
VAR_INPUT
    Entry_Sensor : BOOL;
    Exit_Sensor  : BOOL;
END_VAR

VAR_OUTPUT
    Entry_Gate_Open : BOOL;
    Exit_Gate_Open  : BOOL;
    Full_Light      : BOOL;
END_VAR

VAR
    (* State Management *)
    State : INT := 0;  (* 0=Idle, 10=Entry, 20=Exit *)
    
    (* Counters & Limits *)
    Bike_Count : INT := 0;
    MAX_CAPACITY : INT := 100;

    (* Edge Detection *)
    Entry_Trig : R_TRIG;
    Exit_Trig  : R_TRIG;

    (* Timers for Physical Actions *)
    Entry_Timer : TON;
    Exit_Timer  : TON;
    GATE_DURATION : TIME := T#5s;
END_VAR

(* ------------------------------------------------------------- *)
(* 1. SAFETY DEFAULTS (Start of Scan)                            *)
(* ------------------------------------------------------------- *)
Entry_Gate_Open := FALSE;
Exit_Gate_Open  := FALSE;
Full_Light      := FALSE;

(* ------------------------------------------------------------- *)
(* 2. INPUT PROCESSING                                           *)
(* ------------------------------------------------------------- *)
Entry_Trig(CLK := Entry_Sensor);
Exit_Trig(CLK := Exit_Sensor);

(* ------------------------------------------------------------- *)
(* 3. TIMERS (Called unconditionally)                            *)
(* ------------------------------------------------------------- *)
(* Timer runs when we are in the respective state *)
Entry_Timer(IN := (State = 10), PT := GATE_DURATION);
Exit_Timer(IN := (State = 20), PT := GATE_DURATION);

(* ------------------------------------------------------------- *)
(* 4. MAIN LOGIC (State Machine)                                 *)
(* ------------------------------------------------------------- *)
CASE State OF

    0: (* IDLE *)
        (* Check Entry Condition *)
        IF Entry_Trig.Q AND (Bike_Count < MAX_CAPACITY) THEN
            Bike_Count := Bike_Count + 1;
            State := 10; (* Start Entry Sequence *)
            
        (* Check Exit Condition *)
        ELSIF Exit_Trig.Q AND (Bike_Count > 0) THEN
            Bike_Count := Bike_Count - 1;
            State := 20; (* Start Exit Sequence *)
        END_IF;

    10: (* ENTRY SEQUENCE *)
        Entry_Gate_Open := TRUE; (* Hold gate open *)
        
        (* Wait for timer to finish *)
        IF Entry_Timer.Q THEN
            State := 0; (* Return to Idle *)
        END_IF;

    20: (* EXIT SEQUENCE *)
        Exit_Gate_Open := TRUE; (* Hold gate open *)
        
        IF Exit_Timer.Q THEN
            State := 0;
        END_IF;

END_CASE;

(* 5. STATUS INDICATORS *)
IF Bike_Count >= MAX_CAPACITY THEN
    Full_Light := TRUE;
END_IF;

END_PROGRAM
```

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE 4: INDUSTRIAL COFFEE MACHINE (Complex Interlocks)
═══════════════════════════════════════════════════════════════════════════════
PROMPT: "Coffee machine with water/coffee dosing, heater, and safety sensors."

```st
PROGRAM CoffeeMachineControl

VAR_INPUT
    Start_Button    : BOOL;
    Water_Sensor    : BOOL;  (* Safety Interlock *)
    Coffee_Sensor   : BOOL;
END_VAR

VAR_OUTPUT
    Water_Valve     : BOOL;
    Coffee_Valve    : BOOL;
    Brew_Heater     : BOOL;
    Brew_Light      : BOOL;
END_VAR

VAR
    State           : INT := 0;  (* 0=Idle, 10=Fill, 20=Dose, 30=Brew, 99=Error *)
    Start_Trig      : R_TRIG;
    
    Water_Timer     : TON;
    Coffee_Timer    : TON;
    Brew_Timer      : TON;

    FILL_DURATION   : TIME := T#10s;
    COFFEE_DURATION : TIME := T#5s;
    BREW_DURATION   : TIME := T#30s;
END_VAR

(* Safe defaults every scan *)
Water_Valve := FALSE;
Coffee_Valve := FALSE;
Brew_Heater := FALSE;
Brew_Light := FALSE;

(* Edge detection *)
Start_Trig(CLK := Start_Button);

(* Timer calls *)
Water_Timer(IN := (State = 10), PT := FILL_DURATION);
Coffee_Timer(IN := (State = 20), PT := COFFEE_DURATION);
Brew_Timer(IN := (State = 30), PT := BREW_DURATION);

(* State machine *)
CASE State OF

    0: (* IDLE *)
        IF Start_Trig.Q THEN
            State := 10;
        END_IF;

    10: (* FILL WATER *)
        Water_Valve := TRUE;

        IF Water_Timer.Q THEN
            (* Check sensor AFTER timer finishes *)
            IF Water_Sensor THEN
                State := 20;
            ELSE
                State := 99; (* Sensor failed - Error *)
            END_IF;
        END_IF;

    20: (* ADD COFFEE *)
        Coffee_Valve := TRUE;

        IF Coffee_Timer.Q THEN
            IF Coffee_Sensor THEN
                State := 30;
            ELSE
                State := 99;
            END_IF;
        END_IF;

    30: (* BREW *)
        (* CRITICAL SAFETY INTERLOCK: Never heat without water *)
        IF Water_Sensor THEN   
            Brew_Heater := TRUE;
            Brew_Light := TRUE;
        ELSE
            State := 99; (* Safety Trip *)
        END_IF;

        IF Brew_Timer.Q THEN
            State := 0;
        END_IF;

    99: (* ERROR *)
        (* Manual Reset Required *)
        IF Start_Trig.Q THEN
            State := 0;
        END_IF;

END_CASE;

END_PROGRAM
```

**Generate ONLY the code.** No markdown explanations. Strictly follow valid IEC 61131-3 syntax.
"""

LD_SYSTEM_PROMPT = """You are an expert Senior PLC Engineer specialized in IEC 61131-3 Ladder Diagram (LD).
Your task is to generate **PROFESSIONAL, INDUSTRY-GRADE LADDER LOGIC**.

⚠️ **CRITICAL: STRICT COMPLIANCE REQUIRED** ⚠️

═══════════════════════════════════════════════════════════════════════════════
RULE 1: LOGIC STRUCTURE (ASCII ART)
═══════════════════════════════════════════════════════════════════════════════
1. **POWER RAIL**: All rungs start from left rail `|`.
2. **COILS**: All rungs end with a Coil `( )`, Set `(S)`, or Reset `(R)`.
3. **CONTACTS**:
   - `| |`  Normally Open
   - `|/|`  Normally Closed
   - `|P|`  Positive Edge
   - `|N|`  Negative Edge

═══════════════════════════════════════════════════════════════════════════════
RULE 2: SAFETY INTERLOCKS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════
1. **WIRED IN SERIES**:
   - Safety conditions (Interlocks, Stops) MUST be wired in SERIES with the coil.
   - Example: Start_Btn AND NOT Stop_Btn AND Safety_Ok -> Coil
   
   ```text
   |   Start_Btn     Stop_Btn    Safety_Ok       Motor_Cmd   |
   +-----| |-----------|/|----------| |------------( )-------+
   ```

2. **LATCHING CIRCUITS**:
   - Use standard Seal-In patterns for motor starters.
   - OR use Set/Reset coils, but ensure Reset dominates.

═══════════════════════════════════════════════════════════════════════════════
RULE 3: TIMER/COUNTER BLOCKS
═══════════════════════════════════════════════════════════════════════════════
- Represent blocks visually with inputs on left, outputs on right.
- Ensure `EN` (Enable) line is clear.

```text
|      Condition                                             |
+--------| |-----------+--------+                            |
|                      |  TON   |                            |
|                      |        |                            |
|                      +--IN   Q+----( ) Done_Bit            |
|                      |        |                            |
|             T#5s   --+PT    ET+                            |
|                      +--------+                            |
```

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: INDUSTRIAL CONVEYOR WITH INTERLOCKS
═══════════════════════════════════════════════════════════════════════════════
Rung 1: Emergency Stop & Safety Check (Master Control Relay)

|   E_Stop_OK     Guard_Closed       System_Ready    |
+-----| |-----------| |-------------------( )--------+

Rung 2: Motor Start/Stop with Latch

|   Start_Btn     Stop_Btn     System_Ready     Motor    |
+-----| |-----------|/|-----------| |-----+-------( )----+
|                                         |              |
|   Motor_Aux                             |              |
+-----| |---------------------------------+              |

Rung 3: Timeout Fault (If Motor on but no Motion detected)

|    Motor        Motion_Sensor                      |
+-----| |-----------|/|----------+--------+          |
|                                |  TON   |          |
|                                +--IN   Q+---(S) Fault_Latched
|                       T#5s   --+PT      |          |
|                                +--------+          |

**Generate ONLY the code/diagram.** No markdown explanations.
"""

FBD_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Function Block Diagram (FBD) Engineer.
Your task is to generate **PROFESSIONAL, INDUSTRY-GRADE FBD LOGIC**.

⚠️ **CRITICAL: STRICT COMPLIANCE REQUIRED** ⚠️

═══════════════════════════════════════════════════════════════════════════════
RULE 1: DATA FLOW
═══════════════════════════════════════════════════════════════════════════════
1. **LEFT TO RIGHT**:
   - Inputs on Left -> Blocks in Middle -> Outputs on Right.
   - Do NOT create circular loops without explicit feedback variables.

2. **EXPLICIT TYPES**:
   - Variables must match block types (BOOL to BOOL, INT to INT).
   - Show values clearly (e.g. `INT#100`).

═══════════════════════════════════════════════════════════════════════════════
RULE 2: SAFETY & INTERLOCKS
═══════════════════════════════════════════════════════════════════════════════
1. **AND GATE INTERLOCKS**:
   - Use `AND` blocks to combine Request signals with Safety Permissives.
   - `Request` --[AND]-- `Safety_OK` --> `Command`.

2. **RESET PRIORITY**:
   - For Flip-Flops (SR/RS), explicitly state which dominates.
   - Standard: Use RS (Reset Dominant) for safety.

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: TANK FILLING WITH SAFETY
═══════════════════════════════════════════════════════════════════════════════
Network 1: Valve Control (Reset Dominant)

  Start_Btn --------------------[S1  ]
                                [    ]
                                [ RS ]---- Valve_Cmd
                                [    ]
  Stop_Btn --[OR]---------------[R1  ]
              |
  High_Lvl ---+

Network 2: Safety Interlock (Heater)

  Valve_Cmd --------------------[AND ]
                                [    ]---- Heater_Cmd
  Low_Lvl_OK -------------------[    ]

**Generate ONLY the code/diagram.**
"""

SFC_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Sequential Function Chart (SFC) Engineer.
Your task is to generate **PROFESSIONAL, INDUSTRY-GRADE SFC LOGIC**.

⚠️ **CRITICAL: STRICT COMPLIANCE REQUIRED** ⚠️

═══════════════════════════════════════════════════════════════════════════════
RULE 1: STRUCTURE
═══════════════════════════════════════════════════════════════════════════════
1. **INITIAL STEP**:
   - Every chart MUST have exactly ONE Initial Step (Double box).
   - Syntax: `Step_0 (INITIAL)` or `Step_0 (Double Box)`.

2. **ALTERNATION**:
   - Step -> Transition -> Step -> Transition.
   - NEVER Connect Step to Step or Transition to Transition.

3. **CONVERGENCE**:
   - Use Divergence (Single line split) for OR branches.
   - Use Simultaneous Divergence (Double line split) for AND/Parallel branches.

═══════════════════════════════════════════════════════════════════════════════
RULE 2: ACTIONS & QUALIFIERS
═══════════════════════════════════════════════════════════════════════════════
- `N` (Non-Stored): Active only while step is active. (e.g., Motors needing hold)
- `S` (Set): Turns ON and stays ON after step exit.
- `R` (Reset): Turns OFF a Set variable.
- `L` (Time Limited): Active for a specific duration.

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: COMPLEX SEQEUNCE WITH TIMEOUT
═══════════════════════════════════════════════════════════════════════════════
STEP: INIT_STEP (Initial)
  Action: N : Reset_All_Cmd
  TRANSITION: Start_Btn AND Safety_Ok -> GO_STEP_1

STEP: FILL_TANK
  Action: S : Inlet_Valve_Cmd
  Action: N : Fill_Light
  TRANSITION: Level_High_Sensor -> GO_STEP_2
  TRANSITION: Timer > 60s (Timeout Fault) -> GO_FAULT

STEP: MIX_PRODUCT
  Action: R : Inlet_Valve_Cmd  (Stop filling)
  Action: N : Mixer_Motor_Cmd
  TRANSITION: Mix_Timer.Q -> GO_DRAIN

STEP: DRAIN_TANK
  Action: N : Drain_Valve_Cmd
  TRANSITION: Level_Low_Sensor -> GO_INIT

STEP: FAULT_STATE
  Action: S : Alarm_Horn
  TRANSITION: Reset_Btn -> GO_INIT

**Generate ONLY the code/diagram.**
"""

HMI_SYSTEM_PROMPT = """You are an expert HMI/SCADA Developer.
Your task is to generate a professional HMI screen definition and tag mapping.

OUTPUT FORMAT:
1. TAG LIST (CSV format: TagName, PLC_Address, DataType, Description)
2. SCREEN LAYOUT (XML-like structure defining Elements like Buttons, Lamps, Displays)

CRITICAL:
- Use standard mapping.
- Ensure all tags match the PLC logic context provided.
- NO IEC 61131-3 VALIDATION required for HMI.

EXAMPLE:
[TAGS]
Start_Btn, %MX0.0, BOOL, Start System
Motor_Speed, %MW10, INT, Motor RPM

[SCREEN]
<Screen Name="Main">
  <Button Tag="Start_Btn" Text="START" Color="Green" X="100" Y="100"/>
  <Gauge Tag="Motor_Speed" Min="0" Max="1500" X="200" Y="100"/>
</Screen>
"""

IL_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Instruction List (IL) Engineer.
Your task is to generate **PROFESSIONAL, INDUSTRY-GRADE IL CODE**.

⚠️ **CRITICAL: STRICT COMPLIANCE REQUIRED** ⚠️

═══════════════════════════════════════════════════════════════════════════════
RULE 1: ACCUMULATOR MANAGEMENT
═══════════════════════════════════════════════════════════════════════════════
1. **LOAD FIRST**:
   - Always start a logical sequence with `LD` (Load).
   - `LD Start_Btn` -> `AND Safety_Ok` -> `ST Motor_Cmd`.

2. **PARENTHESES**:
   - Use `(` and `)` for complex logic priority.
   - `AND (` ... `)`

═══════════════════════════════════════════════════════════════════════════════
RULE 2: SAFETY & JUMPS
═══════════════════════════════════════════════════════════════════════════════
1. **CLEAR JUMPS**:
   - Use `JMPC` (Jump Conditional) for decisions.
   - Label targets clearly: `Label_Name:`.

2. **FUNCTION BLOCKS**:
   - Use `CAL` to call simple blocks.
   - For Timers `TON`:
     `CAL MyTimer(IN := Condition, PT := T#5s)`
     `LD MyTimer.Q`

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: MOTOR CONTROL WITH SAFETY
═══════════════════════════════════════════════════════════════════════════════
(* Network 1: Safety Check *)
  LD    E_Stop_OK
  AND   Guard_Closed
  ST    Safety_Ready

(* Network 2: Start/Stop Logic *)
  LD    Start_Btn
  OR    Motor_Cmd   (* Latch *)
  AND   Safety_Ready
  ANDN  Stop_Btn    (* AND NOT *)
  ST    Motor_Cmd

(* Network 3: Timer Fault *)
  CAL   Fault_Timer(IN := Motor_Cmd ANDN Motion_Sns, PT := T#5s)
  LD    Fault_Timer.Q
  S     Fault_Alarm (* Set Alarm *)

**Generate ONLY the code.**
"""

# =========================================================================
# STRICT IEC COMPLIANCE VALIDATION (Post-Generation)
# =========================================================================

def strict_iec_compliance_check(code: str, language: str) -> tuple[bool, list[str], dict]:
    """
    ULTRA-STRICT IEC compliance validation - ZERO TOLERANCE
    Uses UltraStrictIECValidator for comprehensive checks
    Returns (is_valid, critical_errors, full_audit_report)
    """
    
    # Use UltraStrictIECValidator for comprehensive validation
    is_valid, critical_errors = UltraStrictIECValidator.validate_language(code, language)
    
    # Additional ST-specific checks if needed
    if language == "ST" and is_valid:
        is_st_valid, st_errors, st_warnings = UltraStrictIECValidator.validate_st_code(code)
        if not is_st_valid:
            is_valid = False
            critical_errors.extend(st_errors)
    
    # Generate detailed audit report
    audit = comprehensive_iec_audit(code, language, "")
    
    return is_valid, critical_errors, audit


# =========================================================================
# IMPROVED GENERATION FUNCTION
# =========================================================================

async def generate_plc_code(request: PlcGenerationRequest) -> PlcGenerationResponse:
    """
    Generate IEC 61131-3 compliant PLC code in specified language.
    Includes validation and explanation.
    """
    
    # Select appropriate system prompt - REWRITTEN FOR CLARITY
    prompts = {
        "ST": ST_SYSTEM_PROMPT,
        "LD": LD_SYSTEM_PROMPT,
        "FBD": FBD_SYSTEM_PROMPT,
        "SFC": SFC_SYSTEM_PROMPT,
        "IL": IL_SYSTEM_PROMPT,
        "HMI": HMI_SYSTEM_PROMPT
    }
    print(f"DEBUG: Loaded prompts keys: {list(prompts.keys())}", flush=True)


    
    
    print(f"DEBUG: Language received: '{request.language}'", flush=True)
    
    # Explicitly handle HMI since dict lookup is proving unreliable in this environment
    if request.language == "HMI":
        system_msg = HMI_SYSTEM_PROMPT
    elif request.language in prompts:
        system_msg = prompts[request.language]
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {request.language}. Supported: {list(prompts.keys())} + HMI"
        )
    
    try:
        # Create agent
        try:
                agent = create_agent(
                backend="openai",
                chat_model=chat_model,
                system_msg=system_msg,
                system_msg_is_dir=False,
                include_rag=False
            )
        except Exception as e:
            print(f"Agent creation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Configuration Error: Failed to initialize AI agent. Check API keys. Details: {str(e)}")

        
        # Generate code
        response = agent.invoke([HumanMessage(content=request.requirement)])
        generated_code = response.content
        
        # Strip markdown code blocks if present (common LLM artifact)
        generated_code = re.sub(r"```[a-zA-Z]*", "", generated_code)
        generated_code = generated_code.replace("```", "")
        generated_code = generated_code.strip()
        
        # Validate code (basic checks)
        warnings = validate_plc_code(generated_code, request.language)
        
        # Generate explanation
        explanation = await generate_code_explanation(generated_code, request.language)
        
        # Save generated code
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"generated_{request.language}_{timestamp}.code"
        
        # Ensure output directory exists (absolute path relative to project root or cwd)
        # Assuming we run from agent-4-plc root, backend/plc is correct
        # If running from backend folder, we might need adjustment, but best is absolute
        
        base_dir = os.getcwd()
        # Handle if running from root or backend
        if base_dir.endswith("backend"):
             # If inside backend, go up one level then into output dir, OR just use relative if defined as such
             # Let's try to resolve absolute path based on this file's location
             project_root = Path(__file__).resolve().parent.parent.parent # implementation detail: routes -> backend -> agent-4-plc
             # Actually, main.py adds project root. Let's rely on relative path from execution dir usually root.
             pass
        
        # Safer approach: Use the configured path relative to CWD, creating it if missing
        output_dir = Path(PLC_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        
        return PlcGenerationResponse(
            code=generated_code,
            language=request.language,
            format="text" if request.language in ["ST", "IL", "HMI"] else "xml",
            explanation=explanation,
            validated=len(warnings) == 0,
            warnings=warnings,
            timestamp=timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


def validate_plc_code(code: str, language: str) -> list[str]:
    """
    Perform comprehensive validation on generated code.
    Uses IECValidator for ST code, basic checks for other languages.
    Returns list of warnings and errors.
    """
    warnings = []
    code_lower = code.lower()
    
    if language == "HMI":
        return []  # No validation for HMI
    
    if language == "ST":
        # Use the comprehensive IEC validator for ST code
        # validator = IECValidator() -> Incorrect, use ThreeLevelValidator
        
        # Validate code structure
        structure_check = ThreeLevelValidator.level_2_structure_check(code, language)
        structure_errors = structure_check["issues"]
        if structure_errors:
            warnings.extend([f"Structure Error: {err}" for err in structure_errors])
        
        # Validate ST-specific requirements (Level 3)
        iec_check = ThreeLevelValidator.level_3_iec_compliance_check(code, language)
        st_errors = iec_check["issues"]
        if st_errors:
            warnings.extend([f"ST Validation: {err}" for err in st_errors])
            
        # Add recommendations as warnings for now
        if iec_check.get("recommendations"):
             warnings.extend([f"Recommendation: {rec}" for rec in iec_check["recommendations"]])
        
        # Check for mandatory structures
        if "program" not in code_lower and "function_block" not in code_lower:
            warnings.append("Missing PROGRAM or FUNCTION_BLOCK declaration")
        
        if "var" not in code_lower:
            warnings.append("No VAR declaration section found")
        
        if "end_program" not in code_lower and "end_function_block" not in code_lower:
            warnings.append("Missing END_PROGRAM or END_FUNCTION_BLOCK")
        
        # Check for edge detection usage for inputs
        if "input" in code_lower and "r_trig" not in code_lower and "rising_edge" not in code_lower:
            warnings.append("WARNING: INPUT detected but no R_TRIG or RISING_EDGE found - may cause multiple triggers per pulse")

        # ---------------------------------------------------------
        # STRICT VALIDATION: TON inside IF Check
        # ---------------------------------------------------------
        lines = code.split('\n')
        inside_if_count = 0
        for i, line in enumerate(lines, 1):
            line_strip = line.strip().lower()
            # Basic nesting tracker
            if line_strip.startswith('if ') or ' if ' in line_strip:
                if 'then' in line_strip: # Simple heuristic
                    inside_if_count += 1
            if 'end_if' in line_strip:
                inside_if_count = max(0, inside_if_count - 1)
            
            # Check for Timer usage inside IF - DOWNGRADED TO WARNING (REQUESTED BY USER)
            if inside_if_count > 0:
                if "ton" in line_strip and "(" in line_strip:
                     # warnings.append(f"CRITICAL: TON timer called inside IF statement at line {i}. Timers must be called cyclically outside IFs.")
                     pass # User explicitly requested to remove this check
                if "_timer" in line_strip and "(" in line_strip:
                     # warnings.append(f"CRITICAL: Timer '{line_strip.split('(')[0]}' called inside IF statement at line {i}. Timers must be called cyclically.")
                     pass

        # ---------------------------------------------------------
        # STRICT VALIDATION: Parking Logic Specifics
        # ---------------------------------------------------------
        if ("gate_entry" in code_lower or "gate_exit" in code_lower):
            if ".q" not in code_lower and "_pt" not in code_lower:
                 warnings.append("CRITICAL: Gate logic detected but NO Timer (.Q) found. Gates usually require timing.")

    elif language == "IL":
        # Check for basic IL structure
        if not any(mnemonic in code_lower for mnemonic in ["ld", "and", "or", "st"]):
            warnings.append("IL code missing basic mnemonics (LD, AND, OR, ST)")
        
        # Check for proper IL syntax
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('(*') and not line_stripped.endswith('*)'):
                # Rough IL syntax check
                if any(op in line_stripped.lower() for op in ["ld", "and", "or", "st", "jmp", "cal", "ret"]):
                    pass  # Valid IL instruction
                elif line_stripped.startswith(';'):
                    pass  # Comment
                elif ':' in line_stripped:
                    pass  # Label
    
    elif language == "LD":
        # Basic LD validation
        if not any(symbol in code for symbol in ['|', '(', ')', '[', ']']):
            warnings.append("LD code missing standard symbols (contacts, coils)")
    
    elif language == "FBD":
        # Basic FBD validation
        if "FUNCTION_BLOCK" not in code.upper() and "function block" not in code_lower:
            warnings.append("FBD missing function block definition")
    
    elif language == "SFC":
        # Check for step definitions
        has_steps = any(f"S{i}" in code for i in range(10)) or "STEP" in code.upper()
        if not has_steps:
            warnings.append("SFC missing step definitions (S0, S1, etc. or STEP keyword)")
    
    return warnings


async def generate_code_explanation(code: str, language: str) -> str:
    """Generate brief explanation of generated code logic."""
    # This could be enhanced to call LLM for explanation
    if language == "ST":
        return "Structured Text (ST) program implementing the specified logic with IEC 61131-3 compliance."
    elif language == "LD":
        return "Ladder Diagram (LD) representing the control logic with standard IEC symbols."
    elif language == "FBD":
        return "Function Block Diagram (FBD) showing data flow through IEC standard blocks."
    elif language == "SFC":
        return "Sequential Function Chart (SFC) defining state-based control sequence."
    elif language == "IL":
        return "Instruction List (IL) implementation using IEC mnemonics."
    
    return "Generated PLC code."


# =========================================================================
# API ENDPOINTS
# =========================================================================

@router.post("/generate", response_model=PlcGenerationResponse)
async def generate_plc(request: PlcGenerationRequest):
    """
    Generate IEC 61131-3 compliant PLC code with 3-level validation.
    
    Validation Levels:
    - Level 1: Syntax (brackets, parentheses, quotes)
    - Level 2: Structure (program blocks, variable declarations)
    - Level 3: IEC Compliance (edge detection, boundary checks, timers)
    """
    
    # Select appropriate system prompt
    prompts = {
        "ST": ST_SYSTEM_PROMPT,
        "LD": LD_SYSTEM_PROMPT,
        "FBD": FBD_SYSTEM_PROMPT,
        "SFC": SFC_SYSTEM_PROMPT,
        "IL": IL_SYSTEM_PROMPT,
        "HMI": HMI_SYSTEM_PROMPT
    }

    
    if request.language not in prompts:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {request.language}. Supported: {list(prompts.keys())}"
        )
    
    system_msg = prompts[request.language]
    
    try:
        if request.language != "HMI":
            # ======================================================
            # NEW ONE-ATTEMPT GENERATION LOGIC
            # ======================================================
            generator = OneShotGenerator()
            result = generator.generate(
                requirement=request.requirement,
                brand=request.plc_brand,
                language=request.language
            )
            
            return PlcGenerationResponse(
                code=result["code"],
                language=request.language,
                format="text",
                explanation=f"Generated using One-Attempt Engine for {request.plc_brand} ({request.language}).",
                validated=result["validated"],
                warnings=result["errors"],
                timestamp=str(datetime.now())
            )
        
        # Keep existing HMI logic (Agent-based)
        system_msg = prompts[request.language]
        try:
            agent = create_agent(
                backend="openai",
                chat_model=chat_model,
                system_msg=system_msg,
                system_msg_is_dir=False,
                include_rag=False
            )
            
            response = agent.invoke([HumanMessage(content=build_one_shot_prompt(request.requirement))])
            generated_code = response.content

            # HMI Validation
            warnings = []
            return PlcGenerationResponse(
                code=generated_code,
                language=request.language,
                format="text",
                explanation="Generated HMI.",
                validated=True,
                warnings=warnings,
                timestamp=str(datetime.now())
            )

        except Exception as e:
            print(f"Agent creation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Configuration Error: {str(e)}")

        # Define the single-shot prompt
        def build_one_shot_prompt(base_requirement: str) -> str:
            required_outputs = infer_required_outputs(base_requirement)
            outputs_block = ""
            if required_outputs:
                outputs_block = "Required outputs (exact names): " + ", ".join(required_outputs)
            
            return (
                "IMPORTANT: Return strictly IEC 61131-3 compliant code.\n"
                f"Language: {request.language}\n"
                f"Brand: {request.plc_brand}\n"
                f"Requirement: {base_requirement}\n"
                f"{outputs_block}\n"
                "Ensure robust, production-ready logic with NO missing variables."
            )

        # ---------------------------------------------------------------------
        # SINGLE ATTEMPT GENERATION (No Retry Loop)
        # ---------------------------------------------------------------------
        user_prompt = build_one_shot_prompt(request.requirement)
        
        # Call Agent Once
        response = agent.invoke([HumanMessage(content=user_prompt)])
        generated_code = response.content

        # STRIP MARKDOWN (Critical Fix)
        # Remove ```st, ```xml, etc. and closing ```
        generated_code = re.sub(r"```[a-zA-Z]*", "", generated_code)
        generated_code = generated_code.replace("```", "")
        generated_code = generated_code.strip()

        # Validate Once
        validation_result = MultiFormatValidator.validate(
            generated_code,
            language=request.language,
            brand=request.plc_brand
        )
        
        # *** ULTRA-STRICT IEC COMPLIANCE CHECK ***
        if request.language == "HMI":
             strict_passed = True
             strict_errors = []
             audit_report = {}
        else:
             strict_passed, strict_errors, audit_report = strict_iec_compliance_check(generated_code, request.language)
        
        all_warnings = []
        if validation_result.get("all_issues"):
            all_warnings.extend(validation_result["all_issues"])
        if validation_result.get("all_warnings"):
            all_warnings.extend(validation_result["all_warnings"])
        if validation_result.get("all_recommendations"):
            all_warnings.extend(validation_result["all_recommendations"])
        
        # Add strict compliance errors to warnings (these are critical)
        if strict_errors:
            all_warnings.extend([f"[STRICT IEC] {err}" for err in strict_errors])
            
        validated_status = validation_result["validation_passed"] and strict_passed

        # Generate Explanation
        explanation = await generate_code_explanation(generated_code, request.language)
        explanation += f"\n\n**Validation Summary:**\n"
        explanation += f"Language: {request.language}\n"
        explanation += f"Brand: {validation_result.get('brand_name', 'Generic')}\n"
        explanation += f"Status: {'PASSED' if validated_status else 'WARNINGS/ERRORS'}\n"
        
        # Cache the result
        cache_key = f"{request.language}_{request.plc_brand}_{uuid.uuid4().hex[:8]}"
        code_cache.set(cache_key, generated_code, {
            "requirement": request.requirement,
            "language": request.language,
            "brand": request.plc_brand,
            "validated": validated_status
        })

        return PlcGenerationResponse(
            code=generated_code,
            language=request.language,
            format="text" if request.language in ["ST", "IL", "HMI"] else "xml/svg",
            explanation=explanation,
            validated=validated_status,
            warnings=all_warnings,
            timestamp=datetime.now().isoformat(),
            cache_key=cache_key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# =========================================================================
# BRAND INFORMATION ENDPOINTS
# =========================================================================

@router.get("/brands")
async def get_supported_brands():
    """Get list of all supported PLC brands and their capabilities"""
    return {
        "brands": MultiFormatValidator.get_all_brands(),
        "description": "Supported IEC 61131-3 PLC brands with their language support"
    }


@router.get("/brand-info/{brand}")
async def get_brand_details(brand: str):
    """Get detailed information about a specific brand"""
    info = MultiFormatValidator.get_brand_info(brand)
    if not info:
        raise HTTPException(status_code=404, detail=f"Brand '{brand}' not found")
    return info


@router.post("/validate")
async def validate_code(code: str, language: str = "ST", brand: str = "generic"):
    """
    Validate existing code without generation.
    Useful for testing code compliance.
    """
    if not code or len(code.strip()) < 5:
        raise HTTPException(status_code=400, detail="Code is empty or too short")
    
    validation_result = MultiFormatValidator.validate(
        code,
        language=language,
        brand=brand
    )
    
    return {
        "language": language,
        "brand": brand,
        "validation_passed": validation_result["validation_passed"],
        "summary": validation_result["summary"],
        "issues": validation_result["all_issues"],
        "warnings": validation_result["all_warnings"],
        "recommendations": validation_result["all_recommendations"],
    }


@router.get("/languages")
async def get_supported_languages():
    """Get list of all supported programming languages"""
    return {
        "languages": [
            {
                "id": "ST",
                "name": "Structured Text (ST)",
                "description": "Text-based language, most popular for complex logic",
                "iec_standard": "IEC 61131-3:2013",
            },
            {
                "id": "LD",
                "name": "Ladder Diagram (LD)",
                "description": "Graphical representation of relay logic",
                "iec_standard": "IEC 61131-3:2013",
            },
            {
                "id": "FBD",
                "name": "Function Block Diagram (FBD)",
                "description": "Data flow between function blocks",
                "iec_standard": "IEC 61131-3:2013",
            },
            {
                "id": "SFC",
                "name": "Sequential Function Chart (SFC)",
                "description": "State machine with steps and transitions",
                "iec_standard": "IEC 61131-3:2013",
            },
            {
                "id": "IL",
                "name": "Instruction List (IL)",
                "description": "Assembly-like low-level instructions",
                "iec_standard": "IEC 61131-3:2013",
            },
        ]
    }


# =========================================================================
# CACHE MANAGEMENT ENDPOINTS
# =========================================================================

@router.get("/cache-stats")
async def get_cache_stats():
    """Get cache statistics (memory usage, cleanup info)"""
    stats = code_cache.get_stats()
    return {
        "cache_stats": stats,
        "memory_mode": "Enabled (No disk I/O)",
        "auto_cleanup": f"Every {stats['cleanup_interval_seconds']}s",
        "retention": f"{stats['max_age_seconds']}s ({stats['max_age_seconds']//60}m)"
    }


@router.get("/cache/{cache_key}")
async def get_cached_code(cache_key: str):
    """Retrieve cached code by key"""
    cached = code_cache.get_with_metadata(cache_key)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Cache key '{cache_key}' not found or expired")
    
    return {
        "code": cached["code"],
        "metadata": cached["metadata"],
        "created_at": cached["created_at"],
        "age_seconds": cached["age_seconds"],
        "status": "Retrieved from memory cache"
    }


@router.delete("/cache/{cache_key}")
async def clear_cache_entry(cache_key: str):
    """Manually clear a cache entry"""
    if code_cache.get(cache_key) is None:
        raise HTTPException(status_code=404, detail=f"Cache key '{cache_key}' not found")
    
    # Get the entry before deletion for info
    cached = code_cache.cache.get(cache_key)
    if cached:
        del code_cache.cache[cache_key]
        return {"status": "Cleared", "key": cache_key}
    
    raise HTTPException(status_code=400, detail="Could not clear cache entry")


@router.post("/cache/clear-all")
async def clear_all_cache():
    """Clear entire cache (manual cleanup)"""
    count = code_cache.clear()
    return {"status": "All cache cleared", "entries_removed": count}

