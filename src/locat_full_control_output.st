```iec
(* ===================================================================
   Automated Car Wash System in Structured Text
   ===================================================================
   This program controls an automated car wash sequence with the 
   following steps: pre-wash, wash, rinse, and dry. It includes 
   safety checks, alarm handling, and fail-safe behaviors.
   
   ## Summary of Inputs & Outputs ##

   INPUTS:
   - CarAtEntrySensor : BOOL;          // Detects car at entry.
   - DoorClosedSensor : BOOL;          // Detects if the car wash doors are closed.
   - EmergencyStop : BOOL;             // Detects if the emergency stop button is pressed.

   OUTPUTS:
   - PreWashPump : BOOL;               // Controls the pre-wash pump.
   - WashPump : BOOL;                  // Controls the wash pump.
   - RinsePump : BOOL;                 // Controls the rinse pump.
   - DryingFans : BOOL;                // Controls the drying fans.
   - ConveyorMotor : BOOL;             // Controls the conveyor motor.

   ALARMS:
   - AlarmActive : BOOL;               // Indicates an active alarm.
   - AlarmMessage : STRING[50];        // Describes the active alarm.
   =================================================================== *)

(* Declaration of variables *)

VAR
    CarAtEntrySensor : BOOL; // Detects car at entry
    DoorClosedSensor : BOOL; // Detects if doors are closed
    EmergencyStop : BOOL; // Emergency stop button
    
    PreWashPump : BOOL; // Pre-wash pump
    WashPump : BOOL; // Wash pump
    RinsePump : BOOL; // Rinse pump
    DryingFans : BOOL; // Drying fans
    ConveyorMotor : BOOL; // Conveyor motor
    
    PreWashTimer : TON; // Timer for pre-wash stage
    WashTimer : TON; // Timer for wash stage
    RinseTimer : TON; // Timer for rinse stage
    DryTimer : TON; // Timer for dry stage
    
    AlarmActive : BOOL; // Active alarm indicator
    AlarmMessage : STRING[50]; // Description of active alarm

    SequenceStep : INT; // Current step in wash sequence
    Faulted : BOOL; // System fault status
END_VAR

(* Initialization *)
PreWashPump := FALSE;
WashPump := FALSE;
RinsePump := FALSE;
DryingFans := FALSE;
ConveyorMotor := FALSE;
AlarmActive := FALSE;
AlarmMessage := '';
Faulted := FALSE;

(*  Car Wash Sequence Logic  *)

IF EmergencyStop THEN
    (* Emergency stop activated *)
    Faulted := TRUE;
    AlarmActive := TRUE;
    AlarmMessage := 'Emergency Stop Activated';
    (* Ensure all outputs are off *)
    PreWashPump := FALSE;
    WashPump := FALSE;
    RinsePump := FALSE;
    DryingFans := FALSE;
    ConveyorMotor := FALSE;
ELSE
    IF NOT Faulted THEN
        CASE SequenceStep OF
            0: (* Wait for car at entry *)
                IF CarAtEntrySensor AND DoorClosedSensor THEN
                    ConveyorMotor := TRUE;
                    SequenceStep := 1;
                END_IF

            1: (* Pre-wash stage *)
                ConveyorMotor := TRUE;
                PreWashPump := TRUE;
                PreWashTimer(IN := TRUE, PT := T#10s); // Pre-wash for 10 seconds
                IF PreWashTimer.Q THEN
                    PreWashPump := FALSE;
                    PreWashTimer(IN := FALSE);
                    SequenceStep := 2;
                END_IF

            2: (* Wash stage *)
                WashPump := TRUE;
                WashTimer(IN := TRUE, PT := T#20s); // Wash for 20 seconds
                IF WashTimer.Q THEN
                    WashPump := FALSE;
                    WashTimer(IN := FALSE);
                    SequenceStep := 3;
                END_IF

            3: (* Rinse stage *)
                RinsePump := TRUE;
                RinseTimer(IN := TRUE, PT := T#15s); // Rinse for 15 seconds
                IF RinseTimer.Q THEN
                    RinsePump := FALSE;
                    RinseTimer(IN := FALSE);
                    SequenceStep := 4;
                END_IF

            4: (* Dry stage *)
                DryingFans := TRUE;
                DryTimer(IN := TRUE, PT := T#10s); // Dry for 10 seconds
                IF DryTimer.Q THEN
                    DryingFans := FALSE;
                    DryTimer(IN := FALSE);
                    SequenceStep := 0; // Reset to waiting for new car
                END_IF

            ELSE
                (* Default case *)
                SequenceStep := 0;
        END_CASE
    END_IF
END_IF

(* Reset fault state if all conditions are clear *)
IF NOT EmergencyStop AND AlarmActive THEN
    Faulted := FALSE;
    AlarmActive := FALSE;
    AlarmMessage := '';
    SequenceStep := 0;
END_IF

(* ===================================================================
   Explanation of the Car Wash Sequence
   1. Wait for the car to be detected at the entry and doors to be closed.
   2. Start the conveyor and begin the pre-wash stage.
   3. Sequentially transition through wash, rinse, and dry stages using timers.
   4. Monitor emergency stop and faults, defaulting outputs to OFF when activated.
   5. Automatically reset after completing the sequence, or when conditions are clear.
   =================================================================== *)

(* ===================================================================
   LADDER DIAGRAM EQUIVALENT FOR WASH STAGE
   Below is an illustrative ladder logic snippet for the wash stage.
   ===================================================================
   
   // |--[CarAtEntrySensor]--[ ]--[ NOT EmergencyStop]--|
   // |                    |                           |
   // |--[WashPump]---------|                           |
   // |                                                  |
   // |--[WashTimer.Q]------[ NOT WashPump]--------------|
   
   =================================================================== *)
```

This code is structured and modular, allowing for clear understanding and maintenance. It ensures the wash sequence follows a strict order, monitoring for safety conditions and providing alarms in case of any issues.