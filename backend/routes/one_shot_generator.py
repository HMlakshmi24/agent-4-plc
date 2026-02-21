"""
One-Attempt Logic-Only Generator
Implementation of Strict Structure Control.
"""

import json
import re
from openai import OpenAI
import os
from backend.routes.plc_templates import get_strict_skeleton
from backend.routes.iec_validator import IECValidator

# Load Brand Rules
RULES_PATH = Path(__file__).parent.parent / "data" / "brand_rules.json"
try:
    with open(RULES_PATH, "r") as f:
        BRAND_RULES = json.load(f)
except Exception as e:
    print(f"Error loading brand rules: {e}")
    BRAND_RULES = {}

class OneShotGenerator:
    """
    Generates PLC code by asking LLM ONLY for logic/vars, 
    then assembling into a strict backend-controlled skeleton.
    """
    
    def __init__(self):
        # Local or default client
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _get_brand_rules(self, brand: str) -> dict:
        return BRAND_RULES.get(brand.lower(), BRAND_RULES.get("generic", {}))

    def _build_logic_prompt(self, requirement: str, brand: str, language: str) -> str:
        """
        Asks ONLY for variable definitions and logic body.
        Crucially, does NOT ask for PROGRAM/END_PROGRAM or VAR blocks wrappers.
        """
        rules = self._get_brand_rules(brand)
        
        siemens_specifics = ""
        if "siemens" in brand.lower():
            siemens_specifics = """
SIEMENS SCL RULES (CRITICAL):
1. TIMERS: Must be called OUTSIDE of IF/CASE statements.
   - Wrong: IF Cond THEN MyTimer(IN:=TRUE...); END_IF;
   - Correct: MyTimer(IN:=Cond, PT:=T#5s);
2. EDGE DETECTION: Use R_TRIG for all input events (counting, toggling).
   - Wrong: IF Sensor THEN Count := Count + 1; END_IF;
   - Correct: Trig(CLK:=Sensor); IF Trig.Q THEN Count := Count + 1; END_IF;
3. SEMICOLONS: Ensure strict usage, e.g., END_IF;
4. ASSIGNMENT: Explicitly assign outputs every scan (Backend will handle default reset, you handle logic).
"""

        return f"""
You are an expert {brand} PLC Engineer.
Generate ONLY the internal variable definitions and the logic body for the following requirement.

TARGET: {brand} {language}
REQUIREMENT: {requirement}

RULES:
1. Do NOT write PROGRAM or END_PROGRAM.
2. Do NOT write VAR_INPUT or VAR_OUTPUT blocks (I will handle structure).
3. Generate content for these specific sections using the delimiters below.
4. Syntax: {rules.get('standard', 'IEC 61131-3')} compliant.
{siemens_specifics}

OUTPUT FORMAT (Strictly follow this):

[INPUTS]
(List input variables here, e.g., START_BTN : BOOL;)

[OUTPUTS]
(List output variables here with types. Do NOT assign values here.)

[INTERNALS]
(List internal variables here: R_TRIG, TON, State variables.)

[LOGIC]
(Write the main logic code here. Do not include VAR/END_VAR tags. Just code.)
"""

    def _parse_sections(self, raw_output: str) -> dict:
        """
        Parses the LLM output into sections.
        """
        sections = {
            "inputs": "",
            "outputs": "",
            "internals": "",
            "logic": ""
        }
        
        current_section = None
        lines = raw_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if line == "[INPUTS]":
                current_section = "inputs"
                continue
            elif line == "[OUTPUTS]":
                current_section = "outputs"
                continue
            elif line == "[INTERNALS]":
                current_section = "internals"
                continue
            elif line == "[LOGIC]":
                current_section = "logic"
                continue
            
            if current_section and line:
                sections[current_section] += line + "\n"
                
        return sections

    def _generate_output_reset(self, outputs_str: str, brand_rules: dict) -> str:
        """
        Auto-generates strict safety reset logic for outputs.
        """
        if not brand_rules.get("require_output_reset", False):
            return "(* Output reset not enforced for this brand *)"
            
        reset_lines = []
        # Parse variable declarations: "Name : Type;" or "Name : Type := Val;"
        # We generally want to reset BOOLs to FALSE.
        # Regex matches "VarName : BOOL" (case insensitive)
        
        lines = outputs_str.split('\n')
        for line in lines:
            line = line.strip()
            # Remove comments
            line = re.sub(r'\(.*?\)', '', line)
            line = re.sub(r'//.*', '', line)
            
            if ":" in line:
                parts = line.split(":")
                possible_names = parts[0].split(",") # Handle "A, B : BOOL"
                type_part = parts[1].strip().upper()
                
                # Check if it's a BOOL or distinct type
                if "BOOL" in type_part:
                    for name in possible_names:
                        var_name = name.strip()
                        if var_name:
                            reset_lines.append(f"{var_name} := FALSE;")
                # Can add specific resets for INT/REAL if needed, but safer to leave alone if unsure
        
        if not reset_lines:
            return "(* Non-BOOL outputs or parse error: No automatic reset generated *)"
            
        return "(* STRICT OUTPUT RESET START *)\n" + "\n".join(reset_lines) + "\n(* STRICT OUTPUT RESET END *)"

    def generate(self, requirement: str, brand: str = "generic", language: str = "ST") -> dict:
        """
        Execute strict generation flow.
        """
        # 1. Build Prompt
        user_prompt = self._build_logic_prompt(requirement, brand, language)
        
        # 2. Call LLM (Logic only)
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strict logic generator. Output only the requested sections."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            raw_response = resp.choices[0].message.content
            
            # 3. Parse Response
            parts = self._parse_sections(raw_response)
            
            # 4. Load Rules & Skeleton
            rules = self._get_brand_rules(brand)
            skeleton = get_strict_skeleton(language)
            
            # 5. Auto-Generate Helpers
            output_reset = self._generate_output_reset(parts["outputs"], rules)
            
            # 6. Assembly
            program_name = "Main_Control" # Could extract from req or random
            
            if language.upper() == "ST":
                final_code = skeleton.format(
                    program_name=program_name,
                    input_vars=parts["inputs"].strip(),
                    output_vars=parts["outputs"].strip(),
                    internal_vars=parts["internals"].strip(),
                    output_reset=output_reset,
                    main_logic=parts["logic"].strip()
                )
            else:
                # Fallback for LD (basic injection)
                final_code = f"(* Generated {language} *)\n" + raw_response

            # 7. Zero-Token Validation
            validator = IECValidator(brand)
            val_result = validator.validate(final_code)
            
            return {
                "code": final_code,
                "validated": val_result["valid"],
                "errors": val_result["errors"],
                "warnings": val_result["warnings"],
                "method": "Strict Structure Control"
            }

        except Exception as e:
            return {
                "code": "",
                "validated": False,
                "errors": [f"Generation failed: {str(e)}"],
                "warnings": [],
                "method": "Failed"
            }
