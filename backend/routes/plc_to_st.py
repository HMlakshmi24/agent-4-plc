from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

# ✅ Import agent + HumanMessage
from src.langchain_create_agent import create_agent
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/plc", tags=["plc"])

class TextInput(BaseModel):
    requirement: str  # User will send a plain text requirement

@router.post("/generate")
async def generate_st(input_data: TextInput):
    try:
        # ================================
        # Create the Agent
        # ================================
        agent = create_agent(
            backend="openai",
            chat_model="gpt-4o",
            system_msg="You are an expert PLC engineer. Explain Mitsubishi FX/ST ladder logic in plain English.",
            system_msg_is_dir=False,
            include_rag=False
        )

        # ================================
        # Run the Agent
        # ================================
        response = agent.invoke([HumanMessage(content=input_data.requirement)])

        # Extract actual ST code text
        st_code = response.content

        # Save as .st file (Unicode-safe)
        output_path = Path("generated_code.st")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(st_code)
        except UnicodeEncodeError:
            safe_output = st_code.replace("→", "->")
            with open(output_path, "w", encoding="cp1252") as f:
                f.write(safe_output)

        return {
            "st_code": st_code,
            "message": f"✅ ST code generated and saved to {output_path}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
