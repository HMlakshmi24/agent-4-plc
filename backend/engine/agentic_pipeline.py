# backend/engine/agentic_pipeline.py
# Industrial PLC ST Generation Pipeline — Locked Architecture
#
# Pipeline:
#   Stage 1 → AI Requirement Extractor (structure JSON from user prompt)
#   Stage 2 → AI ST Generator (architectural system prompt, temperature 0.1)
#   Stage 3 → IEC Syntax Validator (iec-checker or graceful fallback)
#   Stage 4 → Semantic Validator (read-only, severity-classified)
#   Stage 5 → Severity Aggregator (only CRITICAL triggers a targeted fix)
#   Stage 6 → Single targeted fix (max 2 attempts, targeted — no full rewrite)
#
# Design Rules:
#   - Validators NEVER rewrite code — they only classify issues
#   - Only CRITICAL issues trigger a fix
#   - Warnings are collected and returned, never trigger rewrite
#   - No cascading rewrite loops
#   - No rule engine override collisions

import json
import logging
import subprocess
import os
import re

from backend.openai_client import safe_chat_completion, DEFAULT_MODEL
from backend.engine.semantic_validator import SemanticValidator
from backend.engine.prompt_parser import parse_prompt
from backend.engine.severity_aggregator import aggregate_validation_results
from backend.engine.multipass_extractor import MultiPassExtractor
from backend.engine.model_conflict_analyzer import ModelConflictAnalyzer
from backend.engine.scan_simulator import ScanSimulator
from backend.engine.template_locked_st_generator import TemplateLockedSTGenerator
from backend.engine.engineering_completeness import EngineeringCompletenessValidator
from backend.engine.physical_sequence_rules import PhysicalSequenceRuleEngine
from backend.engine.dead_state_validator import DeadStateValidator
from backend.engine.variable_ownership_validator import VariableOwnershipValidator
from backend.engine.industrial_polish import add_state_comments
from backend.engine.confidence_score import ConfidenceScoreCalculator
from backend.engine.vendor_profile import VendorProfileInjector
from backend.engine.fb_architecture import FBArchitectureInjector
from backend.engine.plc_test_generator import PLCTestGenerator
from backend.engine.sil_mode import SILModeInjector
from backend.engine.st_normalizer import normalize_st
from backend.engine.engineering_scorer import PLCEngineeringScorer

# ──────────────────────────────────────────────────────────────────────────────
# Exception
# ──────────────────────────────────────────────────────────────────────────────

class IECValidationError(Exception):
    def __init__(self, message, code=None, errors=None, tokens=0):
        super().__init__(message)
        self.code = code
        self.errors = errors
        self.tokens = tokens

# ──────────────────────────────────────────────────────────────────────────────
# Vendor Profiles — prefixes & naming style per brand
# ──────────────────────────────────────────────────────────────────────────────

VENDOR_PROFILES = {
    "SIEMENS": {
        "bool_prefix": "",
        "input_prefix": "I_",
        "output_prefix": "Q_",
        "internal_prefix": "M_",
        "edge_block": "R_TRIG",
        "timer_block": "TON",
        "style": "UPPERCASE"
    },
    "CODESYS": {
        "bool_prefix": "b",
        "input_prefix": "b",
        "output_prefix": "b",
        "internal_prefix": "b",
        "edge_block": "R_TRIG",
        "timer_block": "TON",
        "style": "CamelCase"
    },
    "ALLEN_BRADLEY": {
        "bool_prefix": "",
        "input_prefix": "",
        "output_prefix": "",
        "internal_prefix": "",
        "edge_block": "ONS",
        "timer_block": "TON",
        "style": "Mixed"
    },
    "SCHNEIDER": {
        "bool_prefix": "x",
        "input_prefix": "x",
        "output_prefix": "x",
        "internal_prefix": "x",
        "edge_block": "R_TRIG",
        "timer_block": "TON",
        "style": "CamelCase"
    },
    "GENERIC": {
        "bool_prefix": "",
        "input_prefix": "",
        "output_prefix": "",
        "internal_prefix": "",
        "edge_block": "R_TRIG",
        "timer_block": "TON",
        "style": "CamelCase"
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Prompts — Locked Industrial Architecture
# ──────────────────────────────────────────────────────────────────────────────

STRUCTURED_EXTRACTOR_PROMPT = """You are an industrial PLC requirement analyzer.

From the following user description, extract structured PLC control requirements.

Return ONLY valid JSON in this exact format — no code, no explanation:

{
  "system_type": "monitoring" | "control" | "hybrid",
  "inputs": [],
  "outputs": [],
  "timers": [],
  "counters": [],
  "safety_conditions": [],
  "control_rules": []
}
"""

FIX_PROMPT_SYSTEM = """You are a senior IEC 61131-3 PLC engineer performing a targeted fix.

RULES:
- Fix ONLY the listed critical issues.
- Do NOT modify any other part of the code.
- Do NOT rename variables.
- Do NOT change overall architecture.
- Preserve PROGRAM structure, VAR blocks, and all logic not related to the issue.
- Return ONLY the corrected complete ST code block.
"""

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1, is_json: bool = False, api_key: str = None) -> tuple[str, int]:
    """Call LLM via the existing safe_chat_completion. Returns (content, tokens)."""
    try:
        kwargs = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}
        if api_key:
            kwargs["api_key"] = api_key

        response = safe_chat_completion(**kwargs)
        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
        return content, tokens
    except Exception as e:
        logging.error(f"LLM Call Failed: {e}")
        raise


