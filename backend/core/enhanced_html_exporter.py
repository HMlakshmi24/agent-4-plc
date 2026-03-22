"""
Enhanced HTML Exporter — Industrial SCADA Grade v4
====================================================
Features:
- ISA-style SVG symbols for all component types
- Full physics-based process simulation (tanks fill/drain in real-time)
- Animated pipe flows (SVG stroke-dashoffset animation)
- Auto alarm triggering on threshold breach
- Live sensor value updates based on process state
- Real-time trend sparkline for key process values
- Individual equipment start/stop with process impact
- E-Stop with full process lockout
- Professional SCADA dark theme (Siemens/Rockwell style)
"""

import json
import math


# ── helpers ────────────────────────────────────────────────────────────────────

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def _state_col(state):
    s = (state or "").lower()
    if s in ("running", "open", "active", "on"):   return "#22c55e"
    if s in ("fault", "alarm", "error"):            return "#ef4444"
    if s in ("starting", "stopping", "warning"):    return "#f59e0b"
    return "#64748b"


# ── SVG SYMBOLS ────────────────────────────────────────────────────────────────

def _svg_tank(comp: dict) -> str:
    label   = _esc(comp.get("label", "Tank"))
    cid     = _esc(comp.get("_id", "t0"))
    tag     = _esc(comp.get("tag", comp.get("id", "TK")))
    val     = comp.get("value")
    lvl     = max(0.0, min(100.0, float(val) if val is not None else 50.0))
    liq_h   = int(lvl * 0.78)
    liq_y   = 12 + (78 - liq_h)
    liq_col = "#22c55e" if lvl < 75 else "#f59e0b" if lvl < 90 else "#ef4444"
    sim     = comp.get("sim", {}) or {}
    hi      = sim.get("hi_alarm", 90) or 90
    lo      = sim.get("lo_alarm", 10) or 10
    cap     = sim.get("capacity", 10000) or 10000

    return f"""
<div class="sym-wrap tank-wrap" id="sym-{cid}" data-type="tank" data-id="{cid}"
     data-level="{lvl:.1f}" data-capacity="{cap}"
     data-hi="{hi}" data-lo="{lo}"
     data-fill-rate="{sim.get('fill_rate', 0) or 0}"
     data-drain-rate="{sim.get('drain_rate', 0) or 0}">
  <svg width="96" height="120" viewBox="0 0 96 120">
    <!-- shell -->
    <rect x="8" y="12" width="80" height="90" rx="4" fill="#0f172a" stroke="#334155" stroke-width="2"/>
    <!-- liquid fill -->
    <rect id="liq-{cid}" x="10" y="{liq_y}" width="76" height="{liq_h}" rx="2"
          fill="{liq_col}" opacity="0.82" class="tank-liq"/>
    <!-- top cap -->
    <ellipse cx="48" cy="12" rx="40" ry="7" fill="#1e293b" stroke="#334155" stroke-width="2"/>
    <!-- nozzle top -->
    <rect x="43" y="0" width="10" height="12" fill="#475569" rx="1"/>
    <!-- nozzle bottom -->
    <rect x="43" y="102" width="10" height="10" fill="#475569" rx="1"/>
    <!-- level scale -->
    <line x1="8" y1="34" x2="16" y2="34" stroke="#334155" stroke-width="1.2"/>
    <line x1="8" y1="57" x2="16" y2="57" stroke="#334155" stroke-width="1.2"/>
    <line x1="8" y1="80" x2="16" y2="80" stroke="#334155" stroke-width="1.2"/>
    <text x="6" y="37"  text-anchor="end" fill="#475569" font-size="8">75</text>
    <text x="6" y="60"  text-anchor="end" fill="#475569" font-size="8">50</text>
    <text x="6" y="83"  text-anchor="end" fill="#475569" font-size="8">25</text>
    <!-- level % text -->
    <text id="lvltxt-{cid}" x="48" y="62" text-anchor="middle"
          fill="white" font-size="15" font-weight="700">{lvl:.0f}%</text>
    <!-- hi/lo markers -->
    <line x1="82" y1="{12 + int((1 - hi/100)*78)}" x2="90" y2="{12 + int((1 - hi/100)*78)}"
          stroke="#ef4444" stroke-width="1.5" stroke-dasharray="3 2"/>
    <line x1="82" y1="{12 + int((1 - lo/100)*78)}" x2="90" y2="{12 + int((1 - lo/100)*78)}"
          stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="3 2"/>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
  <div class="comp-reading" id="reading-{cid}">
    <span class="rdg-val" id="rdgval-{cid}">{lvl:.1f}</span>
    <span class="rdg-unit">%</span>
  </div>
</div>"""


def _svg_pump(comp: dict) -> str:
    label   = _esc(comp.get("label", "Pump"))
    cid     = _esc(comp.get("_id", "p0"))
    tag     = _esc(comp.get("tag", comp.get("id", "P")))
    state   = comp.get("state", "stopped")
    running = state == "running"
    col     = "#22c55e" if running else "#64748b"
    spin    = "spinning" if running else ""
    status  = "RUNNING" if running else "STOPPED"
    sim     = comp.get("sim", {}) or {}
    fr      = sim.get("fill_rate", 30) or 30

    return f"""
<div class="sym-wrap clickable" id="sym-{cid}" data-type="pump" data-id="{cid}"
     data-state="{state}" data-fill-rate="{fr}" onclick="toggleEquipment(this)">
  <svg width="84" height="95" viewBox="0 0 84 95">
    <!-- casing outer ring -->
    <circle cx="42" cy="44" r="36" fill="#0f172a" stroke="{col}" stroke-width="2.5" id="pring-{cid}"/>
    <!-- volute -->
    <path d="M42,44 Q55,28 66,44 Q55,60 42,44" fill="{col}" opacity="0.15"/>
    <!-- dashed inner ring (spins) -->
    <circle cx="42" cy="44" r="22" fill="none" stroke="{col}" stroke-width="2"
            stroke-dasharray="9 5" id="pdash-{cid}" class="{spin}"/>
    <!-- impeller blades -->
    <g id="pimp-{cid}" class="{spin}" style="transform-origin:42px 44px">
      <line x1="42" y1="44" x2="42" y2="25" stroke="{col}" stroke-width="3" stroke-linecap="round"/>
      <line x1="42" y1="44" x2="57" y2="56" stroke="{col}" stroke-width="3" stroke-linecap="round"/>
      <line x1="42" y1="44" x2="27" y2="56" stroke="{col}" stroke-width="3" stroke-linecap="round"/>
    </g>
    <!-- hub -->
    <circle cx="42" cy="44" r="7" fill="{col}" id="phub-{cid}"/>
    <!-- inlet stub left -->
    <rect x="0" y="39" width="10" height="10" fill="#334155" rx="1"/>
    <!-- outlet stub right -->
    <rect x="74" y="39" width="10" height="10" fill="#334155" rx="1"/>
    <!-- rpm label -->
    <text x="42" y="88" text-anchor="middle" fill="{col}" font-size="9" font-weight="700"
          id="ptxt-{cid}">{status}</text>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
  <div class="comp-reading"><span class="rdg-val" id="rdgval-{cid}">{fr}</span><span class="rdg-unit">L/s</span></div>
</div>"""


def _svg_motor(comp: dict) -> str:
    label   = _esc(comp.get("label", "Motor"))
    cid     = _esc(comp.get("_id", "m0"))
    tag     = _esc(comp.get("tag", comp.get("id", "M")))
    state   = comp.get("state", "stopped")
    running = state == "running"
    col     = "#22c55e" if running else "#64748b"
    spin    = "spinning" if running else ""
    status  = "RUNNING" if running else "STOPPED"
    sim     = comp.get("sim", {}) or {}
    kw      = sim.get("fill_rate", 7.5) or 7.5

    return f"""
<div class="sym-wrap clickable" id="sym-{cid}" data-type="motor" data-id="{cid}"
     data-state="{state}" data-fill-rate="{kw}" onclick="toggleEquipment(this)">
  <svg width="96" height="82" viewBox="0 0 96 82">
    <!-- body -->
    <rect x="6" y="16" width="66" height="44" rx="6" fill="#0f172a" stroke="{col}" stroke-width="2.5"
          id="mrect-{cid}"/>
    <!-- cooling fins -->
    <line x1="20" y1="16" x2="20" y2="60" stroke="{col}" stroke-width="1" opacity="0.35"/>
    <line x1="32" y1="16" x2="32" y2="60" stroke="{col}" stroke-width="1" opacity="0.35"/>
    <line x1="44" y1="16" x2="44" y2="60" stroke="{col}" stroke-width="1" opacity="0.35"/>
    <line x1="56" y1="16" x2="56" y2="60" stroke="{col}" stroke-width="1" opacity="0.35"/>
    <!-- M symbol -->
    <text x="39" y="46" text-anchor="middle" fill="{col}" font-size="24" font-weight="800">M</text>
    <!-- shaft -->
    <rect x="72" y="33" width="20" height="10" fill="#334155" rx="2"/>
    <!-- spin ring -->
    <circle cx="39" cy="38" r="30" fill="none" stroke="{col}" stroke-width="1.5"
            stroke-dasharray="8 5" id="mspin-{cid}" class="{spin}" style="transform-origin:39px 38px"/>
    <!-- status -->
    <text x="39" y="75" text-anchor="middle" fill="{col}" font-size="9" font-weight="700"
          id="mtxt-{cid}">{status}</text>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
  <div class="comp-reading"><span class="rdg-val" id="rdgval-{cid}">{kw}</span><span class="rdg-unit">kW</span></div>
</div>"""


