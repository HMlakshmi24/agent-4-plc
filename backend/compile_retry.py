
from backend.openai_client import generate_logic
from backend.industrial_iec_validator import IndustrialIECValidator

def retry_if_failed(code, description, language):
    """
    Validates code. If it fails, asks AI to fix it ONCE.
    """
    result = IndustrialIECValidator.validate(code)

    if result["valid"]:
        return code, result

    # single retry
    error_text = "\n".join(result["errors"])
    print(f"⚠️ Validation Failed. Retrying... Errors: {error_text}")

    # For retry, we ask AI to fix specific errors
    # Note: We need to be careful. The generate_logic returns ONLY logic body usually.
    # But here we are validating the FULL code.
    # If the error is in the Logic part, we can ask to regenerate logic.
    # IF the error is structure ... the structure is likely fixed by skeleton.
    # So errors are likely logic errors (assignments etc).
    
    # We will try to regenerate the logic part with error context
    
    retry_prompt = f"""
The previous logic had errors:
{error_text}

original instructions:
{description}

Generate corrected logic only.
"""
    new_logic = generate_logic(retry_prompt, language)
    
    # We return just the new logic so the caller can re-assemble
    # Or, if we want this function to handle re-assembly, we'd need skeleton.
    # The user's snippet returns "new_logic". I assume the caller will handle re-insertion.
    
    return new_logic, result
