pascal
PROGRAM ConveyorSortControl
VAR
    (* Inputs *)
    I_JAM_SENSOR : BOOL;
    I_START_PB : BOOL;
    I_STOP_PB : BOOL;
    I_RESET_PB : BOOL;
    I_ESTOP : BOOL;
    I_E___name____ESTOP____type____emergency_stop__ : BOOL;
    (* Outputs *)
    Q_SOL_201 : BOOL := FALSE;
    Q_M_RUN : BOOL := FALSE;
    Q_JAM_FAULT : BOOL := FALSE;
    Q_DIVERT_ACTIVE : BOOL := FALSE;
    (* Analog Values *)
    M_C_CONV_SPEED : REAL := 0.0;
    (* Safety Flags *)
    M_E_Stop : BOOL := FALSE;
    I_E___name____ESTOP____type____emergency_stop__ : BOOL := FALSE;
    (* Internal States *)
    M_Running : BOOL := FALSE;
    M_JamFault : BOOL := FALSE;
    M_TotalCount : INT := 0;
    M_MetalCount : INT := 0;
    (* Edge Detection *)
    I_JAM_SENSOR_Trig : R_TRIG;
    I_START_PB_Trig : R_TRIG;
    I_STOP_PB_Trig : R_TRIG;
    I_RESET_PB_Trig : R_TRIG;
    M_TotalCount_Trig : R_TRIG;
    M_MetalCount_Trig : R_TRIG;
    (* Timers *)
    T_SOL_201_Activation : TON;
    T_JAM_SENSOR : TON;
    (* State Machine *)
    M_State : INT := 0; (* 0 = Idle *)
END_VAR

(* ─ Edge Detection ────────────────────────────── *)
I_JAM_SENSOR_Trig(CLK := I_JAM_SENSOR);
I_START_PB_Trig(CLK := I_START_PB);
I_STOP_PB_Trig(CLK := I_STOP_PB);
I_RESET_PB_Trig(CLK := I_RESET_PB);
M_TotalCount_Trig(CLK := I_M_TotalCount);
M_MetalCount_Trig(CLK := I_M_MetalCount);

(* ─ Safety Overrides ─────────────────────── *)
IF EmergencyStop THEN M_State := 99; END_IF;  
IF I_ESTOP THEN M_State := 99; END_IF;  
IF I_ESTOP_Trig THEN M_State := 99; END_IF;  
IF I_E___name____ESTOP____type____emergency_stop__ THEN M_State := 99; END_IF;  
IF I_E___name____ESTOP____type____emergency_stop___Trig THEN M_State := 99; END_IF;

(* ─ State Machine ─────────────────────────── *)
CASE M_State OF
0: (* Idle *)
    IF I_START_PB THEN M_State := 1; END_IF;
1: (* Running *)
    IF I_STOP_PB THEN M_State := 0; END_IF;
    IF I_JAM_SENSOR THEN M_State := 2; END_IF;
    IF I_E___name____ESTOP____type____emergency_stop__ THEN M_State := 3; END_IF;
2: (* JamFault *)
    IF I_RESET_PB THEN M_State := 0; END_IF;
    IF I_E___name____ESTOP____type____emergency_stop__ THEN M_State := 3; END_IF;
3: (* EmergencyStop *)
    IF I_E___name____ESTOP____type____emergency_stop__ THEN M_State := 0; END_IF;
END_CASE;

(* ─ Timer Calls — State-Locked (outside IF, every scan) *)
T_SOL_201_Activation(IN := (M_State = 1), PT := T#5S);
T_JAM_SENSOR(IN := (M_State = 2), PT := T#5S);

(* ─ Deterministic Output Assignment (bottom only) ─── *)
Q_SOL_201 := (M_State = Running);
Q_M_RUN := (M_State = Running);
Q_JAM_FAULT := (M_State = JamFault);
Q_DIVERT_ACTIVE := (M_State = Running) AND (M_MetalCount > 0);

(* Call the timers to ensure they run *)
T_SOL_201_Activation(IN := (M_State = 1), PT := T#5S);
T_JAM_SENSOR(IN := (M_State = 2), PT := T#5S);

END_PROGRAM