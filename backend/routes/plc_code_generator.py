"""
Improved PLC Code Generator with strict IEC 61131-3 compliance.
Supports ST, LD, FBD, SFC, and IL programming languages.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
from backend.routes.langchain_create_agent import create_agent
from backend.three_level_validator import ThreeLevelValidator
from backend.multi_format_validator import MultiFormatValidator
from backend.cache_manager import code_cache
from backend.cache_manager import code_cache
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

# Load env to get PLC_OUTPUT_DIR
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
PLC_OUTPUT_DIR = os.getenv("PLC_OUTPUT_DIR", "backend/plc")

router = APIRouter(prefix="/plc-v2", tags=["plc-v2"])


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

ST_SYSTEM_PROMPT = """You are an expert IEC 61131-3 PLC Structured Text (ST) developer with 20+ years experience in industrial automation.

⚠️ CRITICAL RULES - VIOLATIONS WILL CAUSE REJECTION ⚠️

1. **STRICT IEC 61131-3 SYNTAX**
   - Use ONLY IEC-standard keywords and syntax
   - No vendor-specific extensions or pragmas
   - Output MUST compile on any IEC-compliant platform (Codesys, Siemens, Schneider, Rockwell)

2. **PROGRAM STRUCTURE** (Mandatory)
   PROGRAM ProgramName
   VAR
       (* Variable declarations with explicit types *)
   END_VAR
   
   (* Main logic here *)
   
   END_PROGRAM

3. **VARIABLE DECLARATION**
   - ALL variables MUST have explicit IEC types: BOOL, INT, REAL, STRING, DINT, etc.
   - Use: VAR, VAR_INPUT, VAR_OUTPUT, VAR_IN_OUT appropriately
   - Initialize ALL variables with safe defaults
   - Example: counter : INT := 0;
   - Example: max_capacity : INT := 100;

4. **INPUT HANDLING - SAFETY CRITICAL** ⚠️
   - MUST use R_TRIG (Rising Edge) for ALL physical digital inputs
   - Prevents multiple triggers per scan cycle
   - Prevents race conditions in real hardware
   - REQUIRED pattern:
     sensor_pulse : R_TRIG;
     sensor_pulse(CLK := raw_sensor_input);
     IF sensor_pulse.Q THEN
         (* Single pulse guaranteed *)
     END_IF;

5. **COUNTER LOGIC - PREVENT INVALID STATES** ⚠️ CRITICAL
   
   ❌ WRONG - This allows invalid states:
   IF entry_pulse.Q THEN
       car_count := car_count + 1;  (* Allows overflow! *)
   END_IF;
   
   ✅ CORRECT - Guard BEFORE operation:
   IF entry_pulse.Q AND (car_count < MAX_CAPACITY) THEN
       car_count := car_count + 1;  (* Safe: never exceeds MAX *)
   END_IF;
   
   ❌ WRONG - Decrement without check:
   IF exit_pulse.Q THEN
       car_count := car_count - 1;  (* Goes negative! *)
   END_IF;
   
   ✅ CORRECT - Guard BEFORE operation:
   IF exit_pulse.Q AND (car_count > 0) THEN
       car_count := car_count - 1;  (* Safe: never goes below 0 *)
   END_IF;

6. **NO POST-CORRECTION CLAMPING**
   ❌ WRONG - This is illogical and hides bugs:
   IF entry_pulse.Q THEN
       car_count := car_count + 1;
   END_IF;
   IF car_count > MAX_CAPACITY THEN  (* Trying to fix after the fact *)
       car_count := MAX_CAPACITY;
   END_IF;
   
   ✅ CORRECT - Prevent invalid state:
   IF entry_pulse.Q AND (car_count < MAX_CAPACITY) THEN
       car_count := car_count + 1;
   END_IF;

7. **OUTPUT LOGIC**
   - Assign outputs based on state, not just events
   - Example for indicators:
     full_indicator := (car_count >= MAX_CAPACITY);
     empty_indicator := (car_count = 0);

