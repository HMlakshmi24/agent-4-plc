
def generate_ld_rungs(domain: str):

    if domain == "heater":
        return """
NETWORK 1
(* Heater Control *)
| TempLow |----( HeaterOut )

NETWORK 2
(* Safety Cutoff *)
| TempHigh |----[/HeaterOut]
"""

    if domain == "tank":
        return """
NETWORK 1
(* Fill Control *)
| LevelLow |----( FillValve )

NETWORK 2
(* Stop Filling *)
| LevelHigh |----[/FillValve]
"""

    if domain == "traffic":
        return """
NETWORK 1
(* Traffic Light Timer *)
| Start |----[TON Timer1]----( Done )

NETWORK 2
(* Green Light *)
| Done |----( Green )
"""

    if domain == "mixing":
        return """
NETWORK 1
(* Start Mixing *)
| Start |---| LevelHit |----( Agitator )

NETWORK 2
(* Drain *)
| Empty |----( OutletValve )
"""

    if domain == "filling" or domain == "bottle":
        return """
NETWORK 1
(* Detect Bottle & Stop Conveyor *)
| BottleSensor |----( StopConveyor )

NETWORK 2
(* Open Fill Valve *)
| BottleSensor |----( FillValve )

NETWORK 3
(* Fill Timer *)
| FillValve |----[TON Timer1]----( FillDone )
PT = 5s

NETWORK 4
(* Restart Conveyor *)
| FillDone |----( StartConveyor )
"""

    return """
NETWORK 1
(* Default Rung *)
| Start |----( Motor )
"""
