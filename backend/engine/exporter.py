
import json

def export_hmi_html(layout_data):
    # This is a placeholder for generating a standalone HTML file
    # In a real engine, we'd inject the React runtime or a lightweight JS renderer
    # For now, we output a simple HTML representation
    
    components_html = ""
    for comp in layout_data.get("components", []):
        style = f"position:absolute; left:{comp['x']}px; top:{comp['y']}px; border:1px solid #ccc; padding:5px;"
        components_html += f"<div style='{style}'><strong>{comp['name']}</strong><br><small>{comp['type']}</small></div>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{layout_data.get('system_name', 'HMI')}</title>
    <style>
        body {{ background-color: #1e293b; color: white; font-family: sans-serif; }}
        #app {{ position: relative; width: 100vw; height: 100vh; }}
    </style>
</head>
<body>
<h1>{layout_data.get('system_name')}</h1>
<div id="app">
    {components_html}
</div>
<script>
var layout = {json.dumps(layout_data)};
console.log("Loaded layout", layout);
</script>
</body>
</html>
"""
    return html


def export_factorytalk_xml(layout_data):
    # Mock FactoryTalk XML structure
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<FactoryTalkScreen name="{layout_data.get('system_name')}">
    <Components>
"""
    for comp in layout_data.get("components", []):
        xml += f"""        <Component type="{comp['type']}" name="{comp['name']}">
            <Position x="{comp['x']}" y="{comp['y']}" />
        </Component>
"""
    xml += """    </Components>
</FactoryTalkScreen>"""
    return xml


def export_webforms_aspx(layout_data):
    # Mock ASP.NET WebForms structure
    aspx = f"""<%@ Page Language="C#" AutoEventWireup="true" %>
<!DOCTYPE html>
<html>
<head><title>{layout_data.get('system_name')}</title></head>
<body>
    <form id="form1" runat="server">
        <asp:Panel ID="MainPanel" runat="server" Height="100%" Width="100%">
"""
    for comp in layout_data.get("components", []):
         aspx += f"""            <asp:Label ID="{comp['id']}" runat="server" Text="{comp['name']}" style="position:absolute; left:{comp['x']}px; top:{comp['y']}px;" />
"""
    aspx += """        </asp:Panel>
    </form>
</body>
</html>"""
    return aspx
