
def validate_language(language: str, code: str) -> bool:
    """
    Checks if the generated code contains keywords appropriate for the requested language.
    """
    c = code.upper()
    lang = language.upper()

    if lang == "LD":
        # LD shouldn't have structured text keywords like CASE or IF
        # (Unless generating structured text representation of ladder)
        # But per user request, we validate strictness.
        if "CASE " in c or "IF " in c:
            return False

    if lang == "FBD":
        if "CASE " in c or "IF " in c:
            return False

    if lang == "ST":
        # ST must have logic.
        if "CASE" not in c and "IF" not in c and ":=" not in c:
            return False

    return True
