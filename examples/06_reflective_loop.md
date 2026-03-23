---
name: reflective-loop
complexity: advanced
pattern: write-review-revise-loop
estimated_cost: <$0.15
---

# Reflective Loop: Self-Improving Content Generation

Demonstrates the review-revise feedback loop pattern where an agent critiques
its own (or another agent's) output and iterates until quality thresholds
are met.

## Goal

```bash
skillos execute: "Write a technical explanation of how transformer attention mechanisms work, suitable for a software engineer with no ML background. Use a reviewer agent to score quality and revise until all criteria score 8/10 or higher."
```

## What Happens

```
WriterAgent → draft → ReviewerAgent → score < 8 → WriterAgent (revision)
                              ↓                              ↓
                         score >= 8                   ReviewerAgent
                              ↓                              ↓
                         Finalize                     score >= 8 or max cycles
                                                            ↓
                                                       Finalize
```

**Max cycles**: 2 revisions (3 total passes)

## Review Criteria

Each scored 1–10:

| Criterion | Description |
|---|---|
| Accuracy | Technically correct? |
| Clarity | Understandable by target audience? |
| Completeness | Key concepts covered? |
| Structure | Logical flow and organization? |
| Examples | Concrete illustrations provided? |

## Example Review Output

```markdown
# Editorial Review — Cycle 1

## Scores
- Accuracy: 9/10 ✓
- Clarity: 6/10 ✗ — too much jargon in section 2
- Completeness: 8/10 ✓
- Structure: 9/10 ✓
- Examples: 5/10 ✗ — code examples missing

## Required Revisions
1. Section 2: Replace "Q, K, V matrices" with plain English before introducing notation
2. Add a simple Python code example showing attention score calculation
3. Add an analogy for "softmax normalization"

## Decision: REVISE (2 criteria below threshold)
```

## Expected Final Output

```
projects/[ProjectName]/output/article.md     # Final polished version
projects/[ProjectName]/output/review_log.md  # All review cycles with scores
```

## Variations

```bash
# Code review loop — agent writes code, another reviews and requests fixes
skillos execute: "Write a Python function to parse ISO 8601 dates robustly, then have a code reviewer check it for edge cases and revise until it handles all common formats"

# Documentation loop
skillos execute: "Write API documentation for the functions in src/api.py, then have a technical writer review for completeness and revise until all endpoints are fully documented"

# Business proposal loop
skillos execute: "Draft a one-page business case for adopting SkillOS in an enterprise, then have a stakeholder reviewer evaluate it for clarity and ROI justification, revise until it scores 8/10"

# Test suite loop
skillos execute: "Write unit tests for src/payment_processor.py, have a QA reviewer check coverage and edge cases, revise until coverage exceeds 90%"
```

## Learning Objectives

- Understand the reflective loop agent pattern
- See how quality gates work in multi-agent pipelines
- Learn to configure review criteria and thresholds
- Observe how agents pass structured feedback through state files
