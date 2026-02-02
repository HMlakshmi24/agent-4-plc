from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

# ✅ Import agent + HumanMessage
from backend.routes.langchain_create_agent import create_agent
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

# Load env to get PLC_OUTPUT_DIR
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
PLC_OUTPUT_DIR = os.getenv("PLC_OUTPUT_DIR", "backend/plc")

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
            system_msg=(
    "You are a senior industrial PLC engineer working under IEC 61131-3 standards. "
    "Generate ONLY valid Structured Text (ST) suitable for industrial controllers.\n"
    "Mandatory rules:\n"
    "- Strict IEC 61131-3 syntax only\n"
    "- PROGRAM or FUNCTION_BLOCK must be explicitly declared\n"
    "- All variables must be declared with explicit IEC types\n"
    "- Use VAR / VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT correctly\n"
    "- No vendor-specific keywords or libraries\n"
    "- No comments explaining logic in natural language\n"
    "- No markdown, no explanations, no test data\n"
    "- Deterministic execution; safe for cyclic PLC scan\n"
    "- No recursion, no dynamic allocation, no side effects\n"
    "- Output MUST be directly compilable ST code\n"
),

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
        output_dir = Path(PLC_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "generated_code.st"
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
            system_msg=(
    "You are a senior SCADA/HMI engineer. "
    "Generate ONLY industrial-grade HTML following ISA-101 and "
    "high-performance HMI standards.\n"
    "Hard constraints:\n"
    "- Output ONLY valid HTML\n"
    "- No JavaScript unless strictly required for value display\n"
    "- Neutral gray background, black/white text by default\n"
    "- Red, amber, or yellow ONLY for alarms or abnormal states\n"
    "- No gradients, shadows, animations, or styling for aesthetics\n"
    "- Clear separation of status, controls, and alarms\n"
    "- Industrial terminology only (START, STOP, RESET, FAULT)\n"
    "- Layout must resemble a real HMI panel, not a web page\n"
    "- No external CSS, JS, fonts, or images\n"
),
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
        output_dir = Path(PLC_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "generated_hmi.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(hmi_code.strip())

        return {
            "hmi_code": hmi_code,
            "message": f"✅ HMI HTML file generated and saved to {output_path}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
