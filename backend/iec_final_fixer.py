
import re

def final_iec_fix(code: str, program_name: str = "Main") -> str:
    if not code:
        return f"PROGRAM {program_name}\n    (* Error: No code generated *)\nEND_PROGRAM"

    U = code.upper()

    # Ensure PROGRAM wrapper
    if "PROGRAM" not in U:
        code = f"PROGRAM {program_name}\n" + code

    if "END_PROGRAM" not in U:
        code += "\nEND_PROGRAM"

    # Remove illegal timer writes
    lines = code.splitlines()
    fixed = []
    for l in lines:
        if ".Q :=" in l or ".ET :=" in l:
            continue
        fixed.append(l)

    code = "\n".join(fixed)

    # Ensure output reset
    # This logic attempts to find VAR_OUTPUT ... END_VAR and insert clean resets
    if "VAR_OUTPUT" in code.upper() and "OUTPUT RESET" not in code.upper():
        current_lines = code.splitlines()
        reset_lines = []
        inside_output = False
        
        # Identify outputs
        for l in current_lines:
            if "VAR_OUTPUT" in l.upper():
                inside_output = True
            elif "END_VAR" in l.upper() and inside_output:
                inside_output = False # End of output block

            if inside_output and ":" in l and "BOOL" in l.upper():
                # Extract variable name from "Name : BOOL;"
                parts = l.split(":")
                name_part = parts[0].strip()
                # Handle multiple standard declarations if possible, though strict ST usually 1 per line logic
                names = [n.strip() for n in name_part.split(",")]
                for name in names:
                    reset_lines.append(f"{name} := FALSE;")

        if reset_lines:
            reset_block = "\n    (* OUTPUT RESET *)\n    " + "\n    ".join(reset_lines) + "\n"
            # Insert after the last END_VAR of the declarations, or specifically the output block?
            # User code replaced "END_VAR" with "END_VAR" + block, limit 1.
            # This is risky if VAR_INPUT is first.
            # Safer: Replace the END_VAR that closes VAR_OUTPUT?
            # User prompt used `code.replace("END_VAR", "END_VAR" + reset_block, 1)`
            # Let's try to be slightly smarter but stick to the spirit. 
            # If we find VAR_OUTPUT, we want to append AFTER that block closes.
            
            # Simple heuristic: Inject at start of body? (i.e., after all VAR blocks)
            # Finding the last END_VAR before logic starts is hard without parsing.
            # Let's use the user's provided logic but apply it carefully.
            
            # If I follow user code exactly:
            # code = code.replace("END_VAR", "END_VAR" + reset_block, 1)
            # This matches the *first* END_VAR. If Inputs are first, it puts reset between Input and Output.
            # However, in ST, order is VAR_INPUT, VAR_OUTPUT, VAR.
            # So 1st END_VAR is likely INPUT.
            # I will modify to replace the LAST occurrence of END_VAR before the code body?
            # Or just use Regex to match `VAR_OUTPUT.*?END_VAR`.
            
            output_block_pattern = re.compile(r"(VAR_OUTPUT.*?END_VAR)", re.DOTALL | re.IGNORECASE)
            match = output_block_pattern.search(code)
            if match:
                # Append reset block after this specific END_VAR
                full_block = match.group(0)
                new_block = full_block + reset_block
                code = code.replace(full_block, new_block, 1)
            else:
                 # Fallback: simple append if Regex fails but VAR_OUTPUT detected (unlikely)
                 pass

    return code
