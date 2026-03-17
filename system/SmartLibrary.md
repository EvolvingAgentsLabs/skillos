# Smart Library - Component Registry

**Status**: [REAL] - Production Ready
**Version**: v4
**Purpose**: Comprehensive registry of all SkillOS agents and tools with metadata, capabilities, dependencies, and integration patterns.

## Quick-Reference Lookup

| Component | Type | Category | Claude Name / Tool | Reliability |
|---|---|---|---|---|
| SystemAgent | Agent | System | system-agent | 95% |
| MemoryAnalysisAgent | Agent | System | memory-analysis-agent | 90% |
| MemoryConsolidationAgent | Agent | System | memory-consolidation-agent | 85% |
| ErrorRecoveryAgent | Agent | System | error-recovery-agent | 90% |
| ValidationAgent | Agent | System | validation-agent | 92% |
| QueryMemoryTool | Tool | System | Read, Grep, Bash, Task | 92% |
| ClaudeCodeToolMap | Registry | System | (all native tools) | 98% |
| MemoryTraceManager | Tool | System | Read, Write, Grep, Bash | 95% |
| ProjectScaffoldTool | Tool | System | Bash, Write, Read | 94% |
| SkillPackageManagerTool | Tool | System | Bash, Read, Write, Grep, Glob, WebFetch | 88% |

## Dependency Graph

```
SystemAgent
├── depends on: MemoryAnalysisAgent, MemoryConsolidationAgent, ErrorRecoveryAgent
├── uses: QueryMemoryTool, ClaudeCodeToolMap, MemoryTraceManager, ProjectScaffoldTool
└── delegates to: [any project-specific agent]

ErrorRecoveryAgent
└── depends on: ClaudeCodeToolMap (for fallback chain)

ValidationAgent
└── depends on: SmartLibrary (this file), ClaudeCodeToolMap

QueryMemoryTool
└── depends on: MemoryAnalysisAgent (sub-agent), system/SmartMemory.md

MemoryTraceManager
└── depends on: system/SmartMemory.md (writes to)

ProjectScaffoldTool
└── depends on: SmartLibrary (registration)

SkillPackageManagerTool
└── depends on: sources.list, packages.lock, SmartLibrary (registration)
```

---

## System Agents

### SystemAgent
- **Type**: Agent
- **Status**: [REAL] - Production Ready
- **Version**: v2
- **File**: system/agents/SystemAgent.md
- **Claude Agent Name**: system-agent
- **Capabilities**: Core orchestration, workflow management, sub-agent delegation, error recovery, parallel execution
- **Tools**: Read, Write, Glob, Grep, Bash, WebFetch, Task
- **Depends On**: MemoryAnalysisAgent, MemoryConsolidationAgent, ErrorRecoveryAgent, QueryMemoryTool, ClaudeCodeToolMap
- **Use Cases**: High-level task planning, complex workflow orchestration, system state management
- **Cost**: Medium (delegates to specialized sub-agents)
- **Reliability**: 95%

### MemoryAnalysisAgent
- **Type**: Agent
- **Status**: [REAL] - Production Ready
- **File**: system/agents/MemoryAnalysisAgent.md
- **Claude Agent Name**: memory-analysis-agent
- **Capabilities**: Cross-project learning, pattern recognition, historical analysis
- **Tools**: Read, Grep, Bash
- **Depends On**: SmartMemory.md
- **Use Cases**: Memory consultation, learning from past executions, behavioral pattern analysis
- **Cost**: Low-Medium
- **Reliability**: 90%

### MemoryConsolidationAgent
- **Type**: Agent
- **Status**: [REAL] - Production Ready
- **File**: system/agents/MemoryConsolidationAgent.md
- **Claude Agent Name**: memory-consolidation-agent
- **Capabilities**: Memory log maintenance, experience aggregation, learning optimization
- **Tools**: Read, Write, Grep
- **Depends On**: SmartMemory.md, MemoryTraceManager
- **Use Cases**: Memory log cleanup, pattern extraction, knowledge base management
- **Cost**: Low
- **Reliability**: 85%

### ErrorRecoveryAgent
- **Type**: Agent
- **Status**: [REAL] - Production Ready
- **Version**: v1
- **File**: system/agents/ErrorRecoveryAgent.md
- **Claude Agent Name**: error-recovery-agent
- **Capabilities**: Error classification, retry with backoff, circuit breaker, alternative approach selection, scope reduction
- **Tools**: Read, Write, Grep, Bash
- **Depends On**: ClaudeCodeToolMap (fallback chain reference)
- **Use Cases**: Fault tolerance, error recovery orchestration, resilience management
- **Cost**: Low-Medium ($0.005-0.025 per recovery session)
- **Reliability**: 90%

