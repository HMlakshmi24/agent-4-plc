# backend/engine/engineering_completeness.py

class EngineeringCompletenessValidator:
    """
    Layer 8: Ensures domain-specific requirements exist before ST generation.
    Checks engineering intent, not syntax.
    """
    def __init__(self, control_model: dict, signal_map: dict):
        self.model = control_model
        self.signal_map = signal_map
        self.critical = []
        self.warning = []

    def check_motion_system(self):
        outputs = self.signal_map.get("outputs", [])
        inputs = self.signal_map.get("inputs", [])
        
        # Determine if this is a motion system based on output naming conventions
        outputs_str = str(outputs).lower()
        if "motor" in outputs_str or "pump" in outputs_str or "drive" in outputs_str:
            if not any("stop" in str(i).lower() for i in inputs):
                self.critical.append("Motion system missing Stop input.")
            if not self.model.get("states"):
                self.critical.append("Motion system requires state machine.")

    def check_star_delta_requirements(self):
        outputs = self.signal_map.get("outputs", [])
        timers = self.signal_map.get("timers", [])
        outputs_str = str(outputs).lower()
        
        if "star" in outputs_str and "delta" in outputs_str:
            if len(timers) < 2:
                self.critical.append("Star-delta requires two timers (star + transition).")

    def check_counter_clamp(self):
        counters = self.signal_map.get("counters", [])
        clamping = self.model.get("clamping_rules", [])

        if counters and not clamping:
            self.warning.append("Counters detected but no clamp rules defined.")

    def check_monitoring_system(self):
        # Already somewhat enforced by multi-pass, but double-checked here
        outputs = self.signal_map.get("outputs", [])
        if not outputs:
            self.warning.append("System has no outputs defined. Monitoring systems require at least 1 output.")

    def validate(self) -> dict:
        self.check_motion_system()
        self.check_star_delta_requirements()
        self.check_counter_clamp()
        self.check_monitoring_system()

        return {
            "critical": self.critical,
            "warning": self.warning
        }
