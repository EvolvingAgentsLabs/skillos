/**
 * Blackboard — TS port of
 * C:\evolvingagents\skillos\cartridge_runtime.py lines 47-190.
 *
 * Typed key-value store shared across subagents. Each entry carries metadata
 * (schema_ref, produced_by, description, created_at) surfaced to downstream
 * agents so they can interpret the data.
 *
 * Validation is pluggable: caller passes a `SchemaValidator` (typically ajv
 * wired up to the cartridge's schemas/ directory). If no validator is given
 * or `validate=false`, the put() call skips the check.
 */

import type {
  BlackboardEntry,
  BlackboardSnapshot,
  SchemaValidator,
  ValidationResult,
} from "./types";

export class Blackboard {
  private _entries = new Map<string, BlackboardEntry>();

  constructor(private readonly validator?: SchemaValidator) {}

  put(
    key: string,
    value: unknown,
    opts: {
      schema_ref?: string;
      produced_by?: string;
      description?: string;
      validate?: boolean;
    } = {},
  ): ValidationResult {
    const schema_ref = opts.schema_ref ?? "";
    const produced_by = opts.produced_by ?? "";
    const description = opts.description ?? "";
    const validate = opts.validate !== false;

    let result: ValidationResult = { ok: true, message: "ok" };
    if (validate && schema_ref && this.validator) {
      result = this.validator(value, schema_ref);
    }

    this._entries.set(key, {
      value,
      schema_ref,
      produced_by,
      description,
      created_at: new Date().toISOString(),
    });
    return result;
  }

  get(key: string): BlackboardEntry | undefined {
    return this._entries.get(key);
  }

  value<T = unknown>(key: string, fallback: T | undefined = undefined): T | undefined {
    const e = this._entries.get(key);
    return e !== undefined ? (e.value as T) : fallback;
  }

  has(key: string): boolean {
    return this._entries.has(key);
  }

  keys(): string[] {
    return Array.from(this._entries.keys());
  }

  snapshot(): BlackboardSnapshot {
    const out: BlackboardSnapshot = {};
    for (const [k, e] of this._entries) {
      out[k] = {
        value: e.value,
        schema_ref: e.schema_ref,
        produced_by: e.produced_by,
        description: e.description,
        created_at: e.created_at,
      };
    }
    return out;
  }

  bundle(keys: string[]): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    for (const k of keys) {
      const e = this._entries.get(k);
      if (e) out[k] = e.value;
    }
    return out;
  }

  describe(keys: string[]): string {
    const lines: string[] = [];
    for (const k of keys) {
      const e = this._entries.get(k);
      if (!e) continue;
      const desc = e.description || "(no description)";
      const origin = e.produced_by || "user";
      lines.push(`- \`${k}\` (from ${origin}): ${desc}`);
    }
    return lines.length > 0 ? lines.join("\n") : "(no inputs)";
  }
}
