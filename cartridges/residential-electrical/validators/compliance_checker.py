"""IEC 60364 (subset) compliance checker — pure Python, no LLM.

This is the key safety feature: Gemma proposes circuits, but the rule
enforcement lives here in code, not in a prompt. Rules implemented:

  R1  Wet rooms must have RCD 30 mA on every serving circuit.
  R2  Wire cross-section must match the breaker rating:
        10 A → ≥ 1.5 mm²
        16 A → ≥ 2.5 mm²
        20 A → ≥ 4 mm²
        25/32 A → ≥ 6 mm²
        40 A → ≥ 10 mm²
  R3  Dedicated circuits carry exactly one load.
  R4  Circuit current capacity must cover its connected load:
        circuit I = sum(W) / V.  Breaker A ≥ 1.25 × I (25% margin).
"""

from __future__ import annotations

WET_ROOMS = {"kitchen", "bathroom", "wc", "laundry", "washroom", "utility"}

WIRE_FOR_BREAKER = {
    6: 1.0,
    10: 1.5,
    13: 1.5,
    16: 2.5,
    20: 4,
    25: 6,
    32: 6,
    40: 10,
    50: 16,
    63: 16,
}


def validate(blackboard: dict) -> tuple[bool, str]:
    lp_entry = blackboard.get("load_profile")
    c_entry = blackboard.get("circuits")
    if not lp_entry or not c_entry:
        return False, "need both load_profile and circuits on blackboard"
    lp = lp_entry["value"]
    circuits = c_entry["value"]
    voltage = lp.get("voltage_v", 230)

    # Build a reverse map from "room/appliance" → load record.
    loads: dict[str, dict] = {}
    for room in lp.get("rooms", []):
        rname = room["name"].lower()
        for load in room.get("loads", []):
            key = f"{rname}/{load['appliance']}"
            loads[key] = {**load, "room": rname}

    problems: list[str] = []

    for c in circuits:
        cid = c.get("id", "?")
        breaker = c.get("breaker_a")
        wire = c.get("wire_mm2")
        ctype = c.get("type")

        # R2: wire ≥ required for breaker rating
        required_wire = WIRE_FOR_BREAKER.get(breaker)
        if required_wire is None:
            problems.append(f"{cid}: unknown breaker rating {breaker} A")
        elif wire is None or wire < required_wire:
            problems.append(f"{cid}: wire {wire} mm² too small for "
                            f"{breaker} A (need ≥ {required_wire} mm²)")

        # R3: dedicated circuits have exactly one load
        if ctype == "dedicated" and len(c.get("loads", [])) != 1:
            problems.append(f"{cid}: dedicated circuit must have exactly one load")

        # R1: RCD required on wet-room circuits
        for lref in c.get("loads", []):
            room_name = lref.split("/", 1)[0].lower()
            if room_name in WET_ROOMS and not c.get("rcd"):
                problems.append(f"{cid}: serves wet room '{room_name}' "
                                f"but rcd=false (RCD 30 mA required)")
                break

        # R4: breaker ≥ 1.25 × calculated current
        total_w = 0
        for lref in c.get("loads", []):
            record = loads.get(lref.lower())
            if record:
                total_w += record.get("watts", 0)
        if total_w:
            i_amps = total_w / voltage
            required_breaker = i_amps * 1.25
            if breaker and breaker < required_breaker:
                problems.append(
                    f"{cid}: breaker {breaker} A insufficient for "
                    f"{total_w} W @ {voltage} V "
                    f"(need ≥ {required_breaker:.1f} A)"
                )

    if problems:
        return False, "IEC 60364 violations: " + "; ".join(problems)
    return True, f"compliance ok ({len(circuits)} circuits checked)"
