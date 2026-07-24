# sysctl

Control plane for [SkillOS](https://github.com/EvolvingAgentsLabs/skillos_plugin) projects. Audits security, scores agents, proposes controlled evolution, and manages lifecycle (merge, deprecate, delete) of agents and memory.

Part of the [Evolving Agents](https://github.com/EvolvingAgentsLabs) ecosystem.

## Install

```bash
/plugin install /path/to/skillos_systemcontrol_plugin/skillos-systemcontrol-plugin
```

## Use

```bash
# Full health check on a project
/sysctl "audit and score all agents in Project_quantum"

# Security scan
/sysctl "scan Project_webapp for security vulnerabilities"

# Score and rank agents
/sysctl "score agents in Project_pipeline"

# Propose improvements for underperformers
/sysctl "evolve low-scoring agents in Project_quantum"

# Identify dead agents and compact memory
/sysctl "prune and compact Project_old"

# Full maintenance pass
/sysctl "full maintenance on all projects"
```

## How it works

`/sysctl` operates on `projects/` created by `/skillos`. It never modifies agent files directly — it produces reports and proposals for human approval.

**Modes**: AUDIT | SCORE | EVOLVE | PRUNE | COMPACT | REPORT

**Agents**:
- `SystemAgent` — orchestrates control operations
- `SecurityAuditAgent` — scans for prompt injection, path traversal, overpermissive tools
- `PerformanceScorecardAgent` — scores agents using 7-type failure taxonomy
- `EvolutionControlAgent` — proposes minimal changes with anti-overfitting gate
- `LifecycleManagerAgent` — handles deprecation, merge, deletion with cascading reference validation

**System specs**: [SecurityFramework](skillos-systemcontrol-plugin/system_files/SecurityFramework.md) | [ScoringRubric](skillos-systemcontrol-plugin/system_files/ScoringRubric.md) | [EvolutionProtocol](skillos-systemcontrol-plugin/system_files/EvolutionProtocol.md) | [LifecycleProtocol](skillos-systemcontrol-plugin/system_files/LifecycleProtocol.md)

## Key concepts

**Anti-Overfitting Gate**: Every proposed change must pass: "If the failures that motivated this change disappeared, would it still be a good change?" YES = approve, NO = reject.

**7-Type Failure Taxonomy**: INSTRUCTION_AMBIGUITY, MISSING_TOOL, PATTERN_MISMATCH, MISSING_RECOVERY, CONTEXT_OVERLOAD, STALE_ASSUMPTION, UNDERSPECIFIED_OUTPUT.

**Cascading Prune-and-Verify**: Before deleting anything, scan all references, classify as routing-critical vs doc-debt, update all critical refs, then delete.

**Minimal Surface Edits**: Instruction clarification > tool addition > recovery rule > output contract > path update > checkpoint guidance.

## Companion plugin

This plugin works alongside [skillos-plugin](https://github.com/EvolvingAgentsLabs/skillos_plugin):
- `/skillos` creates agents and executes goals
- `/sysctl` evaluates, scores, evolves, and maintains what `/skillos` built

## License

Apache 2.0
