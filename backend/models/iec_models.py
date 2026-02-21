from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Variable(BaseModel):
    name: str = Field(..., description="IEC 61131-3 Variable Name (e.g. StartBtn, Timer1)")
    type: str = Field(..., description="IEC Data Type (BOOL, INT, TIME, TON, TOF, REAL)")
    initial_value: Optional[str] = Field(None, description="Optional initial value (e.g. T#10s, 0, TRUE)")
    comment: Optional[str] = Field(None, description="Optional comment describing the variable")

class TimerConfig(BaseModel):
    name: str
    type: str # TON, TOF, TP
    pt: str # Preset Time (e.g. T#5s)
    in_var: str # Trigger variable

class ProgramModel(BaseModel):
    name: str = Field(..., description="Program Name (e.g. TrafficLight)")
    inputs: List[Variable] = Field(default_factory=list, description="VAR_INPUT variables")
    outputs: List[Variable] = Field(default_factory=list, description="VAR_OUTPUT variables")
    # We combine internal vars and timers in the final VAR block, but keep them distinct for AI clarity if needed.
    # For simplicity, let's allow AI to put everything else in 'internals'
    internals: List[Variable] = Field(default_factory=list, description="VAR variables (Internal states, timers, counters)")
    
    # We want logic to be a list of strings for now, or structured? 
    # Strict mode: List of strings is safer than trying to model every IF/THEN statement in JSON yet.
    # The "Compiler" will wrap this in the body.
    logic: List[str] = Field(..., description="Sequential lines of ST logic. Do NOT include VAR/END_VAR here.")
