"""
Graph-Based HMI Generator
- Step 1: Small LLM call extracts component graph from description
- Step 2: Python builds the complete HMI JSON (positions, ISA tags, sim values)
- Result: Single LLM call instead of generate+validate+fix loop, ~70% fewer tokens
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


# ── ISA / layout constants ─────────────────────────────────────────────────────

_ISA_PREFIX = {
    "tank": "TK", "pump": "P", "valve": "V", "motor": "M", "fan": "FAN",
    "compressor": "C", "sensor_level": "LT", "sensor_temp": "TT",
    "sensor_pressure": "PT", "sensor_flow": "FT", "gauge": "GI",
    "alarm": "ALM", "button": "PB", "slider": "SL",
}

_DEFAULT_STATE = {
    "tank": "inactive", "pump": "stopped", "valve": "closed", "motor": "stopped",
    "fan": "stopped", "compressor": "stopped",
    "sensor_level": "active", "sensor_temp": "active",
    "sensor_pressure": "active", "sensor_flow": "active",
    "gauge": "active", "alarm": "inactive", "button": "inactive", "slider": "inactive",
}

_DEFAULT_UNIT = {
    "tank": "%", "sensor_level": "%", "sensor_temp": "°C",
    "sensor_pressure": "bar", "sensor_flow": "m³/h", "valve": "%",
}

_SIM = {
    "tank":            {"role":"sink",     "fill_rate":0,  "drain_rate":0,"capacity":10000,
                        "hi_alarm":90,"lo_alarm":10,"hi_hi_alarm":95,"lo_lo_alarm":5,"normal_min":20,"normal_max":80},
    "pump":            {"role":"transfer", "fill_rate":30, "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "valve":           {"role":"control",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "motor":           {"role":"transfer", "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "sensor_level":    {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":90,"lo_alarm":10,"hi_hi_alarm":95,"lo_lo_alarm":5,"normal_min":20,"normal_max":80},
    "sensor_temp":     {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":80,"lo_alarm":5,"hi_hi_alarm":90,"lo_lo_alarm":0,"normal_min":10,"normal_max":75},
    "sensor_pressure": {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":8,"lo_alarm":0.5,"hi_hi_alarm":10,"lo_lo_alarm":0,"normal_min":1,"normal_max":7},
    "sensor_flow":     {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "gauge":           {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "alarm":           {"role":"measure",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "button":          {"role":"control",  "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "fan":             {"role":"transfer", "fill_rate":0,  "drain_rate":0,"capacity":0,
                        "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,"normal_min":None,"normal_max":None},
    "compressor":      {"role":"source",   "fill_rate":10, "drain_rate":0,"capacity":0,
                        "hi_alarm":8,"lo_alarm":0.5,"hi_hi_alarm":10,"lo_lo_alarm":0,"normal_min":1,"normal_max":7},
}

# Theme selection by keyword
_THEME_MAP = {
    "water": ["water","tank","pump","level","flood","pipe","liquid"],
    "motor": ["motor","conveyor","belt","drive","speed","rpm"],
    "hvac":  ["hvac","air","duct","fan","temperature","cooling","heating"],
    "chemical": ["chemical","reactor","acid","base","ph","process"],
    "food":  ["food","pharma","beverage","bottl","fill","clean"],
}

def _detect_theme(text: str) -> str:
    t = text.lower()
    for theme, kws in _THEME_MAP.items():
        if any(k in t for k in kws):
            return theme
    return "default"


# ── Graph extraction (single small LLM call) ──────────────────────────────────

_GRAPH_SYSTEM = "Return JSON only. No markdown, no explanation."


def _graph_token_budget(description: str) -> int:
    """Scale HMI graph output budget to prompt complexity."""
    text = (description or "").lower()
    word_count = len(text.split())
    complexity_hits = sum(
        1 for token in (
            "tank", "pump", "valve", "sensor", "alarm", "loop", "control",
            "flow", "level", "pressure", "temperature", "motor", "conveyor",
            "interlock", "button", "hmi", "scada",
        )
        if token in text
    )
    if word_count <= 20 and complexity_hits <= 6:
        return 420
    if word_count <= 50 and complexity_hits <= 10:
        return 560
    return 700

def extract_hmi_graph(description: str) -> tuple[dict, int]:
    """
    Small LLM call: extract component list and connections from description.
    Returns (graph_dict, tokens_used). Falls back to keyword analysis.
    """
    user_msg = f"""Analyze this HMI/SCADA requirement and return its component graph as JSON.

Requirement: {description}

