# backend/engine/state_transition_validator.py
# State Machine Transition Validator
#
# Parses IEC 61131-3 ST code and validates the state machine:
#   - Extracts state labels from CASE...OF block
#   - Checks for mandatory transitions (Idle→Starting/Running, Running→Fault, etc.)
#   - Detects illegal transitions
#   - Detects unreachable states
#
# Returns structured warnings — never modifies code.

import re
from dataclasses import dataclass, field


# ── Expected and illegal transition patterns ──────────────────────────────────

# Normalised state name → canonical group
_STATE_GROUPS = {
    # Idle variants
    "idle": "IDLE", "stopped": "IDLE", "ready": "IDLE", "init": "IDLE",
    "initialise": "IDLE", "initialize": "IDLE", "home": "IDLE", "0": "IDLE",
    # Starting/activation variants
    "starting": "STARTING", "activating": "STARTING", "energising": "STARTING",
    "rampup": "STARTING", "1": "STARTING",
    # Running variants
    "running": "RUNNING", "run": "RUNNING", "active": "RUNNING",
    "operating": "RUNNING", "process": "RUNNING", "2": "RUNNING",
    # Stopping variants
    "stopping": "STOPPING", "deactivating": "STOPPING", "ramping": "STOPPING",
    "shutdown": "STOPPING", "3": "STOPPING",
    # Fault variants
    "fault": "FAULT", "error": "FAULT", "alarm": "FAULT", "emergency": "FAULT",
    "faulted": "FAULT", "tripped": "FAULT", "99": "FAULT",
}

# Transitions that SHOULD exist in a well-designed machine
_RECOMMENDED_FROM_TO = [
    ("IDLE",     "STARTING",  "Start command (Idle -> Starting)"),
    ("IDLE",     "RUNNING",   "Start command direct (Idle -> Running)"),   # if no Starting state
    ("STARTING", "RUNNING",   "Startup complete (Starting -> Running)"),
    ("RUNNING",  "FAULT",     "Fault condition during running (Running -> Fault)"),
    ("RUNNING",  "STOPPING",  "Normal stop (Running -> Stopping)"),
    ("RUNNING",  "IDLE",      "Normal stop direct (Running -> Idle)"),      # if no Stopping
    ("STOPPING", "IDLE",      "Shutdown complete (Stopping -> Idle)"),
    ("FAULT",    "IDLE",      "Manual reset (Fault -> Idle)"),
]

# Transitions that should NOT exist (design errors)
_ILLEGAL_FROM_TO = [
    ("IDLE",     "STOPPING",  "Cannot transition from Idle to Stopping"),
    ("STOPPING", "RUNNING",   "Cannot go from Stopping directly to Running (missing Starting)"),
    ("FAULT",    "RUNNING",   "Cannot go directly from Fault to Running (must pass through Idle)"),
]


@dataclass
class TransitionValidationResult:
    states_found:          list[str]    = field(default_factory=list)
    transitions_found:     list[tuple]  = field(default_factory=list)  # (from, to) as canonical names
    missing_transitions:   list[str]    = field(default_factory=list)
    illegal_transitions:   list[str]    = field(default_factory=list)
    unreachable_states:    list[str]    = field(default_factory=list)
    warnings:              list[str]    = field(default_factory=list)
    has_fault_state:       bool         = False
    has_estop_override:    bool         = False
    has_reset_path:        bool         = False


