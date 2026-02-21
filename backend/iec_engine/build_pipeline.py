from typing import Tuple, List
from backend.iec_engine.ai_interface import generate_v4_model
from backend.iec_engine.iec_generator import IECGenerator
from backend.iec_engine.compiler_interface import CompilerInterface
from backend.iec_engine.autofix_engine import AutoFixEngine

def build_plc_code(prompt: str) -> Tuple[str, List[str]]:
    """
    The V4 Industrial Build Loop.
    1. AI Generates Model.
    2. Loop (max 3):
       a. Generate Code.
       b. Compile (Virtual/Real).
       c. If Errors -> AutoFix Model -> Retry.
       d. Else -> Success.
    """
    
    # 1. AI Intent
    model = generate_v4_model(prompt)
    
    generator = IECGenerator()
    compiler = CompilerInterface()
    fixer = AutoFixEngine()
    
    MAX_ATTEMPTS = 3
    last_code = ""
    errors = []
    
    for attempt in range(MAX_ATTEMPTS):
        # 2a. Generate
        last_code = generator.generate(model)
        
        # 2b. Compile
        success, current_errors = compiler.compile(last_code, model.program_name)
        
        if success:
            last_code += "\n\n(* COMPILE SUCCESSFUL (V4 Engine) *)"
            return last_code, []
            
        errors = current_errors
        
        # 2c. Log & Fix
        # Apply specific fixes based on errors
        try:
            model = fixer.apply_fixes(model, errors)
        except Exception as e:
            # If fixing fails, abort loop and return best effort
            errors.append(f"AutoFix Crash: {e}")
            break
            
    # Failed after max attempts
    last_code += "\n\n(* BUILD FAILED - COMPILER ERRORS used best effort *)\n"
    for e in errors:
        last_code += f"(* Error: {e} *)\n"
        
    return last_code, errors
