from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.domain_detector import detect_domain
from backend.openai_client import generate_logic
from backend.skeleton_engine import get_skeleton
from backend.industrial_iec_validator import IndustrialIECValidator
from backend.domain_validator import validate_domain
from backend.iec_final_fixer import final_iec_fix
from backend.iec_engine.build_pipeline import build_plc_code

router = APIRouter()


class PLCRequest(BaseModel):
    program_name: str
    brand: str
    language: str
    description: str


def _finalize_and_validate(code: str, program_name: str, brand: str) -> tuple[str, dict]:
    final_code = final_iec_fix(code, program_name)
    iec_result = IndustrialIECValidator.validate(final_code)
    return final_code, iec_result


def _track(email: str, tokens: int, endpoint: str = "/generate"):
    """Persist real token count to MongoDB. Skips if 0 or no email."""
    if not email or tokens <= 0:
        return
    from backend.token_manager import check_and_update_tokens
    check_and_update_tokens(email, tokens, endpoint)


@router.post("/generate")
def generate(request_body: PLCRequest, http_request: Request):

    email = http_request.headers.get("X-User-Email")

    # Pre-flight quota check (no deduction yet)
    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(
                status_code=403,
                detail="You have reached your token limit. Please upgrade to continue."
            )

    request = request_body

    # ── ST: Intelligent LLM-Powered Generator ─────────────────────────────────
    if request.language.upper() == "ST":
        try:
            # NEW: Use intelligent LLM-powered generator
            from backend.enhanced_intelligent_generator import generate_perfect_industrial_plc
            result = generate_perfect_industrial_plc(
                request.description, program_name=request.program_name, brand=request.brand
            )
            if result.get("code"):
                final_code, iec_result = _finalize_and_validate(
                    result["code"], request.program_name, request.brand
                )
                real_tokens = result.get("tokens_used", 0)
                _track(email, real_tokens, "/generate/intelligent")
                return {
                    "code":         final_code,
                    "iec_valid":    iec_result["valid"],
                    "iec_errors":   iec_result["errors"],
                    "iec_warnings": iec_result["warnings"] + result.get("warnings", []),
                    "domain_valid": True,
                    "domain_error": None,
                    "domain":       "intelligent_llm",
                    "confidence":   result.get("confidence", 0),
                    "model":        result.get("model", {}),
                    "tokens_used":  real_tokens,
                }
        except Exception as e:
            print(f"Intelligent generator failed, trying universal: {e}")

        try:
            from backend.universal_plc_generator import generate_perfect_industrial_plc as universal_gen
            result = universal_gen(request.description, program_name=request.program_name)
            if result.get("code"):
                final_code, iec_result = _finalize_and_validate(
                    result["code"], request.program_name, request.brand
                )
                real_tokens = result.get("tokens_used", 0)
                _track(email, real_tokens, "/generate/universal")
                return {
                    "code":         final_code,
                    "iec_valid":    iec_result["valid"],
                    "iec_errors":   iec_result["errors"],
                    "iec_warnings": iec_result["warnings"] + result.get("warnings", []),
                    "domain_valid": True,
                    "domain_error": None,
                    "domain":       "universal_plc",
                    "confidence":   result.get("confidence", 0),
                    "model":        result.get("model", {}),
                    "tokens_used":  real_tokens,
                }
        except Exception as e:
            print(f"Universal generator failed, trying industrial flow: {e}")

    # ── Industrial 11-layer pipeline ──────────────────────────────────────────
    try:
        from backend.industrial_flow_pipeline import generate_perfect_industrial_plc
        result = generate_perfect_industrial_plc(
            request.description, program_name=request.program_name
        )
        real_tokens = result.get("tokens_used", 0)
        _track(email, real_tokens, "/generate/industrial_flow")
        final_code, iec_result = _finalize_and_validate(
            result.get("code", ""), request.program_name, request.brand
        )
        return {
            "code":         final_code,
            "iec_valid":    iec_result["valid"],
            "iec_errors":   iec_result["errors"],
            "iec_warnings": iec_result["warnings"] + result.get("warnings", []),
            "domain_valid": True,
            "domain_error": None,
            "domain":       "industrial_flow",
            "confidence":   result.get("confidence", 0),
            "model":        result.get("model", {}),
            "tokens_used":  real_tokens,
        }
    except Exception as e2:
        print(f"Industrial flow failed, trying simple pipeline: {e2}")

    # ── Simple pipeline ───────────────────────────────────────────────────────
    try:
        from backend.simple_industrial_pipeline import generate_perfect_industrial_plc
        result = generate_perfect_industrial_plc(
            request.description, program_name=request.program_name
        )
        real_tokens = result.get("tokens_used", 0)
        _track(email, real_tokens, "/generate/simple")
        final_code, iec_result = _finalize_and_validate(
            result.get("code", ""), request.program_name, request.brand
        )
        return {
            "code":         final_code,
            "iec_valid":    iec_result["valid"],
            "iec_errors":   iec_result["errors"],
            "iec_warnings": iec_result["warnings"] + result.get("warnings", []),
            "domain_valid": True,
            "domain_error": None,
            "domain":       "simple_industrial",
            "confidence":   result.get("confidence", 0),
            "model":        result.get("model", {}),
            "tokens_used":  real_tokens,
        }
    except Exception as e3:
        print(f"All fast pipelines failed: {e3}")

    # ── Final fallback: agentic pipeline ─────────────────────────────────────
    domain   = detect_domain(request.description)
    skeleton = get_skeleton(request.brand, request.language, domain)
    lang     = request.language.upper()

    if lang == "ST":
        from backend.engine.agentic_pipeline import run_agentic_pipeline
        try:
            strict_code, actual_tokens = run_agentic_pipeline(
                request.description, request.program_name, request.brand
            )
            _track(email, actual_tokens, "/generate/agentic")
            final_code, iec_result = _finalize_and_validate(
                strict_code, request.program_name, request.brand
            )
            return {
                "code":         final_code,
                "iec_valid":    iec_result["valid"],
                "iec_errors":   iec_result["errors"],
                "iec_warnings": iec_result["warnings"],
                "domain_valid": True,
                "domain_error": None,
                "domain":       domain,
                "tokens_used":  actual_tokens,
            }
        except Exception as e:
            from backend.engine.agentic_pipeline import IECValidationError
            if isinstance(e, IECValidationError) and getattr(e, "code", None):
                final_code  = final_iec_fix(e.code, request.program_name)
                real_tokens = getattr(e, "tokens", 0)
                _track(email, real_tokens, "/generate/agentic_fallback")
                return {
                    "code":         final_code,
                    "iec_valid":    False,
                    "iec_errors":   [str(e.errors)],
                    "iec_warnings": ["Validation failed: " + str(e.errors).split("\n")[0]],
                    "domain_valid": True,
                    "domain_error": None,
                    "domain":       domain,
                    "tokens_used":  real_tokens,
                }
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    else:
        # Non-ST languages (LD, FBD, SFC)
        content, actual_tokens = generate_logic(request.description, request.language)
        _track(email, actual_tokens, f"/generate/{lang.lower()}")

        clean_logic = content.replace("```st", "").replace("```", "").strip()
        if "PROGRAM" in clean_logic.upper():
            lines = [
                l for l in clean_logic.split("\n")
                if not l.strip().upper().startswith(("PROGRAM", "END_PROGRAM"))
            ]
            clean_logic = "\n".join(lines).strip()

        code = (skeleton.replace("{logic}", clean_logic) if "{logic}" in skeleton
                else skeleton + "\n" + clean_logic)

        iec_result     = IndustrialIECValidator.validate(code)
        domain_ok, msg = validate_domain(request.description, code)
        final_code     = final_iec_fix(code, request.program_name)

        return {
            "code":         final_code,
            "iec_valid":    iec_result["valid"],
            "iec_errors":   iec_result["errors"],
            "iec_warnings": iec_result["warnings"],
            "domain_valid": domain_ok,
            "domain_error": msg,
            "domain":       domain,
            "tokens_used":  actual_tokens,
        }
