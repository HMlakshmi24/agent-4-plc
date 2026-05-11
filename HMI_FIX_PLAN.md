do# HMI & P&ID Fix Plan

## Issues to Fix:

### 1. HMI Symbol Names - Messy/Unclear (Issue #1)
- **Problem**: Symbols look cluttered with unclear labels
- **Solution**: 
  - Improve symbol designs in DashboardRenderer.jsx with cleaner, industry-standard look
  - Add clear component type indicators (M for Motor, P for Pump, etc.)
  - Better color coding for states (green=running, red=stopped)
  - Improve label positioning and styling

### 2. Motor Start/Stop Interaction (Issue #2)
- **Problem**: START button doesn't actually start motor, STOP doesn't stop
- **Solution**:
  - In PIDRenderer.jsx: Connect START button to set simState.pumpRunning = true
  - Connect STOP button to set simState.pumpRunning = false
  - In HTML exporter: StartSystem() should start all motors/pumps/fans
  - StopSystem() should stop all motors/pumps/fans

### 3. Alarm Blinking Issue (Issue #3)
- **Problem**: Alarm continuously blinks even when inactive
- **Solution**:
  - In DashboardRenderer.jsx HMI_Alarm: Only apply pulse animation when alarmState === 'active'
  - In PIDRenderer.jsx: Only apply animation when isActive === true
  - In HTML exporter: Only add 'pulsing' class when alarm is active

### 4. Clumsy P&ID View (Issue #4)
- **Problem**: Components look cluttered, poor spacing
- **Solution**:
  - Improve component spacing in PIDRenderer.jsx
  - Add proper grid alignment
  - Clean up component styling
  - Better visual hierarchy

## Files to Modify:

1. **agent-4-plc/frontend/src/components/DashboardRenderer.jsx**
   - Fix alarm blinking
   - Improve symbol designs and labels

2. **agent-4-plc/frontend/src/components/PIDRenderer.jsx**
   - Fix alarm blinking  
   - Fix START/STOP button functionality
   - Clean up P&ID layout

3. **agent-4-plc/backend/core/enhanced_html_exporter.py**
   - Fix alarm animation to only trigger when active
   - Ensure START/STOP controls all machines properly

## Implementation Steps:

1. Fix alarm blinking in DashboardRenderer.jsx
2. Fix alarm blinking in PIDRenderer.jsx
3. Fix alarm blinking in enhanced_html_exporter.py
4. Fix START/STOP interaction in PIDRenderer.jsx
5. Fix START/STOP interaction in enhanced_html_exporter.py
6. Clean up P&ID layout styling
7. Test all 4 scenarios

