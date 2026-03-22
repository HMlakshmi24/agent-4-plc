# backend/engine/prompt_parser.py
# Structured Prompt Parser — AutoMind Platform
#
# Parses the explicit I/O declarations from user prompts so the pipeline
# can enforce exact variable names and timer durations regardless of which
# AI model is used on the backend.
#
# Parsed fields are LOCKED — the AI pipeline cannot rename or drop them.
#
# Supported structured format:
#   Program name: PumpProtection
#   PLC brand: Siemens S7-1200
#   INPUTS:
#     - I_Start: Start pushbutton (NO)
#   OUTPUTS:
#     - Q_PumpMotor: 11 kW pump motor contactor
#   TIMERS:
#     - T_StartDelay: 5 second motor start delay
#   PROCESS DESCRIPTION:
#     - IDLE (0): All outputs OFF. Await Start.
#     - RUNNING (2): Normal operation...
#   DIAGNOSTIC CODES:
#     - FaultCode 10: Emergency stop activated

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Regex Patterns ────────────────────────────────────────────────────────────

_PROG_NAME_RE  = re.compile(r"(?:Program\s+name|PROGRAM\s+NAME)\s*[:=]\s*(\w+)", re.IGNORECASE)
_BRAND_RE      = re.compile(r"PLC\s+brand\s*[:=]\s*([^\n]+)", re.IGNORECASE)

# "- I_SomeName: description" or "- Q_Valve — description"
_SIG_RE = re.compile(r"^\s*[-•*]\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:—\-]{1,3})\s*(.+)$")

# State formats: "IDLE (0): ..." or "0: IDLE ..."  or "- RUNNING (2): ..."
_STATE_ALPHA   = re.compile(r"^\s*[-•]?\s*([A-Z_][A-Z0-9_]*)\s*\((\d+)\)\s*[:—]?\s*(.*)", re.IGNORECASE)
_STATE_NUMERIC = re.compile(r"^\s*[-•]?\s*(\d+)\s*[:=]\s*\(?([A-Z_][A-Z0-9_]+)\)?\s*[:—]?\s*(.*)", re.IGNORECASE)

# "FaultCode 10: description" or "FaultCode 10 = description"
_FAULT_RE = re.compile(r"FaultCode\s+(\d+)\s*[:=\-]\s*(.+)$", re.IGNORECASE)

# Duration e.g. "5 second", "8s", "10 minute", "500ms"
_DUR_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(millisecond|second|minute|hour|ms|sec|min|hr|s|m|h)\b",
    re.IGNORECASE
)

# Section header keywords → canonical section key
_SECTION_MAP = {
    "INPUTS":               "INPUTS",
    "INPUT":                "INPUTS",
    "OUTPUTS":              "OUTPUTS",
    "OUTPUT":               "OUTPUTS",
    "TIMERS":               "TIMERS",
    "TIMER":                "TIMERS",
    "PROCESS DESCRIPTION":  "STATES",
    "PROCESS DESC":         "STATES",
    "STATE DESCRIPTION":    "STATES",
    "STATE DESCRIPTIONS":   "STATES",
    "STATES":               "STATES",
    "SAFETY REQUIREMENTS":  "SAFETY",
    "SAFETY REQUIREMENT":   "SAFETY",
    "SAFETY":               "SAFETY",
    "DIAGNOSTIC CODES":     "FAULTS",
    "DIAGNOSTIC CODE":      "FAULTS",
    "DIAGNOSTICS":          "FAULTS",
    "FAULT CODES":          "FAULTS",
    "FAULT CODE":           "FAULTS",
}


# ── Duration Conversion ───────────────────────────────────────────────────────

def _to_iec_time(text: str) -> str:
    """Extract duration from human text and return IEC T# format. Defaults T#5S."""
    m = _DUR_RE.search(text)
    if not m:
        return "T#5S"
    val  = int(float(m.group(1)))
    unit = m.group(2).lower()
    if unit in ("ms", "millisecond"):
        return f"T#{val}MS"
    if unit in ("s", "sec", "second"):
        return f"T#{val}S"
    if unit in ("m", "min", "minute"):
        return f"T#{val}M"
    if unit in ("h", "hr", "hour"):
        return f"T#{val}H"
    return "T#5S"


