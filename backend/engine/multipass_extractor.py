# backend/engine/multipass_extractor.py
# Universal Multi-Pass AI Requirement Normalization (v2 — Completeness Enforced)
#
# Pass 1A → Domain Analysis            (understand context & equipment)
# Pass 1B → Signal Normalization       (formalize signals + derived internals + outputs)
# Pass 1C → Control Model Builder      (state machine + transitions)
# Post    → Completeness Checker       (guarantee outputs, internals, safety mapping)
#
# All passes: temperature=0.05.  No API key overwritten.

import json
import logging
import re
from backend.openai_client import safe_chat_completion, DEFAULT_MODEL


# ── PASS 1A: DOMAIN ANALYSIS ──────────────────────────────────────────────────

_DOMAIN_SYSTEM_PROMPT = """You are an industrial automation systems analyst.

From the user description, extract a structured system understanding.

Return ONLY valid JSON — no explanation, no code:

{
  "system_category": "monitoring" | "control" | "hybrid",
  "domain_type": "conveyor" | "pump" | "tank" | "motor" | "hvac" | "batch" | "temperature" | "packaging" | "mixing" | "traffic_light" | "press" | "elevator" | "gate" | "car_wash" | "compressor" | "water_treatment" | "sorter" | "crane" | "safety_interlock" | "general",
  "equipment": [],
  "motion_elements": [],
  "sensors": [],
  "actuators": [],
  "safety_elements": [],
  "timing_requirements": [],
  "process_description": "",
  "suggested_program_name": ""
}

RULES:
- domain_type: pick the single closest category for the described process.
  Use these mappings:
    traffic light / intersection / signal / red-green-yellow → traffic_light
    hydraulic press / punch press / stamping / clamp-and-press / ram / two-hand safety → press
    elevator / lift / floor control / cabin / shaft → elevator
    gate / barrier / rolling door / parking gate / sliding door → gate
    car wash / wash station / rinse / spray / vehicle wash → car_wash
    air compressor / pneumatic supply / compressed air → compressor
    water treatment / filtration / clarifier / dosing + pH → water_treatment
    sorter / sorting / diverter / classification / barcode scan → sorter
    crane / hoist / overhead crane / trolley / winch → crane
    safety interlock / guard / light curtain / two-hand → safety_interlock
- suggested_program_name: a short CamelCase IEC-valid name, e.g. TrafficLightControl,
  HydraulicPress, ElevatorControl, ConveyorControl, PumpProtection.
- safety_elements: ALWAYS include at least one emergency stop element.
"""

# ── PASS 1B: SIGNAL NORMALIZATION (enriched — derived internals required) ────

