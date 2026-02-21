
import json

def safe_json_load(text: str):

    try:
        return json.loads(text)
    except Exception:
        # Remove possible markdown or stray text
        text = text.strip()

        if text.startswith("```"):
            # Try to split by code fence, careful if language specifier exists or not
            parts = text.split("```")
            if len(parts) >= 2:
                # part[1] is the content inside the first fence (typically)
                content = parts[1]
                # If content starts with "json", strip it
                if content.lower().startswith("json"):
                    content = content[4:]
                return json.loads(content)

        return json.loads(text)
