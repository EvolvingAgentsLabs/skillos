/**
 * knowledge-tracker — Persistent knowledge base across sessions.
 *
 * Demonstrates two Gallery-impossible features:
 * 1. Persistent state that survives across process restarts
 * 2. A skill that accumulates knowledge over time (compounding)
 *
 * The knowledge base grows with each research session. Topics are
 * cross-referenced by shared key facts and connections.
 */

const KB_KEY = 'knowledge_tracker_db';

function loadKB() {
  const raw = localStorage.getItem(KB_KEY);
  return raw ? JSON.parse(raw) : { topics: {}, meta: { created: new Date().toISOString(), queries: 0 } };
}

function saveKB(kb) {
  kb.meta.updated = new Date().toISOString();
  localStorage.setItem(KB_KEY, JSON.stringify(kb));
}

window['ai_edge_gallery_get_result'] = async (dataStr) => {
  try {
    const input = JSON.parse(dataStr);
    const action = input.action || 'stats';
    const kb = loadKB();

    if (action === 'store') {
      const topic = (input.topic || '').toLowerCase().trim();
      if (!topic) return JSON.stringify({ error: 'No topic provided' });

      let insights = input.insights;
      if (typeof insights === 'string') {
        try { insights = JSON.parse(insights); } catch { insights = { summary: insights }; }
      }

      // Store or merge with existing topic
      const existing = kb.topics[topic];
      if (existing) {
        // Merge: append new facts, update summary
        const existingFacts = new Set(existing.key_facts || []);
        (insights.key_facts || []).forEach(f => existingFacts.add(f));
        existing.key_facts = [...existingFacts];
        if (insights.summary) existing.summary = insights.summary;
        if (insights.connections) {
          const existingConn = new Set(existing.connections || []);
          insights.connections.forEach(c => existingConn.add(c));
          existing.connections = [...existingConn];
        }
        if (insights.surprises) {
          existing.surprises = [...(existing.surprises || []), ...insights.surprises];
        }
        existing.visit_count = (existing.visit_count || 1) + 1;
        existing.last_visited = new Date().toISOString();
      } else {
        kb.topics[topic] = {
          summary: insights.summary || '',
          key_facts: insights.key_facts || [],
          connections: insights.connections || [],
          surprises: insights.surprises || [],
          difficulty: insights.difficulty || 'unknown',
          first_learned: new Date().toISOString(),
          last_visited: new Date().toISOString(),
          visit_count: 1,
        };
      }

      saveKB(kb);
      const topicData = kb.topics[topic];
      const totalTopics = Object.keys(kb.topics).length;
      return JSON.stringify({
        result: `Stored knowledge on "${topic}" (${topicData.key_facts.length} facts, ` +
                `${topicData.connections.length} connections). ` +
                `Knowledge base now has ${totalTopics} topic${totalTopics !== 1 ? 's' : ''}.` +
                (topicData.visit_count > 1 ? ` (visited ${topicData.visit_count} times — knowledge merged)` : '')
      });

    } else if (action === 'query') {
      const topic = (input.topic || '').toLowerCase().trim();
      if (!topic) return JSON.stringify({ error: 'No topic to query' });

      const data = kb.topics[topic];
      if (!data) {
        // Fuzzy search
        const matches = Object.keys(kb.topics).filter(t => t.includes(topic) || topic.includes(t));
        if (matches.length > 0) {
          return JSON.stringify({
            result: `No exact match for "${topic}". Did you mean: ${matches.join(', ')}?`
          });
        }
        return JSON.stringify({ result: `No knowledge stored on "${topic}" yet. Try researching it first.` });
      }

      kb.meta.queries++;
      saveKB(kb);

      let report = `## ${topic}\n`;
      report += `**Summary:** ${data.summary}\n\n`;
      report += `**Key Facts:**\n${(data.key_facts || []).map(f => `- ${f}`).join('\n')}\n\n`;
      if (data.connections && data.connections.length > 0) {
        report += `**Related Topics:** ${data.connections.join(', ')}\n\n`;
      }
      if (data.surprises && data.surprises.length > 0) {
        report += `**Surprising Insights:**\n${data.surprises.map(s => `- ${s}`).join('\n')}\n\n`;
      }
      report += `*Difficulty: ${data.difficulty} | Visited ${data.visit_count}x | First learned: ${data.first_learned.split('T')[0]}*`;

      return JSON.stringify({ result: report });

    } else if (action === 'connections') {
      const topics = Object.keys(kb.topics);
      if (topics.length < 2) {
        return JSON.stringify({ result: `Need at least 2 topics to find connections. Currently have ${topics.length}.` });
      }

      // Build connection graph
      const graph = {};
      for (const topic of topics) {
        const conns = kb.topics[topic].connections || [];
        for (const conn of conns) {
          const connLower = conn.toLowerCase();
          // Check if connection target is also a stored topic
          const match = topics.find(t => t === connLower || connLower.includes(t) || t.includes(connLower));
          if (match && match !== topic) {
            const edge = [topic, match].sort().join(' <-> ');
            graph[edge] = (graph[edge] || 0) + 1;
          }
        }

        // Also check for shared facts across topics
        const facts = new Set((kb.topics[topic].key_facts || []).map(f => f.toLowerCase()));
        for (const other of topics) {
          if (other === topic) continue;
          const otherFacts = (kb.topics[other].key_facts || []).map(f => f.toLowerCase());
          const shared = otherFacts.filter(f => {
            for (const myFact of facts) {
              // Simple word overlap check
              const words = f.split(/\s+/);
              const myWords = new Set(myFact.split(/\s+/));
              const overlap = words.filter(w => myWords.has(w) && w.length > 4).length;
              if (overlap >= 2) return true;
            }
            return false;
          });
          if (shared.length > 0) {
            const edge = [topic, other].sort().join(' <-> ');
            graph[edge] = (graph[edge] || 0) + shared.length;
          }
        }
      }

      const edges = Object.entries(graph).sort((a, b) => b[1] - a[1]);
      if (edges.length === 0) {
        return JSON.stringify({ result: `No connections found between ${topics.length} topics yet. Research more related topics to build connections.` });
      }

      let report = `## Knowledge Graph (${topics.length} topics, ${edges.length} connections)\n\n`;
      for (const [edge, strength] of edges) {
        report += `- ${edge} (strength: ${strength})\n`;
      }
      return JSON.stringify({ result: report });

    } else if (action === 'stats') {
      const topics = Object.keys(kb.topics);
      const totalFacts = topics.reduce((sum, t) => sum + (kb.topics[t].key_facts || []).length, 0);
      const totalConnections = topics.reduce((sum, t) => sum + (kb.topics[t].connections || []).length, 0);

      let report = `## Knowledge Base Stats\n\n`;
      report += `- **Topics:** ${topics.length}\n`;
      report += `- **Total Facts:** ${totalFacts}\n`;
      report += `- **Total Connections:** ${totalConnections}\n`;
      report += `- **Queries Made:** ${kb.meta.queries || 0}\n`;
      report += `- **Created:** ${(kb.meta.created || '').split('T')[0]}\n\n`;

      if (topics.length > 0) {
        report += `**Topics:** ${topics.join(', ')}`;
      }
      return JSON.stringify({ result: report });

    } else if (action === 'export') {
      return JSON.stringify({ result: JSON.stringify(kb, null, 2) });

    } else {
      return JSON.stringify({ error: `Unknown action: ${action}. Use: store, query, connections, stats, export` });
    }

  } catch (e) {
    return JSON.stringify({ error: `Knowledge tracker error: ${e.message}` });
  }
};
