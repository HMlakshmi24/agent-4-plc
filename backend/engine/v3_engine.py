from backend.engine.ai_v3 import generate_iec_model
from backend.engine.compiler_v3 import compile_to_st
from backend.engine.grammar_checker import IECGrammarChecker
from backend.engine.timer_validator import TimerValidator
from backend.engine.state_validator import StateMachineValidator
from backend.engine.semantic_validator import SemanticValidator
from backend.engine.auto_fixer import IECAutoFixer

def generate_v3_st(description: str) -> str:
    """
    Orchestrates the V3.1 Industrial Deterministic Engine Pipeline:
    1. AI generates strict JSON model.
    2. Initial Compile.
    3. Multi-stage Validation & Auto-FixingLoop.
    4. Final Code Generation.
    """
    
    # 1. AI -> JSON
    model = generate_iec_model(description)
    
    # 2. Compile to Text for Validation
    code = compile_to_st(model)
    
    # 3. Validation Loop (Single Pass for now, can be recursive)
    # Instantiate Validators
    grammar = IECGrammarChecker()
    timer = TimerValidator()
    state = StateMachineValidator()
    semantic = SemanticValidator()
    fixer = IECAutoFixer()
    
    errors = []
    
    # Semantic Check (Missing Vars)
    missing_vars = semantic.validate(code)
    if missing_vars:
        # AUTO-FIX: Inject missing variables into the MODEL (not the code string)
        model = fixer.fix_missing_vars(model, missing_vars)
        # Re-compile to reflect changes
        code = compile_to_st(model)
        
    # Grammar Check
    grammar_errs = grammar.check_structure(code)
    errors.extend(grammar_errs)
    
    # Timer Check
    timer_errs = timer.validate(code)
    errors.extend(timer_errs)
    
    # State Machine Check
    state_errs = state.validate(code)
    errors.extend(state_errs)
    
    # Append validation report to code comments if errors persist (non-fatal)
    if errors:
        code += "\n\n(* VALIDATION REPORT:\n"
        for e in errors:
            code += f"   - [WARNING] {e}\n"
        code += "*)"

    return code
