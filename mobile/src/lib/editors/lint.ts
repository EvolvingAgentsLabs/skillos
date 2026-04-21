/**
 * Pure lint functions for the three editor families. Each returns a
 * `@codemirror/lint` Diagnostic[] with line + column info derived from the
 * parser error messages.
 */

import type { Diagnostic } from "@codemirror/lint";
import yaml from "js-yaml";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

export function lintYaml(doc: string): Diagnostic[] {
  if (!doc.trim()) return [];
  try {
    yaml.load(doc);
    return [];
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    const m = /line (\d+), column (\d+)/.exec(msg);
    if (m) {
      const line = Math.max(1, Number(m[1]));
      const col = Math.max(1, Number(m[2]));
      const from = lineColToOffset(doc, line, col);
      return [
        {
          from,
          to: from + 1,
          severity: "error",
          message: msg,
        },
      ];
    }
    return [{ from: 0, to: doc.length, severity: "error", message: msg }];
  }
}

export function lintJsonSchema(doc: string): Diagnostic[] {
  if (!doc.trim()) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(doc);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    const m = /position (\d+)/.exec(msg);
    if (m) {
      const pos = Math.min(Number(m[1]), doc.length);
      return [
        { from: pos, to: Math.min(pos + 1, doc.length), severity: "error", message: msg },
      ];
    }
    return [{ from: 0, to: doc.length, severity: "error", message: msg }];
  }
  try {
    const ajv = new Ajv2020({ strict: false });
    addFormats(ajv as unknown as Parameters<typeof addFormats>[0]);
    ajv.compile(parsed as object);
    return [];
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return [{ from: 0, to: doc.length, severity: "error", message: msg }];
  }
}

export function lintMarkdownFrontmatter(
  doc: string,
  requiredKeys: string[] = [],
): Diagnostic[] {
  if (!doc.startsWith("---")) {
    return [
      {
        from: 0,
        to: Math.min(3, doc.length),
        severity: "warning",
        message: "missing YAML frontmatter — start the file with `---`",
      },
    ];
  }
  const end = doc.indexOf("\n---", 3);
  if (end === -1) {
    return [
      {
        from: 0,
        to: 3,
        severity: "error",
        message: "unclosed frontmatter — needs a trailing `---`",
      },
    ];
  }
  const block = doc.slice(3, end);
  try {
    const fm = yaml.load(block) as unknown;
    if (!fm || typeof fm !== "object") {
      return [
        {
          from: 0,
          to: end + 4,
          severity: "warning",
          message: "frontmatter is empty",
        },
      ];
    }
    const record = fm as Record<string, unknown>;
    const missing = requiredKeys.filter((k) => !(k in record));
    if (missing.length > 0) {
      return [
        {
          from: 0,
          to: end + 4,
          severity: "error",
          message: `frontmatter missing required key(s): ${missing.join(", ")}`,
        },
      ];
    }
    return [];
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return [
      { from: 3, to: end + 4, severity: "error", message: `YAML parse error: ${msg}` },
    ];
  }
}

function lineColToOffset(doc: string, line: number, col: number): number {
  let lineIdx = 1;
  let offset = 0;
  while (lineIdx < line && offset < doc.length) {
    const nl = doc.indexOf("\n", offset);
    if (nl === -1) return doc.length;
    offset = nl + 1;
    lineIdx++;
  }
  return Math.min(offset + col - 1, doc.length);
}
