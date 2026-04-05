---
skill_id: research/datasets/huggingface-llm-trainer
name: huggingface-llm-trainer
type: tool
domain: research
family: datasets
extends: research/base
version: 1.0.0
source: github:huggingface/skills/huggingface-llm-trainer
description: Fine-tune LLMs using the Hugging Face Trainer API with configurable training loops
capabilities: [llm-fine-tuning, HF-trainer, LoRA, PEFT, training-config, model-save]
tools_required: [Bash, Read, Write]
token_cost: high
reliability: 80%
invoke_when: [fine-tune LLM, train model, LoRA, PEFT, HuggingFace trainer, SFT, instruction tuning]
full_spec: system/skills/research/datasets/huggingface-llm-trainer.md
---
