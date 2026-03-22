"""
HMI Agentic Pipeline — Industrial Grade v3
===========================================
Generates rich JSON schemas with:
- Process connections (pipe routes between components)
- ISA-5.1 instrument tags
- Alarm thresholds (hi/lo limits)
- Simulation parameters (physics-based process model)
- Interactive control bindings
"""

import json
import logging
from backend.core.openai_client import generate_layout

logger = logging.getLogger(__name__)


class HMIValidationError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []


# ── SYSTEM PROMPTS ─────────────────────────────────────────────────────────────

GENERATOR_SYSTEM_PROMPT = """\
You are a Senior SCADA/HMI Design Engineer at Siemens.
Generate an industrial-grade HMI layout JSON for a real process control system.
Output ONLY a single valid JSON object. No markdown, no explanation.

FULL SCHEMA (return all applicable fields):
{
  "system_name": "string  (e.g. 'Water Treatment Plant - Unit 1')",
  "mode": "normal",
  "theme": "water" | "motor" | "hvac" | "chemical" | "food" | "default",

  "components": [
    {
      "type": "tank" | "pump" | "valve" | "motor" | "fan" | "compressor" |
              "sensor_level" | "sensor_temp" | "sensor_pressure" | "sensor_flow" |
              "gauge" | "alarm" | "button" | "slider",
      "id":    "unique_id (e.g. TK-101, P-101, V-101, LT-101)",
      "label": "Human readable name",
      "tag":   "ISA tag (e.g. LT-101, PT-201, FT-301)",
      "state": "running" | "stopped" | "open" | "closed" | "active" | "inactive",
      "value": number_or_null,
      "unit":  "%" | "°C" | "bar" | "m³/h" | "rpm" | "kW" | null,
      "x": number,
      "y": number,
      "sim": {
        "role":       "source" | "sink" | "transfer" | "control" | "measure",
        "fill_rate":   number (L/s, positive = fills connected tank),
        "drain_rate":  number (L/s, positive = drains connected tank),
        "capacity":    number (liters, for tanks only),
        "hi_alarm":    number (e.g. 90 for 90% level or 85°C),
        "lo_alarm":    number (e.g. 10 for 10% level),
        "hi_hi_alarm": number (critical high, e.g. 95),
        "lo_lo_alarm": number (critical low, e.g. 5),
        "normal_min":  number,
        "normal_max":  number
      }
    }
  ],

  "connections": [
    {
      "from": "component_id",
      "to":   "component_id",
      "type": "pipe" | "signal" | "control_loop",
      "label": "optional pipe tag (e.g. 2-P-101-50A)",
      "active_when": "running" | "open" | "always"
    }
  ],

  "alarms": [
    {
      "id": "alarm_id",
      "tag": "ALM-101",
      "description": "Tank TK-101 High Level",
      "source_component": "component_id",
      "condition": "value > 90",
      "priority": "critical" | "high" | "medium" | "low",
      "action": "Close V-101, Stop P-101"
    }
  ],

  "process_description": "Brief description of the process this HMI controls"
}

PLACEMENT RULES:
- Canvas = 900x650 pixels. Do NOT place components outside this area.
- Tank width ~100px, height ~140px — keep 120px clearance between tanks
- Pump ~90px — place between tank and valve in flow direction
- Valve ~70px — place before/after each tank connection
- Sensors ~60px — place near the equipment they measure
- Gauges ~80px — place in instrument row above or below main equipment
- Alarms ~60px — group together in top-right area
- Buttons ~100px wide — place in bottom control panel area

CONNECTIONS:
- Always define pipe connections between tanks, pumps, and valves
- Define signal connections between sensors and alarms
- Define control_loop connections between controllers and final elements

SIMULATION PARAMETERS (must be realistic):
- Water/chemical tank: capacity 5000-50000 L, fill_rate 10-100 L/s
- Industrial pump: fill_rate 20-200 L/s
- Control valve: modulates fill_rate by 0-100% setpoint
- Temperature: hi_alarm 80°C, lo_alarm 5°C
- Pressure: hi_alarm 8 bar, lo_alarm 0.5 bar
- Level: hi_alarm 90%, lo_alarm 10%, hi_hi 95%, lo_lo 5%

THEME SELECTION:
- water/chemical = blue/cyan accents
- motor/conveyor = orange/amber accents
- hvac = teal/green accents
- food/pharma = white/clean accents
- default = standard blue

GENERATE COMPLETE, REALISTIC DATA:
- Minimum 6 components for any process
- At least 2 tanks if liquid process
- At least 1 pump per tank
- At least 1 valve per pump outlet
- At least 2 level/temp/pressure sensors
- At least 2 alarms
- At least 1 start button, 1 stop button, 1 e-stop button
- Fill all sim parameters with realistic values
"""

