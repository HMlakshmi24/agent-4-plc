from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union

# ---------------------------------------------------------
# LAYER 1: STRICT JSON SCHEMA FOR AI OUTPUT
# The AI must return exactly this structure. No ST allowed.
# ---------------------------------------------------------

class VariableModel(BaseModel):
    name: str = Field(..., description="Name of the variable cleanly formatted (e.g., StartButton)")
    type: Literal["BOOL", "INT", "REAL", "TIME", "WORD", "DWORD", "STRING"] = Field(..., description="IEC 61131-3 Data Type")
    init: Optional[Union[int, float, bool, str]] = Field(None, description="Optional initial value")

class TimerModel(BaseModel):
    name: str = Field(..., description="Instance name of the timer (e.g., TMR1)")
    type: Literal["TON", "TOF", "TP"] = Field(..., description="Timer Type")
    in_trigger: str = Field(..., alias="in", description="Variable or condition triggering the timer")
    pt: str = Field(..., description="Preset Time (e.g., T#5s)")

class CounterModel(BaseModel):
    name: str = Field(..., description="Instance name of the counter (e.g., CT1)")
    type: Literal["CTU", "CTD", "CTUD"] = Field(..., description="Counter Type")
    cu: Optional[str] = Field(None, description="Count Up trigger variable")
    cd: Optional[str] = Field(None, description="Count Down trigger variable")
    r: Optional[str] = Field(None, description="Reset variable")
    pv: int = Field(..., description="Preset Value (integer)")

class LogicAssignModel(BaseModel):
    type: Literal["assign"] = "assign"
    target: str = Field(..., description="The variable being assigned to")
    value: str = Field(..., description="The boolean or arithmetic expression (e.g., 'A AND B')")

class ProgramSchema(BaseModel):
    program_name: str = Field(..., description="Name of the PLC program (alphanumeric, no spaces)")
    inputs: List[VariableModel] = Field(default_factory=list, description="List of input variables (Sensors, Buttons)")
    outputs: List[VariableModel] = Field(default_factory=list, description="List of output variables (Motors, Valves)")
    internals: List[VariableModel] = Field(default_factory=list, description="List of internal state variables")
    timers: List[TimerModel] = Field(default_factory=list, description="List of timers used")
    counters: List[CounterModel] = Field(default_factory=list, description="List of counters used")
    logic: List[LogicAssignModel] = Field(default_factory=list, description="Ordered list of assignment logic statements")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "program_name": "LogicGate",
                "inputs": [
                    {"name": "A", "type": "BOOL"},
                    {"name": "B", "type": "BOOL"}
                ],
                "outputs": [
                    {"name": "C", "type": "BOOL"}
                ],
                "internals": [],
                "timers": [],
                "counters": [],
                "logic": [
                    {"type": "assign", "target": "C", "value": "A AND B"}
                ]
            }
        }
