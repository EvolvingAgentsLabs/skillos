"""Context compaction for SkillOS — ported from claw-code's compact.rs pattern.

Prevents unbounded message growth by summarizing older messages
when token estimates exceed a threshold, while preserving recent context.
Supports optional LLM-powered summarization via async compact_messages_async().
"""

from __future__ import annotations

import asyncio
import warnings
from dataclasses import dataclass
from typing import Awaitable, Callable

# ── Model context-window registry ────────────────────────────────
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # Qwen via OpenRouter
    "qwen/qwen3.6-plus:free": 32_000,
    "qwen/qwen3-plus": 32_000,
    # Gemini
    "gemini-2.5-flash": 1_048_576,
    "gemini-2.5-pro": 1_048_576,
    "gemini-2.0-flash": 1_048_576,
    # Gemma 4 via Ollama
    "gemma4": 128_000,
    "gemma4:e2b": 128_000,
    "gemma4:e4b": 128_000,
    "gemma4:26b": 256_000,
    "gemma4:31b": 256_000,
    # Gemma 4 via OpenRouter
    "google/gemma-4-26b-a4b-it": 131_072,
}

DEFAULT_COMPACTION_RATIO = 0.70   # compact at 70 % of context window
MIN_COMPACTION_THRESHOLD = 8_000  # never compact below this floor


@dataclass
class CompactionConfig:
    """Controls when and how message lists are compacted."""
    preserve_recent_messages: int = 4
    max_estimated_tokens: int = 10_000

    def configure_for_model(self, model_name: str) -> None:
        """Set *max_estimated_tokens* from the model's context window.

        Unknown models keep the current default.
        """
        window = MODEL_CONTEXT_WINDOWS.get(model_name)
        if window is not None:
            self.max_estimated_tokens = max(
                MIN_COMPACTION_THRESHOLD,
                int(window * DEFAULT_COMPACTION_RATIO),
            )
        # else: keep the default 10_000


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
    if messages and messages[0].get("role") == "system":
        warnings.warn(
            "compact_messages received a system prompt as messages[0]. "
            "The system prompt should be prepended at call time, not stored "
            "in the conversation list — compaction will erase it.",
            stacklevel=2,
        )

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
    if messages and messages[0].get("role") == "system":
        warnings.warn(
            "compact_messages_async received a system prompt as messages[0]. "
            "The system prompt should be prepended at call time, not stored "
            "in the conversation list — compaction will erase it.",
            stacklevel=2,
        )

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
