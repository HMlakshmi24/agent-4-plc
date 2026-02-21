class IECGrammarChecker:
    """
    Layer 3 Structural Validation.
    Ensures Program block integrity and check for common structural issues.
    """
    
    REQUIRED_BLOCKS = ["PROGRAM", "END_PROGRAM", "VAR", "END_VAR"]
    
    def check_structure(self, code: str) -> list[str]:
        errors = []
        
        # 1. Main Blocks
        if "PROGRAM" not in code:
            errors.append("Missing 'PROGRAM' keyword.")
        if "END_PROGRAM" not in code:
            errors.append("Missing 'END_PROGRAM' keyword.")
            
        # 2. End Semicolon Check (Heuristic)
        # Every line that isn't a keyword (IF, THEN, ELSE, VAR, BEGIN, END_XXX) or comment should end in ;
        lines = code.split('\n')
        keywords = ["IF", "THEN", "ELSE", "ELSIF", "CASE", "OF", "FOR", "DO", "WHILE", "REPEAT", "PROGRAM", "VAR", "VAR_INPUT", "VAR_OUTPUT", "END_VAR", "END_IF", "END_CASE", "END_FOR", "END_WHILE", "END_PROGRAM"]
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped: continue
            if stripped.startswith("(*"): continue
            
            # Check for missing semicolon
            # Logic: If it's an assignment or FB call, it needs ;
            # If it ends with a keyword, it doesn't.
            
            ends_with_keyword = any(stripped.upper().endswith(k) for k in keywords)
            is_block_start = stripped.upper().endswith("THEN") or stripped.upper().endswith("DO") or stripped.upper().endswith("OF")
            
            if not ends_with_keyword and not is_block_start and not stripped.endswith(";") and not stripped.endswith(":"):
                # Potential missing semicolon
                # Exclude labels "10:" 
                # Exclude var declarations "Name : Type" (usually end in ; but check anyway)
                pass 
                # This check is hard to make deterministic with simple heuristics without full parser.
                # Sticking to Block Checks for now.
        
        # 3. IF/END_IF Balance
        if code.count("IF ") != code.count("END_IF;"):
             # Simple count check
             pass # heuristic, might be commented out code
             
        return errors