### ValidationAgent
- **Type**: Agent
- **Status**: [REAL] - Production Ready
- **Version**: v1
- **File**: system/agents/ValidationAgent.md
- **Claude Agent Name**: validation-agent
- **Capabilities**: Agent frontmatter validation, tool spec validation, project structure checks, SmartLibrary consistency, memory log format validation
- **Tools**: Read, Write, Grep, Glob
- **Depends On**: SmartLibrary.md, ClaudeCodeToolMap.md
- **Use Cases**: Pre-execution health checks, post-creation validation, periodic system audits
- **Cost**: Low
- **Reliability**: 92%

## System Tools

### QueryMemoryTool
- **Type**: Tool
- **Status**: [REAL] - Production Ready
- **File**: system/tools/QueryMemoryTool.md
- **Claude Tool Mapping**: Read, Grep, Bash, Task
- **Depends On**: MemoryAnalysisAgent (invoked as sub-agent)
- **Capabilities**: Standardized memory consultation interface, query optimization
- **Use Cases**: Memory-driven planning, historical pattern analysis, adaptive behavior
- **Cost**: Low-Medium
- **Reliability**: 92%

### ClaudeCodeToolMap
- **Type**: Tool Registry
- **Status**: [REAL] - Production Ready
- **Version**: v2.0
- **File**: system/tools/ClaudeCodeToolMap.md
- **Capabilities**: Native Claude Code tool integration mapping for all 10 tools
- **Use Cases**: Real tool execution, cost optimization, error handling, decision matrix
- **Cost**: Variable
- **Reliability**: 98%

### MemoryTraceManager
- **Type**: Tool
- **Status**: [REAL] - Production Ready
- **Version**: v2
- **File**: system/tools/MemoryTraceManager.md
- **Claude Tool Mapping**: Read, Write, Grep, Bash
- **Depends On**: SmartMemory.md
- **Capabilities**: Execution trace capture, structured logging, training data export, memory rotation, log validation
- **Use Cases**: Experience recording, training dataset creation, debugging, memory maintenance
- **Cost**: Low
- **Reliability**: 95%

### ProjectScaffoldTool
- **Type**: Tool
- **Status**: [REAL] - Production Ready
- **Version**: v1
- **File**: system/tools/ProjectScaffoldTool.md
- **Claude Tool Mapping**: Bash, Write, Read
- **Depends On**: SmartLibrary.md (for registration)
- **Capabilities**: Project directory bootstrapping, state file generation, agent template creation
- **Use Cases**: New project initialization, standard layout enforcement
- **Cost**: Low
- **Reliability**: 94%

### SkillPackageManagerTool
- **Type**: Tool
- **Status**: [REAL] - Production Ready
- **Version**: v1
- **File**: system/tools/SkillPackageManagerTool.md
- **Claude Tool Mapping**: Bash, Read, Write, Grep, Glob, WebFetch
- **Depends On**: sources.list, packages.lock, SmartLibrary.md
- **Capabilities**: Skill install/remove, source search, version tracking, on-demand skill acquisition
- **Use Cases**: Installing skills from remote repos, updating skills, searching for capabilities, package management
- **Cost**: Low-Medium (git clone + file operations)
- **Reliability**: 88%

## Component Directories (for discovery)

### components/agents/ (Root-Level Shared Agents)

Agents in `components/agents/` are shared across projects and copied to `.claude/agents/` without a project prefix.

### components/tools/ (Root-Level Shared Tools)

Tools in `components/tools/` are shared across projects.

## Integration Patterns

### Standard Agent Workflow
1. SystemAgent orchestrates task
2. QueryMemoryTool provides historical context from SmartMemory.md
3. Specialized agents (created dynamically per project) execute domain-specific work
4. Output saved to projects/[ProjectName]/output/
5. MemoryTraceManager records experience to SmartMemory.md

### Dynamic Agent Pipeline (Example)
1. SystemAgent analyzes goal and identifies required capabilities
2. Creates project-specific agents as markdown in projects/[ProjectName]/components/agents/
3. Orchestrates sequential or parallel execution
4. Specialized agents produce deliverables
5. MemoryConsolidationAgent extracts learnings to long-term memory

---

This Smart Library serves as the definitive registry for all SkillOS components, providing metadata, capabilities, dependencies, and integration patterns to support intelligent component selection and system optimization.
