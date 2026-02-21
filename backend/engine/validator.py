import json

def validate_layout(raw_json):

    try:
        data = json.loads(raw_json)
    except:
        # Try to clean markdown if present (just in case)
        try:
            cleaned = raw_json.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
        except:
            raise ValueError("Invalid JSON from AI")

    # Handling legacy nesting if model hallucinates it, but user wants strict.
    # User said "NOT nested".
    # I will stick to what user requested: Flat structure.

    if str(data.get("style")).lower() not in ["dashboard", "pid"]:
         # Auto-fix case sensitivity
         if "pid" in str(data.get("style")).lower():
             data["style"] = "pid"
         elif "dash" in str(data.get("style")).lower():
             data["style"] = "dashboard"
         else:
             raise ValueError("Invalid style value")

    if not isinstance(data.get("components"), list):
        raise ValueError("components must be list")

    if len(data["components"]) < 1:
        raise ValueError("No components returned")

    for comp in data["components"]:
        required = ["id", "type", "name", "x", "y"]
        for field in required:
            if field not in comp:
                raise ValueError(f"Component missing field: {field}")

    return data
