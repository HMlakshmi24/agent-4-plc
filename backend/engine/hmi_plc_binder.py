# backend/engine/hmi_plc_binder.py
# HMI-PLC Signal Binding Generator
#
# Maps PLC signal names to HMI widget binding hints so that the HMI
# generation prompt produces animated components that respond to real PLC tags.
#
# Usage:
#   bindings = build_hmi_bindings(signal_map, tag_registry)
#   hint     = format_binding_hint(bindings)
#   Inject hint into HMI generation prompt.

from __future__ import annotations
import re

# ── Widget type mapping rules ─────────────────────────────────────────────────
# Each rule: (signal_pattern, widget_type, animation_hint)

_OUTPUT_BINDING_RULES: list[tuple[str, str, str]] = [
    # Motors / actuators
    (r"Pump|Compressor",      "motor_animation",  "spinning impeller, green when TRUE"),
    (r"Motor|Fan|Blower",     "motor_animation",  "rotating symbol, green when TRUE"),
    (r"Conveyor|Belt",        "conveyor_animation","moving belt, arrows flow when TRUE"),
    (r"Agitator|Mixer",       "motor_animation",  "rotating agitator blades when TRUE"),
    # Valves
    (r"Valve",                "valve_animation",  "open/closed position, green=open"),
    (r"Damper",               "valve_animation",  "damper position indicator"),
    # Heating
    (r"Heater",               "heater_indicator", "red glow/orange icon when TRUE"),
    (r"Element",              "heater_indicator", "heating element glow when TRUE"),
    # Status outputs
    (r"Alarm",                "alarm_indicator",  "flashing red when TRUE"),
    (r"StatusRun|Ready",      "status_light",     "green indicator lamp when TRUE"),
    (r"Fault",                "fault_indicator",  "red indicator when TRUE"),
    (r"Batch|Done",           "status_light",     "pulsing amber when TRUE"),
]

_INPUT_BINDING_RULES: list[tuple[str, str, str]] = [
    # Level sensors
    (r"LevelHigh|LevelLow|HighLevel|LowLevel",
                              "level_indicator",  "bar graph level with alarm marker"),
    (r"Level",                "level_indicator",  "level bar graph display"),
    # Temperature
    (r"TempHigh|HighTemp",    "temp_indicator",   "temperature gauge with HH alarm"),
    (r"Temp",                 "temp_indicator",   "temperature gauge display"),
    # Part / count sensors
    (r"PartSensor|Detect",    "counter_display",  "increments on each pulse"),
    (r"JamSensor|Jam",        "fault_indicator",  "amber indicator, flashes on jam"),
    # Pressure
    (r"Pressure|Press",       "pressure_gauge",   "circular gauge 0-100%"),
    # Flow
    (r"Flow",                 "flow_indicator",   "flow arrows and value display"),
    # Safety
    (r"EStop|Emergency",      "estop_indicator",  "large red indicator, always visible"),
    (r"Overload|Overtemp",    "fault_indicator",  "red trip indicator"),
    # Motor feedback
    (r"MotorRunning|Running", "status_light",     "green confirm lamp"),
]

_INTERNAL_BINDING_RULES: list[tuple[str, str, str]] = [
    (r"Count|Batch",          "counter_display",  "numeric counter widget"),
    (r"PartCount|CycleCount", "counter_display",  "part/cycle counter with reset button"),
]


def _match_rules(signal_name: str, rules: list) -> tuple[str, str]:
    """Return (widget_type, animation_hint) for the first matching rule."""
    bare = re.sub(r"^[QIM]_", "", signal_name)
    for pattern, widget_type, hint in rules:
        if re.search(pattern, bare, re.IGNORECASE):
            return widget_type, hint
    return "indicator", "boolean status indicator"


