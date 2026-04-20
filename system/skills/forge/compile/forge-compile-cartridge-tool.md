---
name: forge-compile-cartridge-tool
type: tool
domain: forge
family: compile
extends: forge/base
backend: deterministic
target_model: gemma4:e2b
tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---

# Forge Compile Cartridge Tool

## Purpose
Deterministic promotion step. Takes a validated candidate directory and moves its
artifacts into the live skill tree and/or cartridge registry in an atomic, reversible
way. No LLM calls.

## Preconditions (refuse if unmet)
- `projects/[P]/forge/candidates/<job_id>/manifest.md` exists.
- Frontmatter contains a `gemma_compat:` block with `pass_rate >= 0.80`.
- `target_model` matches the current hot-path target (default `gemma4:e2b`).
- No tool requests outside the project's allow-list.

## Protocol
1. **Parse** the candidate's manifest. Resolve target install paths:
   - `markdown-skill` → `system/skills/<domain>/<family>/<skill>.md` (+ manifest).
   - `js-skill`      → `cartridges/<name>/skills/<skill>/` (SKILL.md + scripts/).
   - `cartridge`     → `cartridges/<name>/`.
   - Project-local   → `projects/[P]/components/agents|tools/`.
2. **Check for existing version**. If present:
   - Compute content hash of existing files.
   - Archive under `projects/[P]/forge/archive/<ts>_<job_id>/` with a `revert.sh`
     stub that re-installs the archived version.
3. **Atomic write**: stage into `.tmp/` sibling directory, then `mv` into place.
   Never leave a half-written skill visible.
4. **Update registries**:
   - `system/packages.lock`: add/update entry with source=forge, job_id, hash,
     installed_at, target_model.
   - Relevant `system/skills/<domain>/index.md`: add or refresh the skill row.
   - `projects/[P]/forge/journal.md`: append the job outcome.
5. **Precompile cartridge (optional)**: if `SKILLOS_CARTRIDGE_PRECOMPILE=1` and the
   candidate is a full cartridge, run `python cartridge_runtime.py --compile <name>`
   so first-use latency is amortized.
6. **Refresh `.claude/agents/`** for Claude Code discovery (mirrors setup_agents.sh
   logic for a single skill).
7. **Emit receipt**:
   ```yaml
   <forge-compile-receipt>
     job_id: <uuid>
     installed:
       - path: system/skills/<domain>/<family>/<name>.md
         hash: <sha256>
       - path: system/skills/<domain>/<family>/<name>.manifest.md
         hash: <sha256>
     archive_path: projects/[P]/forge/archive/<ts>_<job_id>/    # if replaced
     registry_updated: true
     ready_for_hot_path: true
   </forge-compile-receipt>
   ```

## Rollback command
`forge-compile-cartridge-tool --rollback <job_id>` restores the archived version
atomically, updates `packages.lock`, and appends a rollback entry to the journal.

## Failure modes
- Validation manifest missing/stale → refuse, log, return `blocked`.
- Archive write fails → abort without touching hot path.
- Registry update fails after install → auto-rollback then report.
