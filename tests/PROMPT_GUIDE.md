# AutoMind Platform — Perfect Prompt Guide
## How to Get Maximum-Quality Output from PLC, HMI, and P&ID Generators

---

## Quick Reference

| Generator | Key Rules | Common Mistakes |
|-----------|-----------|-----------------|
| **PLC** | Name every I/O, state every sensor, mention E-Stop | Vague descriptions like "control a motor" |
| **HMI** | List every tank/pump/valve with ISA tags, name alarms | Missing connections between components |
| **P&ID** | Give ISA-5.1 instrument tags, describe each control loop | Not specifying instrument function codes |

---

## Part 1 — Perfect PLC Prompts (IEC 61131-3 Structured Text)

### What the PLC Generator Needs

The generator writes IEC 61131-3 Structured Text following this mandatory structure:
- `PROGRAM` / `VAR` / `END_VAR` / `END_PROGRAM` blocks
- Edge detection (`R_TRIG`) for every pushbutton input
- Global E-Stop safety interlock (highest priority)
- `CASE State OF` state machine (0=IDLE, 1=STARTING, 2=RUNNING, 3=STOPPING, 4=FAULT)
- `TON` timers with explicit `IN/PT` calls
- Naming convention: `I_` inputs, `Q_` outputs, `T_` timers, `RT_` edge triggers

### PLC Prompt Template

```
Generate IEC 61131-3 Structured Text for a [SYSTEM TYPE] PLC program.

Program name: [ProgramName]
PLC brand: [Siemens S7-1200 | Rockwell Studio 5000 | Schneider Modicon]

INPUTS:
- I_Start: Start pushbutton (NO contact)
- I_Stop: Stop pushbutton (NC contact)
- I_EStop: Emergency stop (NC contact, safety category 3)
- I_[SensorName]: [What it detects and when TRUE]
- I_[LevelHigh]: High level float switch (TRUE = tank full)
- I_[LevelLow]: Low level float switch (TRUE = tank empty)

OUTPUTS:
- Q_[Motor/Pump]: [Motor/pump description], rated [X] kW
- Q_[Valve]: [Valve description], [normally open/closed]
- Q_Alarm: Audible/visual alarm beacon

TIMERS:
- T_StartDelay: [X] second startup ramp delay
- T_FaultDelay: [X] second fault confirmation delay
- T_RunMax: [X] minute maximum run time protection

PROCESS DESCRIPTION:
[Describe the state machine in plain language]:
- IDLE (State 0): All outputs OFF, wait for Start button
- STARTING (State 1): [What happens during startup sequence]
- RUNNING (State 2): [Normal operation logic and conditions]
- STOPPING (State 3): [Controlled shutdown sequence]
- FAULT (State 4): [Fault conditions and FaultCode values]

SAFETY REQUIREMENTS:
- E-Stop immediately de-energizes all outputs and sets State := 0
- [Any other interlock conditions]

DIAGNOSTIC CODES:
- FaultCode 10: Emergency stop activated
- FaultCode 20: [Process-specific fault]
- FaultCode 30: [Another fault condition]
```

---

### Example 1 — Tank Filling System (Perfect Prompt)

```
Generate IEC 61131-3 Structured Text for a water tank filling PLC program.

Program name: TankFilling
PLC brand: Siemens S7-1200

INPUTS:
- I_Start: Start pushbutton (NO contact)
- I_Stop: Stop pushbutton (NC contact)
- I_EStop: Emergency stop mushroom (NC contact, safety category 3)
- I_LevelHigh: High level float switch at 90% — TRUE when tank full
- I_LevelLow: Low level float switch at 10% — TRUE when tank empty
- I_FlowFault: Flow meter fault input — TRUE when no flow detected

OUTPUTS:
- Q_InletValve: Pneumatic inlet valve, normally closed
- Q_FillPump: 5.5 kW inlet pump motor contactor
- Q_Alarm: Red alarm beacon and buzzer

TIMERS:
- T_StartDelay: 3 second pump start delay before opening valve
- T_FaultDelay: 5 second no-flow fault confirmation delay
- T_EmptyTimeout: 10 minute maximum fill time protection

PROCESS DESCRIPTION:
- IDLE (State 0): Pump OFF, valve CLOSED. Await Start press.
- STARTING (State 1): Energise pump, wait 3s T_StartDelay, then open inlet valve.
- FILLING (State 2): Pump ON, valve OPEN. Monitor I_LevelHigh and I_FlowFault.
  If I_LevelHigh goes TRUE → transition to STOPPING.
  If T_EmptyTimeout expires → set FaultCode 20, go to FAULT.
  If I_FlowFault stays TRUE for T_FaultDelay → set FaultCode 30, go to FAULT.
- STOPPING (State 3): Close inlet valve, run pump 2s to clear line, then stop pump. Go to IDLE.
- FAULT (State 4): All outputs OFF, Q_Alarm ON. Latched until operator resets with I_Stop.

SAFETY REQUIREMENTS:
- E-Stop immediately: Q_FillPump := FALSE, Q_InletValve := FALSE, Q_Alarm := TRUE, State := 0
- Never open valve without pump running (interlock in RUNNING state)

DIAGNOSTIC CODES:
- FaultCode 10: Emergency stop activated
- FaultCode 20: Fill timeout — level not reached in 10 minutes
- FaultCode 30: No-flow fault — pump running but no flow detected
```

