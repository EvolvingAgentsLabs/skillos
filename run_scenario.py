#!/usr/bin/env python3
"""Generic scenario runner for SkillOS.

Replaces run_aorta_gemma.py and run_echoq_gemma.py with a single script
that uses the cognitive pipeline executor and strategy router.

Usage:
    python run_scenario.py scenarios/ProjectAortaScenario.md "quantum arterial navigation" \
        --provider gemma-openrouter --no-stream

    python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
        --provider gemma-openrouter --strategy cognitive_pipeline \
        --project-dir projects/Project_echo_q_gemma

    python run_scenario.py scenarios/ProjectAortaScenario.md "test" \
        --provider gemma-openrouter --strategy agentic --no-stream
"""
import argparse
import sys

sys.stdout.reconfigure(line_buffering=True)

from agent_runtime import AgentRuntime
from permission_policy import SKILLOS_AUTONOMOUS_POLICY, get_policy


def main():
    parser = argparse.ArgumentParser(
        description="Run a SkillOS scenario with automatic strategy routing.",
    )
    parser.add_argument(
        "scenario", help="Path to the scenario markdown file",
    )
    parser.add_argument(
        "context", help="Problem context string for the scenario",
    )
    parser.add_argument(
        "--provider", default="gemma-openrouter",
        help="Runtime provider (default: gemma-openrouter)",
    )
    parser.add_argument(
        "--strategy", default=None,
        choices=["agentic", "cognitive_pipeline", "pipeline"],
        help="Override the automatic strategy selection",
    )
    parser.add_argument(
        "--project-dir", default=None,
        help="Override the project output directory",
    )
    parser.add_argument(
        "--max-turns", type=int, default=10,
        help="Max turns for agentic strategy (default: 10)",
    )
    parser.add_argument(
        "--max-turns-per-step", type=int, default=5,
        help="Max turns per step for cognitive pipeline (default: 5)",
    )
    parser.add_argument(
        "--no-stream", action="store_true",
        help="Disable streaming output",
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Override manifest file path",
    )
    parser.add_argument(
        "--permission-policy", default=None,
        help="Permission policy name",
    )
    parser.add_argument(
        "--sandbox", default="local",
        choices=["local", "e2b"],
        help="Sandbox mode (default: local)",
    )
    args = parser.parse_args()

    policy = get_policy(args.permission_policy) if args.permission_policy else SKILLOS_AUTONOMOUS_POLICY

    rt = AgentRuntime(
        manifest_path=args.manifest,
        permission_policy=policy,
        provider=args.provider,
        stream=not args.no_stream,
        sandbox_mode=args.sandbox,
    )

    print(f"\nScenario: {args.scenario}")
    print(f"Context: {args.context}")
    print(f"Provider: {args.provider} (model: {rt.model})")
    if args.strategy:
        print(f"Strategy override: {args.strategy}")
    if args.project_dir:
        print(f"Project dir: {args.project_dir}")

    result = rt.execute_scenario(
        args.scenario,
        args.context,
        max_turns=args.max_turns,
        max_turns_per_step=args.max_turns_per_step,
        strategy_override=args.strategy,
        project_dir=args.project_dir,
    )

    print("\n" + "=" * 60)
    print("SCENARIO COMPLETE")
    print("=" * 60)
    print(f"Result length: {len(result)} chars")
    print(result[:3000])


if __name__ == "__main__":
    main()
