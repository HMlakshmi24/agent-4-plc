
import os
import json
from datetime import datetime

LAYOUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "layouts")

def save_hmi_layout(layout_data):
    
    if not os.path.exists(LAYOUT_DIR):
        os.makedirs(LAYOUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use system name in filename if safe, else usage timestamp
    safe_name = "".join([c for c in layout_data.get("system_name", "layout") if c.isalnum() or c in (' ', '_')]).rstrip()
    safe_name = safe_name.replace(" ", "_").lower()
    
    filename = f"{safe_name}_{timestamp}.json"
    path = os.path.join(LAYOUT_DIR, filename)

    with open(path, "w") as f:
        json.dump(layout_data, f, indent=2)

    return filename