def _svg_valve(comp: dict) -> str:
    label   = _esc(comp.get("label", "Valve"))
    cid     = _esc(comp.get("_id", "v0"))
    tag     = _esc(comp.get("tag", comp.get("id", "V")))
    state   = comp.get("state", "closed")
    opened  = state in ("open", "active", "running")
    col     = "#22c55e" if opened else "#ef4444"
    fill_b  = "#22c55e" if opened else "#0f172a"
    status  = "OPEN" if opened else "CLOSED"
    val     = comp.get("value") or (100 if opened else 0)

    return f"""
<div class="sym-wrap clickable" id="sym-{cid}" data-type="valve" data-id="{cid}"
     data-state="{state}" data-position="{val}" onclick="toggleValve(this)">
  <svg width="72" height="88" viewBox="0 0 72 88">
    <!-- upper triangle (ISA gate valve symbol) -->
    <polygon points="10,10 62,10 36,46" fill="{fill_b}" stroke="{col}" stroke-width="2.5"
             id="vtri1-{cid}"/>
    <!-- lower triangle -->
    <polygon points="10,68 62,68 36,32" fill="{fill_b}" stroke="{col}" stroke-width="2.5"
             id="vtri2-{cid}"/>
    <!-- stem -->
    <line x1="36" y1="0" x2="36" y2="10" stroke="#64748b" stroke-width="3"/>
    <!-- handwheel -->
    <ellipse cx="36" cy="0" rx="14" ry="5" fill="none" stroke="#64748b" stroke-width="2"/>
    <line x1="22" y1="0" x2="50" y2="0" stroke="#64748b" stroke-width="2"/>
    <!-- centre position dot -->
    <circle cx="36" cy="39" r="5" fill="{col}" id="vdot-{cid}"/>
    <!-- position bar -->
    <rect x="10" y="74" width="{int(val * 52/100)}" height="6" rx="3" fill="{col}" opacity="0.7" id="vbar-{cid}"/>
    <rect x="10" y="74" width="52" height="6" rx="3" fill="none" stroke="{col}" stroke-width="1.2" opacity="0.4"/>
    <!-- status -->
    <text x="36" y="86" text-anchor="middle" fill="{col}" font-size="9" font-weight="700"
          id="vtxt-{cid}">{status}</text>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
  <div class="comp-reading"><span class="rdg-val" id="rdgval-{cid}">{val}</span><span class="rdg-unit">%</span></div>
</div>"""


def _svg_fan(comp: dict) -> str:
    label   = _esc(comp.get("label", "Fan"))
    cid     = _esc(comp.get("_id", "f0"))
    tag     = _esc(comp.get("tag", comp.get("id", "F")))
    state   = comp.get("state", "stopped")
    running = state == "running"
    col     = "#22c55e" if running else "#64748b"
    spin    = "spinning" if running else ""
    status  = "RUNNING" if running else "STOPPED"

    return f"""
<div class="sym-wrap clickable" id="sym-{cid}" data-type="fan" data-id="{cid}"
     data-state="{state}" onclick="toggleEquipment(this)">
  <svg width="82" height="95" viewBox="0 0 82 95">
    <circle cx="41" cy="43" r="36" fill="#0f172a" stroke="{col}" stroke-width="2.5" id="fring-{cid}"/>
    <g id="fblades-{cid}" class="{spin}" style="transform-origin:41px 43px">
      <ellipse cx="41" cy="22" rx="8" ry="19" fill="{col}" opacity="0.75"/>
      <ellipse cx="41" cy="64" rx="8" ry="19" fill="{col}" opacity="0.75"/>
      <ellipse cx="20" cy="43" rx="19" ry="8" fill="{col}" opacity="0.75"/>
      <ellipse cx="62" cy="43" rx="19" ry="8" fill="{col}" opacity="0.75"/>
    </g>
    <circle cx="41" cy="43" r="7" fill="{col}" id="fhub-{cid}"/>
    <text x="41" y="88" text-anchor="middle" fill="{col}" font-size="9" font-weight="700"
          id="ftxt-{cid}">{status}</text>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
</div>"""


def _svg_sensor(comp: dict) -> str:
    label    = _esc(comp.get("label", "Sensor"))
    cid      = _esc(comp.get("_id", "s0"))
    ctype    = comp.get("type", "sensor")
    tag_map  = {
        "sensor_level": "LT", "sensor_temp": "TT", "sensor_pressure": "PT",
        "sensor_flow": "FT", "sensor": "ST"
    }
    isa_tag  = tag_map.get(ctype, "ST")
    disp_tag = _esc(comp.get("tag", comp.get("id", isa_tag)))
    val      = comp.get("value")
    unit     = comp.get("unit") or ""
    val_str  = f"{float(val):.1f}" if val is not None else "—"
    sim      = comp.get("sim", {}) or {}
    hi       = sim.get("hi_alarm")
    lo       = sim.get("lo_alarm")

    return f"""
<div class="sym-wrap" id="sym-{cid}" data-type="sensor" data-subtype="{ctype}" data-id="{cid}"
     data-hi="{hi or ''}" data-lo="{lo or ''}">
  <svg width="64" height="78" viewBox="0 0 64 78">
    <!-- ISA instrument bubble (field-mounted: solid border) -->
    <circle cx="32" cy="30" r="26" fill="white" stroke="#3b82f6" stroke-width="2.5"/>
    <!-- dividing line for field-mounted -->
    <line x1="6" y1="30" x2="58" y2="30" stroke="#3b82f6" stroke-width="1.5"/>
    <!-- ISA tag top (first letter = measured variable) -->
    <text x="32" y="25" text-anchor="middle" fill="#1e40af" font-size="11" font-weight="700"
          id="sisa-{cid}">{isa_tag}</text>
    <!-- value bottom -->
    <text x="32" y="41" text-anchor="middle" fill="#1e40af" font-size="10" font-weight="700"
          id="stxt-{cid}">{val_str}</text>
    <!-- signal line down to process -->
    <line x1="32" y1="56" x2="32" y2="70" stroke="#3b82f6" stroke-width="2"/>
    <circle cx="32" cy="72" r="3" fill="#3b82f6"/>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{disp_tag}</div>
  <div class="comp-reading">
    <span class="rdg-val" id="rdgval-{cid}">{val_str}</span>
    <span class="rdg-unit">{_esc(unit)}</span>
  </div>
</div>"""


def _svg_gauge(comp: dict) -> str:
    label   = _esc(comp.get("label", "Gauge"))
    cid     = _esc(comp.get("_id", "g0"))
    tag     = _esc(comp.get("tag", comp.get("id", "G")))
    val     = float(comp.get("value") or 50)
    val     = max(0.0, min(100.0, val))
    unit    = _esc(comp.get("unit") or "")
    # needle angle: -135° to +135° over 0-100%
    angle   = -135 + val * 2.7
    rad     = math.radians(angle)
    nx      = 44 + 30 * math.cos(rad)
    ny      = 48 + 30 * math.sin(rad)
    col     = "#22c55e" if val < 70 else "#f59e0b" if val < 90 else "#ef4444"

    return f"""
<div class="sym-wrap" id="sym-{cid}" data-type="gauge" data-id="{cid}">
  <svg width="88" height="68" viewBox="0 0 88 68">
    <!-- arc background -->
    <path d="M 8,52 A 36,36 0 1,1 80,52" fill="none" stroke="#1e293b" stroke-width="8" stroke-linecap="round"/>
    <!-- arc green zone 0-70% -->
    <path d="M 8,52 A 36,36 0 0,1 {44 + 36*math.cos(math.radians(-135+70*2.7)):.1f},{48 + 36*math.sin(math.radians(-135+70*2.7)):.1f}"
          fill="none" stroke="#22c55e" stroke-width="5" stroke-linecap="round" opacity="0.3"/>
    <!-- arc red zone 90-100% -->
    <path d="M {44 + 36*math.cos(math.radians(-135+90*2.7)):.1f},{48 + 36*math.sin(math.radians(-135+90*2.7)):.1f}
             A 36,36 0 0,1 80,52"
          fill="none" stroke="#ef4444" stroke-width="5" stroke-linecap="round" opacity="0.4"/>
    <!-- arc fill to value -->
    <path d="M 8,52 A 36,36 0 0,1 {nx:.1f},{ny:.1f}" fill="none" stroke="{col}" stroke-width="6"
          stroke-linecap="round" id="garc-{cid}"/>
    <!-- pivot -->
    <circle cx="44" cy="48" r="5" fill="#94a3b8"/>
    <!-- needle -->
    <line x1="44" y1="48" x2="{nx:.1f}" y2="{ny:.1f}" stroke="white" stroke-width="2.5"
          stroke-linecap="round" id="gneedle-{cid}"/>
    <!-- value text -->
    <text x="44" y="36" text-anchor="middle" fill="{col}" font-size="13" font-weight="800"
          id="gtxt-{cid}">{val:.0f}</text>
  </svg>
  <div class="comp-name">{label}</div>
  <div class="comp-tag">{tag}</div>
  <div class="comp-reading"><span class="rdg-val" id="rdgval-{cid}">{val:.1f}</span><span class="rdg-unit">{unit}</span></div>
</div>"""


