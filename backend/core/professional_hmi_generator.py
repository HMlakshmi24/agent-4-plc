"""
Professional HMI Generator - Clean, Industry-Ready Industrial Interfaces
"""

def generate_professional_hmi(layout):
    """Generate clean, professional industrial HMI"""
    
    system_name = layout.get('system_name', 'Industrial HMI')
    theme = layout.get('theme', 'default')
    components = layout.get('components', [])
    
    # Professional color schemes
    themes = {
        'water': {
            'primary': '#0084C7',
            'secondary': '#005A8B', 
            'accent': '#00C896',
            'background': '#F5F7FA',
            'panel_bg': '#FFFFFF',
            'border': '#E1E8ED',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'tank_fill': '#0084C7'
        },
        'default': {
            'primary': '#3498DB',
            'secondary': '#2980B9',
            'accent': '#1ABC9C',
            'background': '#F5F7FA',
            'panel_bg': '#FFFFFF',
            'border': '#E1E8ED',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'tank_fill': '#3498DB'
        }
    }
    
    colors = themes.get(theme, themes['default'])
    
    # Generate clean HTML structure
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{system_name}</title>
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
            background: {colors['panel_bg']};
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
            background: {colors['success']};
            color: white;
        }}
        
        .status-stopped {{
            background: {colors['text_secondary']};
            color: white;
        }}
        
        /* Main Container */
        .main-container {{
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Control Panel */
        .control-panel {{
            background: {colors['panel_bg']};
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
            background: {colors['success']};
            color: white;
        }}
        
        .btn-start:hover {{
            background: #229954;
            transform: translateY(-2px);
        }}
        
        .btn-stop {{
            background: {colors['danger']};
            color: white;
        }}
        
        .btn-stop:hover {{
            background: #C0392B;
            transform: translateY(-2px);
        }}
        
        /* HMI Grid Layout */
        .hmi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        /* Component Cards */
        .component-card {{
            background: {colors['panel_bg']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .component-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            border-color: {colors['primary']};
        }}
        
        .component-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        
        .component-name {{
            font-size: 16px;
            font-weight: 600;
            color: {colors['text_primary']};
        }}
        
        .component-type {{
            font-size: 12px;
            color: {colors['text_secondary']};
            text-transform: uppercase;
            background: {colors['background']};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        /* Component Visual */
        .component-visual {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 80px;
            margin-bottom: 15px;
            position: relative;
        }}
        
        /* Tank Visualization */
        .tank {{
            width: 60px;
            height: 70px;
            border: 3px solid {colors['primary']};
            border-radius: 8px;
            position: relative;
            background: linear-gradient(to top, {colors['tank_fill']}33 0%, transparent 100%);
        }}
        
        .tank-fill {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: {colors['tank_fill']};
            border-radius: 0 0 5px 5px;
            transition: height 0.5s ease;
        }}
        
        /* Pump Visualization */
        .pump {{
            width: 50px;
            height: 50px;
            border: 3px solid {colors['primary']};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        
        .pump.running {{
            animation: rotate 2s linear infinite;
        }}
        
        .pump-icon {{
            font-size: 20px;
            color: {colors['primary']};
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Valve Visualization */
        .valve {{
            width: 40px;
            height: 40px;
            border: 3px solid {colors['accent']};
            transform: rotate(45deg);
            border-radius: 4px;
        }}
        
        .valve.open {{
            background: {colors['accent']};
        }}
        
        /* Sensor Visualization */
        .sensor {{
            width: 40px;
            height: 40px;
            border: 3px solid {colors['warning']};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .sensor-icon {{
            font-size: 16px;
            color: {colors['warning']};
        }}
        
        /* Gauge Visualization */
        .gauge {{
            width: 60px;
            height: 60px;
            border: 3px solid {colors['text_secondary']};
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .gauge-value {{
            font-size: 14px;
            font-weight: bold;
            color: {colors['text_primary']};
        }}
        
        /* Alarm Visualization */
        .alarm {{
            width: 0;
            height: 0;
            border-left: 20px solid transparent;
            border-right: 20px solid transparent;
            border-bottom: 35px solid {colors['danger']};
            position: relative;
        }}
        
        .alarm.active {{
            animation: blink 1s infinite;
        }}
        
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        
        /* Button Visualization */
        .button {{
            padding: 10px 20px;
            border: 2px solid {colors['primary']};
            border-radius: 6px;
            background: {colors['panel_bg']};
            color: {colors['primary']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .button:hover {{
            background: {colors['primary']};
            color: white;
        }}
        
        .button.start {{
            border-color: {colors['success']};
            color: {colors['success']};
        }}
        
        .button.start:hover {{
            background: {colors['success']};
            color: white;
        }}
        
        .button.stop {{
            border-color: {colors['danger']};
            color: {colors['danger']};
        }}
        
        .button.stop:hover {{
            background: {colors['danger']};
            color: white;
        }}
        
        /* Component Info */
        .component-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .component-value {{
            font-size: 18px;
            font-weight: bold;
            color: {colors['primary']};
        }}
        
        .component-state {{
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .state-active {{
            background: {colors['success']};
            color: white;
        }}
        
        .state-inactive {{
            background: {colors['text_secondary']};
            color: white;
        }}
        
        .state-running {{
            background: {colors['success']};
            color: white;
        }}
        
        .state-stopped {{
            background: {colors['text_secondary']};
            color: white;
        }}
        
        .state-open {{
            background: {colors['accent']};
            color: white;
        }}
        
        .state-closed {{
            background: {colors['text_secondary']};
            color: white;
        }}
        
        /* Alarm Panel */
        .alarm-panel {{
            background: {colors['panel_bg']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .alarm-header {{
            font-size: 18px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .alarm-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .alarm-item {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 10px;
            background: {colors['background']};
            border-radius: 6px;
            border-left: 4px solid {colors['danger']};
        }}
        
        .alarm-item.critical {{
            border-left-color: {colors['danger']};
        }}
        
        .alarm-item.warning {{
            border-left-color: {colors['warning']};
        }}
        
        .alarm-item.info {{
            border-left-color: {colors['primary']};
        }}
        
        .alarm-time {{
            font-size: 12px;
            color: {colors['text_secondary']};
        }}
        
        .alarm-message {{
            flex: 1;
            font-size: 14px;
            color: {colors['text_primary']};
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .hmi-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .control-buttons {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <div class="parijat-logo">P</div>
            <h1 class="system-title">{system_name}</h1>
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
        
        <div class="hmi-grid">"""
    
    # Generate component cards
    for comp in components:
        comp_type = comp.get('type', 'unknown')
        comp_name = comp.get('label', comp.get('name', comp_type.title()))
        comp_state = comp.get('state', 'inactive')
        comp_value = comp.get('value', None)
        
        # Generate component visual
        visual_html = ""
        if comp_type == 'tank':
            fill_height = comp_value if comp_value else 50
            visual_html = f"""
                <div class="tank">
                    <div class="tank-fill" style="height: {fill_height}%"></div>
                </div>"""
        elif comp_type == 'pump':
            running_class = "running" if comp_state == 'running' else ""
            visual_html = f"""
                <div class="pump {running_class}">
                    <div class="pump-icon"></div>
                </div>"""
        elif comp_type == 'valve':
            open_class = "open" if comp_state == 'open' else ""
            visual_html = f'<div class="valve {open_class}"></div>'
        elif comp_type in ['sensor', 'sensor_level', 'sensor_flow', 'sensor_temp']:
            visual_html = """
                <div class="sensor">
                    <div class="sensor-icon"></div>
                </div>"""
        elif comp_type == 'gauge':
            visual_html = f"""
                <div class="gauge">
                    <div class="gauge-value">{comp_value if comp_value else 0}</div>
                </div>"""
        elif comp_type == 'alarm':
            active_class = "active" if comp_state == 'active' else ""
            visual_html = f'<div class="alarm {active_class}"></div>'
        elif comp_type == 'button':
            button_type = "start" if "start" in comp_name.lower() else "stop" if "stop" in comp_name.lower() else ""
            visual_html = f'<div class="button {button_type}">{comp_name}</div>'
        else:
            visual_html = f'<div class="component-type">{comp_type}</div>'
        
        # Generate state class
        state_class = f"state-{comp_state}" if comp_state in ['active', 'inactive', 'running', 'stopped', 'open', 'closed'] else "state-inactive"
        
        # Generate value display
        value_display = ""
        if comp_value is not None:
            if comp_type == 'tank':
                value_display = f'<div class="component-value">{comp_value}%</div>'
            elif comp_type == 'gauge':
                value_display = f'<div class="component-value">{comp_value} L/min</div>'
            else:
                value_display = f'<div class="component-value">{comp_value}</div>'
        
        html += f"""
            <div class="component-card" data-type="{comp_type}" data-name="{comp_name}" onclick="toggleComponent(this)">
                <div class="component-header">
                    <div class="component-name">{comp_name}</div>
                    <div class="component-type">{comp_type}</div>
                </div>
                <div class="component-visual">
                    {visual_html}
                </div>
                <div class="component-info">
                    {value_display}
                    <div class="component-state {state_class}">{comp_state}</div>
                </div>
            </div>"""
    
    html += """
        </div>
        
        <div class="alarm-panel">
            <div class="alarm-header">
                <span></span>
                <span>System Alarms</span>
            </div>
            <div class="alarm-list" id="alarmList">
                <div class="alarm-item info">
                    <div class="alarm-time">10:30:45</div>
                    <div class="alarm-message">System initialized successfully</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let systemRunning = false;
        let componentStates = {};
        
        // Initialize component states
        document.querySelectorAll('.component-card').forEach(card => {
            const name = card.getAttribute('data-name');
            const type = card.getAttribute('data-type');
            componentStates[name] = {
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
            
            // Update all components
            document.querySelectorAll('.component-card').forEach(card => {
                const type = card.getAttribute('data-type');
                const stateDiv = card.querySelector('.component-state');
                const visual = card.querySelector('.component-visual');
                
                if (type === 'pump') {
                    const pump = visual.querySelector('.pump');
                    if (pump) {
                        pump.classList.add('running');
                        stateDiv.className = 'component-state state-running';
                        stateDiv.textContent = 'RUNNING';
                    }
                } else if (type === 'valve') {
                    const valve = visual.querySelector('.valve');
                    if (valve) {
                        valve.classList.add('open');
                        stateDiv.className = 'component-state state-open';
                        stateDiv.textContent = 'OPEN';
                    }
                } else if (type === 'tank') {
                    stateDiv.className = 'component-state state-active';
                    stateDiv.textContent = 'ACTIVE';
                }
            });
            
            addAlarm('info', 'System started successfully');
        }
        
        // Stop System
        function stopSystem() {
            systemRunning = false;
            document.getElementById('systemStatus').className = 'status-indicator status-stopped';
            document.getElementById('systemStatus').textContent = 'STOPPED';
            
            // Update all components
            document.querySelectorAll('.component-card').forEach(card => {
                const type = card.getAttribute('data-type');
                const stateDiv = card.querySelector('.component-state');
                const visual = card.querySelector('.component-visual');
                
                if (type === 'pump') {
                    const pump = visual.querySelector('.pump');
                    if (pump) {
                        pump.classList.remove('running');
                        stateDiv.className = 'component-state state-stopped';
                        stateDiv.textContent = 'STOPPED';
                    }
                } else if (type === 'valve') {
                    const valve = visual.querySelector('.valve');
                    if (valve) {
                        valve.classList.remove('open');
                        stateDiv.className = 'component-state state-closed';
                        stateDiv.textContent = 'CLOSED';
                    }
                } else if (type === 'tank') {
                    stateDiv.className = 'component-state state-inactive';
                    stateDiv.textContent = 'INACTIVE';
                }
            });
            
            addAlarm('warning', 'System stopped');
        }
        
        // Toggle Component
        function toggleComponent(card) {
            const type = card.getAttribute('data-type');
            const name = card.getAttribute('data-name');
            const stateDiv = card.querySelector('.component-state');
            const visual = card.querySelector('.component-visual');
            
            if (type === 'button') {
                if (name.toLowerCase().includes('start')) {
                    startSystem();
                } else if (name.toLowerCase().includes('stop')) {
                    stopSystem();
                }
                return;
            }
            
            if (type === 'pump') {
                const pump = visual.querySelector('.pump');
                if (pump.classList.contains('running')) {
                    pump.classList.remove('running');
                    stateDiv.className = 'component-state state-stopped';
                    stateDiv.textContent = 'STOPPED';
                    addAlarm('info', `${name} stopped`);
                } else {
                    pump.classList.add('running');
                    stateDiv.className = 'component-state state-running';
                    stateDiv.textContent = 'RUNNING';
                    addAlarm('info', `${name} started`);
                }
            } else if (type === 'valve') {
                const valve = visual.querySelector('.valve');
                if (valve.classList.contains('open')) {
                    valve.classList.remove('open');
                    stateDiv.className = 'component-state state-closed';
                    stateDiv.textContent = 'CLOSED';
                    addAlarm('info', `${name} closed`);
                } else {
                    valve.classList.add('open');
                    stateDiv.className = 'component-state state-open';
                    stateDiv.textContent = 'OPEN';
                    addAlarm('info', `${name} opened`);
                }
            } else if (type === 'alarm') {
                const alarm = visual.querySelector('.alarm');
                if (alarm.classList.contains('active')) {
                    alarm.classList.remove('active');
                    stateDiv.className = 'component-state state-inactive';
                    stateDiv.textContent = 'INACTIVE';
                    addAlarm('info', `${name} cleared`);
                } else {
                    alarm.classList.add('active');
                    stateDiv.className = 'component-state state-active';
                    stateDiv.textContent = 'ACTIVE';
                    addAlarm('critical', `${name} triggered!`);
                }
            }
        }
        
        // Add Alarm
        function addAlarm(type, message) {
            const alarmList = document.getElementById('alarmList');
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            const alarmItem = document.createElement('div');
            alarmItem.className = `alarm-item ${type}`;
            alarmItem.innerHTML = `
                <div class="alarm-time">${timeString}</div>
                <div class="alarm-message">${message}</div>
            `;
            
            alarmList.insertBefore(alarmItem, alarmList.firstChild);
            
            // Keep only last 10 alarms
            while (alarmList.children.length > 10) {
                alarmList.removeChild(alarmList.lastChild);
            }
        }
        
        // Simulate tank level changes
        setInterval(() => {
            if (systemRunning) {
                document.querySelectorAll('.component-card').forEach(card => {
                    const type = card.getAttribute('data-type');
                    if (type === 'tank') {
                        const tankFill = card.querySelector('.tank-fill');
                        const valueDiv = card.querySelector('.component-value');
                        if (tankFill && valueDiv) {
                            const currentHeight = parseInt(tankFill.style.height) || 50;
                            const newHeight = Math.max(10, Math.min(90, currentHeight + (Math.random() - 0.5) * 10));
                            tankFill.style.height = newHeight + '%';
                            valueDiv.textContent = Math.round(newHeight) + '%';
                        }
                    }
                });
            }
        }, 3000);
    </script>
</body>
</html>"""
    
    return html
