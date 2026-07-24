# SkillOS Kernel Plugin for Claude Code

This plugin installs the core kernel of the **SkillOS "Pure Markdown Operating System"** into Claude Code. It does not contain pre-built solutions; it provides the factory to build them.

The kernel is powered by a single command, `/skillos`, which enables Claude to solve complex goals by **dynamically creating and orchestrating a team of specialized agents on the fly.**

## Overview

SkillOS represents a paradigm shift in how AI systems solve complex problems. Rather than shipping pre-built agents for specific domains, SkillOS provides a **self-evolving kernel** that:

- **Creates agents on demand** tailored to your specific problem
- **Learns from every execution** by capturing and consolidating patterns
- **Evolves continuously** by reusing successful strategies from past projects
- **Operates purely through markdown** using Claude Code's native capabilities

Think of it as an operating system where the "programs" (specialized agents) are written at runtime based on the task at hand, rather than installed in advance.

## Core Components

This plugin provides the essential "daemons" and system files for the SkillOS:

### Core System Agents

-   **SystemAgent**: High-level orchestrator responsible for agent lifecycle management, task decomposition, and workflow coordination
-   **MemoryAnalysisAgent**: Captures and logs all system activities in structured memory traces
-   **MemoryConsolidationAgent**: Extracts learnings from execution logs and generates reusable patterns

### System Specifications

-   **SmartMemory.md**: Defines the hierarchical memory architecture (short-term logs, long-term learnings)
-   **QueryMemoryTool.md**: Specifies how to search and retrieve knowledge from past projects
-   **MemoryTraceManager.md**: Documents the lifecycle and relationships of memory traces
-   **ClaudeCodeToolMap.md**: Maps SkillOS conceptual operations to Claude Code's actual tools

### Master Command

-   **/skillos**: The kernel shell that analyzes goals, creates specialized agents, orchestrates execution, and consolidates learnings

## Installation

### Install from Marketplace

```bash
/plugin marketplace add evolving-agents-labs/skillos_plugin
/plugin install skillos-plugin
```

### Install from Local Directory

```bash
/plugin install /path/to/skillos_plugin/skillos-plugin
```

### Verify Installation

```bash
/skillos --help
```

## Usage

```bash
/skillos "Your ambitious goal here"
```

## License

Apache License 2.0 - See [LICENSE](../LICENSE) for details.
