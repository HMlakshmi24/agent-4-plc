PROGRAM CoffeeMachineControl

VAR_INPUT
    Start_Button    : BOOL;
    Water_Sensor    : BOOL;    (* TRUE when water level sufficient *)
    Coffee_Sensor   : BOOL;    (* TRUE when coffee hopper has coffee *)
END_VAR

VAR_OUTPUT
    Water_Valve     : BOOL := FALSE;
    Coffee_Valve    : BOOL := FALSE;
    Brew_Heater     : BOOL := FALSE;
    Brew_Light      : BOOL := FALSE;
END_VAR

VAR
    State           : INT := 0;  (* 0=Idle, 10=Fill, 20=AddCoffee, 30=Brew, 99=Error *)

    Start_Trig      : R_TRIG;

    Water_Timer     : TON;
    Coffee_Timer    : TON;
    Brew_Timer      : TON;

    FILL_DURATION   : TIME := T#10S;
    COFFEE_DURATION : TIME := T#5S;
    BREW_DURATION   : TIME := T#30S;

    (* Internal watchdog / safety *)
    ErrorLatch      : BOOL := FALSE;
END_VAR

(* Safe defaults every scan *)
Water_Valve := FALSE;
Coffee_Valve := FALSE;
Brew_Heater := FALSE;
Brew_Light := FALSE;

(* Edge detection - called every scan *)
Start_Trig(CLK := Start_Button);

(* Timers - always called every scan with IN = current state match *)
Water_Timer(IN := (State = 10), PT := FILL_DURATION);
Coffee_Timer(IN := (State = 20), PT := COFFEE_DURATION);
Brew_Timer(IN := (State = 30), PT := BREW_DURATION);

(* Error reset - Start button clears error latch and returns to idle when pressed *)
IF Start_Trig.Q THEN
    ErrorLatch := FALSE;
    IF State = 99 THEN
        State := 0;
    END_IF;
END_IF;

(* If an error latched, remain in error state until reset *)
IF ErrorLatch THEN
    State := 99;
END_IF;

CASE State OF

    0: (* IDLE - waiting for start *)
        IF Start_Trig.Q THEN
            (* basic pre-checks *)
            IF NOT Water_Sensor THEN
                State := 99; (* cannot start without water *)
                ErrorLatch := TRUE;
            ELSIF NOT Coffee_Sensor THEN
                State := 99; (* no coffee available *)
                ErrorLatch := TRUE;
            ELSE
                State := 10; (* start filling *)
            END_IF;
        END_IF;

    10: (* FILL WATER - keep valve open until timer/Q and sensor check complete *)
        Water_Valve := TRUE;

        IF Water_Timer.Q THEN
            (* After fill duration, confirm water sensor is present *)
            IF Water_Sensor THEN
                State := 20;
            ELSE
                State := 99; ErrorLatch := TRUE;
            END_IF;
        END_IF;

    20: (* ADD COFFEE - open coffee valve for measured duration *)
        Coffee_Valve := TRUE;

        IF Coffee_Timer.Q THEN
            IF Coffee_Sensor THEN
                State := 30;
            ELSE
                State := 99; ErrorLatch := TRUE;
            END_IF;
        END_IF;

    30: (* BREW - heater only enabled if water present (safety interlock) *)
        IF Water_Sensor THEN
            Brew_Heater := TRUE;   (* Safety: heater interlock *)
            Brew_Light := TRUE;
        ELSE
            State := 99; ErrorLatch := TRUE;
        END_IF;

        IF Brew_Timer.Q THEN
            (* Finish cycle and return to idle *)
            State := 0;
        END_IF;

    99: (* ERROR - latched until Start pressed *)
        (* indicate error via Brew_Light blink or other HMI - keep heater/valves off *)
        Brew_Light := FALSE;

END_CASE;

END_PROGRAM
