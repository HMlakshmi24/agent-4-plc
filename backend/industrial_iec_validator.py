
import re

class IndustrialIECValidator:

    @staticmethod
    def validate(code: str):
        errors = []
        warnings = []
        U = code.upper()

        # Rule 1: PROGRAM exists
        if "PROGRAM" not in U:
            errors.append("Missing PROGRAM declaration")

        # Rule 2: END_PROGRAM exists
        if "END_PROGRAM" not in U:
            errors.append("Missing END_PROGRAM")

        # Rule 3: Only one PROGRAM — use start-of-line anchor so comments like
        # "// Main program loop" or "// PROGRAM description" don't produce false positives
        code_no_comments = re.sub(r'//[^\n]*', '', code)
        code_no_comments = re.sub(r'\(\*.*?\*\)', '', code_no_comments, flags=re.DOTALL)
        U_no_comments = code_no_comments.upper()
        # Match "PROGRAM <name>" only at start of (possibly indented) line
        prog_decls = re.findall(r'^\s*PROGRAM\s+\w+', U_no_comments, re.MULTILINE)
        true_prog_starts = len(prog_decls)

        if true_prog_starts > 1:
            errors.append("Multiple PROGRAM blocks")

        # Rule 4: VAR sections exist
        if "VAR" not in U:
            errors.append("Missing VAR section")

        # Rule 5: Too many VAR sections (count inside PROGRAM only, using comment-stripped code)
        prog_match = re.search(r'^\s*PROGRAM\s+\w+\b(.*?)\bEND_PROGRAM\b', U_no_comments, re.DOTALL | re.MULTILINE)
        prog_body = prog_match.group(1) if prog_match else U_no_comments
        var_sections = len(re.findall(r'\bVAR\b|\bVAR_INPUT\b|\bVAR_OUTPUT\b', prog_body))
        if var_sections > 6:
            errors.append("Too many VAR sections")

        # Rule 6: Illegal keyword
        if " IEC" in U or U.startswith("IEC"):
            errors.append("Illegal keyword 'iec' found")

        # Rule 7: Timer Q assignment
        if ".Q :=" in U:
            errors.append("Illegal assignment to Timer.Q")

        # Rule 8: Timer ET assignment
        if ".ET :=" in U:
            errors.append("Illegal assignment to Timer.ET")

        # Rule 9: Missing END_CASE
        if "CASE" in U and "END_CASE" not in U:
            errors.append("CASE without END_CASE")

        # Rule 10: Missing END_IF
        if "IF" in U and "END_IF" not in U:
            warnings.append("Possible missing END_IF")

        # Rule 11: Unbalanced parentheses
        if code.count("(") != code.count(")"):
            errors.append("Unbalanced parentheses")

        # Rule 12: No output reset (warn only if outputs aren't initialized)
        if "OUTPUT RESET" not in U:
            output_block = re.search(r"VAR_OUTPUT(.*?)END_VAR", code, re.S | re.I)
            if output_block:
                if not re.search(r":=\s*(FALSE|0)", output_block.group(1), re.I):
                    warnings.append("No output reset section")

        # Rule 13: BOOL outputs without default initialization
        output_block = re.search(r"VAR_OUTPUT(.*?)END_VAR", code, re.S | re.I)
        if output_block and re.search(r':\s*BOOL;', output_block.group(1)) and not re.search(r":=\s*FALSE", output_block.group(1), re.I):
            warnings.append("BOOL outputs not initialized")

        # Rule 14: Multiple END_VAR missing
        if "END_VAR" not in U:
            errors.append("Missing END_VAR")

        # Rule 15: Invalid timer call
        if "TON(" in code and "PT :=" not in code:
            warnings.append("Timer missing PT parameter")

        # Rule 16: No semicolons
        if ";" not in code:
            errors.append("No semicolons detected")

        # Rule 17: Logic before VAR
        if "CASE" in U and "VAR" in U and U.index("CASE") < U.index("VAR"):
            errors.append("Logic before VAR sections")

        # Rule 18: Output inside VAR_INPUT (Disabled due to regex complexity)
        # Using a simple string check is too aggressive.
        pass

        # Rule 19: Duplicate output reset (only if explicit reset section exists)
        if "OUTPUT RESET" in U and U.count(":= FALSE") > 10:
            warnings.append("Possible duplicate resets")

        # Rule 20: Undeclared variables (basic check)
        if "HEATER" in U and "VAR_OUTPUT" not in U:
            warnings.append("Possible undeclared output")

        # Rule 21: Missing logic
        if "CASE" not in U and "IF" not in U:
            warnings.append("No logic detected")

        # Rule 22: Missing timers where expected
        if "TIMER" in U and "TON" not in U:
            warnings.append("Timer mentioned but not used")

        # Rule 23: Assignment outside logic (only warn if no logic present)
        if "VAR" in U and ":=" in U and "CASE" not in U and "IF" not in U:
            warnings.append("Assignments outside logic")

        # Rule 24: Mixed languages
        if "NETWORK" in U and "CASE" in U:
            errors.append("Mixed LD and ST syntax")

        # Rule 25: Missing END_PROGRAM newline
        if not code.strip().endswith("END_PROGRAM"):
            warnings.append("END_PROGRAM formatting issue")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
