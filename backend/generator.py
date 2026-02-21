from .validator import IECValidator

def generate_perfect_plc(app_type: str, brand: str = "siemens") -> str:
    """Generates a simple IEC ST program that follows validation rules."""
    templates = {
        "car_parking": {
            "inputs": ["EntrySensor : BOOL;", "ExitSensor : BOOL;", "MaxCapacity : UINT := 20;"],
            "outputs": ["EntryGate : BOOL;", "ExitGate : BOOL;", "FullLight : BOOL;"],
            "vars": ["CurrentCars : UINT := 0;", "EntryTrig : R_TRIG;", "ExitTrig : R_TRIG;", "GateTimer : TON;", "GateTime : TIME := T#5S;"],
            "logic": """(* OUTPUT RESET *)
EntryGate := FALSE; ExitGate := FALSE; FullLight := FALSE;

(* EDGES *)
EntryTrig(CLK := EntrySensor); ExitTrig(CLK := ExitSensor);

(* TIMER *)
GateTimer(IN := (EntryGate OR ExitGate), PT := GateTime);

(* PARKING LOGIC *)
IF EntryTrig.Q AND CurrentCars < MaxCapacity THEN
  CurrentCars := CurrentCars + UINT#1; EntryGate := TRUE;
ELSIF ExitTrig.Q AND CurrentCars > UINT#0 THEN
  CurrentCars := CurrentCars - UINT#1; ExitGate := TRUE;
END_IF;

FullLight := (CurrentCars >= MaxCapacity);"""
        },
        "lift_controller": {
            "inputs": ["CallButton : BOOL;", "EntrySensor : BOOL;", "ExitSensor : BOOL;"],
            "outputs": ["MotorUp : BOOL;", "MotorDown : BOOL;", "DoorOpen : BOOL;"],
            "vars": ["State : INT := 0;", "TargetFloor : INT := 0;", "CurrentFloor : INT := 0;", "Timer1 : TON;", "EntryTrig : R_TRIG;", "ExitTrig : R_TRIG;"],
            "logic": """(* OUTPUT RESET *)
MotorUp := FALSE; MotorDown := FALSE; DoorOpen := FALSE;

(* EDGE DETECTION *)
EntryTrig(CLK := EntrySensor); ExitTrig(CLK := ExitSensor);

CASE State OF
    0: (* IDLE *)
        IF TargetFloor <> 0 THEN State := 1; END_IF;
    1: (* MOVING *)
        IF TargetFloor > CurrentFloor THEN 
            MotorUp := TRUE;
            MotorDown := FALSE;
        ELSIF TargetFloor < CurrentFloor THEN 
            MotorUp := FALSE;
            MotorDown := TRUE;
        ELSE 
            State := 2; 
        END_IF;
    2: (* DOORS *)
        MotorUp := FALSE;
        MotorDown := FALSE;
        DoorOpen := TRUE;
        IF Timer1.Q THEN 
            State := 0; 
            TargetFloor := 0; 
            DoorOpen := FALSE;
        END_IF;
END_CASE;"""
        }
    }

    template = templates.get(app_type.lower())
    if not template:
        raise ValueError("Unknown application")

    code = f"""PROGRAM {app_type.title().replace(' ', '')}Control
VAR_INPUT
{chr(10).join(template['inputs'])}
END_VAR

VAR_OUTPUT
{chr(10).join(template['outputs'])}
END_VAR

VAR
{chr(10).join(template['vars'])}
END_VAR

{template['logic']}
END_PROGRAM"""

    # FINAL VALIDATION GUARANTEE
    validator = IECValidator()
    results = validator.validate(code)
    if results['errors'] != 0:
        raise AssertionError("Generator failed validation: " + str(results))

    return code
