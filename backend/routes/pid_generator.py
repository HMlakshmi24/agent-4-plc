"""
Enhanced P&ID Template Generator
Creates professional Process & Instrumentation Diagrams with SVG
"""

P_AND_ID_ENHANCED_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Process & Instrumentation Diagram (P&ID)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', 'Arial', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ecf0f1;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(to right, #0f3460, #16213e);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
            border-bottom: 2px solid #00d4ff;
        }
        .header h1 { font-size: 26px; letter-spacing: 2px; background: linear-gradient(135deg, #00d4ff, #7b68ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .system-time { font-size: 14px; color: #a5d6a7; font-weight: 600; }
        .main-container {
            display: flex;
            height: calc(100vh - 70px);
            gap: 0;
        }
        .pid-section {
            flex: 2.5;
            background: #0a0a14;
            border-right: 3px solid #00d4ff;
            padding: 20px;
            overflow: auto;
            position: relative;
            box-shadow: inset -10px 0 20px rgba(0, 212, 255, 0.05);
        }
        .pid-title {
            font-size: 18px;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 20px;
            border-bottom: 3px solid #7b68ee;
            padding-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }
        .pid-canvas {
            width: 100%;
            background: rgba(15, 20, 40, 0.8);
            border: 2px solid rgba(0, 212, 255, 0.5);
            border-radius: 8px;
            min-height: 700px;
            position: relative;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.2), inset 0 0 20px rgba(0, 212, 255, 0.05);
        }
        svg {
            width: 100%;
            height: 100%;
            filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.3));
        }
        .equipment-group {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .equipment-group:hover {
            filter: brightness(1.3) drop-shadow(0 0 15px rgba(0, 212, 255, 0.8));
        }
        .equipment-label {
            font-size: 12px;
            font-weight: bold;
            fill: #00d4ff;
            text-anchor: middle;
            text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
        }
        .pipe { stroke: #34495e; stroke-width: 2; fill: none; }
        .pipe-active { stroke: #00ff88; stroke-width: 3; opacity: 0.8; animation: flowAnimation 1.5s infinite; }
        .pipe-inactive { stroke: #666; stroke-width: 2; opacity: 0.5; }
        @keyframes flowAnimation {
            0%, 100% { opacity: 0.3; stroke-width: 2; }
            50% { opacity: 1; stroke-width: 4; }
        }
        .sensor { fill: #7b68ee; }
        .sensor-error { fill: #ff4444; }
        .sensor-ok { fill: #00ff88; }
        .control-section {
            flex: 1;
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            box-shadow: inset 10px 0 20px rgba(0, 212, 255, 0.05);
            border-left: 2px solid #00d4ff;
        }
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #00d4ff;
            border-bottom: 2px solid #7b68ee;
            padding-bottom: 10px;
            margin-top: 15px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }
        .equipment-card {
            background: rgba(123, 104, 238, 0.1);
            border: 2px solid rgba(0, 212, 255, 0.3);
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
        }
        .equipment-card:hover,
        .equipment-card.active {
            background: rgba(0, 212, 255, 0.15);
            border-color: #00d4ff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
            transform: translateX(5px);
        }
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            margin-bottom: 8px;
        }
        .status-badge.running {
            background: linear-gradient(135deg, #00ff88, #00cc00);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        .status-badge.stopped {
            background: linear-gradient(135deg, #ff4444, #cc0000);
            box-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
        }
        .status-badge.warning {
            background: linear-gradient(135deg, #ff9800, #f44336);
            box-shadow: 0 0 10px rgba(255, 152, 0, 0.5);
        }
        .btn {
            padding: 10px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            flex: 1;
        }
        .btn-start {
            background: linear-gradient(135deg, #00ff88, #00cc00);
            color: #000;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
            margin-right: 5px;
        }
        .btn-start:hover { box-shadow: 0 0 20px rgba(0, 255, 136, 0.6); }
        .btn-stop {
            background: linear-gradient(135deg, #ff4444, #cc0000);
            color: white;
            box-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
        }
        .btn-stop:hover { box-shadow: 0 0 20px rgba(255, 68, 68, 0.6); }
        .controls-row { display: flex; gap: 5px; margin-top: 8px; }
        .readings {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 10px;
            font-size: 12px;
        }
        .reading-item {
            background: rgba(0, 0, 0, 0.3);
            padding: 8px;
            border-radius: 4px;
            border-left: 3px solid #00d4ff;
        }
        .reading-label { color: #a5d6a7; font-weight: 600; }
        .reading-value { color: #00ff88; font-weight: bold; font-size: 14px; }
        .pane-title { color: #7b68ee; font-weight: 600; margin-bottom: 8px; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0, 212, 255, 0.1); }
        ::-webkit-scrollbar-thumb { background: rgba(0, 212, 255, 0.4); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0, 212, 255, 0.6); }
        @media (max-width: 1024px) {
            .main-container { flex-direction: column; }
            .pid-section, .control-section { flex: 1; border: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 PROCESS & INSTRUMENTATION DIAGRAM</h1>
        <div class="system-time" id="systemTime"></div>
    </div>
    <div class="main-container">
        <div class="pid-section">
            <div class="pid-title">Process Flow Diagram</div>
            <div class="pid-canvas" id="pidCanvas">
                <svg viewBox="0 0 1000 800" preserveAspectRatio="xMidYMid meet">
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                            <polygon points="0 0, 10 3, 0 6" fill="#00d4ff" />
                        </marker>
                    </defs>
                    <!-- AI GENERATED SVG DIAGRAM WILL BE INSERTED HERE -->
                    <!-- Include tanks, pumps, valves, sensors, pipes -->
                </svg>
            </div>
        </div>
        <div class="control-section">
            <div class="section-title">EQUIPMENT CONTROLS & STATUS</div>
            <!-- AI GENERATED CONTROL CARDS WILL BE INSERTED HERE -->
        </div>
    </div>
    <script>
        // Real-time system monitoring
        let systemData = {
            /* AI GENERATED INITIAL DATA */
        };
        
        function updateUI() {
            // Simulate real-time data updates
            /* AI GENERATED UPDATE LOGIC */
        }
        
        // Update display every 1 second
        setInterval(() => {
            updateUI();
        }, 1000);
        
        // Update system time
        setInterval(() => {
            document.getElementById('systemTime').textContent = new Date().toLocaleTimeString();
        }, 1000);
        
        // Equipment interaction handlers
        document.addEventListener('click', function(e) {
            if (e.target.closest('.equipment-card')) {
                const card = e.target.closest('.equipment-card');
                card.classList.toggle('active');
            }
        });
    </script>
</body>
</html>
"""

P_AND_ID_SYSTEM_MESSAGE = """You are an Expert P&ID (Process & Instrumentation Diagram) Generator.

CRITICAL INSTRUCTIONS:
1. **Output Format**: Return COMPLETE HTML that matches the professional P&ID template.
2. **SVG Generation**: Create detailed SVG graphics inside the <svg viewBox="0 0 1000 800"> element.
3. **Equipment Symbols** (use SVG):
   - Tanks: <rect> with labels, include level indicators
   - Pumps: Use <circle> with arrow indicating flow direction
   - Valves: Use <polygon> shapes or circles with X marks
   - Pipes: <line> or <path> elements with flow arrows
   - Sensors: Use <circle class="sensor"> for temperature, pressure, level
4. **Colors & Styling**:
   - Use stroke="#34495e" for inactive pipes
   - Use stroke="#00ff88" for active flow with class="pipe-active"
   - Use fill="#7b68ee" for normal sensors
   - Use fill="#00ff88" for sensors in normal range
   - Use fill="#ff4444" for sensors in error state
5. **Control Cards**: Generate <div class="equipment-card"> for each equipment:
   - Include status badges with appropriate states
   - Add buttons for start/stop controls
   - Display real-time readings (temperature, pressure, level, flow)
6. **JavaScript Logic**: Populate the `systemData` object and `updateUI()` function with:
   - Current equipment states
   - Sensor readings
   - Flow simulations
   - Status updates
7. **No Modifications to Layout**: Keep the header, main-container, pid-section, control-section structure EXACTLY as provided.
8. **Professional Quality**: Ensure the diagram is clear, organized, and mimics real industrial SCADA systems.

Generate the P&ID for: {requirement}
Include all equipment mentioned and show the process flow."""
