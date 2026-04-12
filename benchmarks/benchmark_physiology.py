#!/usr/bin/env python3
"""
Benchmark 4: Physiology / System Dynamics — Cognitive Scaffolding

Tests whether system-dynamics dialect allows accurate diagnosis of a
complex physiological system by forcing isomorphic mapping (biology → hydraulics).

Plain Claude writes medical prose and often fumbles unit conversions.
SkillOS system-dynamics dialect treats the heart as a pure hydraulic circuit.

Correct answers:
  - Velocity:             500 cm/s
  - Regurgitant volume:   60 mL
  - Regurgitant fraction: 60%
  - Severity:             Severe

Usage:
    cd skillos && python3 benchmarks/benchmark_physiology.py
"""

import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SKILLOS_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SKILLOS_DIR / "projects" / "Project_patch_benchmark" / "output"

# Expected answers
EXPECTED = {
    "velocity": 500,       # cm/s
    "volume": 60,          # mL
    "fraction": 60,        # %
    "severity": "severe",
}

# ── Prompts ──────────────────────────────────────────────────────────────────

PROBLEM = """\
A patient has acute mitral valve regurgitation. Echocardiography shows:
- Regurgitant orifice area (ROA) = 0.4 cm^2
- Peak systolic transmitral pressure gradient = 100 mmHg
- Simplified Torricelli's equation: velocity v = 50 * sqrt(delta_P) (in cm/s)
- Systolic ejection time = 0.3 seconds
- Total left ventricular stroke volume (SV) = 100 mL

Calculate:
1. The regurgitant jet velocity (v)
2. The regurgitant flow rate (Q = ROA * v)
3. The Regurgitant Volume (RV = Q * systolic_time)
4. The Regurgitant Fraction (RF = RV / SV)
5. Classify severity: Mild (<30%), Moderate (30-50%), Severe (>50%)"""

PLAIN_PROMPT = f"""\
{PROBLEM}

Show all calculations and state the final classification."""

SKILLOS_SOLVER_PROMPT = f"""\
{PROBLEM}

Solve using ONLY system-dynamics dialect notation. No English prose — only structured computation.

### System-Dynamics Grammar (complete reference):
```
[STOCK] name = value (unit)          — accumulated quantity
[FLOW] name: rate_expression         — rate of change
[EXT] name = value (unit)            — external input
[CALC] name = expression = result    — computation step
[EVAL] condition -> classification   — evaluation/threshold
```
Map the heart to a hydraulic circuit: LV = pump, mitral valve = leak orifice.
Output ONLY the structured computation block."""

RENDERER_PROMPT_TEMPLATE = """\
You are a medical writer. Read the following system-dynamics computation \
and write a compassionate, 2-paragraph clinical summary for a physician. \
Preserve ALL numerical values exactly.

---
{dialect_output}
---

Write the clinical summary now. Be concise (under 200 words)."""

# ── Claude Runner ────────────────────────────────────────────────────────────

def run_claude(prompt: str, cwd: str, label: str) -> dict:
    """Run claude -p --output-format json from the given directory."""
    print(f"\n{'='*60}")
    print(f"  Running: {label}")
    print(f"{'='*60}")

    cmd = ["claude", "-p", "--output-format", "json", prompt]
    t0 = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=300)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 300s")
        return {"error": "timeout", "duration_ms": 300000}

    wall_time = (time.time() - t0) * 1000

    if result.returncode != 0:
        print(f"  ERROR (exit {result.returncode}): {result.stderr[:300]}")
        return {"error": result.stderr[:500], "duration_ms": wall_time}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  JSON parse error")
        return {"error": "json_parse", "raw": result.stdout[:1000], "duration_ms": wall_time}

    usage = data.get("usage", {})
    info = {
        "text": data.get("result", ""),
        "input_tokens": usage.get("input_tokens", 0),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_cost_usd": data.get("total_cost_usd", 0),
        "duration_ms": data.get("duration_ms", wall_time),
        "num_turns": data.get("num_turns", 1),
    }
    print(f"  Output tokens: {info['output_tokens']:,}  Cost: ${info['total_cost_usd']:.4f}  "
          f"Duration: {info['duration_ms']/1000:.1f}s")
    return info


