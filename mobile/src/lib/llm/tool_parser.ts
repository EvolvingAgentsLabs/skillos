/**
 * Tool-call parser — TS port of
 * C:\evolvingagents\skillos\agent_runtime.py lines 865-1086 and 910-992.
 *
 * SkillOS cartridges emit tool calls in five shapes:
 *   A.  <tool_call name="x">{"a":1}</tool_call>
 *   A2. <tool_call name="x">{"a":1}     (unclosed — terminates at next tag / EOF)
 *   B.  <tool_call>{"a":1}</tool_call>  (name inferred from keys)
 *   C.  <tool_call>\nx\n{"a":1}\n</tool_call>  (name on first line)
 *   D.  ```json\n[{"tool_name":"x","parameters":{…}}]\n```
 *
 * Plus `<final_answer>…</final_answer>` for completion signaling.
 */

export interface ToolCall {
  name: string;
  args: string; // raw JSON-ish string; caller cleans + parses
}

export const TOOL_ALIASES: Record<string, string> = {
  run_agent: "delegate_to_agent",
};

// ────────────────────────────────────────────────────────────────────────
// Utilities
// ────────────────────────────────────────────────────────────────────────

export function extractTagContent(tag: string, text: string): string | null {
  const re = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, "m");
  const m = text.match(re);
  return m ? m[1].trim() : null;
}

/**
 * Return the first complete JSON object from text, ignoring trailing garbage.
 * Respects quoted strings and escape sequences. Port of _extract_json_object.
 */
export function extractJsonObject(text: string): string {
  const start = text.indexOf("{");
  if (start === -1) return text;
  let depth = 0;
  let inString = false;
  let escape = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (escape) {
      escape = false;
      continue;
    }
    if (c === "\\") {
      escape = true;
      continue;
    }
    if (c === '"') {
      inString = !inString;
      continue;
    }
    if (inString) continue;
    if (c === "{" || c === "[") depth++;
    else if (c === "}" || c === "]") {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return text;
}

/** Best-effort repair for JSON with unescaped quotes inside string values. */
export function repairJsonArgs(raw: string): Record<string, unknown> | null {
  let inner = raw.trim();
  if (!inner.startsWith("{") || !inner.endsWith("}")) return null;
  inner = inner.slice(1, -1).trim();

  const result: Record<string, unknown> = {};
  while (inner.length > 0) {
    const km = /^"([^"]+)"\s*:\s*/.exec(inner);
    if (!km) break;
    const key = km[1];
    inner = inner.slice(km[0].length);

    if (inner.startsWith('"')) {
      // String value. Find the first `"` whose lookahead is one of:
      //   `,\s*"`  (comma then next key)
      //   `}` (end of object)
      //   end-of-string (last value)
      // That's the healthy closing quote. Anything between is treated as
      // literal body even if it contains unescaped `"` characters.
      inner = inner.slice(1);
      let valEnd = -1;
      for (let j = 0; j < inner.length; j++) {
        if (inner[j] !== '"') continue;
        const after = inner.slice(j + 1);
        if (/^,\s*"/.test(after) || after.startsWith("}") || after.length === 0) {
          valEnd = j;
          break;
        }
      }
      if (valEnd < 0) break;
      result[key] = inner.slice(0, valEnd);
      inner = inner
        .slice(valEnd + 1)
        .replace(/^\s*,\s*/, "")
        .replace(/^\s+/, "");
    } else if (inner.startsWith("{")) {
      const nested = extractJsonObject(inner);
      try {
        result[key] = JSON.parse(nested);
      } catch {
        result[key] = nested;
      }
      inner = inner.slice(nested.length).replace(/^\s+|^,\s*/g, "");
    } else if (inner.startsWith("[")) {
      const nested = extractJsonObject(inner);
      try {
        result[key] = JSON.parse(nested);
      } catch {
        result[key] = nested;
      }
      inner = inner.slice(nested.length).replace(/^\s+|^,\s*/g, "");
    } else {
      const vm = /^([^,}]+)/.exec(inner);
      if (!vm) break;
      const rawVal = vm[1].trim();
      try {
        result[key] = JSON.parse(rawVal);
      } catch {
        result[key] = rawVal;
      }
      inner = inner.slice(vm[0].length).replace(/^\s+|^,\s*/g, "");
    }
  }
  return Object.keys(result).length > 0 ? result : null;
}

