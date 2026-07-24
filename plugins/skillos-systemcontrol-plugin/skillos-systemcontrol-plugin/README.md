# SkillOS System Control Plugin

Control plane for SkillOS projects. Security audits, agent scoring, controlled evolution, and lifecycle management.

## Install

```bash
/plugin install /path/to/skillos_systemcontrol_plugin/skillos-systemcontrol-plugin
```

## Usage

```bash
/sysctl "your control-plane goal here"
```

## Modes

| Mode | Keywords | What It Does |
|------|----------|--------------|
| AUDIT | audit, security, scan | Security scan of agent prompts and traces |
| SCORE | score, evaluate, rank | Score agents using 7-type failure taxonomy |
| EVOLVE | evolve, improve, optimize | Propose controlled improvements |
| PRUNE | prune, delete, deprecate | Identify agents for removal |
| COMPACT | compact, merge, memory | Compact traces and merge strategies |
| REPORT | report, health, status | Full health report |

## License

Apache 2.0 — See [LICENSE](../LICENSE) for details.
