import json
from pathlib import Path
from typing import Dict, Any


_LIB_DIR = Path(__file__).resolve().parent / "equipment_library"


def load_equipment_library() -> Dict[str, Dict[str, Any]]:
    library: Dict[str, Dict[str, Any]] = {}
    if not _LIB_DIR.exists():
        return library
    for path in _LIB_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            etype = str(data.get("type") or path.stem).strip()
            if etype:
                library[etype] = data
        except Exception:
            continue
    return library


def get_equipment_definition(etype: str, library: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return library.get(etype, {})


def equipment_dimensions(etype: str, library: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    definition = get_equipment_definition(etype, library)
    return {
        "width": int(definition.get("width", 70)),
        "height": int(definition.get("height", 60)),
    }


def equipment_tag_prefix(etype: str, library: Dict[str, Dict[str, Any]]) -> str:
    definition = get_equipment_definition(etype, library)
    return str(definition.get("tag_prefix") or etype[:2].upper() or "EQ")
