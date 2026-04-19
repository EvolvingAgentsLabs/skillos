---
name: knowledge-tracker
description: Persistent knowledge base that accumulates insights across sessions. Tracks what you've learned, builds connections between topics.
---

# Knowledge Tracker

A stateful skill that maintains a personal knowledge base across sessions.
Every time you research a topic, the insights are stored and cross-referenced.
Over time, the knowledge base grows and reveals connections between topics.

## Instructions

Call the `run_js` tool with:
- data: A JSON string with fields:
  - action: "store" | "query" | "connections" | "stats" | "export"
  - For "store": topic (string), insights (object from insight-extractor)
  - For "query": topic (string) — retrieves stored knowledge
  - For "connections": (no args) — shows cross-topic connections
  - For "stats": (no args) — shows learning statistics
  - For "export": (no args) — exports full knowledge base
