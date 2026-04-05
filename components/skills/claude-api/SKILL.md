---
name: claude-api
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/claude-api/
license: MIT
installed_by: SkillOS
description: Use the Anthropic Claude API / SDK for sub-LLM calls, parallel inference, structured output
tools: [Bash]
dependencies:
  - anthropic>=0.40.0
---

# Claude API Skill (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/meta/claude-api.md`

## What This Skill Does

Enables SkillOS agents to make programmatic calls to the Claude API:
- Sub-agent calls for parallel processing
- Cheaper model routing (Haiku for simple tasks)
- Structured JSON output via `response_format`
- Streaming responses for long-form generation
- Batch processing with rate-limit handling

## Quick Start

```python
import anthropic
client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(message.content[0].text)
```

## Install Dependencies

```bash
pip install anthropic
export ANTHROPIC_API_KEY="your-key"
```
