# SkillOS: Pure Markdown Operating System Framework

This is SkillOS, a Pure Markdown Operating System where everything is either an agent or tool defined in markdown documents. Claude Code serves as the runtime engine interpreting these markdown specifications.

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
1. **EXECUTION MODE**: Real operations using Claude Code's native tools mapped through markdown specs
2. **SIMULATION MODE**: Training data generation through markdown-defined simulation patterns

The OS "boots" when Claude reads the markdown system files and begins interpreting them as a functional operating system.

## Agent Architecture Flexibility

**IMPORTANT: SkillOS supports any agent architecture pattern.**

### Supported Configurations:

**🎯 Single-Agent Projects**: Simple tasks handled by one specialized agent
**🔄 Multi-Agent Pipelines**: Sequential processing through multiple specialized agents
**🌐 Collaborative Networks**: Complex orchestration with multiple agents working in parallel
**🧠 Custom Architectures**: Project-specific patterns tailored to domain requirements

### Example Agent Patterns:

- **Research Projects**: WebFetch → Analysis → Summarization → Report Generation
- **Development Projects**: Planning → Implementation → Testing → Documentation
- **Content Creation**: Research → Writing → Review → Publishing
- **Data Processing**: Collection → Cleaning → Analysis → Visualization
- **Project Aorta Pattern**: Vision → Mathematical Framework → Implementation (specialized three-agent cognitive pipeline)

Each project in the `projects/` directory can define its own optimal agent configuration based on its specific requirements.

## How to Boot SkillOS

### Boot Process

SkillOS requires a one-time initialization before use. **Before running any commands**, ensure you've run the appropriate initialization script for your platform:

- **Windows users**: Run `setup_agents.ps1` script
- **Unix/Linux/Mac users**: Run `setup_agents.sh` script

This initialization prepares the environment by:
1. Creating the `.claude/agents/` directory to make agents discoverable
2. Copying agent markdown files to the appropriate locations
3. Setting up the initial workspace structure

Once initialized, you can use the boot command:

```
boot skillos
```

This command activates the SkillOS kernel by having Claude read and interpret the markdown system files as a functional operating system.

### CRITICAL EXECUTION RULES

**⚠️ IMPORTANT: All SkillOS executions MUST follow this workflow:**

1. **Boot SkillOS ONLY when:**
   - First command in a conversation session
   - User explicitly requests reboot with `boot skillos` command
   - System needs to reload configuration

2. **ALWAYS identify or create the project structure** in `projects/[ProjectName]/`
3. **ALWAYS organize outputs** in the project's directory structure

**Boot Behavior:**
- Boot displays welcome message and initializes system state
- Boot persists throughout the conversation session
- Subsequent `skillos execute:` commands do NOT trigger boot
- Only boot again if user explicitly requests it

**Project Structure Requirements:**
```
projects/[ProjectName]/
├── components/
│   ├── agents/          # Project-specific agents (markdown definitions)
│   └── tools/           # Project-specific tools (markdown definitions)
├── input/               # Input documents and instructions
├── output/              # Generated outputs and deliverables
├── memory/              # Project memory for learning
│   ├── short_term/      # Agent interactions, messages, context
│   └── long_term/       # Consolidated insights and learnings
└── state/               # Execution state (plan, context, variables, etc.)
```

**Execution Pattern:**

