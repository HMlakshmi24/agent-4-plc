
"""
Strict HMI System Module
Provides system prompts and validation for HMI generation.
"""

import re

HMI_SYSTEM_PROMPT = """You are an Expert HMI/SCADA Developer.
Your task is to generate a professional HMI screen definition and tag mapping for a web-based interface.

OUTPUT FORMAT:
Generate a complete, self-contained HTML file with embedded CSS and JavaScript.
The HMI should look modern, industrial, and responsive.

CRITICAL REQUIREMENTS:
1. VISUAL STYLE:
   - Use a dark industrial theme (dark grey background, high contrast controls).
   - Use CSS for styling buttons, lamps, and displays to look like real industrial components.
   - Layout should be clean and grid-based.

2. CONTROLS & INDICATORS:
   - Start/Stop Buttons: Green for Start, Red for Stop.
   - Pilot Lights: Green for Run, Red for Fault, Yellow for Warning.
   - Numeric Displays: For analog values (e.g., Temperature, Level).
   - Tank/Pipe Visuals: Use simple CSS shapes or SVG if needed.

3. JAVASCRIPT LOGIC:
   - Include a simple simulation in <script> tags to demonstrate interactivity.
   - For example, clicking Start should toggle the Run state and light up the Run lamp.
   - Sliders should update numeric displays.

4. SAFETY:
   - Include an Emergency Stop button that is always visible and accessible.

5. TAGGING (Comments):
   - Add comments in the HTML indicating which PLC tags map to which elements.
   - Example: <!-- PLC_TAG: Motor_Start_Cmd -->

Generate the HTML code now based on the user's requirements.
"""

class StrictHMIValidator:
    """
    Validator for HMI HTML code.
    Checks for basic structure, script safety, and required elements.
    """
    
    @staticmethod
    def validate(code: str) -> tuple[bool, list[str]]:
        """
        Validate the generated HMI code.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check 1: HTML Structure
        if "<html" not in code.lower() or "</html>" not in code.lower():
            errors.append("Missing <html> tags")
        if "<body" not in code.lower():
            errors.append("Missing <body> tags")
            
        # Check 2: Script Safety (Basic)
        if "<script" in code.lower():
            # Ensure no external scripts are loaded (except maybe known CDNs, but ideally self-contained)
            # This is a loose check for now
            pass
            
        # Check 3: Essential UI Elements
        if "button" not in code.lower() and "input" not in code.lower():
            errors.append("No interactive elements (buttons/inputs) found")
            
        # Check 4: Styles
        if "<style" not in code.lower():
            errors.append("No embedded CSS found")

        is_valid = len(errors) == 0
        return is_valid, errors
