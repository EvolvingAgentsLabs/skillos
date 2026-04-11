---
type: dialect-registry
version: 1.0.0
dialect_count: 9
last_updated: "2026-04-11"
---

# Dialect Registry

Central index of all domain-specific token compression dialects available in SkillOS.

## Registered Dialects

| dialect_id | name | compression_type | compression_ratio | reversible | domain_scope |
|------------|------|-----------------|-------------------|------------|--------------|
| roclaw-bytecode | RoClaw Bytecode | structural | ~99% | false | robot |
| caveman-prose | Caveman Prose Compression | lexical | ~46-75% | true | memory, knowledge |
| strategy-pointer | Strategy Pointer Notation | symbolic | ~60-80% | true | memory, robot |
| trace-log | Trace Log Compression | structural | ~70-80% | true | robot, memory |
| memory-xp | Memory Experience Compression | symbolic | ~65-75% | true | memory |
| constraint-dsl | Constraint DSL | symbolic | ~55-70% | true | memory, robot, knowledge |
| exec-plan | Execution Plan Compression | symbolic | ~70-85% | true | orchestration, memory |
| strict-patch | Strict Patch Notation | structural | ~90-98% | true | orchestration, knowledge |
| dom-nav | DOM Navigation Dialect | structural | ~90-97% | false | orchestration, knowledge |

## Dialect Files

All dialect definitions live in `system/dialects/` as `.dialect.md` files:

- `system/dialects/roclaw-bytecode.dialect.md`
- `system/dialects/caveman-prose.dialect.md`
- `system/dialects/strategy-pointer.dialect.md`
- `system/dialects/trace-log.dialect.md`
- `system/dialects/memory-xp.dialect.md`
- `system/dialects/constraint-dsl.dialect.md`
- `system/dialects/exec-plan.dialect.md`
- `system/dialects/strict-patch.dialect.md`
- `system/dialects/dom-nav.dialect.md`

## Matching Protocol

To select the best dialect for a task:

1. **Filter by `domain_scope`** — only consider dialects whose scope includes the active SkillOS domain.
2. **Filter by `reversible`** — if the content must be expandable later, exclude `reversible: false` dialects.
3. **Rank by `compression_ratio`** — higher compression wins when multiple dialects match.
4. **Check `compression_type`** — structural dialects require strict format adherence; lexical and symbolic are more flexible.

## MAD (Minimum Actionable Dialects) for Edge AI

Three flagship dialects demonstrate the full spectrum of domain-specific compression for small models:

| Pillar | Dialect | Domain | Compression | Key Insight |
|--------|---------|--------|-------------|-------------|
| Hardware | `roclaw-bytecode` | Motor control | ~99% | 6 bytes instead of JSON. 100% precision. |
| Reasoning & Memory | `caveman-prose` | Prose, logs | ~46-75% | Retains exact logic, strips verbal noise. |
| Software Engineering | `strict-patch` | Code editing | ~90-98% | 20-token line patches instead of 1,000-token file rewrites. Eliminates small-model hallucinations. |
