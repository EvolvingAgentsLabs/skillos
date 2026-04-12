#!/usr/bin/env python3
"""
Dialect Benchmark: SkillOS vs Plain Claude Code

Runs the same microservice cascade failure problem through:
  1. Plain Claude (from temp dir, no CLAUDE.md)
  2. SkillOS with dialects (from skillos/, CLAUDE.md auto-loaded)

Then scores both outputs via an independent judge (from temp dir)
and generates a markdown comparison report.

Usage:
    cd skillos && python3 benchmark_dialects.py
"""

import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

SKILLOS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILLOS_DIR / "projects" / "Project_dialect_benchmark" / "output"

# ── Problem Statement (shared by both runs) ──────────────────────────────────

PROBLEM = """\
Analyze this microservice architecture and identify design flaws:

Service A (API Gateway) receives requests and routes to Service B (Order Service).
Service B calls Service C (Inventory Service) and Service D (Payment Service) in parallel.
If Service C or Service D fails, Service B retries up to 3 times with 2-second backoff.
Service B has a 10-second timeout for each downstream call.
Under load, Service C response times increase from 200ms to 8 seconds.
Service A has a 30-second timeout for requests to Service B.
There is no circuit breaker.

Specifically:
1. Identify the root cause of cascade failures under load
2. Model the system dynamics (stocks, flows, feedback loops)
3. State the retry condition with zero ambiguity (boolean logic)
4. Prove that the current design leads to resource exhaustion
5. Propose constraints for the fix
6. Create an execution plan for implementing the fix"""

# ── SkillOS prompt wraps the problem in a scenario execution ─────────────────

SKILLOS_PROMPT = """\
Execute the Dialect Benchmark scenario from scenarios/Dialect_Benchmark.md.

The scenario analyzes this microservice architecture for design flaws:

Service A (API Gateway) receives requests and routes to Service B (Order Service).
Service B calls Service C (Inventory Service) and Service D (Payment Service) in parallel.
If Service C or Service D fails, Service B retries up to 3 times with 2-second backoff.
Service B has a 10-second timeout for each downstream call.
Under load, Service C response times increase from 200ms to 8 seconds.
Service A has a 30-second timeout for requests to Service B.
There is no circuit breaker.

For each deliverable, use the dialect specified in the scenario:
1. Root cause diagnosis — formal-proof dialect (GIVEN:/DERIVE:/QED with [BY rule])
2. System dynamics model — system-dynamics dialect ([STOCK], [FLOW], [FB+], [FB-])
3. Retry condition — boolean-logic dialect (explicit parenthesization, boolean operators)
4. Resource exhaustion proof — formal-proof dialect (step-by-step numeric derivation)
5. Fix constraints — constraint-dsl dialect (C[N][severity] with thresholds)
6. Implementation plan — exec-plan dialect (@plan, P[N], dep=, verify:, success:)

Produce all 6 deliverables using the correct dialect notation. Do NOT write prose — use the compressed dialect forms only."""

# ── Quality Rubric ───────────────────────────────────────────────────────────

RUBRIC = """\
You are an independent judge scoring a technical analysis of a microservice cascade failure.

Score the following output on these criteria (100 points total):

1. Feedback loop identified (25 pts)
   - 25: Explicitly identified as a reinforcing/positive feedback loop (retries -> more load -> more timeouts -> more retries)
   - 12: Mentioned that retries cause problems but did not identify the reinforcing loop structure
   - 0: Feedback loop not identified

2. Retry condition unambiguous (20 pts)
   - 20: Boolean expression with explicit parenthesization showing exactly when retries fire
   - 10: Condition stated but grouping or precedence is ambiguous
   - 0: Retry condition not clearly stated

3. Logical derivation complete (20 pts)
   - 20: Every step of the resource exhaustion argument cites a rule or premise; no logical jumps
   - 10: Derivation present with some unstated assumptions or skipped steps
   - 0: Conclusion asserted without derivation

4. Constraints actionable (15 pts)
   - 15: Formal constraints with numeric thresholds and severity levels
   - 7: Constraints described in prose without specific thresholds
   - 0: No constraints proposed

5. Execution plan structured (10 pts)
   - 10: Phases with explicit dependencies and verification criteria
   - 5: Steps listed without dependency ordering
   - 0: Vague suggestions only

6. System model accurate (10 pts)
   - 10: Correct identification of stocks, flows, and feedback loops with proper polarity
   - 5: Partial elements (some stocks or flows, but incomplete)
   - 0: No system model

IMPORTANT: Score ONLY based on the content. Do not give bonus points for formatting.

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{"feedback_loop": <0|12|25>, "retry_condition": <0|10|20>, "logical_derivation": <0|10|20>, "constraints": <0|7|15>, "execution_plan": <0|5|10>, "system_model": <0|5|10>, "notes": "<brief explanation of scoring>"}"""