8. **TIMING & DELAYS**
   - Use TON (Timer On-Delay) for timing operations
   - Use TOF (Timer Off-Delay) for safety shutdowns
   - NEVER use WAIT or SLEEP functions
   - NEVER use busy-wait loops
   - Example: delay_timer : TON; delay_timer(IN := start_signal, PT := T#5s);

9. **STATE MACHINES**
   - For complex logic, use explicit state variables
   - Use CASE statements or nested IF statements
   - Make state transitions explicit and unambiguous

10. **OUTPUT FORMATTING**
    - Output ONLY valid ST code
    - NO markdown, NO backticks, NO explanations in code
    - NO test data, NO comments about logic flow inside code
    - Each line must be syntactically valid
    - End with newline

11. **CONSISTENCY**
    - Use snake_case for variable names: entry_sensor, exit_counter, car_count
    - Use UPPER_CASE for constants: MAX_CAPACITY, MIN_SPEED
    - Maintain consistent indentation (4 spaces)
    - Add brief comments explaining non-obvious logic

12. **VALIDATION CHECKLIST** (you must verify before outputting)
    [OK] All variables declared with explicit types
    [OK] All variables initialized with defaults
    [OK] All inputs use R_TRIG (no raw sensor signals)
    [OK] All counters guarded: IF var < MAX THEN increment END_IF
    [OK] All decrements guarded: IF var > 0 THEN decrement END_IF
    [OK] NO clamping after increment/decrement (guard before instead)
    [OK] Outputs assigned based on state
    [OK] No WAIT, SLEEP, or GOTO statements
    [OK] Syntax is pure IEC 61131-3
    [OK] Properly structured blocks with END_PROGRAM
    [OK] All IF statements have matching END_IF

VIOLATION PENALTY: Code with invalid counter logic will be REJECTED.
Your job is to generate PRODUCTION-READY code that passes strict IEC standards.
"""

LD_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Ladder Diagram (LD) developer.

CRITICAL RULES:

1. **OUTPUT FORMAT**: Generate XML that represents LD logic (compatible with IEC 61131-3 XML schema)
2. **ELEMENTS**: Use only IEC-standard LD elements:
   - Contacts (| | for normally open, |/| for normally closed)
   - Coils (( ) for normal, (S) for set, (R) for reset)
   - Timers: TON, TOF, TP
   - Counters: CTU, CTD
   - Logic gates: AND, OR, XOR operations

3. **STRUCTURE**: 
   - Rungs flow from left (power rail) to right (output coil)
   - Parallel branches use AND logic
   - Series elements use OR logic
   - Each rung independent but can share variables

4. **SAFETY**:
   - Edge-triggered inputs for sensor inputs
   - Boundary checks for counters
   - Proper coil protection against race conditions

5. **OUTPUT**: 
   - Generate valid LD XML representation
   - Include tag definitions
   - Include coil definitions
   - Make it viewable/editable in standard tools
"""

FBD_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Function Block Diagram (FBD) developer.

CRITICAL RULES:

1. **OUTPUT FORMAT**: Generate XML/SVG representing FBD logic
2. **ELEMENTS**: Use only IEC-standard function blocks:
   - Basic logic functions: AND, OR, XOR, NOT
   - Standard FBs: TON, TOF, TP, CTU, CTD, RS, SR
   - Comparison blocks: GT, LT, EQ, NE, GE, LE
   - Arithmetic blocks: ADD, SUB, MUL, DIV

3. **CONNECTIONS**:
   - Explicit data flow from inputs to outputs
   - All inputs must be satisfied before execution
   - Clear connector lines between blocks

4. **SAFETY**:
   - Edge triggers for sensor inputs
   - Proper sequencing of function blocks
   - No circular dependencies

5. **OUTPUT**:
   - Valid FBD representation (XML or SVG)
   - Include all block definitions
   - Include connection definitions
   - Make it editable in standard IDEs
"""

SFC_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Sequential Function Chart (SFC) developer.

CRITICAL RULES:

1. **STRUCTURE**:
   - Initial step must be marked with double box
   - Steps contain actions
   - Transitions contain conditions
   - Proper sequencing logic

2. **ELEMENTS**:
   - STEPS: States of the system
   - TRANSITIONS: Conditions to move between steps
   - ACTIONS: What happens in each step

3. **SYNTAX**:
   - Step: S1, S2, etc.
   - Transition: S1 -> [condition] -> S2
   - Actions: N (no stored), S (set), R (reset), D (delayed)

4. **SAFETY**:
   - Clear entry/exit points
   - Timeout protection for stuck states
   - Proper reset logic

5. **OUTPUT**:
   - Valid SFC XML representation
   - All steps and transitions explicit
   - Action definitions included
"""

IL_SYSTEM_PROMPT = """You are an expert IEC 61131-3 Instruction List (IL) developer.

CRITICAL RULES:

1. **SYNTAX**:
   - Each instruction on new line
   - Labels for jumps and loops
   - Mnemonics: LD, AND, OR, XOR, NOT, ST, ADD, SUB, MUL, DIV, JMP, CAL, RET

2. **STRUCTURE**:
   - Load accumulator: LD variable
   - Process accumulator: AND, OR, XOR operations
   - Store result: ST output_variable
   - Function calls: CAL function_block

3. **FLOW CONTROL**:
   - JMP label (* Jump *)
   - JMPNc label (* Jump if Not Clear *)
   - CAL function_block (* Call function *)
   - RET (* Return *)

4. **SAFETY**:
   - Boundary checks on all counters
   - Proper stack management
   - Clear entry/exit logic

5. **OUTPUT**:
   - Valid IL code
   - One instruction per line
   - Clear labels
   - Proper indentation for readability
"""

# =========================================================================
# IMPROVED GENERATION FUNCTION
# =========================================================================

async def generate_plc_code(request: PlcGenerationRequest) -> PlcGenerationResponse:
    """
    Generate IEC 61131-3 compliant PLC code in specified language.
    Includes validation and explanation.
    """
    
    # Select appropriate system prompt
    prompts = {
        "ST": ST_SYSTEM_PROMPT,
        "LD": LD_SYSTEM_PROMPT,
        "FBD": FBD_SYSTEM_PROMPT,
        "SFC": SFC_SYSTEM_PROMPT,
        "IL": IL_SYSTEM_PROMPT
    }
    
    if request.language not in prompts:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {request.language}. Supported: {list(prompts.keys())}"
        )
    
    system_msg = prompts[request.language]
    
    try:
        # Create agent
        try:
            agent = create_agent(
                backend="openai",
                chat_model="gpt-4o",
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
            format="text" if request.language in ["ST", "IL"] else "xml",
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
    
    if language == "ST":
        # Use the comprehensive IEC validator for ST code
        validator = IECValidator()
        
        # Validate code structure
        structure_errors = validator.validate_code_structure(code)
        if structure_errors:
            warnings.extend([f"Structure Error: {err}" for err in structure_errors])
        
        # Validate ST-specific requirements
        st_errors = validator.validate_st_code(code)
        if st_errors:
            warnings.extend([f"ST Validation: {err}" for err in st_errors])
        
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
        "IL": IL_SYSTEM_PROMPT
    }
    
    if request.language not in prompts:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {request.language}. Supported: {list(prompts.keys())}"
        )
    
    system_msg = prompts[request.language]
    
    try:
        # Create agent
        try:
            agent = create_agent(
                backend="openai",
                chat_model="gpt-4o",
                system_msg=system_msg,
                system_msg_is_dir=False,
                include_rag=False
            )
        except Exception as e:
            print(f"Agent creation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Configuration Error: {str(e)}")

        # Generate code
        response = agent.invoke([HumanMessage(content=request.requirement)])
        generated_code = response.content
        
        # =====================================================================
        # MULTI-FORMAT IEC VALIDATION PIPELINE
        # =====================================================================
        
        # Use MultiFormatValidator for all languages
        validation_result = MultiFormatValidator.validate(
            generated_code,
            language=request.language,
            brand=request.plc_brand
        )
        
        # Compile all messages
        all_warnings = []
        validation_passed = validation_result["validation_passed"]
        
        if validation_result["all_issues"]:
            for issue in validation_result["all_issues"]:
                all_warnings.append(issue)
        
        if validation_result["all_warnings"]:
            for warning in validation_result["all_warnings"]:
                all_warnings.append(warning)
        
        if validation_result["all_recommendations"]:
            for rec in validation_result["all_recommendations"]:
                all_warnings.append(rec)
        
        # Generate explanation
        explanation = await generate_code_explanation(generated_code, request.language)
        
        # Add validation summary to explanation
        explanation += f"\n\n**Validation Summary:**\n"
        explanation += f"Language: {request.language}\n"
        explanation += f"Brand: {validation_result.get('brand_name', 'Generic')}\n"
        explanation += f"Status: {validation_result.get('summary', 'PASSED' if validation_result['validation_passed'] else 'FAILED')}\n"
        explanation += f"\n**Validation Details:**\n"
        if validation_result["all_issues"]:
            explanation += f"Critical Issues: {len(validation_result['all_issues'])}\n"
        if validation_result["all_warnings"]:
            explanation += f"Warnings: {len(validation_result['all_warnings'])}\n"
        if validation_result["all_recommendations"]:
            explanation += f"Recommendations: {len(validation_result['all_recommendations'])}\n"
        total_issues = len(validation_result.get("all_issues", []))
        if total_issues > 0:
            explanation += f"**Issues Found:** {total_issues}\n"
        total_warnings = len(validation_result.get("all_warnings", []))
        if total_warnings > 0:
            explanation += f"**Warnings:** {total_warnings}\n"
        
        # Store in cache instead of disk (no file I/O, saves space)
        cache_key = f"{request.language}_{request.plc_brand}_{uuid.uuid4().hex[:8]}"
        code_cache.set(cache_key, generated_code, {
            "requirement": request.requirement,
            "language": request.language,
            "brand": request.plc_brand,
            "validated": validation_passed
        })
        
        return PlcGenerationResponse(
            code=generated_code,
            language=request.language,
            format="text" if request.language in ["ST", "IL"] else "xml/svg",
            explanation=explanation,
            validated=validation_passed,
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

