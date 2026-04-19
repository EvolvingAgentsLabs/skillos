"""Validator: checks that the learn pipeline produced valid output."""


def validate(blackboard: dict) -> tuple[bool, str]:
    # Check for any stored result
    for key in ("store_result", "insights", "quiz", "knowledge", "stats"):
        entry = blackboard.get(key, {})
        value = entry.get("value", entry) if isinstance(entry, dict) else entry
        if value:
            return True, f"ok: {key} present"

    return False, "no output produced by pipeline"
