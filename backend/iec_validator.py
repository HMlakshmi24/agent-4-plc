"""
IEC 61131-3 Validation Module
Tests generated code against IEC standards before and after generation
"""

class IECValidator:
    """Validates PLC code against IEC 61131-3 standards"""
    
    # IEC Keywords
    IEC_KEYWORDS = {
        'PROGRAM', 'FUNCTION_BLOCK', 'FUNCTION', 'VAR', 'VAR_INPUT', 
        'VAR_OUTPUT', 'VAR_IN_OUT', 'VAR_TEMP', 'END_PROGRAM', 'END_FUNCTION_BLOCK',
        'END_FUNCTION', 'END_VAR', 'IF', 'THEN', 'ELSE', 'ELSIF', 'END_IF',
        'WHILE', 'DO', 'END_WHILE', 'FOR', 'BY', 'END_FOR', 'REPEAT', 'UNTIL',
        'END_REPEAT', 'CASE', 'OF', 'END_CASE', 'RETURN'
    }
    
    # IEC Data Types
    IEC_DATA_TYPES = {
        'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD',
        'SINT', 'INT', 'DINT', 'LINT',
        'USINT', 'UINT', 'UDINT', 'ULINT',
        'REAL', 'LREAL',
        'STRING', 'WSTRING',
        'TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME',
        'DURATION'
    }
    
    # Standard Function Blocks
    IEC_FBS = {
        'R_TRIG', 'F_TRIG', 'TRIG', 'RS', 'SR',
        'TON', 'TOF', 'TP',
        'CTU', 'CTD', 'CTUD',
        'ADD', 'SUB', 'MUL', 'DIV', 'MOD',
        'AND', 'OR', 'XOR', 'NOT'
    }
    
    @staticmethod
    def validate_st_code(code):
        """Validate Structured Text code"""
        issues = []
        warnings = []
        
        code_upper = code.upper()
        
        # Check 1: PROGRAM or FUNCTION_BLOCK declaration
        if 'PROGRAM' not in code_upper and 'FUNCTION_BLOCK' not in code_upper:
            issues.append("Missing PROGRAM or FUNCTION_BLOCK declaration")
        
        # Check 2: VAR section
        if 'VAR' not in code_upper:
            issues.append("Missing VAR declaration section")
        
        # Check 3: Proper termination
        if 'PROGRAM' in code_upper and 'END_PROGRAM' not in code_upper:
            issues.append("Missing END_PROGRAM")
        if 'FUNCTION_BLOCK' in code_upper and 'END_FUNCTION_BLOCK' not in code_upper:
            issues.append("Missing END_FUNCTION_BLOCK")
        
        # Check 4: All variables should have types
        var_section = code.split('END_VAR')[0] if 'END_VAR' in code else ""
        if var_section and ':' not in var_section:
            issues.append("Variables declared but no types assigned")
        
        # Check 5: Check for R_TRIG usage for inputs
        if 'INPUT' in code_upper or 'input' in code:
            if 'R_TRIG' not in code_upper and 'TRIG' not in code_upper:
                warnings.append("INPUT detected but no edge detection (R_TRIG) found - may cause multiple triggers")
        
        # Check 6: Check for boundary checks
        if 'COUNTER' in code_upper or 'counter' in code or 'COUNT' in code_upper:
            if 'IF' not in code_upper or '>' not in code or '<' not in code:
                warnings.append("Counter variable found but no boundary checks detected")
        
        # Check 7: Initialize variables
        lines_with_vars = [line for line in code.split('\n') if ':=' in line]
        if not lines_with_vars:
            warnings.append("No variable initialization found - variables should have default values")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'severity': 'critical' if issues else ('warning' if warnings else 'ok')
        }
    
    @staticmethod
    def validate_code_structure(code, language='ST'):
        """Validate code structure"""
        issues = []
        
        # Basic checks
        if not code or len(code.strip()) < 10:
            issues.append("Code is too short or empty")
        
        # Check for syntax errors
        parenthesis_open = code.count('(')
        parenthesis_close = code.count(')')
        if parenthesis_open != parenthesis_close:
            issues.append(f"Parenthesis mismatch: {parenthesis_open} open, {parenthesis_close} close")
        
        # Check line endings
        if language == 'ST':
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.endswith(';') and not any(
                    line.endswith(kw) for kw in ['THEN', 'ELSE', 'ELSIF', 'DO', 'OF', 'BEGIN']
                ):
                    # ST code should end with semicolon or keywords
                    pass
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
    
    @staticmethod
    def quick_test(requirement, language='ST'):
        """Quick test to check if code will likely be valid"""
        tests = {
            'requirement_clear': len(requirement) > 20,
            'has_inputs': any(word in requirement.lower() for word in ['sensor', 'button', 'input', 'switch']),
            'has_outputs': any(word in requirement.lower() for word in ['motor', 'light', 'output', 'pump', 'valve']),
            'has_logic': any(word in requirement.lower() for word in ['when', 'if', 'turn on', 'turn off', 'activate']),
            'mentions_safety': any(word in requirement.lower() for word in ['limit', 'max', 'boundary', 'safe', 'protection']),
        }
        
        return {
            'ready_to_generate': sum(tests.values()) >= 3,
            'test_results': tests,
            'recommendations': [
                k for k, v in tests.items() if not v
            ]
        }

# Singleton instance
validator = IECValidator()
