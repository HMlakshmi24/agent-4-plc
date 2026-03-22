# backend/engine/industrial_polish.py

import re

def add_state_comments(st_code: str, control_model: dict) -> str:
    """
    Layer 10: Deterministic formatting and professional comment injection.
    No AI. Operates on final ST code.
    """
    states = control_model.get("states", [])
    state_names = {}
    
    # Extract state int mapping from CASE if we can, or assume 0, 1, 2...
    for i, state in enumerate(states):
        name = state.get("name", state.get("label", f"State_{i}"))
        state_names[i] = name

    lines = st_code.split("\n")
    new_lines = []

    # Regex for exactly "N:" which triggers a CASE block label
    case_regex = re.compile(r"^(\s*)(\d+):\s*(?:\(\*.*\*\))?\s*$")

    for line in lines:
        stripped = line.strip()
        
        # Add comment to assignment: M_State := N;
        match_assign = re.match(r"^(.*M_State\s*:=\s*)(\d+)(;.*)$", line)
        if match_assign:
            pre, state_val_str, post = match_assign.groups()
            state_val = int(state_val_str)
            if state_val in state_names:
                state_name = state_names[state_val]
                # Avoid double commenting
                if "(*" not in post:
                    line = f"{pre}{state_val_str}{post} (* Transition to {state_name} *)"
        
        # Re-format CASE labels if they lack comments
        match_case = case_regex.match(line)
        if match_case:
            indent, state_val_str = match_case.groups()
            state_val = int(state_val_str)
            if state_val in state_names:
                line = f"{indent}{state_val_str}: (* {state_names[state_val]} *)"
                
        # Normalize simple spacing
        line = line.replace(" := ", " := ") # already normalized usually

        new_lines.append(line.rstrip())

    # Ensure clean trailing newline
    return "\n".join(new_lines).strip() + "\n"
