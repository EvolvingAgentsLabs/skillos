# Flow: new-installation

## Sequence

| # | Agent              | needs         | produces      |
|---|--------------------|---------------|---------------|
| 1 | load-calculator    | user_goal     | load_profile  |
| 2 | circuit-designer   | load_profile  | circuits      |

## Post-step validators

- `compliance_checker.py` — pure-Python IEC 60364 subset. **The rules live in
  code, not in the LLM prompt.** If this fails, the cartridge reports a
  compliance violation rather than silently shipping an unsafe design.

## Why this is safer than a single mega-prompt

- The LLM only decides *what appliances go in which rooms* and *how to
  group them into circuits*. Both are shape-matching tasks Gemma handles well.
- The hard safety rules (wire/breaker ratios, RCD on wet rooms,
  25% breaker margin) are enforced deterministically.
- A rule update (e.g. new code edition) is a Python diff, not a prompt
  rewrite — and it's reviewable like any other code.