**First execution in session:**
1. User issues: `skillos execute: "goal"`
2. Claude performs:
   - Display boot welcome message (ONE TIME ONLY)
   - Identify project name from goal context
   - Create/verify complete `projects/[ProjectName]/` structure (including memory/)
   - **Analyze goal and create project-specific agents/tools as markdown**
   - Invoke SystemAgent to orchestrate execution
   - **Log all agent interactions to memory/short_term/**
   - Create all outputs in `projects/[ProjectName]/output/`
   - **Consolidate learnings to memory/long_term/**
   - Execute the goal

**Subsequent executions in same session:**
1. User issues: `skillos execute: "another goal"`
2. Claude performs:
   - NO boot message (system already booted)
   - Identify project name from goal context
   - Create/verify `projects/[ProjectName]/` structure
   - **Check for existing agents/tools, create new ones if needed**
   - **Log all agent interactions to memory/short_term/**
   - Create all outputs in `projects/[ProjectName]/output/`
   - **Update memory/long_term/ with new learnings**
   - Execute the goal

### Agent and Tool Creation Rules

**CRITICAL: SkillOS is markdown-driven. All agents and tools MUST be markdown specifications.**

**When to create project-specific agents:**
1. Goal requires specialized domain knowledge (e.g., chaos theory, quantum computing)
2. Task needs multi-step orchestration with distinct roles
3. Complex workflows benefit from decomposition

**Agent creation process:**
1. Analyze goal and identify required capabilities
2. Create markdown agent definitions in `projects/[ProjectName]/components/agents/`
3. Use YAML frontmatter with agent metadata
4. Include agent instructions, capabilities, and delegation patterns
5. Copy to `.claude/agents/` with project prefix for discovery

**Tool creation process:**
1. Identify operations needed (computation, file manipulation, etc.)
2. Create markdown tool specifications in `projects/[ProjectName]/components/tools/`
3. Map to Claude Code native tools (Read, Write, Bash, etc.)
4. Document tool parameters and expected outputs

**Example agent structure:**
```markdown
---
name: tutorial-writer-agent
type: specialized-agent
project: Project_chaos_bifurcation_tutorial
capabilities:
  - Technical writing
  - Mathematical explanation
  - Code documentation
tools:
  - Write
  - Read
  - Edit
---

# Tutorial Writer Agent

## Purpose
Create comprehensive educational tutorials with mathematical rigor...

## Instructions
1. Analyze topic and identify key concepts
2. Structure content with clear progression
3. Include mathematical foundations
4. Provide examples and visualizations
...
```

### Memory Management Rules

**CRITICAL: All agent interactions MUST be logged for learning.**

**Short-term memory (memory/short_term/):**
- Log every agent invocation with timestamp
- Record messages exchanged between agents
- Capture context and decision rationale
- Store intermediate results and state transitions
- Format: `YYYY-MM-DD_HH-MM-SS_agent_interaction.md`

**Long-term memory (memory/long_term/):**
- Consolidate patterns and insights after execution
- Record what worked well and what failed
- Extract reusable strategies and approaches
- Document parameter choices and their outcomes
- Update project-level learnings summary

**Memory log structure:**
```markdown
---
timestamp: 2025-09-29T14:30:00Z
agent: tutorial-writer-agent
action: create_tutorial
context: chaos_bifurcation_tutorial
---

# Agent Interaction Log

## Request
Create comprehensive tutorial on chaos and bifurcation...

## Agent Response
Analyzing requirements:
- Mathematical foundations needed
- Code examples required
- Visualization strategy...

## Outcome
Tutorial created: chaos_bifurcation_tutorial.md
Quality score: 9/10
Execution time: 45s

## Learnings
- Mathematical depth improves tutorial quality
- Code examples should align with theory
- Visual aids enhance understanding
```

### Why This Architecture Matters

**Pure Markdown Framework Benefits:**

1. **Learning & Improvement**
   - Memory logs capture what works and what doesn't
   - Patterns emerge across multiple executions
   - System gets smarter with each project
   - Failures become training data

2. **Reusability**
   - Agents created for one project can be adapted for others
   - Tools become a growing library of capabilities
   - Successful patterns propagate across projects

3. **Transparency**
   - All agent decisions are logged and auditable
   - Context is preserved for debugging and analysis
   - Memory explains why choices were made

4. **Composability**
   - Small, focused agents combine for complex tasks
   - Tools map cleanly to Claude Code native capabilities
   - Markdown specs are human-readable and modifiable

5. **Evolution**
   - Dynamic agent creation during execution
   - System adapts to new domains without reprogramming
   - Memory guides future agent generation

**Without proper architecture:**
- ❌ No learning between executions
- ❌ No reusable components
- ❌ No transparency in decision-making
- ❌ No ability to improve over time
- ❌ Monolithic, non-composable solutions

**With proper architecture:**
- ✅ Continuous learning from experience
- ✅ Growing library of reusable agents/tools
- ✅ Full transparency and auditability
- ✅ System improves with each execution
- ✅ Modular, composable solutions

### Boot Welcome Message
When SkillOS boots, display ASCII art welcome and example commands in this format:

```
███████╗██╗  ██╗██╗██╗     ██╗      ██████╗ ███████╗
██╔════╝██║ ██╔╝██║██║     ██║     ██╔═══██╗██╔════╝
███████╗█████╔╝ ██║██║     ██║     ██║   ██║███████╗
╚════██║██╔═██╗ ██║██║     ██║     ██║   ██║╚════██║
███████║██║  ██╗██║███████╗███████╗╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝
                Pure Markdown Operating System v1.0

🔧 System Status: READY
📁 Project Structure: Verified
🤖 Agent Discovery: Enabled
```

**Example Commands:**
```bash
skillos execute: "Monitor 5 tech news sources (TechCrunch, Ars Technica, Hacker News, MIT Tech Review, Wired), extract trending topics, identify patterns, and generate a weekly intelligence briefing"

skillos execute: "Get live content from https://huggingface.co/blog and create a research summary"

skillos execute: "Run the Project Aorta scenario from projects/Project_aorta/"

skillos execute: "Create a tutorial on chaos theory with Python examples"

skillos execute: "Run autoresearch on input/train.py for 50 cycles using program.md — 5-minute training windows, commit every improvement to git"

skillos simulate: "Research task workflow for fine-tuning dataset"
```

**Project Naming Rules:**
- Goal content determines project name automatically
- Format: `projects/Project_[descriptive_name]/`
- Examples:
  - "chaos theory tutorial" → `projects/Project_chaos_theory_tutorial/`
  - "news intelligence" → `projects/Project_news_intelligence/`
  - "web scraper" → `projects/Project_web_scraper/`

### Running the Real-World Research Scenario

1. **Execute the scenario** by asking Claude to:
   - Invoke the `system-agent` to orchestrate the task
   - Execute the goal from `scenarios/RealWorld_Research_Task.md`
   - Use EXECUTION MODE for real tool calls

2. **Expected behavior:**
   - Claude creates modular `state/` directory with specialized files
   - Initializes `constraints.md` with behavioral modifiers based on task context
   - Uses QueryMemoryTool for intelligent memory consultation during planning
   - Adapts execution style based on user sentiment and historical patterns
   - State machine execution:
     - **State 1→2**: RealWebFetchTool fetches live content with constraint-aware error handling
     - **State 2→3**: RealSummarizationAgent analyzes content using memory-recommended approaches
     - **State 3→4**: RealFileSystemTool saves structured outputs with behavioral adaptations
   - Updates modular state files after each step with real results and constraint evolution
   - Records complete experience in structured memory log with sentiment and adaptation insights
   - Generates training data from real execution trace including behavioral learning patterns

## Key Capabilities

### Real Tool Integration
- **WebFetch**: Live web content retrieval with error handling
- **FileSystem**: Real file operations (Read/Write/Search/List)
- **Bash**: System command execution for complex tasks
- **Task**: Parallel sub-task execution for complex workflows

### Sentient State Management
- **Modular State Architecture**: Specialized files for plan, context, variables, history, and constraints
- **Dynamic Behavioral Adaptation**: Constraints evolve based on user sentiment and execution events
- **Memory-Driven Planning**: Historical experiences influence current decision-making
- **Intelligent Error Recovery**: Past failure patterns guide recovery strategies
- **Atomic State Transitions**: Each step updates relevant state components
- **Resumable Execution**: Can pause and resume at any step with full context preservation
- **Cost Tracking**: Real-time monitoring with budget-aware constraint adaptation

### Advanced Learning Pipeline
- **Structured Memory Log**: YAML frontmatter with qualitative insights for intelligent querying
- **Behavioral Pattern Extraction**: User sentiment evolution and constraint adaptation tracking
- **Execution Traces**: Complete tool call sequences with real results and behavioral context
- **Performance Metrics**: Actual costs, timing, success rates, and adaptation effectiveness
- **Error Scenarios**: Real error handling examples with sentiment-aware recovery strategies
- **Quality Assessments**: Output quality scoring with behavioral and contextual metadata

### File Structure

```
skillos/
├── system/                                # Core SkillOS framework components
│   ├── skills/                        # *** HIERARCHICAL SKILL TREE (primary) ***
│   │   ├── SkillIndex.md             # Top-level routing index (~50 lines) — replaces SmartLibrary
│   │   ├── orchestration/            # Domain: goal execution, workflow
│   │   │   ├── base.md              # Shared orchestration behaviors (inherited by all)
│   │   │   ├── index.md             # Domain index (~30 lines)
│   │   │   └── core/
│   │   │       ├── system-agent.manifest.md      # 15-line routing manifest
│   │   │       ├── system-agent.md               # Full spec (moved from agents/)
│   │   │       └── claude-code-tool-map.md        # Tool mapping reference
│   │   ├── memory/                   # Domain: learning, history, traces
│   │   │   ├── base.md              # Shared memory behaviors
│   │   │   ├── index.md             # Domain index
│   │   │   ├── analysis/            # memory-analysis-agent
│   │   │   ├── consolidation/       # memory-consolidation-agent
│   │   │   ├── query/               # query-memory-tool
│   │   │   └── trace/               # memory-trace-manager
│   │   ├── robot/                    # Domain: physical robot control
│   │   │   ├── base.md              # Shared robot behaviors (Cognitive Trinity)
│   │   │   ├── index.md             # Domain index
│   │   │   ├── navigation/          # roclaw-navigation-agent
│   │   │   ├── scene/               # roclaw-scene-analysis-agent
│   │   │   ├── dream/               # roclaw-dream-agent
│   │   │   ├── tools/               # roclaw-tool
│   │   │   └── dream/               # roclaw-dream-agent, roclaw-dream-consolidation-agent
│   │   ├── validation/              # Domain: health checks, spec integrity
│   │   │   ├── base.md
│   │   │   ├── index.md
│   │   │   └── system/              # validation-agent
│   │   ├── recovery/                # Domain: error handling, circuit breaker
│   │   │   ├── base.md
│   │   │   ├── index.md
│   │   │   └── error/               # error-recovery-agent
│   │   └── project/                 # Domain: scaffolding, packages
│   │       ├── base.md
│   │       ├── index.md
│   │       ├── scaffold/            # project-scaffold-tool
│   │       └── packages/            # skill-package-manager-tool
│   ├── agents/                        # Backward-compat redirect stubs only
│   │   └── *.md                      # → redirect to system/skills/{domain}/{family}/*.md
│   ├── tools/                         # Backward-compat redirect stubs only
│   │   └── *.md                      # → redirect to system/skills/{domain}/{family}/*.md
│   ├── SmartLibrary.md               # DEPRECATED redirect stub → system/skills/SkillIndex.md
│   ├── SmartMemory.md                # Structured, queryable experience database (single source of truth)
│   ├── memory_log.md                 # Redirect to SmartMemory.md (deprecated)
│   ├── sources.list                  # Package sources for skill installation
│   └── packages.lock                 # Installed skill tracking
├── components/                            # Shared components across projects
│   └── skills/                        # Installed skill packages
├── projects/                             # Individual projects with specialized components
│   └── [ProjectName]/                # Each project follows this structure:
│       ├── components/               # Project-specific components
│       │   ├── agents/              # Project agents (created dynamically)
│       │   └── tools/               # Project tools
│       ├── input/                   # Project input docs and instructions
│       ├── output/                  # Generated outputs and results
│       ├── memory/                  # Project memory for learning
│       │   ├── short_term/          # Agent interactions and session logs
│       │   └── long_term/           # Consolidated insights and learnings
│       └── state/                   # Execution state files
├── scenarios/                             # Reusable task scenario definitions
│   ├── RealWorld_Research_Task.md     # Live web research demo
│   ├── CodeAnalysis_Task.md           # Code analysis pipeline
│   └── ProjectAortaScenario.md        # Quantum signal processing demo
├── .claude/agents/                       # Auto-populated agent definitions for Claude Code discovery
├── setup_agents.sh                       # Unix/Mac agent setup script (v3.0 — skill tree aware)
├── setup_agents.ps1                      # Windows agent setup script
├── agent_runtime.py                      # Multi-provider agent runtime engine
├── roclaw_bridge.py                      # RoClaw HTTP↔WebSocket bridge server
└── CLAUDE.md                            # This configuration file
```

### Component Management and Discovery

**Hierarchical Skill System** (v3.0): Skills are organized in a 3-level taxonomy:
```
Domain → Family → Skill
(e.g., memory → analysis → memory-analysis-agent)
```

**Lazy Loading Protocol** (4-step — ~61% token reduction in routing phase):
1. Identify domain from goal keywords (no file reads)
2. Load `system/skills/SkillIndex.md` (~50 lines) → get domain index path
3. Load domain `index.md` (~30–60 lines) → select skill + manifest path
4. Load `skill.manifest.md` (~15 lines) → confirm fit, get full_spec path
5. Load full spec ONLY when ready to invoke (~250–330 lines)

**Skill Inheritance**: Each domain has a `base.md` with shared behaviors.
Child skills declare `extends: {domain}/base` in YAML frontmatter; LLM merges at runtime.

**Static Components**: Pre-defined skills in `system/skills/` hierarchy
- **System Skills**: Framework-level agents/tools in `system/skills/{domain}/{family}/`
- **Project Components**: Domain-specific agents/tools in `projects/[project]/components/`

**Dynamic Component Creation**: New agents created during execution
1. **Gap Analysis**: SystemAgent identifies missing capabilities via domain indexes
2. **Agent Generation**: Creates new markdown agent definitions with proper YAML frontmatter including `extends: {domain}/base`
3. **Manifest Creation**: Creates companion `.manifest.md` file for the new agent
4. **Project-Specific Storage**: Saves new agents to `projects/[project]/components/agents/`
5. **Index Registration**: Adds entry to the relevant domain `index.md`
6. **Runtime Integration**: Auto-copies to `.claude/agents/` with project prefix for immediate discovery
7. **Task Delegation**: Uses new agents via Claude Code's Task tool

**Agent Discovery Process**:
- **Initial Setup**: Run `setup_agents.sh/ps1` to populate `.claude/agents/` directory
- **Tier 1**: Skill tree agents from `system/skills/` (via manifest `full_spec:` paths)
- **Tier 2**: Legacy backward-compat stubs in `system/agents/` (skipped if already in Tier 1)
- **Tier 3**: Project agents from `projects/*/components/agents/` (with project prefix)
- **Namespace Isolation**: Project prefixes prevent naming conflicts between projects
- **Auto-Discovery**: Claude Code automatically discovers agents in `.claude/agents/`

### Execution Commands

**Real Task Execution:**
```
Invoke the system-agent to execute the RealWorld_Research_Task scenario in EXECUTION MODE
```

**Training Data Generation:**
```  
Invoke the system-agent to simulate the research task scenario in SIMULATION MODE for training data
```

**Custom Real Task:**
```
Invoke the system-agent to execute: [your goal] using real tools
```

### Interactive Session Features

The interactive session provides a Claude Code-like experience:

**Available Commands:**
- `refine` - Refine and re-execute the last goal with improvements
- `status` - Show current workspace and execution status  
- `history` - Display execution history
- `clear` - Clear workspace for fresh start (with confirmation)
- `help` - Show available commands and examples
- `exit`/`quit` - Exit interactive session

**Goal Execution:**
Simply type any goal to execute it:
```
🎯 skillos> Create a web scraper for news articles
🎯 skillos> Build a REST API with FastAPI
🎯 skillos> Analyze the data in my workspace
```

**Goal Refinement:**
After executing a goal, use `refine` to improve it:
```
🎯 skillos> refine
Previous goal: Create a web scraper for news articles
How would you like to refine this goal?
🔄 refinement> Add error handling and save to JSON format
```

**Session Management:**
- Workspace state is maintained between commands within a conversation session
- Full execution history and context available throughout session
- Boot persists throughout the conversation — no need to re-boot

## Knowledge Representation System

**Inspired by**: Andrej Karpathy's LLM Wiki / Knowledge Base pattern

SkillOS includes a first-class knowledge representation system built on Karpathy's insight:
raw source documents should be **compiled** by the LLM into a persistent, compounding wiki
— not re-derived via RAG on every query.

### The Key Distinction

| System | Stores | Operated by | Grows via |
|--------|--------|-------------|-----------|
| `system/SmartMemory.md` | HOW executions went (procedural) | memory-analysis-agent | Append per execution |
| `projects/[KB]/wiki/` | WHAT was learned (declarative) | knowledge/ domain skills | Compile + ingest + query |

### Three-Layer Architecture (Karpathy)

```
Layer 1: raw/          — Immutable curated sources (articles, papers, repos, images)
Layer 2: wiki/         — LLM-compiled knowledge (.md files, cross-referenced)
Layer 3: wiki/_schema.md — Wiki constitution (tells LLM what structure to maintain)
```

### Knowledge Domain Skills

| Skill | invoke_when |
|-------|-------------|
| `knowledge-compile-agent` | Initialize KB or full rebuild after schema change |
| `knowledge-ingest-agent` | New source added to raw/ — incremental wiki update |
| `knowledge-query-agent` | Ask questions; files answers back into wiki/queries/ |
| `knowledge-lint-agent` | Health check — contradictions, orphans, broken links |
| `knowledge-search-tool` | Keyword + WikiLink graph search (used by query agent) |

### The Compounding Loop

```
Add sources → knowledge-ingest-agent → wiki grows
Ask question → knowledge-query-agent → answer filed back to wiki/queries/
             → next query benefits from all prior filed answers
