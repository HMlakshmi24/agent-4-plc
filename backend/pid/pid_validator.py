from __future__ import annotations
from typing import Dict, Any, List


def validate_pid_layout(layout: Dict[str, Any]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    components = layout.get("components", [])
    if not components:
        errors.append("No components in layout.")
        return {"errors": errors, "warnings": warnings}

    id_set = set()
    tag_set = set()
    for i, c in enumerate(components):
        cid = c.get("id")
        tag = c.get("tag")
        if not cid:
            errors.append(f"Component[{i}] missing id.")
        else:
            if cid in id_set:
                errors.append(f"Duplicate component id: {cid}")
            id_set.add(cid)
        if not tag:
            warnings.append(f"Component[{i}] missing tag.")
        else:
            if tag in tag_set:
                warnings.append(f"Duplicate component tag: {tag}")
            tag_set.add(tag)

    def _resolve(ref: str) -> bool:
        return ref in id_set or ref in tag_set

    for i, conn in enumerate(layout.get("connections", [])):
        src = conn.get("from")
        dst = conn.get("to")
        if not src or not dst:
            errors.append(f"Connection[{i}] missing from/to.")
            continue
        if not _resolve(str(src)):
            errors.append(f"Connection[{i}] invalid from: {src}")
        if not _resolve(str(dst)):
            errors.append(f"Connection[{i}] invalid to: {dst}")

    for i, sig in enumerate(layout.get("signals", [])):
        src = sig.get("from")
        dst = sig.get("to")
        if not src or not dst:
            errors.append(f"Signal[{i}] missing from/to.")
            continue
        if not _resolve(str(src)):
            warnings.append(f"Signal[{i}] invalid from: {src}")
        if not _resolve(str(dst)):
            warnings.append(f"Signal[{i}] invalid to: {dst}")

    return {"errors": errors, "warnings": warnings}
