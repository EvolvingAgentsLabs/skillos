---
name: code-analysis-task
version: v1
description: >
  Codebase analysis scenario using a 5-agent collaborative network with parallel
  discovery, architecture analysis, documentation, and quality review with revision loop.
delegation_pattern: parallel_fanout_with_reflective_loop
error_recovery: per_agent
---

# Code Analysis Task: Comprehensive Codebase Review

## Scenario Overview

Analyzes an existing codebase using a 5-agent collaborative network. Two agents perform parallel discovery (structure mapping and pattern detection), followed by architecture analysis, documentation generation, and quality review with a max 2-cycle revision loop.

## Agent Network

| Agent | Role | Pattern Position |
|---|---|---|
| StructureMapper | Map directory layout, file types, dependency graph | Parallel (with PatternDetector) |
| PatternDetector | Identify code patterns, abstractions, conventions | Parallel (with StructureMapper) |
| ArchitectureAnalyst | Synthesize findings into architecture assessment | Sequential (after parallel phase) |
| DocumentationWriter | Generate comprehensive codebase documentation | Sequential (after analysis) |
| QualityReviewer | Review documentation quality, request revisions | Reflective loop (max 2 cycles) |

## Execution Pipeline

### Phase 1: Parallel Discovery (Fan-Out)

**Pattern**: Parallel Fan-Out

#### StructureMapper Agent
**Tools**: Glob, Grep, Read, Bash
1. `Glob` for all source files by language (`**/*.py`, `**/*.ts`, etc.)
2. `Bash` to count lines of code per directory
3. `Read` key config files (package.json, pyproject.toml, etc.)
4. Map dependency graph from import statements
5. Write `state/structure_map.md`

#### PatternDetector Agent
**Tools**: Grep, Read
1. `Grep` for common patterns: class definitions, decorators, error handling, tests
2. `Read` representative files from each pattern category
3. Identify architectural patterns (MVC, repository, factory, etc.)
4. Catalog coding conventions (naming, error handling, logging)
5. Write `state/pattern_report.md`

### Phase 2: Architecture Analysis (Sequential)

**Agent**: ArchitectureAnalyst
**Tools**: Read, Write
**Depends On**: Phase 1 (both agents)

1. Read `structure_map.md` and `pattern_report.md`
2. Identify system boundaries and module responsibilities
3. Assess coupling between modules
4. Evaluate adherence to SOLID principles
5. Identify technical debt indicators
6. Write `state/architecture_assessment.md`

### Phase 3: Documentation Generation (Sequential)

**Agent**: DocumentationWriter
**Tools**: Read, Write
**Depends On**: Phase 2

1. Read all Phase 1 and Phase 2 outputs
2. Generate comprehensive documentation:
   - Project overview and purpose
   - Architecture diagram (ASCII)
   - Module-by-module description
   - Key patterns and conventions
   - Setup and development guide
   - Technical debt summary
3. Write `projects/[ProjectName]/output/codebase_documentation.md`

### Phase 4: Quality Review (Reflective Loop)

**Pattern**: Reflective Loop (max 2 revision cycles)
**Agent**: QualityReviewer
**Tools**: Read, Write

**Review Criteria**:
- Accuracy: Does documentation match actual code structure?
- Completeness: Are all major modules covered?
- Clarity: Is it understandable by a new developer?
- Actionability: Are technical debt items prioritized?

**Loop**:
1. QualityReviewer reads documentation output
2. Writes `state/review_feedback.md` with scored criteria
3. If any criterion scores below 7/10:
   - DocumentationWriter re-reads feedback and revises
   - QualityReviewer re-reviews (cycle 2)
4. After max 2 cycles or all criteria >= 7/10, finalize

## Error Recovery

| Agent | Error | Action |
|---|---|---|
| StructureMapper | Glob returns 0 files | Check path, try broader pattern |
| PatternDetector | Grep timeout on large repo | Add head_limit, narrow scope |
| ArchitectureAnalyst | Missing input file | Wait for parallel phase completion |
| DocumentationWriter | Output too large | Split into multiple files |
| QualityReviewer | Review criteria unclear | Use default scoring rubric |

## Expected Output

```
projects/[ProjectName]/output/
├── codebase_documentation.md   # Main deliverable
├── structure_map.md            # Directory and dependency map
├── pattern_report.md           # Code pattern catalog
├── architecture_assessment.md  # Architecture analysis
└── review_report.md            # Quality review scores
```

## Success Criteria

- All 5 agents complete successfully
- Documentation covers >= 80% of source directories
- Quality review scores >= 7/10 on all criteria
- Revision loop converges within 2 cycles
- Total execution cost < $0.75

## Usage

```bash
skillos execute: "Analyze the codebase at [path] and generate comprehensive documentation"
```