def run_claude(prompt: str, cwd: str, label: str) -> dict:
    """Run claude -p --output-format json from the given directory."""
    print(f"\n{'='*60}")
    print(f"  Running: {label}")
    print(f"  CWD: {cwd}")
    print(f"{'='*60}")

    cmd = ["claude", "-p", "--output-format", "json", prompt]
    t0 = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300,  # 5 min max
        )
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 300s")
        return {"error": "timeout", "duration_ms": 300000}

    wall_time = (time.time() - t0) * 1000

    if result.returncode != 0:
        print(f"  ERROR (exit {result.returncode})")
        print(f"  stderr: {result.stderr[:500]}")
        return {"error": result.stderr[:500], "duration_ms": wall_time}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  JSON parse error. Raw output length: {len(result.stdout)}")
        return {"error": "json_parse", "raw": result.stdout[:1000], "duration_ms": wall_time}

    usage = data.get("usage", {})
    input_tok = usage.get("input_tokens", 0)
    cache_create = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    output_tok = usage.get("output_tokens", 0)
    cost = data.get("total_cost_usd", 0)
    duration = data.get("duration_ms", wall_time)
    num_turns = data.get("num_turns", 1)
    text = data.get("result", "")

    print(f"  Input tokens:  {input_tok:,}")
    print(f"  Cache create:  {cache_create:,}")
    print(f"  Cache read:    {cache_read:,}")
    print(f"  Output tokens: {output_tok:,}")
    print(f"  Cost:          ${cost:.4f}")
    print(f"  Duration:      {duration/1000:.1f}s")
    print(f"  Turns:         {num_turns}")
    print(f"  Output length: {len(text)} chars")

    return {
        "text": text,
        "input_tokens": input_tok,
        "cache_creation_input_tokens": cache_create,
        "cache_read_input_tokens": cache_read,
        "output_tokens": output_tok,
        "total_cost_usd": cost,
        "duration_ms": duration,
        "num_turns": num_turns,
    }


def judge_quality(output_text: str, label: str) -> dict:
    """Score output quality via independent Claude call from temp dir."""
    print(f"\n  Judging: {label}...")

    prompt = f"{RUBRIC}\n\n--- BEGIN OUTPUT ---\n{output_text}\n--- END OUTPUT ---"

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ["claude", "-p", "--output-format", "json", prompt]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            print(f"    Judge timeout")
            return {"error": "timeout"}

        if result.returncode != 0:
            print(f"    Judge error: {result.stderr[:200]}")
            return {"error": result.stderr[:200]}

        try:
            data = json.loads(result.stdout)
            judge_text = data.get("result", "")
        except json.JSONDecodeError:
            print(f"    Judge JSON parse error")
            return {"error": "json_parse"}

    # Extract the JSON scores from the judge's response
    # The judge may wrap it in markdown code blocks, so strip those
    cleaned = judge_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        scores = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        import re
        match = re.search(r'\{[^}]+\}', judge_text, re.DOTALL)
        if match:
            try:
                scores = json.loads(match.group())
            except json.JSONDecodeError:
                print(f"    Could not parse judge scores from: {judge_text[:300]}")
                return {"error": "parse", "raw": judge_text[:500]}
        else:
            print(f"    No JSON found in judge response: {judge_text[:300]}")
            return {"error": "no_json", "raw": judge_text[:500]}

    total = sum(v for k, v in scores.items() if k != "notes" and isinstance(v, (int, float)))
    scores["total"] = total
    print(f"    Score: {total}/100")
    return scores


def generate_report(plain: dict, skillos: dict, plain_scores: dict, skillos_scores: dict) -> str:
    """Generate markdown comparison report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    p_out = plain.get("output_tokens", 0)
    s_out = skillos.get("output_tokens", 0)
    p_total = plain_scores.get("total", 0)
    s_total = skillos_scores.get("total", 0)

    # Token efficiency: quality per 1000 output tokens
    p_eff = (p_total / p_out * 1000) if p_out > 0 else 0
    s_eff = (s_total / s_out * 1000) if s_out > 0 else 0

    # Output token reduction
    token_reduction = ((p_out - s_out) / p_out * 100) if p_out > 0 else 0

    # Quality delta
    quality_delta = s_total - p_total

    criteria = [
        ("Feedback loop identified", "feedback_loop", 25),
        ("Retry condition unambiguous", "retry_condition", 20),
        ("Logical derivation complete", "logical_derivation", 20),
        ("Constraints actionable", "constraints", 15),
        ("Execution plan structured", "execution_plan", 10),
        ("System model accurate", "system_model", 10),
    ]

    criteria_rows = ""
    for name, key, max_pts in criteria:
        pv = plain_scores.get(key, "?")
        sv = skillos_scores.get(key, "?")
        criteria_rows += f"| {name} | {pv}/{max_pts} | {sv}/{max_pts} |\n"

    report = f"""\
# Dialect Benchmark Report

**Generated**: {now}
**Task**: Microservice Cascade Failure Analysis

## Summary

