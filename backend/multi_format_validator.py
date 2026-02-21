"""
Multi-Format IEC 61131-3 Validator
Supports: ST, LD, FBD, SFC, IL
Validates against IEC standards and brand-specific requirements
"""

import re
from typing import Dict, List, Tuple


class MultiFormatValidator:
    """Unified validator for all IEC 61131-3 languages with brand support"""

    # IEC Standard patterns by language
    LANGUAGE_PATTERNS = {
        "ST": {
            "block_start": r"(PROGRAM|FUNCTION_BLOCK|FUNCTION)",
            "block_end": r"(END_PROGRAM|END_FUNCTION_BLOCK|END_FUNCTION)",
            "var_section": r"VAR(_INPUT|_OUTPUT|_IN_OUT)?",
            "var_end": r"END_VAR",
        },
        "LD": {
            "network_start": r"NETWORK|//Network",
            "contact": r"LD|AND|OR",
            "coil": r"ST|S|R",
            "end_network": r"//End|END_NETWORK",
        },
        "FBD": {
            "block_def": r"VAR_EXTERNAL|FUNCTION_BLOCK",
            "connection": r"\->|;",
            "input_output": r"IN|OUT",
        },
        "SFC": {
            "step": r"STEP|S[0-9]+",
            "transition": r"TRANSITION|T[0-9]+",
            "action": r"ACTION",
            "end_sfc": r"END_SFC",
        },
        "IL": {
            "label": r"^[A-Z][A-Z0-9_]*:",
            "instruction": r"(LD|LDN|AND|OR|NOT|ADD|SUB|MUL|DIV)",
        },
    }

    # Brand-specific compliance rules
    BRAND_RULES = {
        "siemens": {
            "name": "Siemens SIMATIC (S7-1200/1500)",
            "supports": ["ST", "LD", "FBD", "SCL"],
            "timer_format": "TON, TOF, TONR",
            "edge_detection": "R_TRIG, F_TRIG",
            "requirements": [
                "Use IEC 61131-3 standard types",
                "No SIMATIC-specific pragmas in generated code",
                "Counter operations must be guarded",
                "Edge detection mandatory for inputs",
            ],
        },
        "mitsubishi": {
            "name": "Mitsubishi MELSEC",
            "supports": ["LD", "ST", "IL"],
            "timer_format": "TMR, CNT",
            "edge_detection": "Edge relay (*)_i",
            "requirements": [
                "Follow Mitsubishi IEC mapping",
                "Use standard IEC types",
                "Memory addressing must be valid",
            ],
        },
        "ab": {
            "name": "Allen-Bradley CompactLogix/ControlLogix",
            "supports": ["LD", "FBD", "ST"],
            "timer_format": "TON, TOF, TONR",
            "edge_detection": "One-Shot instruction (OSR)",
            "requirements": [
                "Use IEC wrapper compatibility",
                "Structure tag naming conventions",
                "Standard IEC 61131-3 compatibility",
            ],
        },
        "schneider": {
            "name": "Schneider Electric Modicon M241/M251",
            "supports": ["LD", "FBD", "ST"],
            "timer_format": "TON, TOF, TONR",
            "edge_detection": "R_TRIG, F_TRIG",
            "requirements": [
                "IEC 61131-3 compliance required",
                "Standard variable types only",
                "No vendor-specific extensions",
            ],
        },
        "generic": {
            "name": "Generic IEC 61131-3 Compliant PLC",
            "supports": ["ST", "LD", "FBD", "SFC", "IL"],
            "timer_format": "TON, TOF, TONR",
            "edge_detection": "R_TRIG, F_TRIG",
            "requirements": [
                "Pure IEC 61131-3 standard",
                "No vendor extensions",
                "Platform-independent code",
            ],
        },
    }

    # =========================================================================
    # UNIFIED ENTRY POINT
    # =========================================================================
    @staticmethod
    def validate(code: str, language: str = "ST", brand: str = "generic") -> Dict:
        """
        Unified validation method for all languages.
        Returns comprehensive validation result.
        """
        if language not in MultiFormatValidator.LANGUAGE_PATTERNS:
            return {
                "language": language,
                "brand": brand,
                "validation_passed": False,
                "all_issues": [f"❌ [CRITICAL] Unsupported language: {language}"],
                "all_warnings": [],
                "all_recommendations": ["Use one of: ST, LD, FBD, SFC, IL"],
                "summary": "INVALID",
            }

        if brand not in MultiFormatValidator.BRAND_RULES:
            brand = "generic"

        # Check brand supports language
        supported = MultiFormatValidator.BRAND_RULES[brand]["supports"]
        if language not in supported:
            return {
                "language": language,
                "brand": brand,
                "validation_passed": False,
                "all_issues": [
                    f"❌ [CRITICAL] Brand '{brand}' does not support {language}",
                    f"   Supported by {brand}: {', '.join(supported)}",
                ],
                "all_warnings": [],
                "all_recommendations": [
                    f"Use {', '.join(supported)} for {brand}",
                ],
                "summary": "UNSUPPORTED",
            }

        # Route to appropriate validator
        if language == "ST":
            result = MultiFormatValidator._validate_st(code, brand)
        elif language == "LD":
            result = MultiFormatValidator._validate_ld(code, brand)
        elif language == "FBD":
            result = MultiFormatValidator._validate_fbd(code, brand)
        elif language == "SFC":
            result = MultiFormatValidator._validate_sfc(code, brand)
        elif language == "IL":
            result = MultiFormatValidator._validate_il(code, brand)
        else:
            result = {
                "validation_passed": False,
                "all_issues": [f"❌ Unknown language: {language}"],
                "all_warnings": [],
                "all_recommendations": [],
            }

        # Add metadata
        result["language"] = language
        result["brand"] = brand
        result["brand_name"] = MultiFormatValidator.BRAND_RULES[brand]["name"]
        return result

    # =========================================================================
    # ST VALIDATION
    # =========================================================================
    @staticmethod
    def _validate_st(code: str, brand: str) -> Dict:
        """Validate Structured Text (ST) code"""
        issues = []
        warnings = []
        recommendations = []

        code_upper = code.upper()
        lines = code.split("\n")
        timer_vars = set()
        for ln in lines:
            m_timer = re.match(r"\s*(\w+)\s*:\s*TON\b", ln, re.IGNORECASE)
            if m_timer:
                timer_vars.add(m_timer.group(1))

        # 1. SYNTAX CHECKS
        paren_open = code.count("(")
        paren_close = code.count(")")
        if paren_open != paren_close:
            issues.append(f"❌ [CRITICAL] Parenthesis mismatch: {paren_open} open vs {paren_close} close")

        # 2. STRUCTURE CHECKS
        if not re.search(r"PROGRAM\s+\w+", code_upper):
            issues.append("❌ [CRITICAL] Missing PROGRAM declaration")

        if "END_PROGRAM" not in code_upper:
            issues.append("❌ [CRITICAL] Missing END_PROGRAM")

        # 2b. VARIABLE DECLARATION PLACEMENT CHECK (Improved for multiple VAR blocks)
        in_var_block = False
        for ln in lines:
            normalized = ln.strip().upper()
            
            # Enter VAR block
            if re.match(r"^(VAR|VAR_INPUT|VAR_OUTPUT|VAR_IN_OUT|VAR_TEMP)\b", normalized):
                in_var_block = True
                continue
                
            # Exit VAR block
            if normalized == "END_VAR":
                in_var_block = False
                continue
                
            # Check for declaration outside block
            if not in_var_block:
                # Match typical declaration pattern: Name : Type
                # Must have colon, specific types, AND strict structure to avoid false positives on code assignments like "x := y"
                # Exclude lines with ":=" (assignments) to be safe
                if ":=" not in ln and re.search(r"^\s*\w+\s*:\s*(BOOL|INT|DINT|REAL|STRING|BYTE|WORD|TIME|TON|TOF|TP|R_TRIG|F_TRIG)\s*(;|$)", ln, re.IGNORECASE):
                    # One more check: make sure it's not a label like "Step1:" or inside a function call argument
                    if not re.search(r"^\s*\w+:\s*$", ln): 
                        issues.append(f"CRITICAL: Variable declaration found outside VAR block: '{ln.strip()}'")
                        recommendations.append("Move all declarations inside VAR ... END_VAR")
                        # Don't break immediately, find all occurrences


        # 3. IEC COMPLIANCE CHECKS
        # Check for R_TRIG on inputs
        if re.search(r"(SENSOR|INPUT|BUTTON|SWITCH)", code_upper):
            if "R_TRIG" not in code_upper:
                issues.append("❌ [CRITICAL] Input without R_TRIG edge detection detected")
                recommendations.append("💡 Use R_TRIG for all digital inputs to prevent race conditions")

        # 4. COUNTER LOGIC CHECKS
        if re.search(r"(COUNTER|counter).*:=.*(\+|-)", code):
            # Check for guard before increment/decrement
            counter_lines = re.findall(r".*counter.*:=.*(\+|-|1).*", code)
            for line in counter_lines:
                # Look for guard pattern before operation
                if not re.search(
                    r"(IF.*<|IF.*>|IF.*counter|WHILE.*counter)",
                    line,
                    re.IGNORECASE,
                ):
                    issues.append(
                        f"❌ [CRITICAL] Counter operation without proper guard: {line.strip()}"
                    )
                    recommendations.append(
                        "💡 Use 'IF counter < MAX THEN counter := counter + 1; END_IF;'"
                    )

        # 4b. MULTIPLE ENTRY INCREMENTS IN SAME SCAN (heuristic)
        increment_lines = [
            ln for ln in lines
            if re.search(r"\bcar_count\b\s*:=\s*car_count\s*\+\s*1", ln, re.IGNORECASE)
        ]
        if len(increment_lines) > 1:
            if not re.search(r"(entry_count|entry_sum|combined|merge|total_entry)", code, re.IGNORECASE):
                issues.append("âŒ [CRITICAL] Multiple car_count increments found without aggregation; may exceed capacity in one scan")
                recommendations.append("ðŸ’¡ Combine entry pulses and increment once per scan (e.g., entry_sum := BOOL_TO_INT(p1) + BOOL_TO_INT(p2))")

        # 5. TYPE CHECKS
        if not re.search(r"\w+\s*:\s*(BOOL|INT|DINT|REAL|STRING|BYTE|WORD)", code):
            warnings.append("⚠️ No explicit variable types found")

        # 5b. TIMER USAGE: must be called every scan (not only inside IF blocks)
        in_if = False
        for ln in lines:
            stripped = ln.strip()
            if re.match(r"(?i)^IF\b", stripped):
                in_if = True
            if re.search(r"(?i)\bEND_IF\b", stripped):
                in_if = False
            if re.search(r"\w+\s*\(\s*IN\s*:?=", stripped, re.IGNORECASE):
                if in_if:
                    issues.append("âŒ [CRITICAL] Timer/function block call found inside IF; timers must be called every scan")
                    recommendations.append("ðŸ’¡ Move TON/TOF/TP calls outside IF and drive IN with conditions")
                    break

        # 5b-2. TIMER IN CONDITION SHOULD HOLD LONG ENOUGH
        for ln in lines:
            m = re.search(r"^\s*(\w+)\s*\(\s*IN\s*:?=\s*([^,]+),", ln, re.IGNORECASE)
            if not m:
                continue
            timer_name = m.group(1)
            if timer_vars and timer_name not in timer_vars:
                continue
            cond = m.group(2)
            if re.search(r"pulse|trig", cond, re.IGNORECASE):
                if not re.search(rf"({timer_name}|latch|hold|gate_open|gate_cmd|open_cmd|request)", cond, re.IGNORECASE):
                    issues.append("âŒ [CRITICAL] Timer IN driven only by a pulse; gate may not stay open for PT duration")
                    recommendations.append("ðŸ’¡ Use self-hold: timer(IN := pulse OR timer.Q, PT := T#5s)")
                    break

        # 5b-3. MULTI-PULSE INCREMENT MUST CHECK AGAINST CAPACITY
        for idx, ln in enumerate(lines):
            if re.search(r"car_count\s*:=\s*car_count\s*\+", ln, re.IGNORECASE):
                if len(re.findall(r"BOOL_TO_INT", ln, re.IGNORECASE)) >= 2:
                    # Look for a guard line nearby
                    start = max(0, idx - 2)
                    joined = "\n".join(lines[start:idx + 1])
                    guard_ok = re.search(r"car_count\s*\+\s*\w+\s*<=\s*MAX_CAPACITY", joined, re.IGNORECASE) or \
                               re.search(r"MAX_CAPACITY\s*-\s*[12]", joined, re.IGNORECASE)
                    if not guard_ok:
                        issues.append("âŒ [CRITICAL] Multi-entry increment can exceed MAX_CAPACITY in one scan")
                        recommendations.append("ðŸ’¡ Use guard: IF (car_count + entry_sum) <= MAX_CAPACITY THEN ... END_IF;")
                        break

        # 5c. GATE OUTPUTS MUST BE DRIVEN BY TIMER STATE
        for ln in lines:
            if re.search(r"\bgate\w*\b\s*:=", ln, re.IGNORECASE):
                if re.search(r"pulse|trig", ln, re.IGNORECASE) and not re.search(r"(latch|hold|request|cmd)", ln, re.IGNORECASE):
                    issues.append("âŒ [CRITICAL] Gate output tied to pulse; gate may not stay open for PT duration")
                    recommendations.append("ðŸ’¡ Drive gate output from timer.Q or a latched request, not directly from pulse")
                    break
                if re.search(r"\bTRUE\b", ln, re.IGNORECASE):
                    if not re.search(r"(timer|\.Q|\.IN)", ln, re.IGNORECASE):
                        issues.append("âŒ [CRITICAL] Gate output forced TRUE without timer IN/Q; may stay open")
                        recommendations.append("ðŸ’¡ Set gate output based on timer IN or Q (e.g., gate := t.IN OR t.Q)")
                        break

        # 6. BRAND-SPECIFIC CHECKS
        brand_rules = MultiFormatValidator.BRAND_RULES.get(brand, {})
        for rule in brand_rules.get("requirements", []):
            if "guard" in rule.lower() and "counter" in code_upper:
                # Already checked above
                pass

        return {
            "validation_passed": len(issues) == 0,
            "all_issues": issues,
            "all_warnings": warnings,
            "all_recommendations": recommendations,
            "summary": "VALID" if len(issues) == 0 else "INVALID",
        }

    # =========================================================================
    # LD (LADDER DIAGRAM) VALIDATION
    # =========================================================================
    @staticmethod
    def _validate_ld(code: str, brand: str) -> Dict:
        """Validate Ladder Diagram (LD) code"""
        issues = []
        warnings = []
        recommendations = []

        code_upper = code.upper()

        # 1. NETWORK STRUCTURE
        if not re.search(r"NETWORK|//\s*Network", code, re.IGNORECASE):
            warnings.append("⚠️ No NETWORK definitions found")

        # 2. CONTACTS AND COILS
        has_contact = bool(re.search(r"\bLD\b|\bAND\b|\bOR\b", code_upper))
        has_coil = bool(re.search(r"\bST\b|\bS\b|\bR\b", code_upper))

        if not has_contact:
            issues.append("❌ [CRITICAL] No ladder contacts (LD, AND, OR) found")

        if not has_coil:
            issues.append("❌ [CRITICAL] No ladder coils (ST, S, R) found")

        # 3. EDGE DETECTION
        if re.search(r"(SENSOR|INPUT|BUTTON|SWITCH)", code_upper):
            if not re.search(r"(^|\s)(P|F|P1|N1|^P|^N)", code, re.MULTILINE):
                issues.append("❌ [CRITICAL] Input without edge detection (P/F prefix)")
                recommendations.append("💡 Use P for rising edge, F for falling edge on inputs")

        # 4. TIMER/COUNTER BLOCKS
        if re.search(r"TON|TOF|CNT|CTU|CTD", code_upper):
            if "NETWORK" not in code_upper:
                warnings.append("⚠️ Timer/Counter found but no network structure")

        # 5. OUTPUT VALIDATION
        if "=" not in code and "ST" not in code_upper:
            issues.append("❌ [CRITICAL] No outputs defined")

        # 6. BRAND-SPECIFIC LD RULES
        if brand == "mitsubishi":
            # Mitsubishi uses different edge markers
            if not re.search(r"_p|_f", code):
                warnings.append("⚠️ Mitsubishi LD should use _p, _f for edges")

        return {
            "validation_passed": len(issues) == 0,
            "all_issues": issues,
            "all_warnings": warnings,
            "all_recommendations": recommendations,
            "summary": "VALID" if len(issues) == 0 else "INVALID",
        }

    # =========================================================================
    # FBD (FUNCTION BLOCK DIAGRAM) VALIDATION
    # =========================================================================
    @staticmethod
    def _validate_fbd(code: str, brand: str) -> Dict:
        """Validate Function Block Diagram (FBD) code"""
        issues = []
        warnings = []
        recommendations = []

        code_upper = code.upper()

        # 1. BLOCK DEFINITIONS
        if not re.search(r"FUNCTION_BLOCK|FB\s+\w+", code_upper):
            if "VAR_EXTERNAL" not in code_upper:
                warnings.append("⚠️ No FUNCTION_BLOCK or VAR_EXTERNAL found")

        # 2. INPUT/OUTPUT CONNECTIONS
        if not re.search(r"->|;|IN|OUT", code, re.IGNORECASE):
            issues.append("❌ [CRITICAL] No block connections (-> or ;) found")
            recommendations.append("💡 FBD must have inputs connected to outputs")

        # 3. VARIABLE TYPES
        if "INT" not in code_upper and "BOOL" not in code_upper and "REAL" not in code_upper:
            warnings.append("⚠️ No IEC type declarations found")

        # 4. BLOCK INSTANCES
        blocks = re.findall(r"(\w+)\s*:\s*(AND|OR|NOT|TON|TOF|ADD|SUB|MUL|DIV|CTU|CTD)", code_upper)
        if not blocks:
            issues.append("❌ [CRITICAL] No function blocks detected")
            recommendations.append("💡 FBD must contain at least one function block")

        # 5. DATA FLOW VALIDATION
        has_inputs = bool(re.search(r"(INPUT|IN|->)", code, re.IGNORECASE))
        has_outputs = bool(re.search(r"(OUTPUT|OUT|;)", code, re.IGNORECASE))

        if not has_inputs:
            issues.append("❌ [CRITICAL] No inputs defined")
        if not has_outputs:
            issues.append("❌ [CRITICAL] No outputs defined")

        # 6. EDGE DETECTION FOR COUNTERS
        if re.search(r"CTU|CTD", code_upper):
            if "R_TRIG" not in code_upper and "P" not in code:
                issues.append("❌ [CRITICAL] Counter input without edge detection")
                recommendations.append("💡 Use R_TRIG or edge-triggered input for counters")

        return {
            "validation_passed": len(issues) == 0,
            "all_issues": issues,
            "all_warnings": warnings,
            "all_recommendations": recommendations,
            "summary": "VALID" if len(issues) == 0 else "INVALID",
        }

    # =========================================================================
    # SFC (SEQUENTIAL FUNCTION CHART) VALIDATION
    # =========================================================================
    @staticmethod
    def _validate_sfc(code: str, brand: str) -> Dict:
        """Validate Sequential Function Chart (SFC) code"""
        issues = []
        warnings = []
        recommendations = []

        code_upper = code.upper()

        # 1. SFC STRUCTURE
        if "SFC" not in code_upper and "STEP" not in code_upper:
            warnings.append("⚠️ No SFC structure found")

        # 2. STEPS
        steps = re.findall(r"STEP\s+(\w+)|S(\d+)", code_upper)
        if not steps:
            issues.append("❌ [CRITICAL] No STEP definitions found")
            recommendations.append("💡 SFC must have at least one STEP")

        # 3. TRANSITIONS
        transitions = re.findall(r"TRANSITION\s+(\w+)|T(\d+)", code_upper)
        if not transitions:
            issues.append("❌ [CRITICAL] No TRANSITION definitions found")
            recommendations.append("💡 SFC must have transitions between steps")

        # 4. ACTIONS
        actions = re.findall(r"ACTION\s+\w+", code_upper)
        if actions:
            # Actions should have assignments
            if not re.search(r":=", code):
                warnings.append("⚠️ ACTION found but no variable assignments")

        # 5. STEP FLOW
        if len(steps) > 0 and len(transitions) == 0:
            issues.append("❌ [CRITICAL] Steps without transitions - no flow defined")

        # 6. INITIAL STEP
        if not re.search(r"INITIAL\s+STEP|S0|STEP\s+0", code_upper):
            warnings.append("⚠️ No initial step defined")

        # 7. FINAL STEP/END
        if "END_SFC" not in code_upper:
            issues.append("❌ [CRITICAL] Missing END_SFC")

        return {
            "validation_passed": len(issues) == 0,
            "all_issues": issues,
            "all_warnings": warnings,
            "all_recommendations": recommendations,
            "summary": "VALID" if len(issues) == 0 else "INVALID",
        }

    # =========================================================================
    # IL (INSTRUCTION LIST) VALIDATION
    # =========================================================================
    @staticmethod
    def _validate_il(code: str, brand: str) -> Dict:
        """Validate Instruction List (IL) code"""
        issues = []
        warnings = []
        recommendations = []

        code_upper = code.upper()
        lines = code.split("\n")

        # 1. INSTRUCTIONS
        valid_instructions = {
            "LD",
            "LDN",
            "AND",
            "ANDN",
            "OR",
            "ORN",
            "XOR",
            "XORN",
            "NOT",
            "ADD",
            "SUB",
            "MUL",
            "DIV",
            "MOD",
            "GT",
            "GE",
            "EQ",
            "LE",
            "LT",
            "NE",
            "JMP",
            "JMPC",
            "JMPCN",
            "CAL",
            "CALC",
            "CALCN",
            "RET",
            "RETC",
            "RETCN",
            "ST",
            "STN",
        }

        instruction_count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Extract first word (instruction)
            parts = line.split()
            if parts:
                instr = parts[0].upper()
                if instr in valid_instructions:
                    instruction_count += 1
                elif not instr.endswith(":"):  # Not a label
                    warnings.append(f"⚠️ Unknown instruction: {instr}")

        if instruction_count == 0:
            issues.append("❌ [CRITICAL] No valid IL instructions found")

        # 2. LABELS
        labels = re.findall(r"^([A-Z_]\w*):", code, re.MULTILINE)
        jump_targets = re.findall(r"JMP\s+(\w+)|JMPC\s+(\w+)|JMPCN\s+(\w+)", code_upper)
        all_targets = []
        for match in jump_targets:
            all_targets.extend([t for t in match if t])

        for target in all_targets:
            if target not in labels:
                issues.append(f"❌ [CRITICAL] Jump target '{target}' not found as label")

        # 3. STACK OPERATIONS
        if instruction_count > 0 and not re.search(r"LD|LDN", code_upper):
            warnings.append("⚠️ No initial load (LD/LDN) found")

        # 4. EDGE DETECTION
        if re.search(r"(SENSOR|INPUT|BUTTON)", code_upper):
            if not re.search(r"_P|_N|P1|N1", code):
                issues.append("❌ [CRITICAL] Input without edge marker (_P, _N)")

        return {
            "validation_passed": len(issues) == 0,
            "all_issues": issues,
            "all_warnings": warnings,
            "all_recommendations": recommendations,
            "summary": "VALID" if len(issues) == 0 else "INVALID",
        }

    # =========================================================================
    # UTILITY: Get Brand Information
    # =========================================================================
    @staticmethod
    def get_brand_info(brand: str) -> Dict:
        """Get detailed information about a PLC brand"""
        if brand not in MultiFormatValidator.BRAND_RULES:
            brand = "generic"

        info = MultiFormatValidator.BRAND_RULES[brand].copy()
        return {
            "brand": brand,
            "name": info["name"],
            "supported_languages": info["supports"],
            "timer_support": info["timer_format"],
            "edge_detection": info["edge_detection"],
            "compliance_rules": info["requirements"],
        }

    @staticmethod
    def get_all_brands() -> List[Dict]:
        """Get list of all supported brands"""
        brands = []
        for brand_key, brand_info in MultiFormatValidator.BRAND_RULES.items():
            brands.append({
                "id": brand_key,
                "name": brand_info["name"],
                "languages": brand_info["supports"],
            })
        return brands
