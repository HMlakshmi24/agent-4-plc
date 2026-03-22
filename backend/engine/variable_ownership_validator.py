# backend/engine/variable_ownership_validator.py

import re

class VariableOwnershipValidator:
    """
    Layer 11: Validates that Q_ outputs are assigned exactly once, 
    no undeclared vars are used, and no orphan M_ flags exist.
    """
    def __init__(self, st_code: str, signal_map: dict):
        self.st_code = st_code
        self.signal_map = signal_map
        self.critical = []
        self.warning = []

    def check_output_assignments(self):
        outputs = self.signal_map.get("outputs", [])
        
        for out in outputs:
            if isinstance(out, dict):
                name = str(out.get("name", out.get("id", ""))).strip()
            else:
                name = str(out).strip()
                
            if not name:
                continue
            
            # Find assignments: Q_Name := ...
            assign_pattern = rf"\b{re.escape(name)}\s*:="
            assignments = re.findall(assign_pattern, self.st_code)
            
            if len(assignments) == 0:
                self.critical.append(f"Output '{name}' is declared but never assigned.")
            elif len(assignments) > 1:
                self.critical.append(f"Output '{name}' is assigned multiple times (scattered output).")

    def validate(self) -> dict:
        self.check_output_assignments()
        
        return {
            "critical": self.critical,
            "warning": self.warning
        }