class StateTransitionValidator:
    """
    Validates state machine transitions in IEC 61131-3 ST code.
    Returns a TransitionValidationResult with all findings.
    """

    def __init__(self, st_code: str):
        self.code       = st_code
        self.code_upper = st_code.upper()

    def validate(self) -> TransitionValidationResult:
        result = TransitionValidationResult()

        states     = self._extract_states()
        result.states_found = states
        if not states:
            result.warnings.append(
                "No CASE...OF state machine detected — state transition validation skipped."
            )
            return result

        transitions = self._extract_transitions(states)
        result.transitions_found = transitions

        canonical_states = [self._canonicalize(s) for s in states]
        result.has_fault_state    = "FAULT" in canonical_states
        result.has_estop_override = bool(re.search(
            r"\bI_EStop\b.*(?:State|M_State)\s*:=|\bIF\b.*I_EStop",
            self.code, re.IGNORECASE | re.DOTALL
        ))
        result.has_reset_path = bool(re.search(
            r"\bI_Reset\b.*(?:State|M_State)\s*:=", self.code, re.IGNORECASE | re.DOTALL
        ))

        self._check_mandatory_transitions(result, canonical_states, transitions)
        self._check_illegal_transitions(result, transitions)
        self._check_unreachable(result, canonical_states, transitions)
        self._check_fault_requirements(result)

        return result

    # ── State extraction ───────────────────────────────────────────────────────

    def _extract_states(self) -> list[str]:
        """
        Extract CASE branch labels from the first CASE...OF block.
        Handles both named (Idle:) and numeric (0:, 1:) labels.
        """
        case_match = re.search(
            r'\bCASE\b\s+\w+\s+\bOF\b(.*?)\bEND_CASE\b',
            self.code, re.DOTALL | re.IGNORECASE
        )
        if not case_match:
            return []

        body   = case_match.group(1)
        labels = re.findall(
            r'^\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*:(?![=:])',  # label: but not := or ::
            body, re.MULTILINE
        )
        # Filter out keywords used as labels (ELSE, etc.)
        skip = {"ELSE", "END_CASE", "ELSIF"}
        return [lbl for lbl in labels if lbl.upper() not in skip]

    # ── Transition extraction ──────────────────────────────────────────────────

    def _extract_transitions(self, states: list[str]) -> list[tuple[str, str]]:
        """
        Extract (from_state, to_state) pairs by finding state assignments within
        each state's CASE block.
        """
        transitions: list[tuple[str, str]] = []

        # Build a regex that matches each state block up to the next state label
        label_alts = "|".join(re.escape(s) + r"\s*:(?![=:])" for s in states)
        label_alts += r"|\bELSE\b|\bEND_CASE\b"

        case_match = re.search(
            r'\bCASE\b\s+\w+\s+\bOF\b(.*?)\bEND_CASE\b',
            self.code, re.DOTALL | re.IGNORECASE
        )
        if not case_match:
            return transitions

        body = case_match.group(1)

        for i, state in enumerate(states):
            # Find the content of this state's block (between this label and the next)
            pattern = re.escape(state) + r"\s*:(?![=:])(.*?)(?=" + label_alts + r")"
            block_match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
            if not block_match:
                continue

            block = block_match.group(1)
            # Find all state assignments: State := X  or  M_State := X
            targets = re.findall(
                r'(?:M_State|State)\s*:=\s*([A-Za-z_][A-Za-z0-9_]*|\d+)',
                block, re.IGNORECASE
            )
            for target in targets:
                if target.upper() not in ("ELSE", "END_CASE"):
                    from_can = self._canonicalize(state)
                    to_can   = self._canonicalize(target)
                    if from_can and to_can:
                        transitions.append((from_can, to_can))

        return transitions

    # ── Canonical mapping ──────────────────────────────────────────────────────

    @staticmethod
    def _canonicalize(name: str) -> str:
        """Map a state name/number to a canonical group string."""
        return _STATE_GROUPS.get(str(name).lower(), str(name).upper())

    # ── Transition checks ──────────────────────────────────────────────────────

    def _check_mandatory_transitions(
        self,
        result: TransitionValidationResult,
        canonical_states: list[str],
        transitions: list[tuple],
    ) -> None:
        """Warn if expected transitions are missing."""
        has_starting = "STARTING" in canonical_states
        has_stopping = "STOPPING" in canonical_states

        for from_can, to_can, description in _RECOMMENDED_FROM_TO:
            # Skip STARTING-related checks if no Starting state
            if from_can == "STARTING" and not has_starting:
                continue
            if to_can == "STARTING" and not has_starting:
                continue
            # Skip STOPPING-related checks if no Stopping state
            if from_can == "STOPPING" and not has_stopping:
                continue
            if to_can == "STOPPING" and not has_stopping:
                continue
            # Skip if neither from nor to state exists in this machine
            if from_can not in canonical_states and to_can not in canonical_states:
                continue

            if (from_can, to_can) not in transitions:
                result.missing_transitions.append(
                    f"Missing transition: {description}"
                )

    def _check_illegal_transitions(
        self,
        result: TransitionValidationResult,
        transitions: list[tuple],
    ) -> None:
        """Warn if illegal transitions are present."""
        for from_can, to_can, description in _ILLEGAL_FROM_TO:
            if (from_can, to_can) in transitions:
                result.illegal_transitions.append(
                    f"Illegal transition detected: {description}"
                )

    def _check_unreachable(
        self,
        result: TransitionValidationResult,
        canonical_states: list[str],
        transitions: list[tuple],
    ) -> None:
        """Detect states that are never the target of any transition."""
        reachable_targets = {t for _, t in transitions}
        # Idle is always reachable (starting state)
        reachable_targets.add("IDLE")
        reachable_targets.add("0")

        for s in canonical_states:
            if s not in reachable_targets and s != "IDLE" and s != "0":
                result.unreachable_states.append(
                    f"State '{s}' has no incoming transitions — may be unreachable."
                )

    def _check_fault_requirements(
        self, result: TransitionValidationResult
    ) -> None:
        """Check fault-related requirements."""
        if not result.has_fault_state:
            result.warnings.append(
                "No FAULT state detected — industrial safety requires an explicit fault state."
            )
        if result.has_fault_state and not result.has_reset_path:
            result.warnings.append(
                "FAULT state detected but no I_Reset path found — fault may latch permanently."
            )
        if not result.has_estop_override:
            result.warnings.append(
                "No I_EStop override detected — safety input must have highest priority in all states."
            )

        # Compile all warnings into the result.warnings list
        result.warnings.extend(result.missing_transitions)
        result.warnings.extend(result.illegal_transitions)
        result.warnings.extend(result.unreachable_states)

    # ── Convenience method ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        r = self.validate()
        return {
            "states_found":        r.states_found,
            "transitions_found":   [list(t) for t in r.transitions_found],
            "has_fault_state":     r.has_fault_state,
            "has_estop_override":  r.has_estop_override,
            "has_reset_path":      r.has_reset_path,
            "missing_transitions": r.missing_transitions,
            "illegal_transitions": r.illegal_transitions,
            "unreachable_states":  r.unreachable_states,
            "warnings":            r.warnings,
        }
