from typing import List
from backend.iec_engine.model_schema import IECProgramModel, Variable

class AutoFixEngine:
    """
    Parses compiler errors and applies deterministic fixes to the IECProgramModel.
    We fix the MODEL, not the code string, to ensure consistency.
    """
    
    def apply_fixes(self, model: IECProgramModel, errors: List[str]) -> IECProgramModel:
        
        for error in errors:
            # Fix 1: Undeclared identifier
            if "Undeclared identifier" in error:
                # Extract variable name: "Undeclared identifier: 'VarName'"
                import re
                match = re.search(r"Undeclared identifier: '([^']+)'", error)
                if match:
                    var_name = match.group(1)
                    self._inject_variable(model, var_name)
                    
            # Fix 2: Invalid parameter (FB Signature)
            if "Invalid parameter" in error and "Did you mean" in error:
                # Extract: "Invalid parameter 'RESET' ... Did you mean 'R'?"
                match = re.search(r"Invalid parameter '([^']+)' .* Did you mean '([^']+)'", error)
                if match:
                    bad_param = match.group(1)
                    good_param = match.group(2)
                    self._fix_fb_param(model, bad_param, good_param)
                    
        return model

    def _inject_variable(self, model: IECProgramModel, var_name: str):
        # Check if already exists (case insensitive)
        existing = {v.name.upper() for v in model.inputs + model.outputs + model.internals}
        if var_name.upper() in existing:
            return

        # Heuristics
        type_ = "BOOL"
        if "STATE" in var_name.upper(): type_ = "INT"
        elif "COUNT" in var_name.upper(): type_ = "INT"
        elif "TEMP" in var_name.upper(): type_ = "REAL"
        
        model.internals.append(Variable(name=var_name, type=type_, comment="Auto-fixed (Compiler)"))

    def _fix_fb_param(self, model: IECProgramModel, bad_param: str, good_param: str):
        # Iterate recursively through logic to find FBCallBlocks
        # This is expensive but correct.
        from backend.iec_engine.model_schema import FBCallBlock, IfBlock, CaseBlock, ForBlock, WhileBlock
        
        def visit(blocks):
            for b in blocks:
                if isinstance(b, FBCallBlock):
                    # Check params
                    keys = list(b.params.keys())
                    for k in keys:
                        if k.upper() == bad_param.upper():
                            # Swap
                            val = b.params.pop(k)
                            b.params[good_param] = val
                            
                elif isinstance(b, IfBlock):
                    visit(b.then_body)
                    if b.else_body: visit(b.else_body)
                elif isinstance(b, CaseBlock):
                    for c in b.cases: visit(c.body)
                    if b.else_body: visit(b.else_body)
                elif isinstance(b, ForBlock):
                    visit(b.body)
                elif isinstance(b, WhileBlock):
                    visit(b.body)

        visit(model.logic)