---

### Example 2 — Conveyor Belt Sorting (Perfect Prompt)

```
Generate IEC 61131-3 Structured Text for a conveyor sorting system PLC program.

Program name: ConveyorSort
PLC brand: Rockwell Studio 5000 (Allen-Bradley)

INPUTS:
- I_Start: Start pushbutton (NO contact)
- I_Stop: Stop pushbutton (NC contact)
- I_EStop: Emergency stop pull cord, both ends of conveyor (NC contact)
- I_ItemDetect: Photoelectric presence sensor at entry — TRUE when item detected
- I_SortSensor: Colour/weight sensor output — TRUE = divert to Line B
- I_ConveyorFault: Motor overload relay — TRUE when overload tripped
- I_DiverterHome: Diverter gate home position switch — TRUE when retracted

OUTPUTS:
- Q_ConveyorMotor: 7.5 kW conveyor belt motor drive enable
- Q_DiverterSolenoid: Pneumatic diverter gate solenoid valve
- Q_RejectBelt: Secondary reject conveyor motor (small)
- Q_Alarm: Amber alarm light

TIMERS:
- T_SortDelay: 800ms delay from detection to diverter actuation (transport time)
- T_DiverterHold: 600ms diverter hold time per item
- T_MotorStart: 2 second motor acceleration ramp before processing

PROCESS DESCRIPTION:
- IDLE (State 0): All outputs OFF. Wait for Start.
- STARTING (State 1): Start Q_ConveyorMotor, wait T_MotorStart, then enter RUNNING.
- RUNNING (State 2): Normal sorting operation.
  When I_ItemDetect goes TRUE: read I_SortSensor immediately.
  After T_SortDelay: if I_SortSensor was TRUE, activate Q_DiverterSolenoid for T_DiverterHold time.
  Increment CycleCount on each item processed.
  If I_ConveyorFault TRUE → set FaultCode 20, go to FAULT.
- STOPPING (State 3): Stop processing new items, wait for current item to clear (1s), stop motor.
- FAULT (State 4): Q_Alarm ON, all motors OFF. Latch until I_Stop + I_EStop reset.

SAFETY REQUIREMENTS:
- E-Stop: immediate stop of all motors, retract diverter, State := 0
- Do not activate diverter unless Q_DiverterHome confirms gate retracted at cycle start

DIAGNOSTIC CODES:
- FaultCode 10: E-Stop activated
- FaultCode 20: Motor overload trip
- FaultCode 30: Diverter not returning to home position within 2 seconds
```

---

### Example 3 — Temperature Control (Perfect Prompt)

