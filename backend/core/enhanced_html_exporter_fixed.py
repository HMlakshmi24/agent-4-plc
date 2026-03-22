"""
Enhanced HTML Exporter - Industrial P&ID symbols with FULL interactivity and simulation
"""

def generate_enhanced_html_from_json(layout):
    """Generate enhanced HTML with proper industrial HMI symbols and full interactivity"""
    
    # Use the industrial symbol exporter (interactive HMI)
    try:
        from .enhanced_html_exporter import generate_enhanced_html_from_json as render_hmi
        return render_hmi(layout)
    except ImportError as e:
        print(f"Import error: {e}")
        # Fallback to basic implementation if professional generator is not available
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
    """Basic fallback HMI generator"""
    
    system_name = layout.get('system_name', 'HMI System')
    theme = layout.get('theme', 'default')
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
        .component {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px;
            display: inline-block;
            min-width: 200px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .component-name {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .component-state {{
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
    <div class="components">"""
    
    for comp in components:
        comp_type = comp.get('type', 'unknown')
        comp_name = comp.get('label', comp.get('name', comp_type.title()))
        comp_state = comp.get('state', 'inactive')
        
        html += f"""
        <div class="component">
            <div class="component-name">{comp_name}</div>
            <div class="component-state">Type: {comp_type} | State: {comp_state}</div>
        </div>"""
    
    html += """
    </div>
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
