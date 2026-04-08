# Skills: Agents and Tools

A **Skill** in SkillOS is any agent or tool defined as a markdown document. Skills are the basic unit of computation — equivalent to programs in a traditional OS.

---

## Anatomy of a Skill

Every skill has two parts: YAML frontmatter (metadata) and a markdown body (behavior specification).

```markdown
---
name: my-agent                           # Unique kebab-case identifier
type: agent                              # agent | tool
domain: orchestration                    # Skill tree domain
family: core                             # Skill tree family
extends: orchestration/base              # Inherits shared domain behaviors
version: 1.0.0
status: "[REAL] - Production Ready"      # [REAL] | [DRAFT] | [DEPRECATED]
description: >
  One-sentence description. Used by the router to decide when to invoke this skill.
tools: [Read, Write, WebFetch]           # Claude Code native tools available
capabilities:
  - capability-one
  - capability-two
invoke_when:                             # Routing triggers
  - when this goal is detected
  - another trigger phrase
---

# MyAgent

## Purpose
What this skill does and why it exists.

## Instructions
Step-by-step behavior the LLM follows when acting as this agent.

1. First, do this
2. Then, do that
3. Return result in this format

## Output Format
Description of what this skill produces.
```

---

## Agents vs Tools

| | Agent | Tool |
|-|-------|------|
| **Decides** | Yes — reasons, plans, delegates | No — executes deterministically |
| **Can spawn sub-agents** | Yes (via `Task` tool) | No |
| **Returns** | Structured result + rationale | Raw output |
| **Example** | `system-agent`, `memory-consolidation-agent` | `skill-package-manager-tool`, `query-memory-tool` |

---

## Skill Tree Placement

Place skills in the domain that matches their purpose:

| Domain | Purpose | Example Skills |
|--------|---------|----------------|
| `orchestration` | Goal execution, workflow | system-agent |
| `planning` | HWM hierarchical planning, subgoal generation | hwm-planner-agent, flat-planner-agent |
| `memory` | Learning, consolidation | memory-analysis-agent, query-memory-tool |
| `validation` | Health checks, security | validation-agent, skill-security-scan-agent |
| `recovery` | Error handling | error-recovery-agent |
| `project` | Scaffolding, packages | project-scaffold-tool, skill-package-manager-tool |
| `robot` | Physical robot control | roclaw-navigation-agent, roclaw-dream-agent |

### File structure

```
system/skills/{domain}/{family}/{skill-name}.md
system/skills/{domain}/{family}/{skill-name}.manifest.md
```

---

## Creating a Skill

### Step 1: Write the full spec

```markdown
---
name: data-cleaning-agent
type: agent
domain: orchestration
family: data
extends: orchestration/base
version: 1.0.0
description: Cleans and normalizes CSV data files, handles missing values and type errors
tools: [Read, Write, Bash]
capabilities:
  - csv-parsing
  - missing-value-handling
  - type-normalization
invoke_when:
  - clean data
  - normalize CSV
  - fix missing values
---

# DataCleaningAgent

## Purpose
Analyzes CSV files, identifies data quality issues, and produces a cleaned version.

## Instructions

1. Read the input CSV file
2. Identify columns with missing values, type mismatches, or outliers
3. Apply cleaning rules:
   - Numeric columns: fill missing with median
   - String columns: fill missing with empty string
   - Remove rows where >50% of values are missing
4. Write cleaned file to output/cleaned_{filename}
5. Write a cleaning report to output/cleaning_report.md

## Output
- Cleaned CSV at `output/cleaned_{filename}`
- Report at `output/cleaning_report.md` with: rows removed, columns fixed, changes made
```

### Step 2: Write the manifest

The manifest is a lightweight routing card (~15 lines). The router loads this before the full spec:

```markdown
---
skill_id: orchestration/data/data-cleaning-agent
name: data-cleaning-agent
type: agent
domain: orchestration
family: data
extends: orchestration/base
version: 1.0.0
description: Cleans and normalizes CSV data files, handles missing values and type errors
capabilities: [csv-parsing, missing-value-handling, type-normalization]
tools_required: [Read, Write, Bash]
token_cost: medium
reliability: 90%
invoke_when: [clean data, normalize CSV, fix missing values, data quality]
full_spec: system/skills/orchestration/data/data-cleaning-agent.md
---
```

### Step 3: Register in the domain index

Add a row to `system/skills/orchestration/index.md`:

```markdown
| data-cleaning-agent | data | orchestration | clean data, normalize CSV, fix missing values | orchestration/data/data-cleaning-agent.manifest.md |
```

### Step 4: Make it discoverable

```bash
./setup_agents.sh    # Re-populates .claude/agents/
```

Or for project-specific skills, SkillOS auto-copies to `.claude/agents/` at runtime with a project prefix.

---

## Project-Specific Skills

For skills that only apply to one project, place them in:

```
projects/[ProjectName]/components/agents/my-agent.md
projects/[ProjectName]/components/tools/my-tool.md
```

SystemAgent creates these automatically during execution when it detects a capability gap. They are namespaced with the project prefix in `.claude/agents/` to prevent conflicts.

---

## Skill Inheritance

Declare inheritance with `extends` in frontmatter:

```yaml
extends: validation/base
```

The LLM merges the base spec's behaviors with the child skill's instructions at runtime. This means:

- `validation/base` shared behaviors (read-only, report format, escalation rules) apply automatically
- The child skill only needs to define what's different or specific to its function
- Changes to `base.md` propagate to all inheriting skills without any code changes

**Domain bases:**

| Base | Key Shared Behaviors |
|------|---------------------|
| `orchestration/base` | Goal decomposition pattern, state management, memory logging |
| `planning/base` | World state schema, MPPI optimization, cost function, subgoal protocol, replanning triggers |
| `memory/base` | Memory format, query interface, consolidation triggers |
| `validation/base` | Read-only constraint, health report format, HEALTHY/DEGRADED/CRITICAL |
| `recovery/base` | Retry strategy, circuit breaker, exponential backoff |
| `project/base` | Project structure creation, package manifest format |
| `robot/base` | Cognitive Trinity integration, trace fidelity tagging, dream logging |

---

## Skill Package Manager

Install skills from external sources:

```bash
# Install from configured sources
skillos execute: "skill install research-assistant-agent"

# Search across all sources + GitHub
skillos execute: "skill search quantum"

# Update all installed skills
skillos execute: "skill update"

# List installed skills with source and security verdict
skillos execute: "skill list"

# Remove a skill
skillos execute: "skill remove outdated-agent"
```

**Configure sources** in `system/sources.list`:
```
# type  uri                        branch  component-path
github  anthropics/skills          main    skills/
github  myorg/my-custom-skills     main    agents/
url     https://example.com/my-skill.md
local   /path/to/local/skills/
```

Every install automatically goes through the security scanner before writing to disk. See [docs/security.md](security.md).

---

## Skill Status Tags

| Tag | Meaning |
|-----|---------|
| `[REAL] - Production Ready` | Fully implemented, tested |
| `[REAL] - Beta` | Implemented, some edge cases not covered |
| `[DRAFT]` | Spec written, not yet verified |
| `[DEPRECATED]` | Superseded — redirect stub only |

---

## Best Practices

- **One capability per skill** — small, focused skills compose better than large monoliths
- **Write the `description` carefully** — it's used for routing; vague descriptions cause misrouting
- **Use `invoke_when` phrases** that match how users actually phrase goals
- **Declare only the tools you need** — the security scanner flags overclaiming
- **Always write a manifest** — it enables lazy loading and keeps routing fast
- **Extend the domain base** — don't repeat shared behaviors, inherit them