```
Generate IEC 61131-3 Structured Text for a temperature control PLC program.

Program name: TempControl
PLC brand: Schneider Modicon M340

INPUTS:
- I_Start: Start pushbutton (NO contact)
- I_Stop: Stop pushbutton (NC contact)
- I_EStop: Emergency stop (NC contact)
- I_TempHigh: High temperature thermostat — TRUE when > 85°C (hardwired safety)
- I_TempOK: Temperature in range thermostat — TRUE when 60–80°C
- I_HeaterFault: Heater contactor auxiliary contact — FALSE = contactor welded fault

OUTPUTS:
- Q_Heater: 12 kW electric heater contactor
- Q_CoolingFan: Cooling fan motor (runs when too hot)
- Q_Alarm: Temperature alarm beacon

TIMERS:
- T_HeatDelay: 30 second minimum heat time before temperature check
- T_CoolDelay: 10 second fan run-on after heater OFF
- T_FaultConfirm: 5 second fault confirmation delay

PROCESS DESCRIPTION:
- IDLE (State 0): Heater OFF, fan OFF. Wait for Start.
- HEATING (State 1): Energise Q_Heater. Run T_HeatDelay (30s minimum heat time).
  After 30s, if I_TempOK TRUE → transition to HOLDING.
  If I_TempHigh TRUE at any time → EMERGENCY_COOL (State 4).
- HOLDING (State 2): Monitor temperature.
  If I_TempOK FALSE and I_TempHigh FALSE → re-enter HEATING.
  If I_TempHigh TRUE → EMERGENCY_COOL (State 4).
  If I_Stop → go to COOLING (State 3).
- COOLING (State 3): Turn OFF Q_Heater, turn ON Q_CoolingFan for T_CoolDelay (10s), then IDLE.
- EMERGENCY_COOL (State 4): Heater OFF, Fan ON, Q_Alarm ON. FaultCode 20. Latch until manual reset.

SAFETY REQUIREMENTS:
- I_TempHigh is a hardwired NC thermostat — also wired in series with heater contactor coil
- E-Stop: Q_Heater := FALSE immediately, Q_CoolingFan := TRUE (leave fan running for safety)
- Never energise Q_Heater and Q_CoolingFan simultaneously

DIAGNOSTIC CODES:
- FaultCode 10: E-Stop activated
- FaultCode 20: Over-temperature trip (I_TempHigh TRUE)
- FaultCode 30: Heater contactor fault (energised but no auxiliary feedback)
```

---

## Part 2 — Perfect HMI Prompts (SCADA Dashboard)

### What the HMI Generator Needs

The HMI generator produces a JSON schema that drives a physics-simulated SCADA dashboard with:
- Components: `tank`, `pump`, `valve`, `motor`, `sensor_level`, `sensor_temp`, `sensor_pressure`, `sensor_flow`, `gauge`, `alarm`, `button`, `slider`
- ISA-5.1 instrument tags (e.g. `LT-101`, `PT-201`, `FT-301`, `TT-401`)
- Simulation parameters: `fill_rate`, `drain_rate`, `capacity`, alarm thresholds
- Pipe connections between components
- Theme: `water` | `motor` | `hvac` | `chemical` | `food` | `default`

### HMI Prompt Template

```
Generate an industrial HMI SCADA dashboard JSON layout for a [SYSTEM NAME].

System name: [Full descriptive name, e.g. "Water Treatment Plant — Unit 1"]
Theme: [water | motor | hvac | chemical | food | default]

EQUIPMENT LIST (assign ISA-5.1 tags):
- [Equipment type] [TAG]: [Description, capacity/rating]
- Tank TK-101: [Name], [X] litre capacity, normal level 20–80%
- Pump P-101: [Name], [X] L/s flow rate
- Valve V-101: [Name], [normally open/closed]

INSTRUMENTS (one per measurement point):
- Level transmitter LT-101: measures TK-101 level, alarm at 90%/10%
- Pressure transmitter PT-201: measures [location], alarm at [value] bar
- Temperature transmitter TT-301: measures [location], alarm at [value]°C
- Flow transmitter FT-401: measures [location], alarm at [value] m³/h

PROCESS FLOW (describe pipe connections):
- [Source] → [Destination]: [What flows through this pipe]
- P-101 pumps from TK-101 to [destination]
- V-101 controls flow from [A] to [B]

ALARMS:
- [TAG] High alarm: [threshold] [unit] — [consequence]
- [TAG] Low alarm: [threshold] [unit] — [consequence]

SIMULATION PHYSICS:
- TK-101 fills at [X] L/s when P-101 running
- TK-101 drains at [X] L/s when V-101 open
- Normal steady-state level: approximately [X]%
```

---

### Example 1 — Water Treatment Plant (Perfect HMI Prompt)

