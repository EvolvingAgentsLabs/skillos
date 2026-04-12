#!/usr/bin/env python3
"""
Benchmark 3: Mathematics & Formal Proof — Cognitive Scaffolding

Tests whether formal-proof dialect eliminates arithmetic hallucinations
in a multi-step graph theory problem (spanning trees of K_{3,4}).

Plain Claude writes English paragraphs and often loses track of matrix arithmetic.
SkillOS formal-proof dialect forces step-by-step symbolic derivation.

Correct answer: 432 spanning trees (3^3 x 4^2 = 27 x 16 = 432).

Usage:
    cd skillos && python3 benchmark_math.py
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

SKILLOS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILLOS_DIR / "projects" / "Project_patch_benchmark" / "output"

CORRECT_ANSWER = 432

# ── Prompts ──────────────────────────────────────────────────────────────────

PROBLEM = """\
Calculate the exact number of spanning trees in a Complete Bipartite Graph K_{3,4} \
using the Matrix Tree Theorem.

You must:
1. Construct the full 7x7 Laplacian matrix L of K_{3,4} (rows/columns for vertices a1,a2,a3,b1,b2,b3,b4).
2. Find the cofactor L_11 by deleting the first row and first column (yielding a 6x6 matrix).
3. Calculate det(L_11) exactly — this equals the number of spanning trees.
4. State the final answer as a single integer."""

PLAIN_PROMPT = f"""\
{PROBLEM}

Show all work. Write your solution with full explanation."""

SKILLOS_SOLVER_PROMPT = f"""\
{PROBLEM}

Solve using ONLY formal-proof notation. No English prose — only structured derivation.

### Formal-Proof Grammar (complete reference):
```
GIVEN:
  P1: [premise]
  P2: [premise]
DERIVE:
  D1: [statement] [BY rule]
  D2: [statement] [BY rule]
QED: [conclusion]
```
Rules: definition, matrix_tree_theorem, cofactor_expansion, arithmetic, substitution.
Use exact numeric values at every step. Output ONLY the proof block."""

RENDERER_PROMPT_TEMPLATE = """\
You are a technical writer. Read the following formal proof notation and \
write a clear 2-paragraph explanation in plain English. Preserve ALL \
mathematical values exactly as given.

---
{dialect_output}
---

Write the explanation now. Be concise (under 200 words)."""

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

def verify_math(text: str, label: str) -> Dict[str, Any]:
    """
    Verify mathematical correctness of the K_{3,4} spanning tree solution.
    Scoring (100 pts total):
      - answer_correct (50): final answer is exactly 432
      - matrix_shown (10): mentions Laplacian matrix construction
      - cofactor_shown (10): mentions cofactor/minor/submatrix
      - determinant_shown (10): mentions determinant calculation
      - intermediate_values (20): shows 27, 16, or 3^3, 4^2
    """
    result = {
        "label": label,
        "answer_correct": False,
        "matrix_shown": False,
        "cofactor_shown": False,
        "determinant_shown": False,
        "intermediate_values": False,
        "score": 0,
        "extracted_answer": None,
        "errors": [],
    }

    if not text:
        result["errors"].append("No output text")
        return result

    text_lower = text.lower()

    # Check 1: Final answer is 432
    # Look for "432" in the text, ideally near "answer", "QED", "result", "spanning trees"
    if re.search(r'\b432\b', text):
        result["answer_correct"] = True
        result["extracted_answer"] = 432
    else:
        # Try to find any number near answer-like keywords
        answer_patterns = [
            r'(?:answer|result|total|QED|spanning trees)[^\d]*?(\d+)',
            r'(\d+)\s*(?:spanning trees)',
            r'=\s*(\d+)\s*$',
        ]
        for pat in answer_patterns:
            m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
            if m:
                result["extracted_answer"] = int(m.group(1))
                if int(m.group(1)) == 432:
                    result["answer_correct"] = True
                break
        if not result["answer_correct"]:
            result["errors"].append(
                f"Wrong answer: extracted {result['extracted_answer']}, expected 432"
            )

    # Check 2: Laplacian matrix mentioned
    if re.search(r'laplacian|degree\s*matrix|adjacency\s*matrix|\bL\s*=', text_lower):
        result["matrix_shown"] = True

    # Check 3: Cofactor/minor mentioned
    if re.search(r'cofactor|minor|L_\{?11\}?|delet.*first.*row|cross.*out', text_lower):
        result["cofactor_shown"] = True

    # Check 4: Determinant mentioned
    if re.search(r'determinant|det\s*\(|det\s*=|\bdet\b', text_lower):
        result["determinant_shown"] = True

    # Check 5: Intermediate values (27, 16, or 3^3, 4^2)
    has_27 = bool(re.search(r'\b27\b', text))
    has_16 = bool(re.search(r'\b16\b', text))
    has_3_cubed = bool(re.search(r'3\s*[\^*]\s*3|3\s*\*\*\s*3|3³', text))
    has_4_squared = bool(re.search(r'4\s*[\^*]\s*2|4\s*\*\*\s*2|4²', text))
    if (has_27 or has_3_cubed) and (has_16 or has_4_squared):
        result["intermediate_values"] = True

    # Score
    score = 0
    if result["answer_correct"]:
        score += 50
    if result["matrix_shown"]:
        score += 10
    if result["cofactor_shown"]:
        score += 10
    if result["determinant_shown"]:
        score += 10
    if result["intermediate_values"]:
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

    report = f"""\
# Math Benchmark Report: Formal Proof Dialect

