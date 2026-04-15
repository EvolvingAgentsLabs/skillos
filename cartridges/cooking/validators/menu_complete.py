"""Deterministic validator for the cooking cartridge.

Checks that the weekly menu is well-formed and that (when present) the
recipes list covers every dinner. Pure Python — no LLM call.

Signature expected by CartridgeRunner:

    def validate(blackboard: dict) -> tuple[bool, str]
"""

from __future__ import annotations


_REQUIRED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]


def validate(blackboard: dict) -> tuple[bool, str]:
    menu_entry = blackboard.get("weekly_menu")
    if not menu_entry:
        return False, "weekly_menu missing from blackboard"
    menu = menu_entry["value"]
    if not isinstance(menu, dict):
        return False, "weekly_menu is not an object"

    days = menu.get("days", [])
    if len(days) != 7:
        return False, f"weekly_menu must have 7 days, got {len(days)}"

    seen_days = {d.get("day", "") for d in days}
    missing = [d for d in _REQUIRED_DAYS if d not in seen_days]
    if missing:
        return False, f"missing days: {missing}"

    for d in days:
        meals = d.get("meals", [])
        slots = {m.get("slot") for m in meals}
        required_slots = {"breakfast", "lunch", "dinner"}
        if not required_slots.issubset(slots):
            return False, (f"day '{d.get('day')}' missing slots: "
                           f"{required_slots - slots}")

    # Cross-check with recipes if present
    recipes_entry = blackboard.get("recipes")
    if recipes_entry:
        recipes = recipes_entry["value"]
        if not isinstance(recipes, list) or len(recipes) != 7:
            return False, f"recipes must be a list of 7, got {len(recipes)}"
        recipe_days = {r.get("day") for r in recipes}
        menu_days = {d.get("day") for d in days}
        if not recipe_days.issubset(menu_days):
            return False, ("recipes reference days not in weekly_menu: "
                           f"{recipe_days - menu_days}")

    return True, f"weekly_menu has all 7 days × 3 slots"