```
Generate an industrial HMI SCADA dashboard JSON layout for a water treatment plant.

System name: "Municipal Water Treatment Plant — Unit 1"
Theme: water

EQUIPMENT LIST:
- Tank TK-101: Raw water feed tank, 50,000 litre capacity, normal level 40–75%
- Tank TK-201: Filtered water storage tank, 80,000 litre capacity, normal level 50–85%
- Pump P-101: Raw water feed pump, 8.5 L/s flow rate
- Pump P-201: Transfer pump, 6.0 L/s flow rate
- Valve V-101: Feed isolation valve, normally closed
- Valve V-201: Backwash valve, normally closed
- Motor M-101: Filter agitator motor, 3 kW

INSTRUMENTS:
- Level transmitter LT-101: measures TK-101 level, hi alarm 90%, lo alarm 10%, hi-hi 95%, lo-lo 5%
- Level transmitter LT-201: measures TK-201 level, hi alarm 92%, lo alarm 15%
- Flow transmitter FT-101: measures P-101 outlet flow, hi alarm 10 m³/h
- Pressure transmitter PT-101: measures P-101 discharge, hi alarm 4.5 bar, lo alarm 0.5 bar
- Temperature transmitter TT-101: measures raw water temperature, hi alarm 30°C

PROCESS FLOW:
- External supply → V-101 → TK-101 (raw water inlet pipe)
- TK-101 → P-101 → V-201 → Filter (raw water to filter feed)
- Filter → P-201 → TK-201 (filtered water to storage)
- M-101 drives filter agitator during backwash cycle

ALARMS:
- LT-101 High: 90% — risk of overflow, reduce inlet flow
- LT-101 Low: 10% — pump cavitation risk, stop P-101
- LT-201 High: 92% — storage full, divert to drain
- PT-101 Low: 0.5 bar — inlet blocked or pump fault
- FT-101 High: 10 m³/h — flow controller overspeed

SIMULATION PHYSICS:
- TK-101 fills at 5 L/s via V-101, drains at 8.5 L/s when P-101 running
- TK-201 fills at 6 L/s from filter, drains at 3 L/s to distribution
- Normal steady-state: TK-101 at 55%, TK-201 at 65%
```

---

### Example 2 — Chemical Mixing System (Perfect HMI Prompt)

```
Generate an industrial HMI SCADA dashboard JSON layout for a chemical mixing system.

System name: "Chemical Dosing & Mixing Station — Batch B"
Theme: chemical

EQUIPMENT LIST:
- Tank TK-101: Acid feed tank (H2SO4 5%), 5,000 litre capacity, normal level 30–70%
- Tank TK-201: Base feed tank (NaOH 10%), 5,000 litre capacity, normal level 30–70%
- Tank TK-301: Mix reactor vessel, 2,000 litre capacity, normal level 40–80%
- Pump P-101: Acid metering pump, 0.5 L/s, variable speed
- Pump P-201: Base metering pump, 0.5 L/s, variable speed
- Motor M-301: Reactor agitator motor, 5.5 kW, 150 rpm

INSTRUMENTS:
- Level transmitter LT-101: TK-101 acid level, hi alarm 85%, lo alarm 15%
- Level transmitter LT-201: TK-201 base level, hi alarm 85%, lo alarm 15%
- Level transmitter LT-301: TK-301 reactor level, hi alarm 90%, lo alarm 10%
- Temperature transmitter TT-301: Reactor temperature, hi alarm 65°C, hi-hi 75°C
- pH transmitter AT-301: Reactor pH, hi alarm 9.5, lo alarm 5.5 (target 7.0)
- Flow transmitter FT-101: Acid feed flow, hi alarm 0.8 L/s
- Flow transmitter FT-201: Base feed flow, hi alarm 0.8 L/s

PROCESS FLOW:
- TK-101 → P-101 → TK-301 (acid dosing pipe, blue)
- TK-201 → P-201 → TK-301 (base dosing pipe, red)
- M-301 agitates TK-301 continuously during batch
- TK-301 outlet → product transfer after batch complete

ALARMS:
- TT-301 High 65°C: Exothermic reaction runaway, reduce acid/base flow
- TT-301 HiHi 75°C: Emergency coolant injection, stop all pumps
- AT-301 Low 5.5: Excess acid, increase P-201 base flow
- AT-301 High 9.5: Excess base, increase P-101 acid flow
- LT-301 HiHi 95%: Overfill reactor, stop all feed pumps immediately

SIMULATION PHYSICS:
- TK-301 fills at 1.0 L/s total (0.5 acid + 0.5 base) when both pumps running
- TK-301 drains at 0.8 L/s when batch transfer valve open
- Temperature rises 2°C/min during active mixing at full flow
```

---

## Part 3 — Perfect P&ID Prompts (ISA-5.1 Diagrams)

### What the P&ID Generator Needs

The P&ID generator produces SVG diagrams following ISA-5.1 standard with:
- Equipment types: `vertical_tank`, `horizontal_tank`, `pump`, `valve_control`, `valve_manual`, `valve_check`, `heat_exchanger`, `reactor`, `compressor`, `filter`
- Instrument bubbles (circles) with correct ISA-5.1 function codes:
  - First letter: `L`=Level, `P`=Pressure, `T`=Temperature, `F`=Flow, `A`=Analyzer
  - Second letter: `T`=Transmitter, `C`=Controller, `I`=Indicator, `S`=Switch, `V`=Control Valve