def _svg_alarm(comp: dict) -> str:
    label   = _esc(comp.get("label", "Alarm"))
    cid     = _esc(comp.get("_id", "a0"))
    tag     = _esc(comp.get("tag", comp.get("id", "ALM")))
    state   = comp.get("state", "inactive")
    active  = state == "active"
    col     = "#ef4444" if active else "#64748b"
    pulse   = "pulsing" if active else ""
    status  = "ACTIVE" if active else "NORMAL"

    return f"""
<div class="sym-wrap alarm-sym {'active-alarm' if active else ''}" id="sym-{cid}"
     data-type="alarm" data-id="{cid}" data-state="{state}" onclick="acknowledgeAlarm(this)">
  <svg width="62" height="68" viewBox="0 0 62 68">
    <!-- alarm triangle ISA symbol -->
    <polygon points="31,4 58,54 4,54" fill="#0f172a" stroke="{col}" stroke-width="2.5"
             id="atri-{cid}" class="{pulse}"/>
    <!-- ! symbol -->
    <text x="31" y="44" text-anchor="middle" fill="{col}" font-size="20" font-weight="900"
          id="aexcl-{cid}">!</text>
    <!-- status -->
    <text x="31" y="64" text-anchor="middle" fill="{col}" font-size="8" font-weight="700"
          id="atxt-{cid}">{status}</text>
  </svg>
  <div class="comp-name" style="font-size:10px;max-width:90px;text-align:center">{label}</div>
  <div class="comp-tag">{tag}</div>
</div>"""


def _svg_button(comp: dict) -> str:
    label   = comp.get("label", "Button")
    cid     = _esc(comp.get("_id", "b0"))
    lower   = label.lower()
    is_estop  = "emergency" in lower or "e-stop" in lower or "estop" in lower
    is_start  = "start" in lower and not is_estop
    is_stop   = "stop" in lower and not is_estop
    is_reset  = "reset" in lower or "acknowledge" in lower

    if is_estop:
        return f"""
<div class="btn-wrap" id="sym-{cid}">
  <button class="ctrl-btn btn-estop" id="eStopBtn"
    onclick="this.classList.contains('fired') ? releaseEStop() : (triggerEStop(), this.classList.add('fired'))"
    title="Emergency Stop — Click again to release">&#9888; E-STOP</button>
  <div class="comp-tag">SAFETY</div>
</div>"""
    elif is_start:
        return f"""
<div class="btn-wrap" id="sym-{cid}">
  <button class="ctrl-btn btn-start" onclick="startSystem()">&#9654; START</button>
  <div class="comp-tag">CMD</div>
</div>"""
    elif is_stop:
        return f"""
<div class="btn-wrap" id="sym-{cid}">
  <button class="ctrl-btn btn-stop" onclick="stopSystem()">&#9632; STOP</button>
  <div class="comp-tag">CMD</div>
</div>"""
    elif is_reset:
        return f"""
<div class="btn-wrap" id="sym-{cid}">
  <button class="ctrl-btn btn-reset" onclick="resetAlarms()">&#8635; RESET ALARMS</button>
  <div class="comp-tag">CMD</div>
</div>"""
    else:
        return f"""
<div class="btn-wrap" id="sym-{cid}">
  <button class="ctrl-btn btn-normal" onclick="handleBtn(this,'{cid}')">{_esc(label)}</button>
  <div class="comp-tag">CMD</div>
</div>"""


def _svg_slider(comp: dict) -> str:
    label   = _esc(comp.get("label", "Setpoint"))
    cid     = _esc(comp.get("_id", "sl0"))
    val     = int(float(comp.get("value") or 50))
    unit    = _esc(comp.get("unit") or "%")

    return f"""
<div class="slider-block" id="sym-{cid}">
  <div class="slider-label">{label}</div>
  <div class="slider-row">
    <input type="range" min="0" max="100" value="{val}" class="comp-slider"
           oninput="updateSetpoint(this,'{cid}')" id="sldr-{cid}"/>
    <span class="slider-val" id="sval-{cid}">{val}</span>
    <span class="slider-unit">{unit}</span>
  </div>
</div>"""


# ── CONNECTION PIPES (SVG overlay layer) ──────────────────────────────────────

def _build_pipe_svg(connections: list) -> str:
    """Renders animated pipe flow lines in an SVG overlay."""
    if not connections:
        return ""
    pipes = []
    for i, conn in enumerate(connections):
        cid   = f"pipe{i}"
        label = _esc(conn.get("label", ""))
        pipes.append(f"""
  <line id="{cid}" x1="0" y1="0" x2="0" y2="0"
        class="pipe-line pipe-inactive" data-from="{_esc(conn.get('from',''))}"
        data-to="{_esc(conn.get('to',''))}" data-active-when="{_esc(conn.get('active_when','running'))}"/>""")
    return f"""
<svg id="pipeSvg" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2">
  <defs>
    <marker id="arrowEnd" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <polygon points="0,0 8,3 0,6" fill="#22c55e" opacity="0.8"/>
    </marker>
  </defs>
  {"".join(pipes)}
</svg>"""


# ── MAIN RENDER ────────────────────────────────────────────────────────────────

def generate_enhanced_html_from_json(layout: dict) -> str:
    return _render(layout)


def generate_pid_html_from_json(layout: dict) -> str:
    return _render(layout)