# ── Signal Classification Heuristics ─────────────────────────────────────────

def _is_pushbutton(name: str, desc: str) -> bool:
    """True if this input is edge-triggered (pushbutton / momentary contact)."""
    combined = (name + " " + desc).lower()
    return any(kw in combined for kw in (
        "pushbutton", "push button", "push-button", "button",
        "no contact", "nc contact", "normally open", "momentary",
        "pb_", "_pb", "i_start", "i_stop", "i_reset", "i_ack",
    ))


def _is_estop(name: str, desc: str) -> bool:
    """True if this input is an emergency stop."""
    combined = (name + " " + desc).lower()
    return any(kw in combined for kw in (
        "estop", "e_stop", "e-stop", "emergency stop", "emergency",
        "safety stop", "mushroom",
    ))


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class ParsedSignal:
    name:        str
    description: str  = ""
    is_event:    bool = False   # True → needs R_TRIG
    is_estop:    bool = False   # True → safety condition


@dataclass
class ParsedTimer:
    name:        str
    duration:    str            # IEC T# format  e.g. "T#5S"
    description: str = ""


@dataclass
class ParsedState:
    id:          int
    name:        str
    description: str = ""


@dataclass
class ParsedFaultCode:
    code:        int
    description: str


@dataclass
class ParsedPrompt:
    program_name:         Optional[str]       = None
    brand:                Optional[str]       = None
    inputs:               list                = field(default_factory=list)
    outputs:              list                = field(default_factory=list)
    timers:               list                = field(default_factory=list)
    states:               list                = field(default_factory=list)
    fault_codes:          list                = field(default_factory=list)
    safety_requirements:  list                = field(default_factory=list)
    e_stop_name:          Optional[str]       = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def has_explicit_io(self) -> bool:
        """True if the prompt contained explicit INPUTS or OUTPUTS declarations."""
        return bool(self.inputs or self.outputs)

    def get_fault_state_id(self) -> Optional[int]:
        """Return the integer ID of the FAULT/ERROR state (for E-Stop handler)."""
        for s in self.states:
            if any(kw in s.name.upper() for kw in ("FAULT", "ERROR", "ALARM", "FAIL", "TRIP")):
                return s.id
        # If no named fault state, return the highest state ID
        if self.states:
            return max(s.id for s in self.states)
        return None

    def to_locked_signal_map(self) -> dict:
        """
        Return a signal_map dict that OVERRIDES the MultiPassExtractor output.
        Keys match what TemplateLockedSTGenerator expects.
        """
        return {
            "inputs":           [s.name for s in self.inputs],
            "outputs":          [s.name for s in self.outputs],
            "timers":           [t.name for t in self.timers],
            "timer_presets":    {t.name: t.duration for t in self.timers},
            "events":           [s.name for s in self.inputs if s.is_event],
            "safety_conditions":[s.name for s in self.inputs if s.is_estop],
            "internal_states":  [],
            "counters":         [],
            "analog_values":    [],
            "fault_codes":      {fc.code: fc.description for fc in self.fault_codes},
        }

    def to_locked_states(self) -> list:
        """Return a list of state dicts for injection into the control model."""
        return [
            {"id": s.id, "name": s.name, "description": s.description}
            for s in self.states
        ]

    def to_fault_codes_dict(self) -> dict:
        """Return {code_int: description_str} dict."""
        return {fc.code: fc.description for fc in self.fault_codes}


# ── Section Splitter ──────────────────────────────────────────────────────────

def _split_sections(lines: list) -> dict:
    """Split prompt lines into named sections using the keyword table."""
    sections: dict = {"HEADER": []}
    current = "HEADER"

    for line in lines:
        # Normalise candidate: upper, strip trailing punctuation/whitespace
        candidate = line.strip().upper().rstrip(":").rstrip("-").strip()
        if candidate in _SECTION_MAP:
            current = _SECTION_MAP[candidate]
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)

    return sections


