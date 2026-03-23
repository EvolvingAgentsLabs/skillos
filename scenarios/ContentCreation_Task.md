---
name: content-creation-task
version: v1
description: >
  Three-agent sequential pipeline for research-backed content creation:
  ResearchAgent gathers sources, WriterAgent drafts content, EditorAgent
  reviews and refines with a max 2-cycle revision loop.
delegation_pattern: sequential_with_reflective_loop
error_recovery: per_stage
---

# Content Creation Task: Research-Backed Article Generator

## Scenario Overview

Produces a well-researched, polished article or blog post on any topic using a
3-agent pipeline. The ResearchAgent gathers and summarizes sources, the
WriterAgent drafts structured content, and the EditorAgent reviews for quality
with up to 2 revision cycles.

## Agent Pipeline

| Agent | Role | Pattern |
|---|---|---|
| ResearchAgent | Web research, source summarization | First (sequential) |
| WriterAgent | Draft structured article from research | Sequential (after research) |
| EditorAgent | Quality review + revision request | Reflective loop (max 2 cycles) |

## Execution Pipeline

### Stage 1: Research

**Agent**: ResearchAgent
**Tools**: WebFetch, Write

1. Identify 3–5 authoritative sources for the topic
2. `WebFetch` each source
3. Extract key facts, statistics, quotes, and perspectives
4. Identify the main narrative threads across sources
5. Write `state/research_notes.md`

**Research notes structure:**
```
## Key Facts
- [fact with source attribution]

## Statistics
- [stat]: [source]

## Perspectives
- [viewpoint]: [source]

## Narrative Threads
1. [thread]
```

### Stage 2: Article Draft

**Agent**: WriterAgent
**Tools**: Read, Write

1. Read `state/research_notes.md`
2. Determine optimal structure (how-to, listicle, deep-dive, opinion)
3. Write a complete draft with:
   - Compelling headline
   - Hook opening paragraph
   - 3–5 structured sections with subheadings
   - Evidence and examples from research notes
   - Actionable conclusion with key takeaways
4. Write `state/article_draft.md`

**Target**: 800–1200 words, clear structure, citations included

### Stage 3: Editorial Review (Reflective Loop)

**Pattern**: Reflective loop (max 2 revision cycles)
**Agent**: EditorAgent
**Tools**: Read, Write

**Review Criteria** (each scored 1–10):
- Accuracy: Claims supported by research notes?
- Structure: Logical flow and clear sections?
- Clarity: Accessible to target audience?
- Engagement: Compelling opening and conclusion?
- Completeness: Key aspects of topic covered?

**Loop**:
1. EditorAgent reads draft and research notes
2. Scores each criterion, writes `state/editorial_feedback.md`
3. If any criterion < 7/10:
   - WriterAgent revises based on specific feedback (cycle 2)
   - EditorAgent re-reviews (max once more)
4. When all criteria >= 7/10 or 2 cycles complete:
   - Write final to `projects/[ProjectName]/output/article.md`

## Expected Output

```
projects/[ProjectName]/output/
├── article.md              # Final polished article
├── research_notes.md       # Source research summary
└── editorial_report.md     # Quality scores and revision history
```

## Success Criteria

- At least 3 sources successfully researched
- Article is 800–1200 words
- All editorial criteria score >= 7/10
- Revision loop converges within 2 cycles
- All claims traceable to research notes

## Usage

```bash
skillos execute: "Write a research-backed article about the impact of large language models on software development"

skillos execute: "Create a blog post explaining quantum computing to a general audience"

skillos execute: "Write an in-depth guide on building production-ready REST APIs with Python"
```