_SIGNAL_SYSTEM_PROMPT = """You are a PLC signal normalization engine.

Convert the domain analysis into a complete, normalized PLC signal map.

Return ONLY valid JSON — no explanation, no code:

{
  "inputs":           [],
  "outputs":          [],
  "internal_states":  [],
  "timers":           [],
  "counters":         [],
  "analog_values":    [],
  "safety_conditions":[],
  "events":           []
}

STRICT RULES — you MUST follow all of them:

1. CRITICAL: If "LOCKED_SIGNALS" are present in the input, you MUST use those EXACT
   variable names for inputs, outputs, and timers. Do NOT rename, abbreviate, or
   replace any locked signal. You may ADD derived internal states (M_ prefix) but
   you must NEVER remove or rename locked signals.
2. All sensors → inputs (prefix I_, e.g. "I_PartSensor", "I_LevelHigh").
3. All actuators → outputs (prefix Q_, e.g. "Q_ConveyorMotor", "Q_Pump").
4. Derived internal flag for EACH motion/process element → internal_states
   (prefix M_, e.g. "M_Running", "M_Fault").
5. ALL safety elements → safety_conditions. ALWAYS include "I_EStop" as a safety input.
6. Time-based logic → timers (prefix T_). Use LOCKED_SIGNALS timer names exactly.
7. Edge-triggered input events (pushbuttons/momentary contacts) → events list.
8. NEVER leave outputs empty for control systems.
9. OUTPUT NAMING RULES — CRITICAL:
   - Names MUST be SHORT (max 20 chars) using equipment abbreviations.
   - Good: Q_ConveyorMotor, Q_FeedPump, Q_InletValve, Q_Alarm, Q_StatusRun
   - BAD (FORBIDDEN): Q_Along_a_conveyor, Q_Start_the_pump, Q_Turn_on_motor
   - Use: Motor, Pump, Valve, Belt, Fan, Heater, Alarm, Ready, Fault
   - NEVER use prepositions, articles, or full sentences in names.
10. INPUT NAMING RULES:
    - Good: I_Start, I_Stop, I_EStop, I_PartSensor, I_LevelHigh, I_TempHigh
    - BAD: I_Start_the_conveyor, I_Emergency_stop_button
11. ALWAYS include I_Start, I_Stop, I_EStop in inputs for any control system.
12. For conveyor/belt systems: add I_PartSensor, I_JamSensor to inputs.
13. For pump/motor systems: add I_Overload, I_FlowFault to inputs.
14. For tank/filling systems: add I_LevelHigh, I_LevelLow to inputs.
15. For traffic_light systems: outputs MUST be Q_Red, Q_Yellow, Q_Green.
    Add Q_PedestrianWalk if pedestrians mentioned. Inputs: I_PedestrianButton, I_VehicleDetector.
    Timers: T_Red (10s), T_Green (10s), T_Yellow (3s). NO industrial press signals.
16. For press/stamping systems: outputs Q_RamExtend, Q_RamRetract, Q_Clamp, Q_PressValve.
    Inputs: I_TwoHand1, I_TwoHand2, I_GuardClosed, I_RamTop, I_RamBottom, I_PressureOK.
17. For elevator/lift systems: outputs Q_MotorUp, Q_MotorDown, Q_DoorOpen.
    Inputs: I_DoorClosed, I_FloorSensor, I_UpperLimit, I_LowerLimit, I_Overload.
18. For gate/barrier systems: outputs Q_GateOpen, Q_GateClose.
    Inputs: I_GateOpen, I_GateClosed, I_ObstacleSensor, I_CardReader.
19. For crane/hoist systems: outputs Q_HoistUp, Q_HoistDown, Q_TravelLeft, Q_TravelRight.
    Inputs: I_UpperLimit, I_LowerLimit, I_OverloadSwitch, I_SlackRope.
"""

# ── PASS 1C: CONTROL MODEL BUILDER ───────────────────────────────────────────

_CONTROL_MODEL_SYSTEM_PROMPT = """You are a PLC control model architect.

Convert the normalized signal map into a deterministic state-machine control model.

Return ONLY valid JSON — no explanation, no code:

{
  "states":           [],
  "transitions":      [],
  "actions":          [],
  "safety_overrides": [],
  "clamping_rules":   []
}

STRICT RULES:
1. CRITICAL: If "LOCKED_STATES" are present in the input, you MUST use those EXACT
   state IDs and names. Do NOT invent new state names or renumber states.
2. All states must have id (integer), name (string), and description. State 0 = Idle.
3. MINIMUM STATE MACHINE: You MUST generate at least 4 states:
   {"id": 0, "name": "Idle"}, {"id": 1, "name": "Starting"}, {"id": 2, "name": "Running"}, {"id": 3, "name": "Fault"}
   For systems with a stop/cooldown sequence, also add {"id": 3, "name": "Stopping"} and move Fault to id 4.
4. Transitions: { "from": state_id, "to": state_id, "event": "input/condition", "fault_code": int_or_null }
   Use ONLY variable names that exist in the signal map.
5. Actions: { "state": state_id, "output": "Q_XXX", "value": true/false }
   Output names MUST match the outputs list from signal_map exactly.
6. safety_overrides: list the E-Stop input name (e.g. ["I_EStop"]).
7. FAULT_CODES: if provided, add "fault_code" field to transitions that go to a fault state.
   Always include FaultCode 10 = E-Stop in the fault handling.
8. NO invented variable names — only use names from signal_map and locked states.
9. transitions MUST include: Start→Running, Stop→Idle/Stopping, and any fault conditions.
"""


