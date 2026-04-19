"""Validator: checks that the JS skill result has no error."""


def validate(blackboard: dict) -> tuple[bool, str]:
    """Check that skill_result exists and has no error.

    Args:
        blackboard: snapshot dict from Blackboard.snapshot()

    Returns:
        (ok, message) tuple.
    """
    sr = blackboard.get("skill_result", {})
    value = sr.get("value", sr) if isinstance(sr, dict) else sr

    if not value:
        return False, "skill_result is empty"

    if isinstance(value, dict):
        error = value.get("error")
        if error:
            return False, f"skill returned error: {error}"

    return True, "ok: skill result valid"
