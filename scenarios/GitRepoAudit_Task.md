---
name: git-repo-audit-task
version: v1
description: >
  Five-agent parallel audit of a git repository covering security, code quality,
  test coverage, dependency health, and documentation completeness. Agents run
  in parallel fan-out then merge into a unified audit report.
delegation_pattern: parallel_fanout_merge
error_recovery: per_agent
---

# Git Repository Audit Task: Comprehensive Code Health Review

## Scenario Overview

Runs five specialized audit agents in parallel against a local git repository,
then merges findings into a prioritized action report. Covers security
vulnerabilities, code quality, test coverage, dependency health, and
documentation completeness.

## Agent Network

| Agent | Audit Domain | Pattern |
|---|---|---|
| SecurityAuditor | Secrets, vulnerable patterns, injection risks | Parallel |
| QualityAuditor | Complexity, duplication, code smells | Parallel |
| TestCoverageAuditor | Test existence, coverage gaps, test quality | Parallel |
| DependencyAuditor | Outdated/vulnerable deps, license issues | Parallel |
| DocsAuditor | README, API docs, inline comments | Parallel |
| AuditMergeAgent | Synthesize findings, prioritize, generate report | Sequential (after all parallel) |

## Execution Pipeline

### Phase 1: Parallel Audit Fan-Out

**Pattern**: All 5 agents run concurrently

#### SecurityAuditor
**Tools**: Grep, Read, Glob

1. Scan for hardcoded secrets patterns:
   - `Grep` for: `password\s*=`, `api_key`, `secret`, `token`, `AWS_SECRET`
   - Flag any `.env` files checked into git
2. Identify risky code patterns:
   - SQL concatenation (potential injection)
   - `eval()` / `exec()` usage
   - Unvalidated user input paths
3. Check for overly permissive file permissions references
4. Write `state/security_findings.md` with severity ratings (HIGH/MEDIUM/LOW)

#### QualityAuditor
**Tools**: Glob, Read, Bash, Grep

1. `Glob` all source files by language
2. Measure cyclomatic complexity indicators (deeply nested if/for/while)
3. Detect code duplication patterns (identical blocks > 10 lines)
4. Flag long functions (> 50 lines) and large files (> 500 lines)
5. Check naming conventions consistency
6. Write `state/quality_findings.md`

#### TestCoverageAuditor
**Tools**: Glob, Grep, Read

1. Locate test files (`**/*test*`, `**/*spec*`, `tests/`, `__tests__/`)
2. Map test files to source files — identify untested modules
3. Check test quality: assert density, mock overuse, test isolation
4. Look for TODO/FIXME in test files
5. Calculate rough test-to-code ratio
6. Write `state/test_coverage_findings.md`

#### DependencyAuditor
**Tools**: Read, Glob

1. Locate dependency files: `package.json`, `requirements.txt`, `pyproject.toml`, `Gemfile`, `go.mod`
2. List all direct dependencies with versions
3. Flag dependencies pinned to `latest` or without version constraints
4. Identify known-risky packages (common vulnerability patterns)
5. Check license compatibility (MIT, Apache, GPL presence)
6. Write `state/dependency_findings.md`

#### DocsAuditor
**Tools**: Glob, Read, Grep

1. Check for `README.md` — score completeness (setup, usage, API, contributing)
2. Locate API documentation (OpenAPI, JSDoc, docstrings)
3. Measure inline comment density per module
4. Identify undocumented public functions/classes
5. Check for `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`
6. Write `state/docs_findings.md`

### Phase 2: Audit Merge and Report (Sequential)

**Agent**: AuditMergeAgent
**Tools**: Read, Write
**Depends On**: All Phase 1 agents

1. Read all 5 findings files
2. Deduplicate overlapping issues
3. Assign priority score to each finding:
   - P0 (Critical): Security HIGH + exposed secrets
   - P1 (High): Security MEDIUM + no tests + vulnerable deps
   - P2 (Medium): Quality issues + missing docs
   - P3 (Low): Style + minor improvements
4. Generate prioritized action plan
5. Write `projects/[ProjectName]/output/audit_report.md`

**Report structure:**
```
# Repository Audit Report

## Executive Summary
- Overall Health Score: [0-100]
- Critical Issues: [count]
- High Priority: [count]

## P0 — Critical (Fix Immediately)
- [issue]: [location] — [recommended fix]

## P1 — High Priority
...

## Audit Scores by Domain
| Domain | Score | Key Finding |
|---|---|---|
| Security | /10 | ... |
| Quality | /10 | ... |
| Test Coverage | /10 | ... |
| Dependencies | /10 | ... |
| Documentation | /10 | ... |

## Action Plan
1. [highest priority action]
...
```

## Error Recovery

| Agent | Error | Action |
|---|---|---|
| Any auditor | Target path not found | List repo root, ask user to confirm path |
| SecurityAuditor | Binary files in Grep | Skip binary files, continue |
| QualityAuditor | Unknown language | Report unsupported, audit what's possible |
| DependencyAuditor | No dependency file found | Report as finding (missing dependency management) |
| DocsAuditor | No README | Flag as P2 finding, continue |

## Expected Output

```
projects/[ProjectName]/output/
├── audit_report.md             # Prioritized audit report with scores
├── security_findings.md        # Detailed security scan
├── quality_findings.md         # Code quality analysis
├── test_coverage_findings.md   # Test coverage gaps
├── dependency_findings.md      # Dependency health
└── docs_findings.md            # Documentation gaps
```

## Success Criteria

- All 5 audit agents complete (partial success if 4/5)
- Each domain produces at least 3 findings (or "no issues found")
- Final report includes overall health score
- All P0 and P1 issues include specific file/line references
- Action plan is ordered by priority

## Usage

```bash
skillos execute: "Run a comprehensive security and quality audit on the repository at /path/to/myproject"

skillos execute: "Audit the current codebase for vulnerabilities, test coverage gaps, and documentation issues"

skillos execute: "Perform a full code health review of projects/MyApp and generate a prioritized remediation plan"
```
