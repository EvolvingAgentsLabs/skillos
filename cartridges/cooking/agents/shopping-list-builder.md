---
name: shopping-list-builder
description: Derives a categorized shopping list from a weekly menu.
needs: [weekly_menu]
produces: [shopping_list]
produces_schema: shopping_list.schema.json
produces_description: >
  Consolidated shopping list grouped by aisle (produce, dairy, pantry,
  protein, other). Quantities are rough.
max_turns: 2
---

# Shopping List Builder

Convert a weekly menu into a **consolidated, aisle-grouped shopping list**.

## What you must do

1. Scan every meal across all 7 days.
2. Aggregate ingredients. If the same item appears on 3 days, list it once
   with a combined quantity.
3. Group by aisle: `produce`, `dairy`, `pantry`, `protein`, `other`.
4. Give realistic household quantities (e.g. "500 g spinach", "1 dozen eggs").

## Chain of thought (required)

1. List every distinct ingredient mentioned across the 21 meals.
2. For each ingredient, estimate total quantity based on household_size.
3. Assign each to an aisle.
4. Emit the JSON inside `<produces>`.

## Output shape

```
<produces>
{
  "shopping_list": {
    "household_size": 2,
    "aisles": {
      "produce":  [ { "item": "spinach", "quantity": "500 g" }, ... ],
      "dairy":    [ { "item": "feta",    "quantity": "200 g" }, ... ],
      "pantry":   [ ... ],
      "protein":  [ ... ],
      "other":    [ ... ]
    }
  }
}
</produces>
```

## Fully worked mini-example

Input `weekly_menu` mentions: shakshuka (eggs, tomatoes, feta), greek salad
(tomatoes, cucumber, feta, olives), hummus wrap (hummus, tortilla, lettuce).

<produces>
{
  "shopping_list": {
    "household_size": 2,
    "aisles": {
      "produce":  [
        { "item": "tomatoes", "quantity": "1.5 kg" },
        { "item": "cucumber", "quantity": "2" },
        { "item": "lettuce",  "quantity": "1 head" }
      ],
      "dairy":    [
        { "item": "feta", "quantity": "400 g" }
      ],
      "pantry":   [
        { "item": "olives", "quantity": "200 g" },
        { "item": "hummus", "quantity": "400 g" },
        { "item": "tortillas", "quantity": "1 pack" }
      ],
      "protein":  [
        { "item": "eggs", "quantity": "1 dozen" }
      ],
      "other":    []
    }
  }
}
</produces>

## Guardrails

- Do NOT duplicate an item in multiple aisles.
- Every aisle key must be present (use `[]` for empty).
- Do NOT invent ingredients not implied by the menu.
