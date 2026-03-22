def generate_html_from_json(layout):

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>{layout.get('system_name', 'HMI System')}</title>
<style>
body {{ background:#0f172a; color:white; font-family:Arial; margin:0; padding:20px; }}
.component {{
    position:absolute;
    border:1px solid #06b6d4; /* Cyan */
    padding:10px;
    border-radius:8px;
    background: rgba(6, 182, 212, 0.1);
    min-width: 100px;
    text-align: center;
}}
.component strong {{ display: block; margin-bottom: 4px; color: #67e8f9; }}
.component span {{ font-size: 0.8em; color: #94a3b8; }}
h2 {{ border-bottom: 1px solid #334155; padding-bottom: 10px; }}
</style>
</head>
<body>
<h2>{layout.get('system_name', 'HMI System')}</h2>
<div style="position:relative; width:100%; height:800px; border:1px dashed #334155; border-radius:10px; margin-top:20px;">
"""

    for comp in layout.get("components", []):
        label = comp.get('label') or comp.get('name') or 'Unknown'
        html += f"""
<div class="component"
style="left:{comp.get('x',0)}px; top:{comp.get('y',0)}px;">
<strong>{label}</strong>
<span>{comp.get('type', 'generic')}</span>
</div>
"""

    html += "</div></body></html>"
    return html