def _llm_json_pass(system_prompt: str, user_content: str, api_key: str = None) -> tuple[dict, int]:
    """Call LLM expecting a JSON response. Returns (parsed_dict, tokens)."""
    kwargs = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.05,
        "response_format": {"type": "json_object"}
    }
    if api_key:
        kwargs["api_key"] = api_key

    response = safe_chat_completion(**kwargs)
    content = response.choices[0].message.content.strip()
    tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
    return json.loads(content), tokens


def _normalize(name: str) -> str:
    """Ensure signal names are PLC-valid (no spaces, alphanumeric + underscore)."""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(name).strip())
    return cleaned if cleaned else "Signal"


_DOMAIN_OUTPUT_MAP = {
    # domain_type → (primary_output, alarm_output, extra_inputs)
    # ── Motion / Transport ────────────────────────────────────────────────────
    "conveyor":         ("Q_ConveyorMotor",  "Q_Alarm",  ["I_PartSensor",    "I_JamSensor"]),
    "packaging":        ("Q_PackMotor",      "Q_Alarm",  ["I_PartSensor",    "I_JamSensor"]),
    "sorter":           ("Q_SortValve",      "Q_Alarm",  ["I_PartSensor",    "I_BarcodeScan"]),
    # ── Fluid / Level ─────────────────────────────────────────────────────────
    "pump":             ("Q_PumpMotor",      "Q_Alarm",  ["I_LevelLow",      "I_Overload"]),
    "tank":             ("Q_FillValve",      "Q_Alarm",  ["I_LevelHigh",     "I_LevelLow"]),
    "mixing":           ("Q_MixerMotor",     "Q_Alarm",  ["I_LevelLow",      "I_TempHigh"]),
    "water_treatment":  ("Q_DosePump",       "Q_Alarm",  ["I_PHSensor",      "I_TurbidityHigh"]),
    # ── Thermal ───────────────────────────────────────────────────────────────
    "heater":           ("Q_Heater",         "Q_Alarm",  ["I_TempHigh",      "I_ThermalFault"]),
    "temperature":      ("Q_Heater",         "Q_Alarm",  ["I_TempHigh",      "I_ThermalFault"]),
    # ── Motion / Rotating ─────────────────────────────────────────────────────
    "motor":            ("Q_Motor",          "Q_Alarm",  ["I_Overload",      "I_ThermalFault"]),
    "compressor":       ("Q_CompMotor",      "Q_Alarm",  ["I_PressureHigh",  "I_Overload"]),
    # ── HVAC / Ventilation ────────────────────────────────────────────────────
    "hvac":             ("Q_Fan",            "Q_Alarm",  ["I_TempHigh",      "I_FilterFault"]),
    # ── Chemical / Dosing ─────────────────────────────────────────────────────
    "dosing":           ("Q_DosePump",       "Q_Alarm",  ["I_AgitatorRunning","I_SafetyValveOpen"]),
    # ── Batch / Reactor ───────────────────────────────────────────────────────
    "batch":            ("Q_AgitatorMotor",  "Q_Alarm",  ["I_LevelHigh",     "I_TempHigh"]),
    "reactor":          ("Q_AgitatorMotor",  "Q_Alarm",  ["I_LevelHigh",     "I_TempHigh"]),
    # ── Traffic / Infrastructure ──────────────────────────────────────────────
    "traffic_light":    ("Q_Green",          "Q_Yellow", ["I_PedestrianButton","I_VehicleDetector"]),
    # ── Machine Safety / Press ────────────────────────────────────────────────
    "press":            ("Q_RamExtend",      "Q_Alarm",  ["I_TwoHand1",      "I_TwoHand2",
                                                           "I_GuardClosed",   "I_RamTop",
                                                           "I_RamBottom",     "I_PressureOK"]),
    "safety_interlock": ("Q_SafetyRelay",   "Q_Alarm",  ["I_GuardClosed",   "I_LightCurtain"]),
    # ── Material Handling ─────────────────────────────────────────────────────
    "elevator":         ("Q_MotorUp",        "Q_Alarm",  ["I_DoorClosed",    "I_FloorSensor",
                                                           "I_UpperLimit",    "I_LowerLimit"]),
    "crane":            ("Q_HoistUp",        "Q_Alarm",  ["I_UpperLimit",    "I_LowerLimit",
                                                           "I_Overload",      "I_SlackRope"]),
    "gate":             ("Q_GateOpen",       "Q_Alarm",  ["I_GateOpen",      "I_GateClosed",
                                                           "I_ObstacleSensor"]),
    # ── Miscellaneous ─────────────────────────────────────────────────────────
    "car_wash":         ("Q_WashMotor",      "Q_Alarm",  ["I_VehiclePresent","I_DoorClosed"]),
    # ── Fallback ──────────────────────────────────────────────────────────────
    "general":          ("Q_Motor",          "Q_Alarm",  []),
}

