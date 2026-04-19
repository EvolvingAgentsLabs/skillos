---
name: insight-extractor
description: Analyzes text using Gemma 4 and extracts structured insights, key facts, and connections.
---

# Insight Extractor

This skill takes raw text (e.g., a Wikipedia article) and uses Gemma 4 as a
subagent to extract structured insights. It demonstrates a JS skill that
**reasons** — something Gallery skills cannot do with the on-device model.

## Instructions

Call the `run_js` tool with:
- data: A JSON string with fields:
  - text: the raw text to analyze
  - topic: (optional) the topic name for context
  - depth: (optional) "quick" or "deep" (default: "quick")
