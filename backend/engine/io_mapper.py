"""
I/O Mapper — Hardware Address-Aware Variable Generator
-------------------------------------------------------
Converts a user's tag list (CSV or structured JSON) into:
  - Vendor-specific hardware-addressed VAR declarations
  - A context string that informs the agentic pipeline of exact signal names
  - IEC 61131-3 AT %I0.x / AT %Q0.x notation per vendor

Supported vendors:
  SIEMENS       → AT %I{byte}.{bit} : BOOL  (TIA Portal / STEP 7)
  CODESYS       → AT %IX{byte}.{bit} : BOOL
  ALLEN_BRADLEY → (no AT syntax — uses tag names directly, Logix5000)
  SCHNEIDER     → AT %IX{byte}.{bit} : BOOL  (same as CODESYS)
  GENERIC       → no address (pure IEC)
"""

import csv
import io
import re
from typing import List, Dict, Optional

# ── Vendor address format ─────────────────────────────────────────────────────

_INPUT_FMT = {
    "SIEMENS":       "AT %I{byte}.{bit}",
    "CODESYS":       "AT %IX{byte}.{bit}",
    "ALLEN_BRADLEY": "",          # No AT syntax in Logix5000
    "SCHNEIDER":     "AT %IX{byte}.{bit}",
    "GENERIC":       "",
}
_OUTPUT_FMT = {
    "SIEMENS":       "AT %Q{byte}.{bit}",
    "CODESYS":       "AT %QX{byte}.{bit}",
    "ALLEN_BRADLEY": "",
    "SCHNEIDER":     "AT %QX{byte}.{bit}",
    "GENERIC":       "",
}
_MEMORY_FMT = {
    "SIEMENS":       "AT %M{byte}.{bit}",
    "CODESYS":       "AT %MX{byte}.{bit}",
    "ALLEN_BRADLEY": "",
    "SCHNEIDER":     "AT %MX{byte}.{bit}",
    "GENERIC":       "",
}


def _parse_address(addr: str) -> Optional[dict]:
    """Parse hardware address like '%I0.3', 'I0.3', '%Q1.5' into byte/bit."""
    if not addr:
        return None
    m = re.match(r'%?([IQM])X?(\d+)\.(\d+)', addr.strip().upper())
    if m:
        return {"dir": m.group(1), "byte": m.group(2), "bit": m.group(3)}
    # Word address like %IW2
    m2 = re.match(r'%?([IQM])W(\d+)', addr.strip().upper())
    if m2:
        return {"dir": m2.group(1), "byte": m2.group(2), "bit": None, "word": True}
    return None


def _iec_type(raw: str) -> str:
    """Normalize type string to IEC keyword."""
    t = raw.strip().upper()
    mapping = {
        "BOOL": "BOOL", "BOOLEAN": "BOOL",
        "INT": "INT", "INTEGER": "INT",
        "REAL": "REAL", "FLOAT": "REAL",
        "DINT": "DINT", "WORD": "WORD", "DWORD": "DWORD",
        "TIME": "TIME", "STRING": "STRING",
    }
    return mapping.get(t, "BOOL")  # default to BOOL for digital I/O


def parse_io_csv(csv_text: str) -> List[dict]:
    """
    Parse CSV with columns: name, address, type, description, direction
    direction: I (input), Q (output), M (memory/internal)
    Returns list of tag dicts.
    """
    tags = []
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    for row in reader:
        # Normalize column names (case insensitive)
        r = {k.strip().lower(): v.strip() for k, v in row.items()}
        name = r.get("name") or r.get("tag") or r.get("signal") or ""
        addr = r.get("address") or r.get("addr") or r.get("hw_address") or ""
        typ  = r.get("type") or r.get("data_type") or "BOOL"
        desc = r.get("description") or r.get("comment") or ""
        direction = r.get("direction") or r.get("dir") or ""

        if not name:
            continue

        # Infer direction from address or name prefix if not explicit
        if not direction:
            addr_parsed = _parse_address(addr)
            if addr_parsed:
                direction = addr_parsed["dir"]
            elif name.upper().startswith("I_") or name.upper().startswith("DI"):
                direction = "I"
            elif name.upper().startswith("Q_") or name.upper().startswith("DO"):
                direction = "Q"
            else:
                direction = "M"

        tags.append({
            "name":      name,
            "address":   addr,
            "type":      _iec_type(typ),
            "desc":      desc,
            "direction": direction.upper(),
        })

    return tags