- Control loops: describe the complete measurement → controller → final element chain
- Tag format: `[Function][Number]-[Loop]` e.g. `LT-101`, `LIC-101`, `LV-101`

### P&ID Prompt Template

```
Generate an ISA-5.1 compliant P&ID diagram for a [SYSTEM NAME].

System: [Full system name]

EQUIPMENT (use ISA tag format):
- [Equipment type] [TAG]: [Description, key dimension]
- Vertical tank TK-[NNN]: [Name], [volume], [material]
- Pump P-[NNN]: [Name], [type: centrifugal/positive displacement], [flow rate]
- Control valve LV-[NNN]: [Name], air-to-open or air-to-close, [pipe size]

PROCESS INSTRUMENTS (ISA-5.1 tag format):
- LT-[NNN]: Level transmitter on TK-[NNN], 4–20 mA, range 0–100%
- LIC-[NNN]: Level indicating controller, setpoint [X]%, PID loop [NNN]
- LV-[NNN]: Level control valve, manipulated variable for loop [NNN]
- PT-[NNN]: Pressure transmitter on [location], range 0–[X] bar
- TT-[NNN]: Temperature transmitter on [location], range 0–[X]°C
- FT-[NNN]: Flow transmitter on [line], [type: orifice plate/Coriolis/vortex]
- LSH-[NNN]: Level switch high on TK-[NNN], trip at [X]% (hardwired safety)
- LSL-[NNN]: Level switch low on TK-[NNN], trip at [X]% (pump protection)

CONTROL LOOPS:
- Loop [NNN] — Level control: LT-[NNN] measures TK-[NNN] → LIC-[NNN] controller → LV-[NNN] inlet valve
- Loop [NNN] — Temperature control: TT-[NNN] measures reactor → TIC-[NNN] → TV-[NNN] steam valve
- Loop [NNN] — Flow control: FT-[NNN] measures outlet → FIC-[NNN] → FV-[NNN] control valve

PIPE LINES (ISA line designation):
- Line [NNN]-[Fluid Code]-[Size]-[Spec]: [From] → [To]
- e.g. 101-PW-6"-A1: Potable water, 6 inch, spec A1, from TK-101 to P-101 suction

SAFETY INSTRUMENTED FUNCTIONS:
- SIF-[N]: [Tag] trip → [action] (e.g. LSH-101 high level → close LV-101, stop P-101)
```

---

### Example 1 — Boiler Feedwater System (Perfect P&ID Prompt)

```
Generate an ISA-5.1 compliant P&ID diagram for a boiler feedwater system.

System: Steam Boiler Feedwater System — Utility Block A

EQUIPMENT:
- Vertical tank TK-101: Deaerator feed tank, 10,000 litres, carbon steel, 5 bar design
- Centrifugal pump P-101A: Boiler feed pump (duty), 15 L/s at 12 bar
- Centrifugal pump P-101B: Boiler feed pump (standby), same duty
- Boiler B-201: Fire tube steam boiler, 5 tonne/hour steam, 8 bar working pressure

PROCESS INSTRUMENTS:
- LT-101: Level transmitter on TK-101, 4–20 mA, range 0–100%
- LIC-101: Level indicating controller, setpoint 60%, PID loop 101
- LV-101: Level control valve (inlet to TK-101), air-to-close, DN50
- LSH-101: Level switch high on TK-101, trip at 90% (hardwired NC)
- LSL-101: Level switch low on TK-101, trip at 15%, stops P-101A/B
- PT-201: Pressure transmitter on B-201 steam drum, range 0–12 bar
- PIC-201: Pressure indicating controller, setpoint 8 bar, PID loop 201
- TT-101: Temperature transmitter on TK-101, range 0–120°C, deaeration temp
- FT-301: Flow transmitter on P-101A discharge, orifice plate, 0–20 L/s
- FIC-301: Feed flow indicating controller, PID loop 301
- FV-301: Feed control valve, air-to-open, DN40

CONTROL LOOPS:
- Loop 101 — Deaerator level: LT-101 → LIC-101 → LV-101 (inlet makeup valve controls tank level at 60%)
- Loop 201 — Boiler pressure: PT-201 → PIC-201 → burner firing rate (controls steam pressure at 8 bar)
- Loop 301 — Feed flow: FT-301 → FIC-301 → FV-301 (controls feedwater flow to boiler drum)

PIPE LINES:
- 101-BFW-4"-A1: Boiler feedwater, 4 inch, from TK-101 to P-101A/B suction
- 102-BFW-3"-A1: Boiler feedwater, 3 inch, from P-101A/B discharge via FV-301 to B-201
- 103-STM-3"-B2: Steam, 3 inch, from B-201 steam drum to header

SAFETY INSTRUMENTED FUNCTIONS:
- SIF-1: LSH-101 high level → close LV-101 (prevent TK-101 overflow)
- SIF-2: LSL-101 low level → stop P-101A and P-101B (prevent pump dry running)
- SIF-3: PT-201 > 9.5 bar → trip burner and open safety relief valve PSV-201
```

