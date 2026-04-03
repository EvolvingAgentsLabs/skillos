---
skill_id: validation/security/skill-security-scan-agent
name: skill-security-scan-agent
type: agent
domain: validation
family: security
extends: validation/base
version: 1.0.0
description: >
  Antivirus-style security scanner for SkillOS. Analyzes incoming skill files
  before installation to detect prompt injection, tool overclaiming, exfiltration
  vectors, obfuscation, name spoofing, and supply chain attacks. Blocks malicious
  skills and warns on suspicious ones.
capabilities:
  - prompt-injection-detection
  - tool-overclaim-analysis
  - exfiltration-vector-scan
  - obfuscation-detection
  - name-spoof-detection
  - supply-chain-conflict-check
  - scan-report-generation
tools_required: [Read, Write, Grep, Glob]
subagent_type: validation-agent
token_cost: low
reliability: 95%
invoke_when:
  - skill install (pre-install gate)
  - skill update (re-scan on update)
  - on-demand security audit
  - suspicious skill detected
outputs:
  verdict: SAFE | WARNING | BLOCKED
  report_path: system/security/scan_reports/{skill_name}_{timestamp}.md
full_spec: system/skills/validation/security/skill-security-scan-agent.md
---
