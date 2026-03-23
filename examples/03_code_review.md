---
name: code-review
complexity: intermediate
pattern: sequential-three-agent
estimated_cost: <$0.10
---

# Code Review: Automated PR Analysis

Demonstrates multi-agent sequential processing applied to code review.

## Goal

```bash
skillos execute: "Review the Python files in src/ for: code quality issues, missing type hints, potential bugs, and test coverage gaps. Produce a prioritized review report."
```

## What Happens

1. **StructureAgent**: Maps all Python files, counts lines, lists functions
2. **ReviewAgent**: Reads each file, identifies issues by category
3. **ReportAgent**: Produces prioritized report with line-level references

## Expected Output

```
projects/Project_code_review/output/review_report.md
```

```markdown
# Code Review Report — src/

## Summary
- Files reviewed: 12
- Issues found: 23 (3 critical, 8 high, 12 low)

## Critical Issues
### Missing Input Validation
**File**: `src/api/handlers.py:45`
**Issue**: User input passed directly to shell command
**Fix**: Use `shlex.quote()` or avoid shell=True

...

## Type Hint Coverage
| File | Coverage |
|---|---|
| src/models.py | 90% |
| src/utils.py | 40% ← needs improvement |

## Test Coverage Gaps
- `src/payment/processor.py` — no test file found
```

## Variations

```bash
# Review a single file
skillos execute: "Review the file src/database.py for SQL injection vulnerabilities and connection handling issues"

# Review with a specific focus
skillos execute: "Audit all JavaScript files in frontend/src/ for XSS vulnerabilities and unsafe DOM manipulation"

# Pre-commit style check
skillos execute: "Check the recently modified files in the git working tree for obvious bugs, missing error handling, and style issues"

# Language-specific review
skillos execute: "Review the Go code in cmd/ and pkg/ for goroutine leaks, error wrapping conventions, and interface misuse"
```

## Learning Objectives

- Chain multiple specialized agents with sequential dependencies
- Use `Grep` and `Glob` tools through agent specifications
- Produce structured reports with file/line references