---

### Example 2 — Cooling Water System (Perfect P&ID Prompt)

```
Generate an ISA-5.1 compliant P&ID diagram for an industrial cooling water system.

System: Closed-Loop Cooling Water System — Production Hall 3

EQUIPMENT:
- Vertical tank TK-101: Cooling water surge tank, 2,000 litres, HDPE lined
- Centrifugal pump P-101: Cooling water circulation pump, 25 L/s at 3 bar
- Heat exchanger HX-101: Plate heat exchanger, process side / cooling water side
- Cooling tower CT-101: Induced-draft cooling tower, 500 kW rejection duty

PROCESS INSTRUMENTS:
- TT-101: Temperature transmitter on HX-101 cooling water outlet, range 0–50°C
- TIC-101: Temperature indicating controller, setpoint 25°C, controls CT-101 fan speed
- TT-201: Temperature transmitter on HX-101 process inlet, range 0–120°C
- PT-101: Pressure transmitter on P-101 discharge, range 0–6 bar
- FT-101: Flow transmitter on main cooling water header, vortex meter, 0–30 L/s
- LT-101: Level transmitter on TK-101, range 0–100%
- LSL-101: Level switch low on TK-101, trip at 20% (stops pump, prevents cavitation)
- TT-301: Temperature transmitter on cooling tower return, range 0–45°C

CONTROL LOOPS:
- Loop 101 — Cooling water temperature: TT-101 outlet temperature → TIC-101 → CT-101 fan VSD (maintains 25°C supply)
- Loop 201 — Flow monitoring: FT-101 → FIC-201 → FV-201 bypass valve (maintains minimum 15 L/s)

PIPE LINES:
- 101-CWS-6"-C3: Cooling water supply, 6 inch, P-101 discharge to HX-101 process side inlet
- 102-CWR-6"-C3: Cooling water return, 6 inch, from HX-101 to CT-101 hot basin
- 103-CWS-4"-C3: Cooling tower cold basin to TK-101 / P-101 suction
- 104-MKU-2"-A1: Makeup water, 2 inch, city water to TK-101 via LV-101

SAFETY INSTRUMENTED FUNCTIONS:
- SIF-1: LSL-101 low level → stop P-101 (pump protection)
- SIF-2: TT-201 process inlet > 95°C → open bypass valve, alarm to DCS
- SIF-3: PT-101 > 5 bar → trip P-101, open relief line PRV-101
```

---

## Part 4 — Combined System Prompts (All Three Generators)

For the best results when generating PLC + HMI + P&ID for the same system, use **consistent tag names** across all three prompts. This creates a coherent package.

### Example — Pump Transfer Station (Full Package Prompt)

#### Step 1: Generate PLC first