def build_hmi_bindings(
    signal_map:  dict,
    tag_registry: dict = None,
) -> dict:
    """
    Build HMI widget binding definitions for all signals in the signal map.

    Returns a dict structured as:
    {
      "output_bindings": [
        {"plc_signal": "Q_ConveyorMotor", "isa_tag": "CV-101",
         "widget_type": "conveyor_animation", "hint": "moving belt..."},
        ...
      ],
      "input_bindings": [...],
      "internal_bindings": [...]
    }
    """
    tag_reg  = tag_registry or {}
    out_tags = tag_reg.get("outputs", {})
    in_tags  = tag_reg.get("inputs",  {})

    result: dict = {
        "output_bindings":   [],
        "input_bindings":    [],
        "internal_bindings": [],
    }

    for sig in signal_map.get("outputs", []):
        name        = str(sig).strip()
        wtype, hint = _match_rules(name, _OUTPUT_BINDING_RULES)
        isa_info    = out_tags.get(name, {})
        result["output_bindings"].append({
            "plc_signal":  name,
            "isa_tag":     isa_info.get("isa_tag",     name),
            "description": isa_info.get("description", name),
            "widget_type": wtype,
            "hint":        hint,
            "widget_id":   f"widget-{name.replace('_', '-').lower()}",
        })

    for sig in signal_map.get("inputs", []):
        name        = str(sig).strip()
        if name in ("I_Start", "I_Stop", "I_Reset"):
            continue  # Command buttons handled separately in HMI template
        wtype, hint = _match_rules(name, _INPUT_BINDING_RULES)
        isa_info    = in_tags.get(name, {})
        result["input_bindings"].append({
            "plc_signal":  name,
            "isa_tag":     isa_info.get("isa_tag",     name),
            "description": isa_info.get("description", name),
            "widget_type": wtype,
            "hint":        hint,
            "widget_id":   f"widget-{name.replace('_', '-').lower()}",
        })

    for sig in signal_map.get("counters", []) + signal_map.get("internal_states", []):
        name        = str(sig).strip()
        wtype, hint = _match_rules(name, _INTERNAL_BINDING_RULES)
        if wtype != "indicator":  # Only add if a meaningful widget was matched
            result["internal_bindings"].append({
                "plc_signal":  name,
                "isa_tag":     name,
                "description": name,
                "widget_type": wtype,
                "hint":        hint,
                "widget_id":   f"widget-{name.replace('_', '-').lower()}",
            })

    return result


def format_binding_hint(bindings: dict) -> str:
    """
    Format binding dict into a concise text hint to inject into HMI prompt.
    Ensures generated HMI widgets are named and animated to match PLC signals.
    """
    lines = [
        "=== HMI-PLC SIGNAL BINDINGS (MANDATORY) ===",
        "Every widget listed below MUST appear in the HMI layout.",
        "Use the specified widget_type and animate based on the PLC signal value.",
        "",
        "OUTPUT SIGNALS (actuators — animate when TRUE):",
    ]
    for b in bindings.get("output_bindings", []):
        lines.append(
            f"  [{b['widget_type'].upper()}] id={b['widget_id']} "
            f"| PLC:{b['plc_signal']:<25} Tag:{b['isa_tag']:<12} | {b['hint']}"
        )

    lines += ["", "INPUT SIGNALS (sensors — show live status):"]
    for b in bindings.get("input_bindings", []):
        lines.append(
            f"  [{b['widget_type'].upper()}] id={b['widget_id']} "
            f"| PLC:{b['plc_signal']:<25} Tag:{b['isa_tag']:<12} | {b['hint']}"
        )

    if bindings.get("internal_bindings"):
        lines += ["", "INTERNAL VALUES (counters, states):"]
        for b in bindings["internal_bindings"]:
            lines.append(
                f"  [{b['widget_type'].upper()}] id={b['widget_id']} "
                f"| PLC:{b['plc_signal']:<25} | {b['hint']}"
            )

    lines += ["", "=== END HMI-PLC BINDINGS ==="]
    return "\n".join(lines)
