"""
Industrial P&ID Generator — ISA 5.1 / ISA 5.4 Compliant
=========================================================
Produces a fully-animated, interactive P&ID diagram:
  • ISA instrument bubbles (circle with tag number + dividing line)
  • SVG process equipment (tanks, pumps, heat exchangers, vessels)
  • Pipe routing with flow direction arrows
  • Control loops (feedback + feedforward)
  • Real-time simulation (flow, pressure, temperature animation)
  • Clickable equipment with process interaction
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class PIDRequest(BaseModel):
    prompt: str
    system_name: Optional[str] = "Process System"


# ── ISA-5.1 SVG SYMBOL LIBRARY ────────────────────────────────────────────────

ISA_SVG_DEFS = """
<defs>
  <!-- Arrow marker for pipe flow direction -->
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
    <polygon points="0,0 8,3 0,6" fill="#64748b"/>
  </marker>
  <marker id="arrow-active" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
    <polygon points="0,0 8,3 0,6" fill="#22c55e"/>
  </marker>
  <!-- Crosshatch pattern for vessels under pressure -->
  <pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="0" y2="6" stroke="#1e3a5f" stroke-width="1"/>
  </pattern>
  <!-- Gradient for tanks -->
  <linearGradient id="tankGrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#0f172a;stop-opacity:1"/>
    <stop offset="50%" style="stop-color:#1e293b;stop-opacity:1"/>
    <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1"/>
  </linearGradient>
  <!-- Flow animation -->
  <filter id="glow">
    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>"""


P_AND_ID_SYSTEM_MESSAGE = """You are a Senior Process Engineer (PE) creating an ISA 5.1 compliant P&ID.
Output ONLY a single valid JSON object. No markdown, no explanation.

FULL P&ID JSON SCHEMA:
{
  "system_name": "string",
  "revision": "A",
  "project": "string",
  "drawn_by": "AI",
  "date": "2024-01-01",

  "equipment": [
    {
      "id": "TK-101",
      "type": "vertical_tank" | "horizontal_tank" | "pump" | "centrifugal_pump" | "valve_gate" |
              "valve_control" | "valve_check" | "heat_exchanger" | "vessel" | "reactor" |
              "compressor" | "fan" | "filter" | "mixer",
      "label": "Feed Tank",
      "service": "Process water storage",
      "design_pressure": "10 barg",
      "design_temp": "80°C",
      "material": "CS",
      "x": 150,
      "y": 300,
      "width": 100,
      "height": 140
    }
  ],

  "instruments": [
    {
      "id": "LT-101",
      "tag": "LT-101",
      "type": "LT" | "TT" | "PT" | "FT" | "AT" | "LS" | "TS" | "PS" | "FS" | "LSH" | "LSL",
      "service": "Tank TK-101 level transmitter",
      "x": 280,
      "y": 300,
      "connected_to": "TK-101",
      "setpoint": null,
      "hi_alarm": 90,
      "lo_alarm": 10,
      "value": 55,
      "unit": "%",
      "loop": "100"
    }
  ],

  "pipes": [
    {
      "id": "2-P-101-50A-CS",
      "from": "TK-101",
      "to": "P-101",
      "size": "2\"",
      "spec": "50A-CS",
      "service": "Process water",
      "path": [[150,370],[150,430],[280,430]],
      "type": "process" | "utility" | "instrument" | "drain",
      "state": "active" | "inactive"
    }
  ],

  "control_loops": [
    {
      "id": "LIC-101",
      "tag": "LIC-101",
      "type": "LIC" | "TIC" | "PIC" | "FIC" | "AIC",
      "description": "Tank TK-101 level control",
      "x": 400,
      "y": 200,
      "controlled_device": "V-101",
      "primary_element": "LT-101",
      "setpoint": 60,
      "loop": "100"
    }
  ]
}

ISA-5.1 INSTRUMENT TAG RULES:
- LT = Level Transmitter, LI = Level Indicator, LSH = Level Switch High
- TT = Temp Transmitter, TI = Temp Indicator, TC = Temp Controller
- PT = Pressure Transmitter, PI = Pressure Indicator, PSH = Pressure Switch High
- FT = Flow Transmitter, FI = Flow Indicator, FC = Flow Controller
- LIC = Level Indicating Controller, TIC = Temp Indicating Controller
- Loop numbers: 100-series for unit 1, 200-series for unit 2, etc.

EQUIPMENT PLACEMENT (SVG canvas 1100x750):
- Tanks: left area, x=50-300, y=150-500, width=100, height=140
- Pumps: middle, x=350-500, y=350-450
- Valves: x=200-600, near connecting pipes
- Heat exchangers: x=550-700, y=200-400
- Instruments: place close to the equipment they measure (offset 80-120px)
- Control loops: place in DCS symbol area, top center x=400-700, y=50-180
- Keep minimum 100px clearance between equipment

PIPE ROUTING:
- Use orthogonal paths (horizontal + vertical segments only)
- path is array of [x,y] waypoints defining the pipe route
- Avoid crossing pipes where possible
- Show all major process flows

