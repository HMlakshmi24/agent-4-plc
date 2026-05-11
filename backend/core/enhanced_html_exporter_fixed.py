"""
Enhanced HTML Exporter - Industrial P&ID symbols with FULL interactivity and simulation
"""

from html import escape
import json

def generate_enhanced_html_from_json(layout):
    """Generate a standalone HMI HTML export with embedded controls and simulation."""
    return generate_basic_hmi(layout)

def generate_pid_html_from_json(layout):
    """Generate P&ID specific HTML with industrial symbols and interactivity"""

    from pathlib import Path
    import json
    from backend.pid.pid_layout_engine import build_pid_layout

    def _normalize_components(components):
        type_counters = {}
        def _tag_for(comp_type):
            base = {
                'tank': 'TK',
                'pump': 'P',
                'motor': 'M',
                'valve': 'V',
                'sensor': 'S',
                'sensor_level': 'LT',
                'sensor_temp': 'TT',
                'sensor_pressure': 'PT',
                'gauge': 'G',
                'alarm': 'ALM',
                'button': 'PB',
                'conveyor': 'CV',
                'compressor': 'C',
                'fan': 'F'
            }.get(comp_type, comp_type[:2].upper() or 'EQ')
            type_counters[base] = type_counters.get(base, 100) + 1
            return f"{base}-{type_counters[base]}"

        normalized = []
        for comp in components:
            c = dict(comp or {})
            ctype = c.get('type') or 'equipment'
            label = c.get('label') or c.get('name') or c.get('id') or ctype.title()
            c['name'] = c.get('name') or label
            c['tag'] = c.get('tag') or _tag_for(ctype)
            normalized.append(c)
        return normalized

    def _auto_layout(components):
        if not components:
            return components
        xs = [c.get('x', 0) for c in components]
        ys = [c.get('y', 0) for c in components]
        range_x = max(xs) - min(xs)
        range_y = max(ys) - min(ys)
        if range_x >= 260 and range_y >= 220:
            return components

        width, height = 1000, 400
        center_y = 200
        top_y = 80
        bottom_y = 320
        left_x = 80
        right_x = 860

        flow_types = {'tank', 'pump', 'valve', 'motor', 'compressor', 'fan', 'conveyor', 'mixer'}
        def is_alarm(c): return c.get('type') == 'alarm'
        def is_control(c): return c.get('type') in {'button', 'slider'}
        def is_instrument(c):
            t = (c.get('type') or '')
            return t == 'gauge' or t.startswith('sensor')
        def is_flow(c): return c.get('type') in flow_types

        flow = [c for c in components if is_flow(c)]
        instruments = [c for c in components if is_instrument(c)]
        alarms = [c for c in components if is_alarm(c)]
        controls = [c for c in components if is_control(c)]
        others = [c for c in components if c not in flow + instruments + alarms + controls]

        def place_row(items, y, spacing):
            if not items:
                return
            span = max(1, len(items) - 1)
            total = span * spacing
            start_x = max(140, (width - total) / 2)
            for i, item in enumerate(items):
                item['x'] = round(start_x + i * spacing)
                item['y'] = y

        place_row(flow, center_y, 180)
        place_row(instruments, top_y, 150)
        place_row(others, bottom_y, 150)

        for i, item in enumerate(alarms):
            item['x'] = left_x
            item['y'] = top_y + i * 70
        for i, item in enumerate(controls):
            item['x'] = right_x
            item['y'] = top_y + i * 70

        return components

    system_name = layout.get('system_name', 'P&ID Diagram')
    theme = layout.get('theme', 'default')

    enhanced_layout = build_pid_layout(layout)
    enhanced_layout['system_name'] = system_name
    enhanced_layout['theme'] = theme

    root = Path(__file__).resolve().parents[2]
    template_path = root / 'ENHANCED_INDUSTRIAL_PID_TEMPLATE.html'
    template = template_path.read_text(encoding='utf-8')

    # Update title and header
    template = template.replace('Enhanced Industrial P&ID - Theme-Aware', f"{system_name} - P&ID")
    template = template.replace('Enhanced Industrial P&ID', f"{system_name} - P&ID")

    layout_json = json.dumps(enhanced_layout)
    inject = f"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    if (window.applyPIDLayout) {{
        window.applyPIDLayout({layout_json});
    }}
}});
</script>
"""

    if '</body>' in template:
        template = template.replace('</body>', f"{inject}\n</body>")
    else:
        template = template + inject

    return template

def generate_basic_hmi(layout):
    """Standalone industrial HMI export."""

    system_name = layout.get('system_name', 'HMI System')
    theme = layout.get('theme', 'default')
    components = layout.get('components', [])
    connections = layout.get('connections', [])

    def theme_colors(theme_name):
        palettes = {
            'water': ('#071826', '#0f2740', '#38bdf8', '#22c55e'),
            'hvac': ('#0a1620', '#152a36', '#67e8f9', '#84cc16'),
            'chemical': ('#120d1f', '#24153f', '#a78bfa', '#f97316'),
            'food': ('#1b1209', '#362110', '#f59e0b', '#22c55e'),
            'motor': ('#0b1120', '#172036', '#60a5fa', '#22c55e'),
            'default': ('#0b1120', '#18243a', '#60a5fa', '#22c55e'),
        }
        return palettes.get(theme_name, palettes['default'])

    bg, panel, accent, ok = theme_colors(theme)

    def component_state(comp):
        if comp.get('type') == 'button':
            return 'standby'
        return str(comp.get('state') or 'inactive')

    def render_component(comp):
        comp_id = escape(str(comp.get('id', 'component')))
        comp_type = escape(str(comp.get('type', 'equipment')))
        label = escape(str(comp.get('label') or comp.get('name') or comp_id))
        unit = escape(str(comp.get('unit') or ''))
        value = comp.get('value')
        value_text = '' if value is None else escape(str(value))
        state = escape(component_state(comp))
        x = int(comp.get('x', 80))
        y = int(comp.get('y', 80))
        width_map = {
            'tank': 128, 'pump': 108, 'motor': 108, 'valve': 98, 'alarm': 180,
            'button': 112, 'gauge': 110, 'sensor_level': 96, 'sensor_temp': 96,
            'sensor_pressure': 96, 'sensor_flow': 96, 'fan': 108, 'compressor': 112
        }
        height_map = {
            'tank': 188, 'pump': 126, 'motor': 126, 'valve': 108, 'alarm': 88,
            'button': 64, 'gauge': 118, 'sensor_level': 118, 'sensor_temp': 106,
            'sensor_pressure': 106, 'sensor_flow': 106, 'fan': 126, 'compressor': 126
        }
        width = width_map.get(comp.get('type'), 104)
        height = height_map.get(comp.get('type'), 102)
        data_value = '' if value is None else f'data-value="{escape(str(value))}"'
        data_unit = f'data-unit="{unit}"'
        return f"""
        <div class="component component-{comp_type}" id="{comp_id}" data-type="{comp_type}" data-state="{state}" {data_value} {data_unit}
             style="left:{x}px; top:{y}px; width:{width}px; min-height:{height}px;">
            <div class="symbol">
                <div class="symbol-core"></div>
                <div class="symbol-tag">{comp_id}</div>
            </div>
            <div class="component-label">{label}</div>
            <div class="component-meta">
                <span class="component-state">{state.upper()}</span>
                <span class="component-value">{value_text}{(' ' + unit) if value_text and unit else ''}</span>
            </div>
        </div>"""

    svg_lines = []
    comp_map = {str(comp.get('id')): comp for comp in components}
    for conn in connections:
        src = comp_map.get(str(conn.get('from')))
        dst = comp_map.get(str(conn.get('to')))
        if not src or not dst:
            continue
        x1 = int(src.get('x', 0)) + 54
        y1 = int(src.get('y', 0)) + 42
        x2 = int(dst.get('x', 0)) + 54
        y2 = int(dst.get('y', 0)) + 42
        conn_type = escape(str(conn.get('type', 'pipe')))
        svg_lines.append(
            f'<line class="conn conn-{conn_type}" data-when="{escape(str(conn.get("active_when", "always")))}" '
            f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
        )

    layout_json = json.dumps(layout)
    component_markup = ''.join(render_component(comp) for comp in components)
    connection_markup = ''.join(svg_lines)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(system_name)}</title>
    <style>
        :root {{
            --bg: {bg};
            --panel: {panel};
            --accent: {accent};
            --ok: {ok};
            --warn: #f59e0b;
            --danger: #ef4444;
            --text: #e5eef8;
            --muted: #93a7bd;
            --line: rgba(148, 163, 184, 0.28);
        }}
        body {{
            font-family: "Segoe UI", Arial, sans-serif;
            background:
                radial-gradient(circle at 20% 0%, rgba(96,165,250,0.18), transparent 28%),
                radial-gradient(circle at 85% 15%, rgba(34,197,94,0.12), transparent 25%),
                var(--bg);
            margin: 0;
            color: var(--text);
            min-height: 100vh;
        }}
        * {{
            box-sizing: border-box;
        }}
        .shell {{
            padding: 20px;
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            background: linear-gradient(180deg, rgba(24,36,58,0.96), rgba(11,17,32,0.96));
            border: 1px solid rgba(96,165,250,0.18);
            border-radius: 18px;
            padding: 18px 22px;
            box-shadow: 0 18px 40px rgba(0,0,0,0.28);
            backdrop-filter: blur(16px);
        }}
        .header-title {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .header-kicker {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.24em;
            color: var(--accent);
            font-weight: bold;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header-subtitle {{
            color: var(--muted);
            font-size: 13px;
        }}
        .toolbar {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .toolbar button {{
            border: 1px solid rgba(148,163,184,0.22);
            background: rgba(15,23,42,0.94);
            color: var(--text);
            border-radius: 999px;
            padding: 10px 16px;
            font-weight: 700;
            letter-spacing: 0.08em;
            cursor: pointer;
        }}
        .toolbar button[data-role="start"] {{
            border-color: rgba(34,197,94,0.45);
            color: #d1fae5;
        }}
        .toolbar button[data-role="stop"] {{
            border-color: rgba(239,68,68,0.45);
            color: #fecaca;
        }}
        .toolbar button[data-role="estop"] {{
            border-color: rgba(245,158,11,0.45);
            color: #fde68a;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 16px 0;
        }}
        .card {{
            background: linear-gradient(180deg, rgba(24,36,58,0.96), rgba(11,17,32,0.94));
            border: 1px solid rgba(96,165,250,0.12);
            border-radius: 16px;
            padding: 14px 16px;
            min-height: 92px;
        }}
        .card-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.22em;
            color: var(--muted);
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 800;
            margin-top: 8px;
        }}
        .workspace {{
            position: relative;
            min-height: 700px;
            background:
                linear-gradient(rgba(125,211,252,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(125,211,252,0.05) 1px, transparent 1px),
                linear-gradient(180deg, rgba(24,36,58,0.94), rgba(8,13,24,0.98));
            background-size: 56px 56px, 56px 56px, auto;
            border: 1px solid rgba(96,165,250,0.14);
            border-radius: 20px;
            overflow: auto;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
        }}
        .workspace-inner {{
            position: relative;
            width: 1280px;
            height: 820px;
        }}
        .connections {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}
        .conn {{
            stroke: rgba(125,211,252,0.45);
            stroke-width: 6;
            stroke-linecap: round;
        }}
        .conn.conn-signal {{
            stroke: rgba(250,204,21,0.55);
            stroke-dasharray: 10 8;
            stroke-width: 4;
        }}
        .conn.active {{
            stroke: var(--ok);
            filter: drop-shadow(0 0 8px rgba(34,197,94,0.55));
        }}
        .component {{
            position: absolute;
            background: linear-gradient(180deg, rgba(18,28,46,0.98), rgba(11,17,32,0.98));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 18px;
            padding: 12px;
            box-shadow: 0 16px 28px rgba(0,0,0,0.28);
        }}
        .component[data-state="running"],
        .component[data-state="open"],
        .component[data-state="active"] {{
            border-color: rgba(34,197,94,0.4);
            box-shadow: 0 16px 28px rgba(0,0,0,0.28), 0 0 0 1px rgba(34,197,94,0.18);
        }}
        .component[data-state="stopped"],
        .component[data-state="closed"],
        .component[data-state="inactive"] {{
            border-color: rgba(239,68,68,0.2);
        }}
        .symbol {{
            height: 92px;
            border-radius: 14px;
            border: 1px solid rgba(125,211,252,0.14);
            background:
                radial-gradient(circle at 30% 20%, rgba(96,165,250,0.18), transparent 38%),
                rgba(15,23,42,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}
        .symbol-core {{
            width: 52px;
            height: 52px;
            border-radius: 50%;
            border: 3px solid var(--accent);
            box-shadow: 0 0 18px rgba(96,165,250,0.2);
        }}
        .component-tank .symbol-core {{
            width: 54px;
            height: 68px;
            border-radius: 12px;
        }}
        .component-valve .symbol-core {{
            width: 58px;
            height: 58px;
            transform: rotate(45deg);
            border-radius: 10px;
        }}
        .component-alarm .symbol-core {{
            width: 0;
            height: 0;
            border-left: 28px solid transparent;
            border-right: 28px solid transparent;
            border-bottom: 50px solid var(--danger);
            border-top: none;
            border-radius: 0;
        }}
        .component-button .symbol-core {{
            width: 76px;
            height: 42px;
            border-radius: 999px;
        }}
        .symbol-tag {{
            position: absolute;
            bottom: 8px;
            right: 10px;
            font-size: 11px;
            font-family: Consolas, monospace;
            color: var(--muted);
        }}
        .component-label {{
            margin-top: 10px;
            font-weight: 700;
            font-size: 13px;
            line-height: 1.4;
        }}
        .component-meta {{
            margin-top: 8px;
            display: flex;
            justify-content: space-between;
            gap: 10px;
            font-size: 11px;
            color: var(--muted);
            font-family: Consolas, monospace;
        }}
        .component-state {{
            color: var(--accent);
            letter-spacing: 0.08em;
        }}
        .component.alarm-live {{
            animation: pulse-alarm 1.3s ease-in-out infinite;
        }}
        .footer-note {{
            margin-top: 12px;
            color: var(--muted);
            font-size: 12px;
        }}
        @keyframes pulse-alarm {{
            0%, 100% {{ box-shadow: 0 16px 28px rgba(0,0,0,0.28), 0 0 0 0 rgba(239,68,68,0.28); }}
            50% {{ box-shadow: 0 16px 28px rgba(0,0,0,0.28), 0 0 0 8px rgba(239,68,68,0.08); }}
        }}
        @media (max-width: 900px) {{
            .header {{
                flex-direction: column;
                align-items: stretch;
            }}
            .workspace-inner {{
                width: 1180px;
            }}
        }}
    </style>
</head>
<body>
    <div class="shell">
        <div class="header">
            <div class="header-title">
                <div class="header-kicker">Industrial HMI Export</div>
                <h1>{escape(system_name)}</h1>
                <div class="header-subtitle">Theme: {escape(theme)} | Components: {len(components)} | Connections: {len(connections)}</div>
            </div>
            <div class="toolbar">
                <button data-role="start" onclick="startSystem()">START</button>
                <button data-role="stop" onclick="stopSystem()">STOP</button>
                <button data-role="estop" onclick="emergencyStop()">E-STOP</button>
                <button onclick="resetSystem()">RESET</button>
            </div>
        </div>
        <div class="summary">
            <div class="card">
                <div class="card-label">System Status</div>
                <div class="card-value" id="statusValue">STANDBY</div>
            </div>
            <div class="card">
                <div class="card-label">Active Equipment</div>
                <div class="card-value" id="equipmentValue">0</div>
            </div>
            <div class="card">
                <div class="card-label">Average Tank Level</div>
                <div class="card-value" id="tankValue">0%</div>
            </div>
            <div class="card">
                <div class="card-label">Alarm State</div>
                <div class="card-value" id="alarmValue">CLEAR</div>
            </div>
        </div>
        <div class="workspace">
            <div class="workspace-inner">
                <svg class="connections" viewBox="0 0 1280 820" preserveAspectRatio="none">{connection_markup}</svg>
                {component_markup}
            </div>
        </div>
        <div class="footer-note">
            Export includes embedded simulation controls so the HMI can be reviewed without the frontend app.
        </div>
    </div>
    <script>
        const layout = {layout_json};
        const state = {{
            running: false,
            estop: false,
            tankLevel: averageTankLevel(),
        }};

        function averageTankLevel() {{
            const tanks = (layout.components || []).filter((c) => c.type === 'tank');
            if (!tanks.length) return 0;
            const total = tanks.reduce((sum, item) => sum + Number(item.value || 0), 0);
            return Math.round(total / tanks.length);
        }}

        function updateSummary() {{
            const components = Array.from(document.querySelectorAll('.component'));
            const activeCount = components.filter((el) => ['running', 'open', 'active'].includes(el.dataset.state)).length;
            const activeAlarm = components.some((el) => el.dataset.type === 'alarm' && el.dataset.state === 'active');
            document.getElementById('statusValue').textContent = state.estop ? 'E-STOP' : state.running ? 'RUNNING' : 'STANDBY';
            document.getElementById('equipmentValue').textContent = String(activeCount);
            document.getElementById('tankValue').textContent = `${{state.tankLevel}}%`;
            document.getElementById('alarmValue').textContent = activeAlarm ? 'ACTIVE' : 'CLEAR';
        }}

        function setComponentState(typeList, nextState) {{
            document.querySelectorAll('.component').forEach((el) => {{
                if (typeList.includes(el.dataset.type)) {{
                    el.dataset.state = nextState;
                    const badge = el.querySelector('.component-state');
                    if (badge) badge.textContent = nextState.toUpperCase();
                }}
            }});
        }}

        function syncConnections() {{
            document.querySelectorAll('.conn').forEach((line) => {{
                const when = line.dataset.when || 'always';
                const shouldBeActive = when === 'always' || (when === 'running' && state.running && !state.estop);
                line.classList.toggle('active', shouldBeActive);
            }});
        }}

        function syncAlarms() {{
            const tankHigh = state.tankLevel >= 90;
            document.querySelectorAll('.component[data-type="alarm"]').forEach((el) => {{
                const nextState = tankHigh || state.estop ? 'active' : 'inactive';
                el.dataset.state = nextState;
                el.classList.toggle('alarm-live', nextState === 'active');
                const badge = el.querySelector('.component-state');
                if (badge) badge.textContent = nextState.toUpperCase();
            }});
        }}

        function syncTankValues() {{
            document.querySelectorAll('.component[data-type="tank"]').forEach((el) => {{
                const valueEl = el.querySelector('.component-value');
                if (valueEl) valueEl.textContent = `${{state.tankLevel}} %`;
            }});
        }}

        function startSystem() {{
            state.running = true;
            state.estop = false;
            setComponentState(['pump', 'motor', 'fan', 'compressor'], 'running');
            setComponentState(['valve'], 'open');
            syncConnections();
            syncAlarms();
            updateSummary();
        }}

        function stopSystem() {{
            state.running = false;
            setComponentState(['pump', 'motor', 'fan', 'compressor'], 'stopped');
            setComponentState(['valve'], 'closed');
            syncConnections();
            syncAlarms();
            updateSummary();
        }}

        function emergencyStop() {{
            state.running = false;
            state.estop = true;
            setComponentState(['pump', 'motor', 'fan', 'compressor'], 'stopped');
            setComponentState(['valve'], 'closed');
            syncConnections();
            syncAlarms();
            updateSummary();
        }}

        function resetSystem() {{
            state.estop = false;
            syncConnections();
            syncAlarms();
            updateSummary();
        }}

        function tickSimulation() {{
            if (!state.running || state.estop) return;
            state.tankLevel = Math.max(5, Math.min(100, state.tankLevel + (Math.random() * 8 - 2)));
            state.tankLevel = Math.round(state.tankLevel);
            syncTankValues();
            syncAlarms();
            updateSummary();
        }}

        document.querySelectorAll('.component[data-type="button"]').forEach((el) => {{
            el.addEventListener('click', () => {{
                const label = (el.querySelector('.component-label')?.textContent || '').toLowerCase();
                if (label.includes('start')) startSystem();
                else if (label.includes('emergency') || label.includes('estop')) emergencyStop();
                else if (label.includes('stop')) stopSystem();
            }});
        }});

        syncConnections();
        syncAlarms();
        syncTankValues();
        updateSummary();
        window.setInterval(tickSimulation, 1400);
    </script>
</body>
</html>"""

    return html

def generate_basic_pid(layout):
    """Basic fallback P&ID generator"""
    
    system_name = layout.get('system_name', 'P&ID Diagram')
    components = layout.get('components', [])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{system_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: #0084C7;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .parijat-logo {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            color: white;
            margin-right: 10px;
        }}
        .equipment {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px;
            display: inline-block;
            min-width: 200px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .equipment-name {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .equipment-type {{
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="parijat-logo">P</div>
        <h1>{system_name}</h1>
    </div>
    <div class="equipment-list">"""
    
    for comp in components:
        comp_type = comp.get('type', 'unknown')
        comp_name = comp.get('label', comp.get('name', comp_type.title()))
        comp_state = comp.get('state', 'inactive')
        
        html += f"""
        <div class="equipment">
            <div class="equipment-name">{comp_name}</div>
            <div class="equipment-type">Type: {comp_type} | State: {comp_state}</div>
        </div>"""
    
    html += """
    </div>
</body>
</html>"""
    
    return html
