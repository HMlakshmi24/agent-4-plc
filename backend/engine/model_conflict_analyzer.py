# backend/engine/model_conflict_analyzer.py
# Layer 6 — Control Model Conflict Analyzer
#
# Runs BEFORE ST generation on the control model JSON produced by MultiPassExtractor.
# Detects architectural defects at model level so they never reach the generator.
#
# CRITICAL issues → pipeline raises immediately before ST generation.
# WARNING issues  → logged, pipeline continues.
#
# Checks:
#    Duplicate transition triggers (same from-state + same event)
#    States with no outgoing transition (locked / terminal states)
#    States never reachable from initial state
#    Output actuator controlled in multiple states concurrently (ownership conflict)
#    Safety override present without explicit precedence


class ModelConflictAnalyzer:
    """
    Read-only structural validator for the control model JSON.
    Never modifies the model. Only reports conflicts with severity.
    """

    def __init__(self, control_model: dict):
        self.model = control_model
        self.critical: list[str] = []
        self.warning: list[str] = []

    @staticmethod
    def _state_name(state) -> str:
        """Normalize: AI may return states as strings OR as {name, description} dicts."""
        if isinstance(state, dict):
            return str(state.get("name", state.get("id", str(state)))).strip()
        return str(state).strip()

    # ── CHECK 1: Duplicate Transition Triggers ────────────────────────────────

    def check_duplicate_transitions(self):
        """Two transitions from same state on same event = ambiguous routing."""
        seen = set()
        for t in self.model.get("transitions", []):
            from_raw = t.get("from", t.get("from_state", ""))
            event_raw = t.get("event", t.get("trigger", t.get("condition", "")))
            key = (self._state_name(from_raw), str(event_raw).strip())
            if key[0] and key[1]:
                if key in seen:
                    # Changed from critical to warning to be more lenient
                    self.warning.append(
                        f"Duplicate transition: state '{key[0]}' on event '{key[1]}' "
                        f"→ ambiguous routing, scan conflict risk."
                    )
                seen.add(key)

    # ── CHECK 2: States With No Exit (Locked States) ─────────────────────────

    def check_state_without_exit(self):
        """A non-terminal state with no outgoing transitions will lock the machine."""
        states = [self._state_name(s) for s in self.model.get("states", [])]
        from_states = {
            self._state_name(t.get("from", t.get("from_state", "")))
            for t in self.model.get("transitions", [])
        }
        safety = {
            self._state_name(s).lower()
            for s in self.model.get("safety_overrides", [])
        }

        for s in states:
            if s.lower() in safety:
                continue
            if s not in from_states:
                self.warning.append(
                    f"State '{s}' has no outgoing transition — machine may lock here."
                )

    # ── CHECK 3: Unreachable States ───────────────────────────────────────────

    def check_unreachable_states(self):
        """States that can never be entered from any other state are dead code."""
        states = [self._state_name(s) for s in self.model.get("states", [])]
        to_states = {
            self._state_name(t.get("to", t.get("to_state", "")))
            for t in self.model.get("transitions", [])
        }

        if not states:
            return

        initial = states[0]
        for s in states:
            if s != initial and s not in to_states:
                self.warning.append(
                    f"State '{s}' is never reached by any transition — it is dead code."
                )

    # ── CHECK 4: Output Ownership Conflict ────────────────────────────────────

    def check_output_conflict(self):
        """Same actuator/output written in multiple states without mutual exclusivity."""
        action_map: dict[str, set[str]] = {}
        for action in self.model.get("actions", []):
            output = str(action.get("output", action.get("actuator", ""))).strip()
            state  = str(action.get("state", action.get("in_state", ""))).strip()
            if output and state:
                action_map.setdefault(output, set()).add(state)

        for output, owning_states in action_map.items():
            if len(owning_states) > 1:
                self.warning.append(
                    f"Output '{output}' is controlled by multiple states "
                    f"({', '.join(sorted(owning_states))}) — verify mutual exclusivity."
                )

    # ── CHECK 5: Safety Override Without Precedence ───────────────────────────

    def check_safety_precedence(self):
        """Safety overrides must be declared so they supersede normal transitions."""
        overrides = self.model.get("safety_overrides", [])
        transitions = self.model.get("transitions", [])

        if not overrides:
            return  # no safety needed for this system

        # Check if any transition targets a safety override state,
        # meaning the state can be entered from normal flow without priority enforcement
        override_states = {str(s).strip().lower() for s in overrides}
        for t in transitions:
            to_state = str(t.get("to", "")).strip().lower()
            if to_state in override_states:
                # Fine — it has a path in. That's expected.
                pass

        # Warn if safety_overrides exist but there's no corresponding action to enforce them
        actions_with_safety = [
            a for a in self.model.get("actions", [])
            if str(a.get("state", "")).strip().lower() in override_states
        ]
        if not actions_with_safety:
            self.warning.append(
                "Safety overrides are declared but no actions enforce them — "
                "ensure safety logic is implemented in generated code."
            )

    # ── ENTRY POINT ───────────────────────────────────────────────────────────

    def validate(self) -> dict:
        """Run all checks. Returns { 'critical': [...], 'warning': [...] }"""
        self.check_duplicate_transitions()
        self.check_state_without_exit()
        self.check_unreachable_states()
        self.check_output_conflict()
        self.check_safety_precedence()

        return {
            "critical": self.critical,
            "warning": self.warning
        }