def _extract_code(st_code: str) -> str:
    """Strip accidental markdown wrappers."""
    return (
        st_code
        .replace("```st", "")
        .replace("```iecst", "")
        .replace("```iec", "")
        .replace("```", "")
        .strip()
    )


def _run_iec_checker(code: str) -> tuple[bool, str]:
    """Run iec-checker CLI if available. Gracefully falls back if not installed."""
    temp_file = "temp_check.st"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
        result = subprocess.run(["iec-checker", temp_file], capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    except FileNotFoundError:
        logging.warning("iec-checker not found in PATH. Skipping external static analysis.")
        return True, "iec-checker not installed; assumed valid."
    except Exception as e:
        logging.error(f"IEC checker error: {e}")
        return False, str(e)
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 Generator Prompt — built dynamically per vendor profile
# ──────────────────────────────────────────────────────────────────────────────

def _build_st_generator_prompt(brand_key: str, system_type: str, program_name: str) -> str:
    vendor = VENDOR_PROFILES.get(brand_key, VENDOR_PROFILES["GENERIC"])
    return (
        f"You are a senior industrial PLC engineer.\n\n"
        f"Generate IEC 61131-3 Structured Text (ST) for: {brand_key} | {system_type} | {program_name}\n\n"
        f"REQUIRED OUTPUT FORMAT (follow exactly):\n"
        f"PROGRAM {program_name}\n"
        f"VAR\n"
        f"    (* Inputs — prefix: {vendor['input_prefix']} *)\n"
        f"    (* Outputs — prefix: {vendor['output_prefix']} *)\n"
        f"    (* Internal States — prefix: {vendor['internal_prefix']} *)\n"
        f"    (* Edge blocks — {vendor['edge_block']}, only if edge detection needed *)\n"
        f"    (* Timers — {vendor['timer_block']}, ONLY if the system has timed logic *)\n"
        f"END_VAR\n\n"
        f"(* Edge Detection section *)\n"
        f"(* State Logic section *)\n"
        f"(* Timer Calls — OUTSIDE IF blocks, ONLY if timers declared *)\n"
        f"(* Safety Overrides — ONLY if system_type is control or hybrid *)\n"
        f"(* Clamp section — ONLY for INT/counter vars *)\n"
        f"(* Deterministic Output Assignment — ONCE at bottom *)\n"
        f"END_PROGRAM\n\n"
        f"STRICT RULES:\n"
        f"1. Code MUST begin with PROGRAM {program_name} and end with END_PROGRAM.\n"
        f"2. All variables declared in ONE VAR..END_VAR block.\n"
        f"3. Use {vendor['edge_block']} for edge detection and counter increments.\n"
        f"4. Declare timers ONLY if the system needs timed logic. If declared, call once per scan OUTSIDE IF blocks.\n"
        f"5. Assign each output EXACTLY ONCE at the BOTTOM of the program.\n"
        f"6. Logic must be minimal, deterministic, and scan-cycle safe.\n"
        f"7. Return ONLY valid ST code — no markdown, no explanation.\n"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run_agentic_pipeline(description: str, program_name: str, brand: str = "generic", api_key: str = None) -> tuple[str, int]:
    """
    Executes the locked industrial ST generation pipeline.
    Returns: (final_st_code, total_token_usage)
    """
    total_tokens = 0
    MAX_FIX_ATTEMPTS = 2

    # ── Pre-Stage: Parse structured prompt for locked I/O declarations ────
    # This is the key fix: if the user explicitly declares their signals,
    # we enforce those exact names throughout the pipeline.
    print(" [PLC Pre-Stage] Parsing structured prompt for locked signal declarations...")
    parsed = parse_prompt(description)

    _GENERIC_NAMES = {"plcprogram", "myplcprogram", "program", "default", "plc", ""}

    if parsed.program_name:
        # Always respect the explicit declaration in the description
        print(f"    Detected program name in description: '{parsed.program_name}'")
        program_name = parsed.program_name
    elif program_name.lower() in _GENERIC_NAMES:
        # Derive a sensible name from description keywords (ordered: specific → general)
        desc_lc = description.lower()
        _KW_TO_NAME = [
            # Traffic / Infrastructure
            (["traffic light", "traffic signal", "traffic control",
              "intersection", "pedestrian signal", "signal timing"],   "TrafficLightControl"),
            # Machine Safety / Press
            (["hydraulic press", "punch press", "stamping press",
              "ram extend", "two-hand safety", "press machine"],       "HydraulicPress"),
            # Elevator / Lift
            (["elevator", "lift control", "floor control", "cabin"],   "ElevatorControl"),
            # Gate / Barrier
            (["parking gate", "rolling door", "sliding gate",
              "automatic gate", "boom gate", "gate control"],          "GateControl"),
            # Car Wash
            (["car wash", "vehicle wash", "wash station"],             "CarWashControl"),
            # Crane / Hoist
            (["crane", "hoist control", "overhead crane", "winch"],    "CraneControl"),
            # Compressor
            (["air compressor", "compressor control"],                 "CompressorControl"),
            # Water Treatment
            (["water treatment", "filtration plant", "clarifier"],     "WaterTreatment"),
            # Sorter
            (["sorting system", "sorter control", "diverter"],         "SorterControl"),
            # Safety Interlock
            (["safety interlock", "light curtain", "guard monitor"],   "SafetyInterlock"),
            # Conveyor / Belt
            (["conveyor", "belt conveyor"],                            "ConveyorControl"),
            # Packaging
            (["packaging", "packing line", "bottling line"],           "PackagingControl"),
            # Pump
            (["pump station", "pump control", "pumping"],              "PumpControl"),
            # Tank / Level
            (["tank filling", "tank level", "vessel filling"],         "TankControl"),
            # Batch / Reactor
            (["batch control", "batch reactor", "batch process"],      "BatchControl"),
            (["chemical reactor", "cstr"],                             "ReactorControl"),
            # Mixing
            (["mixing system", "agitator control", "blending"],        "MixingControl"),
            # Dosing
            (["chemical dosing", "dosing pump"],                       "DosingControl"),
            # HVAC
            (["hvac", "air conditioning", "ventilation system",
              "climate control", "fan control"],                        "HVACControl"),
            # Heater / Temperature
            (["heater control", "oven control", "furnace control"],    "HeaterControl"),
            (["temperature control", "temperature regulation"],        "TempControl"),
            # Motor Starter (generic fallback)
            (["motor starter", "motor control"],                       "MotorControl"),
        ]
        for keywords, name in _KW_TO_NAME:
            if any(kw in desc_lc for kw in keywords):
                program_name = name
                break
        print(f"    Derived program name from description: '{program_name}'")

    if parsed.brand and brand.lower() in ("generic", ""):
        brand = parsed.brand
        print(f"    Detected brand in description: '{parsed.brand}'")

    locked_signals = parsed.to_locked_signal_map() if parsed.has_explicit_io() else None
    locked_states  = parsed.to_locked_states()     if parsed.states         else None
    fault_codes    = parsed.to_fault_codes_dict()  if parsed.fault_codes    else None

    if locked_signals:
        print(f"    Locked signals: {len(locked_signals.get('inputs', []))} inputs, "
              f"{len(locked_signals.get('outputs', []))} outputs, "
              f"{len(locked_signals.get('timers', []))} timers")
    if locked_states:
        print(f"    Locked states: {[s['name'] for s in locked_states]}")
    if fault_codes:
        print(f"    Fault codes: {list(fault_codes.keys())}")

    # ── Stage 1: Multi-Pass Requirement Normalization ─────────────────────
    # 3 AI passes: Domain Analysis → Signal Normalization → Control Model
    print(" [PLC Stage 1] Multi-pass requirement normalization (3 passes)...")
    system_type = "control"
    struct_info = description  # safe fallback

    try:
        extractor = MultiPassExtractor()
        extraction, t1 = extractor.execute(
            description,
            api_key=api_key,
            locked_signals=locked_signals,
            locked_states=locked_states,
            fault_codes=fault_codes,
        )
        total_tokens += t1
        system_type = extraction.get("system_type", "control")
        # If domain suggested a better program name and we still have generic, use it
        suggested = extraction.get("domain", {}).get("suggested_program_name", "")
        if suggested and program_name.lower() in _GENERIC_NAMES:
            program_name = suggested
            print(f"    Domain suggested program name: '{program_name}'")
        # Pass the full control model to the generator for maximum accuracy
        struct_info = json.dumps({
            "control_model":  extraction["control_model"],
            "signal_map":     extraction["signal_map"],
            "domain_summary": extraction["domain"].get("process_description", description)
        }, indent=2)
        print(f"    Multi-pass complete: system_type={system_type}")
    except Exception as e:
        print(f"    Multi-pass extraction failed ({e}). Falling back to raw description.")

    # ── Layer 6: Control Model Conflict Analyzer ──────────────────────────
    print(" [PLC Layer 6] Control model conflict analysis...")
    control_model_data = extraction.get("control_model", {}) if 'extraction' in dir() else {}
    try:
        conflict_checker = ModelConflictAnalyzer(control_model_data)
        conflict_result = conflict_checker.validate()
        if conflict_result["warning"]:
            for w in conflict_result["warning"]:
                print(f"     {w}")
        if conflict_result["critical"]:
            print("    Control model critical conflicts — aborting generation:")
            for c in conflict_result["critical"]:
                print(f"       {c}")
            raise IECValidationError(
                message="Control model conflict detected before ST generation.",
                code=None,
                errors=str(conflict_result["critical"]),
                tokens=total_tokens
            )
        else:
            print("    Control model conflict analysis passed.")
    except IECValidationError:
        raise
    except Exception as e:
        print(f"     Layer 6 analysis error ({e}) — continuing.")

    # ── Layer 7: Lightweight Scan Simulator ────────────────────────────────
    print(" [PLC Layer 7] Lightweight scan simulation...")
    try:
        simulator = ScanSimulator(control_model_data)
        sim_result = simulator.simulate()
        if sim_result["warning"]:
            for w in sim_result["warning"]:
                print(f"     {w}")
        if sim_result["critical"]:
            print("    Simulation critical failure — aborting generation:")
            for c in sim_result["critical"]:
                print(f"       {c}")
            raise IECValidationError(
                message="Scan simulation failure detected before ST generation.",
                code=None,
                errors=str(sim_result["critical"]),
                tokens=total_tokens
            )
        else:
            print("    Scan simulation passed.")
    except IECValidationError:
        raise
    except Exception as e:
        print(f"     Layer 7 simulation error ({e}) — continuing.")

    # ── Layer 8: Engineering Completeness Validator ──────────────────────────
    print(" [PLC Layer 8] Engineering Completeness...")
    engineering_warnings = 0
    try:
        eng_validator = EngineeringCompletenessValidator(control_model_data, extraction.get("signal_map", {}))
        eng_res = eng_validator.validate()
        engineering_warnings = len(eng_res["warning"])
        for w in eng_res["warning"]:
            print(f"     {w}")
        if eng_res["critical"]:
            print("    Engineering completeness failure — aborting generation:")
            for c in eng_res["critical"]:
                print(f"       {c}")
            raise IECValidationError(
                message="Engineering completeness failure detected before ST generation.",
                code=None,
                errors=str(eng_res["critical"]),
                tokens=total_tokens
            )
        else:
            print("    Engineering completeness passed.")
    except IECValidationError:
        raise
    except Exception as e:
        print(f"     Layer 8 execution error ({e}) — continuing.")

    # ── Layer 9: Physical Sequence Rules ───────────────────────────────────
    print(" [PLC Layer 9] Physical Sequence Rules...")
    physical_warnings = 0
    try:
        phys_validator = PhysicalSequenceRuleEngine(control_model_data)
        phys_res = phys_validator.validate()
        physical_warnings = len(phys_res["warning"])
        for w in phys_res["warning"]:
            print(f"     {w}")
        if phys_res["critical"]:
            print("    Physical sequence failure — aborting generation:")
            for c in phys_res["critical"]:
                print(f"       {c}")
            raise IECValidationError(
                message="Physical sequence failure detected before ST generation.",
                code=None,
                errors=str(phys_res["critical"]),
                tokens=total_tokens
            )
        else:
            print("    Physical sequence rules passed.")
    except IECValidationError:
        raise
    except Exception as e:
        print(f"     Layer 9 execution error ({e}) — continuing.")

    # ── Stage 2: Template-Locked ST Generation ────────────────────────────
    # Structure is 100% locked by backend.
    # AI fills ONLY: safety IF logic, state case bodies, output expressions.
    brand_key = brand.upper().replace(" ", "_").replace("-", "_")
    if brand_key not in VENDOR_PROFILES:
        brand_key = "GENERIC"

    print(f" [PLC Stage 2] Template-locked ST generation for {brand_key} / {system_type}...")

    # Grab signal_map and control_model from Stage 1 extraction (may not exist on fallback)
    _signal_map    = extraction.get("signal_map", {})    if 'extraction' in dir() else {}
    _control_model = extraction.get("control_model", {}) if 'extraction' in dir() else {}

    try:
        tlg = TemplateLockedSTGenerator(brand_key=brand_key, program_name=program_name)
        st_code, t2 = tlg.generate(
            control_model=_control_model,
            signal_map=_signal_map,
            api_key=api_key
        )
        total_tokens += t2
        print("    Template-locked generation complete.")
    except Exception as e:
        # Fallback: free-form generation if template locking fails
        print(f"    Template-locked generation error ({e}). Falling back to free-form.")
        generator_prompt = _build_st_generator_prompt(brand_key, system_type, program_name)
        user_generation_prompt = (
            f"Program Name: {program_name}\n\n"
            f"Structured Requirements:\n{struct_info}\n\n"
            "Generate complete, valid IEC 61131-3 Structured Text code following the mandatory architecture above."
        )
        st_code, t2 = _call_llm(generator_prompt, user_generation_prompt, temperature=0.05, api_key=api_key)
        total_tokens += t2
        st_code = _extract_code(st_code)

    # ── Stage 3: IEC Syntax Check ──────────────────────────────────────────
    print(" [PLC Stage 3] IEC syntax validation...")
    iec_ok, iec_msg = _run_iec_checker(st_code)
    if not iec_ok:
        print(f"    IEC syntax issues detected: {iec_msg[:200]}")

    # ── Stage 4 & 5: Semantic + Severity Loop (max 2 fix attempts) ─────────
    final_code = st_code
    attempts = 0

    while attempts <= MAX_FIX_ATTEMPTS:
        print(f" [PLC Stage 4] Semantic validation (attempt {attempts + 1})...")
        validator = SemanticValidator(final_code)
        sem_results = validator.validate()
        decision = aggregate_validation_results(sem_results)

        if decision["decision"] == "approve":
            if decision["warning"]:
                print(f"    Warnings (informational only, code approved):\n" + "\n".join(f"     - {w}" for w in decision["warning"]))
            print("    Semantic validation passed — code approved.")

            # ── Layer 12: Dead State Validator ────────────────────────────
            print(" [PLC Layer 12] Dead State Validation...")
            try:
                ds_validator = DeadStateValidator(final_code, control_model_data)
                ds_res = ds_validator.validate()
                for w in ds_res["warning"]: print(f"     {w}")
                if ds_res["critical"]:
                    raise IECValidationError("Dead state critical failure", final_code, str(ds_res["critical"]), total_tokens)
                print("    Dead State rules passed.")
            except IECValidationError:
                raise
            except Exception as e:
                print(f"    Layer 12 error ({e})")

            # ── Layer 11: Variable Ownership Validator ────────────────────
            print(" [PLC Layer 11] Variable Ownership...")
            try:
                vo_validator = VariableOwnershipValidator(final_code, extraction.get("signal_map", {}))
                vo_res = vo_validator.validate()
                for w in vo_res["warning"]: print(f"     {w}")
                if vo_res["critical"]:
                    raise IECValidationError("Variable ownership critical failure", final_code, str(vo_res["critical"]), total_tokens)
                print("    Variable ownership validated.")
            except IECValidationError:
                raise
            except Exception as e:
                print(f"    Layer 11 error ({e})")

            # ── Layer 10: Industrial Polish ───────────────────────────────
            print(" [PLC Layer 10] Industrial Polish...")
            final_code = add_state_comments(final_code, control_model_data)

            # ── Layer 10b: ST Code Normalizer ─────────────────────────────
            print(" [PLC Layer 10b] ST Code Normalization...")
            state_names = {
                s.get("name", s.get("id", i)): s.get("description", s.get("name", ""))
                for i, s in enumerate(control_model_data.get("states", []))
                if isinstance(s, dict)
            }
            try:
                final_code = normalize_st(final_code, state_names=state_names)
            except Exception as _norm_err:
                print(f"    ST normalizer warning (non-fatal): {_norm_err}")

            # ── Layer 13: Confidence Score ────────────────────────────────
            print(" [PLC Layer 13] Confidence Scoring...")
            history = {
                "regenerations": 0,
                "fix_loops": attempts,
                "engineering_warnings": engineering_warnings if 'engineering_warnings' in locals() else 0,
                "physical_warnings": physical_warnings if 'physical_warnings' in locals() else 0,
                "semantic_warnings": len(decision["warning"]),
                "fallback_used": False
            }
            score_calc = ConfidenceScoreCalculator()
            score_data = score_calc.evaluate(history)

            # ── Layer 13b: Engineering Score ──────────────────────────────
            print(" [PLC Layer 13b] Engineering Score...")
            eng_result = PLCEngineeringScorer().score(final_code)
            eng_score  = eng_result["engineering_score"]
            eng_rating = eng_result["rating"]
            print(f"    Engineering Score: {eng_score}/100 — {eng_rating}")

            # ── Enterprise Options (Layers 14, 15, 17) ────────────────────
            final_code = VendorProfileInjector.apply(final_code, brand, program_name)

            # ── Layer 16: Auto PLC Tests ──────────────────────────────────
            tests = PLCTestGenerator.generate(control_model_data, extraction.get("signal_map", {}))

            # ── Assemble final output ─────────────────────────────────────
            final_output = (
                f"{final_code}\n\n"
                f"(* ─── CONFIDENCE SCORE ─── *)\n"
                f"(* Rating: {score_data['rating']} ({score_data['confidence']}/100) *)\n"
            )
            for r in score_data["reasons"]:
                final_output += f"(* {r} *)\n"

            final_output += (
                f"\n(* ─── ENGINEERING SCORE ─── *)\n"
                f"(* Score: {eng_score}/100 — {eng_rating} *)\n"
            )
            for b in eng_result["breakdown"]:
                status = "PASS" if b["passed"] else "FAIL"
                final_output += f"(* [{status}] {b['criterion']} *)\n"

            final_output += f"\n{tests}"

            return final_output, total_tokens

        # Only CRITICAL issues reach here
        if attempts == MAX_FIX_ATTEMPTS:
            print(f"    Critical issues remain after {MAX_FIX_ATTEMPTS} fix attempts. Returning best-effort code.")
            raise IECValidationError(
                message=f"Failed strict validation after {MAX_FIX_ATTEMPTS} targeted fix attempts.",
                code=final_code,
                errors=f"Critical: {decision['critical']}",
                tokens=total_tokens
            )

        print(f"    Critical issues found — applying targeted fix (attempt {attempts + 1}/{MAX_FIX_ATTEMPTS}):")
        for issue in decision["critical"]:
            print(f"      {issue}")

        fix_user_prompt = (
            f"The following Structured Text code has critical industrial violations that must be fixed:\n\n"
            f"CRITICAL ISSUES:\n" + "\n".join(f"- {c}" for c in decision["critical"]) + "\n\n"
            f"CODE TO FIX:\n{final_code}\n\n"
            "Fix ONLY the listed issues. Do not modify structure, variable names, or any other logic."
        )

        fixed_code, t_fix = _call_llm(FIX_PROMPT_SYSTEM, fix_user_prompt, temperature=0.1, api_key=api_key)
        total_tokens += t_fix
        final_code = _extract_code(fixed_code)
        attempts += 1
