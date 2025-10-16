Below is the Structured Text (ST) code for a Siemens S7-1200 PLC in TIA Portal format based on the provided requirements:

```pascal
VAR
    TankLevel : REAL;
    OutletValve : BOOL;
    InletValve : BOOL;
    Pump : BOOL;
END_VAR

// Tank Level Control Logic
IF TankLevel > 80.0 THEN
    OutletValve := TRUE;
ELSE
    OutletValve := FALSE;
END_IF;

IF TankLevel < 20.0 THEN
    InletValve := TRUE;
    Pump := TRUE;
ELSE
    InletValve := FALSE;
    Pump := FALSE;
END_IF;

// Ensure all valves closed and pump off between 20.0 and 80.0
IF (TankLevel >= 20.0) AND (TankLevel <= 80.0) THEN
    OutletValve := FALSE;
    InletValve := FALSE;
    Pump := FALSE;
END_IF;
```

### Explanation:

- **Variable Declaration:** The variables `TankLevel`, `OutletValve`, `InletValve`, and `Pump` are declared at the beginning. These variables will be linked to physical addresses in the PLC tag table.
  
- **Logic Implementation:**
  - The first `IF` block handles the condition where `TankLevel` exceeds 80.0, turning the `OutletValve` on and off appropriately.
  - The second `IF` block checks if `TankLevel` is below 20.0, turning both the `InletValve` and `Pump` on when necessary.
  - The final `IF` block ensures that between 20.0 and 80.0, all outputs (`OutletValve`, `InletValve`, `Pump`) are set to FALSE.

- **Testing Scenarios:** The code logic satisfies the following conditions:
  - At 10% (or below 20.0), both the `InletValve` and `Pump` are activated.
  - At 50% (or between 20.0 and 80.0), all outputs remain inactive.
  - At 90% (or above 80.0), the `OutletValve` is activated.

This code is ready for importing into Siemens TIA Portal, where it can be linked to appropriate hardware configurations in the tag table and verified against the desired simulation scenarios.