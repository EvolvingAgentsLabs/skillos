# Scoring Rubric

## Overview
The Scoring Rubric defines how agents are evaluated, scored, and ranked based on their execution traces. It uses the 7-type failure taxonomy for root cause classification and a composite scoring formula for overall performance assessment.

## 7-Type Failure Taxonomy

Every agent failure maps to exactly one root cause type. This classification drives targeted remediation rather than generic improvements.

### Type 1: INSTRUCTION_AMBIGUITY
**Definition**: Agent misinterprets a vague or ambiguous instruction in its system prompt.
**Indicators**: Agent asks clarifying questions, produces output that doesn't match intent, or takes an unexpected path.
**Remediation**: Add 1 sentence clarifying the specific decision point.
**Weight**: 0.3 (low severity — easy to fix)

### Type 2: MISSING_TOOL
**Definition**: Agent cannot complete its task because it lacks a required tool.
**Indicators**: Agent describes what it would do but cannot execute, or produces a workaround that's lower quality.
**Remediation**: Add the missing tool to `tools:` in YAML frontmatter.
**Weight**: 0.5 (medium severity — requires config change)

### Type 3: PATTERN_MISMATCH
**Definition**: Agent uses an incorrect workflow or delegation pattern for the task type.
**Indicators**: Agent completes the task but inefficiently, or produces structurally wrong output.
**Remediation**: Select better delegation pattern from long-term memory.
**Weight**: 0.4 (medium severity — requires prompt restructuring)

### Type 4: MISSING_RECOVERY
**Definition**: Agent encounters an error it has no fallback for.
**Indicators**: Agent fails with an unhandled exception, timeout, or permission error.
**Remediation**: Add a recovery rule for the specific observed error.
**Weight**: 0.6 (higher severity — causes hard failures)

### Type 5: CONTEXT_OVERLOAD
**Definition**: Agent loses track of its objective in long or complex interactions.
**Indicators**: Agent repeats itself, forgets earlier steps, or produces incomplete output.
**Remediation**: Add checkpointing guidance (e.g., "After each phase, summarize progress").
**Weight**: 0.7 (high severity — indicates structural issue)

### Type 6: STALE_ASSUMPTION
**Definition**: Agent references outdated paths, APIs, versions, or facts.
**Indicators**: Agent produces errors from wrong paths, deprecated API calls, or incorrect facts.
**Remediation**: Update the stale assumption in the agent prompt.
**Weight**: 0.5 (medium severity — easy to fix once identified)

### Type 7: UNDERSPECIFIED_OUTPUT
**Definition**: Agent produces output in the wrong format, missing required fields, or without examples.
**Indicators**: Downstream agents or users cannot parse the output correctly.
**Remediation**: Tighten the output format contract and add examples.
**Weight**: 0.3 (low severity — cosmetic but important for integration)

## Composite Scoring Formula

### Per-Agent Score (0.0 to 1.0)

```
success_rate = completed_traces / total_traces

failure_severity = SUM(failure_type_weight * count_of_type) / total_failures
  (0.0 if no failures)

output_quality = traces_with_valid_output_format / total_traces
  (1.0 if no format spec exists — benefit of the doubt)

efficiency = 1.0 - (unused_tools_count * 0.05)
  (capped at 0.5 minimum)

composite = (success_rate * 0.40)
          + ((1.0 - failure_severity) * 0.30)
          + (output_quality * 0.20)
          + (efficiency * 0.10)
```

### Component Weights Rationale
- **Success rate (40%)**: Primary indicator — did the agent accomplish its task?
- **Failure severity (30%)**: Not all failures are equal — context overload is worse than ambiguity
- **Output quality (20%)**: Correct output format enables downstream integration
- **Efficiency (10%)**: Minimal tool access reduces attack surface and complexity

## Tier Classification

| Tier | Score Range | Meaning | Action |
|------|------------|---------|--------|
| **S** | >= 0.90 | Excellent | Candidate for template extraction to long-term memory |
| **A** | 0.70 - 0.89 | Good | No action needed — performing well |
| **B** | 0.50 - 0.69 | Needs Improvement | Candidate for EvolutionControlAgent proposals |
| **C** | < 0.50 | Underperforming | Candidate for evolution or pruning |

## Scoring Edge Cases

### New Agents (< 3 traces)
- Score as "INSUFFICIENT DATA" — do not tier-classify
- Minimum 3 traces required for reliable scoring
- Flag for monitoring but don't propose changes

### Agents with External Dependencies
- If an agent fails because an upstream agent failed, discount that failure
- Only score failures that are within the agent's control
- Note dependency failures separately in the report

### Agents with Mixed Outcomes
- Partial completions count as 0.5 for success_rate calculation
- If an agent partially succeeds, classify the failure portion by taxonomy

## Trend Analysis

Beyond individual scores, the scorecard should identify:
- **Systemic failure types**: If multiple agents share the same failure type, the root cause may be in the project architecture, not individual agents
- **Degradation trends**: If an agent's score drops over successive evaluations, something changed
- **Capability gaps**: If no agent in the project handles a certain task type well, a new agent may be needed

## Scoring Constraints

- **NC-6**: Never fabricate failure evidence — only score based on actual traces
- **NC-21**: Never compute totals by adding increments — recount from source
- Minimum 3 traces per agent for reliable scoring
- Always show evidence (trace IDs) for each score component