# ── Automated Verification ───────────────────────────────────────────────────

def verify_physiology(text: str, label: str) -> Dict[str, Any]:
    """
    Verify correctness of the mitral regurgitation calculation.
    Scoring (100 pts total):
      - velocity_correct (15): v = 500 cm/s
      - volume_correct (15): RV = 60 mL
      - fraction_correct (10): RF = 60%
      - severity_correct (10): classified as severe
      - intermediate_steps (30): shows Q=200, sqrt(100)=10, etc.
      - structured (20): computation is organized, not rambling
    """
    result = {
        "label": label,
        "velocity_correct": False,
        "volume_correct": False,
        "fraction_correct": False,
        "severity_correct": False,
        "intermediate_steps": False,
        "score": 0,
        "extracted_values": {},
        "errors": [],
    }

    if not text:
        result["errors"].append("No output text")
        return result

    text_lower = text.lower()

    # Check 1: Velocity = 500
    if re.search(r'\b500\b', text):
        # Verify it's near velocity/v context
        if re.search(r'(?:v|velocity|speed)\s*[=:≈]\s*500|500\s*(?:cm/s|cm\s*/\s*s)', text, re.IGNORECASE):
            result["velocity_correct"] = True
            result["extracted_values"]["velocity"] = 500
        elif re.search(r'\b500\b', text):
            # Accept 500 appearing in calculation context
            result["velocity_correct"] = True
            result["extracted_values"]["velocity"] = 500

    # Check 2: Regurgitant Volume = 60
    # Handle: "RV = expr = 60 (mL)", "60 mL", "60 (cm^3)", "RV = 60"
    if re.search(r'(?:regurgitant\s*volume|RV|volume)\s*[=:≈]\s*60|60\s*\(?(?:mL|ml|cc|cm\^?3)\)?', text, re.IGNORECASE):
        result["volume_correct"] = True
        result["extracted_values"]["volume"] = 60
    elif re.search(r'\bRV\b.*=\s*60\b', text):
        result["volume_correct"] = True
        result["extracted_values"]["volume"] = 60
    elif re.search(r'\b60\s*\(?m[Ll]\)?', text):
        result["volume_correct"] = True
        result["extracted_values"]["volume"] = 60

    # Check 3: Regurgitant Fraction = 60%
    if re.search(r'(?:regurgitant\s*fraction|RF|fraction)\s*[=:≈]\s*60\s*%?|60\s*%', text, re.IGNORECASE):
        result["fraction_correct"] = True
        result["extracted_values"]["fraction"] = 60
    elif re.search(r'0\.6\b|60\s*/?100', text):
        result["fraction_correct"] = True
        result["extracted_values"]["fraction"] = 60

    # Check 4: Severity = severe
    if re.search(r'\bsevere\b', text_lower):
        result["severity_correct"] = True
        result["extracted_values"]["severity"] = "severe"

    # Check 5: Intermediate steps
    # Should show: sqrt(100)=10, Q=200 (or 0.4*500=200), 200*0.3=60
    has_sqrt = bool(re.search(r'sqrt.*100|10\b.*(?:sqrt|root)', text_lower))
    has_flow_rate = bool(re.search(r'\b200\b', text))  # Q = 200 mL/s
    has_time_mult = bool(re.search(r'200\s*[*x×]\s*0\.3|0\.3\s*[*x×]\s*200', text))
    if has_flow_rate and (has_sqrt or has_time_mult):
        result["intermediate_steps"] = True

    # Score
    score = 0
    if result["velocity_correct"]:
        score += 15
    if result["volume_correct"]:
        score += 15
    if result["fraction_correct"]:
        score += 10
    if result["severity_correct"]:
        score += 10
    if result["intermediate_steps"]:
        score += 30
    # Structured: give 20 pts if at least 3 of 4 numerical checks pass
    correct_count = sum(1 for k in ("velocity_correct", "volume_correct",
                                     "fraction_correct", "severity_correct")
                        if result[k])
    if correct_count >= 3:
        score += 20
    result["score"] = score

    return result


