import json

def normalize_layout(raw_json):
    """
    Normalizes the AI-generated JSON layout to ensure it has the required structure
    and valid component properties for the frontend renderers.
    """
    try:
        # 1. Parse JSON if it's a string
        if isinstance(raw_json, str):
            # Clean markdown code blocks if present
            cleaned = raw_json.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
        elif isinstance(raw_json, dict):
            data = raw_json
        else:
            # Fallback for unexpected types
            data = {}

        # 2. Force 'style' field
        # If AI put it in 'format' or format is missing, default to 'dashboard'
        if "style" not in data:
            if "format" in data:
                data["style"] = data["format"]
            else:
                data["style"] = "dashboard"

        # Normalize style to lowercase
        if isinstance(data["style"], str):
             data["style"] = data["style"].lower()

        # 3. Ensure 'system_name'
        if "system_name" not in data:
            data["system_name"] = "Untitled System"

        # 4. Ensure 'components' exists and is a list
        if "components" not in data or not isinstance(data["components"], list):
            data["components"] = []

        # 5. Normalize each component
        for i, comp in enumerate(data["components"]):
            # Ensure 'name'
            if "name" not in comp:
                comp["name"] = f"Component {i+1}"
            
            # Ensure 'id' (use name as fallback, or gen random?)
            # Use a sanitized version of name + index to ensure uniqueness
            if "id" not in comp:
                comp["id"] = f"{comp['name'].replace(' ', '_')}_{i}"
            
            # Ensure 'type' (default to generic box)
            if "type" not in comp:
                comp["type"] = "box"
            
            # Normalization for specific types
            if comp["type"] in ["alarm_list", "data_grid", "modal"]:
                 # Ensure defaults for these complex types if missing
                 comp.setdefault("width", 400)
                 comp.setdefault("height", 300)

            
            # Ensure positions (default to grid-like or 0,0)
            # If missing, put them in a diagonal line or 0,0 to prevent overlap hell?
            # For now, safe default.
            comp.setdefault("x", 50 + (i * 20))
            comp.setdefault("y", 50 + (i * 20))
            
            # Ensure properties dict
            comp.setdefault("properties", {})

        return data

    except Exception as e:
        print(f"Error normalizing layout: {e}")
        # Return a safe fallback layout
        return {
            "system_name": "Error Loading Layout",
            "style": "dashboard",
            "components": []
        }
