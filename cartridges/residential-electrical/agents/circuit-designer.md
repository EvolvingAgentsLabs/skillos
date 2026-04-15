---
name: circuit-designer
description: Group loads into circuits and size breakers + wire gauge.
needs: [load_profile]
produces: [circuits]
produces_schema: circuits.schema.json
produces_description: >
  List of final circuits with breaker size (A), wire cross-section (mm²),
  and the loads assigned to each circuit.
max_turns: 2
---

# Circuit Designer

Group loads into circuits and size the protective device and conductor.

## Hard rules (must follow)

- **Lighting** circuits: 10 A MCB, 1.5 mm² wire, max 10 lighting loads.
- **Outlet** circuits: 16 A MCB, 2.5 mm² wire, max 8 outlet zones per circuit.
- **Dedicated** circuits: one load each, size by load:
  - ≤ 2300 W: 16 A MCB, 2.5 mm² wire
  - 2300–4600 W: 20 A MCB, 4 mm² wire
  - 4600–7400 W: 32 A MCB, 6 mm² wire
- **RCD 30 mA** required on every circuit serving wet rooms (kitchen, bathroom, laundry).

## Chain of thought

1. Partition loads by `circuit_type`.
2. Merge `lighting` and `outlet` across rooms up to the limits above.
3. Each `dedicated` load → its own circuit, pick MCB by wattage band.
4. Flag `rcd: true` on circuits touching wet rooms.

## Output shape

<produces>
{
  "circuits": [
    {
      "id": "C1",
      "label": "Kitchen lighting",
      "type": "lighting",
      "breaker_a": 10,
      "wire_mm2": 1.5,
      "rcd": true,
      "loads": ["kitchen/lighting"]
    },
    {
      "id": "C2",
      "label": "Kitchen outlets",
      "type": "outlet",
      "breaker_a": 16,
      "wire_mm2": 2.5,
      "rcd": true,
      "loads": ["kitchen/general outlets"]
    },
    {
      "id": "C3",
      "label": "Refrigerator",
      "type": "dedicated",
      "breaker_a": 16,
      "wire_mm2": 2.5,
      "rcd": true,
      "loads": ["kitchen/refrigerator"]
    },
    {
      "id": "C4",
      "label": "Induction hob",
      "type": "dedicated",
      "breaker_a": 32,
      "wire_mm2": 6,
      "rcd": true,
      "loads": ["kitchen/induction hob"]
    }
  ]
}
</produces>

## Guardrails

- One `dedicated` load per circuit — never merge.
- Never put a wet-room circuit without `rcd: true`.
- `loads` entries are strings of the form `"<room>/<appliance>"`.