**Generated**: {now}
**Task**: Calculate spanning trees of K_{{3,4}} via Matrix Tree Theorem
**Correct Answer**: {CORRECT_ANSWER}

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
| Answer = 432 (50) | {"YES" if plain_q.get("answer_correct") else f"NO ({plain_q.get('extracted_answer', '?')})"} | {"YES" if solver_q.get("answer_correct") else f"NO ({solver_q.get('extracted_answer', '?')})"} |
| Laplacian matrix (10) | {"Yes" if plain_q.get("matrix_shown") else "No"} | {"Yes" if solver_q.get("matrix_shown") else "No"} |
| Cofactor/minor (10) | {"Yes" if plain_q.get("cofactor_shown") else "No"} | {"Yes" if solver_q.get("cofactor_shown") else "No"} |
| Determinant calc (10) | {"Yes" if plain_q.get("determinant_shown") else "No"} | {"Yes" if solver_q.get("determinant_shown") else "No"} |
| Intermediate 27x16 (20) | {"Yes" if plain_q.get("intermediate_values") else "No"} | {"Yes" if solver_q.get("intermediate_values") else "No"} |
| **Total score** | **{plain_q.get('score', 0)}/100** | **{solver_q.get('score', 0)}/100** |

## Key Findings

- **Token reduction (solver only)**: {reduction_solver:.1f}% fewer output tokens
- **Token reduction (with renderer)**: {reduction_total:.1f}% fewer even with English translation step
- **Math accuracy**: Plain {"CORRECT" if plain_q.get("answer_correct") else "WRONG"}, SkillOS {"CORRECT" if solver_q.get("answer_correct") else "WRONG"}
- **Cognitive Scaffolding**: Formal-proof notation forces step-by-step computation, {"eliminating" if solver_q.get("answer_correct") and not plain_q.get("answer_correct") else "maintaining"} arithmetic accuracy

## Raw Outputs

### Plain Claude

<details>
<summary>Click to expand ({p_out:,} tokens)</summary>

{plain.get("text", "ERROR")}

</details>

### SkillOS Solver (formal-proof dialect)

<details>
<summary>Click to expand ({s_out:,} tokens)</summary>

{solver.get("text", "ERROR")}

</details>

### SkillOS Renderer (English translation)

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
    print("  Math Benchmark: Formal Proof Dialect vs Plain Claude")
    print(f"  Problem: Spanning trees of K_{{3,4}} (answer = {CORRECT_ANSWER})")
    print("=" * 60)

    # ── Run 1: Plain Claude ──────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        plain = run_claude(PLAIN_PROMPT, cwd=tmpdir, label="Plain Claude (solve + explain)")

    # ── Run 2: SkillOS Solver (formal-proof dialect) ─────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        solver = run_claude(SKILLOS_SOLVER_PROMPT, cwd=tmpdir, label="SkillOS Solver (formal-proof)")

    # ── Run 3: SkillOS Renderer (dialect → English) ──────────────────────
    renderer = {"output_tokens": 0, "total_cost_usd": 0, "duration_ms": 0, "text": ""}
    if solver.get("text") and "error" not in solver:
        render_prompt = RENDERER_PROMPT_TEMPLATE.format(dialect_output=solver["text"])
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = run_claude(render_prompt, cwd=tmpdir, label="SkillOS Renderer (dialect → English)")

    # ── Verify ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Verification")
    print(f"{'='*60}")

    plain_q = verify_math(plain.get("text", ""), "Plain Claude")
    solver_q = verify_math(solver.get("text", ""), "SkillOS Solver")

    for q in (plain_q, solver_q):
        print(f"  {q['label']}: answer={'CORRECT' if q['answer_correct'] else 'WRONG'} "
              f"(extracted={q['extracted_answer']}), score={q['score']}/100")

    # ── Report ───────────────────────────────────────────────────────────
    report = generate_report(plain, solver, renderer, plain_q, solver_q)
    report_path = OUTPUT_DIR / "benchmark_math_report.md"
    report_path.write_text(report, encoding="utf-8")

    raw_data = {
        "timestamp": datetime.now().isoformat(),
        "correct_answer": CORRECT_ANSWER,
        "plain": {k: v for k, v in plain.items() if k != "text"},
        "plain_quality": {k: v for k, v in plain_q.items() if k != "label"},
        "solver": {k: v for k, v in solver.items() if k != "text"},
        "solver_quality": {k: v for k, v in solver_q.items() if k != "label"},
        "renderer": {k: v for k, v in renderer.items() if k != "text"},
    }
    raw_path = OUTPUT_DIR / "benchmark_math_raw.json"
    raw_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")

    # ── Summary ──────────────────────────────────────────────────────────
    p_out = plain.get("output_tokens", 0)
    s_out = solver.get("output_tokens", 0)
    r_out = renderer.get("output_tokens", 0)

    print(f"\n{'='*60}")
    print("  Results")
    print(f"{'='*60}")
    print(f"  Report: {report_path}")
    print(f"  Plain:           {p_out:>6,} tokens, score {plain_q['score']}/100, "
          f"answer={'CORRECT' if plain_q['answer_correct'] else 'WRONG'}")
    print(f"  SkillOS Solver:  {s_out:>6,} tokens, score {solver_q['score']}/100, "
          f"answer={'CORRECT' if solver_q['answer_correct'] else 'WRONG'}")
    print(f"  SkillOS Render:  {r_out:>6,} tokens (English translation)")
    print(f"  Total SkillOS:   {s_out + r_out:>6,} tokens")
    if p_out > 0:
        print(f"  Token reduction:  {(p_out - s_out) / p_out * 100:.1f}% (solver only)")
        print(f"  Token reduction:  {(p_out - s_out - r_out) / p_out * 100:.1f}% (with renderer)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
