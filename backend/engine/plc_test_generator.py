# backend/engine/plc_test_generator.py

class PLCTestGenerator:
    """
    Layer 16: Auto-generates unit test sequences based on the control model.
    """
    @staticmethod
    def generate(control_model: dict, signal_map: dict) -> str:
        lines = ["(* ─── AUTO-GENERATED TEST SCENARIOS ─── *)"]
        
        # Generate transition tests
        transitions = control_model.get("transitions", [])
        for i, t in enumerate(transitions):
            frm = t.get("from", "?")
            to = t.get("to", "?")
            trigger = t.get("event", t.get("trigger", t.get("condition", "UNKNOWN")))
            
            lines.append(f"Test {i+1}: Transition from {frm} to {to}")
            lines.append(f"  Given M_State = {frm}")
            lines.append(f"  When {trigger} = TRUE")
            lines.append(f"  Expect M_State = {to}")
            lines.append("")

        # Generate safety tests
        safety_overrides = control_model.get("safety_overrides", [])
        for i, s in enumerate(safety_overrides):
            cond = str(s)
            lines.append(f"Safety Test {i+1}: Overall Interlock")
            lines.append(f"  When {cond} = TRUE")
            lines.append(f"  Expect M_State = 99")
            lines.append("")

        return "\n".join(lines)
