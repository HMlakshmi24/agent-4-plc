from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.domain_detector import detect_domain
from backend.openai_client import generate_logic
from backend.skeleton_engine import get_skeleton
from backend.industrial_iec_validator import IndustrialIECValidator
from backend.domain_validator import validate_domain
from backend.iec_final_fixer import final_iec_fix
from backend.iec_engine.build_pipeline import build_plc_code # V4 Import

router = APIRouter()

class PLCRequest(BaseModel):
    program_name: str
    brand: str
    language: str
    description: str

@router.post("/generate")
def generate(request_body: PLCRequest, http_request: Request):

    email = http_request.headers.get("X-User-Email")
    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(status_code=403, detail="You have reached the 50k quota. Please continue with renewal.")
    
    # Map back original variable for rest of function
    request = request_body

    # 1. Detect domain
    domain = detect_domain(request.description)

    # 2. Get skeleton
    skeleton = get_skeleton(
        request.brand,
        request.language,
        domain
    )

    # 3. Generate logic
    lang = request.language.upper()
    
    # Token tracker for the request
    total_consumed_tokens = 0
    
    if lang == "ST":
        # 🔥 PURE LLM 3-STAGE AGENTIC ORCHESTRATION PIPELINE
        from backend.engine.agentic_pipeline import run_agentic_pipeline
        
        try:
            # 1. Generator -> 2. Validator -> 3. AutoFix (Sequential LLM Consensus)
            strict_code, total_consumed_tokens = run_agentic_pipeline(request.description, request.program_name, request.brand)
            
            # Post-processing (Standard Fixer for nice formatting if needed)
            final_code = final_iec_fix(strict_code, request.program_name)

            # Update true tokens drawn from response.usage!
            if email:
                from backend.token_manager import check_and_update_tokens
                check_and_update_tokens(email, total_consumed_tokens)

            return {
                "code": final_code,
                "iec_valid": True,  # Forced Valid by Stage 2 Agent
                "iec_errors": [],
                "iec_warnings": [],
                "domain_valid": True,
                "domain_error": None,
                "domain": domain
            }
        except Exception as e:
            from backend.engine.agentic_pipeline import IECValidationError
            if isinstance(e, IECValidationError) and getattr(e, "code", None):
                final_code = final_iec_fix(e.code, request.program_name)
                if email and getattr(e, "tokens", 0) > 0:
                    from backend.token_manager import check_and_update_tokens
                    check_and_update_tokens(email, e.tokens)
                warnings = ["Validation Failed: " + str(e.errors).split("\n")[0]]
                return {
                    "code": final_code,
                    "iec_valid": False,
                    "iec_errors": [str(e.errors)],
                    "iec_warnings": warnings,
                    "fixes_applied": warnings, 
                    "domain_valid": True,
                    "domain_error": None,
                    "domain": domain
                }
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"3-Stage Agentic Pipeline Error: {str(e)}")

    else:
        # Default to Old Engine for other languages (LD, SFC)
        logic = generate_logic(request.description, request.language)

    # Clean up markdown if AI used
    clean_logic = logic.replace("```st", "").replace("```", "").strip()

    # Pre-processing: Strip PROGRAM/END_PROGRAM if AI disobeyed (Structure Enforcer)
    if "PROGRAM" in clean_logic.upper():
        # Try to extract content between PROGRAM and END_PROGRAM, or just strip lines containing them
        lines = clean_logic.split('\n')
        filtered_lines = []
        for line in lines:
            upper_line = line.strip().upper()
            if upper_line.startswith("PROGRAM") or upper_line.startswith("END_PROGRAM"):
                continue
            filtered_lines.append(line)
        clean_logic = "\n".join(filtered_lines).strip()

    # 4. Insert logic
    if "{logic}" in skeleton:
        code = skeleton.replace("{logic}", clean_logic)
    else:
        code = skeleton + "\n" + clean_logic

    # 5. IEC validation (Industrial 25-rule)
    iec_result = IndustrialIECValidator.validate(code)
    
    # 7. Domain validation
    domain_ok, msg = validate_domain(request.description, code)

    # 8. Final fix
    final_code = final_iec_fix(code, request.program_name)

    if email and lang != "ST":
        from backend.token_manager import check_and_update_tokens
        # Fallback estimation for non-agentic routes (LD, SFC) 
        # Since standard generate logic doesn't return usage dynamically yet
        used_tokens = (len(request.description) // 4) + (len(final_code) // 4) + 200
        check_and_update_tokens(email, used_tokens)

    return {
        "code": final_code,
        "iec_valid": iec_result["valid"],
        "iec_errors": iec_result["errors"],
        "iec_warnings": iec_result["warnings"],
        "domain_valid": domain_ok,
        "domain_error": msg,
        "domain": domain
    }
