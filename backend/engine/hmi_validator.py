
import json

def validate_hmi_layout(json_text):

    try:
        # If it's already a dict, use it. If string, load it.
        if isinstance(json_text, dict):
            data = json_text
        else:
            # Clean possible markdown
            cleaned = json_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
    except Exception as e:
        return {"valid": False, "error": f"Invalid JSON: {str(e)}"}

    required = ["system_name", "style", "components"]

    for key in required:
        if key not in data:
            return {"valid": False, "error": f"Missing {key}"}

    if not isinstance(data["components"], list):
        return {"valid": False, "error": "components must be list"}

    # Basic component validation
    for i, comp in enumerate(data["components"]):
        if "id" not in comp:
             return {"valid": False, "error": f"Component at index {i} missing 'id'"}
        if "type" not in comp:
             return {"valid": False, "error": f"Component at index {i} missing 'type'"}
        if "x" not in comp or "y" not in comp:
             return {"valid": False, "error": f"Component at index {i} missing coordinates"}

    return {"valid": True, "data": data}
