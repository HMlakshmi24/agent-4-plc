import re

class StateMachineValidator:
    """
    Validates State Machine logic integrity.
    """

    def extract_state_variable(self, code: str) -> bool:
        # Check for: State : INT or State : DINT
        match = re.search(r"\bState\s*:\s*(INT|DINT)", code, re.IGNORECASE)
        return bool(match)

    def extract_states(self, code: str) -> list[int]:
        # Extract CASE State OF ... END_CASE
        pattern = r"CASE\s+State\s+OF(.*?)END_CASE"
        match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)
        if not match:
            return []

        block = match.group(1)
        # Find 10: or 0:
        state_numbers = re.findall(r"\b(\d+)\s*:", block)
        return sorted(list(set(map(int, state_numbers))))

    def validate(self, code: str) -> list[str]:
        errors = []

        # Only validate if "CASE State OF" is actually used
        if "CASE State OF" not in code and "CASE state OF" not in code:
            return errors # Not a state machine program, skip

        # Rule 1: State variable must be declared
        if not self.extract_state_variable(code):
            errors.append("State variable used in logic but not declared as INT")

        # Rule 2: Check for states
        states = self.extract_states(code)
        if not states:
             # Maybe regex failed or it's empty
             pass 

        # Additional checks can be added here (unreachable states, etc.)
        return errors
