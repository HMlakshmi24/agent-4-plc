from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

# ✅ Import agent + HumanMessage
from backend.routes.langchain_create_agent import create_agent
from backend.routes.hmi_export_formatter import HmiExportFormatter
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
from backend.routes.config import chat_model # Import configured model

# ✅ Import strict HMI system
from backend.routes.hmi_validator import HMI_SYSTEM_PROMPT, StrictHMIValidator
from backend.routes.one_shot_generator import OneShotGenerator # Use OneShot for ST
print(f"DEBUG: StrictHMIValidator loaded from {StrictHMIValidator}")
print(f"DEBUG: dir(StrictHMIValidator): {dir(StrictHMIValidator)}")

# Load env to get PLC_OUTPUT_DIR
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
PLC_OUTPUT_DIR = os.getenv("PLC_OUTPUT_DIR", "backend/plc")

router = APIRouter(prefix="/plc", tags=["plc"])

class TextInput(BaseModel):
    requirement: str  # User will send a plain text requirement
    current_hmi_code: str = None # Optional: Existing HMI code to modify
    style: str = "standard" # Optional: "standard" or "pid"
    temperature: float = 0.5 # Optional: LLM temperature (0-1) for generation determinism
    export_format: str = "html" # Optional: "html", "factorytalk", "webforms"


# ======================================================
# ✅ 1. Generate PLC Structured Text (.st) file
# ======================================================
@router.post("/generate")
async def generate_st(input_data: TextInput):
    try:
        # Use One Shot Generator for Strict ST
        generator = OneShotGenerator()
        brand = "generic" # Default for this endpoint
        
        result = generator.generate(
            requirement=input_data.requirement,
            brand=brand,
            language="ST"
        )
        
        st_code = result["code"]
        is_valid = result["validated"]
        
        # Add basic audit info if needed, or just return code
        # The existing frontend expects { "st_code": ..., "message": ... }

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
                
        status_msg = "✅ ST code generated" if is_valid else "⚠️ Generated with warnings"
        if not is_valid:
            status_msg += f": {result['errors']}"

        return {
            "st_code": st_code,
            "message": f"{status_msg}. Saved to {output_path}"
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
        # Define System Message - Use Strict HMI Prompt
        # ================================
        system_msg_content = HMI_SYSTEM_PROMPT

        # ================================
        # Create the Agent
        # ================================
        agent = create_agent(
            backend="openai",
            chat_model=chat_model,
            system_msg=system_msg_content,
            system_msg_is_dir=False,
            include_rag=False
        )

        # ================================
        # Run the Agent
        # ================================
        user_content = input_data.requirement
        if input_data.current_hmi_code:
            user_content = f"""
            Refer to this existing HMI code and MODIFY it according to the requirement below.
            Do NOT regenerate from scratch if possible, keep the existing structure but apply changes.
            
            EXISTING CODE:
            {input_data.current_hmi_code}
            
            REQUIREMENT:
            {input_data.requirement}
            """

        response = agent.invoke([HumanMessage(content=user_content)])

        # Extract actual HTML code text
        hmi_code = response.content

        # ================================
        # Validate HMI using Strict Validator
        # ================================
        is_valid, validation_errors = StrictHMIValidator.validate(hmi_code)
        validation_status = "✅ PASSED" if is_valid else "⚠️ WARNINGS"
        
        if not is_valid:
            hmi_code += f"\n<!-- VALIDATION WARNINGS:\n{chr(10).join(validation_errors)}\n-->"

        # ================================
        # Apply Export Format (NEW)
        # ================================
        export_format = input_data.export_format or "html"
        hmi_name = input_data.requirement[:30] if input_data.requirement else "HMI_Screen"
        try:
            filename, content_type, formatted_hmi = HmiExportFormatter.export(
                hmi_code, 
                export_format, 
                hmi_name
            )
        except Exception as e:
            # If export fails, use plain HTML
            filename = f"hmi_{hmi_name}.html"
            content_type = "text/html"
            formatted_hmi = hmi_code

        # Save as .html file (UTF-8)
        output_dir = Path(PLC_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_hmi.strip())

        return {
            "hmi_code": formatted_hmi,
            "export_format": export_format,
            "filename": filename,
            "content_type": content_type,
            "validation_status": validation_status,
            "validation_errors": validation_errors,
            "message": f"✅ HMI HTML file generated in {export_format} format and saved to {output_path}. {validation_status}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