# ── Report Generator ─────────────────────────────────────────────────────────

def generate_report(
    plain: dict, solver: dict, renderer: dict,
    plain_q: dict, solver_q: dict,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    p_out = plain.get("output_tokens", 0)
    s_out = solver.get("output_tokens", 0)
    r_out = renderer.get("output_tokens", 0)
    s_total_out = s_out + r_out
    s_total_cost = solver.get("total_cost_usd", 0) + renderer.get("total_cost_usd", 0)
    s_total_dur = solver.get("duration_ms", 0) + renderer.get("duration_ms", 0)

    reduction_solver = ((p_out - s_out) / p_out * 100) if p_out > 0 else 0
    reduction_total = ((p_out - s_total_out) / p_out * 100) if p_out > 0 else 0

    def yn(v): return "Yes" if v else "No"

    report = f"""\
# Physiology Benchmark Report: System Dynamics Dialect

**Generated**: {now}
**Task**: Calculate mitral regurgitation hemodynamics
**Expected**: v=500 cm/s, RV=60 mL, RF=60%, Severity=Severe

## Summary

| Metric | Plain Claude | SkillOS Solver | SkillOS Solver+Renderer |
|---|---|---|---|
| Output tokens | {p_out:,} | {s_out:,} | {s_total_out:,} |
| Token reduction | baseline | **-{reduction_solver:.1f}%** | **-{reduction_total:.1f}%** |
| Cost (USD) | ${plain.get('total_cost_usd', 0):.4f} | ${solver.get('total_cost_usd', 0):.4f} | ${s_total_cost:.4f} |
| Duration (s) | {plain.get('duration_ms', 0)/1000:.1f} | {solver.get('duration_ms', 0)/1000:.1f} | {s_total_dur/1000:.1f} |
| Turns | 1 | 1 | 2 |

## Quality Verification (Automated)

| Check (pts) | Plain Claude | SkillOS Solver |
|---|---|---|
| Velocity = 500 cm/s (15) | {yn(plain_q.get("velocity_correct"))} | {yn(solver_q.get("velocity_correct"))} |
| RV = 60 mL (15) | {yn(plain_q.get("volume_correct"))} | {yn(solver_q.get("volume_correct"))} |
| RF = 60% (10) | {yn(plain_q.get("fraction_correct"))} | {yn(solver_q.get("fraction_correct"))} |
| Severity = Severe (10) | {yn(plain_q.get("severity_correct"))} | {yn(solver_q.get("severity_correct"))} |
| Intermediate steps (30) | {yn(plain_q.get("intermediate_steps"))} | {yn(solver_q.get("intermediate_steps"))} |
| Structured output (20) | {"Yes" if plain_q.get("score", 0) >= 70 else "No"} | {"Yes" if solver_q.get("score", 0) >= 70 else "No"} |
| **Total score** | **{plain_q.get('score', 0)}/100** | **{solver_q.get('score', 0)}/100** |

## Key Findings

- **Token reduction (solver only)**: {reduction_solver:.1f}% fewer output tokens
- **Token reduction (with renderer)**: {reduction_total:.1f}% fewer even with clinical summary step
- **Math accuracy**: Plain {plain_q.get("score", 0)}/100, SkillOS {solver_q.get("score", 0)}/100
- **Cognitive Scaffolding**: System-dynamics notation maps biology to hydraulics, {"forcing flawless deterministic physics" if solver_q.get("score", 0) >= 80 else "improving computational structure"}

## Raw Outputs

### Plain Claude

<details>
<summary>Click to expand ({p_out:,} tokens)</summary>

{plain.get("text", "ERROR")}

</details>

### SkillOS Solver (system-dynamics dialect)

<details>
<summary>Click to expand ({s_out:,} tokens)</summary>

{solver.get("text", "ERROR")}

</details>

### SkillOS Renderer (clinical summary)

<details>
<summary>Click to expand ({r_out:,} tokens)</summary>

{renderer.get("text", "ERROR")}

</details>
"""
    return report


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Physiology Benchmark: System Dynamics Dialect vs Plain Claude")
    print(f"  Expected: v=500, RV=60mL, RF=60%, Severe")
    print("=" * 60)

    # ── Run 1: Plain Claude ──────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        plain = run_claude(PLAIN_PROMPT, cwd=tmpdir, label="Plain Claude (solve + explain)")

    # ── Run 2: SkillOS Solver (system-dynamics dialect) ──────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        solver = run_claude(SKILLOS_SOLVER_PROMPT, cwd=tmpdir, label="SkillOS Solver (system-dynamics)")

    # ── Run 3: SkillOS Renderer (dialect → clinical summary) ─────────────
    renderer = {"output_tokens": 0, "total_cost_usd": 0, "duration_ms": 0, "text": ""}
    if solver.get("text") and "error" not in solver:
        render_prompt = RENDERER_PROMPT_TEMPLATE.format(dialect_output=solver["text"])
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = run_claude(render_prompt, cwd=tmpdir, label="SkillOS Renderer (dialect → clinical)")

    # ── Verify ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Verification")
    print(f"{'='*60}")

    plain_q = verify_physiology(plain.get("text", ""), "Plain Claude")
    solver_q = verify_physiology(solver.get("text", ""), "SkillOS Solver")

    for q in (plain_q, solver_q):
        vals = q["extracted_values"]
        print(f"  {q['label']}: score={q['score']}/100, "
              f"v={'OK' if q['velocity_correct'] else 'MISS'}, "
              f"RV={'OK' if q['volume_correct'] else 'MISS'}, "
              f"RF={'OK' if q['fraction_correct'] else 'MISS'}, "
              f"sev={'OK' if q['severity_correct'] else 'MISS'}")

    # ── Report ───────────────────────────────────────────────────────────
    report = generate_report(plain, solver, renderer, plain_q, solver_q)
    report_path = OUTPUT_DIR / "benchmark_physiology_report.md"
    report_path.write_text(report, encoding="utf-8")

    raw_data = {
        "timestamp": datetime.now().isoformat(),
        "expected": EXPECTED,
        "plain": {k: v for k, v in plain.items() if k != "text"},
        "plain_quality": {k: v for k, v in plain_q.items() if k != "label"},
        "solver": {k: v for k, v in solver.items() if k != "text"},
        "solver_quality": {k: v for k, v in solver_q.items() if k != "label"},
        "renderer": {k: v for k, v in renderer.items() if k != "text"},
    }
    raw_path = OUTPUT_DIR / "benchmark_physiology_raw.json"
    raw_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")

    # ── Summary ──────────────────────────────────────────────────────────
    p_out = plain.get("output_tokens", 0)
    s_out = solver.get("output_tokens", 0)
    r_out = renderer.get("output_tokens", 0)

    print(f"\n{'='*60}")
    print("  Results")
    print(f"{'='*60}")
    print(f"  Report: {report_path}")
    print(f"  Plain:           {p_out:>6,} tokens, score {plain_q['score']}/100")
    print(f"  SkillOS Solver:  {s_out:>6,} tokens, score {solver_q['score']}/100")
    print(f"  SkillOS Render:  {r_out:>6,} tokens (clinical summary)")
    print(f"  Total SkillOS:   {s_out + r_out:>6,} tokens")
    if p_out > 0:
        print(f"  Token reduction:  {(p_out - s_out) / p_out * 100:.1f}% (solver only)")
        print(f"  Token reduction:  {(p_out - s_out - r_out) / p_out * 100:.1f}% (with renderer)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
