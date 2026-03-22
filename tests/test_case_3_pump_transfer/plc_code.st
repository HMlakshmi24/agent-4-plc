pascal
PROGRAM PumpTransferControl
VAR
    (* Inputs *)
    I_LT301 : BOOL;
    I_LT302 : BOOL;
    I_E___type____timeout____event____VALVE_FAULT____duration____10_seconds__ : BOOL;
    I_E___type____emergency_stop____action____stop_pump_and_close_both_valves__ : BOOL;
    (* Outputs *)
    Q_PumpControl : BOOL := FALSE;
    Q_ValveControl : BOOL := FALSE;
    (* Safety Flags *)
    M_E_Stop : BOOL := FALSE;
    I_E___type____timeout____event____VALVE_FAULT____duration____10_seconds__ : BOOL := FALSE;
    I_E___type____emergency_stop____action____stop_pump_and_close_both_valves__ : BOOL := FALSE;
    (* Internal States *)
    M_PumpRunning : BOOL := FALSE;
    M_ValveOpen : BOOL := FALSE;
    M_ValveFault : BOOL := FALSE;
    M_SourceLow : BOOL := FALSE;
    M_Count : INT := 0;
    (* Edge Detection *)
    VALVE_FAULT_Trig : R_TRIG;
    (* Timers *)
    T_ValveTimeout : TON;
    (* State Machine *)
    M_State : INT := 0; (* 0 = Idle *)
END_VAR

(* ─ Edge Detection ────────────────────────────── *)
VALVE_FAULT_Trig(CLK := VALVE_FAULT);

(* ─ Safety Overrides ─────────────────────── *)
(* Safety override — manual implementation required *)

(* ─ State Machine ─────────────────────────── *)
CASE M_State OF
0: (* Idle — no transitions defined *)
END_CASE;

(* ─ Timer Calls — State-Locked (outside IF, every scan) *)
T_ValveTimeout(IN := (M_State = 1), PT := T#5S);
IF T_ValveTimeout.Q THEN
    M_ValveFault := TRUE; (* Set valve fault if timer expires *)
END_IF;

(* ─ Deterministic Output Assignment (bottom only) ─── *)
Q_PumpControl := (Running) AND NOT (Fault) AND NOT (EmergencyStop);
Q_ValveControl := (Running) AND NOT (Fault) AND NOT (EmergencyStop);

END_PROGRAM