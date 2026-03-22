# backend/engine/physical_sequence_rules.py

class PhysicalSequenceRuleEngine:
    """
    Layer 9: Enforces real-world physical safety logic before ST generation.
    Checks for impossible or dangerous overlapping states.
    """
    def __init__(self, control_model: dict):
        self.model = control_model
        self.critical = []
        self.warning = []

    def check_star_delta_overlap(self):
        actions = self.model.get("actions", [])
        star_states = []
        delta_states = []

        for action in actions:
            out_name = str(action.get("output", "")).lower()
            if "star" in out_name:
                star_states.append(action.get("state"))
            if "delta" in out_name:
                delta_states.append(action.get("state"))

        for s in star_states:
            if s in delta_states and s is not None:
                self.critical.append(f"Star and Delta active in same state ({s}).")

    def check_direction_change(self):
        transitions = self.model.get("transitions", [])
        for t in transitions:
            t_str = str(t).lower()
            if "forward" in t_str and "reverse" in t_str:
                self.warning.append("Direct Forward→Reverse transition detected without explicit stop interlock logic.")

    def check_safety_override(self):
        safety_overrides = self.model.get("safety_overrides", [])
        if safety_overrides:
            # Most safety constraints dictate moving to a known safe state (usually 0 or an explicit error state like 99)
            pass # Currently handled broadly by structure locker, but this is a placeholder for model-level checks

    def validate(self) -> dict:
        self.check_star_delta_overlap()
        self.check_direction_change()
        self.check_safety_override()

        return {
            "critical": self.critical,
            "warning": self.warning
        }