```
Generate IEC 61131-3 Structured Text for a pump transfer station PLC.

Program name: PumpTransfer
PLC brand: Siemens S7-1200

INPUTS:
- I_Start: Start pushbutton (NO)
- I_Stop: Stop pushbutton (NC)
- I_EStop: Emergency stop (NC, safety cat 3)
- I_LevelHighSrc: Source tank TK-101 high level switch at 85% — TRUE when full
- I_LevelLowSrc: Source tank TK-101 low level switch at 15% — TRUE when empty
- I_LevelHighDst: Destination tank TK-201 high level switch at 90% — TRUE when full
- I_FlowFault: FT-101 flow switch — TRUE = no flow detected

OUTPUTS:
- Q_Pump_P101: 7.5 kW transfer pump P-101 motor contactor
- Q_Valve_V101: Inlet isolation valve V-101 (normally closed pneumatic)
- Q_Valve_V201: Outlet isolation valve V-201 (normally closed pneumatic)
- Q_Alarm: Transfer station alarm beacon

TIMERS:
- T_PumpStart: 4 second valve-open-to-pump-start delay
- T_NoFlow: 10 second no-flow fault confirmation
- T_MaxRun: 30 minute maximum single transfer time protection

PROCESS DESCRIPTION:
- IDLE (0): All OFF. Await Start.
- STARTING (1): Open V-101 and V-201, wait T_PumpStart (4s), start P-101.
- RUNNING (2): Monitor I_LevelLowSrc (stop if source empty), I_LevelHighDst (stop if dest full), I_FlowFault for T_NoFlow. Increment CycleCount on each completed transfer.
- STOPPING (3): Stop P-101, wait 3s for line depressure, close V-101 and V-201.
- FAULT (4): All OFF, Q_Alarm ON. Reset requires Stop + EStop clear.

DIAGNOSTIC CODES:
- FaultCode 10: E-Stop
- FaultCode 20: Source tank empty during transfer
- FaultCode 21: Destination tank full
- FaultCode 30: No-flow fault — pump running but FT-101 shows zero
- FaultCode 40: Max run time exceeded
```

#### Step 2: Generate HMI using same tags

```
Generate HMI SCADA JSON for a pump transfer station.

System name: "Pump Transfer Station — Block 2"
Theme: water

EQUIPMENT (same tags as PLC):
- Tank TK-101: Source storage tank, 20,000 litre, normal level 30–80%
- Tank TK-201: Destination process tank, 15,000 litre, normal level 20–75%
- Pump P-101: Transfer pump, 7.5 kW, 4.2 L/s at 2.5 bar
- Valve V-101: Inlet isolation valve, normally closed
- Valve V-201: Outlet isolation valve, normally closed

INSTRUMENTS:
- LT-101: TK-101 level, 4–20 mA, hi alarm 85%, lo alarm 15%, hi-hi 95%, lo-lo 5%
- LT-201: TK-201 level, 4–20 mA, hi alarm 90%, lo alarm 10%
- FT-101: P-101 discharge flow, 0–10 L/s, lo alarm 0.5 L/s (no-flow detection)
- PT-101: P-101 discharge pressure, 0–6 bar, hi alarm 4.0 bar, lo alarm 0.3 bar

CONNECTIONS:
- TK-101 → V-101 → P-101 → FT-101 → V-201 → TK-201 (main transfer line)

ALARMS:
- LT-101 Lo 15%: Source empty — stop pump
- LT-201 Hi 90%: Destination full — stop pump
- FT-101 Lo 0.5 L/s: No flow detected — pump fault
- PT-101 Hi 4.0 bar: High discharge pressure — line blocked

SIMULATION:
- TK-101 drains at 4.2 L/s when P-101 running
- TK-201 fills at 4.2 L/s when P-101 running
- TK-201 drains at 1.5 L/s (constant process consumption)
```

#### Step 3: Generate P&ID using same tags

```
Generate ISA-5.1 P&ID for pump transfer station.

System: Pump Transfer Station — Block 2

EQUIPMENT:
- Vertical tank TK-101: Source storage tank, 20,000 litres, carbon steel
- Vertical tank TK-201: Destination process tank, 15,000 litres, carbon steel
- Centrifugal pump P-101: Transfer pump, 4.2 L/s, 2.5 bar, 7.5 kW

INSTRUMENTS:
- LT-101: Level transmitter TK-101, 4–20 mA, 0–100%
- LT-201: Level transmitter TK-201, 4–20 mA, 0–100%
- LSL-101: Level switch low TK-101, trip at 15% (pump protection)
- LSH-201: Level switch high TK-201, trip at 92% (overfill protection)
- FT-101: Flow transmitter P-101 discharge, orifice plate, 0–10 L/s
- FSL-101: Flow switch low P-101 discharge, trip at 0.5 L/s (no-flow)
- PT-101: Pressure transmitter P-101 discharge, 0–6 bar
- V-101: Motorised inlet isolation valve (PLC-controlled, NC)
- V-201: Motorised outlet isolation valve (PLC-controlled, NC)

CONTROL LOOPS:
- Loop 101 — Level monitoring: LT-101 → DCS display only (no automatic control, PLC handles start/stop)
- Loop 201 — Level monitoring: LT-201 → DCS display only

PIPE LINES:
- 101-PW-4"-A1: Process water, 4 inch, from TK-101 via V-101 to P-101 suction
- 102-PW-3"-A1: Process water, 3 inch, from P-101 discharge via FT-101 and V-201 to TK-201

SAFETY INSTRUMENTED FUNCTIONS:
- SIF-1: LSL-101 low level → stop P-101 (prevent cavitation)
- SIF-2: LSH-201 high level → stop P-101, close V-101 and V-201 (prevent overflow)
- SIF-3: FSL-101 no-flow → stop P-101 after 10s delay (blocked line / dry running)
```

