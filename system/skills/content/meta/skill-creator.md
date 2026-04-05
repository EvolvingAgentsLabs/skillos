---
name: skill-creator
extends: content/base
domain: content
family: meta
source: github:anthropics/skills/skill-creator
source_file: components/skills/skill-creator/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash, Glob]
---

# Skill Creator

Bootstrap new SkillOS skills from a template — generates manifest, spec, and registers in the domain index.

## Source

Wraps `components/skills/skill-creator/SKILL.md` (sourced from `anthropics/skills`).
Extended with SkillOS 3-level hierarchy conventions.

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Scaffold skill** | Generate manifest + spec from a description |
| **Register skill** | Add entry to domain index.md |
| **Create domain** | Bootstrap a new domain (base.md + index.md) |
| **Validate skill** | Check manifest/spec completeness |
| **Copy to .claude/agents/** | Make agent-type skills immediately discoverable |

---

## Protocol

### Step 1 — Gather Requirements

Before creating a skill, collect:
- `name`: kebab-case skill name
- `type`: `agent` or `tool`
- `domain`: which domain (existing or new)
- `family`: sub-directory within domain
- `description`: one-line description
- `capabilities`: comma-separated list
- `tools_required`: Claude Code tools needed
- `invoke_when`: trigger keywords/phrases

### Step 2 — Determine Paths

```
Manifest: system/skills/{domain}/{family}/{name}.manifest.md
Full spec: system/skills/{domain}/{family}/{name}.md
Domain index: system/skills/{domain}/index.md
Source (if external): components/skills/{name}/SKILL.md
```

### Step 3 — Generate Manifest

```markdown
---
skill_id: {domain}/{family}/{name}
name: {name}
type: {agent|tool}
domain: {domain}
family: {family}
extends: {domain}/base
version: 1.0.0
source: {original|github:org/repo/path}
description: {one-line description}
capabilities: [{comma-separated list}]
tools_required: [{tools}]
{subagent_type: {name}   ← only for type: agent}
token_cost: {low|medium|high}
reliability: {N}%
invoke_when: [{trigger phrases}]
full_spec: system/skills/{domain}/{family}/{name}.md
---
```

### Step 4 — Generate Full Spec

Use this template:
```markdown
---
name: {name}
extends: {domain}/base
domain: {domain}
family: {family}
source: {provenance}
version: 1.0.0
tools: [{tools}]
---

# {Title}

{One-paragraph description}

## Capabilities
{table}

## Protocol
{step-by-step instructions}

## Examples
{2-3 concrete examples}
```

### Step 5 — Register in Domain Index

Append a row to `system/skills/{domain}/index.md`:
```markdown
| {name} | {family} | {subagent_type or _(tool)_} | system/skills/{domain}/{family}/{name}.manifest.md | {token_cost} |
```
Update `total_skills:` in the frontmatter.

### Step 6 — Update SkillIndex.md

If this is the domain's first new skill, verify domain row exists in `system/skills/SkillIndex.md`.
Update `total_skills:` count.

### Step 7 — Agent Discovery (agent-type skills only)

Copy full spec to `.claude/agents/{name}.md` for immediate Claude Code discovery:
```bash
cp system/skills/{domain}/{family}/{name}.md .claude/agents/{name}.md
```

---

## New Domain Creation

When `domain` does not exist in `system/skills/`:
1. Create `system/skills/{domain}/` directory
2. Create `system/skills/{domain}/base.md` with shared behaviors template
3. Create `system/skills/{domain}/index.md` with empty skills table
4. Add domain row to `system/skills/SkillIndex.md`

---

## Examples

**"Create a new skill for sending Slack notifications"**
→ name: slack-notifier, type: tool, domain: integrations, family: messaging
→ Generates manifest + spec → registers in integrations/index.md

**"Add a web-scraper agent to the research domain"**
→ name: web-scraper-agent, type: agent, domain: research, family: web
→ Generates files + copies to .claude/agents/web-scraper-agent.md
