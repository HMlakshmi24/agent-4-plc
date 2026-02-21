from typing import List, Dict, Tuple
import re

class FBSignatureValidator:
    """
    Enforces correct signatures for standard IEC 61131-3 Function Blocks.
    Prevents AI hallucinations like 'RESET' instead of 'R' or 'START' instead of 'IN'.
    """
    
    # Standard IEC 61131-3 Signatures
    SIGNATURES = {
        "TON": {"IN", "PT"},
        "TOF": {"IN", "PT"},
        "TP":  {"IN", "PT"},
        "CTU": {"CU", "R", "PV"},
        "CTD": {"CD", "LD", "PV"},
        "CTUD": {"CU", "CD", "R", "LD", "PV"},
        "R_TRIG": {"CLK"},
        "F_TRIG": {"CLK"},
        "SR": {"S1", "R"},
        "RS": {"S", "R1"}
    }
    
    # Common AI hallucinations -> Correct mapping
    FIX_MAP = {
        "RESET": "R",
        "START": "IN",
        "TIME": "PT",
        "DELAY": "PT",
        "COUNT": "CU",
        "LOAD": "LD",
        "VALUE": "PV",
        "TRIGGER": "CLK"
    }

    def validate(self, code: str) -> List[str]:
        errors = []
        
        # Regex to find FB calls: Name(Param := Val, ...)
        # We need to know the type of 'Name'. 
        # This validator is context-free on the code string, so we need to first find declarations.
        
        declared_types = self._extract_declarations(code)
        
        # Matches: InstanceName(Param := ...
        # Group 1: Instance Name
        # Group 2: Parameters block
        call_pattern = r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\);"
        calls = re.finditer(call_pattern, code, re.DOTALL)
        
        for match in calls:
            instance_name = match.group(1)
            params_block = match.group(2)
            
            if instance_name.upper() not in declared_types:
                continue # Not a known FB instance, maybe a function call
                
            fb_type = declared_types[instance_name.upper()]
            
            if fb_type not in self.SIGNATURES:
                continue # User defined FB or unknown standard one
                
            valid_inputs = self.SIGNATURES[fb_type]
            
            # Parse used params
            # key := val
            used_params = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:=", params_block)
            
            for param in used_params:
                if param.upper() not in valid_inputs:
                    # check if we can suggest a fix
                    fix = self.FIX_MAP.get(param.upper())
                    msg = f"Invalid parameter '{param}' for {fb_type} instance '{instance_name}'."
                    if fix and fix in valid_inputs:
                        msg += f" Did you mean '{fix}'?"
                    errors.append(msg)
                    
        return errors

    def _extract_declarations(self, code: str) -> Dict[str, str]:
        """Returns {INSTANCE_NAME: TYPE}"""
        upper_code = code.upper()
        # VAR ... END_VAR blocks
        # We just scan all Name : Type patterns, assuming they are in VAR blocks
        # Name : Type;
        matches = re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*;", code)
        types = {}
        for m in matches:
            name = m.group(1).upper()
            typ = m.group(2).upper()
            types[name] = typ
        return types
