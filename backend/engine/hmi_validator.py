
import json

def validate_hmi_layout(json_text):

    try:
        if isinstance(json_text, dict):
            data = json_text
        else:
            cleaned = json_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
    except Exception as e:
        return {"valid": False, "error": f"Invalid JSON: {str(e)}"}

    # Accept both new schema (title) and legacy schema (system_name)
    has_title = "title" in data or "system_name" in data
    if not has_title:
        return {"valid": False, "error": "Missing 'title' or 'system_name'"}

    if "components" not in data:
        return {"valid": False, "error": "Missing 'components'"}

    if not isinstance(data["components"], list):
        return {"valid": False, "error": "components must be a list"}

    for i, comp in enumerate(data["components"]):
        if "type" not in comp:
            return {"valid": False, "error": f"Component {i} missing 'type'"}
        # Auto-assign id if missing
        if "id" not in comp:
            comp["id"] = f"{comp.get('type','c')}_{i}"
        # Auto-assign x,y if missing
        if "x" not in comp:
            comp["x"] = 80 + (i % 5) * 160
        if "y" not in comp:
            comp["y"] = 100 + (i // 5) * 160

    # Normalise: surface title as both keys
    if "title" not in data and "system_name" in data:
        data["title"] = data["system_name"]
    if "system_name" not in data and "title" in data:
        data["system_name"] = data["title"]

    return {"valid": True, "data": data}
