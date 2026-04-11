---
name: dialect-registry-tool
description: Lightweight dialect lookup — lists, matches, and describes dialects from the registry
type: tool
tools: Read, Grep
extends: dialects/base
domain: dialects
family: registry
version: 1.0.0
---

# Dialect Registry Tool

**Component Type**: Tool
**Version**: v1
**Status**: [REAL] - Production Ready
**Reliability**: 92%
**Claude Tool Mapping**: Read, Grep

## Purpose

The DialectRegistryTool provides a lightweight interface for discovering and matching
dialects without loading full dialect definitions. It reads `system/dialects/_index.md`
and returns structured metadata about available dialects.

## Core Functionality

### Actions

The tool supports three actions:

#### `list` — List All Dialects
Returns metadata for all registered dialects.

#### `match` — Match Dialect to Context
Given a domain context, returns ranked dialect recommendations filtered by scope and sorted by compression ratio.

#### `describe` — Describe One Dialect
Returns detailed metadata for a specific dialect by ID.

## Input Specification

```yaml
action: string          # "list", "match", or "describe"
dialect_id: string      # Required for "describe" action
domain_context: string  # Required for "match" action (e.g., "memory", "robot", "knowledge")
require_reversible: boolean  # Optional for "match" — filter to reversible dialects only
```

## Output Specification

### For `list`:
```yaml
dialects:
  - dialect_id: string
    name: string
    compression_type: string
    compression_ratio: string
    reversible: boolean
    domain_scope: []
total: number
```

### For `match`:
```yaml
matches:
  - dialect_id: string
    name: string
    compression_type: string
    compression_ratio: string
    reversible: boolean
    rank: number           # 1 = best match
    reason: string         # Why this dialect was ranked here
domain_context: string
total_matches: number
```

### For `describe`:
```yaml
dialect_id: string
name: string
version: string
compression_type: string
compression_ratio: string
reversible: boolean
domain_scope: []
input_format: string
output_format: string
definition_path: string    # Path to full .dialect.md file
```

## Execution Logic

### For `list`:
1. Read `system/dialects/_index.md`
2. Parse the Registered Dialects table
3. Return all entries with their metadata

### For `match`:
1. Read `system/dialects/_index.md`
2. Filter dialects whose `domain_scope` includes the given `domain_context`
3. If `require_reversible` is true, exclude `reversible: false` dialects
4. Rank remaining dialects by compression ratio (highest first)
5. Return ranked matches with reasoning

### For `describe`:
1. Read `system/dialects/_index.md`
2. Find the entry matching `dialect_id`
3. If found, read the dialect's `.dialect.md` file frontmatter for full metadata
4. Return structured metadata including the definition file path

## Claude Tool Mapping

### Implementation Pattern
```markdown
Action: Read system/dialects/_index.md
Observation: [Registry with dialect table]

Action: [Parse and filter based on action type]
Observation: [Structured result]
```

### Tool Usage Strategy
- **Read**: Load `system/dialects/_index.md` for all actions. Optionally load individual `.dialect.md` for `describe`.
- **Grep**: Search for specific dialect IDs or domain scopes when optimizing lookups.

## Example Usage Scenarios

### List all dialects
```yaml
# Input
action: "list"

# Output
dialects:
  - dialect_id: "roclaw-bytecode"
    name: "RoClaw Bytecode"
    compression_type: "structural"
    compression_ratio: "~99%"
    reversible: false
    domain_scope: [robot]
  - dialect_id: "caveman-prose"
    name: "Caveman Prose Compression"
    compression_type: "lexical"
    compression_ratio: "~46-75%"
    reversible: true
    domain_scope: [memory, knowledge]
  - dialect_id: "strategy-pointer"
    name: "Strategy Pointer Notation"
    compression_type: "symbolic"
    compression_ratio: "~60-80%"
    reversible: true
    domain_scope: [memory, robot]
total: 3
```

### Match dialect for memory domain
```yaml
# Input
action: "match"
domain_context: "memory"
require_reversible: true

# Output
matches:
  - dialect_id: "strategy-pointer"
    name: "Strategy Pointer Notation"
    compression_type: "symbolic"
    compression_ratio: "~60-80%"
    reversible: true
    rank: 1
    reason: "Highest compression ratio among reversible dialects in memory scope"
  - dialect_id: "caveman-prose"
    name: "Caveman Prose Compression"
    compression_type: "lexical"
    compression_ratio: "~46-75%"
    reversible: true
    rank: 2
    reason: "Lower compression but preserves natural language readability"
domain_context: "memory"
total_matches: 2
```

### Describe a specific dialect
```yaml
# Input
action: "describe"
dialect_id: "roclaw-bytecode"

# Output
dialect_id: "roclaw-bytecode"
name: "RoClaw Bytecode"
version: "1.0.0"
compression_type: "structural"
compression_ratio: "~99%"
reversible: false
domain_scope: [robot]
input_format: "natural-language"
output_format: "hex-bytecode"
definition_path: "system/dialects/roclaw-bytecode.dialect.md"
```

## Error Handling

- **Unknown action**: Return error listing valid actions: "list", "match", "describe".
- **Missing `dialect_id` for describe**: Return error requesting the dialect_id parameter.
- **Missing `domain_context` for match**: Return error requesting the domain_context parameter.
- **Unknown dialect_id**: Return error with list of valid dialect IDs from registry.
- **No matches for domain**: Return empty matches list with note that no dialects cover the given domain.
- **Registry file missing**: Return error suggesting the `system/dialects/_index.md` file needs to be created.

## Performance

- **Token cost**: Low — reads only `_index.md` (~30 lines) for list/match actions.
- **Caching**: Results can be cached for the entire session — dialect registry rarely changes.
- **No sub-agents**: Simple lookup operation, no Task tool delegation needed.
