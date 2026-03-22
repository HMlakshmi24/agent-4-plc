from __future__ import annotations
from typing import Dict, List, Any, Tuple
import math

from .equipment_library import load_equipment_library, equipment_dimensions, equipment_tag_prefix


HMI_ONLY_TYPES = {
    "button", "slider", "switch", "indicator", "trend", "trend_chart",
    "alarm_panel", "display", "panel", "screen", "graph"
}

SENSOR_TYPES = {
    "flow_sensor", "pressure_sensor", "temperature_sensor", "level_sensor", "analyzer"
}

CONTROL_TARGET_TYPES = {
    "control_valve", "valve", "check_valve", "pump", "motor", "compressor", "fan", "heater"
}

# Map arbitrary/legacy component types to library types
TYPE_ALIASES = {
    "sensor_level": "level_sensor",
    "sensor_temp": "temperature_sensor",
    "sensor_pressure": "pressure_sensor",
    "sensor_flow": "flow_sensor",
    "sensor": "flow_sensor",
    "control valve": "control_valve",
    "isolation valve": "valve",
    "check valve": "check_valve",
    "agitator": "mixer",
    "mixer": "mixer",
    "heat exchanger": "heat_exchanger",
    "heat-exchanger": "heat_exchanger",
    "separator": "separator",
    "filter": "filter",
    "compressor": "compressor",
    "blower": "fan",
    "fan": "fan",
    "reactor": "reactor",
    "silo": "silo",
    "conveyor": "conveyor",
    "motor": "motor",
    "pump": "pump",
    "tank": "tank",
    "valve": "valve",
    "analyzer": "analyzer",
}

# Render types supported by the P&ID template JS
RENDER_TYPE_MAP = {
    "tank": "tank",
    "silo": "tank",
    "reactor": "tank",
    "separator": "tank",
    "filter": "tank",
    "heat_exchanger": "tank",
    "pump": "pump",
    "compressor": "pump",
    "fan": "motor",
    "mixer": "motor",
    "motor": "motor",
    "conveyor": "motor",
    "control_valve": "valve",
    "valve": "valve",
    "check_valve": "valve",
    "flow_sensor": "sensor_pressure",
    "pressure_sensor": "sensor_pressure",
    "temperature_sensor": "sensor_temp",
    "level_sensor": "sensor_level",
    "analyzer": "gauge",
}

FLOW_ORDER = {
    "tank": 10,
    "silo": 10,
    "pump": 20,
    "compressor": 20,
    "fan": 20,
    "control_valve": 30,
    "valve": 30,
    "check_valve": 30,
    "heat_exchanger": 40,
    "reactor": 50,
    "mixer": 55,
    "separator": 60,
    "filter": 65,
    "conveyor": 70,
    "motor": 80,
}


def _normalize_type(raw_type: str, label: str) -> str:
    t = (raw_type or "").strip().lower().replace("-", " ")
    if not t and label:
        t = label.strip().lower()
    if t in TYPE_ALIASES:
        return TYPE_ALIASES[t]
    for key, val in TYPE_ALIASES.items():
        if key in t:
            return val
    return t or "tank"


def _should_filter_component(comp: Dict[str, Any]) -> bool:
    ctype = (comp.get("type") or "").strip().lower()
    if ctype in HMI_ONLY_TYPES:
        return True
    if any(k in ctype for k in HMI_ONLY_TYPES):
        return True
    return False


