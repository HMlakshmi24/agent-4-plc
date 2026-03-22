"""
AutoMind Platform - Stress Test Runner v2
Fixed: SemanticValidator call, network retry, --set flag, summary.json
"""
from __future__ import annotations
import sys, io, json, time, argparse, traceback, re
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.agentic_pipeline import run_agentic_pipeline, IECValidationError
from backend.engine.hmi_agentic_pipeline import run_hmi_agentic_pipeline
from backend.engine.semantic_validator import SemanticValidator
from backend.engine.state_transition_validator import StateTransitionValidator
from backend.engine.engineering_scorer import PLCEngineeringScorer
from backend.engine.pid_validator import PIDValidator
from backend.engine.tag_consistency_enforcer import (
    build_tag_registry, format_hmi_tag_hint, format_pid_tag_hint)
from backend.engine.hmi_plc_binder import build_hmi_bindings, format_binding_hint
from backend.engine.project_exporter import build_project_zip, build_report_md, AUTOMIND_VERSION
from backend.core.enhanced_html_exporter_fixed import generate_enhanced_html_from_json

BASIC_PROMPTS_FILE    = ROOT / "tests" / "stress_prompts.json"
EXTENDED_PROMPTS_FILE = ROOT / "tests" / "extended_stress_prompts.json"
RESULTS_DIR  = ROOT / "tests" / "results"
REPORT_FILE  = RESULTS_DIR / "report.md"
SUMMARY_FILE = RESULTS_DIR / "summary.json"
_RETRY = 2
_DELAY = 3

def _make_stub(pname: str, domain: str) -> str:
    """Minimal valid ST skeleton returned when LLM is unreachable.

    Includes a 4-state CASE block with FAULT branch and Q_Alarm := TRUE so the
    engineering scorer, semantic validator, and state-transition validator all
    exercise real logic even with no LLM connectivity.
    """
    # Pick domain-appropriate output / sensor names
    _OUT = {
        "conveyor":         ("Q_ConveyorMotor", "I_PartSensor",       "I_JamSensor"),
        "pump":             ("Q_PumpMotor",     "I_LevelLow",         "I_Overload"),
        "tank":             ("Q_FillValve",     "I_LevelHigh",        "I_LevelLow"),
        "motor":            ("Q_Motor",         "I_Overload",         "I_ThermalFault"),
        "heater":           ("Q_Heater",        "I_TempHigh",         "I_ThermalFault"),
        "hvac":             ("Q_Fan",           "I_TempHigh",         "I_FilterFault"),
        "mixing":           ("Q_MixerMotor",    "I_LevelLow",         "I_TempHigh"),
        "batch":            ("Q_AgitatorMotor", "I_LevelHigh",        "I_TempHigh"),
        "dosing":           ("Q_DosePump",      "I_SafetyValveOpen",  "I_LevelLow"),
        "reactor":          ("Q_AgitatorMotor", "I_LevelHigh",        "I_TempHigh"),
        "packaging":        ("Q_PackMotor",     "I_PartSensor",       "I_JamSensor"),
        "traffic_light":    ("Q_Green",         "I_PedestrianButton", "I_VehicleDetector"),
        "press":            ("Q_RamExtend",     "I_GuardClosed",      "I_TwoHand1"),
        "elevator":         ("Q_MotorUp",       "I_DoorClosed",       "I_FloorSensor"),
        "gate":             ("Q_GateOpen",      "I_GateClosed",       "I_ObstacleSensor"),
        "car_wash":         ("Q_WashMotor",     "I_VehiclePresent",   "I_DoorClosed"),
        "crane":            ("Q_HoistUp",       "I_UpperLimit",       "I_LowerLimit"),
        "compressor":       ("Q_CompMotor",     "I_PressureHigh",     "I_Overload"),
        "water_treatment":  ("Q_DosePump",      "I_PHSensor",         "I_TurbidityHigh"),
        "sorter":           ("Q_SortValve",     "I_PartSensor",       "I_BarcodeScan"),
        "safety_interlock": ("Q_SafetyRelay",   "I_GuardClosed",      "I_LightCurtain"),
        "temperature":      ("Q_Heater",        "I_TempHigh",         "I_ThermalFault"),
    }
    q_out, i_s1, i_s2 = _OUT.get(domain, ("Q_Motor", "I_Sensor1", "I_Sensor2"))

    return f"""\
PROGRAM {pname}
VAR
    I_Start        : BOOL;
    I_Stop         : BOOL;
    I_EStop        : BOOL;
    {i_s1:<20} : BOOL;
    {i_s2:<20} : BOOL;
    {q_out:<20} : BOOL;
    Q_Alarm        : BOOL;
    M_State        : INT := 0;
    T_StartDelay   : TON;
END_VAR

(* E-Stop override — highest priority *)
IF I_EStop THEN
    M_State        := 99;
    {q_out} := FALSE;
    Q_Alarm        := TRUE;
END_IF;

T_StartDelay(IN := (M_State = 1), PT := T#3S);

CASE M_State OF

    0: (* Idle *)
        {q_out} := FALSE;
        Q_Alarm        := FALSE;
        IF I_Start AND NOT I_Stop THEN
            M_State := 1;
        END_IF;

    1: (* Starting *)
        {q_out} := FALSE;
        IF T_StartDelay.Q THEN
            M_State := 2;
        END_IF;

    2: (* Running *)
        {q_out} := TRUE;
        IF I_Stop THEN
            M_State := 0;
        END_IF;
        IF {i_s2} THEN
            M_State := 99;
        END_IF;

    99: (* Fault *)
        {q_out} := FALSE;
        Q_Alarm        := TRUE;
        IF NOT I_EStop THEN
            M_State := 0;
        END_IF;

    ELSE
        M_State := 0;

END_CASE;

END_PROGRAM
"""

