from .strict_schema import ProgramSchema

# ---------------------------------------------------------
# LAYER 3: DETERMINISTIC STRUCTUED TEXT GENERATOR
# This engine converts the validated JSON into perfect ST.
# No AI involved here. 100% deterministic template-driven.
# ---------------------------------------------------------

class DeterministicSTGenerator:
    def __init__(self, model: ProgramSchema):
        self.model = model

    def _generate_var_block(self, var_list, block_type):
        """Generates VAR_INPUT, VAR_OUTPUT, or VAR blocks"""
        if not var_list:
            return ""
        
        lines = [f"{block_type}"]
        for v in var_list:
            init_str = f" := {v.init}" if v.init is not None else ""
            lines.append(f"    {v.name} : {v.type}{init_str};")
        lines.append("END_VAR\n")
        return "\n".join(lines)

    def _generate_fb_declarations(self):
        """Generates declarations for Timers and Counters inside VAR block"""
        lines = []
        if self.model.timers or self.model.counters:
            lines.append("VAR")
            for t in self.model.timers:
                lines.append(f"    {t.name} : {t.type};")
            for c in self.model.counters:
                lines.append(f"    {c.name} : {c.type};")
            lines.append("END_VAR\n")
        return "\n".join(lines) if lines else ""

    def _generate_timer_calls(self):
        """Generates the actual execution calls for timers"""
        lines = []
        for t in self.model.timers:
            # e.g., TMR1(IN := Start, PT := T#5s);
            lines.append(f"    {t.name}(IN := {t.in_trigger}, PT := {t.pt});")
        return "\n".join(lines)

    def _generate_counter_calls(self):
        """Generates the actual execution calls for counters"""
        lines = []
        for c in self.model.counters:
            params = []
            if c.cu: params.append(f"CU := {c.cu}")
            if c.cd: params.append(f"CD := {c.cd}")
            if c.r: params.append(f"R := {c.r}")
            params.append(f"PV := {c.pv}")
            param_str = ", ".join(params)
            lines.append(f"    {c.name}({param_str});")
        return "\n".join(lines)

    def _generate_logic(self):
        """Generates the assignment logic"""
        lines = []
        for logic in self.model.logic:
            # Ensure proper semicolon termination always
            # Strip trailing semicolons if AI accidentally included them in 'value'
            clean_val = logic.value.strip().rstrip(";")
            lines.append(f"    {logic.target} := {clean_val};")
        return "\n".join(lines) if lines else ""

    def generate(self) -> str:
        """The main builder function that guarantees ST structure."""
        
        st_parts = []
        
        # 1. Program Header
        st_parts.append(f"PROGRAM {self.model.program_name}\n")
        
        # 2. Variable Declarations
        if self.model.inputs:
            st_parts.append(self._generate_var_block(self.model.inputs, "VAR_INPUT"))
        if self.model.outputs:
            st_parts.append(self._generate_var_block(self.model.outputs, "VAR_OUTPUT"))
        if self.model.internals:
            st_parts.append(self._generate_var_block(self.model.internals, "VAR"))
        
        fb_vars = self._generate_fb_declarations()
        if fb_vars:
            st_parts.append(fb_vars)
        
        # 3. Logic Execution
        st_parts.append("\n    // --- Timer and Counter Execution ---")
        st_parts.append(self._generate_timer_calls())
        st_parts.append(self._generate_counter_calls())
        
        st_parts.append("\n    // --- Assignment Logic ---")
        st_parts.append(self._generate_logic())
        
        # 4. Program Footer
        st_parts.append("\nEND_PROGRAM\n")
        
        # Clean up empty lines
        final_st = "\n".join([line for line in "\n".join(st_parts).split("\n") if line.strip() != "" or line == ""])
        
        return final_st

# Example Usage:
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from backend.engine.strict_schema import ProgramSchema
    
    # Test with standard logic gate
    mock_json = {
        "program_name": "LogicGate",
        "inputs": [{"name": "A", "type": "BOOL"}, {"name": "B", "type": "BOOL"}],
        "outputs": [{"name": "C", "type": "BOOL"}],
        "internals": [],
        "timers": [],
        "counters": [],
        "logic": [{"type": "assign", "target": "C", "value": "A AND B"}]
    }
    
    schema = ProgramSchema(**mock_json)
    gen = DeterministicSTGenerator(schema)
    print(gen.generate())
