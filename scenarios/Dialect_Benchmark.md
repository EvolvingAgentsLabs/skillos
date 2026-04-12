---
name: dialect-benchmark
version: v1
description: >
  Benchmark comparing SkillOS dialect-driven analysis vs plain Claude Code
  on a microservice cascade failure problem. Exercises 5 dialects across 6 deliverables
  to demonstrate token compression and reasoning quality gains.
delegation_pattern: sequential
error_recovery: per_stage
requires_dialects:
  - formal-proof
  - system-dynamics
  - boolean-logic
  - constraint-dsl
  - exec-plan
pipeline:
  - step: 1
    deliverable: "Root cause diagnosis"
    dialect: formal-proof
  - step: 2
    deliverable: "System dynamics model"
    dialect: system-dynamics
  - step: 3
    deliverable: "Retry condition"
    dialect: boolean-logic
  - step: 4
    deliverable: "Resource exhaustion proof"
    dialect: formal-proof
  - step: 5
    deliverable: "Fix constraints"
    dialect: constraint-dsl
  - step: 6
    deliverable: "Implementation plan"
    dialect: exec-plan
---

# Dialect Benchmark: Microservice Cascade Failure Analysis

## Scenario Overview

Analyze a microservice architecture with a deliberately planted feedback loop bug — a retry mechanism that under load creates a reinforcing loop (more retries -> more load -> more timeouts -> more retries). Produce 6 structured deliverables, each using a specific SkillOS dialect.

## Problem Statement

```
Service A (API Gateway) receives requests and routes to Service B (Order Service).
Service B calls Service C (Inventory Service) and Service D (Payment Service) in parallel.
If Service C or Service D fails, Service B retries up to 3 times with 2-second backoff.
Service B has a 10-second timeout for each downstream call.
Under load, Service C response times increase from 200ms to 8 seconds.
Service A has a 30-second timeout for requests to Service B.
There is no circuit breaker.
```

## Dialect Protocol

Each deliverable MUST use the specified dialect notation. Load the dialect definition from `system/dialects/` before producing each deliverable. The dialect forces structured notation that prevents logical shortcuts and ambiguity.

| Deliverable | Dialect | Dialect File |
|---|---|---|
| Root cause diagnosis | `formal-proof` | `system/dialects/formal-proof.dialect.md` |
| System dynamics model | `system-dynamics` | `system/dialects/system-dynamics.dialect.md` |
| Retry condition | `boolean-logic` | `system/dialects/boolean-logic.dialect.md` |
| Resource exhaustion proof | `formal-proof` | `system/dialects/formal-proof.dialect.md` |
| Fix constraints | `constraint-dsl` | `system/dialects/constraint-dsl.dialect.md` |
| Implementation plan | `exec-plan` | `system/dialects/exec-plan.dialect.md` |

## Execution Pipeline

### Phase 1: Root Cause Diagnosis

**Dialect**: `formal-proof`
**Agent**: SystemAgent (direct analysis)

Using GIVEN:/DERIVE:/QED formal proof notation with [BY rule] annotations:
1. Identify all premises from the architecture description
2. Derive the cascade failure mechanism step-by-step
3. Conclude with the root cause — the reinforcing feedback loop

**Expected notation**: `GIVEN:` predicates, `DERIVE:` steps with `[BY rule_name]`, `QED` conclusion.

### Phase 2: System Dynamics Model

**Dialect**: `system-dynamics`
**Agent**: SystemAgent (direct analysis)

Model the system using stock-flow notation:
1. Identify stocks (active connections, pending retries, available threads, queue depth)
2. Identify flows (request rate, timeout rate, retry rate, completion rate)
3. Identify feedback loops — especially the reinforcing retry-load loop `[FB+]`
4. Identify delays and external inputs

**Expected notation**: `[STOCK]`, `[FLOW]`, `[FB+]`, `[FB-]`, `[DELAY]`, `[EXT]`.

### Phase 3: Retry Condition (Boolean Logic)

**Dialect**: `boolean-logic`
**Agent**: SystemAgent (direct analysis)

State the exact retry condition with zero ambiguity:
1. Extract the atomic predicates (service failed, retry count, timeout)
2. Combine with explicit boolean operators and parenthesization
3. Show the condition under which retries fire AND the condition under which they cascade

**Expected notation**: Explicit `∧`, `∨`, `¬`, `→` operators with full parenthesization.

### Phase 4: Resource Exhaustion Proof

**Dialect**: `formal-proof`
**Agent**: SystemAgent (direct analysis)

Prove mathematically that the current design leads to resource exhaustion:
1. Start from the given parameters (3 retries, 2s backoff, 10s timeout, 30s gateway timeout)
2. Derive the worst-case connection holding time
3. Derive the thread/connection multiplication factor
4. Prove that under sustained load, resources are exhausted

**Expected notation**: `GIVEN:` with exact numeric values, `DERIVE:` with arithmetic, `QED` with exhaustion conclusion.

### Phase 5: Fix Constraints

**Dialect**: `constraint-dsl`
**Agent**: SystemAgent (direct analysis)

Propose formal constraints for the fix:
1. Circuit breaker constraint (hard, HIGH severity)
2. Retry budget constraint (hard, HIGH severity)
3. Timeout hierarchy constraint (hard, MEDIUM severity)
4. Backpressure constraint (soft, MEDIUM severity)
5. Monitoring constraint (soft, LOW severity)

**Expected notation**: `C[N][severity]` and `S[N][severity]` with predicates and implications.

### Phase 6: Implementation Plan

**Dialect**: `exec-plan`
**Agent**: SystemAgent (direct analysis)

Create a compressed execution plan for implementing all fixes:
1. Phase dependencies (circuit breaker before retry changes)
2. Verification criteria per phase
3. Rollback strategy

**Expected notation**: `@plan[ID]`, `P[N][agent]: action`, `dep=`, `verify:`, `success:`.

## Success Criteria

- All 6 deliverables produced using correct dialect notation
- Feedback loop explicitly identified as reinforcing `[FB+]` in system dynamics model
- Retry condition fully parenthesized with zero ambiguity
- Resource exhaustion proof contains step-by-step numeric derivation
- Constraints have severity levels and thresholds
- Execution plan has phase dependencies

## Usage

```bash
skillos execute: "Run the Dialect Benchmark scenario"
```
