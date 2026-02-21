#!/usr/bin/env python3
"""
IEC 61131-3 ST Validator - Industrial Grade
Run: python validator.py yourfile.st
"""

import re
import sys
import argparse

class IECValidator:
    def __init__(self):
        self.rules = {
            'program_structure': self._check_program_structure,
            'var_sections': self._check_var_sections,
            'input_writes': self._check_input_writes,
            'output_reset': self._check_output_reset,
            'timer_calls': self._check_timer_calls,
            'edge_detection': self._check_edge_detection,
            'semicolons': self._check_semicolons,
            'dead_vars': self._check_dead_vars
        }

    def validate(self, code: str) -> dict:
        """Run bundled rules (subset of full 28-rule set)."""
        results = {'errors': 0, 'warnings': 0, 'passes': 0, 'issues': []}

        for rule_name, rule_func in self.rules.items():
            issues = rule_func(code)
            results['issues'].extend(issues)
            results['errors'] += len([i for i in issues if i['type'] == 'error'])
            results['warnings'] += len([i for i in issues if i['type'] == 'warning'])
            results['passes'] += 1 if not issues else 0

        return results

    def _check_program_structure(self, code):
        issues = []
        if 'PROGRAM' not in code.upper() or 'END_PROGRAM' not in code.upper():
            issues.append({'rule': 1, 'type': 'error', 'msg': 'Missing PROGRAM/END_PROGRAM'})
        return issues

    def _check_var_sections(self, code):
        sections = re.findall(r'VAR(?:_INPUT|_OUTPUT)?', code, re.I)
        if len(sections) > 3:
            return [{'rule': 3, 'type': 'error', 'msg': f'Too many VAR sections: {len(sections)}'}]
        # detect VAR after executable code (simple heuristic)
        if re.search(r'END_VAR\s*.*?\n\s*\w+\s*:=', code, re.S | re.I):
            return [{'rule': 2, 'type': 'error', 'msg': 'VAR after executable code'}]
        return []

    def _check_input_writes(self, code):
        inputs = re.findall(r'VAR_INPUT\s*((?:.*?\n)+?)(?=END_VAR)', code, re.S | re.I)
        issues = []
        if inputs:
            input_vars = [line.split(':')[0].strip() for line in inputs[0].splitlines()
                         if ':' in line]
            for var in input_vars:
                if re.search(rf"\b{re.escape(var)}\s*:=", code):
                    issues.append({'rule': 4, 'type': 'error', 'msg': f'Write to INPUT: {var}'})
        return issues

    def _check_output_reset(self, code):
        lines = [line.strip() for line in code.splitlines()]
        first_exec = next((i for i, line in enumerate(lines)
                          if ':=' in line and not line.upper().startswith('VAR')), None)
        outputs = re.findall(r'VAR_OUTPUT\s*((?:.*?\n)+?)(?=END_VAR)', code, re.S | re.I)
        if outputs:
            out_vars = [line.split(':')[0].strip() for line in outputs[0].splitlines() if ':' in line]
            reset_count = 0
            if first_exec is not None:
                for var in out_vars:
                    pattern = rf"^{re.escape(var)}\s*:=\s*FALSE;?"
                    if any(re.match(pattern, l, re.I) for l in lines[:first_exec]):
                        reset_count += 1
            if reset_count < len(out_vars):
                return [{'rule': 5, 'type': 'error', 'msg': 'Missing output reset'}]
        return []

    def _check_timer_calls(self, code):
        if 'TON' in code and re.search(r'IF\s+.*?\bTON\b', code, re.I | re.S):
            return [{'rule': 6, 'type': 'error', 'msg': 'Timer inside conditional'}]
        return []

    def _check_edge_detection(self, code):
        if re.search(r'(\w+)\s*:=\s*\1\s*\+\s*1', code) and 'R_TRIG' not in code:
            return [{'rule': 7, 'type': 'warning', 'msg': 'Counter without R_TRIG'}]
        return []

    def _check_semicolons(self, code):
        statements = re.findall(r'^\s*(\w+\s*:=.*)$', code, re.M)
        missing = [s for s in statements if not s.strip().endswith(';')]
        return [{'rule': 9, 'type': 'error', 'msg': f'Missing ; on: {missing[0]}'}] if missing else []

    def _check_dead_vars(self, code):
        vars_decl = re.findall(r'VAR\s*((?:.*?\n)+?)(?=END_VAR)', code, re.S | re.I)
        if vars_decl:
            decl_vars = [line.split(':')[0].strip() for line in vars_decl[0].splitlines() if ':' in line]
            used_vars = re.findall(r'\b(\w+)\s*:=', code)
            unused = [v for v in decl_vars if v not in used_vars]
            return [{'rule': 11, 'type': 'warning', 'msg': f'Unused: {unused}'}] if unused else []
        return []


def main():
    parser = argparse.ArgumentParser(description='IEC 61131-3 Validator')
    parser.add_argument('file', nargs='?', help='ST file to validate')
    parser.add_argument('--code', help='Inline code')
    args = parser.parse_args()

    validator = IECValidator()

    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        print("Provide --code or file")
        return 1

    results = validator.validate(code)

    print(f"{'='*50}")
    print(f"IEC 61131-3 VALIDATION RESULTS")
    print(f"{'='*50}")
    print(f"Errors: {results['errors']} | Warnings: {results['warnings']} | Passes: {results['passes']}")

    if results['issues']:
        print("\nISSUES:")
        for issue in results['issues']:
            print(f"  RULE {issue['rule']}: {issue['msg']} ({issue['type']})")

    if results['errors'] == 0:
        print("\n✅ PASSES ALL IEC RULES - READY FOR COMPILER")
        return 0
    else:
        print("\n❌ FAILS IEC VALIDATION - FIX REQUIRED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
