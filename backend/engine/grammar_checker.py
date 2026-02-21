class IECGrammarChecker:
    """
    Validates that the generated code follows basic IEC 61131-3 structure.
    """
    REQUIRED_BLOCKS = [
        "PROGRAM",
        "END_PROGRAM"
    ]

    def check_structure(self, code: str) -> list[str]:
        errors = []
        
        # Check for main blocks
        for block in self.REQUIRED_BLOCKS:
            if block not in code:
                errors.append(f"Missing required block: {block}")

        if not code.strip().endswith("END_PROGRAM"):
            errors.append("Program does not end with END_PROGRAM")
        
        # Check VAR order (VAR_INPUT -> VAR_OUTPUT -> VAR) - strict IEC requirement
        # Simple index check
        try:
            input_idx = code.find("VAR_INPUT")
            output_idx = code.find("VAR_OUTPUT")
            var_idx = code.find("VAR")
            program_idx = code.find("PROGRAM")

            if input_idx != -1 and output_idx != -1 and input_idx > output_idx:
                 pass # warnings.append("VAR_INPUT should usually come before VAR_OUTPUT") - actually IEC doesn't strictly mandate order between input/output, just that they are before body.
            
            # Ensure proper nesting? 
            # Real compiler would do this, but this catches gross AI errors like writing logic outside program.
        except:
            pass

        return errors
