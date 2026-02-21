import json

def validate_layout(raw_json: str):
    """
    Validates the HMI JSON from AI.
    Accepts new schema: { title, theme, components[{id,type,label,x,y,state,value}] }
    Also accepts legacy schema: { system_name, style, components[...] }
    """
    # ── Parse ────────────────────────────────────────────────────
    try:
        data = json.loads(raw_json)
    except Exception:
        try:
            if "```" in raw_json:
                cleaned = raw_json.split("```json")[-1].split("```")[0].strip()
                if not cleaned:
                    cleaned = raw_json.split("```")[1].split("```")[0].strip()
                data = json.loads(cleaned)
            else:
                raise ValueError
        except Exception:
            raise ValueError("AI returned invalid JSON — cannot parse.")

    # ── Normalise title/system_name ──────────────────────────────
    if "title" not in data and "system_name" in data:
        data["title"] = data["system_name"]
    if "system_name" not in data and "title" in data:
        data["system_name"] = data["title"]
    if "title" not in data and "system_name" not in data:
        data["title"] = "HMI Dashboard"
        data["system_name"] = "HMI Dashboard"

    # ── Require components ───────────────────────────────────────
    components = data.get("components")
    if not isinstance(components, list) or len(components) == 0:
        raise ValueError("No components returned by AI.")

    # ── Normalise each component ─────────────────────────────────
    used_positions = set()
    for i, comp in enumerate(components):
        # Ensure id
        if "id" not in comp:
            comp["id"] = f"{comp.get('type', 'c')}_{i}"

        # Ensure type
        if "type" not in comp:
            raise ValueError(f"Component {i} missing 'type'")

        # Ensure label (new schema uses 'label', legacy uses 'name')
        if "label" not in comp and "name" in comp:
            comp["label"] = comp["name"]
        if "name" not in comp and "label" in comp:
            comp["name"] = comp["label"]
        if "label" not in comp:
            comp["label"] = comp["type"]
        if "name" not in comp:
            comp["name"] = comp["label"]

        # Ensure x, y — auto-assign if missing
        if "x" not in comp:
            comp["x"] = 80 + (i % 5) * 160
        if "y" not in comp:
            comp["y"] = 100 + (i // 5) * 160

        # Avoid exact overlaps — shift if needed
        pos = (comp["x"], comp["y"])
        offset = 0
        while pos in used_positions:
            offset += 20
            pos = (comp["x"] + offset, comp["y"])
        comp["x"] = pos[0]
        used_positions.add(pos)

        # Default state and value
        if "state" not in comp:
            comp["state"] = "stopped"
        if "value" not in comp:
            comp["value"] = 0

    return data
