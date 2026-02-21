"""
Three-Level Validation Pipeline for IEC 61131-3 PLC Code
Level 1: Syntax Validation
Level 2: Structure Validation  
Level 3: IEC Standard Compliance
"""
import re
from typing import Dict, List, Tuple

class ThreeLevelValidator:
    """Three-level validation pipeline ensuring IEC 61131-3 compliance"""
    
    # =========================================================================
    # LEVEL 1: SYNTAX VALIDATION
    # =========================================================================
    @staticmethod
    def level_1_syntax_check(code: str, language: str = "ST") -> Dict:
        """
        Level 1: Check basic syntax correctness
        - Brackets/parenthesis balance
        - Quote matching
        - Comment syntax
        """
        issues = []
        warnings = []
        
        # Check parenthesis balance
        paren_open = code.count('(')
        paren_close = code.count(')')
        if paren_open != paren_close:
            issues.append(f"Parenthesis mismatch: {paren_open} open vs {paren_close} close")
        
        # Check bracket balance
        bracket_open = code.count('[')
        bracket_close = code.count(']')
        if bracket_open != bracket_close:
            issues.append(f"Bracket mismatch: {bracket_open} open vs {bracket_close} close")
        
        # Check curly brace balance
        brace_open = code.count('{')
        brace_close = code.count('}')
        if brace_open != brace_close:
            issues.append(f"Brace mismatch: {brace_open} open vs {brace_close} close")
        
        # Check for proper string quotes (basic check)
        if language == "ST":
            # ST uses single quotes for strings
            single_quotes = code.count("'")
            if single_quotes % 2 != 0:
                warnings.append("Odd number of single quotes - possible unterminated string")
        
        # Check for empty code
        if not code or len(code.strip()) < 5:
            issues.append("Code is empty or too short")
        
        return {
            "level": 1,
            "name": "Syntax Validation",
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "critical": len(issues) > 0
        }
    
    # =========================================================================
    # LEVEL 2: STRUCTURE VALIDATION
    # =========================================================================
    @staticmethod
    def level_2_structure_check(code: str, language: str = "ST") -> Dict:
        """
        Level 2: Check code structure
        - Program/Function declarations
        - Variable sections
        - Block completeness
        - Variable initialization
        """
        issues = []
        warnings = []
        
        code_upper = code.upper()
        
        if language == "ST":
            # Check 1: Program or Function Block declaration
            has_program = "PROGRAM" in code_upper
            has_fb = "FUNCTION_BLOCK" in code_upper
            has_function = "FUNCTION" in code_upper and not has_fb
            
            if not (has_program or has_fb or has_function):
                issues.append("Missing PROGRAM, FUNCTION_BLOCK, or FUNCTION declaration")
            
            # Check 2: Proper block termination
            if has_program and "END_PROGRAM" not in code_upper:
                issues.append("PROGRAM declared but missing END_PROGRAM")
            if has_fb and "END_FUNCTION_BLOCK" not in code_upper:
                issues.append("FUNCTION_BLOCK declared but missing END_FUNCTION_BLOCK")
            if has_function and "END_FUNCTION" not in code_upper:
                issues.append("FUNCTION declared but missing END_FUNCTION")
            
            # Check 3: Variable Declaration Section
            if "VAR" not in code_upper:
                issues.append("Missing VAR section for variable declarations")
            elif "END_VAR" not in code_upper:
                issues.append("VAR section declared but missing END_VAR")
            
            # Check 4: Variables have types
            var_match = re.search(r'VAR\s+(.*?)\s+END_VAR', code_upper, re.DOTALL)
            if var_match:
                var_section = var_match.group(1)
                # Each variable line should have : for type declaration
                var_lines = [line.strip() for line in var_section.split('\n') if line.strip()]
                untyped_vars = [line for line in var_lines if line and ':' not in line and not line.startswith('(*')]
                if untyped_vars:
                    issues.append(f"Variables without type declarations found: {len(untyped_vars)} variable(s)")
            
            # Check 5: Variable initialization
            if ":=" not in code:
                warnings.append("No variable initialization found - variables should have default values")
            
            # Check 6: Main logic exists (between BEGIN or after VAR)
            main_logic = code.split("END_VAR")[-1] if "END_VAR" in code else code
            if not main_logic or len(main_logic.strip()) < 5:
                issues.append("No main logic found after variable declarations")
        
        return {
            "level": 2,
            "name": "Structure Validation",
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "critical": len(issues) > 0
        }
    
    # =========================================================================
    # LEVEL 3: IEC 61131-3 COMPLIANCE CHECK
    # =========================================================================
    @staticmethod
    def level_3_iec_compliance_check(code: str, language: str = "ST") -> Dict:
        """
        Level 3: Check IEC 61131-3 standard compliance
        - Edge detection for inputs (R_TRIG)
        - Boundary checks for counters (CRITICAL)
        - Proper timer usage (TON, TOF)
        - Data type correctness
        - Safety best practices
        - LOGICAL CORRECTNESS (increment/decrement guards)
        """
        issues = []
        warnings = []
        recommendations = []
        
        code_lower = code.lower()
        code_upper = code.upper()
        
        if language == "ST":
            # Check 1: Input handling with edge detection
            if any(word in code_lower for word in ['input', 'sensor', 'button', 'switch', 'entry', 'exit']):
                if 'r_trig' not in code_lower:
                    issues.append("Input signals detected but no R_TRIG (Rising Edge) found - CRITICAL for scan-safe logic")
                    recommendations.append("Use R_TRIG function block for all physical digital inputs to prevent multiple triggers per scan")
            
            # Check 2: CRITICAL - Counter increment guards
            # Pattern: increment without boundary check
            increment_patterns = [
                r'counter\s*:=\s*counter\s*\+\s*1',
                r'count\s*:=\s*count\s*\+\s*1',
                r'accumulator\s*:=\s*accumulator\s*\+\s*1',
                r'car_count\s*:=\s*car_count\s*\+\s*1'
            ]
            
            for pattern in increment_patterns:
                if re.search(pattern, code_lower):
                    # Check if there's a guard condition
                    has_guard = re.search(
                        r'IF\s+\w+\s*<\s*\w+.*?\n.*?:=.*?\+\s*1',
                        code_lower,
                        re.DOTALL
                    )
                    if not has_guard:
                        # Check for MAX_CAPACITY or similar
                        if 'max' not in code_lower or '<' not in code:
                            issues.append("❌ CRITICAL: Counter increment without boundary guard - will overflow at limit")
                            recommendations.append("MUST check: IF counter < MAX_CAPACITY THEN increment END_IF;")
            
            # Check 3: CRITICAL - Counter decrement guards
            decrement_patterns = [
                r'counter\s*:=\s*counter\s*-\s*1',
                r'count\s*:=\s*count\s*-\s*1',
                r'accumulator\s*:=\s*accumulator\s*-\s*1',
                r'car_count\s*:=\s*car_count\s*-\s*1'
            ]
            
            for pattern in decrement_patterns:
                if re.search(pattern, code_lower):
                    # Check if there's a guard condition
                    has_guard = re.search(
                        r'IF\s+\w+\s*>\s*0.*?\n.*?:=.*?-\s*1',
                        code_lower,
                        re.DOTALL
                    )
                    if not has_guard:
                        # Check for boundary check
                        if code.count('>') == 0:
                            issues.append("❌ CRITICAL: Counter decrement without zero guard - will go negative")
                            recommendations.append("MUST check: IF counter > 0 THEN decrement END_IF;")
            
            # Check 4: Post-increment clamping (bad practice)
            if 'car_count := car_count + 1' in code and ':= 0' in code and '<' in code:
                # This suggests increment then clamp pattern
                clamp_patterns = [
                    r'IF\s+\w+\s*>=\s*\w+.*?:=\s*\w+',  # Clamping after increment
                ]
                for clamping in clamp_patterns:
                    if re.search(clamping, code_lower):
                        issues.append("❌ DESIGN ISSUE: Code allows invalid state then corrects it - illogical for industrial systems")
                        recommendations.append("Guard the operation BEFORE: IF entry_pulse.Q AND car_count < MAX THEN increment END_IF;")
            
            # Check 5: Timer usage
            if any(word in code_lower for word in ['delay', 'wait', 'timer', 'timeout']):
                has_proper_timers = 'ton' in code_lower or 'tof' in code_lower or 'tp' in code_lower
                if not has_proper_timers:
                    issues.append("Timing operation detected but no IEC timer (TON/TOF/TP) found")
                    recommendations.append("Use TON (Timer-On-Delay), TOF (Timer-Off-Delay), or TP (Pulse Timer) function blocks")
            
            # Check 6: Output handling
            if any(word in code_lower for word in ['output', 'motor', 'light', 'pump', 'valve']):
                output_lines = [line for line in code.split('\n') if any(
                    word in line.lower() for word in ['output', 'motor', 'light', 'pump', 'valve']
                ) and ':=' in line]
                if not output_lines:
                    warnings.append("Output variables declared but no assignments found")
                    recommendations.append("Ensure all outputs are explicitly assigned in the logic section")
            
            # Check 7: Variable naming convention (snake_case recommended)
            var_section = code.split('END_VAR')[0] if 'END_VAR' in code else ""
            bad_names = re.findall(r'\b([A-Z]+[a-z]*[A-Z][a-zA-Z]*)\b', var_section)
            if bad_names:
                recommendations.append(f"Consider using snake_case for variable names: {', '.join(set(bad_names[:3]))}")
            
            # Check 8: Comment density
            comment_count = code.count('(*') + code.count('--')
            code_lines = len([l for l in code.split('\n') if l.strip()])
            if code_lines > 20 and comment_count < 2:
                recommendations.append("Add comments explaining the logic (one per 10 lines minimum)")
            
            # Check 9: Forbidden patterns
            forbidden_patterns = {
                r'\bWAIT\b': "WAIT statement is not allowed in IEC ST - use TON/TOF timers instead",
                r'\bSLEEP\b': "SLEEP is not part of IEC ST - use timers for delays",
                r'\bGOTO\b': "GOTO is deprecated in IEC ST - use proper control structures",
            }
            
            for pattern, message in forbidden_patterns.items():
                if re.search(pattern, code_upper):
                    issues.append(f"❌ Non-compliant: {message}")
        
        return {
            "level": 3,
            "name": "IEC 61131-3 Compliance",
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "critical": len(issues) > 0
        }
    
    # =========================================================================
    # MAIN VALIDATION PIPELINE
    # =========================================================================
    @staticmethod
    def validate_all_levels(code: str, language: str = "ST") -> Dict:
        """
        Run all three validation levels and return comprehensive report
        """
        level_1 = ThreeLevelValidator.level_1_syntax_check(code, language)
        level_2 = ThreeLevelValidator.level_2_structure_check(code, language)
        level_3 = ThreeLevelValidator.level_3_iec_compliance_check(code, language)
        
        all_passed = level_1["passed"] and level_2["passed"] and level_3["passed"]
        critical_issues = any([level_1["critical"], level_2["critical"], level_3["critical"]])
        
        all_issues = level_1["issues"] + level_2["issues"] + level_3["issues"]
        all_warnings = level_1["warnings"] + level_2["warnings"] + level_3["warnings"]
        all_recommendations = level_3.get("recommendations", [])
        
        return {
            "overall_passed": all_passed,
            "critical_issues": critical_issues,
            "total_issues": len(all_issues),
            "total_warnings": len(all_warnings),
            "total_recommendations": len(all_recommendations),
            "all_issues": all_issues,
            "all_warnings": all_warnings,
            "all_recommendations": all_recommendations,
            "levels": {
                "level_1_syntax": level_1,
                "level_2_structure": level_2,
                "level_3_iec_compliance": level_3
            },
            "validation_passed": all_passed and not critical_issues,
            "summary": f"Syntax: {'✓' if level_1['passed'] else '✗'} | Structure: {'✓' if level_2['passed'] else '✗'} | IEC: {'✓' if level_3['passed'] else '✗'}"
        }

# Singleton instance
validator = ThreeLevelValidator()
