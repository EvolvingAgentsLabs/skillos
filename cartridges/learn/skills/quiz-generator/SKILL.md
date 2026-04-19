---
name: quiz-generator
description: Generates quiz questions from stored knowledge using Gemma 4 as a subagent. Tests comprehension of previously researched topics.
---

# Quiz Generator

This skill uses Gemma 4 to generate quiz questions from your knowledge base.
It reads stored insights and creates questions that test comprehension.
Demonstrates a JS skill that combines persistent state + LLM reasoning.

## Instructions

Call the `run_js` tool with:
- data: A JSON string with fields:
  - topic: the topic to quiz on (must have been researched first)
  - count: (optional) number of questions (default: 3)
  - style: (optional) "multiple_choice" | "true_false" | "open" (default: "multiple_choice")