def build_var_declarations(tags: List[dict], vendor: str) -> dict:
    """
    Build VAR_INPUT / VAR_OUTPUT / VAR blocks with hardware addresses.
    Returns dict with keys: var_input, var_output, var_internal, all_names
    """
    vendor = vendor.upper().replace(" ", "_").replace("-", "_")
    if vendor not in _INPUT_FMT:
        vendor = "GENERIC"

    inputs   = []
    outputs  = []
    internals = []

    for tag in tags:
        addr_parsed = _parse_address(tag["address"])
        name   = tag["name"]
        # Accept "type" or "signal_type"; infer from name prefix if absent
        raw_type = tag.get("type") or tag.get("signal_type") or ""
        if raw_type.upper() in ("INT", "INTEGER", "REAL", "FLOAT", "AI", "AO"):
            typ = "INT"
        elif name.upper().startswith(("AI_", "AO_")):
            typ = "INT"
        else:
            typ = "BOOL"
        desc   = f"  (* {tag.get('desc') or tag.get('description') or ''} *)" if (tag.get('desc') or tag.get('description')) else ""
        direct = tag.get("direction", "I")

        # Build address annotation
        at_str = ""
        if addr_parsed and not addr_parsed.get("word"):
            byte = addr_parsed["byte"]
            bit  = addr_parsed["bit"]
            if direct == "I":
                fmt = _INPUT_FMT[vendor]
            elif direct == "Q":
                fmt = _OUTPUT_FMT[vendor]
            else:
                fmt = _MEMORY_FMT[vendor]
            if fmt:
                at_str = " " + fmt.format(byte=byte, bit=bit)

        decl = f"    {name}{at_str} : {typ};{desc}"

        if direct == "I":
            inputs.append(decl)
        elif direct == "Q":
            outputs.append(decl)
        else:
            internals.append(decl)

    return {
        "var_input":    "\n".join(inputs),
        "var_output":   "\n".join(outputs),
        "var_internal": "\n".join(internals),
        "all_names":    [t["name"] for t in tags],
        "inputs":       [t["name"] for t in tags if t["direction"] == "I"],
        "outputs":      [t["name"] for t in tags if t["direction"] == "Q"],
    }


def build_io_context(io_map: dict, vendor: str) -> str:
    """
    Build a natural-language + structured context block that the agentic
    pipeline injects into the description so the LLM uses EXACT tag names.
    io_map format: {"tags": [...parsed tag dicts...], "vendor": "SIEMENS"}
    """
    tags  = io_map.get("tags", [])
    if not tags:
        return ""

    decls = build_var_declarations(tags, vendor)

    lines = [
        "=== HARDWARE I/O MAP (USE THESE EXACT NAMES — DO NOT INVENT OTHERS) ===",
        "",
        "INPUTS (VAR_INPUT):",
        decls["var_input"] or "    (none)",
        "",
        "OUTPUTS (VAR_OUTPUT):",
        decls["var_output"] or "    (none)",
        "",
    ]
    if decls["var_internal"]:
        lines += ["INTERNAL (VAR):", decls["var_internal"], ""]

    lines.append("=== END I/O MAP ===")
    return "\n".join(lines)


def parse_io_map_to_tags(io_map: dict) -> List[dict]:
    """
    Convert io_map dict (from the /generate endpoint's io_map field) into
    the flat tag-list format that generate_st_direct() expects.
    io_map format: {"tags": [...], "vendor": "SIEMENS"}
    Output format: [{"name", "direction"(INPUT/OUTPUT), "signal_type", "address", "desc"}, ...]
    """
    raw_tags = io_map.get("tags", [])
    result = []
    for t in raw_tags:
        d = t.get("direction", "").upper()
        if d in ("I", "INPUT", "DI"):
            direction = "INPUT"
        elif d in ("Q", "OUTPUT", "DO"):
            direction = "OUTPUT"
        elif d in ("AI", "ANALOG_IN", "ANALOG INPUT"):
            direction = "ANALOG_IN"
        elif d in ("AO", "ANALOG_OUT", "ANALOG OUTPUT"):
            direction = "ANALOG_OUT"
        else:
            # Infer from name prefix
            nm = t.get("name", "").upper()
            if nm.startswith(("AI_",)):
                direction = "ANALOG_IN"
            elif nm.startswith(("AO_",)):
                direction = "ANALOG_OUT"
            elif nm.startswith(("I_", "DI_")):
                direction = "INPUT"
            elif nm.startswith(("Q_", "DO_")):
                direction = "OUTPUT"
            else:
                direction = d or "INPUT"
        nm = t.get("name", "")
        result.append({
            "name":        nm,
            "direction":   direction,
            "type":        "INT" if nm.upper().startswith(("AI_", "AO_")) else "BOOL",
            "signal_type": t.get("signal_type", t.get("type", "")),
            "address":     t.get("address", ""),
            "desc":        t.get("desc", t.get("description", "")),
        })
    return result


def inject_addresses_into_code(st_code: str, tags: List[dict], vendor: str) -> str:
    """
    Post-process generated ST code: inject hardware AT addresses into VAR declarations.
    Finds lines like '    I_Start : BOOL;' and adds AT annotation if tag is in list.
    """
    vendor = vendor.upper().replace(" ", "_").replace("-", "_")
    if vendor not in _INPUT_FMT:
        vendor = "GENERIC"

    tag_map = {t["name"]: t for t in tags}
    result_lines = []

    for line in st_code.splitlines():
        # Match: optional spaces, identifier, optional AT, colon, type, semicolon
        m = re.match(r'^(\s+)(\w+)(\s+AT\s+\S+)?\s*:\s*(\w+)\s*;(.*)$', line)
        if m and m.group(2) in tag_map:
            tag    = tag_map[m.group(2)]
            indent = m.group(1)
            name   = m.group(2)
            typ    = m.group(4)
            rest   = m.group(5)

            addr_parsed = _parse_address(tag["address"])
            if addr_parsed and not addr_parsed.get("word") and not m.group(3):
                byte = addr_parsed["byte"]
                bit  = addr_parsed["bit"]
                d    = tag["direction"]
                fmt  = (_INPUT_FMT if d == "I" else _OUTPUT_FMT if d == "Q" else _MEMORY_FMT)[vendor]
                at_str = (" " + fmt.format(byte=byte, bit=bit)) if fmt else ""
                comment = f"  (* {tag['desc']} *)" if tag.get("desc") else ""
                line = f"{indent}{name}{at_str} : {typ};{comment}"
        result_lines.append(line)

    return "\n".join(result_lines)
