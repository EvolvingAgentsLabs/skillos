# Flow: run-skill

**Trigger**: any user goal matching a Gallery JS skill via `entry_intents` or router.

## Sequence

| # | Agent/Step       | needs                                      | produces      |
|---|------------------|--------------------------------------------|---------------|
| 1 | param-extractor  | user_goal, selected_skill, skill_instructions | skill_params  |
| 2 | js-executor      | skill_params                               | skill_result  |

### Step 1: param-extractor (LLM call)

The LLM reads the skill's SKILL.md instructions (injected via `skill_instructions`
on the blackboard) and extracts structured parameters from the user's goal.

Output: `<produces>{"skill_name": "...", "data": "...", "secret": ""}</produces>`
Validated against `skill_params.schema.json`.

### Step 2: js-executor (DETERMINISTIC — no LLM call)

Node.js subprocess executes the Gallery JS skill with the extracted parameters.
This step is handled by `CartridgeRunner._run_js_skill()`, not by LLM delegation.

Output: `{"result": "...", "error": null, ...}`
Validated against `skill_result.schema.json`.

## Invariants

- `skill_params.skill_name` must match a loaded Gallery skill
- `skill_params.data` must be a valid JSON string
- `skill_result` must not contain an `error` field (or error must be null/empty)

## Typical failure modes & mitigations

| Failure | Mitigation |
|---|---|
| Gemma nests data as object instead of string | Retry with explicit "data must be a JSON string" feedback |
| Gemma picks wrong skill | Router pre-selects skill; param-extractor confirms |
| Node.js timeout | 30s timeout with clear error message |
| Skill requires secret not provided | Error returned; user prompted for API key |