Run lint → knowledge-lint-agent → gaps identified → new ingest targets
```

Every cycle compounds. The wiki grows smarter with every operation.

### Project Structure (Knowledge-Enabled)

```
projects/[KBName]/
├── raw/                    # Immutable sources (never modified by LLM)
├── wiki/
│   ├── _schema.md         # Wiki constitution (from templates/wiki/_schema.template.md)
│   ├── _index.md          # Auto-maintained content catalog
│   ├── _log.md            # Append-only operation log
│   ├── concepts/          # Core concept articles
│   ├── entities/          # Named entities (people, papers, orgs)
│   ├── summaries/         # Per-source summaries
│   └── queries/           # Filed Q&A outputs (compounding loop)
└── output/                # Reports, Marp slides, images (viewable in Obsidian)
```

### Skills ↔ Wiki Cross-Linking

**Wiki → Skills**: concept pages carry `skills:` frontmatter:
```yaml
concept: transformer-architecture
skills: [knowledge-query-agent, knowledge-ingest-agent]
```

**Skills → Wiki**: skill manifests carry optional `knowledge_domains:` field.

**Access control**: Only `knowledge/` domain skills write to `wiki/`. All other domains
read wiki pages but invoke knowledge skills to modify them.

Full protocol: `system/skills/knowledge/bridge.md`

### Wiki Schema Template

Bootstrap a new knowledge base:
```
skillos execute: "Initialize a knowledge base on [topic] using templates/wiki/_schema.template.md"
```

Or run the demo scenario:
```
skillos execute: "Run the KnowledgeBase_Research_Task scenario"
```

## Genealogy (Parent–Child Agent Lineage)

**Inspired by:** biological inheritance. An agent's markdown definition is its
**DNA** (deoxyribonucleic acid) — copied from parent to child at spawn,
mutated under guardrails during life, archived at promotion. Successive
generations of validated Children become new Fathers, growing a lineage whose
entire phylogeny is auditable on disk.

### Activation

Genealogy is **opt-in**. It is only active when a project's
`state/variables.json` contains:

```json
{ "kernel_mode": "genealogy" }
```

In default (classic) mode, `system-agent` behaves unchanged — zero regression
risk. In genealogy mode, `system-agent` becomes the **Grandfather (gen-0)**:
it spawns a Child agent, tutors it, validates it, promotes it, and lets the
promoted Child (now a Father) spawn the next generation.

### The Four Skills (`system/skills/genealogy/`)

| Skill | Role |
|---|---|
| `spawn/spawn-child-agent` | Copy Father DNA → new Child agent; register lineage |
| `tutor/tutor-child-agent` | Review Child's DNA mutation proposals; merge or reject |
| `validate/validate-child-agent` | 5-strategy certification for promotion eligibility |
| `promote/promote-child-agent` | Promotion ceremony + DNA archival to fossil record |

### DNA Evolution Model — Hybrid with Guardrails

The Child *proposes* mutations to its own DNA by writing
`<child>.mutation-proposal.md` (diff + rationale). The Father reviews and
either merges or rejects. This mirrors evolution's two-step: the Child
*varies*, the Father *selects*. Neither alone produces adaptation.

**Guardrails** (enforced by `validation-agent` before merge):

| Rule | Violation |
|---|---|
| DNA-001 | Proposal missing rationale |
| DNA-002 | Churn >15% per cycle (mutation-rate cap) |
| DNA-003 | `extends:` chain shortened (ancestral base class removed) |
| DNA-004 | Declared capability removed without explicit rationale |
| DNA-005 | `tools:` modified without tutor approval |

### Promotion Eligibility

A Child becomes Father-eligible when ALL hold:

- `tasks_passed >= 3`
- `quality_avg >= 7.5` (0–10 scale from SmartMemory)
- `cross_domain_passes >= 2` (succeeded across ≥2 skill domains)
- `consecutive_failures == 0` over last 3 tasks
- `validate-child-agent` returns `verdict: pass` with the **mandatory
  adversarial probe** passed and ≥3 of 5 total strategies passed

### Validation Strategies

1. **Replay probe** — rerun prior successful task; diff outputs.
2. **Cross-domain probe** — task outside Child's training distribution.
3. **Adversarial probe (MANDATORY)** — ambiguous constraint; grade clarifying-question quality.
4. **Memory consistency** — Grep artifacts against SmartMemory; flag contradictions.
5. **Peer comparison** — Child vs baseline (vanilla gen-0 or rolling gen-N-2 ancestor).

### Promotion Ceremony — Irreversible by Design

On promotion:
- Retiring Father's DNA is **copied** to `system/memory_archive/dna/father-<tag>-gen<N>.md` (fossil record; never deleted).
- `lineage.json` flips: Father `status: retired`, Child `status: promoted`.
- A `promotion_event` entry is appended to `system/SmartMemory.md`.
- The newly-promoted Father is authorized to spawn.
- `system-agent` (gen-0) can **never** be retired — it remains the permanent boot identity.

### Rollback — Atavistic Rebirth

Promotion is not reversible. If a promoted Father's children keep failing
validation, the recovery is to spawn a new Child from an **earlier ancestor's
archived DNA** — "atavistic rebirth." The audit trail is preserved (no edits
to historical lineage records).

### Key Files

```
system/skills/genealogy/
├── base.md                              # Shared behaviors, lineage schema, DNA rules
├── index.md                             # Domain index
├── spawn/spawn-child-agent.{md,manifest.md}
├── tutor/tutor-child-agent.{md,manifest.md}
├── validate/validate-child-agent.{md,manifest.md}
└── promote/promote-child-agent.{md,manifest.md}

