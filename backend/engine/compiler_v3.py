from typing import List
from backend.models.iec_models import ProgramModel, Variable

def compile_to_st(model: ProgramModel) -> str:
    """
    Deterministically compiles a ProgramModel into valid IEC 61131-3 Structured Text.
    NO AI involved in this step.
    """
    code = []
    
    # 1. Header
    code.append(f"PROGRAM {model.name}")
    
    # 2. VAR_INPUT
    if model.inputs:
        code.append("VAR_INPUT")
        for var in model.inputs:
            line = f"    {var.name} : {var.type};"
            if var.comment:
                line += f" (* {var.comment} *)"
            code.append(line)
        code.append("END_VAR")

    # 3. VAR_OUTPUT
    if model.outputs:
        code.append("VAR_OUTPUT")
        for var in model.outputs:
            line = f"    {var.name} : {var.type};"
            if var.comment:
                line += f" (* {var.comment} *)"
            code.append(line)
        code.append("END_VAR")

    # 4. VAR (Internals)
    if model.internals:
        code.append("VAR")
        for var in model.internals:
            init = f" := {var.initial_value}" if var.initial_value else ""
            line = f"    {var.name} : {var.type}{init};"
            if var.comment:
                line += f" (* {var.comment} *)"
            code.append(line)
        code.append("END_VAR")

    # 5. Body
    code.append("")
    # Indent logic
    for line in model.logic:
        if line.strip(): # Skip empty lines in logic list
            code.append(f"    {line}")
    
    # 6. Footer
    code.append("END_PROGRAM")
    
    return "\n".join(code)
