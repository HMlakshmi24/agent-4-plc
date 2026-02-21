"""
Strict PLC Language Templates
Enforces rigid skeletons where LLM only fills logic holes.
"""

ST_SKELETON = """PROGRAM {program_name}

VAR_INPUT
{input_vars}
END_VAR

VAR_OUTPUT
{output_vars}
END_VAR

VAR
{internal_vars}
END_VAR

(* Output Reset/Safety *)
{output_reset}

(* Main Logic *)
{main_logic}

END_PROGRAM
"""

# For now, we focus strict skeleton on ST. 
# LD/FBD are harder to template strictly in text without proper XML, 
# but we can try a structured text representation if needed.
LD_SKELETON = """PROGRAM {program_name}
    VAR
        {vars}
    END_VAR

    (* Network 1: Initialization *)
    {net1_logic}

    (* Network 2: Main Control *)
    {net2_logic}
END_PROGRAM
"""

def get_strict_skeleton(language: str) -> str:
    """Retrieve the strict skeleton for the language."""
    lang = language.upper()
    if lang == "ST" or lang == "SCL":
        return ST_SKELETON
    elif lang == "LD" or lang == "LAD":
        return LD_SKELETON
    else:
        # Fallback for now
        return ST_SKELETON