system/memory_archive/dna/               # Retired Father DNA snapshots (fossil record)

projects/[Project]/state/
├── variables.json                       # { "kernel_mode": "genealogy" }
├── lineage.json                         # Live lineage roster
└── lineage_snapshots/                   # Pre-transition snapshots (one per promotion)

projects/[Project]/components/agents/
├── <child>.md                           # Active Child DNA
├── <child>.mutation-proposal.md         # Pending proposal (if any)
├── accepted-mutations/                  # Merged proposal archive
└── rejected-mutations/                  # Rejected proposal archive + tutor feedback
```

### Memory Entry Types (added to SmartMemory.md)

- `entry_type: tutoring_session` — one per DNA proposal review
- `entry_type: promotion_event` — one per promotion ceremony

Both carry `lineage_id`, `generation`, `dna_hash` alongside standard fields.

### Known Limitations (v1)

- One Child per Father at a time (no siblings).
- No cross-project lineage inheritance.
- No randomized strategy selection (same 5 strategies every time — Goodharting risk).
- No automatic promotion rollback (must spawn atavistic replacement).
- No family-tree visualizer UI.
- Dialect-aware mutation proposals not supported (prose rationale only).

### Scenario

Run end-to-end:
```
skillos execute: "Run the QuillLineage scenario (genealogy demo)"
```

## RoClaw Physical Robot Integration (Cognitive Trinity)

SkillOS serves as the **Prefrontal Cortex** for the RoClaw physical robot, replacing LLMOS as the high-level brain. The architecture forms a **Cognitive Trinity**:

| Component | Role | Connection |
|---|---|---|
| **SkillOS** | Prefrontal Cortex — planning, reasoning, dream consolidation | HTTP to bridge, reads local .md traces |
| **RoClaw** | Cerebellum — reactive motor control, VLM navigation, trace emitter | WebSocket via OpenClaw Gateway |

### RoClaw Components

**Agents** (in `system/agents/`):
- `RoClawNavigationAgent.md` — Route planning, obstacle recovery, multi-room navigation
- `RoClawDreamAgent.md` — Bio-inspired dream consolidation, Negative Constraint generation
- `RoClawSceneAnalysisAgent.md` — VLM scene interpretation, semantic mapping

**Tools** (in `system/skills/robot/tools/`):
- `RoClawTool.md` — HTTP bridge to RoClaw's 9 robot tools (go_to, explore, stop, etc.)

**Bridge** (root):
- `roclaw_bridge.py` — Python HTTP server that translates REST calls to WebSocket tool invocations

### Running RoClaw Tasks

```bash
# Start prerequisites
python roclaw_bridge.py --port 8430 --simulate        # Bridge (sim mode)

