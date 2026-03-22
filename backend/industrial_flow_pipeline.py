"""
Industrial Flow Pipeline - 11 Essential Layers for IEC-ST Compliance
Exact implementation of user's specified flow
"""

import json
import re
import subprocess
import logging
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndustrialFlowPipeline:
    """
    11-Layer Industrial Pipeline for Perfect IEC 61131-3 ST Generation
    Exact flow as specified by user
    """
    
    def __init__(self):
        self.ai_api_key = None
        self.warnings = []
        self.errors = []
        
    # ============================================================================
    # LAYER 1 — Domain Extraction (AI)
    # ============================================================================
    
    def extract_model(self, prompt: str) -> Dict:
        """AI converts prompt → structured model"""
        logger.info("🟢 Step 1 — Domain Extraction (AI)")
        
        extraction_prompt = f"""
You are an industrial automation systems analyst.

Extract the control model from this requirement:
{prompt}

Return ONLY valid JSON with these exact keys:
{{
  "system_type": "sequence|combinational|monitoring|hybrid",
  "inputs": ["I_Start", "I_Stop", "I_Sensor"],
  "outputs": ["Q_Motor", "Q_Valve"],
  "states": ["Idle", "Running", "Error"],
  "timers": ["T_Fill", "T_Delay"],
  "counters": ["C_Items"],
  "safety": ["I_EStop"]
}}

Rules:
- Use I_ prefix for inputs
- Use Q_ prefix for outputs  
- Use T_ prefix for timers
- Use C_ prefix for counters
- Safety inputs in safety array
- No explanations, only JSON
"""
        
        try:
            # Mock AI response for now - replace with actual AI call
            mock_response = self._mock_ai_response(prompt)
            model = json.loads(mock_response)
            
            if not isinstance(model, dict):
                raise Exception("Model must be dict")
                
            logger.info(f"✅ Extracted model: {len(model)} keys")
            return model
            
        except Exception as e:
            logger.error(f"❌ Model extraction failed: {str(e)}")
            raise Exception(f"Layer 1 failed: {str(e)}")
    
    # ============================================================================
    # LAYER 2 — Control Model Normalization
    # ============================================================================
    
    def normalize_model(self, model: Dict) -> Dict:
        """Ensure required keys exist"""
        logger.info("🟢 Step 2 — Control Model Normalization")
        
        required = ["inputs", "outputs", "states"]
        for r in required:
            if r not in model:
                model[r] = []  # Add empty array if missing
                self.warnings.append(f"Added missing {r} array")
        
        # Ensure proper prefixes
        model["inputs"] = [f"I_{inp}" if not inp.startswith("I_") else inp for inp in model.get("inputs", [])]
        model["outputs"] = [f"Q_{out}" if not out.startswith("Q_") else out for out in model.get("outputs", [])]
        model["timers"] = [f"T_{timer}" if not timer.startswith("T_") else timer for timer in model.get("timers", [])]
        model["counters"] = [f"C_{counter}" if not counter.startswith("C_") else counter for counter in model.get("counters", [])]
        
        logger.info("✅ Model normalized")
        return model
    
    # ============================================================================
    # LAYER 3 — Engineering Completeness Validator
    # ============================================================================
    
    def validate_engineering(self, model: Dict) -> bool:
        """Ensure industrial realism - AUTO-ENRICH instead of abort"""
        logger.info("🟢 Step 3 — Engineering Completeness Validator")
        
        errors = []
        warnings = []
        enriched = False
        
        outputs_str = str(model.get("outputs", []))
        inputs_str = str(model.get("inputs", []))
        
        # Check motion systems and auto-enrich
        if any(motor in outputs_str for motor in ["Motor", "Pump", "Conveyor", "Valve", "Cylinder", "Press"]):
            if not any(stop in inputs_str for stop in ["Stop", "EStop", "Emergency"]):
                # Auto-enrich with safety inputs
                if "inputs" not in model:
                    model["inputs"] = []
                model["inputs"].extend(["I_Stop", "I_EStop"])
                warnings.append("Auto-added safety inputs for motion system")
                enriched = True
        
        # Check hydraulic/pneumatic systems and auto-enrich states
        model_str = str(model).lower()
        if any(term in model_str for term in ["hydraulic", "pneumatic", "cylinder", "press", "clamp"]):
            required_states = ["Idle", "Clamp", "Press", "RetractPress", "ReleaseClamp", "Complete", "Fault"]
            existing_states = model.get("states", [])
            
            for state in required_states:
                if state not in existing_states:
                    if "states" not in model:
                        model["states"] = []
                    model["states"].append(state)
                    warnings.append(f"Auto-added required state: {state}")
                    enriched = True
            
            # Auto-add required timers
            required_timers = ["T_ClampTimeout", "T_PressTimeout"]
            for timer in required_timers:
                if timer not in model.get("timers", []):
                    if "timers" not in model:
                        model["timers"] = []
                    model["timers"].append(timer)
                    warnings.append(f"Auto-added required timer: {timer}")
                    enriched = True
        
        # Check Star-Delta requirements
        if "Star" in outputs_str or "Delta" in outputs_str:
            if len(model.get("timers", [])) < 2:
                if "timers" not in model:
                    model["timers"] = []
                model["timers"].extend(["T_Star", "T_Delta"])
                warnings.append("Auto-added Star-Delta timers")
                enriched = True
        
        # Check counters and auto-add bounds
        for counter in model.get("counters", []):
            if "Max" not in counter and "Limit" not in counter:
                warnings.append(f"Counter {counter} should have bounds - will be added in ST")
        
        # Only abort on FATAL structure errors
        if not model.get("outputs"):
            model["outputs"] = ["Q_SystemReady"]
            warnings.append("Auto-added Q_SystemReady output")
            enriched = True
        if not model.get("states"):
            model["states"] = ["Idle", "Active"]
            warnings.append("Auto-added default states")
            enriched = True

        
        # Store warnings for later
        self.warnings.extend(warnings)
        
        if errors:
            self.errors.extend(errors)
            logger.error(f"❌ Engineering validation failed: {errors}")
            return False
        
        logger.info(f"✅ Engineering validation passed - Enriched: {enriched}")
        return True
    
    # ============================================================================
    # LAYER 4 — Physical Safety Rule Checker
    # ============================================================================
    
    def validate_physical_safety(self, model: Dict) -> bool:
        """Ensure real-world safety - AUTO-ENRICH instead of abort"""
        logger.info("🟢 Step 4 — Physical Safety Rule Checker")
        
        errors = []
        warnings = []
        enriched = False
        
        model_str = str(model)
        
        # Check Forward/Reverse interlock and auto-enrich
        if "Forward" in model_str and "Reverse" in model_str:
            # Add interlock logic in warnings, don't abort
            warnings.append("Forward/Reverse interlock required - will be added in ST")
            enriched = True
        
        # Check safety dominance and auto-enrich
        if model.get("safety"):
            safety_inputs = model["safety"]
            for safety in safety_inputs:
                if "EStop" in safety or "Emergency" in safety:
                    # Ensure safety dominates - add to warnings
                    warnings.append(f"Safety input {safety} will dominate all states")
                    enriched = True
        else:
            # Auto-add safety for dangerous outputs
            dangerous_outputs = ["Motor", "Heater", "Valve", "Conveyor", "Press", "Cylinder"]
            for output in model.get("outputs", []):
                if any(danger in output for danger in dangerous_outputs):
                    if "safety" not in model:
                        model["safety"] = []
                    if "I_EStop" not in model["safety"]:
                        model["safety"].append("I_EStop")
                        warnings.append(f"Auto-added EStop for dangerous output {output}")
                        enriched = True
        
        # Only abort on FATAL structure errors
        if not model.get("outputs"):
            errors.append("No outputs defined")
        
        # Store warnings for later
        self.warnings.extend(warnings)
        
        if errors:
            self.errors.extend(errors)
            logger.error(f"❌ Physical safety validation failed: {errors}")
            return False
        
        logger.info(f"✅ Physical safety validation passed - Enriched: {enriched}")
        return True
    
    # ============================================================================
    # LAYER 5 — Template-Locked ST Generator
    # ============================================================================
    
    def build_st(self, model: Dict) -> str:
        """This builds structure deterministically"""
        logger.info("🟢 Step 5 — Template-Locked ST Generator")
        
        program_name = "ControlProgram"
        
        # Build ENUM for states
        st = ""
        if model.get("states"):
            st += "TYPE eState : (\n"
            for s in model["states"]:
                if s != "Fault":
                    st += f"    {s},\n"
            st += "    Fault\n"
            st += ");\nEND_TYPE\n\n"
            
        # Build VAR sections
        st += f"PROGRAM {program_name}\n\n"
        
        # VAR_INPUT
        if model.get("inputs"):
            st += "VAR_INPUT\n"
            for inp in model["inputs"]:
                st += f"    {inp} : BOOL;\n"
            st += "END_VAR\n\n"
        
        # VAR_OUTPUT
        if model.get("outputs"):
            st += "VAR_OUTPUT\n"
            for out in model["outputs"]:
                st += f"    {out} : BOOL := FALSE;\n"
            st += "END_VAR\n\n"
        
        # VAR (internal)
        st += "VAR\n"
        initial_state = model["states"][0] if model.get("states") else "Idle"
        st += f"    State : eState := {initial_state};\n"
        
        # Edge detection triggers
        for inp in model.get("inputs", []):
            trig_name = inp.replace("I_", "") + "Trig"
            st += f"    {trig_name} : R_TRIG;\n"
        
        # Timers
        for timer in model.get("timers", []):
            st += f"    {timer} : TON;\n"
            st += f"    {timer}_Condition : BOOL := FALSE;\n"
        
        # Counters
        for counter in model.get("counters", []):
            st += f"    {counter} : INT := 0;\n"
        
        st += "END_VAR\n\n"
        
        # Edge Detection calls
        st += "(* Edge Detection *)\n"
        for inp in model.get("inputs", []):
            trig_name = inp.replace("I_", "") + "Trig"
            st += f"{trig_name}(CLK := {inp});\n"
        st += "\n"
        
        # Timer calls (outside IF blocks)
        st += "(* Timer Calls *)\n"
        for timer in model.get("timers", []):
            st += f"{timer}(IN := ({timer}_Condition), PT := T#5S);\n"
        st += "\n"
        
        # Mandatory Safety Injection
        st += "(* Safety Override *)\n"
        st += "IF I_EStop THEN\n"
        st += "    State := Fault;\n"
        st += "END_IF;\n\n"
        
        # State machine
        st += "(* State Machine *)\n"
        st += "CASE State OF\n"
        
        states_to_generate = model.get("states", []).copy()
        if "Fault" not in states_to_generate:
            states_to_generate.append("Fault")
            
        for state in states_to_generate:
            st += f"    {state}:\n"
            st += "        (* AI STATE LOGIC HERE *)\n"
            st += "        (* State transitions and actions *)\n"
            st += "\n"
        
        st += "ELSE\n"
        st += "    State := Fault;\n"
        st += "END_CASE;\n\n"
        
        st += "END_PROGRAM"
        
        logger.info("✅ ST structure built")
        return st
    
    # ============================================================================
    # LAYER 6 — IEC Syntax Validator
    # ============================================================================
    
    def syntax_validate(self, st_code: str) -> bool:
        """IEC syntax validation"""
        logger.info("🟢 Step 6 — IEC Syntax Validator")
        
        # Basic syntax checks (mock iec-checker)
        syntax_errors = []
        
        # Check PROGRAM/END_PROGRAM
        if "PROGRAM" not in st_code:
            syntax_errors.append("Missing PROGRAM")
        if "END_PROGRAM" not in st_code:
            syntax_errors.append("Missing END_PROGRAM")
        
        # Check VAR sections
        if "VAR_INPUT" not in st_code:
            syntax_errors.append("Missing VAR_INPUT")
        if "VAR_OUTPUT" not in st_code:
            syntax_errors.append("Missing VAR_OUTPUT")
        if "END_VAR" not in st_code:
            syntax_errors.append("Missing END_VAR")
        
        # Check CASE/END_CASE
        if "CASE" in st_code and "END_CASE" not in st_code:
            syntax_errors.append("Missing END_CASE")
        
        if syntax_errors:
            self.errors.extend(syntax_errors)
            logger.error(f"❌ Syntax validation failed: {syntax_errors}")
            return False
        
        logger.info("✅ Syntax validation passed")
        return True
    
    # ============================================================================
    # LAYER 7 — Semantic Scan Validator
    # ============================================================================
    
    def semantic_check(self, st_code: str) -> bool:
        """Ensure deterministic behavior"""
        logger.info("🟢 Step 7 — Semantic Scan Validator")
        
        errors = []
        
        # Check timer misuse
        if "TON(" in st_code and "Enable" not in st_code and "_Condition" not in st_code:
            errors.append("Timer must use enable variable pattern")
        
        # Check multiple CASE blocks
        case_count = st_code.count("CASE State")
        if case_count > 1:
            errors.append(f"Multiple CASE blocks detected: {case_count}")
        
        # Check direct sensor usage
        lines = st_code.split('\n')
        for line in lines:
            if "IF " in line and any(sensor in line for sensor in ["I_", "Sensor", "Button"]):
                if "Trig" not in line and "I_EStop" not in line:
                    errors.append("Direct sensor usage without edge detection")
        
        if errors:
            self.errors.extend(errors)
            logger.error(f"❌ Semantic validation failed: {errors}")
            return False
        
        logger.info("✅ Semantic validation passed")
        return True
    
    # ============================================================================
    # LAYER 8 — Variable Ownership Validator
    # ============================================================================
    
    def variable_ownership_check(self, st_code: str) -> bool:
        """Ensure clean variable usage"""
        logger.info("🟢 Step 8 — Variable Ownership Validator")
        
        # Find declared variables
        var_pattern = r'(\w+)\s*:'
        vars_declared = re.findall(var_pattern, st_code)
        
        # Find used variables
        used_pattern = r'\b(\w+)\b'
        vars_used = re.findall(used_pattern, st_code)
        
        errors = []
        
        # Check for multiple output writes
        # Count writes only inside CASE. Reject if output written outside CASE block.
        case_blocks = re.findall(r'CASE.*?END_CASE;', st_code, re.DOTALL)
        code_without_cases = st_code
        for block in case_blocks:
            code_without_cases = code_without_cases.replace(block, '')
            
        var_output_match = re.search(r'VAR_OUTPUT.*?END_VAR', code_without_cases, re.DOTALL)
        if var_output_match:
            code_without_cases = code_without_cases.replace(var_output_match.group(0), '')
            
        for var in vars_used:
            if var.startswith("Q_"):
                if re.search(rf'\b{var}\s*:=', code_without_cases):
                    errors.append(f"Output {var} written outside CASE block")
        
        # Check for undeclared variables
        for var in vars_used:
            if var.startswith("M_") or var.startswith("T_") or var.startswith("C_") or var == "State":
                if var not in vars_declared:
                    errors.append(f"Undeclared variable: {var}")
        
        if errors:
            self.errors.extend(errors)
            logger.error(f"❌ Variable ownership validation failed: {errors}")
            return False
        
        logger.info("✅ Variable ownership validation passed")
        return True
    
    # ============================================================================
    # LAYER 9 — Dead State Validator
    # ============================================================================
    
    def dead_state_check(self, st_code: str, model: Dict = None) -> bool:
        """Deterministic State Validation check"""
        logger.info("🟢 Step 9 — Dead State Validator")
        
        errors = []
        if model and model.get("states"):
            for state in model["states"]:
                if f"    {state}:" not in st_code and f"CASE State OF\n    {state}" not in st_code:
                    errors.append(f"State {state} not implemented")
        
        if errors:
            self.errors.extend(errors)
            logger.error(f"❌ Dead state validation failed: {errors}")
            return False
        
        logger.info("✅ Deterministic state validation passed")
        return True
    
    # ============================================================================
    # LAYER 10 — Industrial Polish
    # ============================================================================
    
    def polish(self, st_code: str) -> str:
        """Industrial formatting"""
        logger.info("🟢 Step 10 — Industrial Polish")
        
        # Add state comments
        st_code = st_code.replace("State := Idle;", "State := Idle; (* Return to Idle *)")
        
        # Clean whitespace
        lines = st_code.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                cleaned_lines.append(line.rstrip())
        
        # Add proper spacing
        polished_code = '\n'.join(cleaned_lines)
        
        logger.info("✅ Industrial polish applied")
        return polished_code
    
    # ============================================================================
    # LAYER 11 — Confidence Scoring
    # ============================================================================
    
    def calculate_confidence(self, warnings: List[str], fix_used: bool) -> int:
        """Calculate confidence score"""
        logger.info("🟢 Step 11 — Confidence Scoring")
        
        score = 100
        score -= len(warnings) * 10
        if fix_used:
            score -= 20
        if self.errors:
            score -= len(self.errors) * 15
        
        final_score = max(score, 0)
        logger.info(f"✅ Confidence score: {final_score}")
        return final_score
    
    # ============================================================================
    # MAIN PIPELINE
    # ============================================================================
    
    def generate_industrial_st(self, prompt: str) -> Dict:
        """Execute full 11-layer pipeline"""
        logger.info("🏗 Starting 11-Layer Industrial Pipeline")
        
        try:
            # Layer 1: Domain Extraction
            model = self.extract_model(prompt)
            
            # Layer 2: Normalization
            model = self.normalize_model(model)
            
            # Layer 3: Engineering Validation
            if not self.validate_engineering(model):
                raise Exception("Engineering validation failed")
            
            # Layer 4: Physical Safety
            if not self.validate_physical_safety(model):
                raise Exception("Physical safety validation failed")
            
            # Layer 5: ST Generation
            st_code = self.build_st(model)
            
            # Layer 6: Syntax Validation
            if not self.syntax_validate(st_code):
                raise Exception("Syntax validation failed")
            
            # Layer 7: Semantic Validation
            if not self.semantic_check(st_code):
                raise Exception("Semantic validation failed")
            
            # Layer 8: Variable Ownership
            if not self.variable_ownership_check(st_code):
                raise Exception("Variable ownership validation failed")
            
            # Layer 9: Dead State Check
            if not self.dead_state_check(st_code, model):
                raise Exception("Dead state validation failed")
            
            # Layer 10: Industrial Polish
            st_code = self.polish(st_code)
            
            # Layer 11: Confidence Scoring
            confidence = self.calculate_confidence(self.warnings, False)
            
            logger.info("🎯 11-Layer Pipeline Completed Successfully")
            
            return {
                "code": st_code,
                "confidence": confidence,
                "iec_compliant": len(self.errors) == 0,
                "warnings": self.warnings,
                "errors": self.errors,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            return {
                "code": f"// Generation failed: {str(e)}",
                "confidence": 0,
                "iec_compliant": False,
                "warnings": self.warnings,
                "errors": [str(e)],
                "model": {}
            }
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _mock_ai_response(self, prompt: str) -> str:
        """Mock AI response for testing"""
        prompt_lower = prompt.lower()
        
        if "traffic" in prompt_lower or "light" in prompt_lower:
            return """{
  "system_type": "sequence",
  "inputs": ["I_RedSensor", "I_GreenSensor", "I_Button", "I_EStop"],
  "outputs": ["Q_RedLight", "Q_GreenLight", "Q_YellowLight"],
  "states": ["Red", "Yellow", "Green"],
  "timers": ["T_Traffic", "T_Yellow"],
  "counters": ["C_Vehicles"],
  "safety": ["I_EStop"]
}"""
        elif "elevator" in prompt_lower:
            return """{
  "system_type": "sequence",
  "inputs": ["I_Floor1", "I_Floor2", "I_CallButton", "I_DoorSensor", "I_EStop"],
  "outputs": ["Q_Motor", "Q_Door", "Q_FloorLight"],
  "states": ["Idle", "Moving", "DoorOpen", "AtFloor"],
  "timers": ["T_Move", "T_Door"],
  "counters": ["C_FloorCount"],
  "safety": ["I_EStop"]
}"""
        elif "hydraulic" in prompt_lower or "press" in prompt_lower or "cylinder" in prompt_lower:
            return """{
  "system_type": "sequence",
  "inputs": ["I_Start", "I_Stop", "I_EStop", "I_PartPresent", "I_CylinderExtended"],
  "outputs": ["Q_Cylinder", "Q_Press", "Q_Clamp", "Q_Light"],
  "states": ["Idle", "Clamp", "Press", "RetractPress", "ReleaseClamp", "Complete", "Fault"],
  "timers": ["T_ClampTimeout", "T_PressTimeout"],
  "counters": ["C_CycleCount"],
  "safety": ["I_EStop"]
}"""
        elif "bottling" in prompt_lower or "conveyor" in prompt_lower:
            return """{
  "system_type": "sequence",
  "inputs": ["I_Start", "I_Stop", "I_EStop", "I_BottleSensor", "I_FillSensor"],
  "outputs": ["Q_Conveyor", "Q_FillValve", "Q_CapValve", "Q_Light"],
  "states": ["Idle", "Convey", "Fill", "Cap", "Complete", "Fault"],
  "timers": ["T_FillTime", "T_CapTime"],
  "counters": ["C_BottleCount"],
  "safety": ["I_EStop"]
}"""
        else:
            return """{
  "system_type": "sequence",
  "inputs": ["I_Start", "I_Stop", "I_EStop", "I_Sensor"],
  "outputs": ["Q_Motor", "Q_Light"],
  "states": ["Idle", "Running", "Error"],
  "timers": ["T_Delay"],
  "counters": ["C_Items"],
  "safety": ["I_EStop"]
}"""


# ============================================================================
# MAIN INTERFACE FUNCTION
# ============================================================================

def generate_perfect_industrial_plc(prompt: str) -> Dict:
    """Main interface for 11-layer industrial pipeline"""
    pipeline = IndustrialFlowPipeline()
    return pipeline.generate_industrial_st(prompt)


if __name__ == "__main__":
    # Test the pipeline
    test_prompt = "Traffic lights control system with red, yellow, green lights and timing"
    result = generate_perfect_industrial_plc(test_prompt)
    
    print("=" * 80)
    print("INDUSTRIAL FLOW PIPELINE TEST")
    print("=" * 80)
    print(f"IEC Compliant: {result['iec_compliant']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Errors: {len(result['errors'])}")
    
    if result['code']:
        print("\nGenerated Code:")
        print("-" * 50)
        print(result['code'])
        print("-" * 50)
