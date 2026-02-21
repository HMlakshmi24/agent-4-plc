"""
HMI Export Formatters for Various Platforms
Supports: FactoryTalk, WebForms, Standard HTML, P&ID SVG
"""

from enum import Enum
from datetime import datetime
import json


class ExportFormat(Enum):
    HTML = "html"
    FACTORYTALK = "factorytalk"
    WEBFORMS = "webforms"
    PID = "pid"


class HmiExportFormatter:
    """Converts HMI HTML to platform-specific formats"""

    @staticmethod
    def to_factorytalk(hmi_html: str, hmi_name: str = "HMI_Screen") -> tuple:
        """
        Export HMI to FactoryTalk View format (XAML-compatible HTML)
        Returns: (filename, content_type, formatted_html)
        """
        # FactoryTalk uses tag-based format with specific naming conventions
        factorytalk_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="FactoryTalk-Version" content="7.0">
    <meta name="FactoryTalk-Project" content="{hmi_name}">
    <meta name="FactoryTalk-Type" content="Screen">
    <title>FactoryTalk - {hmi_name}</title>
    <style>
        :root {{
            --ft-primary: #2196F3;
            --ft-danger: #f44336;
            --ft-success: #4caf50;
            --ft-warning: #ff9800;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Arial', sans-serif;
            background: #f5f5f5;
        }}
        .ft-screen {{
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: white;
        }}
        .ft-header {{
            background: linear-gradient(to right, #1a237e, #283593);
            color: white;
            padding: 15px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .ft-header h1 {{
            font-size: 20px;
            margin: 0;
        }}
        .ft-status-bar {{
            background: #eeeeee;
            padding: 8px 20px;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #ddd;
        }}
        .ft-component {{
            border: 2px solid var(--ft-primary);
            border-radius: 4px;
            padding: 8px;
            margin: 8px;
            background: white;
        }}
        .ft-button {{
            background: var(--ft-primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .ft-button:hover {{
            background: #1976d2;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .ft-button.danger {{
            background: var(--ft-danger);
        }}
        .ft-button.success {{
            background: var(--ft-success);
        }}
        .ft-gauge {{
            display: inline-block;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: radial-gradient(circle, #ffeb3b 0%, #fbc02d 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .ft-tank {{
            border: 3px solid #424242;
            border-radius: 10px;
            min-height: 200px;
            position: relative;
            overflow: hidden;
        }}
        .ft-tank-fill {{
            position: absolute;
            bottom: 0;
            width: 100%;
            background: linear-gradient(to right, #4caf50, #8bc34a);
            transition: height 0.5s ease;
        }}
        .ft-alarms {{
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 10px;
            margin: 10px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="ft-screen">
        <div class="ft-header">
            <h1>⚙️ {hmi_name}</h1>
        </div>
        
        <div style="flex: 1; overflow-y: auto;">
            {hmi_html}
        </div>
        
        <div class="ft-status-bar">
            <span>FactoryTalk® View • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Ready</span>
        </div>
    </div>
</body>
</html>"""
        return (f"{hmi_name}_factorytalk.html", "text/html", factorytalk_template)

    @staticmethod
    def to_webforms(hmi_html: str, hmi_name: str = "HmiControl") -> tuple:
        """
        Export HMI to ASP.NET WebForms format
        Returns: (filename, content_type, formatted_html)
        """
        webforms_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="aspnet-version" content="4.7.2">
    <meta name="control-class" content="{hmi_name}Control">
    <title>ASP.NET WebForms - {hmi_name}</title>
    <style>
        :root {{
            --webforms-primary: #0078d4;
            --webforms-secondary: #50e6ff;
            --webforms-danger: #d13438;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background: white;
            color: #333;
        }}
        .aspnet-container {{
            display: grid;
            grid-template-rows: auto 1fr auto;
            min-height: 100vh;
        }}
        .aspnet-header {{
            background: var(--webforms-primary);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .aspnet-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .aspnet-content {{
            padding: 20px;
            overflow-y: auto;
        }}
        .aspnet-button {{
            background: var(--webforms-primary);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .aspnet-button:hover {{
            background: #005a9e;
        }}
        .aspnet-button:active {{
            transform: translateY(1px);
        }}
        .aspnet-textbox {{
            border: 1px solid #d3d3d3;
            padding: 8px 12px;
            border-radius: 2px;
            font-size: 14px;
            width: 100%;
            max-width: 400px;
        }}
        .aspnet-textbox:focus {{
            outline: none;
            border-color: var(--webforms-primary);
            box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.1);
        }}
        .aspnet-label {{
            display: block;
            margin-bottom: 4px;
            font-size: 14px;
            font-weight: 600;
            color: #333;
        }}
        .aspnet-control-container {{
            margin: 16px 0;
            padding: 12px;
            border: 1px solid #d3d3d3;
            border-radius: 2px;
            background: #fafafa;
        }}
        .aspnet-footer {{
            border-top: 1px solid #ebebeb;
            padding: 10px 20px;
            background: #f5f5f5;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="aspnet-container">
        <div class="aspnet-header">
            <h1>🔧 {hmi_name} Control</h1>
        </div>
        
        <div class="aspnet-content">
            {hmi_html}
        </div>
        
        <div class="aspnet-footer">
            <p>© ASP.NET WebForms • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Control ID: {hmi_name}Control</p>
        </div>
    </div>
</body>
</html>"""
        return (f"{hmi_name}_webforms.html", "text/html", webforms_template)

    @staticmethod
    def to_html(hmi_html: str, hmi_name: str = "HMI") -> tuple:
        """Standard HTML export with metadata"""
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Generated HMI Interface - {hmi_name}">
    <meta name="generator" content="Agent4PLC AI HMI Designer">
    <meta name="created" content="{datetime.now().isoformat()}">
    <title>{hmi_name} - Human Machine Interface</title>
</head>
<body>
    {hmi_html}
</body>
</html>"""
        return (f"{hmi_name}.html", "text/html", html_template)

    @staticmethod
    def export(hmi_html: str, format: str = "html", hmi_name: str = "HMI") -> tuple:
        """
        Main export function
        Args:
            hmi_html: Generated HMI HTML content
            format: Export format (html, factorytalk, webforms)
            hmi_name: Project/screen name
        
        Returns:
            (filename, content_type, content)
        """
        format_map = {
            "html": HmiExportFormatter.to_html,
            "factorytalk": HmiExportFormatter.to_factorytalk,
            "webforms": HmiExportFormatter.to_webforms,
        }
        
        formatter = format_map.get(format.lower(), HmiExportFormatter.to_html)
        return formatter(hmi_html, hmi_name)
