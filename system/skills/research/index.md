---
domain: research
type: domain-index
version: 1.0.0
total_skills: 4
base: system/skills/research/base.md
---

# Research Domain Index

Use for: web research, academic paper access, dataset discovery, model fine-tuning.

## Skills

| Skill | Family | subagent_type | Manifest | Token Cost |
|-------|--------|---------------|---------|-----------|
| web-research-agent | web | web-research-agent | system/skills/research/web/web-research-agent.manifest.md | medium |
| huggingface-papers | papers | _(tool)_ | system/skills/research/papers/huggingface-papers.manifest.md | low |
| huggingface-datasets | datasets | _(tool)_ | system/skills/research/datasets/huggingface-datasets.manifest.md | low |
| huggingface-llm-trainer | datasets | _(tool)_ | system/skills/research/datasets/huggingface-llm-trainer.manifest.md | high |

## Invoke When

- Agent needs to research a topic from live web sources
- Looking for academic papers or ML research on Hugging Face
- Need to load or explore a dataset for training or analysis
- Fine-tuning an LLM with the HF Trainer pipeline

## Base Behaviors

Inherited from `system/skills/research/base.md`:
- Source attribution required for all claims
- Research quality tiers (PRIMARY / SECONDARY / TERTIARY)
- Deduplication against local cache before fetching
- Hallucination guard: only cite verified sources
