---
name: spawn-child-agent
description: Creates a Child agent by copying the Father's DNA (markdown spec), registering the new generation in lineage.json, and making the Child discoverable via .claude/agents/.
tools: Read, Write, Bash, Task
extends: genealogy/base
---

# Spawn-Child Agent

## Purpose

Create a new Child agent by cloning the active Father's DNA, assigning it a
lineage identity, and registering it so Claude Code can discover it. The
Child is a *worker* — it executes delegated tasks — while the Father tutors.

## Inputs

```yaml
father_agent_id: string          # e.g. "system-agent" (gen-0) or "father-quill-gen1"
father_dna_path: string          # path to the Father's full-spec .md
project: string                  # project name (for lineage.json location)
lineage_tag: string              # stable noun (e.g. "quill"); generated at gen-1, reused thereafter
kernel_mode: "genealogy"         # required; must match variables.json
```

## Outputs

```yaml
child_agent_id: string           # e.g. "child-quill-gen1"
child_dna_path: string           # projects/<project>/components/agents/<child>.md
dna_hash: string                 # sha256 of the copied DNA
generation: integer
registered: bool                 # true if copied into .claude/agents/
lineage_json_path: string
```

## Execution Logic

### Phase 1 — Preflight
1. Read `projects/<project>/state/variables.json`; confirm `kernel_mode: genealogy`.
   If not present or not `genealogy`, **abort** with error `GEN-001: kernel_mode not genealogy`.
2. Read `projects/<project>/state/lineage.json` if it exists; else initialize empty structure.
3. Determine next `generation = max(existing.generation) + 1`.
4. Resolve Father by `father_agent_id`:
   - If `generation == 1`: Father is `system-agent` (the Grandfather). DNA path = `system/skills/orchestration/core/system-agent.md`.
   - Otherwise: Father must have `status: promoted` in lineage.json.
5. Confirm lineage tag: if `generation == 1` and no tag provided, generate a stable short noun (e.g. random pick from `system/skills/genealogy/spawn/tag-pool.txt` if present, else UUID-short).

### Phase 2 — DNA Copy
1. Read Father's DNA from `father_dna_path` (full-spec .md).
2. Transform frontmatter:
   - Replace `name:` with `child-<tag>-gen<N>`
   - Replace `description:` with Father's description + ` (gen<N>, offspring of <father_agent_id>)`
   - Add `lineage_id`, `generation`, `parent_id`, `dna_hash` (computed after write), `spawned_at` ISO-8601
   - Preserve `extends:` chain (DNA-003: never shorten it)
   - Preserve all declared `capabilities:` (DNA-004: never remove without rationale)
   - Preserve `tools:` (DNA-005: never drift at spawn — mutations come later via tutor)
3. Write to `projects/<project>/components/agents/child-<tag>-gen<N>.md`.
4. Compute `sha256` of the written file → `dna_hash`.

### Phase 3 — Manifest Generation
1. Generate a companion `.manifest.md` at `projects/<project>/components/agents/child-<tag>-gen<N>.manifest.md` with:
   - `skill_id: project/<project>/child-<tag>-gen<N>`
   - `full_spec: projects/<project>/components/agents/child-<tag>-gen<N>.md`
   - `extends: <father's extends chain>`
   - `lineage_id`, `generation`, `parent_id`, `dna_hash`
2. This manifest is how system-agent's lazy-loading protocol finds the Child.

### Phase 4 — Registry Update
1. Copy both files to `.claude/agents/<project>-child-<tag>-gen<N>.md` (project prefix per
   existing setup_agents convention). No setup_agents.sh re-run required for project agents.
2. Append a new `members[]` entry to `projects/<project>/state/lineage.json`:
   ```json
   {
     "agent_id": "child-<tag>-gen<N>",
     "generation": N,
     "parent_id": "<father_agent_id>",
     "spawn_timestamp": "<ISO-8601>",
     "dna_hash": "<sha256>",
     "status": "tutoring",
     "promotion_criteria_met": {
       "tasks_passed": 0,
       "quality_avg": 0.0,
       "cross_domain_passes": 0,
       "consecutive_failures": 0
     }
   }
   ```
3. Append `<father_agent_id>@<N-1> → child-<tag>-gen<N>@<N>` to `lineage_path`.

### Phase 5 — Handoff
1. Append a line to `projects/<project>/state/history.md`:
   `<ISO> SPAWN: <father_agent_id> → child-<tag>-gen<N> (dna_hash: <short>)`
2. Return the output structure. System-agent (or current Father) may now delegate
   the first task to `child-<tag>-gen<N>` via the Task tool.

## Claude Tool Mapping

| Step | Tool |
|------|------|
| Read Father DNA + lineage.json | Read |
| Compute sha256 | Bash (`sha256sum`) |
| Write Child DNA + manifest | Write |
| Copy to .claude/agents/ | Bash (`cp`) |
| Append to lineage.json | Read + Write (load → mutate → save) |

## Error Handling

- `GEN-001` kernel_mode not genealogy → abort, no side effects.
- `GEN-002` Father not promoted (for N≥2) → abort, instruct caller to run promote-child-agent first.
- `GEN-003` lineage.json corrupt → move to `lineage.json.bak-<timestamp>`, reinitialize, log WARN.
- `GEN-004` write failure → do NOT update lineage.json; return partial-success = false.

## Non-Goals (v1)

- Multiple concurrent Children per Father (siblings) — one Child per Father at a time.
- Cross-project lineage (Father in Project A → Child in Project B).
- Runtime `.claude/agents/` hot-reload verification — relies on Claude Code's own discovery.