| Metric | Plain Claude | SkillOS + Dialects | Delta |
|---|---|---|---|
| Output tokens | {p_out:,} | {s_out:,} | {token_reduction:+.1f}% |
| Input tokens | {plain.get('input_tokens', 0):,} | {skillos.get('input_tokens', 0):,} | — |
| Cache creation | {plain.get('cache_creation_input_tokens', 0):,} | {skillos.get('cache_creation_input_tokens', 0):,} | — |
| Cost (USD) | ${plain.get('total_cost_usd', 0):.4f} | ${skillos.get('total_cost_usd', 0):.4f} | ${skillos.get('total_cost_usd', 0) - plain.get('total_cost_usd', 0):+.4f} |
| Duration (s) | {plain.get('duration_ms', 0)/1000:.1f} | {skillos.get('duration_ms', 0)/1000:.1f} | — |
| Turns | {plain.get('num_turns', 0)} | {skillos.get('num_turns', 0)} | — |
| **Quality score** | **{p_total}/100** | **{s_total}/100** | **{quality_delta:+d}** |
| Token efficiency (quality/ktok) | {p_eff:.1f} | {s_eff:.1f} | {s_eff - p_eff:+.1f} |

## Quality Breakdown

| Criterion | Plain | SkillOS |
|---|---|---|
{criteria_rows}
## Judge Notes

**Plain Claude**: {plain_scores.get('notes', 'N/A')}

**SkillOS + Dialects**: {skillos_scores.get('notes', 'N/A')}

## Key Findings

- **Output token reduction**: {token_reduction:.1f}% fewer output tokens with SkillOS
- **Quality delta**: {quality_delta:+d} points ({'+' if quality_delta > 0 else ''}{quality_delta/100*100:.0f}% of scale)
- **Token efficiency**: SkillOS achieves {s_eff:.1f} quality per 1k output tokens vs {p_eff:.1f} for plain ({s_eff/p_eff:.1f}x better)

## Raw Outputs

### Plain Claude Output

<details>
<summary>Click to expand ({p_out:,} output tokens)</summary>

{plain.get('text', 'ERROR: No output')}

</details>

### SkillOS + Dialects Output

<details>
<summary>Click to expand ({s_out:,} output tokens)</summary>

{skillos.get('text', 'ERROR: No output')}

</details>
"""
    return report


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Dialect Benchmark: SkillOS vs Plain Claude Code")
    print("=" * 60)

    # ── Run 1: Plain Claude (no CLAUDE.md) ────────────────────────────────
    with tempfile.TemporaryDirectory() as tmpdir:
        plain = run_claude(PROBLEM, cwd=tmpdir, label="Plain Claude (no SkillOS context)")

    if "error" in plain:
        print(f"\nPlain run failed: {plain['error']}")
        print("Continuing with available data...")

    # ── Run 2: SkillOS with dialects ──────────────────────────────────────
    skillos = run_claude(SKILLOS_PROMPT, cwd=str(SKILLOS_DIR), label="SkillOS + Dialects")

    if "error" in skillos:
        print(f"\nSkillOS run failed: {skillos['error']}")
        print("Continuing with available data...")

    # ── Judge both outputs ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Quality Judging (independent Claude calls)")
    print(f"{'='*60}")

    plain_scores = {"total": 0}
    skillos_scores = {"total": 0}

    if plain.get("text"):
        plain_scores = judge_quality(plain["text"], "Plain Claude")
    else:
        print("  Skipping plain judge (no output)")

    if skillos.get("text"):
        skillos_scores = judge_quality(skillos["text"], "SkillOS + Dialects")
    else:
        print("  Skipping SkillOS judge (no output)")

    # ── Generate report ───────────────────────────────────────────────────
    report = generate_report(plain, skillos, plain_scores, skillos_scores)

    report_path = OUTPUT_DIR / "benchmark_report.md"
    report_path.write_text(report, encoding="utf-8")

    # Also save raw JSON data for later analysis
    raw_data = {
        "timestamp": datetime.now().isoformat(),
        "plain": {k: v for k, v in plain.items() if k != "text"},
        "plain_text_len": len(plain.get("text", "")),
        "plain_scores": plain_scores,
        "skillos": {k: v for k, v in skillos.items() if k != "text"},
        "skillos_text_len": len(skillos.get("text", "")),
        "skillos_scores": skillos_scores,
    }
    raw_path = OUTPUT_DIR / "benchmark_raw.json"
    raw_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print("  Results")
    print(f"{'='*60}")
    print(f"  Report: {report_path}")
    print(f"  Raw data: {raw_path}")
    print()

    p_out = plain.get("output_tokens", 0)
    s_out = skillos.get("output_tokens", 0)
    p_total = plain_scores.get("total", 0)
    s_total = skillos_scores.get("total", 0)

    print(f"  Plain:   {p_out:>6,} output tokens, {p_total}/100 quality")
    print(f"  SkillOS: {s_out:>6,} output tokens, {s_total}/100 quality")

    if p_out > 0:
        reduction = (p_out - s_out) / p_out * 100
        print(f"  Token reduction: {reduction:.1f}%")
    if p_out > 0 and s_out > 0:
        p_eff = p_total / p_out * 1000
        s_eff = s_total / s_out * 1000
        print(f"  Efficiency: {s_eff:.1f} vs {p_eff:.1f} quality/ktok ({s_eff/p_eff:.1f}x)")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
