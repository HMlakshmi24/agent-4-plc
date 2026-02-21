
def get_st_skeleton(domain: str):
    """
    Returns a strict IEC 61131-3 Structured Text Skeleton for the given domain.
    Includes 15+ verified industrial templates.
    """
    
    skeletons = {
        # 1. COFFEE MACHINE
        "coffee": """PROGRAM CoffeeMachine
VAR_INPUT
    StartBtn : BOOL;
    StopBtn : BOOL;
    WaterLevelOK : BOOL;
    BeanLevelOK : BOOL;
END_VAR
VAR_OUTPUT
    Grinder : BOOL;
    Heater : BOOL;
    Pump : BOOL;
    ReadyLamp : BOOL;
END_VAR
VAR
    State : INT := 0; 
    Timer1 : TON;
    TReq : BOOL := FALSE;
    HeatingTime : TIME := T#5s;
END_VAR

(* OUTPUT RESET *)
Grinder := FALSE;
Heater := FALSE;
Pump := FALSE;
ReadyLamp := FALSE;

(* TIMER *)
Timer1(IN := TReq, PT := HeatingTime);

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 2. PARKING SYSTEM
        "parking": """PROGRAM Parking
VAR_INPUT
    EntrySensor : BOOL;
    ExitSensor : BOOL;
    TicketButton : BOOL;
END_VAR
VAR_OUTPUT
    EntryGate : BOOL;
    ExitGate : BOOL;
    FullSign : BOOL;
END_VAR
VAR
    Count : INT := 0;
    MaxSpots : INT := 10;
    State : INT := 0;
END_VAR

(* OUTPUT RESET *)
EntryGate := FALSE;
ExitGate := FALSE;
FullSign := FALSE;

(* BOILERPLATE LOGIC *)
IF Count >= MaxSpots THEN
    FullSign := TRUE;
ELSE
    FullSign := FALSE;
END_IF;

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 3. TRAFFIC LIGHT
        "traffic": """PROGRAM TrafficLight
VAR_INPUT
    Start : BOOL;
    PedestrianBtn : BOOL;
END_VAR
VAR_OUTPUT
    Red : BOOL;
    Yellow : BOOL;
    Green : BOOL;
    WalkSign : BOOL;
END_VAR
VAR
    State : INT := 0;
    Timer1 : TON;
    TReq : BOOL := FALSE;
    Duration : TIME := T#2s;
END_VAR

(* OUTPUT RESET *)
Red := FALSE;
Yellow := FALSE;
Green := FALSE;
WalkSign := FALSE;

(* TIMER *)
Timer1(IN := TReq, PT := Duration);

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 4. MIXING PROCESS
        "mixing": """PROGRAM Mixing
VAR_INPUT
    Start : BOOL;
    LevelLow : BOOL;
    LevelHigh : BOOL;
END_VAR
VAR_OUTPUT
    InletValve : BOOL;
    Agitator : BOOL;
    OutletValve : BOOL;
END_VAR
VAR
    State : INT := 0;
    Timer1 : TON;
    TReq : BOOL := FALSE;
END_VAR

InletValve := FALSE;
Agitator := FALSE;
OutletValve := FALSE;

Timer1(IN := TReq, PT := T#10s);

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 5. FILLING STATION
        "filling": """PROGRAM Filling
VAR_INPUT
    Start : BOOL;
    BottlePresent : BOOL;
END_VAR
VAR_OUTPUT
    Conveyor : BOOL;
    FillValve : BOOL;
    Capper : BOOL;
END_VAR
VAR
    State : INT := 0;
    Timer1 : TON;
    TReq : BOOL := FALSE;
END_VAR

(* OUTPUT RESET *)
Conveyor := FALSE;
FillValve := FALSE;
Capper := FALSE;

(* TIMER *)
Timer1(IN := TReq, PT := T#3s);

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 6. PRESSURE CONTROL
        "pressure": """PROGRAM PressureSystem
VAR_INPUT
    PressureInput : REAL;
END_VAR
VAR_OUTPUT
    PumpRun : BOOL;
    PumpSpeed : REAL;
END_VAR
VAR
    State : INT := 0;
    PressureSetpoint : REAL := 5.0;
    Error : REAL;
END_VAR

(* OUTPUT RESET *)
PumpRun := FALSE;

(* MAIN LOGIC *)
{logic}
END_PROGRAM
""",

        # 7. LIFT / ELEVATOR
        "lift": """PROGRAM Lift
VAR_INPUT
    Call : BOOL;
END_VAR
VAR_OUTPUT
    MotorUp : BOOL;
    MotorDown : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
MotorUp := FALSE;
MotorDown := FALSE;
{logic}
END_PROGRAM
""",
        
        # 8. CONVEYOR BELT
        "conveyor": """PROGRAM Conveyor
VAR_INPUT
    Start : BOOL;
END_VAR
VAR_OUTPUT
    Motor : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
Motor := FALSE;
{logic}
END_PROGRAM
""",

        # 9. TANK LEVEL
        "tank": """PROGRAM Tank
VAR_INPUT
    LevelLow : BOOL;
    LevelHigh : BOOL;
END_VAR
VAR_OUTPUT
    FillValve : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
FillValve := FALSE;
{logic}
END_PROGRAM
""",

        # 10. PUMP CONTROL
        "pump": """PROGRAM Pump
VAR_INPUT
    Start : BOOL;
END_VAR
VAR_OUTPUT
    PumpMotor : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
PumpMotor := FALSE;
{logic}
END_PROGRAM
""",

        # 11. COMPRESSOR
        "compressor": """PROGRAM Compressor
VAR_INPUT
    Start : BOOL;
END_VAR
VAR_OUTPUT
    CompressorMotor : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
CompressorMotor := FALSE;
{logic}
END_PROGRAM
""",

        # 12. FAN CONTROL
        "fan": """PROGRAM Fan
VAR_INPUT
    Start : BOOL;
END_VAR
VAR_OUTPUT
    FanMotor : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
FanMotor := FALSE;
{logic}
END_PROGRAM
""",

        # 13. HEATER CONTROL
        "heater": """PROGRAM Heater
VAR_INPUT
    TempLow : BOOL;
    TempHigh : BOOL;
END_VAR
VAR_OUTPUT
    HeaterOut : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
HeaterOut := FALSE;
{logic}
END_PROGRAM
""",

        # 14. SORTING SYSTEM
        "sorting": """PROGRAM Sorting
VAR_INPUT
    Sensor : BOOL;
END_VAR
VAR_OUTPUT
    Diverter : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
Diverter := FALSE;
{logic}
END_PROGRAM
""",

        # 15. BOTTLE SYSTEM
        "bottle": """PROGRAM BottleSystem
VAR_INPUT
    BottleSensor : BOOL;
END_VAR
VAR_OUTPUT
    Conveyor : BOOL;
    Valve : BOOL;
END_VAR
VAR
    State : INT := 0;
END_VAR
Conveyor := FALSE;
Valve := FALSE;
{logic}
END_PROGRAM
""",

        # 16. GENERIC (Fallback)
        "generic": """PROGRAM Main
VAR_INPUT
    Start : BOOL;
    Stop : BOOL;
    Sensor1 : BOOL;
END_VAR
VAR_OUTPUT
    Motor : BOOL;
    Valve : BOOL;
    Lamp : BOOL;
END_VAR
VAR
    State : INT := 0;
    Timer1 : TON;
    TReq : BOOL := FALSE;
END_VAR

(* OUTPUT RESET *)
Motor := FALSE;
Valve := FALSE;
Lamp := FALSE;

(* TIMER *)
Timer1(IN := TReq, PT := T#2s);

(* MAIN LOGIC *)
{logic}
END_PROGRAM
"""
    }

    # Normalize domain to match keys
    key = domain.lower()
    if "mix" in key: key = "mixing"
    if "level" in key: key = "tank"
    if "elevator" in key: key = "lift"
    if "light" in key and "traffic" not in key: key = "traffic" 
    if "pump" in key: key = "pump"
    if "compressor" in key: key = "compressor"
    if "fan" in key: key = "fan"
    if "heat" in key: key = "heater"
    if "pressure" in key: key = "pressure"
    if "bottle" in key: key = "bottle"
    if "sort" in key: key = "sorting"
    if "fill" in key: key = "filling"
    
    return skeletons.get(key, skeletons["generic"])
