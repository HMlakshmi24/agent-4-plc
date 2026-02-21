
def validate_domain(description, code):
    """
    Validates that the generated code aligns with the requested domain.
    """
    d = description.lower()
    c = code.lower()

    if "pressure" in d:
        if "pressure" not in c and "pump" not in c:
            return False, "Pressure logic missing"

    if "tank" in d or "level" in d:
        if "valve" not in c and "pump" not in c and "fill" not in c:
            return False, "Tank/Level logic missing (valve/pump)"

    if "coffee" in d:
        if "heater" not in c:
            return False, "Coffee heater missing"

    if "mix" in d or "agitator" in d:
        if "agitator" not in c and "mix" not in c:
            return False, "Mixing agitator missing"
            
    if "lift" in d or "elevator" in d:
        if "motor" not in c and "door" not in c:
            return False, "Lift components missing"
            
    if "traffic" in d:
        if "red" not in c and "green" not in c:
            return False, "Traffic light outputs missing"

    return True, ""
