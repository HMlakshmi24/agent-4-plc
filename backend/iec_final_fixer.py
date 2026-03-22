
import re


def _merge_multiple_programs(code: str, program_name: str) -> str:
    """
    If the LLM generates multiple PROGRAM blocks, merge them into one.
    Keeps TYPE/FUNCTION_BLOCK preamble intact.
    """
    # Use start-of-line anchor so comments like "// Main program loop" don't match
    prog_re = re.compile(r'^\s*PROGRAM\s+\w+\b(.*?)\bEND_PROGRAM\b', re.DOTALL | re.IGNORECASE | re.MULTILINE)
    matches = list(prog_re.finditer(code))
    if len(matches) <= 1:
        return code

    # Collect preamble (TYPE / FUNCTION_BLOCK sections before first PROGRAM)
    preamble = code[:matches[0].start()].strip()

    var_input_parts, var_output_parts, var_parts, logic_parts = [], [], [], []

    for m in matches:
        body = m.group(1)

        vi = re.search(r'\bVAR_INPUT\b(.*?)\bEND_VAR\b', body, re.DOTALL | re.IGNORECASE)
        if vi:
            var_input_parts.append(vi.group(1).strip())

        vo = re.search(r'\bVAR_OUTPUT\b(.*?)\bEND_VAR\b', body, re.DOTALL | re.IGNORECASE)
        if vo:
            var_output_parts.append(vo.group(1).strip())

        # Local VAR only (strip VAR_INPUT and VAR_OUTPUT first)
        body_no_io = re.sub(r'\bVAR_INPUT\b.*?\bEND_VAR\b', '', body, flags=re.DOTALL | re.IGNORECASE)
        body_no_io = re.sub(r'\bVAR_OUTPUT\b.*?\bEND_VAR\b', '', body_no_io, flags=re.DOTALL | re.IGNORECASE)
        vl = re.search(r'\bVAR\b(.*?)\bEND_VAR\b', body_no_io, re.DOTALL | re.IGNORECASE)
        if vl:
            var_parts.append(vl.group(1).strip())

        # Logic = everything after the last END_VAR in this body
        all_end_var = [m2.end() for m2 in re.finditer(r'\bEND_VAR\b', body, re.IGNORECASE)]
        if all_end_var:
            logic = body[all_end_var[-1]:].strip()
            if logic:
                logic_parts.append(logic)

    lines = []
    if preamble:
        lines.append(preamble)
        lines.append('')

    lines.append(f'PROGRAM {program_name}')

    if var_input_parts:
        lines.append('VAR_INPUT')
        for part in var_input_parts:
            lines.append(part)
        lines.append('END_VAR')

    if var_output_parts:
        lines.append('VAR_OUTPUT')
        for part in var_output_parts:
            lines.append(part)
        lines.append('END_VAR')

    lines.append('VAR')
    for part in var_parts:
        lines.append(part)
    lines.append('END_VAR')

    for logic in logic_parts:
        lines.append(logic)

    lines.append('END_PROGRAM')
    return '\n'.join(lines)


def _merge_duplicate_var_sections(code: str) -> str:
    """
    Merge duplicate VAR, VAR_INPUT, VAR_OUTPUT sections inside the PROGRAM block.
    Only merges the first PROGRAM block's internals.
    """
    prog_match = re.search(r'(\bPROGRAM\s+\w+\b)(.*?)(\bEND_PROGRAM\b)', code, re.DOTALL | re.IGNORECASE)
    if not prog_match:
        return code

    prog_header = prog_match.group(1)
    body = prog_match.group(2)
    prog_footer = prog_match.group(3)
    before = code[:prog_match.start()]
    after = code[prog_match.end():]

    def merge_sections(tag: str, body_text: str) -> tuple[str, str]:
        pattern = re.compile(rf'\b{tag}\b(.*?)\bEND_VAR\b', re.DOTALL | re.IGNORECASE)
        found = pattern.findall(body_text)
        if len(found) <= 1:
            return body_text, ''
        # Remove all occurrences, return merged content
        cleaned = pattern.sub('', body_text)
        merged_content = '\n'.join(p.strip() for p in found if p.strip())
        return cleaned, merged_content

    body, vi_content = merge_sections('VAR_INPUT', body)
    body, vo_content = merge_sections('VAR_OUTPUT', body)
    body, v_content = merge_sections('VAR', body)

    # Rebuild declarations at the top of the body
    new_decls = ''
    if vi_content:
        new_decls += f'\nVAR_INPUT\n{vi_content}\nEND_VAR'
    if vo_content:
        new_decls += f'\nVAR_OUTPUT\n{vo_content}\nEND_VAR'
    if v_content:
        new_decls += f'\nVAR\n{v_content}\nEND_VAR'

    new_body = new_decls + '\n' + body.strip()
    result = before + prog_header + new_body + '\n' + prog_footer + after
    return result


def final_iec_fix(code: str, program_name: str = "Main") -> str:
    if not code:
        return f"PROGRAM {program_name}\n    (* Error: No code generated *)\nEND_PROGRAM"

    # Step 0: Normalize invalid END_VAR_INPUT / END_VAR_OUTPUT → END_VAR
    code = re.sub(r'\bEND_VAR_INPUT\b', 'END_VAR', code, flags=re.IGNORECASE)
    code = re.sub(r'\bEND_VAR_OUTPUT\b', 'END_VAR', code, flags=re.IGNORECASE)

    # Step 0a: Merge multiple PROGRAM blocks if LLM generated more than one
    code = _merge_multiple_programs(code, program_name)

    U = code.upper()

    # Ensure PROGRAM wrapper
    if "PROGRAM" not in U:
        code = f"PROGRAM {program_name}\n" + code

    if "END_PROGRAM" not in U:
        code += "\nEND_PROGRAM"

    # Step 0b: Merge duplicate VAR sections within the single PROGRAM
    code = _merge_duplicate_var_sections(code)

    # Remove illegal timer writes
    lines = code.splitlines()
    fixed = []
    for l in lines:
        if ".Q :=" in l or ".ET :=" in l:
            continue
        fixed.append(l)

    code = "\n".join(fixed)

    # Ensure output reset (only if outputs are never assigned later)
    # This logic attempts to find VAR_OUTPUT ... END_VAR and insert clean resets
    if "VAR_OUTPUT" in code.upper() and "OUTPUT RESET" not in code.upper():
        current_lines = code.splitlines()
        reset_lines = []
        inside_output = False
        output_names = []
        
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
                    output_names.append(name)
                    reset_lines.append(f"{name} := FALSE;")

        # Skip reset injection if outputs are already assigned in logic body
        if output_names:
            # Look for assignments outside the VAR_OUTPUT block
            body = code
            for name in output_names:
                if re.search(rf"\b{name}\s*:=", body):
                    reset_lines = []
                    break

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
