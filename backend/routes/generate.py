from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from backend.industrial_iec_validator import IndustrialIECValidator
from backend.iec_final_fixer import final_iec_fix

router = APIRouter()


class PLCRequest(BaseModel):
    program_name: str
    brand: str
    language: str
    description: str
    api_key: Optional[str] = None
    io_map: Optional[dict] = None


def _finalize_and_validate(code: str, program_name: str, brand: str) -> tuple[str, dict]:
    from backend.engine.vendor_profile import VendorProfileInjector
    final_code = final_iec_fix(code, program_name)
    final_code = VendorProfileInjector.apply(final_code, brand, program_name)
    iec_result = IndustrialIECValidator.validate(final_code)
    return final_code, iec_result


def _track(email: str, tokens: int, endpoint: str = "/generate"):
    if not email or tokens <= 0:
        print(f"[TRACK SKIP] email={email!r}  tokens={tokens}  (skipped)")
        return
    print(f"[TRACK] Writing {tokens} tokens for {email!r} at {endpoint}")
    from backend.token_manager import check_and_update_tokens
    result = check_and_update_tokens(email, tokens, endpoint)
    print(f"[TRACK DONE] tokens_used={result.get('tokens_used')}  remaining={result.get('remaining')}")


def _get_user_api_key(email: str) -> Optional[str]:
    """Fetch user's personal API key stored in their profile."""
    if not email:
        return None
    try:
        from backend.db import get_user_by_email
        import asyncio
        loop = asyncio.new_event_loop()
        user = loop.run_until_complete(get_user_by_email(email))
        loop.close()
        return user.get("api_key") if user else None
    except Exception:
        return None