def _load(mode):
    files = {"basic": [BASIC_PROMPTS_FILE],
             "extended": [EXTENDED_PROMPTS_FILE],
             "all": [BASIC_PROMPTS_FILE, EXTENDED_PROMPTS_FILE]}[mode]
    out = []
    for f in files:
        if f.exists():
            out.extend(json.loads(f.read_text(encoding="utf-8")))
        else:
            print(f"  WARNING: {f} not found.")
    return out

def _safe(pid, name):
    return f"{pid:02d}_" + "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

def _gen_plc(desc, pname, brand, domain="general"):
    last = None
    for attempt in range(1, _RETRY + 2):
        try:
            code, _ = run_agentic_pipeline(description=desc, program_name=pname, brand=brand)
            return code, "OK"
        except IECValidationError as e:
            partial = getattr(e, "code", None) or ""
            if len(partial) > 100:
                return partial, "IEC_WARN"
            last = e; break
        except Exception as e:
            last = e
            if any(k in str(e).lower() for k in ("connection","network","timeout","socket","http")) \
               and attempt <= _RETRY:
                print(f"      Retry {attempt} in {_DELAY}s..."); time.sleep(_DELAY); continue
            break
    # LLM unavailable — return a minimal but valid stub so validation layers run
    stub = _make_stub(pname, domain)
    return stub, f"STUB (LLM_DOWN: {last})"

def _gen_pid(prompt, system_name):
    try:
        from backend.routes.pid_generator import P_AND_ID_SYSTEM_MESSAGE, _build_pid_html
        from backend.core.openai_client import generate_layout
        pid_data = json.loads(generate_layout(
            P_AND_ID_SYSTEM_MESSAGE.replace("{requirement}", prompt), prompt))
    except Exception as e:
        print(f"      [PID] fallback ({type(e).__name__})")
        from backend.routes.pid_generator import _fallback_pid
        pid_data = _fallback_pid(prompt)
    from backend.routes.pid_generator import _build_pid_html
    return _build_pid_html(pid_data, system_name), pid_data

def _sm(code):
    return {
        "inputs":          list(dict.fromkeys(re.findall(r"\bI_[A-Za-z]\w+", code))),
        "outputs":         list(dict.fromkeys(re.findall(r"\bQ_[A-Za-z]\w+", code))),
        "timers":          list(dict.fromkeys(re.findall(r"\bT_[A-Za-z]\w+", code))),
        "counters":        list(dict.fromkeys(re.findall(r"\bM_[A-Za-z]*Count\w*", code))),
        "internal_states": list(dict.fromkeys(re.findall(r"\bM_[A-Za-z]\w+", code))),
    }

