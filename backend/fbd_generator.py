
def generate_fbd_blocks(domain: str):

    if domain == "heater":
        return """
(* Heater FBD *)
TempLow ----> HeaterOut
TempHigh ----|NOT|----> HeaterOut
"""

    if domain == "tank" or domain == "filling":
        return """
(* Tank FBD *)
LevelLow ----> FillValve
LevelHigh ----|NOT|----> FillValve
"""


    if domain == "traffic":
        return """
(* Traffic FBD *)
Start ----[TON]----> TimerDone
TimerDone ----> GreenLight
"""

    if domain == "mixing":
        return """
(* Mixing FBD *)
Start --|AND|-- LevelHit ----> Agitator
Empty ----> OutletValve
"""

    return """
(* Default FBD *)
Start ----> Motor
"""
