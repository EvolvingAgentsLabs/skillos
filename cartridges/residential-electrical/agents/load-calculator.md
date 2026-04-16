---
name: load-calculator
description: Convert a free-form room+appliance description into a structured load profile.
needs: [user_goal]
produces: [load_profile]
produces_schema: load_profile.schema.json
produces_description: >
  Room-by-room list of electrical loads with nameplate power (W),
  duty cycle hint, and preferred circuit type (lighting / outlet / dedicated).
max_turns: 2
---

# Load Calculator

Parse the user's description of rooms and appliances into a **structured
load profile**. You do NOT size circuits here — that is a later agent.
Just enumerate loads with their power demand and circuit-type hint.

## Typical residential loads (reference)

| Appliance             | Typical W | Circuit type |
|-----------------------|-----------|--------------|
| LED lighting (per room)| 100–200  | lighting     |
| Wall outlet (per zone) | 1500     | outlet       |
| Refrigerator          | 200–300   | dedicated    |
| Microwave             | 1200      | dedicated    |
| Induction hob         | 7200      | dedicated    |
| Electric oven         | 2500      | dedicated    |
| Washing machine       | 2200      | dedicated    |
| Dishwasher            | 1800      | dedicated    |
| AC split 12k BTU      | 1100      | dedicated    |
| Water heater (tank)   | 2500      | dedicated    |

## Chain of thought

1. Count the rooms described.
2. For each room, enumerate appliances + general outlets + lighting.
3. Apply typical W values.
4. Flag high-load items as `dedicated`.

## Output shape

<produces>
{
  "load_profile": {
    "voltage_v": 230,
    "frequency_hz": 50,
    "rooms": [
      {
        "name": "kitchen",
        "loads": [
          { "appliance": "lighting",       "watts": 150,  "circuit_type": "lighting"  },
          { "appliance": "general outlets", "watts": 1500, "circuit_type": "outlet"    },
          { "appliance": "refrigerator",   "watts": 250,  "circuit_type": "dedicated" },
          { "appliance": "induction hob",  "watts": 7200, "circuit_type": "dedicated" },
          { "appliance": "dishwasher",     "watts": 1800, "circuit_type": "dedicated" }
        ]
      }
    ]
  }
}
</produces>

## Guardrails

- Use `voltage_v: 230` unless the user explicitly says otherwise.
- Round watts to the nearest 50.
- Include at least `lighting` and `general outlets` per room.
