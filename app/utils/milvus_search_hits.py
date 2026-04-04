"""Normalize MilvusClient / Zilliz vector search hits into flat book records.

pymilvus may return hits as:
- Nested: {id, distance, entity: {work_key, title, ...}}
- Flat: {id, distance, work_key, title, ...}
- Broken hybrid: entity: {} with scalars only at top level — taking entity alone would
  drop all output_fields and skip explanation logic. This module merges safely.
"""

from __future__ import annotations

import re
from typing import Any

_HIT_META_KEYS = frozenset({"entity", "id", "distance"})


def normalize_open_library_work_id(work_key: object) -> str | None:
    """Return OL id e.g. OL45804W for comparison, or None if not parseable."""
    if work_key is None:
        return None
    s = str(work_key).strip()
    if not s:
        return None
    m = re.search(r"OL\d+W", s, re.IGNORECASE)
    return m.group(0).upper() if m else None


def same_open_library_work(a: object, b: object) -> bool:
    """True if both refer to the same Open Library work (OL…W), tolerant of /works/ prefix."""
    ta = normalize_open_library_work_id(a)
    tb = normalize_open_library_work_id(b)
    if ta is not None and tb is not None:
        return ta == tb
    if a is None or b is None:
        return False
    return str(a).strip() == str(b).strip()


def sanitize_numpy_scalars(record: dict) -> dict:
    """Convert numpy scalar types to native Python for JSON serialization."""
    out: dict[str, Any] = {}
    for k, v in record.items():
        t = type(v).__module__
        if t == "numpy":
            tn = type(v).__name__
            if "float" in tn:
                v = float(v)
            elif "int" in tn or "uint" in tn:
                v = int(v)
            elif "bool" in tn:
                v = bool(v)
        out[k] = v
    return out


def search_hit_entity_dict(hit: object) -> dict | None:
    """
    Return one book field dict from a search hit, or None if nothing usable.

    Inner ``entity`` wins on key conflicts; if ``entity`` is empty, top-level
    scalar fields (output_fields) are used.
    """
    if not isinstance(hit, dict):
        return None
    raw_inner = hit.get("entity")
    inner = raw_inner if isinstance(raw_inner, dict) else {}
    flat = {k: v for k, v in hit.items() if k not in _HIT_META_KEYS}
    merged = {**flat, **inner} if inner else flat
    if not merged:
        return None
    return sanitize_numpy_scalars(merged)


def search_hit_distance(hit: object) -> float | None:
    """Milvus search hit: lower COSINE distance = closer match."""
    if isinstance(hit, dict):
        d = hit.get("distance")
    else:
        d = getattr(hit, "distance", None)
    if isinstance(d, (int, float)):
        return float(d)
    return None