# ── Deterministic keyword pre-classifier ─────────────────────────────────────
# Runs BEFORE the LLM Pass 1A.  Higher entries have priority.
# Each entry: (domain_type, [keyword_fragments_lowercase])
_DOMAIN_KEYWORD_MAP: list[tuple[str, list[str]]] = [
    # Traffic / Infrastructure
    ("traffic_light",   ["traffic light", "traffic signal", "traffic control",
                          "intersection", "pedestrian signal", "red light",
                          "green light", "yellow light", "road signal",
                          "signal timing", "traffic lamp"]),
    # Machine Safety / Press
    ("press",           ["hydraulic press", "punch press", "stamping press",
                          "ram extend", "ram retract", "two-hand safety",
                          "two hand safety", "press machine", "clamp and press"]),
    # Elevator / Lift
    ("elevator",        ["elevator", "lift control", "floor control",
                          "floor sensor", "cabin", "lift shaft", "motor up",
                          "motor down"]),
    # Gate / Door
    ("gate",            ["parking gate", "rolling door", "sliding gate",
                          "barrier control", "gate control", "automatic gate",
                          "boom gate"]),
    # Car Wash
    ("car_wash",        ["car wash", "vehicle wash", "wash station",
                          "pre-wash", "rinse cycle", "drying blower"]),
    # Crane / Hoist
    ("crane",           ["crane control", "overhead crane", "hoist control",
                          "trolley control", "winch", "bridge crane"]),
    # Compressor
    ("compressor",      ["air compressor", "compressor control",
                          "pneumatic supply", "compressed air"]),
    # Water Treatment
    ("water_treatment", ["water treatment", "filtration plant", "clarifier",
                          "chlorination", "ph dosing", "water filtration"]),
    # Sorter
    ("sorter",          ["sorting system", "diverter", "sorter control",
                          "barcode sorter", "classification system"]),
    # Safety Interlock — use full phrases to avoid matching "safety interlocks" as a qualifier
    ("safety_interlock",["safety interlock system", "safety interlock controller",
                          "light curtain control", "guard monitoring relay",
                          "safety relay module", "category 3 safety"]),
    # Conveyor / Transport
    ("conveyor",        ["conveyor", "belt conveyor", "transport belt",
                          "parts conveyor", "assembly line conveyor"]),
    # Packaging
    ("packaging",       ["packaging", "packing line", "filling machine",
                          "bottling line", "labelling"]),
    # Pump
    ("pump",            ["pump station", "pump control", "pumping",
                          "booster pump", "submersible pump"]),
    # Tank / Level
    ("tank",            ["tank filling", "tank level", "vessel filling",
                          "sump control", "reservoir"]),
    # Batch / Reactor
    ("batch",           ["batch control", "batch reactor", "recipe control",
                          "batch process", "batch production"]),
    ("reactor",         ["chemical reactor", "cstr", "pfr"]),
    # Mixing
    ("mixing",          ["mixing system", "agitator control", "blending"]),
    # Dosing
    ("dosing",          ["chemical dosing", "dosing pump", "chemical injection",
                          "metering pump"]),
    # HVAC
    ("hvac",            ["hvac", "air conditioning", "ventilation system",
                          "climate control", "ahu control", "fan control"]),
    # Heater / Temperature
    ("heater",          ["heater control", "heating element", "oven control",
                          "furnace control"]),
    ("temperature",     ["temperature control", "temperature regulation",
                          "pid temperature", "thermal control"]),
    # Motor Starter
    ("motor",           ["motor starter", "motor control centre",
                          "direct online", "star delta", "vfd control"]),
]


