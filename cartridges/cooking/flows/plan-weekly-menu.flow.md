# Flow: plan-weekly-menu

**Trigger**: any user goal matching `entry_intents` or classifier picks it.

## Sequence

| # | Agent                    | needs          | produces       |
|---|--------------------------|----------------|----------------|
| 1 | menu-planner             | user_goal      | weekly_menu    |
| 2 | shopping-list-builder    | weekly_menu    | shopping_list  |
| 3 | recipe-writer            | weekly_menu    | recipes        |

Each step runs inside a scoped `delegate_to_agent` call with:
- The agent's full `.md` body as system prompt (frontmatter stripped).
- `input_data` bundled from the blackboard keys declared in `needs`.
- Output required to arrive inside `<produces>{…}</produces>`.
- JSON Schema validated on write; one retry with structured feedback.

## Invariants

- `weekly_menu.days.length == 7`.
- Every dinner has a matching recipe (checked by `menu_complete.py`).
- `shopping_list.aisles` has all five canonical aisles.

## Typical failure modes & mitigations

| Failure                                  | Mitigation                                   |
|------------------------------------------|----------------------------------------------|
| Gemma skips a day                        | Validator flags `days.length != 7`; retry.   |
| JSON with unescaped quotes               | `_repair_json_args` in agent_runtime + retry.|
| Output outside `<produces>` tag          | Explicit retry feedback asking for the tag.  |
| Ingredient mentioned in recipe but       | `shopping_list_sane.py` logs a warning.      |
| absent from shopping list                |                                              |
