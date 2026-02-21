import re

class IECValidator:
    def __init__(self, brand="generic"):
        self.brand = brand.lower()

    def validate(self, code: str):
        errors = []
        warnings = []

        # Normalize text
        code_upper = code.upper()

        # ---------------------------
        # 1. STRUCTURE CHECKS
        # ---------------------------
        if "PROGRAM" not in code_upper:
            errors.append("Missing PROGRAM declaration")

        if "END_PROGRAM" not in code_upper:
            errors.append("Missing END_PROGRAM")

        if code_upper.count("VAR_INPUT") > 1:
            errors.append("Multiple VAR_INPUT sections")

        if code_upper.count("VAR_OUTPUT") > 1:
            errors.append("Multiple VAR_OUTPUT sections")

        # Detect multiple VAR blocks (internal)
        # We look for VAR followed by newlines or variables, excluding VAR_INPUT/OUTPUT
        # This regex attempts to find standalone VAR blocks
        var_blocks = re.findall(r"\bVAR\b", code_upper)
        # VAR_INPUT and VAR_OUTPUT also contain VAR, so we need to be careful.
        # Simple count check:
        total_vars = len(var_blocks)
        input_vars = code_upper.count("VAR_INPUT")
        output_vars = code_upper.count("VAR_OUTPUT")
        in_out_vars = code_upper.count("VAR_IN_OUT")
        temp_vars = code_upper.count("VAR_TEMP")
        
        # Expected standalone VARs = Total - (Inputs + Outputs + InOuts + Temps)
        standalone_vars = total_vars - (input_vars + output_vars + in_out_vars + temp_vars)
        
        if standalone_vars > 1:
            warnings.append("Multiple VAR blocks detected")

        # ---------------------------
        # 2. OUTPUT INITIALIZATION CHECK
        # ---------------------------
        # Check if assignments happen inside VAR_OUTPUT block
        output_block = self.extract_section(code, "VAR_OUTPUT")
        if output_block and ":=" in output_block:
             if self.brand in ["siemens", "codesys"]:
                errors.append("Output initialized inside VAR_OUTPUT (not allowed)")

        # ---------------------------
        # 3. OUTPUT RESET CHECK
        # ---------------------------
        output_section = self.extract_section(code, "VAR_OUTPUT")
        outputs = self.extract_variable_names(output_section)

        for out in outputs:
            # Simple check: is the output assigned to?
            if f"{out} :=" not in code and f"{out}:=" not in code:
                # Also check for function block outputs like Timer(Q=>Out) or plain assignments
                # This is a basic check; might need refinement for formal parameters
                warnings.append(f"Output '{out}' may not be written to in scan")

        # ---------------------------
        # 4. TIMER USAGE CHECK
        # ---------------------------
        # Strict Rule: Timers should not be inside IF statements usually, 
        # or at least should be called unconditionally if possible.
        # This is hard to detect perfectly with regex, but we can look for basic patterns.
        if "TON" in code_upper or "TOF" in code_upper:
            # Check if likely inside an IF block (heuristic: indentation or previous line)
            # Find lines with Timer(
            pass

        # ---------------------------
        # 5. COUNTER SAFETY CHECK (Edge Detection)
        # ---------------------------
        # Pattern: Count := Count + 1 inside an IF without a 'TRIG' or '.Q' condition
        # This is a heuristic to catch level-triggered counting
        if self.brand == "siemens":
            # Find addition assignments
            add_assigns = re.finditer(r"(\w+)\s*:=\s*\1\s*\+\s*1", code, re.IGNORECASE)
            for match in add_assigns:
                var_name = match.group(1)
                # Look at context (preceding lines) - simplistic check
                # Ideally, we want to see if the surrounding IF condition involves a trigger
                # Complex to do with regex on the whole string, but we can warn generally
                if "R_TRIG" not in code_upper and "F_TRIG" not in code_upper:
                     warnings.append(f"Counter usage '{var_name} := {var_name} + 1' detected without R_TRIG declaration. Ensure edge detection is used.")

        # ---------------------------
        # 6. UNUSED VARIABLE CHECK
        # ---------------------------
        var_section = self.extract_section(code, "VAR")
        internal_vars = self.extract_variable_names(var_section)

        for var in internal_vars:
            # Count occurrences in the whole code
            # Should be > 1 (declaration + usage)
            usage_count = len(re.findall(rf"\b{re.escape(var)}\b", code, re.IGNORECASE))
            if usage_count <= 1:
                warnings.append(f"Unused variable: {var}")

        # ---------------------------
        # 6. STATE MACHINE CHECK
        # ---------------------------
        # Only warn if it looks like a sequence but has no case
        if "STEP" in code_upper or "STATE" in code_upper:
            if "CASE" not in code_upper:
                warnings.append("State machine variables detected but no CASE statement found")

        # ---------------------------
        # RESULT
        # ---------------------------
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    # -----------------------------------
    # Helper: extract section text
    # -----------------------------------
    def extract_section(self, code, section_name):
        # Look for SECTION_NAME ... END_VAR
        pattern = rf"{section_name}(.+?)END_VAR"
        match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    # -----------------------------------
    # Helper: extract variable names
    # -----------------------------------
    def extract_variable_names(self, section_text):
        variables = []
        if not section_text:
            return variables
            
        lines = section_text.split("\n")

        for line in lines:
            line = line.strip()
            # Remove comments
            line = re.sub(r"\(*.*?\)*", "", line) # (* comment *)
            line = re.sub(r"//.*", "", line)     # // comment
            
            if ":" in line:
                # var_name : type ...
                part = line.split(":")[0].strip()
                # Handle multiple decls: var1, var2 : type
                names = [n.strip() for n in part.split(",")]
                for name in names:
                    if name:
                        variables.append(name)

        return variables
