---
skill_domain: dialects
type: base-template
version: 1.0.0
---

# Dialects Domain — Shared Behaviors

All skills in the `dialects/` domain inherit these conventions.

## Purpose

The dialects domain provides domain-specific token compression and expansion capabilities.
Dialects transform content between verbose natural language and compact, domain-optimized
representations — reducing token cost for storage, memory, and inter-agent communication.

## Dialect Registry

All dialect definitions live in `system/dialects/` as `.dialect.md` files.
The registry index at `system/dialects/_index.md` lists all available dialects with
their metadata, domain scope, and compression characteristics.

## Compression Types

| Type | Description | Example |
|------|-------------|---------|
| structural | Changes representation entirely (text → binary/hex) | roclaw-bytecode |
| lexical | Strips/abbreviates words, output stays natural language | caveman-prose |
| symbolic | Replaces constructs with symbols and pointers | strategy-pointer |

## Standard Workflow

1. **Resolve dialect**: Identify which dialect to use — explicit ID or auto-match via registry.
2. **Load definition**: Read the `.dialect.md` file for rules, grammar, and preservation constraints.
3. **Apply transform**: Compress or expand the content following the dialect's rules.
4. **Validate output**: Check preservation rules were respected, verify grammar compliance.
5. **Report metrics**: Return compression ratio, reversibility confidence, and any information loss.

## Conventions

- **Dialect definitions are data, not skills**: `.dialect.md` files in `system/dialects/` are read-only
  reference material. Skills in this domain operate ON them.
- **Preservation rules are absolute**: If a dialect says "preserve code blocks", that rule cannot
  be overridden by compression pressure.
- **Compression ratios are estimates**: Actual ratios depend on input verbosity. Report the real
  ratio alongside the dialect's claimed range.
- **Reversibility is per-dialect**: Some dialects (structural) cannot be reversed. Always check
  the `reversible` field before promising expansion.

## Token Efficiency

- Load dialect definitions only when needed — they are 60-120 lines each.
- Use the registry tool (`dialect-registry-tool`) for quick lookups before loading full definitions.
- Cache dialect definitions within a session — they don't change during execution.
