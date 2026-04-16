"""Sanity checks for the shopping list produced by the cooking cartridge.

Non-fatal: returns True with a message even when the list is odd, unless
it's outright malformed (missing aisles, non-list types).
"""

from __future__ import annotations

_REQUIRED_AISLES = ("produce", "dairy", "pantry", "protein", "other")


def validate(blackboard: dict) -> tuple[bool, str]:
    entry = blackboard.get("shopping_list")
    if not entry:
        return True, "skipped (no shopping_list on blackboard — flow may omit it)"
    sl = entry["value"]
    if not isinstance(sl, dict):
        return False, "shopping_list is not an object"
    aisles = sl.get("aisles")
    if not isinstance(aisles, dict):
        return False, "shopping_list.aisles must be an object"
    missing = [a for a in _REQUIRED_AISLES if a not in aisles]
    if missing:
        return False, f"missing aisles: {missing}"
    total_items = sum(len(aisles[a]) for a in _REQUIRED_AISLES
                      if isinstance(aisles.get(a), list))
    if total_items < 5:
        return True, (f"warning: only {total_items} items across all aisles — "
                      f"suspiciously thin list")
    return True, f"shopping_list ok ({total_items} items across {len(_REQUIRED_AISLES)} aisles)"