# ── Main Parser ───────────────────────────────────────────────────────────────

def parse_prompt(text: str) -> ParsedPrompt:
    """
    Parse a structured AutoMind prompt.

    Returns a ParsedPrompt whose fields are the ground-truth declarations
    that the AI pipeline must honour exactly.
    """
    result = ParsedPrompt()
    lines  = text.splitlines()
    sections = _split_sections(lines)

    # ── Metadata (scan first 15 lines + HEADER section) ──────────────────────
    header_text = "\n".join(sections.get("HEADER", []) + lines[:15])

    m = _PROG_NAME_RE.search(header_text)
    if m:
        result.program_name = m.group(1).strip()

    m = _BRAND_RE.search(header_text)
    if m:
        result.brand = m.group(1).strip()

    # ── INPUTS ────────────────────────────────────────────────────────────────
    for line in sections.get("INPUTS", []):
        m = _SIG_RE.match(line)
        if m:
            name, desc = m.group(1).strip(), m.group(2).strip()
            sig = ParsedSignal(
                name=name,
                description=desc,
                is_event=_is_pushbutton(name, desc),
                is_estop=_is_estop(name, desc),
            )
            result.inputs.append(sig)
            if sig.is_estop and result.e_stop_name is None:
                result.e_stop_name = name

    # ── OUTPUTS ───────────────────────────────────────────────────────────────
    for line in sections.get("OUTPUTS", []):
        m = _SIG_RE.match(line)
        if m:
            name, desc = m.group(1).strip(), m.group(2).strip()
            result.outputs.append(ParsedSignal(name=name, description=desc))

    # ── TIMERS ────────────────────────────────────────────────────────────────
    for line in sections.get("TIMERS", []):
        m = _SIG_RE.match(line)
        if m:
            name, desc = m.group(1).strip(), m.group(2).strip()
            result.timers.append(ParsedTimer(
                name=name,
                duration=_to_iec_time(desc),
                description=desc,
            ))

    # ── STATES (Process Description) ─────────────────────────────────────────
    seen_state_ids: set = set()
    for line in sections.get("STATES", []):
        stripped = line.strip()
        matched = _STATE_ALPHA.match(stripped) or _STATE_NUMERIC.match(stripped)
        if matched:
            try:
                # _STATE_ALPHA: group(1)=name, group(2)=id, group(3)=desc
                # _STATE_NUMERIC: group(1)=id, group(2)=name, group(3)=desc
                if _STATE_ALPHA.match(stripped):
                    state_name = matched.group(1).upper()
                    state_id   = int(matched.group(2))
                    state_desc = matched.group(3).strip()
                else:
                    state_id   = int(matched.group(1))
                    state_name = matched.group(2).upper()
                    state_desc = matched.group(3).strip()

                if state_id not in seen_state_ids:
                    seen_state_ids.add(state_id)
                    result.states.append(ParsedState(
                        id=state_id,
                        name=state_name,
                        description=state_desc,
                    ))
            except (ValueError, IndexError):
                pass

    # ── FAULT CODES ───────────────────────────────────────────────────────────
    seen_codes: set = set()
    # Search both the FAULTS section AND full text (FaultCode may appear anywhere)
    fault_search_lines = sections.get("FAULTS", []) + lines
    for line in fault_search_lines:
        m = _FAULT_RE.search(line)
        if m:
            code = int(m.group(1))
            if code not in seen_codes:
                seen_codes.add(code)
                result.fault_codes.append(ParsedFaultCode(
                    code=code,
                    description=m.group(2).strip(),
                ))

    # ── SAFETY REQUIREMENTS ───────────────────────────────────────────────────
    for line in sections.get("SAFETY", []):
        stripped = line.strip().lstrip("-•*").strip()
        if stripped:
            result.safety_requirements.append(stripped)

    return result