/** Guess a tool name from the shape of its JSON args. */
export function inferToolFromArgs(jsonStr: string): string | null {
  let args: Record<string, unknown>;
  try {
    const parsed = JSON.parse(jsonStr);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    args = parsed as Record<string, unknown>;
  } catch {
    return null;
  }
  const keys = new Set(Object.keys(args));
  if (keys.has("agent_name")) return "delegate_to_agent";
  if (keys.has("path") && keys.has("content")) return "write_file";
  if (keys.has("url")) return "web_fetch";
  if (keys.has("prompt")) return "call_llm";
  if (keys.has("pattern")) return "memory_search";
  if (keys.has("type") && keys.has("key") && keys.has("value")) return "memory_store";
  if (keys.has("type") && keys.has("key")) return "memory_recall";
  if (keys.has("path")) return "read_file";
  if (keys.has("query")) return "call_llm";
  return null;
}

function parseJsonArrayTools(response: string): ToolCall[] {
  const results: ToolCall[] = [];
  const fenceRe = /```json\s*\n([\s\S]*?)```/g;
  let candidates: string[] = [];
  for (const m of response.matchAll(fenceRe)) candidates.push(m[1]);
  if (candidates.length === 0) {
    const bareRe = /(\[[\s\S]*?\])/g;
    for (const m of response.matchAll(bareRe)) candidates.push(m[1]);
  }
  for (const candidate of candidates) {
    let parsed: unknown;
    try {
      parsed = JSON.parse(candidate.trim());
    } catch {
      continue;
    }
    if (!Array.isArray(parsed)) continue;
    for (const item of parsed) {
      if (!item || typeof item !== "object" || Array.isArray(item)) continue;
      const obj = item as Record<string, unknown>;
      let name = String(obj.tool_name ?? obj.tool_call ?? obj.name ?? "");
      const params = (obj.parameters ?? obj.params ?? obj.arguments ?? {}) as unknown;
      if (!name && params) name = inferToolFromArgs(JSON.stringify(params)) ?? "";
      if (name) results.push({ name, args: JSON.stringify(params) });
    }
  }
  return results;
}

// ────────────────────────────────────────────────────────────────────────
// Main entry
// ────────────────────────────────────────────────────────────────────────

export function parseToolCalls(response: string): ToolCall[] {
  const calls: ToolCall[] = [];

  // Format A: <tool_call name="x">{…}</tool_call>
  const reA = /<tool_call name="(.*?)">([\s\S]*?)<\/tool_call>/g;
  for (const m of response.matchAll(reA)) {
    calls.push({ name: m[1], args: m[2] });
  }
  if (calls.length > 0) return calls;

  // Format A2: <tool_call name="x">… (unclosed) — terminate at next <tool_call|<final_answer|EOF.
  const reA2 = /<tool_call name="(.*?)">([\s\S]*?)(?=<tool_call|<final_answer|$)/g;
  for (const m of response.matchAll(reA2)) {
    const name = m[1].trim();
    let body = m[2].trim();
    body = body.replace(/<\/tool_call>\s*$/, "").trim();
    if (name && body) calls.push({ name, args: body });
  }
  if (calls.length > 0) return calls;

  // Format B/C: <tool_call>…</tool_call>
  const reBC = /<tool_call>([\s\S]*?)<\/tool_call>/g;
  for (const m of response.matchAll(reBC)) {
    const body = m[1].trim();
    const inferred = inferToolFromArgs(body);
    if (inferred) {
      calls.push({ name: inferred, args: body });
    } else {
      const firstNl = body.indexOf("\n");
      if (firstNl > 0) {
        const first = body.slice(0, firstNl).trim();
        const rest = body.slice(firstNl + 1).trim();
        if (!first.startsWith("{") && rest.length > 0) {
          calls.push({ name: first, args: rest });
        }
      }
    }
  }
  if (calls.length > 0) return calls;

  // Format D: JSON array
  return parseJsonArrayTools(response);
}
