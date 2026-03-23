---
name: custom-agent-creation
complexity: expert
pattern: dynamic-agent-generation
estimated_cost: <$0.30
---

# Custom Agent Creation: Domain-Specific Agent Synthesis

Demonstrates SkillOS's ability to dynamically create new agents during
execution when existing agents lack required domain capabilities.

## Goal

```bash
skillos execute: "Analyze climate change datasets from the input/ directory, identify statistical trends in temperature anomalies, and generate a scientific-style report with confidence intervals — create any specialized agents needed"
```

## What Happens

1. **SystemAgent** analyzes the goal:
   - Identifies required capabilities: climate science, statistics, scientific writing
   - Checks SmartLibrary — no climate specialist agents exist
   - Decides to create 2 new agents dynamically

2. **New agents created** and saved to `projects/[ProjectName]/components/agents/`:
   - `climate-data-agent.md` — specialized in climate metrics and anomalies
   - `scientific-report-agent.md` — formats output in academic style

3. **New agents copied** to `.claude/agents/` with project prefix

4. **Execution proceeds** using the newly created agents

## Dynamically Created Agent Example

`projects/Project_climate_analysis/components/agents/climate-data-agent.md`:

```markdown
---
name: climate-data-agent
type: specialized-agent
project: Project_climate_analysis
capabilities:
  - Climate metric interpretation
  - Temperature anomaly calculation
  - Statistical trend analysis with confidence intervals
  - IPCC data format familiarity
tools:
  - Read
  - Bash
  - Write
---

# Climate Data Agent

## Purpose
Analyze climate datasets for temperature anomalies and statistical trends
using rigorous scientific methodology.

## Instructions
1. Load climate dataset and identify metric types (°C anomaly, baseline period)
2. Calculate rolling averages (5-year, 10-year windows)
3. Compute linear regression trend with 95% confidence interval
4. Identify statistically significant anomalies (> 2σ from mean)
5. Format all statistics with proper units and uncertainty ranges
...
```

## Expected Output

```
projects/Project_climate_analysis/
├── components/agents/
│   ├── climate-data-agent.md          # Newly created agent
│   └── scientific-report-agent.md     # Newly created agent
└── output/
    └── climate_analysis_report.md     # Final scientific report
```

## When Dynamic Agent Creation Triggers

SystemAgent creates new agents when:
- Goal requires specialized domain knowledge not in SmartLibrary
- Task needs a communication style not present (e.g., legal, medical, academic)
- Workflow benefits from a role not yet defined (e.g., fact-checker, devil's advocate)
- Domain-specific validation is needed (e.g., units, terminology, format)

## Variations

```bash
# Legal document analysis
skillos execute: "Review the contracts in input/agreements/ for liability clauses — create a legal analysis agent if needed"

# Medical literature synthesis
skillos execute: "Analyze the clinical trial summaries in input/trials/ and produce an evidence summary — create agents specialized in medical research methodology"

# Financial modeling
skillos execute: "Build a DCF valuation model from the financial data in input/financials.csv — create a financial analyst agent with proper valuation methodology"

# Creative domain
skillos execute: "Analyze the narrative structure of the screenplay at input/script.pdf and provide screenwriting feedback — create a screenwriting critique agent"
```

## Inspecting Created Agents

After execution, view the created agents:

```bash
# List project-specific agents
ls projects/[ProjectName]/components/agents/

# View a created agent
cat projects/[ProjectName]/components/agents/climate-data-agent.md

# See all agents available to Claude Code
ls .claude/agents/
```

## Learning Objectives

- Understand how SystemAgent detects capability gaps
- See the structure of a dynamically generated agent markdown spec
- Learn when agent creation is triggered vs. using existing agents
- Observe how new agents integrate with the project's namespace
