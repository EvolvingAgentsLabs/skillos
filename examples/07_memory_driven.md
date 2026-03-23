---
name: memory-driven
complexity: advanced
pattern: memory-informed-execution
estimated_cost: <$0.20
---

# Memory-Driven Execution: Learning from Past Projects

Demonstrates how SkillOS uses memory from previous executions to improve
current task performance — the key differentiator of the framework.

## Goal

```bash
skillos execute: "Using insights from all previous research projects in memory, write a tutorial on distributed systems consensus algorithms (Raft, Paxos) — apply any writing improvements learned from past feedback"
```

## What Happens

1. **QueryMemoryTool** consults `system/SmartMemory.md` for:
   - Past research task outcomes (what worked well)
   - Writing quality patterns (what scored highest)
   - Common mistakes to avoid
   - Preferred output formats

2. **PlanningAgent** creates execution plan *informed by memory*:
   - Uses source types that worked in past projects
   - Applies writing structure that received high review scores
   - Avoids patterns that failed previously

3. **ExecutionAgents** carry out the plan, adapting in real time

4. **LearningAgent** consolidates new insights back to memory

## Memory Consultation Output

```markdown
## Memory Query Results

### Relevant Past Experiences
1. [2026-02-15] Tech Intelligence Briefing — quality score 8.5/10
   - Key success: parallel fetch + structured synthesis
   - Learning: always include source attribution

2. [2026-02-28] Quantum Computing Tutorial — quality score 9/10
   - Key success: progressive complexity (beginner → advanced)
   - Learning: code examples dramatically improve clarity scores

### Recommended Approach
- Structure: beginner intro → core concepts → implementation → examples
- Include: working Python pseudocode, visual ASCII diagrams
- Avoid: jargon without definition, jumping to complex math immediately
- Estimated WebFetch calls: 4-6 (consistent with past research tasks)
```

## Expected Output

```
projects/[ProjectName]/output/tutorial.md       # Final tutorial
projects/[ProjectName]/memory/short_term/       # This execution's log
projects/[ProjectName]/memory/long_term/        # Updated learnings
system/SmartMemory.md                           # Updated with new insights
```

## Variations

```bash
# Memory-informed code generation
skillos execute: "Based on what's worked in past code projects in memory, implement a Redis-based rate limiter in Python — apply any patterns that scored well"

# Cross-project pattern application
skillos execute: "Review memory from all past documentation projects and apply the best structural patterns to write documentation for src/core/"

# Adaptive error handling
skillos execute: "Attempt to fetch and analyze arxiv.org papers on RAG — use memory to handle any fetch errors the way past projects did successfully"

# Learning consolidation
skillos execute: "Analyze all project memory logs from the past month and write a 'lessons learned' report with recommendations for future SkillOS projects"
```

## Memory File Structure

After execution, inspect:
```
projects/[ProjectName]/memory/
├── short_term/
│   └── 2026-03-22_10-00-00_agent_interaction.md
└── long_term/
    └── learnings_summary.md
```

And the shared:
```
system/SmartMemory.md    # Cross-project experience database
```

## Learning Objectives

- Understand how `QueryMemoryTool` retrieves relevant past experiences
- See how memory influences planning and execution
- Observe how new learnings get written back to memory
- Experience the compounding value of the memory system over time
