
from backend.engine.prompt_builder import build_strict_prompt
from backend.engine.validator import validate_ld
from backend.engine.json_loader import safe_json_load
from backend.ai.openai_client import generate_ld
from backend.engine.models import LDProgram
from backend.engine.renderer import render_ladder # Imported for final logic generation if needed by routes

MAX_RETRIES = 3

def compile_ld(user_prompt: str):

    errors = None
    structured = None
    validation = None

    for attempt in range(MAX_RETRIES):

        strict_prompt = build_strict_prompt(user_prompt, errors)

        ai_output = generate_ld(strict_prompt)

        try:
            structured = safe_json_load(ai_output)
            program = LDProgram(**structured)
            
            validation = validate_ld(program)

            if validation["valid"]:
                
                # Render ASCII for convenience
                ascii_logic = render_ladder(program)
                
                return {
                    "status": "valid",
                    "attempts": attempt + 1,
                    "validation": validation,
                    "program": structured,
                    "ladder_ascii": ascii_logic
                }

            errors = validation["errors"]
            print(f"Compiler Attempt {attempt+1} Failed: {errors}")

        except Exception as e:
            print(f"Compiler Parsing Error (Attempt {attempt+1}): {e}")
            errors = [f"JSON Parsing Error: {str(e)}"]

    # Failed after retries
    return {
        "status": "failed",
        "attempts": MAX_RETRIES,
        "validation": validation if validation else {"valid": False, "errors": errors},
        "program": structured, # Might be partial or None
        "ladder_ascii": f"(* Compilation Failed after {MAX_RETRIES} attempts. Errors: {errors} *)"
    }
