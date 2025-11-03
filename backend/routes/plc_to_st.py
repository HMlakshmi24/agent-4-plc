from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

# ✅ Import agent + HumanMessage
from backend.routes.langchain_create_agent import create_agent
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/plc", tags=["plc"])

class TextInput(BaseModel):
    requirement: str  # User will send a plain text requirement


# ======================================================
# ✅ 1. Generate PLC Structured Text (.st) file
# ======================================================
@router.post("/generate")
async def generate_st(input_data: TextInput):
    try:
        # ================================
        # Create the Agent
        # ================================
        agent = create_agent(
            backend="openai",
            chat_model="gpt-4o",
            system_msg="You are an expert PLC engineer",
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



# ======================================================
# ✅ 2. Generate HMI HTML file
# ======================================================
@router.post("/generate-hmi")
async def generate_hmi(input_data: TextInput):
    try:
        # ================================
        # Create the Agent
        # ================================
        agent = create_agent(
            backend="openai",
            chat_model="gpt-4o",
            system_msg="You are an expert HMI and PLC engineer. Generate valid, minimal, and modern only HTML code for an industrial HMI interface based on the user's requirement. Do not include markdown or explanations — only HTML code.",
            system_msg_is_dir=False,
            include_rag=False
        )

        # ================================
        # Run the Agent
        # ================================
        response = agent.invoke([HumanMessage(content=input_data.requirement)])

        # Extract actual HTML code text
        hmi_code = response.content

        # Save as .html file (UTF-8)
        output_path = Path("generated_hmi.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(hmi_code.strip())

        return {
            "hmi_code": hmi_code,
            "message": f"✅ HMI HTML file generated and saved to {output_path}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
