# SkillOS Examples

Quick-reference examples organized by complexity and agent pattern.

## Quick Start

```bash
# Boot the system first
boot skillos

# Then run any example below
skillos execute: "[your goal]"
```

---

## By Complexity

### Beginner — Single Agent, Simple Goal

```bash
# Summarize a web page
skillos execute: "Fetch https://en.wikipedia.org/wiki/Large_language_model and write a 3-paragraph summary"

# Summarize a local file
skillos execute: "Read projects/MyProject/input/notes.txt and produce a bullet-point summary"

# Generate a simple document
skillos execute: "Create a one-page project proposal for a mobile app that tracks daily water intake"

# Answer a research question
skillos execute: "Research what WebAssembly is and write a beginner-friendly explanation"

# Translate a document
skillos execute: "Read input/README_en.md and produce a Spanish translation at output/README_es.md"
```

### Intermediate — Multi-Step, Sequential Pipeline

```bash
# Research + write an article (uses ContentCreation_Task pattern)
skillos execute: "Write a research-backed blog post about the current state of vector databases"

# Analyze data (uses DataAnalysis_Task pattern)
skillos execute: "Analyze the CSV at projects/Sales/input/q3_sales.csv and highlight the top 5 trends"

# Code documentation
skillos execute: "Read all Python files in src/ and generate API documentation in Markdown"

# Changelog generation
skillos execute: "Read the git log for the last 30 commits and write a structured CHANGELOG.md"

# Competitive research
skillos execute: "Research the top 5 open-source vector databases, compare their features, and produce a comparison table"
```

### Advanced — Multi-Agent Parallel Pipelines

```bash
# Full tech intelligence briefing (uses RealWorld_Research_Task pattern)
skillos execute: "Monitor TechCrunch, Hacker News, and Ars Technica for today and generate an intelligence briefing"

# Repository audit (uses GitRepoAudit_Task pattern)
skillos execute: "Run a comprehensive security and quality audit on the current repository"

# Codebase documentation (uses CodeAnalysis_Task pattern)
skillos execute: "Analyze the codebase at /path/to/project and generate full developer documentation"

# Knowledge base from multiple sources (uses KnowledgeSynthesis_Task pattern)
skillos execute: "Build a knowledge base on LLM fine-tuning from these 6 papers: [url1..url6]"

# Quantum biomedical implementation (uses ProjectAorta pattern)
skillos execute: "Run the Project Aorta scenario for quantum homomorphic signal processing"
```

### Expert — Custom Agent Networks

```bash
# Create a custom 4-agent research pipeline for a domain
skillos execute: "Design and run a 4-agent research pipeline to produce a market analysis report on AI coding assistants"

# Adaptive content pipeline with memory
skillos execute: "Using lessons from previous research projects, create a tutorial series on distributed systems"

# Cross-project synthesis
skillos execute: "Synthesize learnings from all previous SkillOS project memory logs into a best practices guide"
```

### Autonomous — Self-Directed Feedback Loops (Karpathy-style)

```bash
# Run autoresearch on a training script (Karpathy's autoresearch pattern)
skillos execute: "Run autoresearch on input/train.py for 50 cycles using program.md — 5-minute training windows, commit every improvement to git"

# Autonomous prompt optimization
skillos execute: "Run autoresearch on system_prompt.md for 20 cycles — measure accuracy on evaluation_set.json and commit every improvement"

# Algorithm autotuning
skillos execute: "Run autoresearch on solver.py for 30 cycles to minimize benchmark runtime — follow program.md constraints"

# Resume a stopped autoresearch run
skillos execute: "Resume autoresearch from where it stopped in projects/Project_autoresearch/"
```

---

## By Use Case

### Research & Intelligence
| Goal | Pattern | Scenario |
|---|---|---|
| Tech news briefing | Parallel fetch + synthesis | `RealWorld_Research_Task` |
| Competitor analysis | Multi-source + knowledge base | `KnowledgeSynthesis_Task` |
| Academic literature review | Parallel fetch + extraction | `KnowledgeSynthesis_Task` |
| Market research report | Research + write + review | `ContentCreation_Task` |

### Code & Development
| Goal | Pattern | Scenario |
|---|---|---|
| Security audit | 5-agent parallel audit | `GitRepoAudit_Task` |
| Architecture documentation | Parallel discovery + synthesis | `CodeAnalysis_Task` |
| Test gap analysis | Single audit agent | `GitRepoAudit_Task` |
| Refactoring suggestions | Quality + architecture agents | `CodeAnalysis_Task` |

### Content & Writing
| Goal | Pattern | Scenario |
|---|---|---|
| Research-backed article | Research + write + review loop | `ContentCreation_Task` |
| Technical tutorial | Research + structure + examples | `ContentCreation_Task` |
| Documentation site | Analysis + writing agents | `CodeAnalysis_Task` |

### Data & Analysis
| Goal | Pattern | Scenario |
|---|---|---|
| Sales data report | Parallel ingest + analysis | `DataAnalysis_Task` |
| Anomaly detection | Profiling + analysis agents | `DataAnalysis_Task` |
| Dataset comparison | Parallel profiles + merge | `DataAnalysis_Task` |

### Science & Engineering
| Goal | Pattern | Scenario |
|---|---|---|
| Quantum biomedical signal processing | 3-agent cognitive pipeline | `ProjectAortaScenario` |
| Custom domain algorithm | Vision + math + implementation | `ProjectAortaScenario` |

### Autonomous Experimentation (Karpathy-style)
| Goal | Pattern | Scenario |
|---|---|---|
| ML training optimization | Autonomous feedback loop | `AutoResearch_Task` |
| Prompt engineering optimization | Autonomous feedback loop | `AutoResearch_Task` |
| Algorithm parameter tuning | Autonomous feedback loop | `AutoResearch_Task` |
| Any script + scalar metric | Autonomous feedback loop | `AutoResearch_Task` |

---

## Agent Patterns Reference

```
Sequential:         A → B → C → D
Parallel:           A ─┬─ B ─┬─ D
                       └─ C ─┘
Reflective Loop:    A → B → [review → revise]×2 → output
Fan-Out Merge:      ─┬─ A ─┬─
                     ├─ B ─┤  → merge → report
                     └─ C ─┘
Cognitive Triple:   Vision → Math → Implementation
Autonomous Loop:    hypothesis → edit → run → evaluate → [commit|revert] → loop
```

---

## Tips

- **Specify output format** in your goal for better results:
  `"...and save as Markdown with sections for each topic"`

- **Reference existing project context** to continue work:
  `"Using the research in projects/MyProject/, now write the final report"`

- **Control agent behavior** with constraints in your goal:
  `"...use only free/open sources, keep total under 5 WebFetch calls"`

- **Chain goals** in the same session — state persists:
  ```
  skillos execute: "Research quantum computing trends"
  skillos execute: "Now write a 1000-word article based on that research"
  ```
