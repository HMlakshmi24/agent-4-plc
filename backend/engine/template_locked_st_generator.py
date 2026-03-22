# backend/engine/template_locked_st_generator.py
# Template-Locked IEC ST Generator v2 — Variable Guard Enforced
#
# Backend ENFORCES structure. AI FILLS only constrained logic fragments.
#
# NEW in v2:
#   - allowed_vars set built from signal_map before any AI call
#   - Every AI fragment is validated: only declared variables may be used
#   - Hallucinated variables → fragment regenerated once with stricter prompt
#   - If regeneration still violates → fallback to deterministic stub
#
# Temperature: 0.0 for all fragments (zero creativity).

import json
import re
from backend.openai_client import safe_chat_completion, DEFAULT_MODEL


# ── VENDOR PREFIXES ───────────────────────────────────────────────────────────

_VENDOR_PREFIXES = {
    "SIEMENS":       ("I_", "Q_", "M_"),
    "CODESYS":       ("b",  "b",  "b"),
    "ALLEN_BRADLEY": ("",   "",   ""),
    "SCHNEIDER":     ("x",  "x",  "x"),
    "GENERIC":       ("",   "",   ""),
}

# IEC keywords that are never variable names
_IEC_KEYWORDS = {
    "PROGRAM", "END_PROGRAM", "VAR", "END_VAR", "VAR_INPUT", "VAR_OUTPUT",
    "IF", "THEN", "ELSE", "ELSIF", "END_IF", "CASE", "OF", "END_CASE",
    "AND", "OR", "NOT", "XOR", "TRUE", "FALSE", "BOOL", "INT", "REAL",
    "TIME", "TON", "TOF", "R_TRIG", "F_TRIG", "STRING", "RETURN",
    "FOR", "TO", "DO", "END_FOR", "WHILE", "END_WHILE", "REPEAT",
    "UNTIL", "END_REPEAT", "WITH", "M_State"  # M_State is always declared by template
}


def _name(signal) -> str:
    """Normalize signal: may be plain string or dict with 'name'/'label'."""
    if isinstance(signal, dict):
        return str(signal.get("name", signal.get("label", signal.get("id", "")))).strip()
    return str(signal).strip()


def _apply_prefix(name: str, prefix: str) -> str:
    if not name:
        return name
    return name if name.startswith(prefix) else f"{prefix}{name}"


def _extract_identifiers(code: str) -> set[str]:
    """Extract all identifiers used in ST code, excluding IEC keywords."""
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code)
    return {t for t in tokens if t.upper() not in _IEC_KEYWORDS and not t.isdigit()}


def _clean_fragment(code: str) -> str:
    """Strip markdown wrappers."""
    return re.sub(r"```[a-z]*\n?", "", code).replace("```", "").strip()


def _call_llm(system_prompt: str, user_content: str, api_key: str = None) -> tuple[str, int]:
    """Call LLM for a fragment. Returns (content, tokens)."""
    kwargs = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
    }
    if api_key:
        kwargs["api_key"] = api_key
    response = safe_chat_completion(**kwargs)
    content = response.choices[0].message.content.strip()
    tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
    return _clean_fragment(content), tokens


# ── FRAGMENT GUARDS ──────────────────────────────────────────────────────────
# Rule priority:
#   1. Variable whitelist  (vars guard)
#   2. Q_ forbidden in safety/state fragments  (output guard)
#   3. Timer calls forbidden in fragments      (timer guard)

def _validate_fragment(fragment: str, allowed: set[str]) -> tuple[bool, set[str]]:
    """Returns (is_valid, violating_vars). Valid = all identifiers in allowed set."""
    used = _extract_identifiers(fragment)
    violations = used - allowed
    return len(violations) == 0, violations


def _contains_output_write(fragment: str, out_prefix: str = "Q_") -> bool:
    """
    Rule 2 + 5: Reject any fragment that assigns to an output variable.
    Detects patterns like:  Q_Motor := ...  or  bMotor := ...
    """
    # Match '<word> :=' where word starts with output prefix
    return bool(re.search(rf"\b{re.escape(out_prefix)}\w+\s*:=", fragment))


