from fastapi import APIRouter
from pydantic import BaseModel
from backend.llm_generator import llm_generator

router = APIRouter(prefix="/offline", tags=["Offline Generation"])


class PLCRequest(BaseModel):
    brand: str
    language: str = "ST"
    program_name: str = "Main"
    description: str


@router.post("/generate")
async def generate_offline(request: PLCRequest):
    result = llm_generator.generate(request)
    return result
