# backend/engine/scan_simulator.py
# Layer 7 — Lightweight Scan Simulator
#
# Simulates scan-cycle execution on the control model BEFORE ST generation.
# Walks state transitions for N scans to detect structural runtime problems.
#
# Detects:
#    No initial state defined (CRITICAL)
#    Deadlock (state reached with no exit, in mid-simulation)
#    State oscillation (A→B→A→B infinite cycle)
#    No stable resting state (machine never settles)
#    Safety override priority reachability
#
# CRITICAL issues stop the pipeline before ST generation.
# WARNING issues are reported but allow generation to continue.

MAX_SCAN_CYCLES = 6  # simulate up to 6 scan transitions


class ScanSimulator:
    """
    Lightweight structural scan simulator.
    Read-only — never modifies the control model.
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

    def _get_transitions_from(self, state_name: str) -> list[dict]:
        return [
            t for t in self.model.get("transitions", [])
            if self._state_name(t.get("from", t.get("from_state", ""))) == state_name
        ]

    def _get_transition_to(self, t: dict) -> str:
        return self._state_name(t.get("to", t.get("to_state", "")))

    def _all_states(self) -> list[str]:
        return [self._state_name(s) for s in self.model.get("states", []) if self._state_name(s)]

    def simulate(self) -> dict:
        states = self._all_states()
        transitions = self.model.get("transitions", [])

        # ── Guard: No States ─────────────────────────────────────────────
        if not states:
            self.critical.append(
                "Control model has no states — cannot simulate or generate logic."
            )
            return self._result()

        # ── Guard: No Transitions ────────────────────────────────────────
        if not transitions:
            self.warning.append(
                "Control model has no transitions — state machine is static (no state changes)."
            )
            # Not a critical error — monitoring-only systems can have a single static state
            return self._result()

        # ── Simulation Walk ──────────────────────────────────────────────
        initial_state = states[0]
        current = initial_state
        path: list[str] = [current]
        visited_sequence: list[str] = [current]

        for scan in range(MAX_SCAN_CYCLES):
            outgoing = self._get_transitions_from(current)

            if not outgoing:
                # Reached a terminal/deadlock state mid-simulation
                if scan < 2:
                    self.critical.append(
                        f"Simulation deadlock: state '{current}' reached on scan {scan + 1} "
                        f"with no outgoing transitions. Machine will be locked."
                    )
                # Terminal state after some work is acceptable (e.g. DONE state)
                break

            # Take the first available transition (deterministic walk)
            next_state = self._get_transition_to(outgoing[0])
            if not next_state:
                self.warning.append(
                    f"Transition from '{current}' has no 'to' target — malformed transition."
                )
                break

            # ── Oscillation Detection ────────────────────────────────────
            # If we've seen this state before and it immediately loops back, flag it
            if next_state in visited_sequence:
                cycle_start = visited_sequence.index(next_state)
                cycle = visited_sequence[cycle_start:] + [next_state]
                if len(cycle) <= 3:
                    self.warning.append(
                        f"State oscillation detected: {' → '.join(cycle)} "
                        f"— verify transition guards are mutually exclusive."
                    )
                break

            visited_sequence.append(next_state)
            current = next_state
            path.append(current)

        # ── Stability Check ──────────────────────────────────────────────
        # A healthy state machine should settle into a stable state or cycle back to initial.
        if path and path[-1] != initial_state and len(path) >= MAX_SCAN_CYCLES:
            self.warning.append(
                f"Machine did not return to initial state '{initial_state}' after "
                f"{MAX_SCAN_CYCLES} scans. Final state: '{path[-1]}'. "
                f"Ensure a return/reset path exists."
            )

        # ── Safety Override Reachability ─────────────────────────────────
        safety_overrides = [str(s).strip() for s in self.model.get("safety_overrides", [])]
        if safety_overrides:
            reachable = set(path) | set(visited_sequence)
            for override in safety_overrides:
                if override not in reachable:
                    self.warning.append(
                        f"Safety override state '{override}' was not reached in simulation "
                        f"— verify it is triggered by the correct event/condition."
                    )

        return self._result()

    def _result(self) -> dict:
        return {
            "critical": self.critical,
            "warning": self.warning
        }