def _render(layout: dict) -> str:
    system_name  = layout.get("system_name", "Industrial Process")
    components   = layout.get("components", [])
    connections  = layout.get("connections", [])
    alarms_def   = layout.get("alarms", [])
    proc_desc    = layout.get("process_description", "")
    theme        = layout.get("theme", "default")

    # Theme accent colors
    theme_colors = {
        "water":    ("#0ea5e9", "#0284c7"),
        "motor":    ("#f59e0b", "#d97706"),
        "hvac":     ("#10b981", "#059669"),
        "chemical": ("#a855f7", "#9333ea"),
        "food":     ("#84cc16", "#65a30d"),
        "default":  ("#3b82f6", "#2563eb"),
    }
    accent, accent_dark = theme_colors.get(theme, theme_colors["default"])

    # Assign stable IDs
    for i, comp in enumerate(components):
        ct = comp.get("type", "")
        comp_id = comp.get("id") or comp.get("tag") or f"c{i}_{ct}"
        comp["_id"] = comp_id.replace(" ", "_").replace("-", "_")

    # Categorize
    tanks, machines, valves, sensors, gauges, alarms_comps, buttons, sliders = (
        [], [], [], [], [], [], [], []
    )

    for comp in components:
        ct = comp.get("type", "")
        if ct == "tank":                             tanks.append(comp)
        elif ct in ("pump", "motor", "fan",
                    "compressor", "conveyor"):       machines.append(comp)
        elif ct == "valve":                          valves.append(comp)
        elif ct.startswith("sensor") or ct == "sensor": sensors.append(comp)
        elif ct == "gauge":                          gauges.append(comp)
        elif ct == "alarm":                          alarms_comps.append(comp)
        elif ct == "button":                         buttons.append(comp)
        elif ct == "slider":                         sliders.append(comp)
        else:                                        gauges.append(comp)

    # ── Build process canvas HTML ──────────────────────────────────────────────
    def section(label, items_html):
        return f'<div class="section-label">{label}</div><div class="sym-row">{items_html}</div>'

    canvas_html = _build_pipe_svg(connections)

    if tanks:
        canvas_html += section("Storage & Vessels",
            "".join(_svg_tank(c) for c in tanks))
    if machines:
        canvas_html += section("Rotating Equipment",
            "".join(
                _svg_pump(c) if c["type"] == "pump" else
                _svg_fan(c)  if c["type"] == "fan"  else
                _svg_motor(c)
                for c in machines))
    if valves:
        canvas_html += section("Final Control Elements",
            "".join(_svg_valve(c) for c in valves))
    if sensors:
        canvas_html += section("Field Instruments",
            "".join(_svg_sensor(c) for c in sensors))
    if gauges:
        canvas_html += section("Process Indicators",
            "".join(_svg_gauge(c) for c in gauges))

    # ── Build right control panel HTML ────────────────────────────────────────
    ctrl_html = f"""
<div class="ctrl-section">
  <div class="ctrl-title">System Control</div>
  <div class="main-btns">
    <button class="ctrl-btn btn-start" onclick="startSystem()">&#9654; START</button>
    <button class="ctrl-btn btn-stop"  onclick="stopSystem()">&#9632; STOP</button>
    <button class="ctrl-btn btn-estop" id="eStopBtn"
      onclick="this.classList.contains('fired') ? releaseEStop() : (triggerEStop(), this.classList.add('fired'))"
      title="E-Stop — click again to release">&#9888;</button>
  </div>
  <div class="sys-status-row">
    <span class="sys-dot" id="sysDot"></span>
    <span class="sys-txt" id="sysTxt">STOPPED</span>
    <span class="sys-clock" id="sysClock"></span>
  </div>
</div>"""

    # Alarm panel (overview sidebar)
    if alarms_comps:
        ctrl_html += '<div class="ctrl-section"><div class="ctrl-title">Alarms &amp; Events</div>'
        ctrl_html += '<div class="alarm-grid">'
        ctrl_html += "".join(_svg_alarm(c) for c in alarms_comps)
        ctrl_html += '</div>'
        ctrl_html += '<button class="ctrl-btn btn-reset" style="margin-top:10px;width:100%" onclick="resetAlarms()">&#8635; ACK ALL ALARMS</button>'
        ctrl_html += '</div>'

    # Custom buttons
    user_buttons = [b for b in buttons if not any(
        x in (b.get("label","")).lower()
        for x in ("start","stop","emergency","e-stop","estop","reset"))]
    if user_buttons:
        ctrl_html += '<div class="ctrl-section"><div class="ctrl-title">Commands</div>'
        ctrl_html += "".join(_svg_button(c) for c in user_buttons)
        ctrl_html += '</div>'

    # Event log
    ctrl_html += """
<div class="ctrl-section" style="flex:1">
  <div class="ctrl-title">Event Log</div>
  <div class="event-log" id="eventLog">
    <div class="ev-item ev-info">System initialized — ready</div>
  </div>
</div>"""

    # ── Build Trends tab — one card per tracked component ─────────────────────
    trend_tracked = tanks + sensors + gauges
    trend_cards_html = ""
    for comp in trend_tracked:
        cid   = comp["_id"]
        label = _esc(comp.get("label", cid))
        tag   = _esc(comp.get("tag", comp.get("id", cid)))
        unit  = _esc(comp.get("unit", "%"))
        trend_cards_html += f"""
<div class="trend-card">
  <div class="trend-hdr">
    <span class="trend-tag">{tag}</span>
    <span class="trend-name">{label}</span>
    <span class="trend-live" id="tlive-{cid}">—</span>
    <span class="trend-unit">{unit}</span>
  </div>
  <canvas id="tcanv-{cid}" class="trend-canvas" width="320" height="72"></canvas>
  <div class="trend-footer">
    <span class="trend-stat" id="tmin-{cid}">min —</span>
    <span class="trend-stat" id="tavg-{cid}">avg —</span>
    <span class="trend-stat" id="tmax-{cid}">max —</span>
  </div>
</div>"""
    if not trend_cards_html:
        trend_cards_html = '<div class="no-data">No trend data — add tanks or sensors to the system.</div>'

    # ── Build Settings tab ────────────────────────────────────────────────────
    settings_html = '<div class="settings-section"><div class="settings-title">Setpoints &amp; Control Parameters</div>'
    if sliders:
        settings_html += "".join(_svg_slider(c) for c in sliders)
    else:
        settings_html += '<div class="no-data">No configurable setpoints defined for this system.</div>'
    settings_html += '</div>'
    if proc_desc:
        settings_html += f'<div class="settings-section"><div class="settings-title">Process Description</div><div class="proc-desc-full">{_esc(proc_desc)}</div></div>'
    settings_html += f"""<div class="settings-section">
  <div class="settings-title">System Information</div>
  <div class="sysinfo-grid">
    <div class="sysinfo-row"><span>System Name</span><span>{_esc(system_name)}</span></div>
    <div class="sysinfo-row"><span>Theme</span><span>{_esc(theme)}</span></div>
    <div class="sysinfo-row"><span>Components</span><span>{len(components)}</span></div>
    <div class="sysinfo-row"><span>Connections</span><span>{len(connections)}</span></div>
  </div>
  <button class="ctrl-btn btn-normal" style="margin-top:14px;width:100%" onclick="window.print()">&#128438; Print / Export PDF</button>
</div>"""

    # ── Build simulation data for JS ───────────────────────────────────────────
    sim_data = {}
    for comp in components:
        cid  = comp["_id"]
        ct   = comp.get("type", "")
        sim  = comp.get("sim", {}) or {}
        sim_data[cid] = {
            "type":       ct,
            "state":      comp.get("state", "stopped"),
            "value":      comp.get("value"),
            "unit":       comp.get("unit", ""),
            "fill_rate":  sim.get("fill_rate", 0) or 0,
            "drain_rate": sim.get("drain_rate", 0) or 0,
            "capacity":   sim.get("capacity", 10000) or 10000,
            "hi_alarm":   sim.get("hi_alarm"),
            "lo_alarm":   sim.get("lo_alarm"),
            "hi_hi":      sim.get("hi_hi_alarm"),
            "lo_lo":      sim.get("lo_lo_alarm"),
            "normal_min": sim.get("normal_min"),
            "normal_max": sim.get("normal_max"),
        }

    # IDs of trend-tracked components (for JS history push)
    trend_ids_json = json.dumps([c["_id"] for c in trend_tracked])
    conn_data      = json.dumps(connections)
    sim_json       = json.dumps(sim_data)
    title          = f"{_esc(system_name)}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
/* ── RESET ──────────────────────────────────────── */
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#060d1a;color:#e2e8f0;
  height:100vh;display:flex;flex-direction:column;overflow:hidden;}}

/* ── HEADER ─────────────────────────────────────── */
.hdr{{background:linear-gradient(90deg,#0a1628,#0d1f35);
  border-bottom:2px solid {accent};padding:10px 24px;
  display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 4px 20px rgba(0,0,0,.6);flex-shrink:0;}}
.hdr-title{{font-size:17px;font-weight:700;color:{accent};
  letter-spacing:1.5px;text-transform:uppercase;}}
.hdr-right{{display:flex;align-items:center;gap:14px;}}
.online-badge{{display:flex;align-items:center;gap:6px;
  background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);
  border-radius:20px;padding:4px 12px;}}