def _pre_classify_domain(description: str) -> str | None:
    """
    Deterministically classify the domain from keyword matching before
    calling the LLM.  Returns a domain_type string or None if no match.
    Priority follows the order of _DOMAIN_KEYWORD_MAP (first match wins).
    """
    desc_lc = description.lower()
    for domain, keywords in _DOMAIN_KEYWORD_MAP:
        if any(kw in desc_lc for kw in keywords):
            return domain
    return None

_BAD_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_]")


def _sanitize_signal_name(name: str, prefix: str = "") -> str:
    """Sanitize a signal name: remove bad chars, enforce prefix, limit length."""
    clean = _BAD_NAME_PATTERN.sub("_", str(name).strip())
    # Collapse multiple underscores
    clean = re.sub(r"_+", "_", clean).strip("_")
    # Enforce prefix if missing
    if prefix and not clean.startswith(prefix):
        clean = f"{prefix}{clean}"
    # Limit length to 30 chars
    return clean[:30] if clean else f"{prefix}Signal"


def _enforce_completeness(domain: dict, signal_map: dict) -> dict:
    """
    Post-pass completeness enforcer.
    Guarantees: E-Stop exists, outputs named properly, domain signals added,
    counters matched to internals.
    Mutates and returns the signal_map.
    """
    cat         = domain.get("system_category", "control").lower()
    domain_type = domain.get("domain_type", "general").lower()
    sm          = signal_map

    # Guarantee lists exist
    for key in ("inputs", "outputs", "internal_states", "timers",
                "counters", "analog_values", "safety_conditions", "events"):
        if key not in sm:
            sm[key] = []

    # ── Sanitize output names (kill descriptive garbage like Q_Along_a_conveyor) ──
    cleaned_outputs = []
    for out in sm["outputs"]:
        n = str(out).strip()
        # Reject names that are too long or contain spaces/lowercase words after prefix
        if (len(n) > 25 or n.count("_") > 3
                or any(kw in n.lower() for kw in (" ", "along", "start_the", "turn_on",
                                                    "move_the", "activate_the"))):
            # Replace with domain default
            dt = domain_type
            n = _DOMAIN_OUTPUT_MAP.get(dt, _DOMAIN_OUTPUT_MAP["general"])[0]
        cleaned_outputs.append(_sanitize_signal_name(n, "Q_") if not n.startswith("Q_") else n)
    sm["outputs"] = cleaned_outputs

    # ── Sanitize input names ───────────────────────────────────────────────────
    sm["inputs"] = [
        _sanitize_signal_name(str(s), "I_") if not str(s).startswith("I_") else str(s)
        for s in sm["inputs"]
    ]

    # ── Rule: Always inject I_EStop if no safety input exists ─────────────────
    has_estop = any(
        any(kw in str(s).upper() for kw in ("ESTOP", "E_STOP", "EMERGENCY"))
        for s in sm["inputs"] + sm["safety_conditions"]
    )
    if not has_estop:
        # Insert at top of inputs list (highest priority)
        sm["inputs"].insert(0, "I_EStop")
        sm["safety_conditions"].append("I_EStop")

    # ── Rule: Always inject I_Start, I_Stop for control systems ───────────────
    for required_input in ("I_Start", "I_Stop"):
        if required_input not in sm["inputs"]:
            # Only add if no similar input exists
            if not any(required_input.lower() in str(s).lower() for s in sm["inputs"]):
                sm["inputs"].insert(0, required_input)

    # ── Rule: Add domain-specific signals if missing ──────────────────────────
    domain_defaults = _DOMAIN_OUTPUT_MAP.get(domain_type, _DOMAIN_OUTPUT_MAP["general"])
    primary_out, alarm_out, extra_inputs = domain_defaults

    # Ensure alarm output exists
    has_alarm = any("alarm" in str(o).lower() or "fault" in str(o).lower()
                    for o in sm["outputs"])
    if not has_alarm:
        sm["outputs"].append(alarm_out)

    # Add domain-specific inputs if the input list is very sparse (only Start/Stop/EStop)
    meaningful_inputs = [s for s in sm["inputs"]
                         if str(s) not in ("I_Start", "I_Stop", "I_EStop")]
    if len(meaningful_inputs) < 1 and extra_inputs:
        for extra in extra_inputs:
            sm["inputs"].append(extra)

    # ── Rule: monitoring/hybrid must have at least one output ─────────────────
    if cat in ("monitoring", "hybrid", "control") and not sm["outputs"]:
        sm["outputs"].append(primary_out)

    # ── Rule: safety elements from domain analysis → safety_conditions ────────
    for sf in domain.get("safety_elements", []):
        sname = f"I_E_{_normalize(sf)}"
        if sname not in sm["inputs"] and sname not in sm["safety_conditions"]:
            sm["safety_conditions"].append(sname)
            sm["inputs"].append(sname)

    # ── Rule: counters must also have matching M_ internal state ──────────────
    for ctr in list(sm.get("counters", [])):
        cname = f"M_{_normalize(ctr)}" if not str(ctr).startswith("M_") else str(ctr)
        if cname not in sm["internal_states"]:
            sm["internal_states"].append(cname)

    # ── Rule: deduplicate all lists ───────────────────────────────────────────
    for key in ("inputs", "outputs", "internal_states", "timers",
                "counters", "analog_values", "safety_conditions", "events"):
        seen = set()
        deduped = []
        for item in sm[key]:
            k = str(item)
            if k not in seen:
                seen.add(k)
                deduped.append(item)
        sm[key] = deduped

    return sm


