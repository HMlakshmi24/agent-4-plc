pascal
PROGRAM TempControlLoop
VAR
    (* Inputs *)
    I_Thermocouple : BOOL;
    I_E___condition____TT_401___160____action____sets_HI_TEMP_ALARM__cut_heater__ : BOOL;
    I_E___condition____TT_401___180____action____sets_HI_HI_TEMP_ALARM__cut_heater_open_cooling_to_100_percent__ : BOOL;
    (* Outputs *)
    Q_PID_Output : BOOL := FALSE;
    Q_HI_TEMP_Alarm : BOOL := FALSE;
    Q_HI_HI_TEMP_Alarm : BOOL := FALSE;
    (* Safety Flags *)
    M_HI_TEMP_Alarm : BOOL := FALSE;
    M_HI_HI_TEMP_Alarm : BOOL := FALSE;
    I_E___condition____TT_401___160____action____sets_HI_TEMP_ALARM__cut_heater__ : BOOL := FALSE;
    I_E___condition____TT_401___180____action____sets_HI_HI_TEMP_ALARM__cut_heater_open_cooling_to_100_percent__ : BOOL := FALSE;
    (* Internal States *)
    M_Batch_Running : BOOL := FALSE;
    M_Count : INT := 0;
    (* Edge Detection *)
    I_Thermocouple_Trig : R_TRIG;
    M_Count_Trig : R_TRIG;
    (* Timers *)
    T_I : TON;
    T_D : TON;
    (* State Machine *)
    M_State : INT := 0; (* 0 = Idle *)
END_VAR

(* ─ Edge Detection ────────────────────────────── *)
I_Thermocouple_Trig(CLK := xI_Thermocouple);
M_Count_Trig(CLK := xM_Count);

(* ─ Safety Overrides ─────────────────────── *)
IF HighTempAlarm THEN M_State := 99; END_IF;  
IF HighHighTempAlarm THEN M_State := 99; END_IF;

(* ─ State Machine ─────────────────────────── *)
CASE M_State OF
0: (* Idle *)
    IF I_Thermocouple THEN M_State := 1; END_IF;
1: (* Heating *)
    IF I_E___condition____TT_401___160____action____sets_HI_TEMP_ALARM__cut_heater__ THEN M_State := 3; END_IF;
    IF I_E___condition____TT_401___180____action____sets_HI_HI_TEMP_ALARM__cut_heater_open_cooling_to_100_percent__ THEN M_State := 4; END_IF;
2: (* Cooling *)
    IF I_Thermocouple THEN M_State := 0; END_IF;
3: (* HighTempAlarm *)
    IF I_E___condition____TT_401___180____action____sets_HI_HI_TEMP_ALARM__cut_heater_open_cooling_to_100_percent__ THEN M_State := 2; END_IF;
4: (* HighHighTempAlarm *)
    IF I_E___condition____TT_401___180____action____sets_HI_HI_TEMP_ALARM__cut_heater_open_cooling_to_100_percent__ THEN M_State := 2; END_IF;
END_CASE;

(* ─ Timer Calls — State-Locked (outside IF, every scan) *)
T_I(IN := (M_State = 1), PT := T#5S);
T_D(IN := (M_State = 2), PT := T#5S);

(* ─ Deterministic Output Assignment (bottom only) ─── *)
Q_PID_Output := (Heating) AND NOT (Cooling);
Q_HI_TEMP_Alarm := HighTempAlarm;
Q_HI_HI_TEMP_Alarm := HighHighTempAlarm;

(* Call timers to ensure they run *)
T_I(IN := (M_State = 1), PT := T#5S);
T_D(IN := (M_State = 2), PT := T#5S);

END_PROGRAM