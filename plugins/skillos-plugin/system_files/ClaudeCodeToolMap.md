# Claude Code Tool Mapping for SkillOS

## Overview
This document maps SkillOS conceptual operations to actual Claude Code tools, providing clear implementation guidance for the system's core functions.

## Core Tool Inventory

### File Operations
- **Read**: Read file contents
- **Write**: Create or overwrite files
- **Edit**: Make targeted edits to existing files
- **MultiEdit**: Make multiple edits to a file atomically
- **Glob**: Find files matching patterns
- **NotebookEdit**: Edit Jupyter notebooks

### Search Operations
- **Grep**: Search file contents using regex
- **WebSearch**: Search the web
- **WebFetch**: Fetch and analyze web content

### Execution Operations
- **Bash**: Execute shell commands
- **Task**: Delegate to specialized agents
- **BashOutput**: Retrieve background process output
- **KillBash**: Terminate background processes

### IDE Integration
- **mcp__ide__getDiagnostics**: Get language diagnostics
- **mcp__ide__executeCode**: Execute code in Jupyter kernel

## SkillOS Operation Mappings

### 1. Agent Creation

**SkillOS Concept**: Create a new specialized agent

**Claude Code Implementation**:
```
Tool: Write
Path: projects/[project]/components/agents/[AgentName].md
Content:
  - YAML frontmatter (name, type, capabilities, tools)
  - System prompt defining agent behavior
```

**Example**:
```python
Write(
  file_path="projects/Project_quantum/components/agents/MathematicianAgent.md",
  content="""---
name: MathematicianAgent
type: dynamic
capabilities: [mathematical_modeling, theory_development]
tools: [Read, Write, Bash]
---

You are a MathematicianAgent specialized in...
"""
)
```

### 2. Agent Delegation

**SkillOS Concept**: Execute a task using a specialized agent

**Claude Code Implementation**:
```
Step 1: Read agent definition
Tool: Read
Path: projects/[project]/components/agents/[AgentName].md

Step 2: Delegate task
Tool: Task
Parameters:
  - subagent_type: "general-purpose" (for dynamic agents)
  - description: Brief task description
  - prompt: Full agent definition + specific task instructions
```

**Example**:
```python
# Step 1
agent_def = Read("projects/Project_quantum/components/agents/MathematicianAgent.md")

# Step 2
Task(
  subagent_type="general-purpose",
  description="Develop wave propagation theory",
  prompt=f"{agent_def}\n\nTask: Develop a mathematical framework for analyzing pressure wave echoes in arterial systems. Output your theory to output/wave_theory.md"
)
```

### 3. Memory Logging

**SkillOS Concept**: Record an interaction trace

**Claude Code Implementation**:
```
Tool: Write
Path: projects/[project]/memory/short_term/[timestamp]_[agent]_[task].md
Content: Structured log with metadata, request, and response
```

**Example**:
```python
Write(
  file_path="projects/Project_quantum/memory/short_term/20250111_143022_MathematicianAgent_wave_theory.md",
  content="""---
trace_id: 20250111_143022
timestamp: 2025-01-11T14:30:22Z
agent_name: MathematicianAgent
task: "Develop wave propagation theory"
status: completed
---

# MathematicianAgent - Wave Propagation Theory

## Request
[Full prompt sent to agent]

## Response
[Complete agent response]

## Outputs
- output/wave_theory.md
"""
)
```

### 4. Memory Consolidation

**SkillOS Concept**: Extract learnings from project traces

**Claude Code Implementation**:
```
Tool: Task (MemoryConsolidationAgent)
Parameters:
  - subagent_type: "MemoryConsolidationAgent" (core agent)
  - description: "Consolidate project learnings"
  - prompt: Task details and short_term memory location
```

**Example**:
```python
Task(
  subagent_type="general-purpose",
  description="Consolidate project learnings",
  prompt="""You are the MemoryConsolidationAgent.

Analyze all memory traces in:
projects/Project_quantum/memory/short_term/

Generate consolidated learnings in:
projects/Project_quantum/memory/long_term/project_learnings.md

Follow the learning format specified in system_files/SmartMemory.md"""
)
```

### 5. Memory Querying

**SkillOS Concept**: Search long-term memory for relevant patterns

**Claude Code Implementation**:
```
Step 1: Find relevant files
Tool: Glob
Pattern: projects/*/memory/long_term/**/*.md

Step 2: Search for keywords
Tool: Grep
Pattern: [relevant keywords]
Path: [paths from Glob]

Step 3: Read matching files
Tool: Read
Path: [paths from Grep results]

Step 4: Synthesize results
```

**Example**:
```python
# Step 1
memory_files = Glob(pattern="projects/*/memory/long_term/**/*.md")

# Step 2
matches = Grep(
  pattern="mathematical.*agent|theory.*development",
  path="projects/",
  output_mode="files_with_matches"
)

# Step 3
for match in matches:
  content = Read(match)
  # Analyze content

# Step 4: Synthesize and return relevant templates
```

### 6. Project Structure Creation

**SkillOS Concept**: Initialize a new project workspace

**Claude Code Implementation**:
```
Tool: Bash (mkdir)
Alternative: Multiple Write operations with empty content
```

**Example**:
```bash
mkdir -p projects/Project_quantum/{components/agents,output,memory/{short_term,long_term}}
```

