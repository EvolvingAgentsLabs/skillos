---
skill_id: validation/security/skill-security-scan-agent
name: skill-security-scan-agent
type: agent
domain: validation
family: security
extends: validation/base
version: 1.0.0
description: Antivirus-style security gate — scans skill files for prompt injection, name spoofing, tool overclaiming, exfiltration URLs, obfuscation, delegation bombs, frontmatter integrity, and supply chain conflicts
capabilities: [prompt-injection-scan, name-spoofing-check, tool-overclaiming-check, exfiltration-url-scan, obfuscation-detection, delegation-bomb-check, frontmatter-validation, supply-chain-check]
tools_required: [Read, Glob, Grep, Write]
subagent_type: skill-security-scan-agent
token_cost: medium
reliability: 95%
invoke_when: [skill install, skill update, security scan, security audit, before disk write of external skill]
full_spec: system/skills/validation/security/skill-security-scan-agent.md
---
