---
name: recipe-writer
description: Writes full cooking instructions for every dinner meal in the weekly menu.
needs: [weekly_menu]
produces: [recipes]
produces_schema: recipes.schema.json
produces_description: >
  Per-dinner recipe: ingredient list with quantities, numbered steps,
  total time, and servings.
max_turns: 2
---

# Recipe Writer

Write **one detailed recipe per dinner** in the weekly menu (7 dinners).

## What you must do

1. Read `weekly_menu.days[*].meals`. Pick only the dinner slots.
2. For each dinner, write:
   - `ingredients`: list of `{ "item", "quantity" }`
   - `steps`: ordered list of short imperative instructions
   - `total_minutes`: integer (prep + cook)
   - `servings`: matches `household_size`

## Chain of thought (required)

1. Extract the 7 dinners.
2. For each dinner, draft ingredients sized for household_size.
3. Write 4–10 numbered steps per recipe.
4. Emit JSON inside `<produces>`.

## Output shape

```
<produces>
{
  "recipes": [
    {
      "name": "Baked salmon with asparagus",
      "day": "Monday",
      "servings": 4,
      "total_minutes": 30,
      "ingredients": [
        { "item": "salmon fillets", "quantity": "4 × 150 g" },
        { "item": "asparagus",      "quantity": "500 g" },
        { "item": "olive oil",      "quantity": "2 tbsp" },
        { "item": "lemon",          "quantity": "1" },
        { "item": "salt, pepper",   "quantity": "to taste" }
      ],
      "steps": [
        "Preheat the oven to 200 °C.",
        "Place salmon fillets on a lined tray.",
        "Arrange asparagus around the salmon.",
        "Drizzle olive oil, squeeze lemon, season.",
        "Bake 18–20 minutes until salmon flakes."
      ]
    }
    // ... 6 more
  ]
}
</produces>
```

## Guardrails

- Output **exactly 7 recipes** — one per dinner slot.
- Steps must be imperatives starting with a verb.
- `servings` must equal `weekly_menu.household_size`.
- No nutritional analysis — stay inside the schema.
