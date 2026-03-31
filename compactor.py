"""Context compaction for SkillOS — ported from claw-code's compact.rs pattern.

Prevents unbounded message growth by summarizing older messages
when token estimates exceed a threshold, while preserving recent context.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompactionConfig:
    """Controls when and how message lists are compacted."""
    preserve_recent_messages: int = 4
    max_estimated_tokens: int = 10_000


def estimate_tokens(messages: list[dict]) -> int:
    """Estimate token count using char/4 heuristic (same as claw-code)."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content) // 4 + 1
        elif isinstance(content, list):
            # Handle multi-part content (vision messages, etc.)
            for part in content:
                if isinstance(part, dict):
                    total += len(str(part.get("text", ""))) // 4 + 1
                else:
                    total += len(str(part)) // 4 + 1
    return total


def should_compact(messages: list[dict], config: CompactionConfig) -> bool:
    """Check if messages exceed thresholds and need compaction."""
    return (
        len(messages) > config.preserve_recent_messages
        and estimate_tokens(messages) >= config.max_estimated_tokens
    )


def compact_messages(
    messages: list[dict], config: CompactionConfig
) -> tuple[list[dict], str]:
    """Compact older messages into a summary, preserving recent ones.

    Returns (compacted_messages, summary_text).
    If compaction is not needed, returns the original messages unchanged.
    """
    if not should_compact(messages, config):
        return messages, ""

    keep_from = max(0, len(messages) - config.preserve_recent_messages)
    removed = messages[:keep_from]
    preserved = messages[keep_from:]

    summary = _summarize_messages(removed)
    continuation = (
        "This session continues from an earlier conversation. "
        f"Summary of prior context:\n\n{summary}\n\n"
        "Recent messages are preserved verbatim. "
        "Continue without recapping."
    )

    compacted = [{"role": "system", "content": continuation}] + preserved
    return compacted, summary


def _summarize_messages(messages: list[dict]) -> str:
    """Create a concise textual summary of a message list."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, str):
            text = content[:160]
            if len(content) > 160:
                text += "..."
        else:
            text = str(content)[:160] + "..."
        lines.append(f"- {role}: {text}")
    return "\n".join(lines)
