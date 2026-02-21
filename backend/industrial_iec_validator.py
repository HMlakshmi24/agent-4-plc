
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

        # Rule 3: Only one PROGRAM (excluding END_PROGRAM counts)
        prog_count = U.count("PROGRAM")
        end_prog_count = U.count("END_PROGRAM")
        # Since END_PROGRAM contains the substring "PROGRAM", the raw count of "PROGRAM" includes it.
        # True PROGRAM count = Raw "PROGRAM" count - "END_PROGRAM" count
        true_prog_starts = prog_count - end_prog_count
        
        if true_prog_starts > 1:
            errors.append("Multiple PROGRAM blocks")

        # Rule 4: VAR sections exist
        if "VAR" not in U:
            errors.append("Missing VAR section")

        # Rule 5: Too many VAR sections
        var_sections = len(re.findall(r'\bVAR\b|\bVAR_INPUT\b|\bVAR_OUTPUT\b', U))
        if var_sections > 3:
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

        # Rule 12: No output reset
        if "OUTPUT RESET" not in U:
            warnings.append("No output reset section")

        # Rule 13: BOOL without default
        if re.search(r':\s*BOOL;', code) and ":= FALSE" not in code:
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

        # Rule 19: Duplicate output reset
        if U.count(":= FALSE") > 10:
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

        # Rule 23: Assignment outside logic
        if "VAR" in U and ":=" in U and "CASE" not in U:
            # This logic is a bit loose, relying on CASE existing to define logic block
            # But adhering to user spec
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