FIXER_SYSTEM_PROMPT = """\
You are an HMI JSON Fixer. Fix validation errors and return ONLY the corrected JSON.
Preserve all existing fields. No markdown, no explanation.
"""


# ── VALIDATION ─────────────────────────────────────────────────────────────────

def validate_hmi_layout(layout: dict):
    errors = []
    if "mode" not in layout and "view_mode" not in layout:
        errors.append("Missing 'mode' field.")
    comps = layout.get("components")
    if not isinstance(comps, list) or len(comps) == 0:
        errors.append("'components' list is missing or empty.")
    else:
        for i, c in enumerate(comps):
            if "type" not in c:
                errors.append(f"Component[{i}] missing 'type'.")
            if "x" not in c or "y" not in c:
                errors.append(f"Component[{i}] ({c.get('type','?')}) missing x/y coordinates.")
    if errors:
        raise HMIValidationError("Validation failed", errors)


# ── FALLBACK ───────────────────────────────────────────────────────────────────

def _fallback_stub(description: str) -> dict:
    return {
        "system_name": "Industrial Control System",
        "mode": "normal",
        "theme": "default",
        "process_description": description,
        "components": [
            {"type": "tank",   "id": "TK-101", "label": "Process Tank",  "tag": "TK-101",
             "state": "inactive", "value": 50, "unit": "%", "x": 200, "y": 200,
             "sim": {"role":"sink","fill_rate":0,"drain_rate":0,"capacity":10000,
                     "hi_alarm":90,"lo_alarm":10,"hi_hi_alarm":95,"lo_lo_alarm":5,
                     "normal_min":20,"normal_max":80}},
            {"type": "pump",   "id": "P-101",  "label": "Feed Pump",     "tag": "P-101",
             "state": "stopped", "value": None, "unit": None, "x": 400, "y": 250,
             "sim": {"role":"transfer","fill_rate":30,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
            {"type": "valve",  "id": "V-101",  "label": "Inlet Valve",   "tag": "V-101",
             "state": "closed", "value": 0, "unit": "%", "x": 300, "y": 250,
             "sim": {"role":"control","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
            {"type": "sensor_level", "id": "LT-101", "label": "Tank Level", "tag": "LT-101",
             "state": "active", "value": 50, "unit": "%", "x": 150, "y": 160,
             "sim": {"role":"measure","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":90,"lo_alarm":10,"hi_hi_alarm":95,"lo_lo_alarm":5,
                     "normal_min":20,"normal_max":80}},
            {"type": "alarm",  "id": "ALM-101","label": "High Level Alarm","tag": "ALM-101",
             "state": "inactive","value": None,"unit": None,"x": 700,"y": 100,
             "sim": {"role":"measure","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
            {"type": "button", "id": "PB-START","label": "Start",         "tag": "PB-001",
             "state": "inactive","value": None,"unit": None,"x": 100,"y": 550,
             "sim": {"role":"control","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
            {"type": "button", "id": "PB-STOP", "label": "Stop",          "tag": "PB-002",
             "state": "inactive","value": None,"unit": None,"x": 230,"y": 550,
             "sim": {"role":"control","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
            {"type": "button", "id": "PB-ESTOP","label": "Emergency Stop","tag": "PB-000",
             "state": "inactive","value": None,"unit": None,"x": 360,"y": 550,
             "sim": {"role":"control","fill_rate":0,"drain_rate":0,"capacity":0,
                     "hi_alarm":None,"lo_alarm":None,"hi_hi_alarm":None,"lo_lo_alarm":None,
                     "normal_min":None,"normal_max":None}},
        ],
        "connections": [
            {"from": "P-101", "to": "TK-101", "type": "pipe", "label": "2-P-101", "active_when": "running"},
            {"from": "V-101", "to": "P-101",  "type": "pipe", "label": "2-V-101", "active_when": "open"},
            {"from": "LT-101","to": "ALM-101","type": "signal","label": "","active_when": "always"},
        ],
        "alarms": [
            {"id": "ALM-101","tag": "ALM-101","description": "Tank TK-101 High Level",
             "source_component": "TK-101","condition": "value > 90",
             "priority": "high","action": "Close V-101, Stop P-101"}
        ],
        "_generation_note": "Fallback layout — LLM unavailable or timed out."
    }


# ── MAIN PIPELINE ──────────────────────────────────────────────────────────────

def run_hmi_agentic_pipeline(description: str, api_key: str = None) -> dict:
    """
    Two-stage pipeline:
      Stage 1 — Generate rich industrial JSON from description   (1 LLM call)
      Stage 2 — Validate; if invalid fix once                    (max 1 extra call)
    """
    MAX_RETRIES = 1

    logger.info("[HMI Stage 1] Generating industrial HMI JSON…")
    print("[HMI Stage 1] Generating structured industrial HMI JSON…")

    layout: dict = {}
    total_tokens = 0

    try:
        raw, tok = generate_layout(GENERATOR_SYSTEM_PROMPT, description, api_key=api_key)
        total_tokens += tok
        layout = json.loads(raw)
    except Exception as e:
        logger.error(f"[HMI] Generator failed: {e}")
        print(f"[HMI Stage 1] Generator error: {e}. Returning fallback.")
        stub = _fallback_stub(description)
        stub["_tokens_used"] = 0
        return stub

    logger.info("[HMI Stage 2] Validating output…")
    print("[HMI Stage 2] Validating…")

    for attempt in range(MAX_RETRIES + 1):
        try:
            validate_hmi_layout(layout)
            print(f"[HMI] Validation passed (attempt {attempt + 1})")
            layout.setdefault("mode", "normal")
            layout.setdefault("theme", "default")
            layout.setdefault("connections", [])
            layout.setdefault("alarms", [])
            layout["_tokens_used"] = total_tokens
            return layout
        except HMIValidationError as ve:
            if attempt == MAX_RETRIES:
                print("[HMI] Validation still failing after fix — returning best-effort layout.")
                layout["_tokens_used"] = total_tokens
                return layout

            print(f"[HMI] Validation errors: {ve.errors} → Calling fixer…")
            fix_prompt = (
                f"User request: {description}\n\n"
                f"Previous output:\n{json.dumps(layout, indent=2)}\n\n"
                f"Validation errors:\n" + "\n".join(f"- {e}" for e in ve.errors) +
                "\n\nReturn the corrected JSON only."
            )
            try:
                raw, tok = generate_layout(FIXER_SYSTEM_PROMPT, fix_prompt, api_key=api_key)
                total_tokens += tok
                layout = json.loads(raw)
            except Exception as fix_e:
                logger.error(f"[HMI] Fixer failed: {fix_e}")
                layout["_tokens_used"] = total_tokens
                return layout

    layout["_tokens_used"] = total_tokens
    return layout
