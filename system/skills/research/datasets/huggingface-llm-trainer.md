---
name: huggingface-llm-trainer
extends: research/base
domain: research
family: datasets
source: github:huggingface/skills/huggingface-llm-trainer
source_file: components/skills/huggingface-llm-trainer/SKILL.md
version: 1.0.0
tools: [Bash, Read, Write]
---

# Hugging Face LLM Trainer

Fine-tune LLMs using the Hugging Face Trainer API with support for LoRA/PEFT,
configurable training loops, and model saving.

## Source

Wraps `components/skills/huggingface-llm-trainer/SKILL.md` (sourced from `huggingface/skills`).

> **Note**: This skill runs GPU-intensive training. Verify hardware availability before
> invoking. Token cost is HIGH due to long-running Bash executions.

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **SFT training** | Supervised fine-tuning with Trainer API |
| **LoRA / PEFT** | Parameter-efficient fine-tuning |
| **Training config** | Generate `TrainingArguments` from requirements |
| **Dataset prep** | Format dataset for instruction tuning |
| **Model save** | Save adapter weights + full model |
| **Evaluation** | Run eval loop and report metrics |

---

## Protocol

### Step 1 — Prepare Training Config

Collect requirements:
- Base model (e.g., `meta-llama/Llama-3.2-1B`)
- Dataset name or path
- Training objective (SFT / instruction-tuning / DPO)
- Hardware: GPU VRAM available
- Target: adapter only (LoRA) or full fine-tune

### Step 2 — Dataset Formatting

```python
python3 - <<'EOF'
from datasets import load_dataset

# Load and format for instruction tuning
dataset = load_dataset("json", data_files="input/train.json", split="train")

def format_prompt(example):
    return {
        "text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
    }

dataset = dataset.map(format_prompt)
dataset.save_to_disk("output/formatted_dataset")
print(f"Formatted {len(dataset)} examples")
EOF
```

### Step 3 — LoRA Fine-Tuning

```python
python3 - <<'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_from_disk
import torch

model_name = "meta-llama/Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Training args
args = TrainingArguments(
    output_dir="output/checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    save_steps=100,
    logging_steps=10,
    report_to="none"
)

dataset = load_from_disk("output/formatted_dataset")

def tokenize(example):
    return tokenizer(example["text"], truncation=True, max_length=512)

tokenized = dataset.map(tokenize, batched=True)

trainer = Trainer(model=model, args=args, train_dataset=tokenized)
trainer.train()

# Save adapter
model.save_pretrained("output/lora_adapter")
tokenizer.save_pretrained("output/lora_adapter")
print("Training complete. Adapter saved to output/lora_adapter/")
EOF
```

---

## Hardware Recommendations

| VRAM | Strategy |
|------|---------|
| < 8 GB | LoRA r=4, 4-bit quantization (bitsandbytes) |
| 8–16 GB | LoRA r=16, fp16 |
| 16–24 GB | LoRA r=64 or full fine-tune small model |
| > 24 GB | Full fine-tune, DeepSpeed ZeRO-2 |

---

## Dependencies

```bash
pip install transformers peft datasets accelerate bitsandbytes trl
```

---

## Output Convention

Checkpoints → `projects/[Project]/output/checkpoints/`
Final adapter → `projects/[Project]/output/lora_adapter/`
Training log → `projects/[Project]/output/training_log.json`