---

## Part 5 — What to Avoid (Common Mistakes)

### PLC Mistakes

| Bad Prompt | Why It Fails | Good Prompt |
|------------|-------------|-------------|
| "Control a motor" | No I/O specified, no state machine | Specify I_Start, I_Stop, I_EStop, Q_Motor, states 0–4 |
| "Water pump system" | No alarm conditions or timers | Add I_LevelHigh, I_LevelLow, T_NoFlow, FaultCodes |
| "Add PID control" | No setpoint/feedback tag | Specify `SP_Temp: REAL := 75.0` and `PV_Temp: REAL` with full PID parameters |
| Missing E-Stop | Fails safety interlock check | Always include `I_EStop: BOOL` and safety block |

### HMI Mistakes

| Bad Prompt | Why It Fails | Good Prompt |
|------------|-------------|-------------|
| "Show a tank" | No connections, no alarms, no sim params | Add LT-101 instrument, alarm thresholds, fill/drain rates |
| "Motor control panel" | Missing ISA tags | Assign MT-101, add sensor_temp TT-101, alarm at 85°C |
| No theme specified | Gets generic colours | Add `Theme: water` or `chemical` or `hvac` |
| No connections | Pipes not drawn | Explicitly write "P-101 pumps FROM TK-101 TO TK-201" |

### P&ID Mistakes

| Bad Prompt | Why It Fails | Good Prompt |
|------------|-------------|-------------|
| "Show instrumentation" | No ISA tag format | Always use `LT-101`, `LIC-101`, `LV-101` pattern |
| No control loops | Just a drawing, no function | Add "Loop 101: LT-101 → LIC-101 → LV-101 inlet valve" |
| Missing SIFs | No safety annotation | Add at least 2 safety instrumented functions |
| No pipe line IDs | Non-standard diagram | Add line numbers e.g. "101-PW-4-A1" |

---

## Part 6 — Quick Cheat Sheets

### ISA-5.1 Instrument Tag Letters

**First Letter (Measured Variable):**
- `L` = Level
- `P` = Pressure
- `T` = Temperature
- `F` = Flow
- `A` = Analyzer (pH, conductivity, O2)
- `I` = Current
- `S` = Speed / Vibration
- `W` = Weight / Force

**Second Letter (Function):**
- `T` = Transmitter (e.g. `LT-101`)
- `C` = Controller (e.g. `LIC-101` = Level Indicating Controller)
- `I` = Indicator (e.g. `LI-101` = Level Indicator)
- `S` = Switch (e.g. `LSH-101` = Level Switch High)
- `V` = Control Valve (e.g. `LV-101` = Level Valve)
- `E` = Element / Primary element (e.g. `TE-101` = Temperature Element/thermowell)

### State Machine States (PLC)
```
State 0 = IDLE      (all outputs OFF, await start)
State 1 = STARTING  (startup sequence, ramp timers)
State 2 = RUNNING   (normal operation, monitor alarms)
State 3 = STOPPING  (controlled shutdown sequence)
State 4 = FAULT     (all outputs OFF, alarm ON, latched)
```

### HMI Themes
```
water    → blue colour scheme (water/wastewater)
chemical → yellow/amber (chemical processing)
hvac     → green (HVAC/building)
motor    → grey/industrial (motor drives)
food     → white/clean room
default  → dark blue
```

### PLC Naming Convention
```
I_  = Digital Input  (I_Start, I_EStop, I_LevelHigh)
Q_  = Digital Output (Q_Motor, Q_Valve, Q_Alarm)
AI_ = Analog Input   (AI_Temperature, AI_Pressure)
AO_ = Analog Output  (AO_ValvePosition, AO_Speed)
T_  = Timer          (T_StartDelay, T_FaultDelay)
RT_ = Rising Trigger (RT_Start, RT_EStop)
FT_ = Falling Trigger (FT_Stop)
SP_ = Setpoint       (SP_Temperature, SP_Level)
PV_ = Process Value  (PV_Temperature, PV_Level)
```

---

*AutoMind Platform — Prompt Guide v1.0 | Generated 2026-03-10*
