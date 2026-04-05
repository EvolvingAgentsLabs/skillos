---
name: huggingface-llm-trainer
version: 1.0.0
source_repo: huggingface/skills
source_path: skills/huggingface-llm-trainer/
license: Apache-2.0
installed_by: SkillOS
description: Fine-tune LLMs using the HF Trainer API with LoRA/PEFT support
tools: [Bash, Read, Write]
dependencies:
  - transformers>=4.40.0
  - peft>=0.10.0
  - datasets>=2.0.0
  - accelerate>=0.27.0
  - trl>=0.8.0
---

# Hugging Face LLM Trainer (Source)

Raw skill source from `huggingface/skills`.
SkillOS-integrated version: `system/skills/research/datasets/huggingface-llm-trainer.md`

## What This Skill Does

Fine-tune large language models using the HF ecosystem:
- Supervised Fine-Tuning (SFT) with Trainer API
- LoRA / PEFT for parameter-efficient training (fits on consumer GPUs)
- Configurable training arguments (learning rate, epochs, batch size)
- Automatic checkpoint saving and resumable training
- Model and adapter weight saving to disk

## Quick Start

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
lora_cfg = LoraConfig(r=16, lora_alpha=32, task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, lora_cfg)
# ... set up dataset, TrainingArguments, Trainer, then trainer.train()
```

## Install Dependencies

```bash
pip install transformers peft datasets accelerate trl bitsandbytes
```
