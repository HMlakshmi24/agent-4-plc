import re

class SemanticValidator:
    """
    Validates that all used symbols are declared in the Variable Tables.
    """
    
    KEYWORDS = {
        "PROGRAM", "END_PROGRAM", "VAR", "END_VAR", "VAR_INPUT", "END_VAR", "VAR_OUTPUT", 
        "IF", "THEN", "ELSE", "ELSIF", "END_IF", "CASE", "OF", "END_CASE", "FOR", "TO", "DO", 
        "WHILE", "REPEAT", "UNTIL", "TRUE", "FALSE", "NOT", "AND", "OR", "XOR", "MOD", 
        "TON", "TOF", "TP", "R_TRIG", "F_TRIG", "CTU", "CTD", "BOOL", "INT", "REAL", "TIME", 
        "STRING", "AT", "BYTE", "WORD", "DWORD", "LREAL", "DINT", "SINT", "USINT", "UINT", 
        "UDINT", "ULINT", "DATE", "TOD", "DT"
    }

    def extract_declared(self, code: str) -> set:
        declared = set()
        # Regex to capture "Name : Type" pattern inside VAR blocks
        # We assume standard formatting from our compiler, but regex handles some variation
        # name : type;
        pattern = r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*[A-Za-z_]"
        matches = re.finditer(pattern, code)
        for m in matches:
            name = m.group(1)
            if name.upper() not in self.KEYWORDS:
                declared.add(name.upper())
        return declared

    def extract_used(self, code: str) -> set:
        used = set()
        # Naive token extraction: find all words
        # Remove comments first
        code_no_comments = re.sub(r'\(\*.*?\*\)', '', code, flags=re.DOTALL)
        
        # Look for identifiers
        tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code_no_comments)
        
        for t in tokens:
            up = t.upper()
            if up not in self.KEYWORDS and not up.isdigit():
                # Filter out likely literals (T#5s split into T, s) -> T is handled 
                # Better regex needed for literals validation context, but simple set diff is powerful
                if up not in ['S', 'MS', 'M', 'H', 'D', 'T']: # Time units
                    used.add(up)
        return used

    def validate(self, code: str) -> list[str]:
        # Returns list of missing variables
        declared = self.extract_declared(code)
        used = self.extract_used(code)
        
        missing = used - declared
        return list(missing)
