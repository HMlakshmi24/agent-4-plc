"""
Ultimate IEC 61131-3 Validator - Zero Tolerance Compliance Checker
Implements comprehensive validation for industrial-grade ST code
"""

import re
from typing import Dict, List, Tuple, Set
from enum import Enum

class ValidationLevel(Enum):
    CRITICAL = "CRITICAL"  # Must fix - code will not run
    ERROR = "ERROR"        # Should fix - violates IEC standard
    WARNING = "WARNING"    # Recommended fix - best practice

class UltimateIECValidator:
    """
    Comprehensive IEC 61131-3 validator with zero tolerance for violations
    Covers all aspects of industrial PLC programming standards
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.iec_keywords = self._load_iec_keywords()
        self.validation_rules = self._initialize_validation_rules()
    
    def _load_iec_keywords(self) -> Set[str]:
        """Load IEC 61131-3 reserved keywords"""
        return {
            "PROGRAM", "END_PROGRAM", "FUNCTION", "END_FUNCTION", 
            "FUNCTION_BLOCK", "END_FUNCTION_BLOCK", "VAR", "END_VAR",
            "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT", "VAR_EXTERNAL",
            "VAR_GLOBAL", "VAR_ACCESS", "CONSTANT", "RETAIN", "NON_RETAIN",
            "IF", "THEN", "ELSE", "ELSIF", "END_IF", "CASE", "OF", "END_CASE",
            "FOR", "TO", "BY", "DO", "END_FOR", "WHILE", "END_WHILE",
            "REPEAT", "UNTIL", "END_REPEAT", "WITH", "EXIT", "RETURN",
            "AND", "OR", "XOR", "NOT", "MOD", "DIV", "TRUE", "FALSE",
            "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", 
            "UDINT", "ULINT", "REAL", "LREAL", "TIME", "DATE", "TIME_OF_DAY",
            "DATE_AND_TIME", "STRING", "WSTRING", "BYTE", "WORD", "DWORD", "LWORD",
            "TON", "TOF", "TP", "CTU", "CTD", "CTUD", "R_TRIG", "F_TRIG",
            "RISING_EDGE", "FALLING_EDGE", "SEL", "MUX", "MAX", "MIN", "LIMIT",
            "MOVE", "BLKMOV", "ADD", "SUB", "MUL", "DIV", "EXPT", "SHL", "SHR",
            "ROL", "ROR", "AND", "OR", "XOR", "NOT", "ABS", "SQRT", "LN", "EXP",
            "SIN", "COS", "TAN", "ASIN", "ACOS", "ATAN", "TRUNC", "ROUND"
        }
    
    def _initialize_validation_rules(self) -> Dict:
        """Initialize all validation rules"""
        return {
            "structure_rules": {
                "program_required": {
                    "pattern": r"PROGRAM\s+\w+",
                    "message": "Missing PROGRAM declaration",
                    "level": ValidationLevel.CRITICAL
                },
                "end_program_required": {
                    "pattern": r"END_PROGRAM",
                    "message": "Missing END_PROGRAM",
                    "level": ValidationLevel.CRITICAL
                },
                "var_input_required": {
                    "pattern": r"VAR_INPUT",
                    "message": "Missing VAR_INPUT section",
                    "level": ValidationLevel.ERROR
                },
                "var_output_required": {
                    "pattern": r"VAR_OUTPUT",
                    "message": "Missing VAR_OUTPUT section", 
                    "level": ValidationLevel.ERROR
                },
                "var_required": {
                    "pattern": r"VAR\s*$",
                    "message": "Missing VAR section for internal variables",
                    "level": ValidationLevel.ERROR
                },
                "end_var_required": {
                    "pattern": r"END_VAR",
                    "message": "Missing END_VAR terminator",
                    "level": ValidationLevel.CRITICAL
                }
            },
            "syntax_rules": {
                "unmatched_parentheses": {
                    "check": self._check_unmatched_parentheses,
                    "message": "Unmatched parentheses in code",
                    "level": ValidationLevel.CRITICAL
                },
                "missing_end_if": {
                    "pattern": r"IF\s+.*?THEN(?!.*?END_IF)",
                    "message": "IF without matching END_IF",
                    "level": ValidationLevel.CRITICAL
                },
                "missing_end_case": {
                    "pattern": r"CASE\s+.*?OF(?!.*?END_CASE)",
                    "message": "CASE without matching END_CASE",
                    "level": ValidationLevel.CRITICAL
                },
                "invalid_variable_names": {
                    "check": self._check_variable_names,
                    "message": "Invalid variable names found",
                    "level": ValidationLevel.ERROR
                }
            },
            "safety_rules": {
                "direct_sensor_usage": {
                    "pattern": r"IF\s+(I_\w+|Sensor|Button|Switch)\s*THEN",
                    "message": "Direct sensor usage without R_TRIG edge detection",
                    "level": ValidationLevel.ERROR,
                    "suggestion": "Use R_TRIG: SensorTrig(CLK := Sensor); IF SensorTrig.Q THEN..."
                },
                "unbounded_counters": {
                    "pattern": r":=\s*\w+\s*[+-]\s*1\s*;",
                    "message": "Unbounded counter increment/decrement",
                    "level": ValidationLevel.ERROR,
                    "suggestion": "Add boundary check: IF Count < MaxCount THEN Count := Count + 1;"
                },
                "timer_in_if": {
                    "pattern": r"IF\s+.*?THEN.*?\w+\s*\(\s*IN\s*:=",
                    "message": "Timer called inside IF block - must be called every scan",
                    "level": ValidationLevel.ERROR,
                    "suggestion": "Move timer call outside IF: Timer(IN := Condition, PT := T#5s);"
                },
                "output_not_initialized": {
                    "pattern": r"Q_\w+\s*:\s*BOOL\s*;",
                    "message": "BOOL output not initialized to FALSE",
                    "level": ValidationLevel.WARNING,
                    "suggestion": "Initialize: Q_Output : BOOL := FALSE;"
                }
            },
            "forbidden_rules": {
                "wait_function": {
                    "pattern": r"WAIT\s*\(",
                    "message": "WAIT() function is forbidden - use timers",
                    "level": ValidationLevel.CRITICAL
                },
                "goto_statement": {
                    "pattern": r"\bGOTO\b",
                    "message": "GOTO statement is forbidden - use structured programming",
                    "level": ValidationLevel.CRITICAL
                },
                "while_loop": {
                    "pattern": r"WHILE\s+",
                    "message": "WHILE loop is forbidden - use bounded FOR or state machine",
                    "level": ValidationLevel.ERROR
                },
                "timer_q_assignment": {
                    "pattern": r"\.\s*Q\s*:=",
                    "message": "Direct assignment to timer .Q is forbidden",
                    "level": ValidationLevel.CRITICAL
                },
                "timer_et_assignment": {
                    "pattern": r"\.\s*ET\s*:=",
                    "message": "Direct assignment to timer .ET is forbidden",
                    "level": ValidationLevel.CRITICAL
                }
            },
            "best_practice_rules": {
                "missing_edge_detection": {
                    "check": self._check_edge_detection,
                    "message": "Input signals detected but no R_TRIG found",
                    "level": ValidationLevel.WARNING
                },
                "missing_timer_pt": {
                    "pattern": r"TON\s*\([^)]*IN\s*:=",
                    "message": "TON timer missing PT parameter",
                    "level": ValidationLevel.ERROR
                },
                "state_machine_not_used": {
                    "check": self._check_state_machine_usage,
                    "message": "Sequential logic detected but no state machine (CASE) used",
                    "level": ValidationLevel.WARNING
                },
                "no_output_reset": {
                    "check": self._check_output_reset,
                    "message": "No output reset section found - outputs may stay TRUE",
                    "level": ValidationLevel.WARNING
                }
            }
        }
    
    def validate_code(self, code: str) -> Dict:
        """
        Main validation function - performs comprehensive IEC 61131-3 check
        """
        validation_result = {
            "is_valid": True,
            "critical_errors": [],
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "iec_compliant": False,
            "compliance_score": 0,
            "validation_details": {}
        }
        
        if not code or len(code.strip()) < 50:
            validation_result["critical_errors"].append("Code is empty or too short")
            validation_result["is_valid"] = False
            return validation_result
        
        code_upper = code.upper()
        code_lines = code.split('\n')
        
        # Run all validation rules
        for category, rules in self.validation_rules.items():
            category_results = []
            
            for rule_name, rule in rules.items():
                if "pattern" in rule:
                    matches = re.findall(rule["pattern"], code, re.IGNORECASE | re.DOTALL)
                    if matches:
                        issue = {
                            "rule": rule_name,
                            "message": rule["message"],
                            "level": rule["level"].value,
                            "line": self._find_line_number(code, matches[0] if isinstance(matches, str) else str(matches[0])),
                            "suggestion": rule.get("suggestion", "")
                        }
                        category_results.append(issue)
                        self._add_issue_to_result(validation_result, issue)
                
                elif "check" in rule:
                    issues = rule["check"](code, code_lines)
                    for issue in issues:
                        issue["rule"] = rule_name
                        issue["message"] = rule["message"]
                        issue["level"] = rule["level"].value
                        issue["suggestion"] = rule.get("suggestion", "")
                        category_results.append(issue)
                        self._add_issue_to_result(validation_result, issue)
            
            validation_result["validation_details"][category] = category_results
        
        # Calculate compliance score
        validation_result["compliance_score"] = self._calculate_compliance_score(validation_result)
        validation_result["iec_compliant"] = (
            len(validation_result["critical_errors"]) == 0 and 
            len(validation_result["errors"]) == 0
        )
        validation_result["is_valid"] = validation_result["iec_compliant"]
        
        return validation_result
    
    def _add_issue_to_result(self, result: Dict, issue: Dict):
        """Add issue to appropriate category in result"""
        level = issue["level"]
        if level == ValidationLevel.CRITICAL.value:
            result["critical_errors"].append(issue)
        elif level == ValidationLevel.ERROR.value:
            result["errors"].append(issue)
        elif level == ValidationLevel.WARNING.value:
            result["warnings"].append(issue)
        
        if issue.get("suggestion"):
            result["suggestions"].append(issue["suggestion"])
    
    def _check_unmatched_parentheses(self, code: str, lines: List[str]) -> List[Dict]:
        """Check for unmatched parentheses, brackets, braces"""
        issues = []
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for i, char in enumerate(code):
            if char in pairs:
                stack.append((char, i))
            elif char in pairs.values():
                if not stack:
                    issues.append({
                        "message": f"Unmatched closing '{char}' at position {i}",
                        "line": self._line_from_position(code, i)
                    })
                else:
                    open_char, _ = stack.pop()
                    if pairs[open_char] != char:
                        issues.append({
                            "message": f"Mismatched brackets: '{open_char}' and '{char}'",
                            "line": self._line_from_position(code, i)
                        })
        
        for char, pos in stack:
            issues.append({
                "message": f"Unmatched opening '{char}' at position {pos}",
                "line": self._line_from_position(code, pos)
            })
        
        return issues
    
    def _check_variable_names(self, code: str, lines: List[str]) -> List[Dict]:
        """Check for invalid variable names"""
        issues = []
        var_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*[A-Z_]+'
        
        for match in re.finditer(var_pattern, code):
            var_name = match.group(1)
            if var_name.upper() in self.iec_keywords:
                issues.append({
                    "message": f"Variable name '{var_name}' conflicts with IEC keyword",
                    "line": self._line_from_position(code, match.start())
                })
        
        return issues
    
    def _check_edge_detection(self, code: str, lines: List[str]) -> List[Dict]:
        """Check if inputs have proper edge detection"""
        issues = []
        input_pattern = r'\b(I_\w+|Sensor|Button|Switch)\b'
        trig_pattern = r'\bR_TRIG\b|\bF_TRIG\b|\bRISING_EDGE\b'
        
        inputs = re.findall(input_pattern, code, re.IGNORECASE)
        if inputs and not re.search(trig_pattern, code, re.IGNORECASE):
            issues.append({
                "message": f"Inputs found ({len(inputs)}) but no edge detection (R_TRIG/F_TRIG)",
                "line": 1
            })
        
        return issues
    
    def _check_state_machine_usage(self, code: str, lines: List[str]) -> List[Dict]:
        """Check if sequential logic uses state machine"""
        issues = []
        sequential_indicators = ["step", "sequence", "then", "next", "after", "when"]
        
        has_sequential = any(indicator in code.lower() for indicator in sequential_indicators)
        has_case = "CASE" in code.upper()
        
        if has_sequential and not has_case:
            issues.append({
                "message": "Sequential logic detected but no CASE state machine found",
                "line": 1
            })
        
        return issues
    
    def _check_output_reset(self, code: str, lines: List[str]) -> List[Dict]:
        """Check if outputs are reset to safe state"""
        issues = []
        reset_pattern = r':=\s*FALSE\s*;'
        
        if "VAR_OUTPUT" in code.upper():
            reset_count = len(re.findall(reset_pattern, code, re.IGNORECASE))
            if reset_count == 0:
                issues.append({
                    "message": "No output reset to FALSE found - safety risk",
                    "line": 1
                })
        
        return issues
    
    def _find_line_number(self, code: str, pattern: str) -> int:
        """Find line number of pattern in code"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 1
    
    def _line_from_position(self, code: str, position: int) -> int:
        """Convert character position to line number"""
        return code[:position].count('\n') + 1
    
    def _calculate_compliance_score(self, result: Dict) -> int:
        """Calculate IEC compliance score (0-100)"""
        total_issues = (
            len(result["critical_errors"]) * 10 +
            len(result["errors"]) * 5 +
            len(result["warnings"]) * 1
        )
        
        # Start with 100, deduct points for issues
        score = max(0, 100 - total_issues)
        
        # Bonus for good practices
        if "(*" in code and "*)" in code:  # Has comments
            score += 2
        
        if re.search(r'CASE\s+.*?OF', code, re.IGNORECASE):  # Uses state machine
            score += 3
        
        if re.search(r'R_TRIG|F_TRIG', code, re.IGNORECASE):  # Uses edge detection
            score += 2
        
        return min(100, score)
    
    def generate_compliance_report(self, validation_result: Dict) -> str:
        """Generate detailed compliance report"""
        report = []
        report.append("=" * 60)
        report.append("IEC 61131-3 COMPLIANCE REPORT")
        report.append("=" * 60)
        
        # Overall status
        report.append(f"\nOverall Status: {'✅ COMPLIANT' if validation_result['iec_compliant'] else '❌ NON-COMPLIANT'}")
        report.append(f"Compliance Score: {validation_result['compliance_score']}/100")
        
        # Critical errors
        if validation_result["critical_errors"]:
            report.append("\n🚨 CRITICAL ERRORS (Must Fix):")
            for error in validation_result["critical_errors"]:
                report.append(f"  • Line {error['line']}: {error['message']}")
                if error.get("suggestion"):
                    report.append(f"    💡 {error['suggestion']}")
        
        # Errors
        if validation_result["errors"]:
            report.append("\n⚠️  ERRORS (Should Fix):")
            for error in validation_result["errors"]:
                report.append(f"  • Line {error['line']}: {error['message']}")
                if error.get("suggestion"):
                    report.append(f"    💡 {error['suggestion']}")
        
        # Warnings
        if validation_result["warnings"]:
            report.append("\n⚡ WARNINGS (Recommended):")
            for warning in validation_result["warnings"]:
                report.append(f"  • Line {warning['line']}: {warning['message']}")
                if warning.get("suggestion"):
                    report.append(f"    💡 {warning['suggestion']}")
        
        # Summary
        report.append("\n" + "=" * 60)
        report.append("SUMMARY:")
        report.append(f"Critical Errors: {len(validation_result['critical_errors'])}")
        report.append(f"Errors: {len(validation_result['errors'])}")
        report.append(f"Warnings: {len(validation_result['warnings'])}")
        report.append("=" * 60)
        
        return "\n".join(report)
