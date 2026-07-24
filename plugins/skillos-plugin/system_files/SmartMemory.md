# SmartMemory System Specification

## Overview
SmartMemory is the persistent knowledge layer of SkillOS, enabling the system to learn from past executions and improve over time. It provides structured storage and retrieval of interaction traces, agent designs, and extracted patterns.

## Architecture

### Memory Hierarchy

```
memory/
├── short_term/          # Raw interaction logs (ephemeral)
│   └── [timestamp]_[agent]_[task].md
└── long_term/           # Consolidated learnings (persistent)
    ├── project_learnings.md
    ├── agent_templates/
    ├── workflow_patterns/
    └── domain_knowledge/
```

### Memory Types

#### 1. Short-Term Memory
**Purpose**: Capture raw, temporal interaction data during project execution

**Characteristics**:
- Granular: One file per agent interaction
- Chronological: Timestamped for sequence reconstruction
- Complete: Full prompts, responses, and metadata
- Project-scoped: Lives in project-specific directory

**Lifecycle**: Created during execution, consumed during consolidation, archived or deleted after learning extraction

#### 2. Long-Term Memory
**Purpose**: Store distilled knowledge for future reuse

**Characteristics**:
- Abstract: Generalized patterns, not specific interactions
- Structured: Organized by type (templates, patterns, knowledge)
- Persistent: Survives beyond individual projects
- Queryable: Designed for efficient retrieval

**Lifecycle**: Created by MemoryConsolidationAgent, queried at project start, updated with new learnings

## Memory Operations

### Write Operations
- **Log**: MemoryAnalysisAgent writes interaction traces to short_term
- **Consolidate**: MemoryConsolidationAgent reads short_term, writes to long_term
- **Update**: Merge new learnings with existing long_term knowledge

### Read Operations
- **Query**: Search long_term memory for relevant patterns
- **Retrieve**: Load specific agent templates or workflows
- **Scan**: Review short_term logs during active execution

## Data Formats

### Interaction Log Format
```markdown
# [Agent Name] - [Task]
**Timestamp**: 2025-01-11T14:30:22Z
**Agent**: AgentName (type)
**Task**: Brief description

## Request
[Complete prompt]

## Response
[Complete response]

## Metadata
- Status: success|failure|partial
- Output Files: [list]
- Dependencies: [list]
```

### Learning Format
```markdown
# Project Learnings: [Project Name]
**Date**: YYYY-MM-DD
**Goal**: [Original goal]

## Executive Summary
[Overview]

## Agent Architecture
[Agent designs and effectiveness]

## Successful Strategies
[Reusable patterns]

## Challenges Encountered
[Problems and solutions]

## Reusable Templates
[Generalized agent specs]

## Recommendations
[Future guidance]
```

## Integration with Core Agents

### MemoryAnalysisAgent
- Writes to short_term memory
- Maintains consistent logging format
- Captures complete interaction context

### MemoryConsolidationAgent
- Reads short_term memory
- Extracts patterns and learnings
- Writes to long_term memory
- Generates reusable templates

### SystemAgent
- Queries long_term memory before creating agents
- Leverages existing templates when applicable
- Initiates consolidation after project completion

## Memory-Driven Learning Loop

1. **Execution**: SystemAgent orchestrates project, MemoryAnalysisAgent logs all interactions
2. **Consolidation**: MemoryConsolidationAgent analyzes logs, extracts learnings
3. **Storage**: Learnings persisted to long_term memory
4. **Retrieval**: Future projects query long_term memory for relevant patterns
5. **Application**: SystemAgent uses retrieved patterns to create better agents
6. **Iteration**: New learnings continuously improve the knowledge base

## Best Practices

### For Logging
- Log immediately after interactions
- Include complete context
- Use descriptive filenames
- Maintain consistent formatting

### For Consolidation
- Wait until project completion
- Analyze entire short_term history
- Extract generalizable patterns
- Document both successes and failures

### For Querying
- Search before creating new agents
- Adapt templates to current context
- Combine multiple patterns when beneficial
- Update templates based on new experiences

## Future Enhancements
- Cross-project pattern detection
- Semantic search capabilities
- Automatic template evolution
- Performance metrics tracking
