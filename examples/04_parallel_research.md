---
name: parallel-research
complexity: advanced
pattern: parallel-fanout-merge
estimated_cost: <$0.25
---

# Parallel Research: Multi-Source Intelligence Gathering

Demonstrates parallel agent fan-out — multiple agents fetching sources
simultaneously, then merging into a unified report.

## Goal

```bash
skillos execute: "Research the current state of AI coding assistants by fetching information about GitHub Copilot, Cursor, Codeium, Tabnine, and Amazon CodeWhisperer simultaneously, then synthesize a comparison report"
```

## What Happens

1. **5 FetchAgents run in parallel** — one per tool
2. Each agent: fetches product page, extracts features, pricing, and differentiators
3. **MergeAgent** synthesizes all findings into a structured comparison

## Agent Timeline

```
t=0s  ┌─ FetchAgent(Copilot)   ─────────────┐
      ├─ FetchAgent(Cursor)    ─────────────┤
      ├─ FetchAgent(Codeium)   ───────────  ┤
      ├─ FetchAgent(Tabnine)   ──────────── ┤
      └─ FetchAgent(CodeWhisperer) ─────────┘
t=15s └───────────────── MergeAgent ────────── output
```

## Expected Output

```
projects/Project_ai_coding_assistants/output/comparison_report.md
```

```markdown
# AI Coding Assistants: 2025 Comparison

## Overview
| Tool | Company | Pricing | IDE Support | LLM Backend |
|---|---|---|---|---|
| Copilot | GitHub/MS | $10/mo | VS Code, JetBrains, Vim | GPT-4 |
| Cursor | Cursor | $20/mo | Custom fork of VS Code | Claude, GPT-4 |
...

## Feature Comparison
### Code Completion
...

## Pricing Analysis
...

## Recommendation by Use Case
- **Best for teams**: [tool] — because [reason]
- **Best free option**: [tool]
- **Best for privacy**: [tool]
```

## Variations

```bash
# Parallel news monitoring
skillos execute: "Simultaneously fetch today's AI news from TechCrunch, VentureBeat, and The Verge, then identify the 3 most important stories"

# Parallel documentation comparison
skillos execute: "Fetch the getting-started guides for FastAPI, Flask, and Django simultaneously, then create a beginner's guide comparing their approaches"

# Parallel pricing research
skillos execute: "Research the pricing pages of AWS, GCP, and Azure for vector database services in parallel, then create a cost comparison table"

# Multi-repo parallel analysis
skillos execute: "Analyze the README and architecture of these 4 open-source agent frameworks in parallel: AutoGen, LangChain, CrewAI, and LlamaIndex"
```

## Learning Objectives

- Understand parallel agent fan-out execution
- See how intermediate state files coordinate between phases
- Observe cost efficiency of parallel vs sequential fetching
- Learn to structure merge/synthesis agents
