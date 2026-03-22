# backend/engine/dead_state_validator.py

import re

class DeadStateValidator:
    """
    Layer 12: Ensures all referenced M_State values exist in the CASE,
    and no defined states are unreachable.
    """
    def __init__(self, st_code: str, control_model: dict):
        self.st_code = st_code
        self.model = control_model
        self.critical = []
        self.warning = []

    def check_state_reachability(self):
        states = self.model.get("states", [])
        
        # Find all transitions: `M_State := <val>`
        assignments = re.findall(r"M_State\s*:=\s*(\d+)", self.st_code)
        assigned_states = set(int(s) for s in assignments)
        assigned_states.add(0)  # 0 is always reachable (init)

        for i, state in enumerate(states):
            if i not in assigned_states:
                self.warning.append(f"State {i} ({state.get('name')}) appears unreachable.")

    def check_undefined_transitions(self):
        states = self.model.get("states", [])
        valid_indices = set(range(len(states)))
        
        assignments = re.findall(r"M_State\s*:=\s*(\d+)", self.st_code)
        for s_str in assignments:
            s = int(s_str)
            if s not in valid_indices and s != 99: # 99 is safety override
                self.critical.append(f"Transition to undefined state {s} detected.")

    def validate(self) -> dict:
        self.check_state_reachability()
        self.check_undefined_transitions()
        
        return {
            "critical": self.critical,
            "warning": self.warning
        }
