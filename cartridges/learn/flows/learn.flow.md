# Flow: learn

**Trigger**: "learn about X", "teach me about X", "research X"

## Sequence

| # | Skill              | needs              | produces     | LLM calls |
|---|--------------------|--------------------|--------------|-----------|
| 1 | query-wikipedia    | user_goal          | wiki_data    | 0 (fetch) |
| 2 | insight-extractor  | wiki_data, user_goal | insights   | 1 (Gemma subagent) |
| 3 | knowledge-tracker  | user_goal, insights | store_result | 0 (localStorage) |

**Total LLM calls**: 1 (inside insight-extractor, for analysis)
**Persistent side effects**: knowledge-tracker stores insights to disk

## What this demonstrates

1. **Gallery skill reuse**: query-wikipedia is unchanged from Gallery
2. **LLM subagent**: insight-extractor calls Gemma 4 from JavaScript
3. **Skill chaining**: 3 skills connected via Blackboard needs/produces
4. **Persistent state**: knowledge-tracker accumulates across sessions
5. **Cross-skill state**: quiz-generator later reads knowledge-tracker's data