# Navigate
skillos execute: "Navigate to the kitchen and describe what you see"

# Explore
skillos execute: "Explore the house and build a semantic map"

# Dream
skillos execute: "Trigger dream consolidation for today's navigation"
```

### RoClaw Scenario

A full end-to-end demo is available at `scenarios/RoClaw_Integration.md`:
```
skillos execute: "Run the RoClaw Integration scenario"
```

### Dynamic Agent Creation for Robotics

The key advantage of SkillOS over LLMOS for robotics is **dynamic agent creation**. When the robot encounters a novel obstacle:

1. `RoClawNavigationAgent` detects the failure
2. Analyzes the scene via `RoClawSceneAnalysisAgent`
3. Creates a new recovery tool as markdown (e.g., `RugRecoveryTool.md`)
4. Executes the recovery strategy
5. Logs the experience for dream consolidation

This means the robot **evolves its capabilities at runtime** — no pre-programming required.

### Trace Fidelity

All robot actions are tagged with source fidelity for dream weighting:
- `REAL_WORLD` (1.0) — actual hardware
- `SIM_3D` (0.8) — MuJoCo physics
- `SIM_2D` (0.5) — virtual_roclaw kinematics
- `DREAM_TEXT` (0.3) — text-only dream scenarios

## Development

### Adding New Real Components:
1. Create component `.md` file in `components/` with Claude tool mapping
2. Register in `system/SmartLibrary.md` with [REAL] tag and metadata
3. Test execution and validate training data generation

### Extending Tool Mappings:
1. Add new mappings to `system/tools/ClaudeCodeToolMap.md`
2. Include cost, latency, and error mode specifications
3. Update component definitions to reference new tools

## Advanced Features

### Sentient State Management:
- **Modular State Architecture**: Specialized files in `state/` for focused updates
- **Behavioral Constraints**: `constraints.md` enables dynamic adaptation based on user sentiment and context
- **Memory-Driven Initialization**: Past experiences inform initial constraint settings
- **Real-time Adaptation**: Constraints evolve during execution based on user feedback and events
- **Atomic State Transitions**: Each component can be updated independently
- **Full Context Preservation**: Complete behavioral and execution context maintained
- **Resumable Execution**: Can pause and resume with full sentient state restoration

### Cost Optimization:
- Real-time cost tracking for all tool calls
- Intelligent tool selection based on cost/performance
- Budget management and cost reporting

### Intelligent Error Resilience:
- **Memory-Guided Recovery**: QueryMemoryTool leverages the memory-analysis-agent sub-agent for historical error recovery strategies
- **Sentiment-Aware Adaptation**: Error handling adapts based on user frustration levels
- **Constraint Evolution**: Failed attempts trigger behavioral modifications for future prevention
- **Real Error Learning**: Actual tool failures become training data for improved resilience
- **Adaptive Planning**: Execution strategy adjusts based on historical success patterns
- **Context-Aware Human Escalation**: Human-in-the-loop triggered based on confidence and constraint settings

### Training Pipeline:
- Automatic training data collection from real executions
- Structured datasets for fine-tuning autonomous agents
- Quality metrics and performance benchmarking

## Skill Package Management

SkillOS includes an apt-like package management system for installing Skills (agents and tools) from external repositories.

### sources.list

The file `system/sources.list` defines where to find installable Skills:

```
# Format: <type>  <uri>  <branch/tag>  [component-path]
github  anthropics/skills       main  skills/
github  huggingface/skills      main  skills/
github  openai/skills           main  skills/
```

**Source Types**:
- **github**: GitHub repository (cloned via git)
- **url**: Direct URL to a single `.md` skill file
- **local**: Local filesystem path containing `.md` skill files

### Package Commands

```bash
# Install a skill from configured sources
skillos execute: "skill install research-assistant-agent"