def _assign_ids_and_tags(components: List[Dict[str, Any]], library: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    counters: Dict[str, int] = {}
    out: List[Dict[str, Any]] = []
    for i, comp in enumerate(components):
        c = dict(comp)
        lib_type = c.get("library_type") or c.get("type") or "tank"
        lib_type = str(lib_type)
        prefix = equipment_tag_prefix(lib_type, library)
        counters[prefix] = counters.get(prefix, 100) + 1
        c["id"] = c.get("id") or c.get("_id") or f"{prefix}{counters[prefix]}"
        c["tag"] = c.get("tag") or f"{prefix}-{counters[prefix]}"
        c["name"] = c.get("name") or c.get("label") or c.get("id") or lib_type.title()
        out.append(c)
    return out


def _flow_components(components: List[Dict[str, Any]], connections: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    if connections:
        order = _topo_order_from_connections(components, connections)
        if order:
            return order
    def rank(c: Dict[str, Any]) -> Tuple[int, str]:
        if "_index" in c:
            return (int(c.get("_index", 0)), c.get("id", ""))
        t = c.get("library_type") or c.get("type") or "tank"
        return (FLOW_ORDER.get(t, 999), c.get("id", ""))
    return sorted(components, key=rank)


def _layout_flow(components: List[Dict[str, Any]], library: Dict[str, Dict[str, Any]], connections: List[Dict[str, Any]] | None) -> None:
    if not components:
        return
    # If components already spread out, keep positions
    xs = [c.get("x", 0) for c in components if isinstance(c.get("x"), (int, float))]
    ys = [c.get("y", 0) for c in components if isinstance(c.get("y"), (int, float))]
    if xs and ys and (max(xs) - min(xs) >= 260 or max(ys) - min(ys) >= 200):
        return

    flow = _flow_components([c for c in components if c.get("library_type") not in SENSOR_TYPES], connections)
    sensors = [c for c in components if c.get("library_type") in SENSOR_TYPES]

    start_x = 120
    spacing = 180
    flow_y = 220
    sensor_y = 80

    for idx, comp in enumerate(flow):
        comp["x"] = start_x + idx * spacing
        comp["y"] = flow_y

    # Place sensors above nearest flow component
    for sensor in sensors:
        target = _nearest_component(sensor, flow)
        if target:
            sensor["x"] = target["x"]
            sensor["y"] = sensor_y
        else:
            sensor["x"] = start_x
            sensor["y"] = sensor_y


def _nearest_component(comp: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not candidates:
        return None
    cx = comp.get("x", 0)
    cy = comp.get("y", 0)
    def dist(c):
        return math.hypot((c.get("x", 0) - cx), (c.get("y", 0) - cy))
    return min(candidates, key=dist)


def _build_connections(components: List[Dict[str, Any]], existing: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    if existing:
        return existing
    flow = _flow_components([c for c in components if c.get("library_type") not in SENSOR_TYPES], None)
    connections = []
    for i in range(len(flow) - 1):
        connections.append({"from": flow[i]["id"], "to": flow[i + 1]["id"]})
    return connections


def _build_signals(components: List[Dict[str, Any]], connections: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    sensors = [c for c in components if c.get("library_type") in SENSOR_TYPES]
    targets = [c for c in components if c.get("library_type") in CONTROL_TARGET_TYPES]
    signals: List[Dict[str, Any]] = []
    lookup = _component_lookup(components)
    for sensor in sensors:
        target = _find_control_target_via_graph(sensor, targets, connections, lookup) or _nearest_component(sensor, targets)
        if target:
            signals.append({"from": sensor["id"], "to": target["id"], "type": "control"})
    return signals


def _component_lookup(components: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for c in components:
        cid = c.get("id")
        if cid:
            lookup[cid] = c
        tag = c.get("tag")
        if tag:
            lookup[str(tag)] = c
        name = c.get("name")
        if name:
            lookup[str(name)] = c
    return lookup


def _topo_order_from_connections(components: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lookup = _component_lookup(components)
    nodes = [c for c in components if c.get("library_type") not in SENSOR_TYPES]
    node_ids = [c.get("id") for c in nodes if c.get("id")]
    if not node_ids:
        return []

    indeg: Dict[str, int] = {nid: 0 for nid in node_ids}
    adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}

    for c in connections:
        src = c.get("from")
        dst = c.get("to")
        if not src or not dst:
            continue
        src_comp = lookup.get(src)
        dst_comp = lookup.get(dst)
        if not src_comp or not dst_comp:
            continue
        if src_comp.get("library_type") in SENSOR_TYPES or dst_comp.get("library_type") in SENSOR_TYPES:
            continue
        if src_comp.get("id") in adj:
            adj[src_comp["id"]].append(dst_comp["id"])
            indeg[dst_comp["id"]] = indeg.get(dst_comp["id"], 0) + 1

    queue = [nid for nid in node_ids if indeg.get(nid, 0) == 0]
    queue.sort()
    ordered: List[str] = []
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for nxt in adj.get(current, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
                queue.sort()

    # Append any remaining nodes (cycles or disconnected) in index order
    remaining = [nid for nid in node_ids if nid not in ordered]
    if remaining:
        remaining.sort(key=lambda nid: lookup.get(nid, {}).get("_index", 0))
        ordered.extend(remaining)

    id_to_comp = {c.get("id"): c for c in nodes if c.get("id")}
    return [id_to_comp[nid] for nid in ordered if nid in id_to_comp]


def _find_control_target_via_graph(sensor: Dict[str, Any], targets: List[Dict[str, Any]], connections: List[Dict[str, Any]] | None, lookup: Dict[str, Dict[str, Any]]):
    if not connections:
        return None
    sensor_id = sensor.get("id")
    if not sensor_id:
        return None

    forward: Dict[str, List[str]] = {}
    backward: Dict[str, List[str]] = {}
    for c in connections:
        src = c.get("from")
        dst = c.get("to")
        if not src or not dst:
            continue
        forward.setdefault(src, []).append(dst)
        backward.setdefault(dst, []).append(src)

    target_ids = {t.get("id") for t in targets if t.get("id")}

    def bfs(start_id: str, graph: Dict[str, List[str]]):
        visited = set()
        queue = [start_id]
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            if cur in target_ids and cur != start_id:
                return lookup.get(cur)
            for nxt in graph.get(cur, []):
                if nxt not in visited:
                    queue.append(nxt)
        return None

    return bfs(sensor_id, forward) or bfs(sensor_id, backward)


def _port_point(comp: Dict[str, Any], side: str, library: Dict[str, Dict[str, Any]]) -> Tuple[float, float]:
    dims = equipment_dimensions(comp.get("library_type") or comp.get("type") or "tank", library)
    x = comp.get("x", 0)
    y = comp.get("y", 0)
    w = dims["width"]
    h = dims["height"]
    if side == "left":
        return (x - w / 2, y)
    if side == "right":
        return (x + w / 2, y)
    if side == "top":
        return (x, y - h / 2)
    if side == "bottom":
        return (x, y + h / 2)
    return (x, y)


def _route_connection(start: Tuple[float, float], end: Tuple[float, float], pipe_id_start: int, is_signal: bool) -> Tuple[List[Dict[str, Any]], int]:
    x1, y1 = start
    x2, y2 = end
    pipes: List[Dict[str, Any]] = []
    pipe_id = pipe_id_start
    if abs(y1 - y2) < 10 or abs(x1 - x2) < 10:
        pipes.append({"id": f"pipe_{pipe_id}", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "active": bool(is_signal), "kind": "signal" if is_signal else "process"})
        return pipes, pipe_id + 1

    mid_x = (x1 + x2) / 2
    pipes.append({"id": f"pipe_{pipe_id}", "x1": x1, "y1": y1, "x2": mid_x, "y2": y1, "active": bool(is_signal), "kind": "signal" if is_signal else "process"})
    pipe_id += 1
    pipes.append({"id": f"pipe_{pipe_id}", "x1": mid_x, "y1": y1, "x2": mid_x, "y2": y2, "active": bool(is_signal), "kind": "signal" if is_signal else "process"})
    pipe_id += 1
    pipes.append({"id": f"pipe_{pipe_id}", "x1": mid_x, "y1": y2, "x2": x2, "y2": y2, "active": bool(is_signal), "kind": "signal" if is_signal else "process"})
    return pipes, pipe_id + 1


def _build_pipes(components: List[Dict[str, Any]], connections: List[Dict[str, Any]], signals: List[Dict[str, Any]], library: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    lookup = _component_lookup(components)
    pipes: List[Dict[str, Any]] = []
    pipe_id = 1

    for conn in connections:
        src = lookup.get(conn.get("from"))
        dst = lookup.get(conn.get("to"))
        if not src or not dst:
            continue
        start = _port_point(src, "right", library)
        end = _port_point(dst, "left", library)
        segs, pipe_id = _route_connection(start, end, pipe_id, False)
        pipes.extend(segs)

    for sig in signals:
        src = lookup.get(sig.get("from"))
        dst = lookup.get(sig.get("to"))
        if not src or not dst:
            continue
        start = _port_point(src, "bottom", library)
        end = _port_point(dst, "top", library)
        segs, pipe_id = _route_connection(start, end, pipe_id, True)
        pipes.extend(segs)

    return pipes


def build_pid_layout(layout: Dict[str, Any]) -> Dict[str, Any]:
    library = load_equipment_library()

    components = []
    for idx, comp in enumerate(layout.get("components", [])):
        if _should_filter_component(comp):
            continue
        raw_type = comp.get("type", "")
        label = comp.get("label", "") or comp.get("name", "")
        lib_type = _normalize_type(raw_type, label)
        render_type = RENDER_TYPE_MAP.get(lib_type, "tank")
        normalized = dict(comp)
        normalized["library_type"] = lib_type
        normalized["type"] = render_type
        normalized["_index"] = idx
        components.append(normalized)

    components = _assign_ids_and_tags(components, library)
    connections = _build_connections(components, layout.get("connections"))
    _layout_flow(components, library, connections)

    signals = layout.get("signals") or _build_signals(components, connections)
    pipes = _build_pipes(components, connections, signals, library)

    enhanced = dict(layout)
    enhanced["components"] = components
    enhanced["connections"] = connections
    enhanced["signals"] = signals
    enhanced["pipes"] = pipes
    enhanced["_pid_enhanced"] = True
    try:
        from .pid_validator import validate_pid_layout
        enhanced["_pid_validation"] = validate_pid_layout(enhanced)
    except Exception:
        pass
    return enhanced