class MultiPassExtractor:
    """
    Universal 3-pass industrial requirement normalizer with completeness enforcement.
    Accepts optional locked_signals and locked_states from the PromptParser to
    guarantee that explicitly declared I/O names are never renamed by the AI.
    """

    def execute(
        self,
        user_prompt: str,
        api_key: str = None,
        locked_signals: dict = None,
        locked_states: list = None,
        fault_codes: dict = None,
    ) -> tuple[dict, int]:
        """
        Run all 3 passes + completeness check.
        locked_signals — if provided, these exact signal names override Pass 1B output.
        locked_states  — if provided, these exact states override Pass 1C output.
        fault_codes    — {code_int: description} injected into control model.
        Returns (extraction_result, total_tokens).
        """
        total_tokens = 0

        # ── Pre-classify domain deterministically (before LLM) ───────────────
        pre_domain = _pre_classify_domain(user_prompt)
        if pre_domain:
            print(f"    [MultiPass pre] Keyword domain: '{pre_domain}'")

        # ── Pass 1A: Domain Analysis ──────────────────────────────────────────
        print("    [MultiPass 1A] Domain analysis...")
        try:
            # Inject pre-classified domain as a hint so the LLM doesn't drift
            prompt_1a = user_prompt
            if pre_domain:
                prompt_1a = (
                    f"[DOMAIN HINT — use this in domain_type unless clearly wrong]: {pre_domain}\n\n"
                    + user_prompt
                )
            domain, t1a = _llm_json_pass(_DOMAIN_SYSTEM_PROMPT, prompt_1a, api_key)
            total_tokens += t1a
            # If the pre-classifier is confident and the LLM returned "general", override
            if pre_domain and domain.get("domain_type", "general") == "general":
                domain["domain_type"] = pre_domain
                print(f"       LLM returned 'general' — overriding with pre-classified: '{pre_domain}'")
            system_type = domain.get("system_category", "control").lower()
            print(f"       domain={domain.get('domain_type','?')}, category={system_type}, "
                  f"sensors={len(domain.get('sensors', []))}, "
                  f"actuators={len(domain.get('actuators', []))}, "
                  f"safety={len(domain.get('safety_elements', []))}")
        except Exception as e:
            logging.warning(f"[MultiPass 1A] failed: {e} — using fallback")
            domain = {
                "system_category": "control",
                "domain_type": pre_domain or "general",
                "process_description": user_prompt,
            }
            system_type = "control"

        # ── Pass 1B: Signal Normalization ─────────────────────────────────────
        print("    [MultiPass 1B] Signal normalization (with derived internals)...")
        pass1b_input = {"domain": domain, "user_prompt": user_prompt}
        if locked_signals:
            # Tell the AI what names are LOCKED so it cannot invent alternatives
            pass1b_input["LOCKED_SIGNALS"] = {
                "inputs": locked_signals.get("inputs", []),
                "outputs": locked_signals.get("outputs", []),
                "timers": locked_signals.get("timers", []),
            }
        try:
            signal_map, t1b = _llm_json_pass(
                _SIGNAL_SYSTEM_PROMPT,
                json.dumps(pass1b_input),
                api_key
            )
            total_tokens += t1b
        except Exception as e:
            logging.warning(f"[MultiPass 1B] failed: {e} — using domain fallback")
            signal_map = {
                "inputs": [f"I_{_normalize(s)}" for s in domain.get("sensors", [])],
                "outputs": [f"Q_{_normalize(a)}" for a in domain.get("actuators", [])],
                "internal_states": [],
                "timers": [f"T_{_normalize(t)}" for t in domain.get("timing_requirements", [])],
                "counters": [],
                "analog_values": [],
                "safety_conditions": [f"I_E_{_normalize(s)}" for s in domain.get("safety_elements", [])],
                "events": []
            }

        # ── HARD ENFORCEMENT: Override AI output with locked signals ──────────
        # This is the critical fix: regardless of what the AI generated in Pass 1B,
        # if the user explicitly declared their I/O we use those EXACT names.
        if locked_signals:
            print("    [MultiPass 1B+] Enforcing locked signal names from prompt...")
            if locked_signals.get("inputs"):
                signal_map["inputs"] = locked_signals["inputs"]
            if locked_signals.get("outputs"):
                signal_map["outputs"] = locked_signals["outputs"]
            if locked_signals.get("timers"):
                signal_map["timers"] = locked_signals["timers"]
            if locked_signals.get("timer_presets"):
                signal_map["timer_presets"] = locked_signals["timer_presets"]
            if locked_signals.get("events"):
                signal_map["events"] = locked_signals["events"]
            if locked_signals.get("safety_conditions"):
                signal_map["safety_conditions"] = locked_signals["safety_conditions"]
            if locked_signals.get("fault_codes"):
                signal_map["fault_codes"] = locked_signals["fault_codes"]
            print(f"       Locked: inputs={len(signal_map['inputs'])}, "
                  f"outputs={len(signal_map['outputs'])}, "
                  f"timers={len(signal_map['timers'])}")

        # ── Completeness Check ────────────────────────────────────────────────
        print("    [MultiPass 1B+] Signal completeness enforcement...")
        signal_map = _enforce_completeness(domain, signal_map)
        print(f"       inputs={len(signal_map.get('inputs', []))}, "
              f"outputs={len(signal_map.get('outputs', []))}, "
              f"internals={len(signal_map.get('internal_states', []))}, "
              f"safety={len(signal_map.get('safety_conditions', []))}")

        # ── Pass 1C: Control Model Builder ────────────────────────────────────
        print("    [MultiPass 1C] Control model construction...")
        pass1c_input = {"signal_map": signal_map}
        if locked_states:
            pass1c_input["LOCKED_STATES"] = locked_states
        if fault_codes:
            pass1c_input["FAULT_CODES"] = fault_codes
        try:
            control_model, t1c = _llm_json_pass(
                _CONTROL_MODEL_SYSTEM_PROMPT,
                json.dumps(pass1c_input),
                api_key
            )
            total_tokens += t1c
            print(f"       states={len(control_model.get('states', []))}, "
                  f"transitions={len(control_model.get('transitions', []))}, "
                  f"safety_overrides={len(control_model.get('safety_overrides', []))}")
        except Exception as e:
            logging.warning(f"[MultiPass 1C] failed: {e} — using empty model fallback")
            control_model = {
                "states": locked_states or [{"id": 0, "name": "Idle", "description": "Initial state"}],
                "transitions": [],
                "actions": [],
                "safety_overrides": [],
                "clamping_rules": []
            }

        # ── HARD ENFORCEMENT: Override control model states if locked ─────────
        if locked_states:
            print("    [MultiPass 1C+] Enforcing locked states from prompt...")
            control_model["states"] = locked_states
        if locked_signals and locked_signals.get("safety_conditions"):
            control_model["safety_overrides"] = locked_signals["safety_conditions"]
        if fault_codes:
            control_model["fault_codes"] = fault_codes

        return {
            "domain": domain,
            "signal_map": signal_map,
            "control_model": control_model,
            "system_type": system_type
        }, total_tokens