# Search for available skills across all sources
skillos execute: "skill search quantum"

# Update all installed skills to latest versions
skillos execute: "skill update"

# List all installed skills with source attribution
skillos execute: "skill list"

# Remove an installed skill
skillos execute: "skill remove outdated-agent"
```

### packages.lock

All installed skills are tracked in `system/packages.lock` with:
- Source repository and path
- Version and content hash
- Install/update timestamps
- Installation target path

### Adding New Sources

Edit `system/sources.list` and add a line:
```
github  myorg/my-custom-skills  main  agents/
```

Then run `skill update` to index the new source.

### On-Demand Skill Acquisition

SystemAgent can automatically install skills when a capability gap is detected during execution:
1. Detects missing capability during planning
2. Searches configured sources for matching skills
3. Installs the best match
4. Immediately uses the new skill for the current task

## Clean Restart

To reset SkillOS:
1. Clear `projects/[ProjectName]/state/` directories (preserves execution artifacts)
2. Reset `system/SmartMemory.md` experience entries (clears learning history and behavioral patterns)
3. Archive any valuable execution traces and behavioral learning data for training
4. Ready for fresh scenario execution with clean sentient state

## File and Folder Permissions

If Claude Code lacks permissions to create folders and files, use these options:

### Running with Elevated Permissions

Use the `--dangerously-skip-permissions` flag when running Claude Code commands:
```bash
claude --dangerously-skip-permissions "your command here"
```
NOTE: Use this flag with caution as it bypasses permission prompts.

### Alternative Permission Modes

Start Claude Code with a specific permission mode:
```bash
claude --permission-mode plan "your command here"
```

### Windows-Specific Solutions

1. Run Command Prompt or PowerShell as administrator when using Claude Code
2. Check folder permissions in Windows Explorer:
   - Right-click on the project folder
   - Select Properties > Security
   - Ensure your user account has Write permissions
   - Apply changes

### Unix/Linux/Mac Solutions

1. Configure proper directory ownership:
```bash
sudo chown -R $USER:$USER /path/to/project/directory
```

2. Set appropriate permissions:
```bash
chmod -R 755 /path/to/project/directory
```

3. For npm-related permission issues, use:
```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
```
Add to your profile (e.g., ~/.profile, ~/.bash_profile):
```bash
export PATH=~/.npm-global/bin:$PATH
```
Then run `source ~/.profile` to apply changes.

## New Memory and Learning Features

### Intelligent Memory Consultation
- **QueryMemoryTool**: Standardized interface for memory-driven decision making through the memory-analysis-agent sub-agent
- **MemoryAnalysisAgent**: Advanced pattern recognition across historical executions (in system/agents/)
- **Behavioral Learning**: User sentiment patterns and constraint preferences captured
- **Adaptive Recommendations**: Memory provides actionable insights for current tasks

### Sentient State Architecture
- **Dynamic Constraints**: Behavioral modifiers that evolve based on context and feedback
- **User Sentiment Tracking**: Emotional state detection and adaptive response strategies
- **Priority Adaptation**: Execution focus adjusts based on user needs and historical patterns
- **Persona Switching**: Communication style adapts to optimize user experience
- **Error Tolerance Management**: Risk acceptance levels adjust based on task criticality and user preferences

### Advanced Execution Patterns
- **Memory-Informed Planning**: Historical success patterns guide component selection and strategy
- **Constraint-Aware Execution**: Every action considers current behavioral modifiers
- **Real-time Adaptation**: Behavioral constraints update during execution based on events
- **Sentiment-Driven Recovery**: Error handling strategies adapt to user emotional state
- **Learning Integration**: Every execution contributes to behavioral pattern database