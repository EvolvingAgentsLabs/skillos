---
name: realworld-research-task
version: v2
description: >
  Live web research scenario demonstrating a 4-stage intelligence pipeline
  with parallel fetching, trend analysis, pattern synthesis, and briefing generation.
delegation_pattern: sequential_with_parallel_fanout
error_recovery: per_stage
---

# RealWorld Research Task: Tech Intelligence Briefing

## Scenario Overview

Monitors 5 tech news sources, extracts trending topics, identifies cross-source patterns, and generates a structured intelligence briefing.

## Target Sources

| Source | URL | Type |
|---|---|---|
| TechCrunch | https://techcrunch.com | Startup/VC news |
| Ars Technica | https://arstechnica.com | Deep tech analysis |
| Hacker News | https://news.ycombinator.com | Developer community |
| MIT Tech Review | https://technologyreview.com | Research/emerging tech |
| Wired | https://wired.com | Tech culture/trends |

## Execution Pipeline

### Stage 1: Content Acquisition (Parallel Fan-Out)

**Pattern**: Parallel Fan-Out (all 5 fetches concurrent)
**Agent**: SystemAgent (direct tool use)
**Tools**: WebFetch (x5 concurrent)

For each source:
1. `WebFetch` the homepage/feed URL
2. Extract headlines, summaries, publication dates
3. Write to `state/source_{name}_raw.md`

**Error Recovery**:
| Error | Action |
|---|---|
| HTTP timeout | Retry 2x with backoff, then skip source |
| Rate limited | Wait 5s, retry once |
| Content empty | Log warning, continue with remaining sources |

**Minimum viable**: Proceed if >= 3 of 5 sources succeed.

### Stage 2: Trend Analysis

**Pattern**: Sequential (depends on Stage 1 output)
**Agent**: IntelligenceBriefingAgent
**Tools**: Read, Grep, Write

1. Read all `source_*_raw.md` files
2. Extract named entities, topics, and themes
3. Rank topics by cross-source frequency
4. Write `state/trend_analysis.md`

### Stage 3: Pattern Synthesis

**Pattern**: Sequential (depends on Stage 2)
**Agent**: ResearchReportAgent
**Tools**: Read, Write

1. Read `trend_analysis.md`
2. Identify convergent narratives across sources
3. Detect emerging signals (topics appearing in 2+ sources for first time)
4. Write `state/pattern_synthesis.md`

### Stage 4: Briefing Generation

**Pattern**: Sequential (depends on Stage 3)
**Agent**: WritingAgent
**Tools**: Read, Write

1. Read `trend_analysis.md` and `pattern_synthesis.md`
2. Generate structured intelligence briefing:
   - Executive summary (3-5 bullet points)
   - Top trending topics with source attribution
   - Emerging signals section
   - Source reliability notes
3. Write final output to `projects/[ProjectName]/output/intelligence_briefing.md`

## Expected Output

```markdown
# Tech Intelligence Briefing - [Date]

## Executive Summary
- [Top 3-5 key findings]

## Trending Topics
### Topic 1: [Name]
- Sources: [list]
- Summary: [analysis]
- Signal strength: [strong/moderate/emerging]

## Emerging Signals
- [Topics appearing for the first time across multiple sources]

## Source Notes
- [Availability and quality notes per source]
```

## Success Criteria

- At least 3 sources successfully fetched
- Minimum 5 distinct topics identified
- Cross-source patterns detected
- Briefing is well-structured and actionable
- Total execution cost < $0.50

## Usage

```bash
skillos execute: "Monitor 5 tech news sources and generate a weekly intelligence briefing"
```
