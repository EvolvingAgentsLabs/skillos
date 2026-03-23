# SkillOS: Pure Markdown Operating System [POC]

> **Transform any Agents + LLM into an intelligent operating system using pure markdown**


SkillOS continue to explore how create and use AI agents and tools  defined entirely in markdown documents. No code compilation, in this first exploration, no complex APIs - just markdown that any LLM can interpret to become a powerful problem-solving system.

> This project is a evolution of [LLMos](https://github.com/EvolvingAgentsLabs/llmos) to test Skills as basic programs.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/EvolvingAgentsLabs/skillos.git
cd skillos

# Initialize the agent system
./setup_agents.sh    # Mac/Linux
# OR
powershell -ExecutionPolicy Bypass -File .\setup_agents.ps1  # Windows
```

## 🎯 Choose Your Runtime

### Option 1: SkillOS Terminal (Recommended)
**Best for:** Interactive use, the full Unix-like experience
- Classic terminal REPL with `skillos$` prompt
- Markdown output rendered beautifully in terminal
- Auto-boots SkillOS, hides Claude Code internals
- Built-in commands: `help`, `status`, `projects`, `agents`, `history`

```bash
# Launch the SkillOS terminal
./skillos.sh
# Or directly with Python
python3 skillos.py
```

Once inside the terminal:
```
skillos$ Create a tutorial on chaos theory
skillos$ Monitor tech news and generate a briefing
skillos$ help
skillos$ status
```

> **Requirements:** Python 3.11+, `rich` (auto-installed on first run), Claude Code CLI

### Option 2: Claude Code (Direct)
**Best for:** Scripting, CI/CD, single-command execution
- Powered by Claude (model determined by your Claude Code installation)
- Full tool integration
- Advanced capabilities

```bash
# Boot SkillOS
claude --dangerously-skip-permissions "boot skillos"

# Execute any goal
claude --dangerously-skip-permissions "skillos execute: 'Your goal here'"
```

### Option 3: Qwen Runtime (Lightweight)
**Best for:** Learning, development, resource-constrained environments
- Uses Qwen 3 4B model (free tier)
- Minimal resource requirements
- Self-hosted option available

```bash
# Install dependencies
pip install openai python-dotenv

# Run any goal
python qwen_runtime.py "Your goal here"

# Interactive mode
python qwen_runtime.py interactive
```

## 💡 Core Concept

SkillOS treats everything as either an **Agent** (decision maker) or **Tool** (executor), all defined in markdown:

```markdown
---
name: example-agent
description: An agent that solves problems
tools: Read, Write, WebFetch
---

# ExampleAgent
You are an expert problem solver...
```

The framework automatically:
- 🔍 Discovers available agents
- 🎯 Selects the best agent for each task
- 🔄 Delegates work between specialized agents
- 📝 Executes tools based on agent decisions

## 🛠️ What Can You Build?

SkillOS can handle any task by combining its agent ecosystem:

### Research & Analysis
```bash
"Research the latest AI developments and create a comprehensive report"
"Analyze this codebase and suggest improvements"
"Compare different approaches to solving this problem"
```

### Development
```bash
"Create a web application with user authentication"
"Build a data pipeline for processing CSV files"
"Implement a machine learning model for classification"
```

### Content Creation
```bash
"Write a technical blog post about quantum computing"
"Generate documentation for this API"
"Create a tutorial for beginners"
```

### Complex Projects
```bash
"Design and implement a complete system for invoice processing"
"Create a multi-agent research system for market analysis"
"Build a quantum algorithm for signal processing"
```

## 🏗️ Framework Architecture

```
skillos/
├── skillos.sh             # Terminal launcher (bash wrapper)
├── skillos.py             # Terminal REPL with markdown rendering
├── system/                # Core framework
│   ├── agents/            # System-level agents
│   └── tools/             # Framework tools
├── projects/              # Your projects (working directory)
│   └── [project_name]/    # Project-specific agents
├── workspace/             # Execution outputs
└── qwen_runtime.py        # Lightweight runtime
```

## 🤝 Creating Custom Agents

1. **Define your agent** in markdown:
```markdown
---
name: my-custom-agent
description: Specialized agent for my domain
tools: Read, Write, Bash
---

# MyCustomAgent
You are an expert in [domain]...
```

2. **Place in project folder**: `projects/my_project/components/agents/`

3. **Use it immediately**:
```bash
"Use my-custom-agent to solve this problem"
```

## 📚 Advanced Features

### Interactive Mode
Explore SkillOS capabilities interactively:
```bash
# Full terminal experience (Claude Code)
./skillos.sh
skillos$ help                    # Show commands
skillos$ status                  # Check workspace
skillos$ Create a calculator     # Execute any goal

# Lightweight interactive mode (Qwen)
python qwen_runtime.py interactive
> help                    # Show commands
> Create a calculator     # Execute any goal
```

### Generic Goal Execution
The runtime interprets natural language goals without hardcoded solutions:
```python
# Any text becomes an executable goal
python qwen_runtime.py "Build a REST API with authentication"
```

### Multi-Agent Collaboration
Agents automatically collaborate on complex tasks:
```
SystemAgent → Breaks down the problem
├── ResearchAgent → Gathers information
├── DesignAgent → Creates architecture
└── ImplementationAgent → Builds solution
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
# For Qwen Runtime (OpenRouter)
OPENROUTER_API_KEY=your_key_here

# For local Qwen (Ollama)
OLLAMA_HOST=http://localhost:11434
```

### Local Deployment with Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download Qwen model
ollama pull qwen:4b

# Update qwen_runtime.py base_url to localhost:11434
```

## 🌟 Why SkillOS?

- **Pure Markdown**: No code compilation, just markdown interpretation
- **Universal**: Works with any LLM that can read markdown
- **Extensible**: Add new agents and tools without modifying core
- **Transparent**: See exactly what each agent is doing
- **Powerful**: Solve complex problems through agent collaboration

## 📖 Examples

### Simple Task
```bash
python qwen_runtime.py "Create a Python script that generates passwords"
```

### Complex Project
```bash
python qwen_runtime.py "Build a complete web scraping system with scheduling, data storage, and error handling"
```

### Research Task
```bash
python qwen_runtime.py "Research quantum computing applications in medicine and create a detailed report"
```

## 🎓 Try It: Create Your First Project

Generate a complete project with a single command:

```bash
claude --dangerously-skip-permissions "skillos execute: 'Create a tutorial on chaos theory with Python examples'"
```

SkillOS automatically:
1. Creates a project directory with standard structure
2. Generates specialized agents as markdown definitions
3. Orchestrates multi-agent collaboration
4. Produces deliverables in `projects/[ProjectName]/output/`
5. Logs all interactions to memory for learning
6. Extracts reusable patterns for future projects

### Available Scenarios

Run pre-built scenarios to see SkillOS in action:

```bash
# Live web research with real tool calls
skillos execute: "Run the RealWorld_Research_Task scenario in EXECUTION MODE"

# Quantum signal processing (three-agent cognitive pipeline)
skillos execute: "Run the Project Aorta scenario"

# Code analysis pipeline
skillos execute: "Run the CodeAnalysis_Task scenario on this repository"
```

## 🤔 Getting Help

- **Documentation**: See `projects/` folder for example implementations
- **Issues**: [GitHub Issues](https://github.com/EvolvingAgentsLabs/skillos/issues)
- **Interactive Help**: Run `python qwen_runtime.py interactive` then type `help`

## 📄 License

Apache License 2.0 - see LICENSE file for details

---

*Built with ❤️ by [Evolving Agents Labs](https://evolvingagentslabs.github.io)*