def _fs(s):
    if s in ("OK", "IEC_WARN", "PASS"):
        return "OK"
    if "STUB" in s:
        return "STUB"
    if "WARN" in s:
        return "WARN"
    return "FAIL"

def run_prompt(prompt, results_dir):
    pid, name  = prompt["id"], prompt["name"]
    domain     = prompt.get("domain", "general")
    pname      = prompt.get("program_name", "PLCProgram")
    brand      = prompt.get("brand", "SIEMENS")
    desc       = prompt["description"]
    folder     = results_dir / _safe(pid, name)
    folder.mkdir(parents=True, exist_ok=True)
    r = {
        "id": pid, "name": name, "program_name": pname, "brand": brand, "domain": domain,
        "folder": str(folder.relative_to(ROOT)),
        "plc_status": "NOT RUN", "hmi_status": "NOT RUN", "pid_status": "NOT RUN",
        "val_status": "NOT RUN", "trans_status": "NOT RUN",
        "eng_score": 0, "eng_rating": "N/A",
        "errors": [], "warnings": [], "files": [], "elapsed_s": 0.0,
    }
    t0 = time.time(); code = ""; sm = {}

    # 1. PLC
    print(f"  [PLC]  {name}")
    code, plc_s = _gen_plc(desc, pname, brand, domain=domain); r["plc_status"] = plc_s
    if code:
        (folder/"plc_program.st").write_text(code, encoding="utf-8")
        r["files"].append(str((folder/"plc_program.st").relative_to(ROOT)))
        sm = _sm(code); print(f"         {len(code.splitlines())} lines [{plc_s}]")
    else:
        r["errors"].append(plc_s); print(f"         FAILED: {plc_s}")

    # 2. Score
    eng = PLCEngineeringScorer().score(code) if code else {
        "engineering_score": 0, "rating": "N/A", "breakdown": [], "failed_checks": []}
    r["eng_score"] = eng["engineering_score"]; r["eng_rating"] = eng["rating"]
    if code:
        (folder/"engineering_score.json").write_text(json.dumps(eng, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"engineering_score.json").relative_to(ROOT)))

    # 3. Semantic validation  <<< BUG FIX: SemanticValidator(code).validate()
    sem = {}
    if code:
        sem = SemanticValidator(code).validate()
        r["val_status"] = "PASS" if not sem.get("critical") else "FAIL"
        r["warnings"].extend(sem.get("warning", [])); r["errors"].extend(sem.get("critical", []))
        (folder/"semantic_validation.json").write_text(json.dumps(sem, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"semantic_validation.json").relative_to(ROOT)))

    # 4. State transitions
    stv = {}
    if code:
        stv = StateTransitionValidator(code).to_dict()
        r["trans_status"] = "WARN" if stv.get("warnings") else "PASS"
        r["warnings"].extend(stv.get("warnings", []))
        (folder/"state_transitions.json").write_text(json.dumps(stv, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"state_transitions.json").relative_to(ROOT)))

    # 5. Tag registry
    reg = build_tag_registry(sm, domain_type=domain, program_name=pname)
    (folder/"tag_registry.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    r["files"].append(str((folder/"tag_registry.json").relative_to(ROOT)))

    # 6. HMI bindings
    bindings = build_hmi_bindings(sm, tag_registry=reg)
    bhint    = format_binding_hint(bindings)
    (folder/"hmi_bindings.json").write_text(json.dumps(bindings, indent=2), encoding="utf-8")
    r["files"].append(str((folder/"hmi_bindings.json").relative_to(ROOT)))

    # 7. HMI
    hmi_html = ""
    try:
        print(f"  [HMI]  {name}")
        hl = run_hmi_agentic_pipeline(f"{format_hmi_tag_hint(reg)}\n{bhint}\n\n{desc}")
        hl.pop("_tokens_used", None)
        (folder/"hmi_layout.json").write_text(json.dumps(hl, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"hmi_layout.json").relative_to(ROOT)))
        hmi_html = generate_enhanced_html_from_json(hl)
        (folder/"hmi_dashboard.html").write_text(hmi_html, encoding="utf-8")
        r["files"].append(str((folder/"hmi_dashboard.html").relative_to(ROOT)))
        r["hmi_status"] = "OK"; print("         HMI OK")
    except Exception as e:
        r["hmi_status"] = "FAILED"; r["errors"].append(f"HMI:{e}"); print(f"         HMI FAILED:{type(e).__name__}")

    # 8. P&ID
    pid_html = ""; pid_data = {}
    try:
        print(f"  [PID]  {name}")
        pid_html, pid_data = _gen_pid(f"{format_pid_tag_hint(reg)}\n\n{desc}", name)
        (folder/"pid_layout.json").write_text(json.dumps(pid_data, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"pid_layout.json").relative_to(ROOT)))
        (folder/"pid_diagram.html").write_text(pid_html, encoding="utf-8")
        r["files"].append(str((folder/"pid_diagram.html").relative_to(ROOT)))
        r["pid_status"] = "OK"; print("         P&ID OK")
    except Exception as e:
        r["pid_status"] = "FAILED"; r["errors"].append(f"PID:{e}"); print(f"         P&ID FAILED:{type(e).__name__}")

    # 9. P&ID validation
    if pid_data:
        pv = PIDValidator(pid_data).validate()
        r["warnings"].extend(pv.get("warnings", []))
        (folder/"pid_validation.json").write_text(json.dumps(pv, indent=2), encoding="utf-8")
        r["files"].append(str((folder/"pid_validation.json").relative_to(ROOT)))

    # 10. ZIP
    try:
        llm_status = "STUB" if "STUB" in plc_s else "REAL"
        rmd = build_report_md(program_name=pname, engineering_score=eng,
            validation_result={"iec_valid": r["val_status"]=="PASS", "iec_errors":[], "iec_warnings":[]},
            signal_map=sm, warnings=r["warnings"], brand=brand, domain_type=domain,
            semantic_result=sem, state_transitions=stv, llm_status=llm_status)
        zb = build_project_zip(st_code=code, hmi_html=hmi_html, pid_html=pid_html,
                               report_md=rmd, program_name=pname)
        zp = folder / f"{pname}_project.zip"; zp.write_bytes(zb)
        r["files"].append(str(zp.relative_to(ROOT)))
    except Exception as e:
        r["warnings"].append(f"ZIP:{e}")

    r["elapsed_s"] = round(time.time() - t0, 1)
    return r

