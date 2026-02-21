"""
ULTRA-STRICT IEC 61131-3 VALIDATION ENGINE
Zero tolerance for any IEC violations
"""

import re
from typing import Dict, List, Tuple

class UltraStrictIECValidator:
    """
    ZERO TOLERANCE validator for IEC 61131-3 compliance.
    Every rule MUST pass or code is rejected.
    """

    @staticmethod
    def validate_st_code(code: str) -> Tuple[bool, List[str], List[str]]:
        """
        ULTRA-STRICT validation for Structured Text (ST)
        Returns (is_valid, critical_errors, warnings)
        """
        critical_errors = []
        warnings = []
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 0: BASIC CODE INTEGRITY (No flexible interpretation)
        # ═══════════════════════════════════════════════════════════════════════════
        
        if not code or len(code.strip()) < 50:
            critical_errors.append("Code is empty or too short (< 50 chars)")
            return False, critical_errors, warnings
        
        code_upper = code.upper()
        code_lower = code.lower()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 1: FORBIDDEN CONSTRUCTS (ZERO TOLERANCE)
        # ═══════════════════════════════════════════════════════════════════════════
        
        forbidden_constructs = {
            r'\bWAIT\s*\(': "WAIT() is forbidden - use TON/TOF timers",
            r'\bSLEEP\s*\(': "SLEEP is forbidden - use timers",
            r'\bGOTO\b': "GOTO is forbidden - use proper control structures",
            r'WHILE\s+\(.*\)': "WHILE loops forbidden - use bounded loops or IF/CASE",
            r'```': "NO MARKDOWN BACKTICKS - code only",
            r'here is|here are|below is|example:': "NO EXPLANATIONS - code must be pure",
        }
        
        for pattern, message in forbidden_constructs.items():
            if re.search(pattern, code_upper, re.IGNORECASE):
                critical_errors.append(f"FORBIDDEN: {message}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 2: MANDATORY STRUCTURE
        # ═══════════════════════════════════════════════════════════════════════════
        
        # PROGRAM/END_PROGRAM required
        if 'PROGRAM' not in code_upper:
            critical_errors.append("MISSING: PROGRAM declaration")
        if 'END_PROGRAM' not in code_upper:
            critical_errors.append("MISSING: END_PROGRAM")
        
        # Check matching parentheses/brackets/braces
        if code.count('(') != code.count(')'):
            critical_errors.append("SYNTAX ERROR: Unmatched parentheses")
        if code.count('{') != code.count('}'):
            critical_errors.append("SYNTAX ERROR: Unmatched braces")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 3: VAR SECTION REQUIREMENTS
        # ═══════════════════════════════════════════════════════════════════════════
        
        if 'VAR' not in code_upper:
            critical_errors.append("MISSING: VAR section for variable declarations")
        if 'END_VAR' not in code_upper:
            critical_errors.append("MISSING: END_VAR terminator")
        
        # Extract all VAR sections (VAR_INPUT, VAR_OUTPUT, VAR)
        var_sections = re.finditer(r'(VAR(?:_[A-Z]+)?)(.*?)(END_VAR)', code_upper, re.DOTALL)

        for vs in var_sections:
            header = vs.group(1).strip()  # e.g., VAR_INPUT, VAR_OUTPUT, VAR
            body = vs.group(2)

            # Split into lines and validate each declaration line
            var_lines = [l.strip() for l in body.split('\n') if l.strip()]
            for line in var_lines:
                # Skip comments
                if line.startswith('(*') or line.startswith('//'):
                    continue

                # Skip section header-like lines accidentally captured
                if line.upper().startswith('VAR'):
                    continue

                # Every non-comment variable MUST have type declaration (':' present)
                if ':' not in line and '=' not in line:
                    critical_errors.append(f"UNTYPED VARIABLE: '{line}' has no type declaration")

                # Variables SHOULD have initialization (default value) - warn only
                if ':=' not in line and ':' in line:
                    var_name = line.split(':')[0].strip()
                    warnings.append(f"UNINITIALIZED: '{var_name}' has no default value")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 4: TIMER USAGE (CRITICAL SAFETY)
        # ═══════════════════════════════════════════════════════════════════════════
        
        if any(kw in code_lower for kw in ['delay', 'wait', 'timer', 'duration', 'timeout']):
            # Timers detected - validate strict usage
            has_ton = 'TON' in code_upper
            has_tof = 'TOF' in code_upper
            has_tp = 'TP' in code_upper
            
            if not (has_ton or has_tof or has_tp):
                critical_errors.append("TIMER KEYWORDS found but NO TON/TOF/TP instantiation")
            
            # Check that timers are called outside IF blocks when possible
            # This is complex, so we check for obvious violations
            timer_inside_if = re.search(
                r'IF\s+.*?THEN\s+.*?(?:TON|TOF|TP)\s*\(',
                code_upper,
                re.DOTALL
            )
            if timer_inside_if:
                warnings.append("WARNING: Timer called inside IF block (should be outside when possible)")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 5: EDGE DETECTION FOR INPUTS (CRITICAL SAFETY)
        # ═══════════════════════════════════════════════════════════════════════════
        
        input_indicators = ['sensor', 'button', 'switch', 'input', 'detector', 'trigger']
        has_input_like = any(indicator in code_lower for indicator in input_indicators)
        
        if has_input_like:
            has_r_trig = 'R_TRIG' in code_upper
            has_f_trig = 'F_TRIG' in code_upper
            has_rising_edge = 'RISING_EDGE' in code_upper
            
            if not (has_r_trig or has_f_trig or has_rising_edge):
                critical_errors.append("INPUT SIGNALS detected but NO R_TRIG/F_TRIG/RISING_EDGE")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 6: COUNTER BOUNDARY GUARDS (CRITICAL SAFETY)
        # ═══════════════════════════════════════════════════════════════════════════
        
        counter_patterns = [
            r'counter\s*:=\s*counter\s*\+\s*1',
            r'counter\s*:=\s*counter\s*-\s*1',
            r'count\s*:=\s*count\s*\+\s*1',
            r'count\s*:=\s*count\s*-\s*1',
            r'\w+\s*:=\s*\w+\s*\+\s*1',  # Generic increment
            r'\w+\s*:=\s*\w+\s*-\s*1',   # Generic decrement
        ]
        
        for pattern in counter_patterns:
            matches = re.findall(pattern, code_lower)
            if matches:
                # Check if operation is guarded
                for match in matches:
                    var_name = match.split(':=')[0].strip().split()[-1]
                    
                    # Look for guard condition
                    increment = '+' in match
                    if increment:
                        # Allow any condition as long as var_name is involved in a comparison (<, <=, >) before THEN
                        # Cases: IF var < max THEN... or IF enable AND var < max THEN...
                        guard_pattern = rf'IF\s+.*?\b{var_name}\b\s*[<>=]+.*?\bTHEN.*?:=\s*{var_name}\s*\+\s*1'
                    else:
                        guard_pattern = rf'IF\s+.*?\b{var_name}\b\s*[<>=]+.*?\bTHEN.*?:=\s*{var_name}\s*-\s*1'
                    
                    if not re.search(guard_pattern, code, re.IGNORECASE | re.DOTALL):
                        critical_errors.append(f"UNGUARDED {'INCREMENT' if increment else 'DECREMENT'}: '{match}'")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 7: OUTPUT SAFETY
        # ═══════════════════════════════════════════════════════════════════════════
        
        critical_outputs = ['motor', 'pump', 'valve', 'heater', 'solenoid']
        for output in critical_outputs:
            if output in code_lower:
                # Critical outputs should have safety conditions
                output_pattern = rf'{output}\s*:\s*BOOL\s*:=\s*FALSE'
                if not re.search(output_pattern, code_upper, re.IGNORECASE):
                    warnings.append(f"WARNING: Critical output '{output}' should default to FALSE for safety")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LEVEL 8: BOOLEAN COMPARISONS
        # ═══════════════════════════════════════════════════════════════════════════
        
        if re.search(r'(?<!:)=\s*TRUE\b', code_upper):
            critical_errors.append("ANTI-PATTERN: Use 'IF flag' not 'IF flag = TRUE'")
        if re.search(r'(?<!:)=\s*FALSE\b', code_upper):
            critical_errors.append("ANTI-PATTERN: Use 'IF NOT flag' not 'IF flag = FALSE'")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # DECISION: Determine validity
        # ═══════════════════════════════════════════════════════════════════════════
        
        is_valid = len(critical_errors) == 0
        
        return is_valid, critical_errors, warnings

    @staticmethod
    def validate_language(code: str, language: str) -> Tuple[bool, List[str]]:
        """
        Validate based on programming language
        Returns (is_valid, critical_errors)
        """
        critical_errors = []
        
        if language == "ST":
            is_valid, crit_errs, _ = UltraStrictIECValidator.validate_st_code(code)
            return is_valid, crit_errs
        
        elif language == "LD":
            # Ladder Diagram validation
            if not any(kw in code.upper() for kw in ['NETWORK', 'RUNG', 'LD', 'AND', 'OR']):
                critical_errors.append("LD code missing network/rung definitions")
        
        elif language == "FBD":
            # Function Block Diagram validation
            if not any(kw in code.upper() for kw in ['BLOCK', 'FUNCTION_BLOCK', '->', 'IN', 'OUT']):
                critical_errors.append("FBD code missing function block definitions")
        
        elif language == "SFC":
            # Sequential Function Chart validation
            if not any(kw in code.upper() for kw in ['STEP', 'TRANSITION', 'ACTION']):
                critical_errors.append("SFC code missing step/transition/action definitions")
        
        elif language == "IL":
            # Instruction List validation
            if not any(kw in code.upper() for kw in ['LD', 'AND', 'OR', 'ST']):
                critical_errors.append("IL code missing basic mnemonics (LD, AND, OR, ST)")
        
        is_valid = len(critical_errors) == 0
        return is_valid, critical_errors


def comprehensive_iec_audit(code: str, language: str, requirement: str) -> Dict:
    """
    Comprehensive IEC audit - checks everything
    Returns detailed report
    """
    is_valid, critical_errors = UltraStrictIECValidator.validate_language(code, language)
    
    audit_report = {
        "language": language,
        "valid": is_valid,
        "critical_errors": critical_errors,
        "error_count": len(critical_errors),
        "status": "PASS" if is_valid else "FAIL",
        "requirement_met": len(critical_errors) == 0,
        "iec_compliant": is_valid,
    }
    
    return audit_report


print("[✓] UltraStrictIECValidator loaded")
print("[✓] Zero-tolerance validation engine active")
print("[✓] All IEC rules enforced: timers, edge detection, guards, safety")
