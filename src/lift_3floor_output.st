```iec
PROGRAM AutomatedCarWashSystem
VAR
    State: ENUM {WAIT_FOR_CAR, PRE_WASH, SOAP, BRUSH, RINSE, DRY, FINISH, STOPPED};
    CarDetected, EmergencyStop, WaterPump, SoapPump, BrushMotor, RinsePump, Dryer, ExitGate: BOOL;
    TimerPreWash, TimerSoap, TimerBrush, TimerRinse, TimerDry, TimerFinish: TON;
    
    // Function blocks instantiation
    TimerPreWash(IN:=CarDetected, PT:=5000, Q=>TimerPreWash.Q);
    TimerSoap(IN:=WaterPump, PT:=7000, Q=>TimerSoap.Q);
    TimerBrush(IN:=SoapPump, PT:=10000, Q=>TimerBrush.Q);
    TimerRinse(IN:=BrushMotor, PT:=5000, Q=>TimerRinse.Q);
    TimerDry(IN:=RinsePump, PT:=8000, Q=>TimerDry.Q);
    TimerFinish(IN:=Dryer, PT:=0, Q=>TimerFinish.Q);
    
    // State machine logic
    CASE State OF
        WAIT_FOR_CAR:
            IF CarDetected THEN
                State := PRE_WASH;
            END_IF
        PRE_WASH:
            IF NOT EmergencyStop THEN
                WaterPump := TRUE;
                IF TimerPreWash.Q THEN
                    State := SOAP;
                END_IF
            ELSE
                // Emergency stop logic
                WaterPump := FALSE;
                State := STOPPED;
            END_IF
        SOAP:
            IF NOT EmergencyStop THEN
                SoapPump := TRUE;
                IF TimerSoap.Q THEN
                    State := BRUSH;
                END_IF
            ELSE
                SoapPump := FALSE;
                State := STOPPED;
            END_IF
        BRUSH:
            IF NOT EmergencyStop THEN
                BrushMotor := TRUE;
                IF TimerBrush.Q THEN
                    State := RINSE;
                END_IF
            ELSE
                BrushMotor := FALSE;
                State := STOPPED;
            END_IF
        RINSE:
            IF NOT EmergencyStop THEN
                RinsePump := TRUE;
                IF TimerRinse.Q THEN
                    State := DRY;
                END_IF
            ELSE
                RinsePump := FALSE;
                State := STOPPED;
            END_IF
        DRY:
            IF NOT EmergencyStop THEN
                Dryer := TRUE;
                IF TimerDry.Q THEN
                    State := FINISH;
                END_IF
            ELSE
                Dryer := FALSE;
                State := STOPPED;
            END_IF
        FINISH:
            IF NOT EmergencyStop THEN
                ExitGate := TRUE;
                IF TimerFinish.Q THEN
                    State := STOPPED;
                END_IF
            ELSE
                ExitGate := FALSE;
                State := STOPPED;
            END_IF
        STOPPED:
            // Clear all outputs
            WaterPump := FALSE;
            SoapPump := FALSE;
            BrushMotor := FALSE;
            RinsePump := FALSE;
            Dryer := FALSE;
            ExitGate := FALSE;
    END_CASE
END_PROGRAM
```

This code implements the automated car wash system using a state machine with enums, TON timers, and boolean variables for sensors and actuators. It also includes emergency stop logic that forces all outputs off and sets the state to STOPPED.