def _report(results, elapsed, mode):
    n = len(results)
    passed   = sum(1 for r in results if r["plc_status"] in ("OK","IEC_WARN"))
    warnings = sum(1 for r in results if r["plc_status"] == "IEC_WARN")
    stubs    = sum(1 for r in results if "STUB" in r["plc_status"])
    failures = n - passed - stubs
    avg  = sum(r["eng_score"] for r in results) / max(n, 1)
    slow = max(results, key=lambda r: r["elapsed_s"]) if results else {}
    failing = [r for r in results if _fs(r["plc_status"]) == "FAIL"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = [
        "# AutoMind Stress Test Report", "",
        "| Metric | Value |", "|--------|-------|",
        f"| Total tests | **{n}** |",
        f"| Passed (LLM) | **{passed}** |",
        f"| IEC Warnings | {warnings} |",
        f"| Stubs (LLM down) | {stubs} |",
        f"| Hard Failures | {failures} |",
        f"| Average Engineering Score | **{avg:.0f}/100** |",
        f"| Slowest | {slow.get('name','?')} ({slow.get('elapsed_s','?')}s) |",
        f"| Total elapsed | {elapsed:.1f}s |",
        f"| Test set | {mode} |",
        f"| Generated | {now} |",
        f"| AutoMind version | {AUTOMIND_VERSION} |", "",
    ]
    if failing:
        L += ["## Failing Prompts", ""]
        for r in failing:
            L.append(f"- **{r['id']}. {r['name']}** `{r['plc_status']}`")
            for e in r["errors"][:2]: L.append(f"  - {e}")
        L += [""]
    L += ["---", "", "## Results Table", "",
          "| # | Name | Program | PLC | HMI | P&ID | Val | Trans | Score | Rating |",
          "|---|------|---------|-----|-----|------|-----|-------|-------|--------|"]
    for r in results:
        L.append(f"| {r['id']} | {r['name'][:28]} | `{r['program_name']}` "
                 f"| {_fs(r['plc_status'])} | {_fs(r['hmi_status'])} "
                 f"| {_fs(r['pid_status'])} | {_fs(r['val_status'])} "
                 f"| {_fs(r['trans_status'])} | {r['eng_score']}/100 | {r['eng_rating']} |")
    L += ["---", f"*AutoMind Stress Test Runner v{AUTOMIND_VERSION}*"]
    return "\n".join(L) + "\n"

def _summary(results, elapsed, mode):
    n = len(results); passed = sum(1 for r in results if r["plc_status"] in ("OK","IEC_WARN"))
    stubs = sum(1 for r in results if "STUB" in r["plc_status"])
    avg = sum(r["eng_score"] for r in results) / max(n, 1)
    slow = max(results, key=lambda r: r["elapsed_s"]) if results else {}
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "automind_version": AUTOMIND_VERSION, "test_set": mode,
        "total_tests": n, "plc_passed": passed,
        "plc_stubs": stubs,
        "plc_warnings": sum(1 for r in results if r["plc_status"]=="IEC_WARN"),
        "plc_failed": n-passed-stubs, "avg_engineering_score": round(avg,1),
        "total_elapsed_s": elapsed,
        "slowest_prompt": {"id": slow.get("id"),"name":slow.get("name"),"elapsed_s":slow.get("elapsed_s")},
        "failing_prompts": [{"id":r["id"],"name":r["name"],"status":r["plc_status"]}
                            for r in results if _fs(r["plc_status"])=="FAIL"],
        "results": results,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", dest="test_set", choices=["basic","extended","all"], default="basic")
    parser.add_argument("--id",  dest="prompt_id", type=int, default=None)
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("="*62 + "\n  AutoMind Stress Test Runner v2")
    print(f"  Set: {args.test_set}   ID: {args.prompt_id or 'all'}\n" + "="*62)
    prompts = _load(args.test_set)
    if args.prompt_id is not None:
        prompts = [p for p in prompts if p["id"]==args.prompt_id]
        if not prompts: print(f"No prompt id={args.prompt_id}"); sys.exit(1)
    print(f"\nLoaded {len(prompts)} prompt(s).\n")
    results = []; t0 = time.time()
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] #{prompt['id']} -- {prompt['name']}\n" + "-"*50)
        try:
            r = run_prompt(prompt, RESULTS_DIR)
        except Exception as e:
            traceback.print_exc()
            r = {"id":prompt["id"],"name":prompt["name"],"program_name":prompt.get("program_name","?"),
                 "brand":prompt.get("brand","?"),"domain":prompt.get("domain","?"),"folder":"N/A",
                 "plc_status":"FATAL","hmi_status":"FATAL","pid_status":"FATAL",
                 "val_status":"FATAL","trans_status":"FATAL",
                 "eng_score":0,"eng_rating":"N/A","errors":[str(e)],"warnings":[],"files":[],"elapsed_s":0.0}
        results.append(r)
        print(f"  PLC={r['plc_status']} | Score={r['eng_score']}/100 | Val={r['val_status']} | {r['elapsed_s']}s")
    elapsed = round(time.time()-t0, 1)
    REPORT_FILE.write_text(_report(results, elapsed, args.test_set), encoding="utf-8")
    SUMMARY_FILE.write_text(json.dumps(_summary(results, elapsed, args.test_set), indent=2), encoding="utf-8")
    passed = sum(1 for r in results if r["plc_status"] in ("OK","IEC_WARN"))
    stubs  = sum(1 for r in results if "STUB" in r["plc_status"])
    avg    = sum(r["eng_score"] for r in results)/max(len(results),1)
    print(f"\n  Done {elapsed:.1f}s | Passed:{passed}/{len(results)} | Stubs:{stubs} | Avg:{avg:.0f}/100")
    print(f"  Report:  {REPORT_FILE}\n  Summary: {SUMMARY_FILE}\n")

if __name__=="__main__":
    main()