Or using Write:
```python
Write("projects/Project_quantum/components/agents/.gitkeep", "")
Write("projects/Project_quantum/output/.gitkeep", "")
Write("projects/Project_quantum/memory/short_term/.gitkeep", "")
Write("projects/Project_quantum/memory/long_term/.gitkeep", "")
```

### 7. File Discovery

**SkillOS Concept**: Find agents, outputs, or memory traces

**Claude Code Implementation**:
```
Tool: Glob
Patterns:
  - Agents: "projects/[project]/components/agents/*.md"
  - Outputs: "projects/[project]/output/*"
  - Short-term memory: "projects/[project]/memory/short_term/*.md"
  - Long-term memory: "projects/[project]/memory/long_term/**/*.md"
```

### 8. Content Search

**SkillOS Concept**: Search within memory traces or outputs

**Claude Code Implementation**:
```
Tool: Grep
Parameters:
  - pattern: Search regex
  - path: Directory to search
  - output_mode: "content" (with context) or "files_with_matches"
  - -i: Case insensitive (optional)
```

### 9. Code Execution

**SkillOS Concept**: Run tests, build code, or execute generated programs

**Claude Code Implementation**:
```
Tool: Bash
Command: [language-specific execution command]
```

**Examples**:
```bash
# Python
python output/quantum_circuit.py

# Qiskit
python -m pytest output/test_circuit.py

# Jupyter
jupyter nbconvert --execute output/analysis.ipynb
```

### 10. Validation

**SkillOS Concept**: Verify outputs and check for errors

**Claude Code Implementation**:
```
Tool: Read (for output inspection)
Tool: Bash (for test execution)
Tool: mcp__ide__getDiagnostics (for code validation)
```

## Tool Usage Guidelines

### Prefer Tool Batching
When multiple independent operations are needed, batch tool calls:

```python
# Good: Parallel execution
Read("agent1.md")
Read("agent2.md")
Read("agent3.md")

# Avoid: Sequential waiting
Read("agent1.md")
# wait
Read("agent2.md")
# wait
Read("agent3.md")
```

### Use Appropriate Search Tools
- **Glob**: For file pattern matching (names, extensions)
- **Grep**: For content search (code patterns, keywords)
- **Task**: For complex, multi-step searches requiring reasoning

### Leverage Specialized Agents
- **Core agents**: Invoke by name (e.g., MemoryAnalysisAgent)
- **Dynamic agents**: Read definition, then delegate with Task + prompt
- **General tasks**: Use Task with general-purpose subagent

### Handle Paths Correctly
- Always use absolute paths from working directory
- Use consistent path separators (/)
- Verify parent directories exist before writing

### Manage Long-Running Operations
- Use Bash with timeout for quick commands
- Use run_in_background for long-running processes
- Monitor with BashOutput and KillBash as needed

## Common Patterns

### Pattern: Agent Creation + Delegation
```python
# Create agent
Write("projects/Proj/components/agents/MyAgent.md", agent_spec)

# Delegate task
agent_def = Read("projects/Proj/components/agents/MyAgent.md")
Task(subagent_type="general-purpose", prompt=f"{agent_def}\n\nTask: ...", description="...")

# Log interaction
Write("projects/Proj/memory/short_term/[timestamp]_MyAgent_task.md", log_content)
```

### Pattern: Memory Query + Template Reuse
```python
# Search for templates
relevant_files = Grep(pattern="agent.*template", path="projects/", output_mode="files_with_matches")

# Read best match
template = Read(relevant_files[0])

# Adapt template
new_agent = adapt_template(template, current_needs)

# Create new agent
Write("projects/Proj/components/agents/AdaptedAgent.md", new_agent)
```

### Pattern: Project Initialization
```python
# Create structure
Bash("mkdir -p projects/Proj/{components/agents,output,memory/{short_term,long_term}}")

# Create core agents for project
Write("projects/Proj/components/agents/Agent1.md", agent1_spec)
Write("projects/Proj/components/agents/Agent2.md", agent2_spec)

# Initialize memory
Write("projects/Proj/memory/short_term/.gitkeep", "")
Write("projects/Proj/memory/long_term/.gitkeep", "")
```

## Tool Limitations

### Write Tool
- Cannot create files in non-existent directories (create dirs first with Bash)
- Overwrites existing files completely (use Edit for partial changes)

### Task Tool
- Cannot receive follow-up messages (one-shot delegation)
- Results returned only at completion (no streaming)

### Grep Tool
- Single-line patterns by default (use multiline: true for cross-line patterns)
- Returns truncated results for very large matches

### Bash Tool
- 2-minute default timeout (specify longer for big operations)
- No interactive input support (avoid tools like git rebase -i)

## Best Practices

1. **Read before Edit**: Always Read files before editing them
2. **Verify before Write**: Check parent directories exist
3. **Batch when possible**: Parallel tool calls for independent operations
4. **Log immediately**: Write traces right after agent interactions
5. **Use typed paths**: Absolute paths from working directory
6. **Handle errors**: Check tool results and implement fallbacks
7. **Prefer specialization**: Use Grep over Bash grep, Read over Bash cat

## Future Tool Extensions

As Claude Code evolves, SkillOS may leverage:
- Native memory/knowledge base tools
- Built-in agent delegation APIs
- Structured data storage tools
- Real-time collaboration tools
- Visual workflow builders

This mapping will be updated as new tools become available.
