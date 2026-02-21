import re

class TimerValidator:
    """
    Enforces strict rules for IEC Timers (TON, TOF, TP).
    """

    VALID_TYPES = {"TON", "TOF", "TP"}

    def extract_declared_timers(self, code: str) -> dict:
        """Returns dict {name: type}"""
        # Matches: TimerName : TON;
        pattern = r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(TON|TOF|TP)"
        return dict(re.findall(pattern, code, re.IGNORECASE))

    def extract_called_timers(self, code: str) -> list:
        """Returns list of timer names used in calls like Timer1(IN:=..."""
        # Matches: TimerName(IN :=
        pattern = r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*IN\s*:="
        return re.findall(pattern, code, re.IGNORECASE)

    def validate_time_format(self, pt: str) -> bool:
        """Validates T#5s, T#100ms format"""
        return bool(re.match(r"^T#\d+(ms|s|m|h|d)$", pt.strip(), re.IGNORECASE))

    def validate(self, code: str) -> list[str]:
        errors = []

        declared = self.extract_declared_timers(code)
        called = self.extract_called_timers(code)

        # Rule 1: Called but not declared
        for timer in called:
            # Case insensitive check
            found = False
            for d in declared:
                if d.upper() == timer.upper():
                    found = True
                    break
            if not found:
                errors.append(f"Timer '{timer}' called but not declared in VAR")

        # Rule 2: Declared but never used (Warning)
        # We skip this for errors, maybe just warning log

        # Rule 3: PT format check
        # Extract PT := T#...
        pt_matches = re.finditer(r"PT\s*:=\s*([^,;)]+)", code)
        for match in pt_matches:
            pt_val = match.group(1).strip()
            if not self.validate_time_format(pt_val):
                # Try to see if it is a variable?
                # If it's not a variable (which we can't fully know without full symbol table), assume it attempts to be a literal if starts with T#
                if pt_val.upper().startswith("T#") and not self.validate_time_format(pt_val):
                     errors.append(f"Invalid PT time format: {pt_val}")

        return errors
