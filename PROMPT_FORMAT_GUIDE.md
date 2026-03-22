"""
PROMPT FORMAT GUIDE FOR PERFECT IEC 61131-3 ST CODE GENERATION
================================================================

The functional_state_generator works best with prompts that describe:
1. What the system does (control function)
2. Key inputs (sensors, buttons, switches)
3. Key outputs (motors, valves, lights)
4. Safety features (emergency stops, interlocks)
5. Operational states/sequences

BEST PROMPT FORMATS:
===================

Format 1: "Control a [device] with [inputs] and [safety features]"
--------------------------------------------------------------------
Examples:
- "Control a motor with start and stop buttons and emergency stop"
- "Control a pump with level sensor and overflow alarm"
- "Control a valve with pressure sensor and manual override"

Format 2: "[System type] with [features]"
-----------------------------------------
Examples:
- "Industrial conveyor with start stop and safety sensors"
- "Temperature control system with PID and safety limits"
- "Parking gate control with entry exit sensors"

Format 3: "[Complete description]"
--------------------------------
Examples:
- "Elevator control with floor sensors, door control, overload protection"
- "Bottling line with fill valve, capping motor, conveyor, emergency stop"
- "Traffic light control with pedestrian crossing and vehicle detection"

PROMPT TEMPLATES:
=================

1. MOTOR CONTROL:
   "Control a motor with start button, stop button, and emergency stop"
   "Motor control with forward reverse direction and thermal overload protection"

2. ELEVATOR:
   "Elevator control with floor selection, door open close, overload sensor"
   "Lift control with floor sensors, emergency stop, door interlocks"

3. CONVEYOR:
   "Conveyor belt with start stop, product detection, emergency stop"
   "Industrial conveyor with speed control and safety sensors"

4. PROCESS CONTROL:
   "Bottling line with fill valve, capper, conveyor, level sensors"
   "Mixing system with dosing pumps, level control, temperature monitoring"

5. SAFETY SYSTEMS:
   "Safety system with emergency stop, light curtain, safety relays"
   "Machine guard with safety sensors and emergency stop"

6. PARKING:
   "Parking gate control with entry sensor, exit sensor, barrier control"
   "Parking system with vehicle detection and capacity monitoring"

7. TEMPERATURE:
   "Temperature control with heater, cooler, PID control, alarm"
   "HVAC system with thermostat, fan control, temperature sensors"

8. PUMP STATION:
   "Pump station with pressure control, flow monitoring, dry run protection"
   "Water pump with level sensors and automatic on/off control"

DO's AND DON'Ts:
================

✅ DO:
- Be specific about inputs (sensors, buttons)
- Be specific about outputs (motors, valves, lights)
- Mention safety features (emergency stop, interlocks)
- Describe the sequence of operations
- Use industrial terminology

❌ DON'T:
- Don't be too vague: "make a PLC program"
- Don't use ambiguous terms without specifics
- Don't forget to mention safety requirements

BRAND PARAMETER:
================
You can specify the PLC brand:
- "SIEMENS" - Uses Siemens SCL syntax
- "CODESYS" - Uses standard IEC 61131-3
- "ALLEN_BRADLEY" - Uses RSLogix syntax
- "GENERIC" - Uses standard IEC syntax

Example API call:
{
  "requirement": "Control a motor with start and stop buttons and emergency stop",
  "brand": "SIEMENS"
}
"""