.online-dot{{width:8px;height:8px;border-radius:50%;background:#22c55e;
  box-shadow:0 0 8px #22c55e;animation:pulse-dot 2s infinite;}}
@keyframes pulse-dot{{0%,100%{{box-shadow:0 0 4px #22c55e;}}50%{{box-shadow:0 0 14px #22c55e;}}}}
.hdr-clock{{font-size:13px;color:#94a3b8;font-family:monospace;}}

/* ── TAB BAR ─────────────────────────────────────── */
.tab-bar{{
  display:flex;background:#080f1e;border-bottom:2px solid #1e3a5f;
  flex-shrink:0;padding:0 16px;gap:2px;
}}
.tab-btn{{
  padding:9px 20px;font-size:12px;font-weight:700;cursor:pointer;
  background:transparent;border:none;color:#475569;
  border-bottom:3px solid transparent;transition:all .2s;
  display:flex;align-items:center;gap:7px;letter-spacing:.5px;
  text-transform:uppercase;
}}
.tab-btn:hover{{color:#94a3b8;}}
.tab-btn.active{{color:{accent};border-bottom-color:{accent};}}
.tab-badge{{
  background:#ef4444;color:#fff;border-radius:10px;
  padding:1px 6px;font-size:9px;font-weight:900;
  display:none;min-width:16px;text-align:center;
}}
.tab-badge.visible{{display:inline-block;}}

/* ── TAB CONTENT ─────────────────────────────────── */
.tab-content{{display:none;flex:1;overflow:hidden;}}
.tab-content.active{{display:flex;flex-direction:column;}}
#tab-overview{{flex-direction:row;}}

/* ── OVERVIEW LAYOUT ─────────────────────────────── */
.process-area{{
  flex:1;background:#080f1e;border-right:2px solid #1e3a5f;
  padding:18px 22px;overflow-y:auto;position:relative;
}}
.ctrl-area{{
  width:290px;flex-shrink:0;background:#0a1628;
  display:flex;flex-direction:column;overflow-y:auto;
}}

/* ── SECTION LABELS ──────────────────────────────── */
.section-label{{
  font-size:10px;font-weight:700;color:#475569;
  text-transform:uppercase;letter-spacing:2px;
  border-left:3px solid {accent};padding-left:10px;
  margin:16px 0 10px;
}}
.sym-row{{
  display:flex;flex-wrap:wrap;gap:20px;
  padding:6px 0 14px;border-bottom:1px solid #0f2040;
}}

/* ── SYMBOL CARDS ────────────────────────────────── */
.sym-wrap{{
  display:flex;flex-direction:column;align-items:center;gap:5px;
  padding:10px 12px;border-radius:10px;
  background:rgba(15,32,64,.5);border:1px solid rgba(59,130,246,.12);
  transition:border-color .2s,background .2s,box-shadow .2s;
  min-width:82px;
}}
.sym-wrap.clickable{{cursor:pointer;}}
.sym-wrap.clickable:hover{{
  border-color:{accent};background:rgba(59,130,246,.08);
  box-shadow:0 0 12px rgba(59,130,246,.2);
}}
.sym-wrap.active-state{{
  border-color:#22c55e!important;background:rgba(34,197,94,.07)!important;
  box-shadow:0 0 14px rgba(34,197,94,.25)!important;
}}
.sym-wrap.alarm-state{{
  border-color:#ef4444!important;background:rgba(239,68,68,.07)!important;
  animation:alarm-border 1s ease-in-out infinite;
}}
@keyframes alarm-border{{
  0%,100%{{box-shadow:0 0 8px rgba(239,68,68,.3);}}
  50%{{box-shadow:0 0 20px rgba(239,68,68,.7);}}
}}
.active-alarm{{border-color:#ef4444!important;}}
.comp-name{{font-size:10px;font-weight:700;color:#cbd5e1;text-align:center;max-width:110px;}}
.comp-tag{{font-size:8px;color:#475569;text-transform:uppercase;letter-spacing:.5px;}}
.comp-reading{{display:flex;align-items:baseline;gap:3px;margin-top:2px;}}
.rdg-val{{font-size:13px;font-weight:700;color:{accent};font-family:monospace;}}
.rdg-unit{{font-size:9px;color:#64748b;}}

/* ── TANK LIQUID ─────────────────────────────────── */
.tank-liq{{transition:y 0.8s ease,height 0.8s ease,fill 0.5s;}}

/* ── CONTROL PANEL ───────────────────────────────── */
.ctrl-section{{border-bottom:1px solid #0f2040;padding:16px 18px;}}
.ctrl-title{{font-size:10px;font-weight:700;color:#475569;
  text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;}}
.main-btns{{display:flex;gap:8px;}}
.ctrl-btn{{
  padding:10px 14px;border:none;border-radius:8px;
  font-size:12px;font-weight:700;cursor:pointer;
  font-family:'Segoe UI',Arial,sans-serif;transition:all .2s;
}}
.btn-start{{background:#22c55e;color:#fff;flex:1;}}
.btn-start:hover{{background:#16a34a;box-shadow:0 0 16px rgba(34,197,94,.5);}}
.btn-stop{{background:#ef4444;color:#fff;flex:1;}}
.btn-stop:hover{{background:#dc2626;box-shadow:0 0 16px rgba(239,68,68,.5);}}
.btn-estop{{background:#f59e0b;color:#000;border:2px solid #b45309;
  font-size:16px;padding:10px 12px;}}
.btn-estop:hover{{background:#d97706;box-shadow:0 0 20px rgba(245,158,11,.6);}}
.btn-estop.fired{{background:#ef4444;color:#fff;border-color:#991b1b;
  animation:e-blink 0.6s step-end infinite;}}
@keyframes e-blink{{0%,100%{{opacity:1;}}50%{{opacity:.2;}}}}
.btn-reset{{background:#6366f1;color:#fff;border:none;border-radius:8px;
  padding:8px 14px;font-size:11px;font-weight:700;cursor:pointer;}}
.btn-reset:hover{{background:#4f46e5;}}
.btn-normal{{background:{accent};color:#fff;border:none;border-radius:8px;
  padding:9px 14px;font-size:11px;font-weight:700;cursor:pointer;width:100%;margin-top:4px;}}
.sys-status-row{{display:flex;align-items:center;gap:10px;margin-top:12px;}}
.sys-dot{{width:12px;height:12px;border-radius:50%;background:#334155;transition:all .3s;flex-shrink:0;}}
.sys-dot.running{{background:#22c55e;box-shadow:0 0 12px #22c55e;}}
.sys-dot.fault{{background:#ef4444;box-shadow:0 0 12px #ef4444;animation:pulse-dot 0.5s infinite;}}
.sys-txt{{font-size:12px;font-weight:700;color:#64748b;transition:color .3s;}}
.sys-txt.running{{color:#22c55e;}}
.sys-txt.fault{{color:#ef4444;}}
.sys-clock{{font-size:11px;color:#334155;font-family:monospace;margin-left:auto;}}

/* ── ALARMS SIDEBAR ──────────────────────────────── */
.alarm-grid{{display:flex;flex-wrap:wrap;gap:8px;}}
.alarm-sym.active-alarm .comp-name{{color:#ef4444;}}

/* ── SLIDER / SETPOINT ───────────────────────────── */
.slider-block{{margin-bottom:12px;}}
.slider-label{{font-size:11px;color:#94a3b8;font-weight:600;margin-bottom:6px;}}
.slider-row{{display:flex;align-items:center;gap:8px;}}
.comp-slider{{flex:1;accent-color:{accent};cursor:pointer;}}
.slider-val{{font-size:13px;font-weight:700;color:{accent};font-family:monospace;min-width:30px;}}
.slider-unit{{font-size:10px;color:#64748b;}}
.btn-wrap{{margin-bottom:6px;}}

/* ── EVENT LOG ───────────────────────────────────── */
.event-log{{
  background:#050c17;border-radius:6px;border:1px solid #0f2040;
  max-height:160px;overflow-y:auto;padding:6px;
  display:flex;flex-direction:column;gap:3px;
}}
.ev-item{{font-size:10px;padding:4px 8px;border-radius:4px;border-left:3px solid;}}
.ev-info{{background:rgba(59,130,246,.08);border-left-color:#3b82f6;color:#93c5fd;}}
.ev-ok{{background:rgba(34,197,94,.08);border-left-color:#22c55e;color:#86efac;}}
.ev-warn{{background:rgba(245,158,11,.08);border-left-color:#f59e0b;color:#fcd34d;}}
.ev-crit{{background:rgba(239,68,68,.1);border-left-color:#ef4444;color:#fca5a5;}}
.proc-desc{{font-size:10px;color:#64748b;line-height:1.5;}}

/* ── PIPES ───────────────────────────────────────── */
.pipe-line{{stroke-width:3;stroke-linecap:round;transition:stroke .5s,opacity .5s;}}
.pipe-active{{stroke:#22c55e;opacity:0.75;stroke-dasharray:12 6;
  animation:flow-dash 1.2s linear infinite;}}
.pipe-inactive{{stroke:#1e3a5f;opacity:0.4;stroke-dasharray:none;}}
@keyframes flow-dash{{to{{stroke-dashoffset:-18;}}}}

/* ── ANIMATIONS ──────────────────────────────────── */
@keyframes spin{{to{{transform:rotate(360deg);}}}}
.spinning{{animation:spin 1.4s linear infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:.15;}}}}
.pulsing{{animation:pulse 0.7s ease-in-out infinite;}}

/* ── TRENDS TAB ──────────────────────────────────── */
#tab-trends{{background:#060d1a;overflow-y:auto;padding:20px 24px;flex-wrap:wrap;
  align-content:flex-start;flex-direction:row;gap:16px;}}
.trend-card{{
  background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;
  padding:12px 14px;min-width:360px;flex:1;max-width:480px;
}}
.trend-hdr{{display:flex;align-items:center;gap:8px;margin-bottom:8px;}}
.trend-tag{{font-size:10px;font-weight:900;color:{accent};letter-spacing:1px;
  background:rgba(59,130,246,.12);border-radius:4px;padding:2px 7px;}}
.trend-name{{font-size:11px;font-weight:600;color:#94a3b8;flex:1;}}
.trend-live{{font-size:16px;font-weight:800;color:#e2e8f0;font-family:monospace;}}
.trend-unit{{font-size:10px;color:#475569;}}
.trend-canvas{{display:block;width:100%;border-radius:6px;background:#050c17;}}
.trend-footer{{display:flex;gap:16px;margin-top:6px;}}
.trend-stat{{font-size:10px;color:#475569;font-family:monospace;}}

/* ── ALARMS TAB ──────────────────────────────────── */
#tab-alarms{{background:#060d1a;flex-direction:column;}}
.alarms-toolbar{{
  display:flex;align-items:center;gap:12px;padding:12px 24px;
  background:#0a1628;border-bottom:1px solid #1e3a5f;flex-shrink:0;
}}
.alm-summary{{font-size:12px;color:#94a3b8;}}
.alm-active-count{{font-weight:800;color:#ef4444;}}
.alarm-table-wrap{{flex:1;overflow-y:auto;padding:0 24px 24px;}}
.alarm-table{{width:100%;border-collapse:collapse;margin-top:14px;}}
.alarm-table th{{
  font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;
  letter-spacing:1px;border-bottom:2px solid #1e3a5f;padding:8px 12px;
  text-align:left;position:sticky;top:0;background:#060d1a;
}}
.alarm-table td{{
  font-size:11px;color:#cbd5e1;padding:9px 12px;
  border-bottom:1px solid #0f2040;font-family:monospace;
}}
.alarm-table tr:hover td{{background:rgba(59,130,246,.04);}}
.alm-prio-crit{{color:#ef4444;font-weight:700;}}
.alm-prio-high{{color:#f59e0b;font-weight:700;}}
.alm-prio-low{{color:#22c55e;}}
.alm-state-active{{color:#ef4444;font-weight:700;}}
.alm-state-acked{{color:#475569;}}
.ack-btn{{
  background:transparent;border:1px solid #334155;color:#64748b;
  padding:3px 10px;border-radius:5px;font-size:10px;cursor:pointer;
  font-weight:700;transition:all .15s;
}}
.ack-btn:hover{{background:#1e3a5f;color:#e2e8f0;}}
.ack-btn:disabled{{opacity:.4;cursor:default;}}
.no-alarms{{text-align:center;padding:60px 20px;color:#334155;font-size:13px;}}

/* ── SETTINGS TAB ────────────────────────────────── */
#tab-settings{{background:#060d1a;overflow-y:auto;flex-direction:column;padding:24px;gap:20px;}}
.settings-section{{
  background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;padding:20px;
  max-width:680px;
}}
.settings-title{{
  font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;
  letter-spacing:1.5px;border-left:3px solid {accent};padding-left:10px;margin-bottom:16px;
}}
.proc-desc-full{{font-size:12px;color:#94a3b8;line-height:1.7;}}
.sysinfo-grid{{display:flex;flex-direction:column;gap:8px;}}
.sysinfo-row{{
  display:flex;justify-content:space-between;align-items:center;
  font-size:12px;padding:7px 0;border-bottom:1px solid #0f2040;
}}
.sysinfo-row span:first-child{{color:#64748b;}}
.sysinfo-row span:last-child{{color:#e2e8f0;font-weight:600;font-family:monospace;}}
.no-data{{color:#334155;font-size:12px;padding:10px 0;}}

/* ── SCROLLBAR ───────────────────────────────────── */
::-webkit-scrollbar{{width:5px;}}
::-webkit-scrollbar-track{{background:rgba(255,255,255,.02);}}
::-webkit-scrollbar-thumb{{background:rgba(59,130,246,.3);border-radius:10px;}}

@media print{{
  .tab-bar,.ctrl-area{{display:none;}}
  .tab-content{{display:block!important;}}
  body{{background:#fff;color:#000;height:auto;overflow:visible;}}
}}
</style>
</head>
<body>

<!-- HEADER -->
<div class="hdr">
  <div class="hdr-title">&#9670; {title}</div>
  <div class="hdr-right">
    <div class="online-badge">
      <div class="online-dot"></div>
      <span style="font-size:11px;color:#22c55e;font-weight:700;">ONLINE</span>
    </div>
    <span class="hdr-clock" id="hdrClock">--:--:--</span>
  </div>
</div>

<!-- TAB BAR -->
<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('overview',this)">&#9635; Overview</button>
  <button class="tab-btn" onclick="switchTab('trends',this)">&#9196; Trends</button>
  <button class="tab-btn" onclick="switchTab('alarms',this)">
    &#9888; Alarms <span class="tab-badge" id="alarmBadge">0</span>
  </button>
  <button class="tab-btn" onclick="switchTab('settings',this)">&#9881; Settings</button>
</div>

<!-- TAB: OVERVIEW -->
<div class="tab-content active" id="tab-overview">
  <div class="process-area" id="processArea">
    {canvas_html}
  </div>
  <div class="ctrl-area">
    {ctrl_html}
  </div>
</div>

<!-- TAB: TRENDS -->
<div class="tab-content" id="tab-trends">
  {trend_cards_html}
</div>

<!-- TAB: ALARMS -->
<div class="tab-content" id="tab-alarms">
  <div class="alarms-toolbar">
    <button class="ctrl-btn btn-reset" onclick="ackAllAlarms()">&#8635; ACK ALL</button>
    <span class="alm-summary">Active: <span class="alm-active-count" id="almActiveCount">0</span>
      &nbsp;|&nbsp; Total: <span id="almTotalCount">0</span></span>
  </div>
  <div class="alarm-table-wrap">
    <table class="alarm-table">
      <thead>
        <tr>
          <th>Time</th><th>Tag / ID</th><th>Description</th>
          <th>Priority</th><th>State</th><th>ACK</th>
        </tr>
      </thead>
      <tbody id="alarmTableBody">
        <tr><td colspan="6" class="no-alarms">No alarms — system normal</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- TAB: SETTINGS -->
<div class="tab-content" id="tab-settings">
  {settings_html}
</div>

<script>
// ═══════════════════════════════════════════════════════════
// INDUSTRIAL SIMULATION ENGINE v5 — Tabbed SCADA Dashboard
// ═══════════════════════════════════════════════════════════

// ── SIMULATION STATE ────────────────────────────────────────
const SIM        = {sim_json};
const CONNS      = {conn_data};
const TREND_IDS  = {trend_ids_json};

let sysRunning   = false;
let eStopActive  = false;
let simTick      = null;
let runSeconds   = 0;
let alarmCount   = 0;
let alarmRowIdx  = 0;

// Circular history buffer — 120 points = 60 seconds at 0.5s tick
const HIST_LEN = 120;
const HISTORY  = {{}};
TREND_IDS.forEach(id => {{ HISTORY[id] = []; }});

// ── TAB SWITCHING ─────────────────────────────────────────────
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-content').forEach(el => {{
    el.classList.remove('active');
  }});
  document.querySelectorAll('.tab-btn').forEach(el => {{
    el.classList.remove('active');
  }});
  const panel = document.getElementById('tab-' + name);
  if (panel) panel.classList.add('active');
  if (btn)   btn.classList.add('active');
  if (name === 'trends') _redrawAllTrends();
  if (name === 'overview') setTimeout(_updatePipes, 100);
}}

// ── CLOCK ────────────────────────────────────────────────────
function tick() {{
  const t = new Date().toLocaleTimeString('en-GB');
  const c = document.getElementById('hdrClock');
  const s = document.getElementById('sysClock');
  if (c) c.textContent = t;
  if (s) s.textContent = t;
}}
setInterval(tick, 1000); tick();

// ── EVENT LOG ────────────────────────────────────────────────
function log(cls, msg) {{
  const el = document.getElementById('eventLog');
  if (!el) return;
  const d = document.createElement('div');
  d.className = 'ev-item ev-' + cls;
  d.textContent = new Date().toLocaleTimeString('en-GB') + '  ' + msg;
  el.prepend(d);
  while (el.children.length > 50) el.removeChild(el.lastChild);
}}

// ── STATUS BADGE ──────────────────────────────────────────────
function _badge(running, estop) {{
  const dot = document.getElementById('sysDot');
  const txt = document.getElementById('sysTxt');
  if (!dot || !txt) return;
  if (estop) {{
    dot.className = 'sys-dot fault';
    txt.className = 'sys-txt fault'; txt.textContent = 'E-STOP';
  }} else if (running) {{
    dot.className = 'sys-dot running';
    txt.className = 'sys-txt running'; txt.textContent = 'RUNNING';
  }} else {{
    dot.className = 'sys-dot';
    txt.className = 'sys-txt'; txt.textContent = 'STOPPED';
  }}
}}

// ── SYSTEM START / STOP ───────────────────────────────────────
function startSystem() {{
  if (eStopActive) {{ log('crit', '⚠ E-STOP active — reset before starting'); return; }}
  sysRunning = true;
  _badge(true, false);
  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    if (['pump','motor','fan','compressor'].includes(s.type)) {{
      s.state = 'running';
      _applyMachineState(id, true);
    }}
    if (s.type === 'valve') {{
      s.state = 'open';
      _applyValveState(id, true, 100);
    }}
  }});
  _startSimLoop();
  log('ok', '▶ System STARTED — all equipment online');
}}

function stopSystem() {{
  sysRunning = false;
  _badge(false, false);
  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    if (['pump','motor','fan','compressor'].includes(s.type)) {{
      s.state = 'stopped';
      _applyMachineState(id, false);
    }}
  }});
  _stopSimLoop();
  log('warn', '■ System STOPPED — all equipment offline');
}}

function triggerEStop() {{
  eStopActive = true; sysRunning = false;
  _badge(false, true);
  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    s.state = 'stopped';
    if (['pump','motor','fan','compressor'].includes(s.type)) _applyMachineState(id, false);
    if (s.type === 'valve') _applyValveState(id, false, 0);
  }});
  _stopSimLoop();
  const eb = document.getElementById('eStopBtn');
  if (eb) eb.textContent = '⚠ E-STOP ACTIVE';
  log('crit', '🔴 EMERGENCY STOP — system locked out');
}}

function releaseEStop() {{
  eStopActive = false;
  const eb = document.getElementById('eStopBtn');
  if (eb) {{ eb.classList.remove('fired'); eb.textContent = '⚠ E-STOP'; }}
  _badge(false, false);
  log('warn', 'E-Stop released — press START to resume');
}}

// ── MACHINE TOGGLE ────────────────────────────────────────────
function toggleEquipment(el) {{
  if (eStopActive) {{ log('crit', '⚠ E-Stop active'); return; }}
  if (!sysRunning) {{ log('warn', '⚠ Start system first'); return; }}
  const id = el.dataset.id;
  if (!SIM[id]) return;
  const on = SIM[id].state !== 'running';
  SIM[id].state = on ? 'running' : 'stopped';
  _applyMachineState(id, on);
  const lbl = el.querySelector('.comp-name')?.textContent || id;
  log(on ? 'ok' : 'warn', lbl + ' ' + (on ? 'started' : 'stopped'));
}}

function _applyMachineState(id, on) {{
  const el = document.getElementById('sym-' + id);
  if (!el) return;
  const col = on ? '#22c55e' : '#64748b';
  const status = on ? 'RUNNING' : 'STOPPED';
  el.querySelectorAll('[id^="pdash-"],[id^="pimp-"],[id^="mspin-"],[id^="fblades-"]')
    .forEach(s => s.classList.toggle('spinning', on));
  el.querySelectorAll('[id^="phub-"],[id^="fhub-"]').forEach(s => s.setAttribute('fill', col));
  el.querySelectorAll('[id^="pring-"],[id^="fring-"],[id^="mrect-"]')
    .forEach(s => s.setAttribute('stroke', col));
  el.querySelectorAll('[id^="ptxt-"],[id^="mtxt-"],[id^="ftxt-"]')
    .forEach(s => {{ s.setAttribute('fill', col); if (s.tagName==='text') s.textContent = status; }});
  el.classList.toggle('active-state', on);
  _updatePipes();
}}

// ── VALVE TOGGLE ──────────────────────────────────────────────
function toggleValve(el) {{
  if (eStopActive) {{ log('crit', '⚠ E-Stop active'); return; }}
  if (!sysRunning) {{ log('warn', '⚠ Start system first'); return; }}
  const id = el.dataset.id;
  if (!SIM[id]) return;
  const open = SIM[id].state !== 'open';
  SIM[id].state = open ? 'open' : 'closed';
  SIM[id].value = open ? 100 : 0;
  _applyValveState(id, open, open ? 100 : 0);
  const lbl = el.querySelector('.comp-name')?.textContent || id;
  log('info', lbl + ' ' + (open ? 'opened' : 'closed'));
}}

function _applyValveState(id, open, pct) {{
  const el = document.getElementById('sym-' + id);
  if (!el) return;
  const col  = open ? '#22c55e' : '#ef4444';
  const fill = open ? '#22c55e' : '#0f172a';
  const status = open ? 'OPEN' : 'CLOSED';
  el.querySelectorAll('[id^="vtri1-"],[id^="vtri2-"]').forEach(s => {{
    s.setAttribute('fill', fill); s.setAttribute('stroke', col);
  }});
  el.querySelectorAll('[id^="vdot-"]').forEach(s => s.setAttribute('fill', col));
  el.querySelectorAll('[id^="vtxt-"]').forEach(s => {{
    s.setAttribute('fill', col); s.textContent = status;
  }});
  const bar = document.getElementById('vbar-' + id);
  if (bar) bar.setAttribute('width', Math.round(pct * 52 / 100));
  const rv = document.getElementById('rdgval-' + id);
  if (rv) rv.textContent = pct;
  el.classList.toggle('active-state', open);
  _updatePipes();
}}

// ── ALARM SYMBOL (overview sidebar) ──────────────────────────
function acknowledgeAlarm(el) {{
  const id = el.dataset.id;
  _clearAlarmSymbol(id);
  log('ok', '✓ Alarm ' + id + ' acknowledged');
}}

function resetAlarms() {{
  document.querySelectorAll('[data-type="alarm"]').forEach(el => {{
    const id = el.dataset.id;
    if (id) _clearAlarmSymbol(id);
  }});
  alarmCount = 0;
  _updateAlarmCounts();
  log('ok', '✓ All alarms cleared');
}}

function _clearAlarmSymbol(id) {{
  const el = document.getElementById('sym-' + id);
  if (!el) return;
  el.classList.remove('active-alarm');
  const tri  = document.getElementById('atri-'  + id);
  const txt  = document.getElementById('atxt-'  + id);
  const excl = document.getElementById('aexcl-' + id);
  if (tri)  {{ tri.classList.remove('pulsing');  tri.setAttribute('stroke','#64748b'); }}
  if (txt)  {{ txt.textContent = 'NORMAL'; txt.setAttribute('fill','#64748b'); }}
  if (excl) excl.setAttribute('fill','#64748b');
}}

function _triggerAlarmSymbol(id, label, priority) {{
  // SVG symbol on overview sidebar
  const el = document.getElementById('sym-' + id);
  if (el && !el.classList.contains('active-alarm')) {{
    el.classList.add('active-alarm');
    const tri  = document.getElementById('atri-'  + id);
    const txt  = document.getElementById('atxt-'  + id);
    const excl = document.getElementById('aexcl-' + id);
    if (tri)  {{ tri.classList.add('pulsing');  tri.setAttribute('stroke','#ef4444'); }}
    if (txt)  {{ txt.textContent = 'ACTIVE';    txt.setAttribute('fill','#ef4444'); }}
    if (excl) excl.setAttribute('fill','#ef4444');
  }}
  // Alarm table row
  _addAlarmRow(id, label, priority);
  log('crit', '🔔 [ALM] ' + label);
}}

// ── ALARM TABLE ────────────────────────────────────────────────
const ALARM_ROWS = [];  // {{idx, id, label, priority, acked, time}}

function _addAlarmRow(id, label, priority) {{
  // Deduplicate — don't add same alarm tag twice while active
  if (ALARM_ROWS.some(r => r.id === id && !r.acked)) return;
  const idx = alarmRowIdx++;
  const now = new Date().toLocaleTimeString('en-GB');
  ALARM_ROWS.unshift({{ idx, id, label, priority, acked: false, time: now }});
  alarmCount++;
  _rebuildAlarmTable();
  _updateAlarmCounts();
}}

function ackAlarmRow(idx) {{
  const row = ALARM_ROWS.find(r => r.idx === idx);
  if (!row) return;
  row.acked = true;
  alarmCount = Math.max(0, alarmCount - 1);
  _clearAlarmSymbol('sym-' + row.id);
  _rebuildAlarmTable();
  _updateAlarmCounts();
  log('ok', '✓ ACK: ' + row.label);
}}

function ackAllAlarms() {{
  ALARM_ROWS.forEach(r => {{ r.acked = true; _clearAlarmSymbol('sym-' + r.id); }});
  alarmCount = 0;
  _rebuildAlarmTable();
  _updateAlarmCounts();
  log('ok', '✓ All alarms acknowledged');
}}

function _rebuildAlarmTable() {{
  const tbody = document.getElementById('alarmTableBody');
  if (!tbody) return;
  if (ALARM_ROWS.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="6" class="no-alarms">No alarms — system normal</td></tr>';
    return;
  }}
  tbody.innerHTML = ALARM_ROWS.map(r => {{
    const prioCls  = r.priority === 'critical' ? 'alm-prio-crit' :
                     r.priority === 'high'     ? 'alm-prio-high' : 'alm-prio-low';
    const stateCls = r.acked ? 'alm-state-acked' : 'alm-state-active';
    const state    = r.acked ? 'ACKED' : 'ACTIVE';
    const ackDis   = r.acked ? 'disabled' : '';
    return `<tr>
      <td>${{r.time}}</td>
      <td>${{r.id}}</td>
      <td>${{r.label}}</td>
      <td class="${{prioCls}}">${{(r.priority||'').toUpperCase()}}</td>
      <td class="${{stateCls}}">${{state}}</td>
      <td><button class="ack-btn" onclick="ackAlarmRow(${{r.idx}})" ${{ackDis}}>ACK</button></td>
    </tr>`;
  }}).join('');
}}

function _updateAlarmCounts() {{
  const active = ALARM_ROWS.filter(r => !r.acked).length;
  const badge  = document.getElementById('alarmBadge');
  const ac     = document.getElementById('almActiveCount');
  const tc     = document.getElementById('almTotalCount');
  if (badge) {{
    badge.textContent = active;
    badge.classList.toggle('visible', active > 0);
  }}
  if (ac) ac.textContent = active;
  if (tc) tc.textContent = ALARM_ROWS.length;
}}

// ── SETPOINT SLIDER ───────────────────────────────────────────
function updateSetpoint(inp, id) {{
  const v = document.getElementById('sval-' + id);
  if (v) v.textContent = inp.value;
  if (SIM[id]) SIM[id].value = parseFloat(inp.value);
  log('info', 'Setpoint → ' + inp.value + '%');
}}

function handleBtn(el, id) {{
  log('info', 'Command: ' + (el.textContent || id));
}}

// ── PIPE FLOW ANIMATION ──────────────────────────────────────
function _updatePipes() {{
  CONNS.forEach((conn, i) => {{
    const line   = document.getElementById('pipe' + i);
    if (!line) return;
    const fromEl = document.getElementById('sym-' + conn.from?.replace(/-/g,'_'));
    const toEl   = document.getElementById('sym-' + conn.to?.replace(/-/g,'_'));
    if (!fromEl || !toEl) return;

    const fr     = fromEl.getBoundingClientRect();
    const to     = toEl.getBoundingClientRect();
    const canvas = document.getElementById('processArea').getBoundingClientRect();
    const x1 = fr.left + fr.width/2  - canvas.left;
    const y1 = fr.top  + fr.height/2 - canvas.top;
    const x2 = to.left + to.width/2  - canvas.left;
    const y2 = to.top  + to.height/2 - canvas.top;
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);

    const fromSim = SIM[conn.from?.replace(/-/g,'_')];
    const active  = fromSim && (fromSim.state === 'running' || fromSim.state === 'open');
    line.className = 'pipe-line ' + (active ? 'pipe-active' : 'pipe-inactive');
    line.setAttribute('marker-end', active ? 'url(#arrowEnd)' : '');
  }});
}}

// ── TREND SPARKLINE ENGINE ────────────────────────────────────
function _pushHistory(id, val) {{
  if (!HISTORY[id]) return;
  HISTORY[id].push(parseFloat(val) || 0);
  if (HISTORY[id].length > HIST_LEN) HISTORY[id].shift();

  // Update live label in trend card header
  const liveEl = document.getElementById('tlive-' + id);
  if (liveEl) liveEl.textContent = (parseFloat(val) || 0).toFixed(1);

  // If trends tab is visible, redraw immediately
  const trendsTab = document.getElementById('tab-trends');
  if (trendsTab && trendsTab.classList.contains('active')) _drawTrend(id);
}}

function _drawTrend(id) {{
  const canvas = document.getElementById('tcanv-' + id);
  if (!canvas) return;
  const data = HISTORY[id];
  if (!data || data.length < 2) return;

  const ctx = canvas.getContext('2d');
  const W   = canvas.width;
  const H   = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const mn  = Math.min(...data);
  const mx  = Math.max(...data);
  const rng = Math.max(mx - mn, 1);

  // Background grid lines
  ctx.strokeStyle = '#0f2040';
  ctx.lineWidth   = 1;
  [0.25, 0.5, 0.75].forEach(p => {{
    const y = H * p;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }});

  // Gradient fill
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0,   'rgba(59,130,246,0.35)');
  grad.addColorStop(1,   'rgba(59,130,246,0.01)');

  const xStep = W / (HIST_LEN - 1);
  const yFor  = v => H - ((v - mn) / rng) * (H - 8) - 4;

  // Fill area
  ctx.beginPath();
  ctx.moveTo(0, H);
  data.forEach((v, i) => {{
    const x = (HIST_LEN - data.length + i) * xStep;
    i === 0 ? ctx.lineTo(x, yFor(v)) : ctx.lineTo(x, yFor(v));
  }});
  ctx.lineTo((HIST_LEN - 1) * xStep, H);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  ctx.strokeStyle = '#3b82f6';
  ctx.lineWidth   = 2;
  ctx.lineJoin    = 'round';
  data.forEach((v, i) => {{
    const x = (HIST_LEN - data.length + i) * xStep;
    i === 0 ? ctx.moveTo(x, yFor(v)) : ctx.lineTo(x, yFor(v));
  }});
  ctx.stroke();

  // Last point dot
  const lastX = (HIST_LEN - 1) * xStep;
  const lastY = yFor(data[data.length - 1]);
  ctx.beginPath();
  ctx.arc(lastX, lastY, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = '#60a5fa';
  ctx.fill();

  // Update stats
  const avg  = data.reduce((a, b) => a + b, 0) / data.length;
  const minEl = document.getElementById('tmin-' + id);
  const avgEl = document.getElementById('tavg-' + id);
  const maxEl = document.getElementById('tmax-' + id);
  if (minEl) minEl.textContent = 'min ' + mn.toFixed(1);
  if (avgEl) avgEl.textContent = 'avg ' + avg.toFixed(1);
  if (maxEl) maxEl.textContent = 'max ' + mx.toFixed(1);
}}

function _redrawAllTrends() {{
  TREND_IDS.forEach(id => _drawTrend(id));
}}

// ── PROCESS SIMULATION LOOP (runs every 500ms) ────────────────
function _startSimLoop() {{
  if (simTick) return;
  simTick = setInterval(_simStep, 500);
}}

function _stopSimLoop() {{
  if (simTick) {{ clearInterval(simTick); simTick = null; }}
}}

function _simStep() {{
  if (!sysRunning) return;
  runSeconds += 0.5;

  // ── Net flow into each tank ───────────────────────────────
  const tankFlow = {{}};
  Object.keys(SIM).forEach(id => {{ tankFlow[id] = 0; }});

  CONNS.forEach(conn => {{
    const fid = conn.from?.replace(/-/g,'_');
    const tid = conn.to?.replace(/-/g,'_');
    if (!fid || !tid || !SIM[fid] || !SIM[tid]) return;
    const srcState = SIM[fid].state;
    if (srcState === 'running' || srcState === 'open') {{
      const rate = SIM[fid].fill_rate || 0;
      if (SIM[tid].type === 'tank') tankFlow[tid] += rate;
    }}
  }});

  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    if (s.type !== 'tank') return;
    const drain = s.drain_rate || 0;
    if (drain > 0) tankFlow[id] -= drain;
  }});

  // ── Update tank levels ────────────────────────────────────
  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    if (s.type !== 'tank') return;

    const cap      = s.capacity || 10000;
    const netFlow  = tankFlow[id] || 0;
    const deltaPct = (netFlow / cap) * 100 * 0.5;
    let lvl = (s.value !== null && s.value !== undefined) ? parseFloat(s.value) : 50;
    lvl = Math.max(0, Math.min(100, lvl + deltaPct));
    s.value = parseFloat(lvl.toFixed(1));
    _updateTankLevel(id, lvl);
    _pushHistory(id, lvl);

    if (s.hi_hi    !== null && s.hi_hi    !== undefined && lvl >= s.hi_hi)
      _triggerAlarmSymbol('ALM_' + id, 'CRITICAL HIGH LEVEL: ' + id + ' ' + lvl.toFixed(1) + '%', 'critical');
    else if (s.hi_alarm !== null && s.hi_alarm !== undefined && lvl >= s.hi_alarm)
      _triggerAlarmSymbol('ALM_' + id, 'HIGH LEVEL: ' + id + ' ' + lvl.toFixed(1) + '%', 'high');
    else if (s.lo_lo   !== null && s.lo_lo   !== undefined && lvl <= s.lo_lo)
      _triggerAlarmSymbol('ALM_' + id, 'CRITICAL LOW LEVEL: ' + id + ' ' + lvl.toFixed(1) + '%', 'critical');
    else if (s.lo_alarm !== null && s.lo_alarm !== undefined && lvl <= s.lo_alarm)
      _triggerAlarmSymbol('ALM_' + id, 'LOW LEVEL: ' + id + ' ' + lvl.toFixed(1) + '%', 'high');
  }});

  // ── Sensor / gauge random walk ────────────────────────────
  Object.keys(SIM).forEach(id => {{
    const s = SIM[id];
    if (!s.type.startsWith('sensor') && s.type !== 'gauge') return;

    let val = parseFloat(s.value) || 0;
    const nMin  = s.normal_min || 20;
    const nMax  = s.normal_max || 80;
    const drift = (Math.random() - 0.5) * 0.8;
    val = Math.max(nMin - 5, Math.min(nMax + 5, val + drift));
    s.value = parseFloat(val.toFixed(1));
    _updateSensorDisplay(id, val);
    _pushHistory(id, val);

    if (s.hi_alarm !== null && s.hi_alarm !== undefined && val >= s.hi_alarm)
      _triggerAlarmSymbol('ALM_S_' + id, 'HIGH VALUE: ' + id + ' ' + val.toFixed(1), 'high');
  }});

  _updatePipes();
}}

// ── DOM UPDATE HELPERS ────────────────────────────────────────
function _updateTankLevel(id, lvl) {{
  const liq  = document.getElementById('liq-'    + id);
  const lvlt = document.getElementById('lvltxt-' + id);
  const rdg  = document.getElementById('rdgval-' + id);
  if (!liq) return;
  const liqH = Math.round(lvl * 0.78);
  const liqY = 12 + (78 - liqH);
  liq.setAttribute('y', liqY);
  liq.setAttribute('height', liqH);
  const col = lvl < 75 ? '#22c55e' : lvl < 90 ? '#f59e0b' : '#ef4444';
  liq.setAttribute('fill', col);
  if (lvlt) lvlt.textContent = lvl.toFixed(0) + '%';
  if (rdg)  rdg.textContent  = lvl.toFixed(1);
}}

function _updateSensorDisplay(id, val) {{
  const el  = document.getElementById('stxt-'   + id);
  const rdg = document.getElementById('rdgval-' + id);
  if (el)  el.textContent  = val.toFixed(1);
  if (rdg) rdg.textContent = val.toFixed(1);
}}

// ── INIT ──────────────────────────────────────────────────────
window.addEventListener('load', () => {{
  setTimeout(_updatePipes, 300);
  log('info', 'System ready — press START to begin');
}});
window.addEventListener('resize', _updatePipes);
</script>
</body>
</html>"""

    return html
