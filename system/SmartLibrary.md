# Smart Library — Redirect Stub

**Status**: DEPRECATED (backward-compat stub)
**Version**: v5 (redirect)
**Replaced by**: `system/skills/SkillIndex.md`

---

> **IMPORTANT**: The SmartLibrary has been superseded by the Hierarchical Skill System.
> Load `system/skills/SkillIndex.md` instead for all component lookups.
>
> This file is retained only for backward compatibility with older scripts or agents
> that reference `system/SmartLibrary.md` directly.

## Migration Guide

| Old usage | New usage |
|-----------|-----------|
| Read `system/SmartLibrary.md` to find an agent | Read `system/skills/SkillIndex.md` → domain index → manifest |
| SmartLibrary quick-reference table | `system/skills/SkillIndex.md` Quick Skill Lookup table |
| Agent full spec in SmartLibrary | `system/skills/{domain}/{family}/{skill}.md` |
| Capability/dependency metadata | `system/skills/{domain}/{family}/{skill}.manifest.md` |

## Token Savings

Loading SkillIndex.md + domain index + manifest (~115 lines total) instead of this file
(295 lines) reduces routing-phase token consumption by ~61%.

## Authoritative Registry

The full skill registry is now maintained across:
- **`system/skills/SkillIndex.md`** — top-level routing table (all 15 skills)
- **`system/skills/{domain}/index.md`** — per-domain skill tables (6 files)
- **`system/skills/{domain}/{family}/*.manifest.md`** — individual skill manifests (15 files)
- **`system/skills/{domain}/base.md`** — shared domain behaviors (6 files)
