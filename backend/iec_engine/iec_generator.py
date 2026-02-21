from typing import List
from backend.iec_engine.model_schema import (
    IECProgramModel, LogicBlock, AssignBlock, IfBlock, CaseBlock, ForBlock, WhileBlock, FBCallBlock, CommentBlock
)

class IECGenerator:
    """
    Deterministically converts valid IECProgramModel into IEC 61131-3 Structured Text.
    Recursive logic handling ensures arbitrary nesting depth.
    """

    def generate(self, model: IECProgramModel) -> str:
        code = []
        
        # 1. Header
        code.append(f"PROGRAM {model.program_name}")
        
        # 2. Variable Blocks
        self._generate_var_block(code, "VAR_INPUT", model.inputs)
        self._generate_var_block(code, "VAR_OUTPUT", model.outputs)
        
        # Combine internals, timers, counters into VAR
        all_internals = model.internals[:]
        
        # Add Timers as FB instances
        for t in model.timers:
            all_internals.append({"name": t.name, "type": t.type}) # implicitly Variable-like dict works if we handle it
        
        # Add Counters as FB instances
        for c in model.counters:
             all_internals.append({"name": c.name, "type": c.type})

        self._generate_var_block(code, "VAR", all_internals) # Accepts list of Variables or dicts

        # 3. Body
        code.append("")
        for block in model.logic:
            code.extend(self._generate_logic_block(block, indent_level=1))
            
        # 4. Footer
        code.append("END_PROGRAM")
        
        return "\n".join(code)

    def _generate_var_block(self, code: List[str], block_name: str, vars: List):
        if not vars:
            return
        
        code.append(block_name)
        for v in vars:
            # Handle both Pydantic Variable obj and dict (from manual merging above)
            if hasattr(v, 'name'):
                name, type_ = v.name, v.type
                init = f" := {v.initial_value}" if v.initial_value else ""
                comment = f" (* {v.comment} *)" if v.comment else ""
            else:
                name, type_ = v['name'], v['type']
                init = "" # Simplified for timers/counters in VAR
                comment = ""

            code.append(f"    {name} : {type_}{init};{comment}")
        code.append("END_VAR")

    def _generate_logic_block(self, block: LogicBlock, indent_level: int) -> List[str]:
        lines = []
        indent = "    " * indent_level
        
        if isinstance(block, AssignBlock):
            lines.append(f"{indent}{block.variable} := {block.value};")
            
        elif isinstance(block, IfBlock):
            lines.append(f"{indent}IF {block.condition} THEN")
            for sub in block.then_body:
                lines.extend(self._generate_logic_block(sub, indent_level + 1))
            
            # TODO: Handle ELSIF if we modeled it in schema rigorously (omitted in basic generator for brevity, but schema has it)
            
            if block.else_body:
                lines.append(f"{indent}ELSE")
                for sub in block.else_body:
                    lines.extend(self._generate_logic_block(sub, indent_level + 1))
            
            lines.append(f"{indent}END_IF;")
            
        elif isinstance(block, CaseBlock):
            lines.append(f"{indent}CASE {block.expression} OF")
            for case in block.cases:
                lines.append(f"{indent}    {case.values}:")
                for sub in case.body:
                    lines.extend(self._generate_logic_block(sub, indent_level + 2))
            
            if block.else_body:
                lines.append(f"{indent}    ELSE")
                for sub in block.else_body:
                    lines.extend(self._generate_logic_block(sub, indent_level + 2))
                    
            lines.append(f"{indent}END_CASE;")

        elif isinstance(block, ForBlock):
            by_part = f" BY {block.by_value}" if block.by_value else ""
            lines.append(f"{indent}FOR {block.iterator} := {block.start_value} TO {block.end_value}{by_part} DO")
            for sub in block.body:
                 lines.extend(self._generate_logic_block(sub, indent_level + 1))
            lines.append(f"{indent}END_FOR;")
            
        elif isinstance(block, WhileBlock):
            lines.append(f"{indent}WHILE {block.condition} DO")
            for sub in block.body:
                 lines.extend(self._generate_logic_block(sub, indent_level + 1))
            lines.append(f"{indent}END_WHILE;")

        elif isinstance(block, FBCallBlock):
            # T1(IN := Start, PT := T#5s);
            param_str = ", ".join([f"{k} := {v}" for k, v in block.params.items()])
            lines.append(f"{indent}{block.name}({param_str});")

        elif isinstance(block, CommentBlock):
            lines.append(f"{indent}(* {block.text} *)")
            
        return lines
