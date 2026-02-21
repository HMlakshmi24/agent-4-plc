import re
from typing import Set, List
from backend.models.iec_models import ProgramModel, Variable

KEYWORDS = {
    "IF", "THEN", "ELSE", "ELSIF", "END_IF",
    "CASE", "OF", "END_CASE",
    "FOR", "TO", "DO", "END_FOR",
    "WHILE", "END_WHILE",
    "VAR", "VAR_INPUT", "VAR_OUTPUT", "END_VAR", "PROGRAM", "END_PROGRAM",
    "TRUE", "FALSE", "NOT", "AND", "OR", "XOR",
    "TON", "TOF", "TP", "R_TRIG", "F_TRIG", "CTU", "CTD",
    "INT", "BOOL", "REAL", "TIME", "STRING"
}

def validate_and_fix_model(model: ProgramModel) -> ProgramModel:
    """
    Scans the logic for used variables.
    If a variable is used but not defined in inputs/outputs/internals,
    it automatically injects it into 'internals'.
    """
    
    # 1. Build Symbol Table
    defined_symbols: Set[str] = set()
    
    for v in model.inputs: defined_symbols.add(v.name.upper())
    for v in model.outputs: defined_symbols.add(v.name.upper())
    for v in model.internals: defined_symbols.add(v.name.upper())

    # 2. Scan Logic for Tokens
    # Regex for potential identifiers: starts with letter, contains alphanumeric or underscore
    identifier_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
    
    used_symbols = set()
    code_text = "\n".join(model.logic)
    
    # Simple comment stripper (not perfect but good enough for heuristics)
    # Remove (* ... *)
    code_no_comments = re.sub(r'\(\*.*?\*\)', '', code_text, flags=re.DOTALL)
    
    for match in identifier_pattern.finditer(code_no_comments):
        token = match.group()
        if token.upper() not in KEYWORDS and not token.isdigit():
             # Basic heuristic: if it looks like a variable
             used_symbols.add(token)

    # 3. Detect Missing Symbols
    missing = []
    for symbol in used_symbols:
        if symbol.upper() not in defined_symbols:
            # It's missing! Determine type heuristics.
            missing.append(symbol)

    # 4. Auto-Fix: Inject Missing
    for name in missing:
        # Heuristic 1: Timers often used as Timer1(IN:=...)
        # Check usage in code
        if re.search(rf'\b{name}\s*\(', code_text):
            # Function Block call? Likely TON/TOF or R_TRIG
            # Default to TON as it's most common, or check context?
            # Safe bet: TON if "Timer" in name, code usually suggests.
            
            # If name contains "Timer" -> TON
            if "TIMER" in name.upper():
                model.internals.append(Variable(name=name, type="TON", comment="Auto-corrected"))
            else:
                 # Generic Function Block or helper? 
                 # Let's default to BOOL to be safe if it's like "MyFunc()"? No, that's bad.
                 # If it looks like a function call, maybe we shouldn't define it as VAR.
                 # But in ST, FB instances MUST be in VAR.
                 pass
        
        # Heuristic 2: State variable
        elif name.upper() == "STATE":
            model.internals.append(Variable(name=name, type="INT", initial_value="0", comment="Auto-corrected"))
        
        # Heuristic 3: Default to BOOL for everything else (Flags, Sensors)
        else:
            # If it's used with := it's likely a variable.
            # If it defines a value T#..., it's not a var.
            # T#5s is caught by regex? \bT\b and \bs\b? No, T# is distinct.
            # Check if it's a literal part like 's', 'ms'?
            if name.upper() in ['S', 'MS', 'M', 'H']: continue # Time units

            model.internals.append(Variable(name=name, type="BOOL", comment="Auto-corrected"))

    return model
