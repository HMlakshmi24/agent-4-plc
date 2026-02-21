from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Literal

# --- Base Types ---
class Variable(BaseModel):
    name: str
    type: str # BOOL, INT, REAL, TIME, etc.
    initial_value: Optional[str] = None
    comment: Optional[str] = None

class TimerConfig(BaseModel):
    name: str # T1
    type: Literal["TON", "TOF", "TP"]
    pt: str # T#5s - Default if not overridden in call
    comment: Optional[str] = None

class CounterConfig(BaseModel):
    name: str # C1
    type: Literal["CTU", "CTD", "CTUD"]
    pv: int # Default PV
    comment: Optional[str] = None

# --- Logic Blocks (Recursive) ---

class AssignBlock(BaseModel):
    type: Literal["ASSIGN"] = "ASSIGN"
    variable: str
    value: str # Expression or variable name

class IfBlock(BaseModel):
    type: Literal["IF"] = "IF"
    condition: str
    then_body: List['LogicBlock']
    else_body: Optional[List['LogicBlock']] = None
    elsif_blocks: Optional[List[Dict[str, List['LogicBlock']]]] = None # Simple Condition -> Body mapping? Complex to model Pydanticly strict. use list of objects.

class CaseItem(BaseModel):
    values: str # "1", "1, 2", "1..5"
    body: List['LogicBlock']

class CaseBlock(BaseModel):
    type: Literal["CASE"] = "CASE"
    expression: str
    cases: List[CaseItem]
    else_body: Optional[List['LogicBlock']] = None

class ForBlock(BaseModel):
    type: Literal["FOR"] = "FOR"
    iterator: str
    start_value: str
    end_value: str
    by_value: Optional[str] = None
    body: List['LogicBlock']

class WhileBlock(BaseModel):
    type: Literal["WHILE"] = "WHILE"
    condition: str
    body: List['LogicBlock']

class FBCallBlock(BaseModel):
    type: Literal["FB_CALL"] = "FB_CALL"
    name: str # generic FB or Timer instance name
    params: Dict[str, str] # IN := ..., PT := ...

class CommentBlock(BaseModel):
    type: Literal["COMMENT"] = "COMMENT"
    text: str

# Union for Recursion
LogicBlock = Union[AssignBlock, IfBlock, CaseBlock, ForBlock, WhileBlock, FBCallBlock, CommentBlock]

# Update forward references for recursive models
IfBlock.model_rebuild()
CaseBlock.model_rebuild()
CaseItem.model_rebuild()
ForBlock.model_rebuild()
WhileBlock.model_rebuild()

# --- Main Program Model ---
class IECProgramModel(BaseModel):
    program_name: str
    inputs: List[Variable] = []
    outputs: List[Variable] = []
    internals: List[Variable] = []
    timers: List[TimerConfig] = []
    counters: List[CounterConfig] = []
    logic: List[LogicBlock] = []
