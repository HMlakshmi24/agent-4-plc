# backend/engine/tag_consistency_enforcer.py
# Tag Consistency Enforcer — PLC ↔ HMI ↔ P&ID
#
# Builds a tag registry that maps PLC signal names to ISA-5.1 equipment tags.
# The registry is used to keep naming consistent across:
#   - PLC: Q_PumpMotor, I_LevelHigh
#   - HMI: animated pump widget labelled "P-101"
#   - P&ID: ISA instrument bubble "LT-101"
#
# Usage:
#   registry = build_tag_registry(signal_map, domain_type="pump")
#   hmi_hint = format_hmi_tag_hint(registry)
#   pid_hint = format_pid_tag_hint(registry)
#   Inject these hints into the HMI / PID generation prompts.

from __future__ import annotations
import re


# ── Equipment type inference ──────────────────────────────────────────────────

# Maps signal name fragments → (ISA_prefix, equipment_type, loop_number_start)
_OUTPUT_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"Pump",        re.I), "P",    "pump"),
    (re.compile(r"Conveyor|Belt|CV", re.I), "CV",  "conveyor"),
    (re.compile(r"Mixer|Agitator|MX", re.I), "MX",  "mixer"),
    (re.compile(r"Heater|HE",   re.I), "HE",   "heater"),
    (re.compile(r"Fan|Blower",  re.I), "FAN",  "fan"),
    (re.compile(r"Valve|XV",    re.I), "XV",   "valve"),
    (re.compile(r"Motor",       re.I), "M",    "motor"),
    (re.compile(r"Alarm",       re.I), "ALM",  "alarm"),
    (re.compile(r"Batch",       re.I), "RX",   "reactor"),
    (re.compile(r"Reactor",     re.I), "RX",   "reactor"),
    (re.compile(r"Dose|Dosing", re.I), "DP",   "dosing_pump"),
]

_INPUT_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"LevelHigh",   re.I), "LSH",  "level_switch_high"),
    (re.compile(r"LevelLow",    re.I), "LSL",  "level_switch_low"),
    (re.compile(r"Level",       re.I), "LT",   "level_transmitter"),
    (re.compile(r"TempHigh",    re.I), "TSH",  "temperature_switch_high"),
    (re.compile(r"Temp",        re.I), "TT",   "temperature_transmitter"),
    (re.compile(r"Flow",        re.I), "FT",   "flow_transmitter"),
    (re.compile(r"Part|Detect", re.I), "DE",   "detector"),
    (re.compile(r"Jam",         re.I), "DE",   "jam_detector"),
    (re.compile(r"Overload",    re.I), "ZSL",  "overload_switch"),
    (re.compile(r"Pressure",    re.I), "PT",   "pressure_transmitter"),
    (re.compile(r"Overflow",    re.I), "LSH",  "overflow_switch"),
]


def _infer_equipment(signal_name: str, rules: list) -> tuple[str, str]:
    """Return (ISA_prefix, equipment_type) for a signal name."""
    # Strip prefix (Q_ or I_)
    bare = re.sub(r"^[QIM]_", "", signal_name)
    for pattern, prefix, eq_type in rules:
        if pattern.search(bare):
            return prefix, eq_type
    return "EQ", "equipment"


