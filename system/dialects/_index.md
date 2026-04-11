---
type: dialect-registry
version: 1.0.0
dialect_count: 3
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

## Dialect Files

All dialect definitions live in `system/dialects/` as `.dialect.md` files:

- `system/dialects/roclaw-bytecode.dialect.md`
- `system/dialects/caveman-prose.dialect.md`
- `system/dialects/strategy-pointer.dialect.md`

## Matching Protocol

To select the best dialect for a task:

1. **Filter by `domain_scope`** — only consider dialects whose scope includes the active SkillOS domain.
2. **Filter by `reversible`** — if the content must be expandable later, exclude `reversible: false` dialects.
3. **Rank by `compression_ratio`** — higher compression wins when multiple dialects match.
4. **Check `compression_type`** — structural dialects require strict format adherence; lexical and symbolic are more flexible.
