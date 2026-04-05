---
name: claude-api
extends: content/base
domain: content
family: meta
source: github:anthropics/skills/claude-api
source_file: components/skills/claude-api/SKILL.md
version: 1.0.0
tools: [Bash]
---

# Claude API Skill

Use the Anthropic Claude API / SDK to make sub-LLM calls — enables parallel inference, cost optimization,
and specialized model routing within SkillOS pipelines.

## Source

Wraps `components/skills/claude-api/SKILL.md` (sourced from `anthropics/skills`).

---

## When to Use

- Fan-out: run the same prompt against multiple inputs in parallel
- Specialization: route sub-tasks to a smaller/cheaper model
- Batch processing: process large datasets with controlled rate limiting
- Structured output: use `response_format` for guaranteed JSON responses
- Multi-turn: manage conversation history programmatically

---

## Protocol

### Basic Single Call

```python
python3 - <<'EOF'
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-haiku-4-5-20251001",   # cheapest for sub-tasks
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Summarize this in 2 sentences: ..."}
    ]
)
print(message.content[0].text)
EOF
```

### Parallel Fan-out

```python
python3 - <<'EOF'
import anthropic
import concurrent.futures
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

inputs = ["topic A", "topic B", "topic C"]

def analyze(topic):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": f"Analyze: {topic}"}]
    )
    return topic, msg.content[0].text

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    results = dict(ex.map(lambda t: analyze(t), inputs))

for topic, analysis in results.items():
    print(f"=== {topic} ===\n{analysis}\n")
EOF
```

### Structured JSON Output

```python
python3 - <<'EOF'
import anthropic, json, os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Return a JSON object with keys: summary, keywords (list), sentiment"
    }]
)
# Parse JSON from response
text = message.content[0].text
# Strip markdown code fences if present
if "```" in text:
    text = text.split("```")[1].lstrip("json").strip()
data = json.loads(text)
print(json.dumps(data, indent=2))
EOF
```

---

## Model Selection Guide

| Model | Use case | Cost |
|-------|---------|------|
| `claude-haiku-4-5-20251001` | Simple extraction, classification | Lowest |
| `claude-sonnet-4-6` | Complex reasoning, synthesis | Medium |
| `claude-opus-4-6` | Hardest tasks, full context | Highest |

---

## Environment Setup

```bash
export ANTHROPIC_API_KEY="your-key-here"
pip install anthropic
```

Check key is set:
```bash
python3 -c "import os; print('Key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

---

## Examples

**"Classify these 100 support tickets in parallel"**
→ Fan-out with ThreadPoolExecutor, Haiku model, batch size 10

**"Extract structured data from each document in input/"**
→ For-loop with JSON output format, save results to output/extracted.json