def build_tag_registry(
    signal_map: dict,
    domain_type: str = "general",
    program_name: str = "PLCProgram",
) -> dict:
    """
    Build a tag registry from the signal_map.

    Returns:
    {
      "program_name": "ConveyorControl",
      "domain_type":  "conveyor",
      "outputs": {
        "Q_ConveyorMotor": {"isa_tag": "CV-101", "type": "conveyor", "loop": "100"},
        "Q_Alarm":         {"isa_tag": "ALM-101", "type": "alarm",   "loop": "101"},
      },
      "inputs": {
        "I_PartSensor":  {"isa_tag": "DE-101", "type": "detector", "loop": "102"},
        "I_LevelHigh":   {"isa_tag": "LSH-101","type": "level_switch_high","loop":"103"},
      }
    }
    """
    registry: dict = {
        "program_name": program_name,
        "domain_type":  domain_type,
        "outputs":      {},
        "inputs":       {},
    }

    loop_counters: dict[str, int] = {}   # ISA_prefix → last loop number used

    def _next_tag(prefix: str) -> tuple[str, str]:
        loop_counters.setdefault(prefix, 100)
        tag   = f"{prefix}-{loop_counters[prefix]}"
        loop  = str(loop_counters[prefix])
        loop_counters[prefix] += 1
        return tag, loop

    for sig in signal_map.get("outputs", []):
        name = str(sig).strip()
        if not name:
            continue
        prefix, eq_type = _infer_equipment(name, _OUTPUT_RULES)
        isa_tag, loop = _next_tag(prefix)
        registry["outputs"][name] = {
            "isa_tag":     isa_tag,
            "type":        eq_type,
            "loop":        loop,
            "description": _human_name(name),
        }

    for sig in signal_map.get("inputs", []):
        name = str(sig).strip()
        if not name or name in ("I_Start", "I_Stop", "I_EStop", "I_Reset"):
            continue  # Skip standard control inputs — no ISA instrument tag needed
        prefix, eq_type = _infer_equipment(name, _INPUT_RULES)
        isa_tag, loop = _next_tag(prefix)
        registry["inputs"][name] = {
            "isa_tag":     isa_tag,
            "type":        eq_type,
            "loop":        loop,
            "description": _human_name(name),
        }

    return registry


def _human_name(signal_name: str) -> str:
    """Convert Q_ConveyorMotor → 'Conveyor Motor'."""
    bare = re.sub(r"^[QIM]_", "", signal_name)
    # Split CamelCase
    words = re.sub(r"([A-Z])", r" \1", bare).strip().split()
    return " ".join(w.capitalize() for w in words)


# ── Prompt injection helpers ──────────────────────────────────────────────────

def format_hmi_tag_hint(registry: dict) -> str:
    """
    Return a concise hint string to inject into the HMI generation prompt,
    so the AI uses the same ISA tag names as the PLC.
    """
    lines = [
        f"PROGRAM: {registry['program_name']}",
        f"DOMAIN:  {registry['domain_type']}",
        "",
        "EQUIPMENT TAG MAPPING (use these exact tags in HMI widget labels and animations):",
    ]
    for plc_name, info in registry["outputs"].items():
        lines.append(
            f"  PLC:{plc_name:<25} → HMI Tag:{info['isa_tag']:<12} ({info['description']})"
        )
    for plc_name, info in registry["inputs"].items():
        lines.append(
            f"  PLC:{plc_name:<25} → HMI Tag:{info['isa_tag']:<12} ({info['description']})"
        )
    return "\n".join(lines)


def format_pid_tag_hint(registry: dict) -> str:
    """
    Return a concise hint string to inject into the P&ID generation prompt,
    so the AI uses consistent equipment IDs.
    """
    lines = [
        f"PROGRAM: {registry['program_name']}",
        f"DOMAIN:  {registry['domain_type']}",
        "",
        "EQUIPMENT IDs FOR P&ID (ISA-5.1 compliant — use exactly these IDs):",
    ]
    for plc_name, info in registry["outputs"].items():
        lines.append(
            f"  Equipment: {info['isa_tag']:<12} | {info['description']:<30} (PLC: {plc_name})"
        )
    for plc_name, info in registry["inputs"].items():
        lines.append(
            f"  Instrument: {info['isa_tag']:<12} | {info['description']:<30} (PLC: {plc_name})"
        )
    return "\n".join(lines)


def get_consistent_prompt_prefix(registry: dict) -> str:
    """
    Combined prefix for both HMI and P&ID generation prompts.
    Injects both the HMI tag hint and the P&ID tag hint.
    """
    return (
        "=== TAG REGISTRY (MANDATORY — use these exact tags) ===\n"
        + format_hmi_tag_hint(registry)
        + "\n\n"
        + format_pid_tag_hint(registry)
        + "\n=== END TAG REGISTRY ===\n\n"
    )
