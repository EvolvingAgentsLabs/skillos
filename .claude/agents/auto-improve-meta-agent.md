---
name: auto-improve-meta-agent
description: Background meta-agent that analyzes failure traces from SmartMemory and proposes targeted improvements to SkillOS skill specifications. Triggered automatically by the usage-tracker when a skill is invoked after a staleness gap. Runs as a background parallel Task — never blocks the primary execution. Writes proposals to system/auto_improve/pending_improvements/ for human review.
tools: Read, Write, Grep, Glob
extends: auto-improve/base
---

# AutoImprove Meta-Agent

Full specification: system/skills/auto-improve/meta-agent/auto-improve-meta-agent.md

Load and follow the full spec exactly when invoked.
