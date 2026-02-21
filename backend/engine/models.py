
from pydantic import BaseModel
from typing import List, Optional

class Element(BaseModel):
    type: str # contact, coil, timer
    name: str # Stop_Btn, Motor_Coil
    normally_closed: Optional[bool] = False
    timer_type: Optional[str] = None
    preset: Optional[str] = None

class Output(BaseModel):
    type: str # coil, timer
    name: str
    timer_type: Optional[str] = None # For timers
    preset: Optional[str] = None

class Rung(BaseModel):
    title: str
    branches: List[List[Element]] # Parallel branches of elements
    output: Optional[Output] = None # Output coil/timer

class LDProgram(BaseModel):
    program_name: str
    rungs: List[Rung]
