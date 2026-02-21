
from backend.iec_skeletons import ST_SKELETON
from backend.iec_enforcer import enforce_iec


class LLMGenerator:
    """
    Domain-based generator (no confusion between systems)
    """

    def generate(self, request):

        desc = request.description.lower()

        if "coffee" in desc:
            return self._coffee_program(request)

        if "parking" in desc or "car" in desc:
            return self._parking_program(request)

        if "lift" in desc or "elevator" in desc:
            return self._lift_program(request)

        return {
            "code": "(* ERROR: Unknown system requested *)",
            "fixes_applied": []
        }

    # -----------------------------
    # Coffee machine logic
    # -----------------------------
    def _coffee_program(self, request):

        inputs = """StartButton : BOOL;
WaterOK : BOOL;
CoffeeOK : BOOL;"""

        outputs = """Grinder : BOOL;
Heater : BOOL;
Pump : BOOL;
ReadyLight : BOOL;
EmptyLight : BOOL;"""

        vars_ = """State : INT := 0;"""

        reset = """Grinder := FALSE;
Heater := FALSE;
Pump := FALSE;
ReadyLight := FALSE;
EmptyLight := FALSE;"""

        logic = """
CASE State OF
0:
    ReadyLight := TRUE;
    IF NOT WaterOK OR NOT CoffeeOK THEN
        EmptyLight := TRUE;
    END_IF;

    IF StartButton AND WaterOK AND CoffeeOK THEN
        State := 1;
    END_IF;

1:
    Grinder := TRUE;
    State := 2;

2:
    Heater := TRUE;
    State := 3;

3:
    Pump := TRUE;
    State := 0;
END_CASE;
"""

        code = ST_SKELETON.format(
            program_name=request.program_name,
            input_decls=inputs,
            output_decls=outputs,
            vars_decls=vars_,
            output_reset=reset,
            edge_detection="(* Edge detection handled automatically *)",
            timer_section="(* Timer section handled automatically *)",
            main_logic=logic
        )

        final_code, errors = enforce_iec(code)

        return {
            "code": final_code,
            "fixes_applied": errors
        }

    # -----------------------------
    # Parking system
    # -----------------------------
    def _parking_program(self, request):

        inputs = """EntrySensor : BOOL;
ExitSensor : BOOL;"""

        outputs = """EntryGate : BOOL;
EntryGate : BOOL;
ExitGate : BOOL;
FullLight : BOOL;"""

        vars_ = """Count : INT := 0;
Max : INT := 10;"""

        reset = """EntryGate := FALSE;
ExitGate := FALSE;
FullLight := FALSE;"""

        logic = """
IF EntrySensor AND Count < Max THEN
    Count := Count + 1;
    EntryGate := TRUE;
END_IF;

IF ExitSensor AND Count > 0 THEN
    Count := Count - 1;
    ExitGate := TRUE;
END_IF;

IF Count >= Max THEN
    FullLight := TRUE;
END_IF;
"""

        code = ST_SKELETON.format(
            program_name=request.program_name,
            input_decls=inputs,
            output_decls=outputs,
            vars_decls=vars_,
            output_reset=reset,
            edge_detection="(* Edge detection handled automatically *)",
            timer_section="(* Timer section handled automatically *)",
            main_logic=logic
        )

        final_code, errors = enforce_iec(code)

        return {
            "code": final_code,
            "fixes_applied": errors
        }

    # -----------------------------
    # Lift system
    # -----------------------------
    def _lift_program(self, request):

        inputs = """UpCommand : BOOL;
DownCommand : BOOL;"""

        outputs = """MotorUp : BOOL;
MotorDown : BOOL;"""

        vars_ = """State : INT := 0;"""

        reset = """MotorUp := FALSE;
MotorDown := FALSE;"""

        logic = """
IF UpCommand THEN
    MotorUp := TRUE;
END_IF;

IF DownCommand THEN
    MotorDown := TRUE;
END_IF;
"""

        code = ST_SKELETON.format(
            program_name=request.program_name,
            input_decls=inputs,
            output_decls=outputs,
            vars_decls=vars_,
            output_reset=reset,
            edge_detection="(* Edge detection handled automatically *)",
            timer_section="(* Timer section handled automatically *)",
            main_logic=logic
        )

        final_code, errors = enforce_iec(code)

        return {
            "code": final_code,
            "fixes_applied": errors
        }


llm_generator = LLMGenerator()
