"""
Professional P&ID Generator - Clean, Industry-Ready P&ID Diagrams
"""

def generate_professional_pid(layout):
    """Generate clean, professional P&ID diagram"""
    
    system_name = layout.get('system_name', 'P&ID Diagram')
    theme = layout.get('theme', 'default')
    components = layout.get('components', [])
    
    # Professional color schemes for P&ID
    themes = {
        'water': {
            'primary': '#0084C7',
            'secondary': '#005A8B', 
            'accent': '#00C896',
            'background': '#FFFFFF',
            'canvas_bg': '#F8FAFB',
            'border': '#E1E8ED',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'pipe': '#34495E',
            'instrument': '#E74C3C',
            'equipment': '#95A5A6'
        },
        'default': {
            'primary': '#3498DB',
            'secondary': '#2980B9',
            'accent': '#1ABC9C',
            'background': '#FFFFFF',
            'canvas_bg': '#F8FAFB',
            'border': '#E1E8ED',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'pipe': '#34495E',
            'instrument': '#E74C3C',
            'equipment': '#95A5A6'
        }
    }
    
    colors = themes.get(theme, themes['default'])
    
    # Generate clean P&ID HTML structure
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{system_name} - P&ID Diagram</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: {colors['background']};
            color: {colors['text_primary']};
            overflow-x: hidden;
        }}
        
        /* Header */
        .header {{
            background: {colors['canvas_bg']};
            border-bottom: 3px solid {colors['primary']};
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header-left {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .parijat-logo {{
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            color: white;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            box-shadow: 0 3px 12px rgba(255, 107, 53, 0.6);
            font-family: 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }}
        
        .system-title {{
            font-size: 24px;
            font-weight: 600;
            color: {colors['text_primary']};
        }}
        
        .status-bar {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .status-indicator {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .status-running {{
            background: #27AE60;
            color: white;
        }}
        
        .status-stopped {{
            background: {colors['text_secondary']};
            color: white;
        }}
        
        /* Main Container */
        .main-container {{
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        /* Control Panel */
        .control-panel {{
            background: {colors['canvas_bg']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .control-buttons {{
            display: flex;
            gap: 15px;
            justify-content: center;
        }}
        
        .control-btn {{
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.3s ease;
        }}
        
        .btn-start {{
            background: #27AE60;
            color: white;
        }}
        
        .btn-start:hover {{
            background: #229954;
            transform: translateY(-2px);
        }}
        
        .btn-stop {{
            background: #E74C3C;
            color: white;
        }}
        
        .btn-stop:hover {{
            background: #C0392B;
            transform: translateY(-2px);
        }}
        
        /* P&ID Canvas */
        .pid-canvas {{
            background: {colors['canvas_bg']};
            border: 2px solid {colors['border']};
            border-radius: 12px;
            padding: 40px;
            min-height: 600px;
            position: relative;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: auto;
        }}
        
        /* P&ID Grid Layout */
        .pid-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 40px;
            align-items: start;
        }}
        
        /* P&ID Equipment Cards */
        .equipment-card {{
            background: white;
            border: 2px solid {colors['border']};
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .equipment-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: {colors['primary']};
        }}
        
        .equipment-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            border-bottom: 2px solid {colors['border']};
            padding-bottom: 15px;
        }}
        
        .equipment-name {{
            font-size: 18px;
            font-weight: 700;
            color: {colors['text_primary']};
        }}
        
        .equipment-tag {{
            font-size: 12px;
            color: {colors['text_secondary']};
            text-transform: uppercase;
            background: {colors['canvas_bg']};
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
        }}
        
        /* P&ID Symbol Styles */
        .pid-symbol {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 120px;
            margin-bottom: 20px;
            position: relative;
        }}
        
        /* Tank Symbol */
        .tank-symbol {{
            width: 80px;
            height: 100px;
            border: 4px solid {colors['equipment']};
            border-radius: 8px;
            position: relative;
            background: linear-gradient(to top, {colors['primary']}20 0%, transparent 100%);
        }}
        
        .tank-fill {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: {colors['primary']};
            border-radius: 0 0 4px 4px;
            transition: height 0.5s ease;
            opacity: 0.7;
        }}
        
        .tank-level {{
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            font-weight: bold;
            color: {colors['text_primary']};
        }}
        
        /* Pump Symbol */
        .pump-symbol {{
            width: 70px;
            height: 70px;
            border: 4px solid {colors['equipment']};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            background: {colors['canvas_bg']};
        }}
        
        .pump-symbol.running {{
            animation: rotate 2s linear infinite;
            border-color: {colors['primary']};
        }}
        
        .pump-icon {{
            font-size: 24px;
            color: {colors['equipment']};
        }}
        
        .pump-symbol.running .pump-icon {{
            color: {colors['primary']};
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Valve Symbol */
        .valve-symbol {{
            width: 60px;
            height: 60px;
            border: 4px solid {colors['accent']};
            transform: rotate(45deg);
            border-radius: 8px;
            background: {colors['canvas_bg']};
            position: relative;
        }}
        
        .valve-symbol.open {{
            background: {colors['accent']};
            opacity: 0.3;
        }}
        
        /* Instrument Symbol */
        .instrument-symbol {{
            width: 50px;
            height: 50px;
            border: 3px solid {colors['instrument']};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            position: relative;
        }}
        
        .instrument-tag {{
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            font-weight: bold;
            color: {colors['instrument']};
            background: white;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid {colors['instrument']};
        }}
        
        /* Sensor Symbol */
        .sensor-symbol {{
            width: 40px;
            height: 40px;
            border: 3px solid {colors['accent']};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
        }}
        
        .sensor-icon {{
            font-size: 16px;
            color: {colors['accent']};
        }}
        
        /* Gauge Symbol */
        .gauge-symbol {{
            width: 60px;
            height: 60px;
            border: 3px solid {colors['text_secondary']};
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
        }}
        
        .gauge-needle {{
            position: absolute;
            width: 2px;
            height: 25px;
            background: {colors['text_secondary']};
            transform-origin: bottom center;
            transition: transform 0.5s ease;
        }}
        
        .gauge-value {{
            font-size: 12px;
            font-weight: bold;
            color: {colors['text_primary']};
            z-index: 1;
        }}
        
        /* Alarm Symbol */
        .alarm-symbol {{
            width: 0;
            height: 0;
            border-left: 25px solid transparent;
            border-right: 25px solid transparent;
            border-bottom: 40px solid {colors['instrument']};
            position: relative;
        }}
        
        .alarm-symbol.active {{
            animation: blink 1s infinite;
        }}
        
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        
        /* Button Symbol */
        .button-symbol {{
            padding: 12px 24px;
            border: 2px solid {colors['primary']};
            border-radius: 8px;
            background: white;
            color: {colors['primary']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .button-symbol:hover {{
            background: {colors['primary']};
            color: white;
        }}
        
        .button-symbol.start {{
            border-color: #27AE60;
            color: #27AE60;
        }}
        
        .button-symbol.start:hover {{
            background: #27AE60;
            color: white;
        }}
        
        .button-symbol.stop {{
            border-color: #E74C3C;
            color: #E74C3C;
        }}
        
        .button-symbol.stop:hover {{
            background: #E74C3C;
            color: white;
        }}
        
        /* Equipment Info */
        .equipment-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .info-label {{
            font-size: 11px;
            color: {colors['text_secondary']};
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .info-value {{
            font-size: 14px;
            font-weight: 600;
            color: {colors['text_primary']};
        }}
        
        .state-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .state-active {{
            background: #D5F4E6;
            color: #27AE60;
        }}
        
        .state-inactive {{
            background: #F4F6F7;
            color: {colors['text_secondary']};
        }}
        
        .state-running {{
            background: #D5F4E6;
            color: #27AE60;
        }}
        
        .state-stopped {{
            background: #F4F6F7;
            color: {colors['text_secondary']};
        }}
        
        .state-open {{
            background: #D5F4E6;
            color: {colors['accent']};
        }}
        
        .state-closed {{
            background: #F4F6F7;
            color: {colors['text_secondary']};
        }}
        
        /* Connection Lines */
        .connection-line {{
            position: absolute;
            background: {colors['pipe']};
            z-index: -1;
        }}
        
        .horizontal-line {{
            height: 4px;
            width: 100px;
        }}
        
        .vertical-line {{
            width: 4px;
            height: 100px;
        }}
        
        /* Legend */
        .legend {{
            background: white;
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .legend-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            color: {colors['text_primary']};
        }}
        
        .legend-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-symbol {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        
        .legend-text {{
            font-size: 12px;
            color: {colors['text_secondary']};
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .pid-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .control-buttons {{
                flex-direction: column;
            }}
            
            .equipment-info {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <div class="parijat-logo">P</div>
            <h1 class="system-title">{system_name} - P&ID Diagram</h1>
        </div>
        <div class="status-bar">
            <div class="status-indicator status-stopped" id="systemStatus">STOPPED</div>
            <div id="currentTime"></div>
        </div>
    </div>
    
    <div class="main-container">
        <div class="control-panel">
            <div class="control-buttons">
                <button class="control-btn btn-start" onclick="startSystem()">START SYSTEM</button>
                <button class="control-btn btn-stop" onclick="stopSystem()">STOP SYSTEM</button>
            </div>
        </div>
        
        <div class="pid-canvas">
            <div class="pid-grid">"""
    
    # Generate equipment cards
    for comp in components:
        comp_type = comp.get('type', 'unknown')
        comp_name = comp.get('label', comp.get('name', comp_type.title()))
        comp_state = comp.get('state', 'inactive')
        comp_value = comp.get('value', None)
        
        # Generate P&ID symbol
        symbol_html = ""
        if comp_type == 'tank':
            fill_height = comp_value if comp_value else 50
            symbol_html = f"""
                <div class="tank-symbol">
                    <div class="tank-fill" style="height: {fill_height}%"></div>
                    <div class="tank-level">{fill_height}%</div>
                </div>"""
        elif comp_type == 'pump':
            running_class = "running" if comp_state == 'running' else ""
            symbol_html = f"""
                <div class="pump-symbol {running_class}">
                    <div class="pump-icon"></div>
                </div>"""
        elif comp_type == 'valve':
            open_class = "open" if comp_state == 'open' else ""
            symbol_html = f'<div class="valve-symbol {open_class}"></div>'
        elif comp_type in ['sensor', 'sensor_level', 'sensor_flow', 'sensor_temp']:
            symbol_html = f"""
                <div class="instrument-symbol">
                    <div class="instrument-tag">LT</div>
                    <div class="sensor-icon"></div>
                </div>"""
        elif comp_type == 'gauge':
            symbol_html = f"""
                <div class="gauge-symbol">
                    <div class="gauge-needle" style="transform: rotate({comp_value if comp_value else 0}deg)"></div>
                    <div class="gauge-value">{comp_value if comp_value else 0}</div>
                </div>"""
        elif comp_type == 'alarm':
            active_class = "active" if comp_state == 'active' else ""
            symbol_html = f'<div class="alarm-symbol {active_class}"></div>'
        elif comp_type == 'button':
            button_type = "start" if "start" in comp_name.lower() else "stop" if "stop" in comp_name.lower() else ""
            symbol_html = f'<div class="button-symbol {button_type}">{comp_name}</div>'
        else:
            symbol_html = f'<div class="equipment-tag">{comp_type}</div>'
        
        # Generate state class
        state_class = f"state-{comp_state}" if comp_state in ['active', 'inactive', 'running', 'stopped', 'open', 'closed'] else "state-inactive"
        
        # Generate value display
        value_display = ""
        if comp_value is not None:
            if comp_type == 'tank':
                value_display = f'<div class="info-value">{comp_value}%</div>'
            elif comp_type == 'gauge':
                value_display = f'<div class="info-value">{comp_value} L/min</div>'
            else:
                value_display = f'<div class="info-value">{comp_value}</div>'
        
        html += f"""
                <div class="equipment-card" data-type="{comp_type}" data-name="{comp_name}" onclick="toggleEquipment(this)">
                    <div class="equipment-header">
                        <div class="equipment-name">{comp_name}</div>
                        <div class="equipment-tag">{comp_type.upper()}</div>
                    </div>
                    <div class="pid-symbol">
                        {symbol_html}
                    </div>
                    <div class="equipment-info">
                        <div class="info-item">
                            <div class="info-label">Status</div>
                            <div class="info-value">
                                <span class="state-badge {state_class}">{comp_state}</span>
                            </div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Value</div>
                            <div class="info-value">
                                {value_display if value_display else 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>"""
    
    html += """
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title">P&ID Legend</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #95A5A6;"></div>
                    <div class="legend-text">Equipment (Tank, Vessel)</div>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #0084C7;"></div>
                    <div class="legend-text">Pump/Compressor</div>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #00C896;"></div>
                    <div class="legend-text">Valve</div>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #E74C3C;"></div>
                    <div class="legend-text">Instrument/Alarm</div>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #34495E;"></div>
                    <div class="legend-text">Pipe/Connection</div>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol" style="background: #F39C12;"></div>
                    <div class="legend-text">Sensor</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let systemRunning = false;
        let equipmentStates = {};
        
        // Initialize equipment states
        document.querySelectorAll('.equipment-card').forEach(card => {
            const name = card.getAttribute('data-name');
            const type = card.getAttribute('data-type');
            equipmentStates[name] = {
                type: type,
                state: card.getAttribute('data-state') || 'inactive',
                value: card.getAttribute('data-value') || null
            };
        });
        
        // Update current time
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            document.getElementById('currentTime').textContent = timeString;
        }
        
        setInterval(updateTime, 1000);
        updateTime();
        
        // Start System
        function startSystem() {
            systemRunning = true;
            document.getElementById('systemStatus').className = 'status-indicator status-running';
            document.getElementById('systemStatus').textContent = 'RUNNING';
            
            // Update all equipment
            document.querySelectorAll('.equipment-card').forEach(card => {
                const type = card.getAttribute('data-type');
                const stateBadge = card.querySelector('.state-badge');
                const symbol = card.querySelector('.pid-symbol');
                
                if (type === 'pump') {
                    const pump = symbol.querySelector('.pump-symbol');
                    if (pump) {
                        pump.classList.add('running');
                        stateBadge.className = 'state-badge state-running';
                        stateBadge.textContent = 'RUNNING';
                    }
                } else if (type === 'valve') {
                    const valve = symbol.querySelector('.valve-symbol');
                    if (valve) {
                        valve.classList.add('open');
                        stateBadge.className = 'state-badge state-open';
                        stateBadge.textContent = 'OPEN';
                    }
                } else if (type === 'tank') {
                    stateBadge.className = 'state-badge state-active';
                    stateBadge.textContent = 'ACTIVE';
                }
            });
        }
        
        // Stop System
        function stopSystem() {
            systemRunning = false;
            document.getElementById('systemStatus').className = 'status-indicator status-stopped';
            document.getElementById('systemStatus').textContent = 'STOPPED';
            
            // Update all equipment
            document.querySelectorAll('.equipment-card').forEach(card => {
                const type = card.getAttribute('data-type');
                const stateBadge = card.querySelector('.state-badge');
                const symbol = card.querySelector('.pid-symbol');
                
                if (type === 'pump') {
                    const pump = symbol.querySelector('.pump-symbol');
                    if (pump) {
                        pump.classList.remove('running');
                        stateBadge.className = 'state-badge state-stopped';
                        stateBadge.textContent = 'STOPPED';
                    }
                } else if (type === 'valve') {
                    const valve = symbol.querySelector('.valve-symbol');
                    if (valve) {
                        valve.classList.remove('open');
                        stateBadge.className = 'state-badge state-closed';
                        stateBadge.textContent = 'CLOSED';
                    }
                } else if (type === 'tank') {
                    stateBadge.className = 'state-badge state-inactive';
                    stateBadge.textContent = 'INACTIVE';
                }
            });
        }
        
        // Toggle Equipment
        function toggleEquipment(card) {
            const type = card.getAttribute('data-type');
            const name = card.getAttribute('data-name');
            const stateBadge = card.querySelector('.state-badge');
            const symbol = card.querySelector('.pid-symbol');
            
            if (type === 'button') {
                if (name.toLowerCase().includes('start')) {
                    startSystem();
                } else if (name.toLowerCase().includes('stop')) {
                    stopSystem();
                }
                return;
            }
            
            if (type === 'pump') {
                const pump = symbol.querySelector('.pump-symbol');
                if (pump.classList.contains('running')) {
                    pump.classList.remove('running');
                    stateBadge.className = 'state-badge state-stopped';
                    stateBadge.textContent = 'STOPPED';
                } else {
                    pump.classList.add('running');
                    stateBadge.className = 'state-badge state-running';
                    stateBadge.textContent = 'RUNNING';
                }
            } else if (type === 'valve') {
                const valve = symbol.querySelector('.valve-symbol');
                if (valve.classList.contains('open')) {
                    valve.classList.remove('open');
                    stateBadge.className = 'state-badge state-closed';
                    stateBadge.textContent = 'CLOSED';
                } else {
                    valve.classList.add('open');
                    stateBadge.className = 'state-badge state-open';
                    stateBadge.textContent = 'OPEN';
                }
            } else if (type === 'alarm') {
                const alarm = symbol.querySelector('.alarm-symbol');
                if (alarm.classList.contains('active')) {
                    alarm.classList.remove('active');
                    stateBadge.className = 'state-badge state-inactive';
                    stateBadge.textContent = 'INACTIVE';
                } else {
                    alarm.classList.add('active');
                    stateBadge.className = 'state-badge state-active';
                    stateBadge.textContent = 'ACTIVE';
                }
            }
        }
        
        // Simulate tank level changes
        setInterval(() => {
            if (systemRunning) {
                document.querySelectorAll('.equipment-card').forEach(card => {
                    const type = card.getAttribute('data-type');
                    if (type === 'tank') {
                        const tankFill = card.querySelector('.tank-fill');
                        const tankLevel = card.querySelector('.tank-level');
                        const valueDisplay = card.querySelector('.info-value');
                        if (tankFill && tankLevel && valueDisplay) {
                            const currentHeight = parseInt(tankFill.style.height) || 50;
                            const newHeight = Math.max(10, Math.min(90, currentHeight + (Math.random() - 0.5) * 10));
                            tankFill.style.height = newHeight + '%';
                            tankLevel.textContent = Math.round(newHeight) + '%';
                            valueDisplay.textContent = Math.round(newHeight) + '%';
                        }
                    }
                });
            }
        }, 4000);
    </script>
</body>
</html>"""
    
    return html