GENERATE COMPLETE INDUSTRIAL P&ID:
- Minimum 3 major equipment items
- Every tank needs: level transmitter, level control loop
- Every pump needs: pressure gauge, flow meter downstream
- Every heat exchanger needs: temperature transmitters on both sides
- All process connections piped
- Realistic process conditions (temperature, pressure, flow)
"""


def _build_pid_html(pid_data: dict, system_name: str) -> str:
    """Build a complete interactive ISA-5.1 P&ID HTML page from JSON data."""

    import json as _json

    title    = system_name or pid_data.get("system_name", "P&ID Diagram")
    rev      = pid_data.get("revision", "A")
    proj     = pid_data.get("project", "")
    equip    = pid_data.get("equipment", [])
    instr    = pid_data.get("instruments", [])
    pipes    = pid_data.get("pipes", [])
    loops    = pid_data.get("control_loops", [])

    # ── Build equipment SVG ────────────────────────────────────────────────────
    equip_svg = []
    for eq in equip:
        eid  = eq.get("id", "EQ")
        x    = eq.get("x", 100)
        y    = eq.get("y", 200)
        w    = eq.get("width", 100)
        h    = eq.get("height", 140)
        lbl  = eq.get("label", eid)
        typ  = eq.get("type", "vertical_tank")
        svc  = eq.get("service", "")

        if "tank" in typ or "vessel" in typ or "reactor" in typ:
            # Vertical tank / vessel
            equip_svg.append(f"""
  <g id="eq-{eid}" class="equipment-g" data-id="{eid}" data-type="{typ}"
     onclick="selectEquipment('{eid}')">
    <title>{eid}: {lbl}\\n{svc}</title>
    <!-- tank body -->
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"
          fill="url(#tankGrad)" stroke="#334155" stroke-width="2"/>
    <!-- top head (elliptical) -->
    <ellipse cx="{x+w//2}" cy="{y}" rx="{w//2}" ry="{int(w*0.12)}"
             fill="#1e293b" stroke="#334155" stroke-width="2"/>
    <!-- bottom head -->
    <ellipse cx="{x+w//2}" cy="{y+h}" rx="{w//2}" ry="{int(w*0.12)}"
             fill="#1e293b" stroke="#334155" stroke-width="2"/>
    <!-- liquid level indicator (animated) -->
    <rect id="liq-eq-{eid}" x="{x+3}" y="{y+h//2}" width="{w-6}" height="{h//2-2}"
          fill="#0ea5e9" opacity="0.3" class="tank-liquid"/>
    <!-- nozzle top -->
    <line x1="{x+w//2}" y1="{y-int(w*0.12)}" x2="{x+w//2}" y2="{y-int(w*0.12)-15}"
          stroke="#475569" stroke-width="4"/>
    <!-- nozzle bottom -->
    <line x1="{x+w//2}" y1="{y+h+int(w*0.12)}" x2="{x+w//2}" y2="{y+h+int(w*0.12)+15}"
          stroke="#475569" stroke-width="4"/>
    <!-- equipment tag bubble -->
    <rect x="{x}" y="{y+h+int(w*0.12)+16}" width="{w}" height="18" rx="3"
          fill="#0f2744" stroke="#334155" stroke-width="1"/>
    <text x="{x+w//2}" y="{y+h+int(w*0.12)+28}" text-anchor="middle"
          fill="#94a3b8" font-size="11" font-weight="700" font-family="monospace">{eid}</text>
    <text x="{x+w//2}" y="{y+h+int(w*0.12)+46}" text-anchor="middle"
          fill="#64748b" font-size="9" font-family="Arial">{lbl}</text>
  </g>""")

        elif "pump" in typ or "compressor" in typ:
            cx = x + w//2
            cy = y + h//2
            r  = min(w,h)//2
            equip_svg.append(f"""
  <g id="eq-{eid}" class="equipment-g clickable" data-id="{eid}" data-type="{typ}"
     onclick="togglePump('{eid}')">
    <title>{eid}: {lbl}\\n{svc}</title>
    <!-- pump casing -->
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="#0f172a" stroke="#475569" stroke-width="2.5"
            id="pcasing-{eid}"/>
    <!-- impeller (spins) -->
    <g id="pimp-{eid}" style="transform-origin:{cx}px {cy}px">
      <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r+6}" stroke="#475569" stroke-width="3" stroke-linecap="round"/>
      <line x1="{cx}" y1="{cy}" x2="{cx+r-6}" y2="{cy+int((r-6)*0.7)}" stroke="#475569" stroke-width="3" stroke-linecap="round"/>
      <line x1="{cx}" y1="{cy}" x2="{cx-r+6}" y2="{cy+int((r-6)*0.7)}" stroke="#475569" stroke-width="3" stroke-linecap="round"/>
    </g>
    <circle cx="{cx}" cy="{cy}" r="5" fill="#475569" id="phub2-{eid}"/>
    <!-- suction stub -->
    <line x1="{x}" y1="{cy}" x2="{x-20}" y2="{cy}" stroke="#475569" stroke-width="4"/>
    <!-- discharge stub -->
    <line x1="{x+w}" y1="{cy}" x2="{x+w+20}" y2="{cy}" stroke="#475569" stroke-width="4"/>
    <text x="{cx}" y="{y+h+18}" text-anchor="middle" fill="#94a3b8"
          font-size="11" font-weight="700" font-family="monospace">{eid}</text>
    <text x="{cx}" y="{y+h+30}" text-anchor="middle" fill="#64748b" font-size="9">{lbl}</text>
  </g>""")

        elif "heat_exchanger" in typ:
            equip_svg.append(f"""
  <g id="eq-{eid}" class="equipment-g" data-id="{eid}" data-type="{typ}"
     onclick="selectEquipment('{eid}')">
    <title>{eid}: {lbl}\\n{svc}</title>
    <!-- shell -->
    <ellipse cx="{x}" cy="{y+h//2}" rx="{int(w*0.1)}" ry="{h//2}"
             fill="#1e293b" stroke="#475569" stroke-width="2"/>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1e293b" stroke="#475569" stroke-width="2"/>
    <ellipse cx="{x+w}" cy="{y+h//2}" rx="{int(w*0.1)}" ry="{h//2}"
             fill="#1e293b" stroke="#475569" stroke-width="2"/>
    <!-- tubes -->
    <line x1="{x+int(w*0.1)}" y1="{y+h//2-12}" x2="{x+w-int(w*0.1)}" y2="{y+h//2-12}"
          stroke="#475569" stroke-width="2"/>
    <line x1="{x+int(w*0.1)}" y1="{y+h//2}" x2="{x+w-int(w*0.1)}" y2="{y+h//2}"
          stroke="#475569" stroke-width="2"/>
    <line x1="{x+int(w*0.1)}" y1="{y+h//2+12}" x2="{x+w-int(w*0.1)}" y2="{y+h//2+12}"
          stroke="#475569" stroke-width="2"/>
    <!-- nozzles -->
    <line x1="{x}" y1="{y+h//2-15}" x2="{x-20}" y2="{y+h//2-15}" stroke="#475569" stroke-width="4"/>
    <line x1="{x}" y1="{y+h//2+15}" x2="{x-20}" y2="{y+h//2+15}" stroke="#475569" stroke-width="4"/>
    <line x1="{x+w}" y1="{y+h//2-15}" x2="{x+w+20}" y2="{y+h//2-15}" stroke="#475569" stroke-width="4"/>
    <line x1="{x+w}" y1="{y+h//2+15}" x2="{x+w+20}" y2="{y+h//2+15}" stroke="#475569" stroke-width="4"/>
    <text x="{x+w//2}" y="{y+h+16}" text-anchor="middle" fill="#94a3b8"
          font-size="11" font-weight="700" font-family="monospace">{eid}</text>
    <text x="{x+w//2}" y="{y+h+28}" text-anchor="middle" fill="#64748b" font-size="9">{lbl}</text>
  </g>""")

        elif "valve" in typ:
            cx = x + w//2
            cy = y + h//2
            vw = max(w, 28)
            vh = max(h, 24)
            fill_v = "#0f172a"
            equip_svg.append(f"""
  <g id="eq-{eid}" class="equipment-g clickable" data-id="{eid}" data-type="{typ}"
     onclick="toggleValvePID('{eid}')">
    <title>{eid}: {lbl}</title>
    <polygon points="{cx-vw//2},{cy-vh//2} {cx+vw//2},{cy-vh//2} {cx},{cy+vh//2}"
             fill="{fill_v}" stroke="#475569" stroke-width="2" id="vtri1-{eid}"/>
    <polygon points="{cx-vw//2},{cy+vh//2} {cx+vw//2},{cy+vh//2} {cx},{cy-vh//2}"
             fill="{fill_v}" stroke="#475569" stroke-width="2" id="vtri2-{eid}"/>
    <!-- stem -->
    <line x1="{cx}" y1="{cy-vh//2}" x2="{cx}" y2="{cy-vh//2-20}" stroke="#475569" stroke-width="2"/>
    <!-- actuator (for control valves) -->
    {'<ellipse cx="'+str(cx)+'" cy="'+str(cy-vh//2-26)+'" rx="14" ry="8" fill="#1e3a5f" stroke="#475569" stroke-width="1.5"/>' if 'control' in typ else ''}
    <text x="{cx}" y="{cy+vh//2+14}" text-anchor="middle" fill="#94a3b8"
          font-size="9" font-weight="700" font-family="monospace">{eid}</text>
  </g>""")

        else:
            # Generic equipment box
            equip_svg.append(f"""
  <g id="eq-{eid}" class="equipment-g" data-id="{eid}" data-type="{typ}"
     onclick="selectEquipment('{eid}')">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4"
          fill="#0f172a" stroke="#334155" stroke-width="2"/>
    <text x="{x+w//2}" y="{y+h//2+4}" text-anchor="middle"
          fill="#64748b" font-size="11" font-weight="700">{eid}</text>
    <text x="{x+w//2}" y="{y+h+14}" text-anchor="middle" fill="#475569" font-size="9">{lbl}</text>
  </g>""")

    # ── Build instrument bubbles SVG (ISA-5.1) ────────────────────────────────
    instr_svg = []
    for ins in instr:
        iid  = ins.get("id", "LT-000")
        tag  = ins.get("tag", iid)
        x    = ins.get("x", 300)
        y    = ins.get("y", 300)
        val  = ins.get("value")
        unit = ins.get("unit", "")
        val_str = f"{float(val):.1f}" if val is not None else "—"
        itype = ins.get("type", "LT")
        # ISA bubble: circle with dividing line
        # Top half: measured variable (first letter)
        # Bottom half: function/output (second letter)
        letter1 = itype[0] if itype else "X"
        letter2 = itype[1:] if len(itype) > 1 else ""
        # Field-mounted = circle with line through centre
        # DCS/panel = dashed border
        loop = ins.get("loop", "")

        instr_svg.append(f"""
  <g id="ins-{iid}" class="instrument-g" data-id="{iid}" data-type="{itype}"
     onclick="selectInstrument('{iid}')">
    <title>{tag}: {ins.get('service','')} | Value: {val_str} {unit}</title>
    <!-- ISA instrument bubble (field-mounted = solid circle) -->
    <circle cx="{x}" cy="{y}" r="22" fill="white" stroke="#334155" stroke-width="2"/>
    <!-- dividing line (indicates field-mounted) -->
    <line x1="{x-22}" y1="{y}" x2="{x+22}" y2="{y}" stroke="#334155" stroke-width="1.5"/>
    <!-- measured variable (top) -->
    <text x="{x}" y="{y-5}" text-anchor="middle" fill="#0f172a"
          font-size="11" font-weight="700" font-family="Arial">{letter1}</text>
    <!-- function (bottom) -->
    <text x="{x}" y="{y+13}" text-anchor="middle" fill="#0f172a"
          font-size="9" font-weight="600" font-family="Arial">{letter2}</text>
    <!-- loop number (outside, bottom-right) -->
    <text x="{x+18}" y="{y+22}" text-anchor="start" fill="#64748b"
          font-size="8" font-family="monospace">{loop}</text>
    <!-- process value display below bubble -->
    <rect x="{x-26}" y="{y+25}" width="52" height="16" rx="3"
          fill="#0f172a" stroke="#1e3a5f" stroke-width="1"/>
    <text id="ival-{iid}" x="{x}" y="{y+36}" text-anchor="middle"
          fill="#22c55e" font-size="9" font-weight="700" font-family="monospace"
          >{val_str} {unit}</text>
    <!-- signal line to process equipment -->
    <line x1="{x}" y1="{y+22}" x2="{x}" y2="{y+42}" stroke="#334155" stroke-width="1.5"
          stroke-dasharray="4 2"/>
  </g>""")

    # ── Build pipe lines SVG ───────────────────────────────────────────────────
    pipe_svg = []
    for pipe in pipes:
        pid   = pipe.get("id", "pipe")
        path  = pipe.get("path", [])
        state = pipe.get("state", "inactive")
        ptype = pipe.get("type", "process")
        size  = pipe.get("size", "2\"")
        svc   = pipe.get("service", "")
        active= state == "active"

        if len(path) < 2:
            continue

        # Build SVG polyline path
        points = " ".join(f"{pt[0]},{pt[1]}" for pt in path)
        col    = "#22c55e" if active else "#334155"
        cls    = "pipe-active" if active else "pipe-process"
        dash   = ""
        if ptype == "instrument": dash = 'stroke-dasharray="4 3"'
        elif ptype == "utility":  dash = 'stroke-dasharray="8 4"'
        elif ptype == "drain":    dash = 'stroke-dasharray="2 4"'

        # Mid-point label
        mid_idx = len(path) // 2
        mid_x   = path[mid_idx][0]
        mid_y   = path[mid_idx][1] - 8

        pipe_svg.append(f"""
  <g id="pipe-{pid}" class="pipe-g" data-id="{pid}" data-state="{state}">
    <title>{pid}: {svc} ({size})</title>
    <polyline points="{points}" fill="none" stroke="{col}" stroke-width="3"
              stroke-linecap="square" {dash} class="{cls}" id="pline-{pid}"
              marker-end="url(#{'arrow-active' if active else 'arrow'})"/>
    <!-- size label -->
    <text x="{mid_x}" y="{mid_y}" text-anchor="middle" fill="#475569"
          font-size="9" font-family="monospace" class="pipe-label">{size}</text>
  </g>""")

    # ── Build control loop symbols ─────────────────────────────────────────────
    loop_svg = []
    for loop in loops:
        lid   = loop.get("id", "LIC-101")
        ltype = loop.get("type", "LIC")
        x     = loop.get("x", 400)
        y     = loop.get("y", 150)
        sp    = loop.get("setpoint")
        sp_str = f"SP:{sp:.0f}" if sp is not None else ""
        letter1 = ltype[0] if ltype else "X"
        letter2 = ltype[1:] if len(ltype) > 1 else ""

        loop_svg.append(f"""
  <g id="loop-{lid}" class="instrument-g dcs-instrument" onclick="selectLoop('{lid}')">
    <title>{lid}: {loop.get('description','')}</title>
    <!-- DCS indicator controller (dashed border = panel-mounted) -->
    <circle cx="{x}" cy="{y}" r="24" fill="white" stroke="#334155" stroke-width="2"
            stroke-dasharray="5 3"/>
    <line x1="{x-24}" y1="{y}" x2="{x+24}" y2="{y}" stroke="#334155" stroke-width="1.5"/>
    <text x="{x}" y="{y-6}" text-anchor="middle" fill="#0f172a"
          font-size="11" font-weight="700" font-family="Arial">{letter1}</text>
    <text x="{x}" y="{y+13}" text-anchor="middle" fill="#0f172a"
          font-size="9" font-weight="700" font-family="Arial">{letter2}</text>
    <!-- setpoint display -->
    <text x="{x}" y="{y+40}" text-anchor="middle" fill="#0ea5e9"
          font-size="9" font-family="monospace">{sp_str}</text>
    <!-- loop ID -->
    <text x="{x}" y="{y+52}" text-anchor="middle" fill="#64748b"
          font-size="9" font-weight="700" font-family="monospace">{lid}</text>
  </g>""")

    # ── Build title block ───────────────────────────────────────────────────────
    title_block = f"""
  <!-- Title Block (bottom-right) -->
  <rect x="750" y="690" width="340" height="55" fill="#0a1628" stroke="#334155" stroke-width="1.5"/>
  <line x1="750" y1="710" x2="1090" y2="710" stroke="#334155" stroke-width="1"/>
  <line x1="850" y1="710" x2="850" y2="745" stroke="#334155" stroke-width="1"/>
  <line x1="950" y1="710" x2="950" y2="745" stroke="#334155" stroke-width="1"/>
  <text x="920" y="703" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="700"
        font-family="Arial">{title[:40]}</text>
  <text x="800" y="725" text-anchor="middle" fill="#64748b" font-size="8">PROJECT: {proj[:15]}</text>
  <text x="800" y="738" text-anchor="middle" fill="#64748b" font-size="8">DRAWN BY: AI Engineer</text>
  <text x="900" y="725" text-anchor="middle" fill="#64748b" font-size="8">REV: {rev}</text>
  <text x="900" y="738" text-anchor="middle" fill="#64748b" font-size="8">P&ID</text>
  <text x="1020" y="725" text-anchor="middle" fill="#64748b" font-size="8">DATE: 2024</text>
  <text x="1020" y="738" text-anchor="middle" fill="#64748b" font-size="8">SHEET: 1 OF 1</text>"""

    # Combine all SVG elements
    all_svg = (
        "".join(pipe_svg) +
        "".join(equip_svg) +
        "".join(instr_svg) +
        "".join(loop_svg) +
        title_block
    )

    sim_json = _json.dumps({
        "equipment": equip,
        "instruments": instr,
        "pipes": pipes,
    })

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — P&amp;ID</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#060d1a;color:#e2e8f0;
  height:100vh;display:flex;flex-direction:column;overflow:hidden;}}

/* HEADER */
.hdr{{background:linear-gradient(90deg,#0a1628,#0d1f35);border-bottom:2px solid #0ea5e9;
  padding:10px 24px;display:flex;align-items:center;justify-content:space-between;
  flex-shrink:0;box-shadow:0 4px 20px rgba(0,0,0,.6);}}
.hdr-title{{font-size:16px;font-weight:700;color:#0ea5e9;letter-spacing:1.5px;text-transform:uppercase;}}
.hdr-right{{display:flex;gap:16px;align-items:center;}}
.hdr-clock{{font-size:12px;color:#64748b;font-family:monospace;}}
.online-badge{{display:flex;align-items:center;gap:6px;background:rgba(34,197,94,.1);
  border:1px solid rgba(34,197,94,.3);border-radius:20px;padding:4px 10px;}}
.online-dot{{width:7px;height:7px;border-radius:50%;background:#22c55e;
  animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 4px #22c55e;}}50%{{box-shadow:0 0 14px #22c55e;}}}}

/* LAYOUT */
.body-wrap{{display:flex;flex:1;overflow:hidden;}}
.pid-area{{flex:1;background:#050c17;overflow:auto;position:relative;}}

/* SVG CANVAS */
#pidSvg{{width:100%;min-height:750px;cursor:default;}}
#pidSvg .equipment-g{{cursor:pointer;}}
#pidSvg .equipment-g:hover rect,
#pidSvg .equipment-g:hover circle,
#pidSvg .equipment-g:hover ellipse{{
  stroke:#0ea5e9!important;filter:drop-shadow(0 0 8px rgba(14,165,233,0.6));
}}
#pidSvg .instrument-g{{cursor:pointer;}}
#pidSvg .instrument-g:hover circle{{stroke:#22c55e!important;}}

/* PIPE ANIMATION */
.pipe-active{{stroke:#22c55e;stroke-dasharray:16 6;
  animation:flow 1.5s linear infinite;filter:url(#glow);}}
@keyframes flow{{to{{stroke-dashoffset:-22;}}}}
.pipe-process{{stroke:#334155;}}

/* SPINNING IMPELLER */
@keyframes spin{{to{{transform:rotate(360deg);}}}}
.spinning{{animation:spin 1.2s linear infinite;}}

/* RIGHT PANEL */
.ctrl-area{{width:280px;flex-shrink:0;background:#080f1e;
  border-left:2px solid #0f2744;display:flex;flex-direction:column;overflow-y:auto;}}
.ctrl-section{{border-bottom:1px solid #0f2040;padding:14px 16px;}}
.ctrl-title{{font-size:10px;font-weight:700;color:#475569;
  text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;}}
.info-card{{background:#0a1628;border-radius:6px;border:1px solid #0f2744;
  padding:10px;margin-bottom:8px;}}
.info-id{{font-size:12px;font-weight:700;color:#0ea5e9;font-family:monospace;}}
.info-svc{{font-size:10px;color:#64748b;margin-top:3px;}}
.info-val{{font-size:14px;font-weight:700;color:#22c55e;font-family:monospace;margin-top:4px;}}
.main-btns{{display:flex;gap:8px;flex-wrap:wrap;}}
.ctrl-btn{{padding:9px 12px;border:none;border-radius:7px;font-size:11px;font-weight:700;
  cursor:pointer;transition:all .2s;}}
.btn-start{{background:#22c55e;color:#fff;flex:1;}}
.btn-start:hover{{background:#16a34a;box-shadow:0 0 14px rgba(34,197,94,.4);}}
.btn-stop{{background:#ef4444;color:#fff;flex:1;}}
.btn-stop:hover{{background:#dc2626;box-shadow:0 0 14px rgba(239,68,68,.4);}}
.sys-dot{{width:10px;height:10px;border-radius:50%;background:#334155;
  display:inline-block;transition:all .3s;margin-right:8px;}}
.sys-dot.running{{background:#22c55e;box-shadow:0 0 10px #22c55e;}}
.status-row{{display:flex;align-items:center;margin-top:10px;}}
.status-txt{{font-size:12px;font-weight:700;color:#64748b;}}
.status-txt.running{{color:#22c55e;}}
.event-log{{background:#050c17;border-radius:5px;border:1px solid #0f2040;
  max-height:160px;overflow-y:auto;padding:6px;display:flex;flex-direction:column;gap:3px;}}
.ev-item{{font-size:9px;padding:3px 7px;border-radius:3px;border-left:3px solid;}}
.ev-info{{background:rgba(14,165,233,.08);border-color:#0ea5e9;color:#7dd3fc;}}
.ev-ok{{background:rgba(34,197,94,.08);border-color:#22c55e;color:#86efac;}}
.ev-warn{{background:rgba(245,158,11,.08);border-color:#f59e0b;color:#fcd34d;}}
.ev-crit{{background:rgba(239,68,68,.1);border-color:#ef4444;color:#fca5a5;}}
.legend-row{{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:10px;}}
.legend-line{{width:24px;height:3px;background:#334155;}}
.legend-line.active{{background:#22c55e;}}
.legend-line.dashed{{background:none;border-top:2px dashed #475569;}}
::-webkit-scrollbar{{width:4px;}}
::-webkit-scrollbar-thumb{{background:rgba(14,165,233,.3);border-radius:10px;}}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-title">&#9670; {title} — P&amp;ID</div>
  <div class="hdr-right">
    <div class="online-badge">
      <div class="online-dot"></div>
      <span style="font-size:10px;color:#22c55e;font-weight:700">LIVE</span>
    </div>
    <span class="hdr-clock" id="hdrClock">--:--:--</span>
  </div>
</div>

<div class="body-wrap">

  <!-- P&ID SVG Canvas -->
  <div class="pid-area">
    <svg id="pidSvg" viewBox="0 0 1100 750" preserveAspectRatio="xMidYMid meet">
      {ISA_SVG_DEFS}
      <!-- Grid (engineering drawing style) -->
      <rect x="0" y="0" width="1100" height="750" fill="#050c17"/>
      <!-- Border -->
      <rect x="10" y="10" width="1080" height="730" fill="none" stroke="#0f2744" stroke-width="2"/>
      <!-- Inner border -->
      <rect x="15" y="15" width="1070" height="720" fill="none" stroke="#0f2040" stroke-width="0.5"/>

      {all_svg}

    </svg>
  </div>

  <!-- Right Control Panel -->
  <div class="ctrl-area">

    <div class="ctrl-section">
      <div class="ctrl-title">System Control</div>
      <div class="main-btns">
        <button class="ctrl-btn btn-start" onclick="startProcess()">&#9654; START</button>
        <button class="ctrl-btn btn-stop"  onclick="stopProcess()">&#9632; STOP</button>
      </div>
      <div class="status-row">
        <span class="sys-dot" id="sysDot"></span>
        <span class="status-txt" id="sysTxt">STOPPED</span>
      </div>
    </div>

    <div class="ctrl-section">
      <div class="ctrl-title">Selected Equipment</div>
      <div class="info-card" id="selCard">
        <div class="info-id">—</div>
        <div class="info-svc">Click any equipment to inspect</div>
      </div>
    </div>

    <div class="ctrl-section">
      <div class="ctrl-title">Live Process Values</div>
      <div id="liveValues" style="display:flex;flex-direction:column;gap:6px;"></div>
    </div>

    <div class="ctrl-section">
      <div class="ctrl-title">Legend</div>
      <div class="legend-row"><div class="legend-line active"></div> Active flow pipe</div>
      <div class="legend-row"><div class="legend-line"></div> Process pipe</div>
      <div class="legend-row"><div class="legend-line dashed"></div> Instrument signal</div>
      <div style="margin-top:8px;font-size:9px;color:#475569">
        ISA 5.1 instrument bubbles:<br>
        Circle = Field-mounted<br>
        Dashed circle = DCS/Panel
      </div>
    </div>

    <div class="ctrl-section" style="flex:1">
      <div class="ctrl-title">Event Log</div>
      <div class="event-log" id="eventLog">
        <div class="ev-item ev-info">P&amp;ID loaded — system ready</div>
      </div>
    </div>

  </div>
</div>

<script>
// ── CLOCK ────────────────────────────────────────────────────────
function tick(){{const t=new Date().toLocaleTimeString('en-GB');const c=document.getElementById('hdrClock');if(c)c.textContent=t;}}
setInterval(tick,1000); tick();

// ── LOG ──────────────────────────────────────────────────────────
function log(cls,msg){{
  const el=document.getElementById('eventLog');if(!el)return;
  const d=document.createElement('div');d.className='ev-item ev-'+cls;
  d.textContent=new Date().toLocaleTimeString('en-GB')+'  '+msg;
  el.prepend(d);while(el.children.length>40)el.removeChild(el.lastChild);
}}

// ── SIM DATA ─────────────────────────────────────────────────────
const SIM_DATA = {sim_json};
let sysRunning = false;
let simTick = null;

// Build live value cards from instruments
function _buildLiveValues(){{
  const container = document.getElementById('liveValues');
  if (!container) return;
  SIM_DATA.instruments.forEach(ins => {{
    const div = document.createElement('div');
    div.style.cssText = 'display:flex;justify-content:space-between;align-items:center;'+
      'background:#0a1628;border-radius:5px;padding:7px 10px;border-left:3px solid #0ea5e9;';
    div.innerHTML = '<span style="font-size:10px;color:#64748b;font-family:monospace;">' +
      (ins.tag||ins.id) + '</span><span id="lv-' + ins.id + '" style="font-size:12px;'+
      'font-weight:700;color:#22c55e;font-family:monospace;">' +
      (ins.value !== undefined ? ins.value : '—') + ' ' + (ins.unit||'') + '</span>';
    container.appendChild(div);
  }});
}}
_buildLiveValues();

// ── PROCESS START / STOP ──────────────────────────────────────────
function startProcess(){{
  sysRunning = true;
  document.getElementById('sysDot').className='sys-dot running';
  document.getElementById('sysTxt').className='status-txt running';
  document.getElementById('sysTxt').textContent='RUNNING';
  // animate all pumps
  document.querySelectorAll('.equipment-g[data-type="pump"],.equipment-g[data-type="centrifugal_pump"]')
    .forEach(el => {{
      const id = el.dataset.id;
      const imp = document.getElementById('pimp-'+id);
      if(imp) imp.classList.add('spinning');
      const cas = document.getElementById('pcasing-'+id);
      if(cas) cas.setAttribute('stroke','#22c55e');
    }});
  // activate pipes
  document.querySelectorAll('.pipe-g').forEach(el => {{
    const line = el.querySelector('polyline');
    if(line){{line.classList.remove('pipe-process');line.classList.add('pipe-active');
      line.setAttribute('marker-end','url(#arrow-active)');}}
  }});
  _startSimLoop();
  log('ok','▶ Process STARTED — all equipment online');
}}

function stopProcess(){{
  sysRunning = false;
  document.getElementById('sysDot').className='sys-dot';
  document.getElementById('sysTxt').className='status-txt';
  document.getElementById('sysTxt').textContent='STOPPED';
  document.querySelectorAll('.equipment-g').forEach(el => {{
    const id = el.dataset.id;
    const imp = document.getElementById('pimp-'+id);
    if(imp) imp.classList.remove('spinning');
    const cas = document.getElementById('pcasing-'+id);
    if(cas) cas.setAttribute('stroke','#475569');
  }});
  document.querySelectorAll('.pipe-g').forEach(el => {{
    const line = el.querySelector('polyline');
    if(line){{line.classList.remove('pipe-active');line.classList.add('pipe-process');
      line.setAttribute('marker-end','url(#arrow)');}}
  }});
  _stopSimLoop();
  log('warn','■ Process STOPPED');
}}

// ── PUMP / VALVE TOGGLES ──────────────────────────────────────────
function togglePump(id){{
  if(!sysRunning){{log('warn','⚠ Start system first');return;}}
  const imp = document.getElementById('pimp-'+id);
  if(!imp) return;
  const on = !imp.classList.contains('spinning');
  if(on) imp.classList.add('spinning'); else imp.classList.remove('spinning');
  const cas = document.getElementById('pcasing-'+id);
  if(cas) cas.setAttribute('stroke', on ? '#22c55e' : '#475569');
  log(on?'ok':'warn', id + (on?' started':' stopped'));
}}

function toggleValvePID(id){{
  if(!sysRunning){{log('warn','⚠ Start system first');return;}}
  const t1 = document.getElementById('vtri1-'+id);
  const t2 = document.getElementById('vtri2-'+id);
  if(!t1) return;
  const open = t1.getAttribute('fill') === '#0f172a';
  const col = open ? '#22c55e' : '#0f172a';
  t1.setAttribute('fill',col); t2.setAttribute('fill',col);
  t1.setAttribute('stroke', open ? '#22c55e' : '#475569');
  t2.setAttribute('stroke', open ? '#22c55e' : '#475569');
  log('info', id + (open ? ' OPENED' : ' CLOSED'));
}}

// ── EQUIPMENT SELECTION ───────────────────────────────────────────
function selectEquipment(id){{
  const eq = SIM_DATA.equipment.find(e => e.id === id);
  if(!eq) return;
  const card = document.getElementById('selCard');
  if(card) card.innerHTML = `
    <div class="info-id">${{eq.id}}</div>
    <div class="info-svc">${{eq.label}} — ${{eq.service||''}}</div>
    <div style="margin-top:6px;font-size:9px;color:#475569">
      Design P: ${{eq.design_pressure||'N/A'}} | T: ${{eq.design_temp||'N/A'}}<br>
      Material: ${{eq.material||'N/A'}} | Size: ${{eq.width||'?'}}×${{eq.height||'?'}}
    </div>`;
  log('info','Selected: '+id+' — '+eq.label);
}}

function selectInstrument(id){{
  const ins = SIM_DATA.instruments.find(i => i.id === id);
  if(!ins) return;
  const card = document.getElementById('selCard');
  if(card) card.innerHTML = `
    <div class="info-id">${{ins.tag||ins.id}}</div>
    <div class="info-svc">${{ins.service||''}}</div>
    <div class="info-val" id="selVal">${{ins.value||'—'}} ${{ins.unit||''}}</div>
    <div style="margin-top:6px;font-size:9px;color:#475569">
      Hi: ${{ins.hi_alarm||'N/A'}} | Lo: ${{ins.lo_alarm||'N/A'}}
    </div>`;
  log('info','Instrument: '+id);
}}

function selectLoop(id){{
  log('info','Control loop selected: '+id);
}}

// ── SIMULATION LOOP ───────────────────────────────────────────────
function _startSimLoop(){{
  if(simTick) return;
  simTick = setInterval(_simStep, 1000);
}}
function _stopSimLoop(){{
  if(simTick){{clearInterval(simTick);simTick=null;}}
}}

function _simStep(){{
  if(!sysRunning) return;
  SIM_DATA.instruments.forEach(ins => {{
    let val = parseFloat(ins.value) || 50;
    const nMin = 20, nMax = 80;
    val = Math.max(nMin-5, Math.min(nMax+5, val + (Math.random()-0.5)*1.5));
    ins.value = parseFloat(val.toFixed(1));
    // Update ISA bubble display
    const ivel = document.getElementById('ival-'+ins.id);
    if(ivel) ivel.textContent = val.toFixed(1)+' '+(ins.unit||'');
    // Update live value panel
    const lvel = document.getElementById('lv-'+ins.id);
    if(lvel) lvel.textContent = val.toFixed(1)+' '+(ins.unit||'');
    // Alarm check
    if(ins.hi_alarm !== null && val >= ins.hi_alarm)
      log('crit','🔔 HIGH ALARM: '+ins.tag+' = '+val.toFixed(1)+' '+(ins.unit||''));
    else if(ins.lo_alarm !== null && val <= ins.lo_alarm)
      log('crit','🔔 LOW ALARM: '+ins.tag+' = '+val.toFixed(1)+' '+(ins.unit||''));
  }});
}}
</script>
</body>
</html>"""


@router.post("/generate")
async def generate_pid(req: PIDRequest, request: Request):
    """Generate an ISA-5.1 compliant P&ID using AI + deterministic HTML renderer."""
    import json

    email        = request.headers.get("X-User-Email")
    user_api_key = None

    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(status_code=403,
                detail="Token limit reached. Please upgrade to continue.")
        from backend.db import get_user_by_email
        user = await get_user_by_email(email)
        if user and user.get("api_key"):
            user_api_key = user.get("api_key")

    try:
        from backend.core.openai_client import generate_layout
        raw = generate_layout(P_AND_ID_SYSTEM_MESSAGE.replace("{requirement}", req.prompt),
                              req.prompt, api_key=user_api_key)
        pid_data = json.loads(raw)
    except Exception as e:
        print(f"[PID] AI generation failed, using fallback: {e}")
        pid_data = _fallback_pid(req.prompt)

    if email:
        from backend.token_manager import check_and_update_tokens
        used = (len(req.prompt) // 4) + (len(str(pid_data)) // 4) + 300
        check_and_update_tokens(email, used)

    system_name = req.system_name or pid_data.get("system_name", "Process System")
    html_out    = _build_pid_html(pid_data, system_name)

    return {
        "html":        html_out,
        "json":        pid_data,
        "system_name": system_name,
    }


def _fallback_pid(prompt: str) -> dict:
    """Minimal valid P&ID for when AI fails."""
    return {
        "system_name": "Process System",
        "revision": "A",
        "project": "Industrial Plant",
        "drawn_by": "AI",
        "date": "2024-01-01",
        "equipment": [
            {"id":"TK-101","type":"vertical_tank","label":"Feed Tank","service":"Raw water storage",
             "design_pressure":"ATM","design_temp":"80°C","material":"CS","x":80,"y":250,"width":100,"height":150},
            {"id":"P-101","type":"centrifugal_pump","label":"Feed Pump","service":"Transfer pump",
             "design_pressure":"6 barg","design_temp":"60°C","material":"CS","x":280,"y":360,"width":60,"height":60},
            {"id":"TK-201","type":"vertical_tank","label":"Process Tank","service":"Product storage",
             "design_pressure":"ATM","design_temp":"80°C","material":"CS","x":480,"y":250,"width":100,"height":150},
        ],
        "instruments": [
            {"id":"LT-101","tag":"LT-101","type":"LT","service":"Feed Tank level",
             "x":215,"y":290,"connected_to":"TK-101","hi_alarm":90,"lo_alarm":10,"value":55,"unit":"%","loop":"100"},
            {"id":"FT-101","tag":"FT-101","type":"FT","service":"Feed flow",
             "x":380,"y":310,"connected_to":"P-101","hi_alarm":None,"lo_alarm":None,"value":42,"unit":"m³/h","loop":"101"},
            {"id":"LT-201","tag":"LT-201","type":"LT","service":"Process Tank level",
             "x":615,"y":290,"connected_to":"TK-201","hi_alarm":90,"lo_alarm":10,"value":30,"unit":"%","loop":"200"},
        ],
        "pipes": [
            {"id":"2-P-101-50A","from":"TK-101","to":"P-101","size":'2"',"spec":"50A-CS",
             "service":"Raw water","path":[[180,380],[280,380]],"type":"process","state":"active"},
            {"id":"2-P-102-50A","from":"P-101","to":"TK-201","size":'2"',"spec":"50A-CS",
             "service":"Pumped water","path":[[340,380],[480,380]],"type":"process","state":"active"},
        ],
        "control_loops": [
            {"id":"LIC-101","tag":"LIC-101","type":"LIC","description":"Feed Tank level control",
             "x":350,"y":150,"controlled_device":"P-101","primary_element":"LT-101","setpoint":60,"loop":"100"},
        ],
    }