def _contains_timer_call(fragment: str) -> bool:
    """
    Rule 1: Reject any fragment that calls a timer FB.
    Detects patterns like: T_Run( or M_Timer(
    """
    return bool(re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(\s*IN\s*:=", fragment))


def _build_strict_regen_prompt(original_prompt: str, allowed: set[str], violations: set[str]) -> str:
    return (
        f"{original_prompt}\n\n"
        f"CRITICAL — SECOND ATTEMPT:\n"
        f"You MUST use ONLY these exact declared variable names:\n"
        f"{sorted(allowed)}\n\n"
        f"You used undeclared identifiers: {sorted(violations)}\n"
        f"DO NOT invent names. Replace or remove any undeclared identifier.\n"
        f"DO NOT assign outputs (Q_ variables) in this fragment.\n"
        f"DO NOT call timer function blocks in this fragment."
    )

def _pick_state_id(states: list, name_candidates: list[str], default_id: int) -> int:
    for s in states:
        sname = s.get("name", "") if isinstance(s, dict) else str(s)
        sid = s.get("id", None) if isinstance(s, dict) else None
        if any(c in sname.upper() for c in name_candidates) and isinstance(sid, int):
            return sid
    return default_id

def _pick_signal(signal_map: dict, contains_any: list[str]) -> str | None:
    for key in ("events", "inputs", "safety_conditions"):
        for sig in signal_map.get(key, []):
            n = _name(sig)
            if n and any(c in n.upper() for c in contains_any):
                return n
    return None

def _fallback_state_cases(control_model: dict, signal_map: dict) -> str:
    states = control_model.get("states", []) if control_model else []
    idle_id = _pick_state_id(states, ["IDLE"], 0)
    start_id = _pick_state_id(states, ["START", "STARTING"], 1)
    run_id = _pick_state_id(states, ["RUN", "RUNNING", "ACTIVE", "OPERAT"], 1)
    fault_id = _pick_state_id(states, ["FAULT", "ERROR", "ALARM", "TRIP", "FAIL"], 99)

    start_sig = _pick_signal(signal_map, ["START", "RUN", "ENABLE"])
    stop_sig = _pick_signal(signal_map, ["STOP", "RESET", "HALT"])
    fault_sig = _pick_signal(signal_map, ["FAULT", "TRIP", "OVERLOAD", "ESTOP", "E_STOP", "EMERGENCY"])
    reset_sig = _pick_signal(signal_map, ["RESET", "ACK", "CLEAR"])

    start_trig = f"{start_sig}_Trig.Q" if start_sig else "FALSE"
    stop_trig = f"{stop_sig}_Trig.Q" if stop_sig else "FALSE"
    reset_trig = f"{reset_sig}_Trig.Q" if reset_sig else stop_trig
    timers = signal_map.get("timers", []) if signal_map else []
    start_done = f"{_name(timers[0])}.Q" if timers else start_trig

    lines = []
    lines += [f"{idle_id}: (* IDLE *)",
              f"    IF {start_trig} THEN M_State := {start_id}; END_IF;"]
    if start_id != run_id:
        lines += [f"{start_id}: (* STARTING *)",
                  f"    IF {start_done} THEN M_State := {run_id}; END_IF;"]
    lines += [f"{run_id}: (* RUNNING *)",
              f"    IF {stop_trig} THEN M_State := {idle_id}; END_IF;"]
    if fault_sig:
        lines += [f"    IF {fault_sig} THEN M_FaultCode := 1; M_State := {fault_id}; END_IF;"]
    lines += [f"{fault_id}: (* FAULT *)",
              f"    M_FaultCode := M_FaultCode; (* Latched *)",
              f"    IF {reset_trig} THEN M_FaultCode := 0; M_State := {idle_id}; END_IF;"]
    return "\n".join(lines)

def _fallback_output_assignments(signal_map: dict, control_model: dict) -> str:
    outputs = signal_map.get("outputs", []) if signal_map else []
    states = control_model.get("states", []) if control_model else []
    run_id = _pick_state_id(states, ["RUN", "RUNNING", "ACTIVE", "OPERAT"], 1)
    lines = []
    for o in outputs:
        n = _name(o)
        if not n:
            continue
        n_up = n.upper()
        if any(k in n_up for k in ("ALARM", "BUZZER", "BEACON", "FAULT")):
            lines.append(f"{n} := (M_FaultCode > 0);")
        elif any(k in n_up for k in ("MOTOR", "PUMP", "VALVE", "CONVEYOR", "FAN", "HEATER", "MIXER")):
            lines.append(f"{n} := (M_State = {run_id});")
        else:
            lines.append(f"{n} := FALSE; (* TODO: verify assignment *)")
    return "\n".join(lines) if lines else "(* No outputs defined *)"

# ── FRAGMENT SYSTEM PROMPTS ───────────────────────────────────────────────────

_SAFETY_SYSTEM = """You are a PLC safety logic specialist.

Generate ONLY safety override IF statements.

STRICT RULES — violating any rule causes the fragment to be rejected:
1. Set ONLY M_State or internal boolean flags (M_ prefix).
   Example: IF I_E_Stop THEN M_State := 99; END_IF;
2. NEVER assign any output (Q_ variables). Outputs are set at the bottom only.
3. NEVER call any timer function block.
4. Use ONLY variable names from ALLOWED_VARIABLES in the input.
5. Return pure ST IF statements only. No explanation. No comments."""

_STATE_CASES_SYSTEM = """You are a PLC state machine specialist.

Generate ONLY the numbered CASE block bodies for the M_State variable.

STRICT RULES — violating any rule causes the fragment to be rejected:
1. Transitions update M_State and optionally M_FaultCode. Write nothing else.
2. NEVER assign any Q_ output variable inside a CASE block.
3. NEVER call any timer function block. Timers are called by the template.
4. Use ONLY variable names from ALLOWED_VARIABLES in the input.
5. If FAULT_CODES are provided: when transitioning to a fault state, also set
   M_FaultCode := <fault_code_number>; on the line before M_State assignment.
6. Use the EXACT state IDs from LOCKED_STATES or the states list (do NOT invent).
7. Format:
    0: (* IDLE *)
        IF <declared_input>_Trig.Q THEN M_State := 1; END_IF;
    1: (* STARTING *)
        IF T_<Name>.Q THEN M_State := 2; END_IF;
    2: (* RUNNING *)
        IF <fault_condition> THEN M_FaultCode := <code>; M_State := <fault_id>; END_IF;
    <fault_id>: (* FAULT *)
        M_FaultCode := M_FaultCode; (* Latched *)
        IF <reset_condition>_Trig.Q THEN M_FaultCode := 0; M_State := 0; END_IF;
8. Return CASE block bodies only. No surrounding CASE...END_CASE. No explanation."""

_OUTPUT_SYSTEM = """You are a PLC deterministic output assignment specialist.

Generate ONLY bottom-of-program boolean output assignments.

STRICT RULES:
1. Assign each output from OUTPUTS list EXACTLY ONCE.
2. Use boolean expressions — NOT IF blocks.
   Examples:
       Q_Motor   := (M_State = 2) OR (M_State = 3);
       Q_Alarm   := (M_FaultCode > 0);
       Q_Running := (M_State = 1) OR (M_State = 2);
3. IMPORTANT: Any output with "Alarm", "alarm", "ALARM", "beacon", or "buzzer"
   in its name or description MUST be assigned as: Q_<AlarmName> := (M_FaultCode > 0);
4. Use ONLY variable names from ALLOWED_VARIABLES in the input.
5. M_FaultCode is always available — use it for alarm outputs.
6. Return assignment lines only. No explanation. No IF. No CASE."""


# ── MAIN CLASS ────────────────────────────────────────────────────────────────

class TemplateLockedSTGenerator:
    """
    Deterministic IEC ST generator with variable guard enforcement.
    Structure: 100% backend-controlled.
    AI: fills only safety logic, state transitions, output expressions.
    Guard: validates identifiers; regenerates once on violation; stubs if still invalid.
    """

    MAX_GUARD_RETRIES = 1  # one regeneration attempt per fragment

    def __init__(self, brand_key: str = "GENERIC", program_name: str = "PLCProgram"):
        bk = brand_key.upper().replace(" ", "_").replace("-", "_")
        self.brand_key = bk if bk in _VENDOR_PREFIXES else "GENERIC"
        self.program_name = program_name
        self.in_pfx, self.out_pfx, self.int_pfx = _VENDOR_PREFIXES[self.brand_key]

    # ── Build Allowed Variable Set ────────────────────────────────────────────

    def _build_allowed_vars(self, signal_map: dict, control_model: dict = None) -> set[str]:
        """
        Build the complete set of declared identifiers from signal_map + control_model.
        State names appear in CASE labels — must be in allowed set.
        Transition event names may be used as boolean conditions.
        """
        allowed = {"M_State"}

        # Signal map variables
        for key in ("inputs", "outputs", "internal_states",
                    "timers", "counters", "analog_values", "safety_conditions"):
            for sig in signal_map.get(key, []):
                n = _name(sig)
                if n:
                    allowed.add(n)
                    allowed.add(f"{n}_Trig")
        for ev in signal_map.get("events", []):
            n = _name(ev)
            if n:
                allowed.add(f"{n}_Trig")

        # State names + transition event identifiers from control model
        if control_model:
            for state in control_model.get("states", []):
                n = _name(state)
                if n:
                    allowed.add(n)
            for t in control_model.get("transitions", []):
                for field in ("event", "trigger", "condition"):
                    v = str(t.get(field, "")).strip()
                    if v and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", v):
                        allowed.add(v)

        return allowed

    def _guard_call(
        self,
        system_prompt: str,
        user_content: str,
        allowed: set[str],
        fallback_stub: str,
        api_key: str = None,
        forbid_output_writes: bool = False,
        forbid_timer_calls: bool = False
    ) -> tuple[str, int]:
        """
        Call LLM for a fragment. Enforces all active guards:
          1. Variable whitelist guard
          2. Output-write guard (Q_ in safety/state fragments)
          3. Timer-call guard  (IN := pattern in any non-output fragment)
        Retries once with stricter prompt. Falls back to stub if still invalid.
        """
        total_tokens = 0

        def _check(frag: str) -> tuple[bool, list[str]]:
            reasons = []
            is_ok, violations = _validate_fragment(frag, allowed)
            if not is_ok:
                reasons.append(f"undeclared vars: {sorted(violations)}")
            if forbid_output_writes and _contains_output_write(frag, self.out_pfx):
                reasons.append("Q_ output write detected — not allowed in this fragment")
            if forbid_timer_calls and _contains_timer_call(frag):
                reasons.append("timer call detected — timers are locked to template")
            return len(reasons) == 0, reasons

        try:
            fragment, t = _call_llm(system_prompt, user_content, api_key)
            total_tokens += t
        except Exception as e:
            print(f"        LLM fragment failed ({type(e).__name__}: {e}). Using stub.")
            return fallback_stub, total_tokens

        ok, reasons = _check(fragment)
        if ok:
            return fragment, total_tokens

        print(f"        Fragment guard violations: {reasons} — regenerating...")
        # Build violations set for regen prompt (variable violations)
        _, var_violations = _validate_fragment(fragment, allowed)
        strict_prompt = _build_strict_regen_prompt(system_prompt, allowed, var_violations)
        try:
            fragment2, t2 = _call_llm(strict_prompt, user_content, api_key)
            total_tokens += t2
        except Exception as e:
            print(f"        LLM regen failed ({type(e).__name__}: {e}). Using stub.")
            return fallback_stub, total_tokens

        ok2, reasons2 = _check(fragment2)
        if ok2:
            print(f"       Regenerated fragment passed all guards.")
            return fragment2, total_tokens

        print(f"       Second attempt still violated ({reasons2}). Using stub.")
        return fallback_stub, total_tokens

    # ── VAR Section (100% deterministic) ─────────────────────────────────────

    def _build_var_section(self, signal_map: dict) -> str:
        lines = []

        def section(key, label, prefix, type_str, default=""):
            items = signal_map.get(key, [])
            if not items:
                return
            lines.append(f"    (* {label} *)")
            for sig in items:
                n = _name(sig)
                if n:
                    n = _apply_prefix(n, prefix) if not any(n.startswith(p) for p in ("I_", "Q_", "M_", "T_", "b", "x")) else n
                    suffix = f" := {default}" if default else ""
                    lines.append(f"    {n} : {type_str}{suffix};")

        section("inputs",           "Inputs",           self.in_pfx,  "BOOL")
        section("outputs",          "Outputs",          self.out_pfx, "BOOL", "FALSE")
        section("analog_values",    "Analog Values",    self.int_pfx, "REAL", "0.0")

        # Safety conditions that are NOT already declared in inputs (avoid duplicate declarations)
        declared_inputs = {_name(s) for s in signal_map.get("inputs", [])}
        extra_safety = [s for s in signal_map.get("safety_conditions", [])
                        if _name(s) not in declared_inputs]
        if extra_safety:
            lines.append("    (* Safety Flags *)")
            for sig in extra_safety:
                n = _name(sig)
                if n:
                    n = _apply_prefix(n, self.int_pfx) if not any(n.startswith(p) for p in ("I_", "Q_", "M_", "T_", "b", "x")) else n
                    lines.append(f"    {n} : BOOL := FALSE;")

        # Internal states + counters split: counters are INT, others BOOL
        int_states = signal_map.get("internal_states", [])
        counters_set = {_name(c) for c in signal_map.get("counters", [])}
        if int_states:
            lines.append("    (* Internal States *)")
        for sig in int_states:
            n = _name(sig)
            if n:
                n = n if any(n.startswith(p) for p in ("M_", "b", "x")) else f"{self.int_pfx}{n}"
                is_counter = n in counters_set or "Count" in n or "count" in n
                if is_counter:
                    lines.append(f"    {n} : INT := 0;")
                else:
                    lines.append(f"    {n} : BOOL := FALSE;")

        # Edge triggers — one R_TRIG per pushbutton/event input
        events = signal_map.get("events", [])
        extra_trigs = signal_map.get("counters", [])
        if events or extra_trigs:
            lines.append("    (* Edge Detection *)")
        for ev in events + extra_trigs:
            n = _name(ev)
            if n:
                lines.append(f"    {n}_Trig : R_TRIG;")

        # Timers
        timers = signal_map.get("timers", [])
        if timers:
            lines.append("    (* Timers *)")
        for tmr in timers:
            n = _name(tmr)
            if n:
                n = n if n.startswith("T_") else f"T_{n}"
                lines.append(f"    {n} : TON;")

        # State machine + FaultCode — always present
        lines.append("    (* State Machine *)")
        lines.append("    M_State     : INT := 0;   (* 0 = Idle *)")
        lines.append("    M_FaultCode : INT := 0;   (* 0 = No fault *)")

        return "\n".join(lines)

    # ── Edge Calls (deterministic) ────────────────────────────────────────────

    def _build_edge_calls(self, signal_map: dict) -> str:
        lines = []
        for key in ("events", "counters"):
            for sig in signal_map.get(key, []):
                n = _name(sig)
                if n:
                    inp = _apply_prefix(n, self.in_pfx)
                    lines.append(f"{n}_Trig(CLK := {inp});")
        return "\n".join(lines) if lines else "(* No edge detection required *)"

    # ── Timer Calls (deterministic, outside IF) ───────────────────────────────

    def _build_locked_timer_calls(self, signal_map: dict, control_model: dict) -> str:
        """
        Rule 1 — Timer calls are LOCKED to backend template.
        AI cannot call timers. Activation derived from state index.
        Uses actual timer durations from signal_map["timer_presets"] when available.
        """
        timers = signal_map.get("timers", [])
        if not timers:
            return "(* No timers *)"

        # timer_presets: {"T_StartDelay": "T#5S", "T_NoPressure": "T#8S", ...}
        presets = signal_map.get("timer_presets", {})
        states  = control_model.get("states", [])
        lines   = []

        for idx, tmr in enumerate(timers):
            n = _name(tmr)
            if n:
                n = n if n.startswith("T_") else f"T_{n}"
                # Derive the state that activates this timer (timer[i] → state index i+1)
                state_idx = (idx + 1) if (idx + 1) < len(states) else (idx + 1)
                # Use declared duration if available, else default T#5S
                pt = presets.get(n, presets.get(n.replace("T_", ""), "T#5S"))
                lines.append(f"{n}(IN := (M_State = {state_idx}), PT := {pt});")

        return "\n".join(lines)

    def _build_direction_interlock(self, signal_map: dict) -> str:
        """
        Rule 4 — Direction interlock is template-derived. AI does NOT decide.
        Detects Forward/Reverse input pairs and emits safe interlock expression.
        """
        inputs = [_name(s) for s in signal_map.get("inputs", [])]
        outputs = [_name(s) for s in signal_map.get("outputs", [])]
        fwd_in = next((s for s in inputs if "forward" in s.lower() or "fwd" in s.lower()), None)
        rev_in = next((s for s in inputs if "reverse" in s.lower() or "rev" in s.lower()), None)
        fwd_out = next((s for s in outputs if "forward" in s.lower() or "fwd" in s.lower()), None)
        rev_out = next((s for s in outputs if "reverse" in s.lower() or "rev" in s.lower()), None)

        if not (fwd_in and rev_in and fwd_out and rev_out):
            return ""  # no direction interlock needed

        return (
            f"(* Direction Interlock - Template Locked *)\n"
            f"{fwd_out} := {fwd_in} AND NOT {rev_in} AND M_Run;\n"
            f"{rev_out} := {rev_in} AND NOT {fwd_in} AND M_Run;"
        )

    # ── Deterministic E-Stop Block ────────────────────────────────────────────

    def _build_estop_block(self, signal_map: dict, control_model: dict) -> str:
        """
        Generate a fully deterministic E-Stop safety interlock.
        Uses the exact E-Stop input name from safety_conditions.
        Sets M_State to the FAULT state ID (highest numbered state) and M_FaultCode := 10.
        """
        # Detect E-Stop signal name
        safety_conds = signal_map.get("safety_conditions", [])
        estop_name = None
        for sig in safety_conds:
            n = _name(sig)
            if n:
                estop_name = n
                break

        if not estop_name:
            # Fallback: scan inputs for anything with EStop/Emergency in name
            for sig in signal_map.get("inputs", []):
                n = _name(sig)
                if n and any(kw in n.upper() for kw in ("ESTOP", "E_STOP", "EMERGENCY")):
                    estop_name = n
                    break

        if not estop_name:
            return "(* No E-Stop input declared *)"

        # Determine fault state ID (highest state number, typically FAULT)
        states = control_model.get("states", [])
        fault_state_id = 0
        if states:
            for s in states:
                sid = s.get("id", 0) if isinstance(s, dict) else 0
                sname = s.get("name", "") if isinstance(s, dict) else str(s)
                if any(kw in sname.upper() for kw in ("FAULT", "ERROR", "ALARM", "FAIL", "TRIP")):
                    fault_state_id = sid
                    break
            if fault_state_id == 0 and states:
                # Use highest state ID as fault state
                try:
                    fault_state_id = max(
                        s.get("id", 0) if isinstance(s, dict) else 0
                        for s in states
                    )
                except Exception:
                    fault_state_id = 0

        return (
            f"(* E-Stop Safety Interlock - Highest Priority - Safety Category 3 *)\n"
            f"IF {estop_name} THEN\n"
            f"    M_State     := {fault_state_id};   (* Go directly to FAULT state *)\n"
            f"    M_FaultCode := 10;                  (* FaultCode 10 = E-Stop activated *)\n"
            f"END_IF;"
        )

    # ── AI Fragments ──────────────────────────────────────────────────────────

    def _gen_safety(self, control_model: dict, allowed: set[str], api_key: str = None) -> tuple[str, int]:
        if not control_model.get("safety_overrides"):
            return "(* No safety overrides defined *)", 0
        user_content = json.dumps({
            "safety_overrides":  control_model.get("safety_overrides", []),
            "safety_state_id":   99,
            "ALLOWED_VARIABLES": sorted(allowed)
        })
        return self._guard_call(
            _SAFETY_SYSTEM, user_content, allowed,
            fallback_stub="(* Safety override — manual implementation required *)",
            api_key=api_key,
            forbid_output_writes=True,   # Rule 5: safety cannot write Q_
            forbid_timer_calls=True      # Rule 1: timers locked to template
        )

    def _gen_state_cases(self, control_model: dict, signal_map: dict, allowed: set[str], api_key: str = None) -> tuple[str, int]:
        user_content = json.dumps({
            "states":            control_model.get("states", []),
            "transitions":       control_model.get("transitions", []),
            "actions":           control_model.get("actions", []),
            "FAULT_CODES":       control_model.get("fault_codes", {}),
            "LOCKED_STATES":     control_model.get("states", []),
            "ALLOWED_VARIABLES": sorted(allowed | {"M_FaultCode"})
        })
        return self._guard_call(
            _STATE_CASES_SYSTEM, user_content, allowed | {"M_FaultCode"},
            fallback_stub=_fallback_state_cases(control_model, signal_map),
            api_key=api_key,
            forbid_output_writes=True,   # Rule 2: state fragment cannot write Q_
            forbid_timer_calls=True      # Rule 1: timers locked to template
        )

    def _gen_output_assignments(self, signal_map: dict, control_model: dict, allowed: set[str], api_key: str = None) -> tuple[str, int]:
        outputs = signal_map.get("outputs", [])
        if not outputs:
            return "(* No outputs defined *)", 0
        out_names = [_name(o) for o in outputs if _name(o)]
        user_content = json.dumps({
            "outputs":           out_names,
            "states":            control_model.get("states", []),
            "actions":           control_model.get("actions", []),
            "clamping_rules":    control_model.get("clamping_rules", []),
            "FAULT_CODES":       control_model.get("fault_codes", {}),
            "ALLOWED_VARIABLES": sorted(allowed | {"M_FaultCode"})
        })
        return self._guard_call(
            _OUTPUT_SYSTEM,
            user_content,
            allowed | {"M_FaultCode"},
            fallback_stub=_fallback_output_assignments(signal_map, control_model),
            api_key=api_key
        )

    # ── Assembly (100% backend-controlled) ────────────────────────────────────

    def _assemble(self, var_section, edge_calls, estop_block, state_cases,
                  timer_calls, output_assignments, direction_interlock="") -> str:
        extra = f"\n\n{direction_interlock}" if direction_interlock else ""
        return (
            f"PROGRAM {self.program_name}\n"
            f"VAR\n{var_section}\nEND_VAR\n\n"
            f"(* -- Edge Detection ----------------------------------------- *)\n{edge_calls}\n\n"
            f"(* -- Safety Interlock: E-Stop (Highest Priority) ------------ *)\n{estop_block}\n\n"
            f"(* -- State Machine ------------------------------------------ *)\n"
            f"CASE M_State OF\n\n{state_cases}\n\n"
            f"    ELSE\n"
            f"        (* Unknown state - safe fallback *)\n"
            f"        M_State     := 0;\n"
            f"        M_FaultCode := 99;\n"
            f"END_CASE;\n\n"
            f"(* -- Timer Calls: State-Locked, called every scan outside IF *)\n{timer_calls}\n\n"
            f"(* -- Deterministic Output Assignment: ONCE at bottom -------- *)\n{output_assignments}{extra}\n\n"
            f"END_PROGRAM"
        )

    # ── Public Entry ──────────────────────────────────────────────────────────

    def generate(self, control_model: dict, signal_map: dict, api_key: str = None) -> tuple[str, int]:
        """Build template-locked ST with all 5 industrial rules enforced."""
        total_tokens = 0

        print("    [TLG] Building allowed variable set...")
        # Always include M_FaultCode in the allowed set
        allowed = self._build_allowed_vars(signal_map, control_model) | {"M_FaultCode"}
        print(f"       {len(allowed)} declared identifiers available to AI fragments")

        print("    [TLG] Building deterministic VAR section...")
        var_section = self._build_var_section(signal_map)

        print("    [TLG] Building edge detection calls...")
        edge_calls = self._build_edge_calls(signal_map)

        print("    [TLG] Rule 1 — Building state-locked timer calls (AI excluded)...")
        timer_calls = self._build_locked_timer_calls(signal_map, control_model)

        print("    [TLG] Rule 4 — Checking for direction interlock (template-derived)...")
        direction_interlock = self._build_direction_interlock(signal_map)
        if direction_interlock:
            print("       Direction interlock detected and locked.")

        print("    [TLG] Building deterministic E-Stop block (AI excluded)...")
        estop_block = self._build_estop_block(signal_map, control_model)

        print("    [TLG] Rule 2 — AI state cases fragment (guard: no-Q_, no-timer)...")
        state_cases, t2 = self._gen_state_cases(control_model, signal_map, allowed, api_key)
        total_tokens += t2

        print("    [TLG] AI output assignments fragment (guard: var whitelist)...")
        output_assignments, t3 = self._gen_output_assignments(signal_map, control_model, allowed, api_key)
        total_tokens += t3

        print("    [TLG] Assembling locked IEC structure...")
        st_code = self._assemble(
            var_section, edge_calls, estop_block, state_cases,
            timer_calls, output_assignments, direction_interlock
        )

        return st_code, total_tokens
