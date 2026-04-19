/**
 * insight-extractor — A JS skill that calls Gemma 4 as a subagent.
 *
 * This is the key differentiator from Gallery: the skill doesn't just
 * compute — it REASONS by calling the LLM for analysis.
 *
 * Input:  { text, topic?, depth? }
 * Output: { result: JSON string with insights }
 *
 * Uses: __skillos.llm.chatJSON() for structured LLM output
 */

window['ai_edge_gallery_get_result'] = async (dataStr) => {
  try {
    const input = JSON.parse(dataStr);
    const text = input.text || input.wiki_data || '';
    const topic = input.topic || input.user_goal || 'this topic';
    const depth = input.depth || 'quick';

    if (!text || text.length < 20) {
      return JSON.stringify({ error: 'Text too short to analyze. Provide at least 20 characters.' });
    }

    // Check if LLM is available
    if (!__skillos || !__skillos.llm || !__skillos.llm.available) {
      // Fallback: extract insights without LLM (basic heuristic)
      return JSON.stringify({
        result: JSON.stringify({
          topic: topic,
          method: 'heuristic (no LLM available)',
          key_facts: extractBasicFacts(text),
          summary: text.substring(0, 300) + '...',
        }, null, 2)
      });
    }

    // Use Gemma 4 as a subagent to analyze the text
    const prompt = depth === 'deep'
      ? `Analyze this text about "${topic}" in depth. Extract:
1. A one-paragraph summary (2-3 sentences)
2. Exactly 5 key facts (short, specific, verifiable statements)
3. 3 connections to related topics (things a learner should explore next)
4. 2 surprising or non-obvious insights
5. A difficulty rating: beginner/intermediate/advanced

Text to analyze:
${text.substring(0, 4000)}

Respond with valid JSON only. No markdown. Schema:
{
  "summary": "string",
  "key_facts": ["string", ...],
  "connections": ["string", ...],
  "surprises": ["string", ...],
  "difficulty": "string"
}`
      : `Extract 3 key facts and a one-sentence summary from this text about "${topic}".

Text: ${text.substring(0, 3000)}

Respond with valid JSON only: {"summary": "...", "key_facts": ["...", "...", "..."]}`;

    const insights = await __skillos.llm.chatJSON(prompt, null, {
      temperature: 0.2,
      max_tokens: 1000,
    });

    // Enrich with metadata
    insights.topic = topic;
    insights.method = 'gemma4-subagent';
    insights.analyzed_chars = text.length;
    insights.depth = depth;
    insights.timestamp = new Date().toISOString();

    return JSON.stringify({ result: JSON.stringify(insights, null, 2) });

  } catch (e) {
    return JSON.stringify({ error: `Insight extraction failed: ${e.message}` });
  }
};

// Fallback: basic fact extraction without LLM
function extractBasicFacts(text) {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20);
  return sentences.slice(0, 3).map(s => s.trim());
}
