---
name: project-scaffold-tool
type: tool
version: v1
status: "[REAL] - Production Ready"
description: >
  Bootstraps a complete SkillOS project directory structure from a project name,
  description, and optional agent templates. Creates all required subdirectories,
  initial state files, a project README, and copies agent markdown files into
  .claude/agents/ for immediate Claude Code discovery.
tools: Bash, Write, Read
---

# ProjectScaffoldTool

**Component Type**: Tool
**Version**: v1
**Status**: [REAL] - Production Ready
**Claude Tool Mapping**: Bash, Write, Read

## Purpose

Canonical bootstrap mechanism for new SkillOS projects. Eliminates ad-hoc directory creation and enforces the standard project layout defined in CLAUDE.md.

## Input Specification

```yaml
project_name: string            # CamelCase or underscore-separated, no spaces
description: string             # One-paragraph project purpose
agent_templates:
  - name: string                # Agent filename stem
    role: string                # Brief role description
    capabilities: []            # Capability strings
    tools: []                   # Claude Code tools (Read, Write, Bash, etc.)
options:
  overwrite_existing: boolean   # Default: false
  register_in_smart_library: boolean  # Default: true
  dry_run: boolean              # Default: false
```

## Output Specification

```yaml
status: "success" | "partial" | "failed"
project_root: string
created_paths:
  directories: []
  files: []
agent_discovery:
  agents_written: []
  agents_copied_to_discovery: []
  agents_skipped: []
smart_library_updated: boolean
warnings: []
errors: []
summary: string
```

## Execution Logic

### Phase 1: Input Validation
- Normalize project_name to `Project_` prefix
- Conflict check if overwrite_existing is false

### Phase 2: Directory Tree Creation
```bash
mkdir -p \
  projects/[ProjectName]/components/agents \
  projects/[ProjectName]/components/tools \
  projects/[ProjectName]/input \
  projects/[ProjectName]/output \
  projects/[ProjectName]/memory/short_term \
  projects/[ProjectName]/memory/long_term \
  projects/[ProjectName]/state
```

### Phase 3: State File Generation
Writes plan.md, context.md, variables.json, history.md, constraints.md with project-aware templates.

### Phase 4: Project README Generation
Writes projects/[ProjectName]/README.md with metadata, agent roster, and execution notes.

### Phase 5: Agent Template Creation
For each agent_template, creates markdown with YAML frontmatter and copies to `.claude/agents/[ProjectName]_[AgentName].md`.

### Phase 6: SmartLibrary Registration
Appends placeholder registration block to system/SmartLibrary.md if not already present.

## Claude Tool Mapping

- **Bash**: Directory creation, existence checks, agent discovery copy loop
- **Write**: State files, README, agent templates, SmartLibrary updates
- **Read**: SmartLibrary conflict detection

## Integration with SystemAgent

Called during planning phase when target project directory does not yet exist. Invoked immediately after project name derivation from user goal.

## Error Handling

- **Permission Denied**: Return failed, suggest chmod
- **SmartLibrary Write Failure**: Partial status, manual registration warning
- **Duplicate Agent Name**: Skip copy, add warning
- **Blank project_name**: Immediate failure
