import json

def validate_layout(raw_json: str):

    try:
        data = json.loads(raw_json)
    except:
        # Try to clean markdown if allowed, but strict rules say "No markdown".
        # However, to be "Production-Stable", we should probably handle it if the LLM slips.
        try:
             if "```" in raw_json:
                 cleaned = raw_json.split("```json")[-1].split("```")[0].strip()
                 if not cleaned: # Handle case where it might be just ```
                     cleaned = raw_json.split("```")[-1].split("```")[0].strip()
                 data = json.loads(cleaned)
             else:
                 raise ValueError
        except:
             raise ValueError("Invalid JSON format from AI")

    if data.get("style") not in ["dashboard", "pid"]:
        raise ValueError(f"Invalid style: {data.get('style')}")

    if "system_name" not in data:
        raise ValueError("Missing system_name")

    components = data.get("components")

    if not isinstance(components, list) or len(components) < 4:
        raise ValueError("Minimum 4 components required")

    used_positions = set()

    for comp in components:
        for field in ["id", "type", "name", "x", "y"]:
            if field not in comp:
                raise ValueError(f"Missing {field} in component")
        
        # Grid/Overlap Check (Simple exact match)
        # In production, we might want a radius check, but strictly following requirements:
        pos = (comp["x"], comp["y"])

        if pos in used_positions:
             # Just warn or shift? User said "Coordinates must not overlap" (Rule).
             # Validator raises ValueError as per user code.
             raise ValueError(f"Overlapping components at {pos}")

        used_positions.add(pos)

    if data["style"] == "pid" and len(components) < 5:
        raise ValueError("P&ID requires minimum 5 components")

    return data
