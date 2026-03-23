# SkillOS: Pure Markdown Operating System Framework

This is SkillOS, a Pure Markdown Operating System where everything is either an agent or tool defined in markdown documents. The LLM runtime (Claude Code, OpenCode, Gemini CLI, etc.) serves as the interpreter executing these markdown specifications.

## Framework Philosophy: Pure Markdown

**CRITICAL: SkillOS is a PURE MARKDOWN framework. Everything is either an agent or tool defined in markdown documents.**

### Core Principles:
- **Markdown-Driven Execution**: LLM interpreter reads and sends full markdown specifications to LLM for interpretation and execution
- **No Code Generation**: System behavior emerges from LLM interpreting markdown documents sent at runtime
- **Agent/Tool Duality**: Every component is either an agent (decision maker) or tool (executor) defined in markdown
- **Flexible Architecture**: Projects can define any agent configuration - single agents, multi-agent pipelines, or custom patterns
- **Real Tool Integration**: Markdown components map to actual tool execution via TOOL_CALL format
- **Sentient State Architecture**: Behavioral constraints evolve dynamically to enable adaptive decision-making
- **Memory-Driven Learning**: Historical experiences become actionable intelligence for continuous improvement
- **Dynamic Creation**: New tools/agents are created as markdown specifications during runtime
- **LLM as Interpreter**: LLM receives and interprets markdown system definitions to achieve any goal

### Operating Modes:
1. **EXECUTION MODE**: Real operations using the runtime's native tools mapped through markdown specs
2. **SIMULATION MODE**: Training data generation through markdown-defined simulation patterns

The OS "boots" when the LLM reads the markdown system files and begins interpreting them as a functional operating system.

## Project Structure

```
skillos/
├── system/                            # Core SkillOS framework components
│   ├── agents/                        # System-wide orchestration agents
│   │   ├── SystemAgent.md            # Core orchestration and workflow management
│   │   ├── MemoryAnalysisAgent.md    # Cross-project learning and pattern recognition
│   │   ├── MemoryConsolidationAgent.md # Memory log maintenance and consolidation
│   │   ├── ErrorRecoveryAgent.md     # Fault tolerance and error recovery
│   │   └── ValidationAgent.md        # System health checks and validation
│   ├── tools/                         # Framework-level tools
│   │   ├── ClaudeCodeToolMap.md      # Integration with Claude Code's native tools
│   │   ├── QueryMemoryTool.md        # Framework-level memory consultation
│   │   ├── MemoryTraceManager.md     # Execution trace capture and logging
│   │   └── ProjectScaffoldTool.md    # Project directory bootstrapping
│   ├── SmartLibrary.md               # Component registry with metadata and capabilities
│   └── SmartMemory.md                # Structured, queryable experience database
├── components/                        # Shared components across projects
│   └── skills/                        # Installed skill packages
├── projects/                          # Individual projects with specialized components
│   └── [ProjectName]/                 # Each project follows this structure:
│       ├── components/                # Project-specific components
│       │   ├── agents/               # Project agents (created dynamically)
│       │   └── tools/                # Project tools
│       ├── input/                    # Project input docs and instructions
│       ├── output/                   # Generated outputs and results
│       ├── memory/                   # Project memory for learning
│       │   ├── short_term/           # Agent interactions and session logs
│       │   └── long_term/            # Consolidated insights and learnings
│       └── state/                    # Execution state files
├── scenarios/                         # Reusable task scenario definitions
├── CLAUDE.md                          # Claude Code configuration
├── AGENTS.md                          # OpenCode configuration (this file)
├── GEMINI.md                          # Gemini CLI configuration
└── QWEN.md                           # Qwen runtime configuration
```

## How to Boot SkillOS

### Boot Command
```
skillos execute: "your goal here"
```

Or simply:
```
boot skillos
```

### Boot Process

1. Display the SkillOS welcome banner
2. Identify/create project structure in `projects/[ProjectName]/`
3. Analyze goal and create project-specific agents/tools as markdown
4. Invoke SystemAgent to orchestrate execution
5. Log all agent interactions to `memory/short_term/`
6. Create outputs in `projects/[ProjectName]/output/`
7. Consolidate learnings to `memory/long_term/`

### Execution Rules

- **First command in a session**: Boot displays welcome message and initializes
- **Subsequent commands**: NO re-boot, system is already active
- **Always** identify or create the project structure in `projects/[ProjectName]/`
- **Always** organize outputs in the project's directory structure

### Project Naming Rules
- Goal content determines project name automatically
- Format: `projects/Project_[descriptive_name]/`

## Agent Architecture

SkillOS supports any agent architecture pattern:

- **Single-Agent Projects**: Simple tasks handled by one specialized agent
- **Multi-Agent Pipelines**: Sequential processing through multiple agents
- **Collaborative Networks**: Complex orchestration with parallel agents
- **Custom Architectures**: Project-specific patterns tailored to domain requirements

### Agent and Tool Creation

When to create project-specific agents:
1. Goal requires specialized domain knowledge
2. Task needs multi-step orchestration with distinct roles
3. Complex workflows benefit from decomposition

Agents are defined as markdown files with YAML frontmatter:
```markdown
---
name: agent-name
description: What this agent does
tools:
  - Read
  - Write
  - Bash
---

# Agent Name

## Purpose
...

## Instructions
...
```

## Memory Management

### Short-term memory (`memory/short_term/`)
- Log every agent invocation with timestamp
- Record messages exchanged between agents
- Capture context and decision rationale
- Format: `YYYY-MM-DD_HH-MM-SS_agent_interaction.md`

### Long-term memory (`memory/long_term/`)
- Consolidate patterns and insights after execution
- Record what worked well and what failed
- Extract reusable strategies and approaches

## Key Capabilities

### Real Tool Integration
- **WebFetch**: Live web content retrieval with error handling
- **FileSystem**: Real file operations (Read/Write/Search/List)
- **Bash**: System command execution for complex tasks
- **Task**: Parallel sub-task execution for complex workflows

### State Management
- Modular state files in `projects/[ProjectName]/state/`
- Dynamic behavioral adaptation via `constraints.md`
- Resumable execution via checkpoint files
- Cost tracking and budget-aware execution

## Example Commands

```bash
skillos execute: "Monitor 5 tech news sources, extract trending topics, and generate a weekly intelligence briefing"
skillos execute: "Create a tutorial on chaos theory with Python examples"
skillos execute: "Get live content from https://huggingface.co/blog and create a research summary"
skillos execute: "Run autoresearch on input/train.py for 50 cycles using program.md"
```

## Clean Restart

To reset SkillOS:
1. Clear `projects/[ProjectName]/state/` directories
2. Reset `system/SmartMemory.md` experience entries
3. Archive any valuable execution traces
4. Ready for fresh scenario execution