@router.post("/generate")
def generate(request_body: PLCRequest, http_request: Request):
    email = http_request.headers.get("X-User-Email")
    print(f"[GENERATE] email={email!r}  brand={request_body.brand}  lang={request_body.language}")

    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(
                status_code=403,
                detail="You have reached your token limit. Please upgrade to continue.",
            )

    api_key = request_body.api_key or _get_user_api_key(email)

    if request_body.language.upper() == "ST":
        description = request_body.description
        tags = []

        if request_body.io_map:
            from backend.engine.io_mapper import build_io_context, parse_io_map_to_tags
            io_context = build_io_context(request_body.io_map, request_body.brand)
            description = f"{description}\n\n{io_context}"
            tags = parse_io_map_to_tags(request_body.io_map)

        try:
            from backend.enhanced_intelligent_generator import generate_perfect_industrial_plc
            graph_result = generate_perfect_industrial_plc(
                description,
                program_name=request_body.program_name,
                brand=request_body.brand,
            )
            if graph_result.get("clarification_needed"):
                return {
                    "code": "",
                    "iec_valid": False,
                    "iec_errors": graph_result.get("errors", []),
                    "iec_warnings": graph_result.get("warnings", []),
                    "domain_valid": False,
                    "domain_error": "Description too vague - see questions below",
                    "domain": "clarification_needed",
                    "tokens_used": 0,
                    "tag_list": [],
                    "clarification_needed": True,
                    "questions": graph_result.get("questions", []),
                    "confidence": graph_result.get("confidence", 0),
                }

            if graph_result.get("code"):
                final_code, iec_result = _finalize_and_validate(
                    graph_result["code"], request_body.program_name, request_body.brand
                )
                actual_tokens = graph_result.get("tokens_used", 0)
                _track(email, actual_tokens, "/generate/graph_primary")
                return {
                    "code": final_code,
                    "iec_valid": iec_result["valid"],
                    "iec_errors": iec_result["errors"],
                    "iec_warnings": iec_result["warnings"] + graph_result.get("warnings", []),
                    "domain_valid": True,
                    "domain_error": None,
                    "domain": "graph_primary",
                    "tokens_used": actual_tokens,
                    "tag_list": graph_result.get("tag_list", []),
                    "confidence": graph_result.get("confidence", 95),
                    "clarification_needed": False,
                    "explicitly_extracted": graph_result.get("explicitly_extracted", []),
                    "inferred_or_defaulted": graph_result.get("inferred_or_defaulted", []),
                }
        except Exception as e:
            print(f"[WARN] Graph generator failed ({e}), falling back to direct generation")

        try:
            from backend.enhanced_intelligent_generator import generate_st_direct
            code, actual_tokens = generate_st_direct(
                description, tags, request_body.program_name, request_body.brand
            )
            if code and len(code) > 200 and "FUNCTION_BLOCK" in code.upper():
                final_code, iec_result = _finalize_and_validate(
                    code, request_body.program_name, request_body.brand
                )
                _track(email, actual_tokens, "/generate/direct")
                return {
                    "code": final_code,
                    "iec_valid": iec_result["valid"],
                    "iec_errors": iec_result["errors"],
                    "iec_warnings": iec_result["warnings"],
                    "domain_valid": True,
                    "domain_error": None,
                    "domain": "direct_with_tags" if tags else "direct",
                    "tokens_used": actual_tokens,
                    "tag_list": tags,
                    "confidence": 95,
                    "clarification_needed": False,
                    "explicitly_extracted": [],
                    "inferred_or_defaulted": [],
                }
            print(f"[WARN] Direct gen produced insufficient output ({len(code)} chars), falling back to agentic")
        except Exception as e:
            print(f"[WARN] Direct generation failed ({e}), falling back to agentic pipeline")

        from backend.engine.agentic_pipeline import run_agentic_pipeline, IECValidationError
        try:
            strict_code, actual_tokens = run_agentic_pipeline(
                description,
                request_body.program_name,
                request_body.brand,
                api_key=api_key,
            )
            _track(email, actual_tokens, "/generate/agentic_fallback")

            final_code, iec_result = _finalize_and_validate(
                strict_code, request_body.program_name, request_body.brand
            )
            return {
                "code": final_code,
                "iec_valid": iec_result["valid"],
                "iec_errors": iec_result["errors"],
                "iec_warnings": iec_result["warnings"],
                "domain_valid": True,
                "domain_error": None,
                "domain": "agentic_fallback",
                "tokens_used": actual_tokens,
                "tag_list": [],
            }
        except IECValidationError as e:
            real_tokens = getattr(e, "tokens", 0)
            if getattr(e, "code", None) and real_tokens > 0:
                final_code = final_iec_fix(e.code, request_body.program_name)
                _track(email, real_tokens, "/generate/agentic_besteff")
                return {
                    "code": final_code,
                    "iec_valid": False,
                    "iec_errors": [str(e.errors)],
                    "iec_warnings": ["Returned best-effort code after fix attempts"],
                    "domain_valid": True,
                    "domain_error": None,
                    "domain": "agentic_fallback",
                    "tokens_used": real_tokens,
                    "tag_list": [],
                }
        except Exception as e2:
            print(f"[ERROR] All PLC pipelines failed: {e2}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {e2}")

    from backend.domain_detector import detect_domain
    from backend.openai_client import generate_logic
    from backend.skeleton_engine import get_skeleton
    from backend.domain_validator import validate_domain

    domain = detect_domain(request_body.description)
    skeleton = get_skeleton(request_body.brand, request_body.language, domain)

    content, actual_tokens = generate_logic(request_body.description, request_body.language)
    _track(email, actual_tokens, f"/generate/{request_body.language.lower()}")

    clean_logic = content.replace("```st", "").replace("```", "").strip()
    if "PROGRAM" in clean_logic.upper():
        lines = [
            line for line in clean_logic.split("\n")
            if not line.strip().upper().startswith(("PROGRAM", "END_PROGRAM"))
        ]
        clean_logic = "\n".join(lines).strip()

    code = skeleton.replace("{logic}", clean_logic) if "{logic}" in skeleton else f"{skeleton}\n{clean_logic}"

    iec_result = IndustrialIECValidator.validate(code)
    domain_ok, msg = validate_domain(request_body.description, code)
    final_code = final_iec_fix(code, request_body.program_name)

    return {
        "code": final_code,
        "iec_valid": iec_result["valid"],
        "iec_errors": iec_result["errors"],
        "iec_warnings": iec_result["warnings"],
        "domain_valid": domain_ok,
        "domain_error": msg,
        "domain": domain,
        "tokens_used": actual_tokens,
    }
