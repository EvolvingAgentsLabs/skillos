"""Context compaction for SkillOS — ported from claw-code's compact.rs pattern.

Prevents unbounded message growth by summarizing older messages
when token estimates exceed a threshold, while preserving recent context.
Supports optional LLM-powered summarization via async compact_messages_async().
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable


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


async def _summarize_with_llm(
    messages: list[dict],
    llm_fn: Callable[[str, str], Awaitable[str]],
) -> str:
    """Summarize using LLM. llm_fn: async (prompt, system) -> str."""
    transcript = "\n".join(
        f"[{m.get('role')}]: {str(m.get('content', ''))[:500]}"
        for m in messages
    )
    prompt = (
        "Summarize this conversation into 3-5 bullet points. "
        "Preserve key decisions, tool results, errors encountered.\n\n"
        f"Conversation ({len(messages)} messages):\n{transcript}"
    )
    try:
        return (await llm_fn(prompt, "Output only bullet points.")).strip()
    except Exception:
        return _summarize_messages(messages)  # fallback


async def compact_messages_async(
    messages: list[dict],
    config: CompactionConfig,
    llm_fn: Callable[[str, str], Awaitable[str]] | None = None,
) -> tuple[list[dict], str]:
    """Async compact with optional LLM summarization.

    If llm_fn is provided and there are enough messages, uses LLM for
    semantic summarization. Otherwise falls back to text truncation.
    """
    if not should_compact(messages, config):
        return messages, ""

    keep_from = max(0, len(messages) - config.preserve_recent_messages)
    removed = messages[:keep_from]
    preserved = messages[keep_from:]

    if llm_fn and len(removed) >= 4:
        summary = await _summarize_with_llm(removed, llm_fn)
    else:
        summary = _summarize_messages(removed)

    continuation = [{
        "role": "system",
        "content": (
            "Session continues. Prior context:\n\n"
            f"{summary}\n\n"
            "Recent messages preserved. Continue without recapping."
        ),
    }]
    return continuation + preserved, summary