Return exactly this JSON:
{{
  "system_name": "descriptive system name",
  "components": [
    {{"type": "tank|pump|valve|motor|fan|compressor|sensor_level|sensor_temp|sensor_pressure|sensor_flow|gauge|alarm|button", "id": "TK-101", "label": "human readable label"}}
  ],
  "connections": [
    {{"from": "component_id", "to": "component_id", "type": "pipe|signal|control_loop"}}
  ]
}}

Rules:
- Always include a start button, a stop button, and an emergency stop button.
- Minimum 5 components for any system.
- Use ISA-style IDs: TK- for tanks, P- for pumps, V- for valves, LT- for level sensors, TT- for temp, ALM- for alarms, PB- for buttons."""

    try:
        from backend.core.openai_client import generate_layout
        raw, tok = generate_layout(_GRAPH_SYSTEM, user_msg, max_tokens=_graph_token_budget(description))
        # Strip any markdown fences or preamble before parsing
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        graph = json.loads(raw)
        return graph, tok
    except Exception as e:
        print(f"[WARN] HMI graph extraction failed ({e}), using keyword fallback")
        return _keyword_hmi_graph(description), 0


def _keyword_hmi_graph(description: str) -> dict:
    """Instant keyword-based fallback — no LLM."""
    d = description.lower()

    if "tank" in d or "pump" in d or "level" in d or "water" in d:
        return {
            "system_name": "Water Treatment System",
            "components": [
                {"type": "tank",         "id": "TK-101", "label": "Feed Tank"},
                {"type": "pump",         "id": "P-101",  "label": "Transfer Pump"},
                {"type": "valve",        "id": "V-101",  "label": "Inlet Valve"},
                {"type": "tank",         "id": "TK-102", "label": "Process Tank"},
                {"type": "sensor_level", "id": "LT-101", "label": "Feed Tank Level"},
                {"type": "sensor_level", "id": "LT-102", "label": "Process Tank Level"},
                {"type": "alarm",        "id": "ALM-101","label": "High Level Alarm"},
                {"type": "button",       "id": "PB-START","label": "Start"},
                {"type": "button",       "id": "PB-STOP", "label": "Stop"},
                {"type": "button",       "id": "PB-ESTOP","label": "Emergency Stop"},
            ],
            "connections": [
                {"from": "TK-101", "to": "P-101",  "type": "pipe"},
                {"from": "P-101",  "to": "V-101",  "type": "pipe"},
                {"from": "V-101",  "to": "TK-102", "type": "pipe"},
                {"from": "LT-102", "to": "ALM-101","type": "signal"},
            ]
        }

    if "motor" in d or "conveyor" in d or "belt" in d:
        return {
            "system_name": "Motor Control System",
            "components": [
                {"type": "motor",         "id": "M-101",  "label": "Drive Motor"},
                {"type": "sensor_temp",   "id": "TT-101", "label": "Motor Temperature"},
                {"type": "gauge",         "id": "GI-101", "label": "Speed Gauge"},
                {"type": "alarm",         "id": "ALM-101","label": "Overtemp Alarm"},
                {"type": "button",        "id": "PB-START","label": "Start"},
                {"type": "button",        "id": "PB-STOP", "label": "Stop"},
                {"type": "button",        "id": "PB-ESTOP","label": "Emergency Stop"},
            ],
            "connections": [
                {"from": "TT-101", "to": "ALM-101", "type": "signal"},
                {"from": "GI-101", "to": "M-101",   "type": "signal"},
            ]
        }

    # Generic default
    return {
        "system_name": "Industrial Control System",
        "components": [
            {"type": "pump",         "id": "P-101",  "label": "Process Pump"},
            {"type": "valve",        "id": "V-101",  "label": "Control Valve"},
            {"type": "sensor_flow",  "id": "FT-101", "label": "Flow Sensor"},
            {"type": "alarm",        "id": "ALM-101","label": "Process Alarm"},
            {"type": "button",       "id": "PB-START","label": "Start"},
            {"type": "button",       "id": "PB-STOP", "label": "Stop"},
            {"type": "button",       "id": "PB-ESTOP","label": "Emergency Stop"},
        ],
        "connections": [
            {"from": "P-101",  "to": "V-101",   "type": "pipe"},
            {"from": "FT-101", "to": "ALM-101", "type": "signal"},
        ]
    }


# ── HMI JSON assembler — pure Python, 0 LLM tokens ───────────────────────────

# Grid positions for process components (canvas 900x650)
_GRID_X = [100, 260, 420, 580, 740]
_GRID_Y = [160, 320, 460]
_BUTTON_Y = 570
_ALARM_X_START = 700
_ALARM_Y_START = 80


def build_hmi_json(graph: dict, description: str) -> dict:
    """Build complete HMI JSON from graph. No LLM needed."""

    raw_comps   = graph.get("components", [])
    connections = graph.get("connections", [])
    system_name = graph.get("system_name", "Industrial Control System")
    theme       = graph.get("theme", _detect_theme(description))

    buttons = [c for c in raw_comps if c.get("type") == "button"]
    alarms  = [c for c in raw_comps if c.get("type") == "alarm"]
    process = [c for c in raw_comps if c.get("type") not in ("button", "alarm")]

    # Guarantee start/stop/estop buttons
    existing = {b.get("label", "").lower() for b in buttons}
    if not any("start" in l for l in existing):
        buttons.append({"type": "button", "id": "PB-START", "label": "Start"})
    if not any("stop" in l and "emer" not in l for l in existing):
        buttons.append({"type": "button", "id": "PB-STOP", "label": "Stop"})
    if not any("emer" in l or "estop" in l for l in existing):
        buttons.append({"type": "button", "id": "PB-ESTOP", "label": "Emergency Stop"})

    built = []

    # Process components — grid layout
    for i, comp in enumerate(process):
        col = i % len(_GRID_X)
        row = i // len(_GRID_X)
        ctype  = comp.get("type", "pump")
        cid    = comp.get("id",   f"{_ISA_PREFIX.get(ctype,'X')}-{101+i}")
        sim    = dict(_SIM.get(ctype, _SIM["pump"]))
        built.append({
            "type":  ctype,
            "id":    cid,
            "label": comp.get("label", cid),
            "tag":   cid,
            "state": _DEFAULT_STATE.get(ctype, "inactive"),
            "value": 50 if ctype == "tank" else None,
            "unit":  _DEFAULT_UNIT.get(ctype),
            "x":     _GRID_X[col] if col < len(_GRID_X) else 100 + col * 160,
            "y":     _GRID_Y[row] if row < len(_GRID_Y) else 160 + row * 150,
            "sim":   sim,
        })

    # Alarm components — top-right cluster
    for i, comp in enumerate(alarms):
        cid = comp.get("id", f"ALM-{101+i}")
        built.append({
            "type":  "alarm",
            "id":    cid,
            "label": comp.get("label", cid),
            "tag":   cid,
            "state": "inactive",
            "value": None,
            "unit":  None,
            "x":     _ALARM_X_START,
            "y":     _ALARM_Y_START + i * 70,
            "sim":   dict(_SIM["alarm"]),
        })

    # Buttons — bottom row
    for i, btn in enumerate(buttons):
        cid = btn.get("id", f"PB-{i+1:03d}")
        built.append({
            "type":  "button",
            "id":    cid,
            "label": btn.get("label", cid),
            "tag":   cid,
            "state": "inactive",
            "value": None,
            "unit":  None,
            "x":     80 + i * 170,
            "y":     _BUTTON_Y,
            "sim":   dict(_SIM["button"]),
        })

    # Connections — augment with active_when
    built_connections = []
    for conn in connections:
        built_connections.append({
            "from":        conn.get("from", ""),
            "to":          conn.get("to", ""),
            "type":        conn.get("type", "pipe"),
            "label":       conn.get("label", ""),
            "active_when": "running" if conn.get("type", "pipe") == "pipe" else "always",
        })

    # Auto-connect adjacent process components if none provided
    if not built_connections and len(process) >= 2:
        proc_ids = [c["id"] for c in built if c["type"] not in ("button", "alarm")]
        for a, b in zip(proc_ids, proc_ids[1:]):
            built_connections.append({"from": a, "to": b, "type": "pipe",
                                      "label": "", "active_when": "running"})

    return {
        "system_name":        system_name,
        "mode":               "normal",
        "theme":              theme,
        "process_description": description,
        "components":         built,
        "connections":        built_connections,
        "alarms":             [],
    }


# ── Main pipeline (public API, same signature as before) ─────────────────────

def run_hmi_agentic_pipeline(description: str, api_key: str = None) -> dict:
    """
    Graph-based HMI generation — single LLM call + Python assembly.
    Returns a complete HMI JSON dict with _tokens_used field.
    """
    print("[HMI] Graph-based pipeline: extracting component graph…")

    graph, tokens = extract_hmi_graph(description)
    layout = build_hmi_json(graph, description)
    layout["_tokens_used"] = tokens

    comp_count = len(layout.get("components", []))
    print(f"[HMI] Done: {comp_count} components, {tokens} tokens")
    return layout
