from backend.models.iec_models import ProgramModel, Variable
import re

class IECAutoFixer:
    """
    Fixes common errors in ProgramModel before compilation.
    """
    
    def fix_missing_vars(self, model: ProgramModel, missing_vars: list[str]) -> ProgramModel:
        """
        Injects missing variables into model.internals based on heuristics.
        """
        if not missing_vars:
            return model
            
        current_vars = {v.name.upper() for v in model.inputs + model.outputs + model.internals}
        
        for name in missing_vars:
            if name.upper() in current_vars:
                continue
                
            # Heuristics
            var_type = "BOOL" # Default
            initial = None
            
            # Timer Heuristic
            if "TIMER" in name.upper() or name.upper().startswith("T"):
                # If it looks like a timer usage, check if it's used as instance
                # Simple check: if name contains 'Timer', likely TON
                if "TIMER" in name.upper():
                    var_type = "TON"
            
            # State Heuristic
            if name.upper() == "STATE":
                var_type = "INT"
                initial = "0"
            
            # Counter Heuristic
            if "COUNT" in name.upper() or name.upper().startswith("C"):
                 # Determine logic? standard INT for now usually
                 if "CTU" in name.upper(): var_type = "CTU"
                 else: var_type = "INT"

            new_var = Variable(
                name=name, 
                type=var_type, 
                initial_value=initial, 
                comment="Auto-fixed by Agent4PLC"
            )
            model.internals.append(new_var)
            current_vars.add(name.upper())

        return model
