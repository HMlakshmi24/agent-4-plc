Here's a Structured Text (ST) code template for the Siemens S7-1200 PLC, following your guidelines:

```structured-text
// Declare variables
VAR
    TankLevel : REAL;        // Mapped to %MW10
    OutletValve : BOOL;      // Mapped to %Q0.0
    InletValve : BOOL;       // Mapped to %Q0.1
    Pump : BOOL;             // Mapped to %Q0.2
END_VAR

// Logic to control the OutletValve based on TankLevel
IF TankLevel > 80.0 THEN
    OutletValve := TRUE;
ELSE
    OutletValve := FALSE;
END_IF;

// Logic to control the InletValve and Pump based on TankLevel
IF TankLevel < 20.0 THEN
    InletValve := TRUE;
    Pump := TRUE;
ELSE
    InletValve := FALSE;
    Pump := FALSE;
END_IF;

// Ensure all valves and pump are off when TankLevel is between 20 and 80
IF TankLevel >= 20.0 AND TankLevel <= 80.0 THEN
    OutletValve := FALSE;
    InletValve := FALSE;
    Pump := FALSE;
END_IF;
```

### Explanation:

1. **Variable Declaration**: Variables for the tank control are declared at the beginning, as specified. These include `TankLevel`, `OutletValve`, `InletValve`, and `Pump`.

2. **Logic Implementation**:
   - **OutletValve**: When `TankLevel` is greater than 80.0, `OutletValve` is set to `TRUE`; otherwise, it is set to `FALSE`.
   - **InletValve and Pump**: When `TankLevel` is less than 20.0, both `InletValve` and `Pump` are set to `TRUE`. Otherwise, they are set to `FALSE`.
   - **Intermediate Range (20.0 to 80.0)**: In this range, all devices (`OutletValve`, `InletValve`, `Pump`) are explicitly set to `FALSE` to ensure no unintended behavior.

3. **End Conditions**: Each conditional block is closed with `END_IF` to properly structure the logic.

This code should compile successfully in TIA Portal. In simulation:
- At `TankLevel = 10.0`, both `InletValve` and `Pump` should be `TRUE`.
- At `TankLevel = 50.0`, all outputs should be `FALSE`.
- At `TankLevel = 90.0`, `OutletValve` should be `TRUE`.