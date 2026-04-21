/**
 * Host-side bridge to the sandboxed skill iframe.
 *
 * Protocol (see public/iframe/skill-host.js for the receiver):
 *
 *   Host → iframe:
 *     { type: "load-skill",    id, skillName, source, state }
 *     { type: "run",           id, data, secret }
 *     { type: "llm-response",  id, ok, content, error }
 *     { type: "state-flushed", id }
 *
 *   Iframe → host:
 *     { type: "ready" }
 *     { type: "loaded",      id, ok, error? }
 *     { type: "result",      id, ok, result?, error?, webview?, image?, raw? }
 *     { type: "llm-request", id, prompt, options, mode }   mode ∈ "text" | "json"
 *     { type: "state-save",  skillName, key, value }
 *     { type: "log",         level, message }
 *
 * The bridge is a singleton: call `attachIframe(el, origin)` once from
 * SkillHostIframe.svelte, then `runSkill()` / `loadSkill()` from anywhere.
 */

import { getFileText } from "../storage/db";
import type { SkillDefinition } from "./skill_loader";
import { skillResultFromError, skillResultFromJson, type SkillResult } from "./skill_result";

export interface LLMProxy {
  /** Single-turn text completion. */
  chat(prompt: string, options: { system?: string; temperature?: number; max_tokens?: number }): Promise<string>;
  /** JSON-coerced completion (skill adds "Respond with JSON" suffix). */
  chatJSON(
    prompt: string,
    schema: unknown,
    options: { system?: string; temperature?: number; max_tokens?: number },
  ): Promise<unknown>;
}

export interface SkillStateStore {
  load(skillName: string): Promise<Record<string, unknown>>;
  save(skillName: string, key: string, value: unknown): Promise<void>;
}

export interface RunSkillOptions {
  data?: unknown;
  secret?: string;
  timeoutMs?: number;
}

type Pending<T> = {
  resolve: (v: T) => void;
  reject: (err: Error) => void;
  timer?: ReturnType<typeof setTimeout>;
};

const DEFAULT_TIMEOUT = 30_000;

class SkillHostBridge {
  private iframe: HTMLIFrameElement | null = null;
  private ready = false;
  private readyWaiters: Array<() => void> = [];
  private pending = new Map<string, Pending<unknown>>();
  private currentSkill: string | null = null;
  private currentSource = "";
  private llm: LLMProxy | null = null;
  private state: SkillStateStore = inMemoryStore();

  attachIframe(el: HTMLIFrameElement): void {
    if (this.iframe && this.iframe !== el) this.detach();
    this.iframe = el;
    window.addEventListener("message", this.onMessage);
  }

  detach(): void {
    window.removeEventListener("message", this.onMessage);
    this.iframe = null;
    this.ready = false;
  }

  setLLMProxy(proxy: LLMProxy | null): void {
    this.llm = proxy;
  }

  setStateStore(store: SkillStateStore): void {
    this.state = store;
  }

  /** Load a skill's source into the iframe. Pre-fetches state. */
  async loadSkill(skill: SkillDefinition): Promise<void> {
    await this.awaitReady();
    const source = await resolveSkillSource(skill);
    if (!source) throw new Error(`could not load source for skill "${skill.name}"`);

    const state = await this.state.load(skill.name);
    const id = newId();
    this.currentSkill = skill.name;
    this.currentSource = source;
    await this.request<{ ok: boolean; error?: string }>(
      id,
      { type: "load-skill", id, skillName: skill.name, source, state },
      10_000,
    ).then((res) => {
      if (!res.ok) throw new Error(res.error ?? "load-skill failed");
    });
  }

  /** Run the previously-loaded skill with the given data + optional secret. */
  async runSkill(skill: SkillDefinition, opts: RunSkillOptions = {}): Promise<SkillResult> {
    await this.awaitReady();
    if (this.currentSkill !== skill.name) {
      await this.loadSkill(skill);
    }
    const id = newId();
    const data =
      typeof opts.data === "string" ? opts.data : JSON.stringify(opts.data ?? {});
    try {
      const raw = await this.request<Record<string, unknown>>(
        id,
        { type: "run", id, data, secret: opts.secret ?? "" },
        opts.timeoutMs ?? DEFAULT_TIMEOUT,
      );
      if (raw && typeof raw === "object" && "error" in raw && typeof raw.error === "string") {
        return { ok: false, error: raw.error as string, raw };
      }
      return skillResultFromJson(raw);
    } catch (err) {
      return skillResultFromError(err);
    }
  }

  /** Test-only: return true if the iframe has signalled readiness. */
  isReady(): boolean {
    return this.ready;
  }

  // ────────────────────────────────────────────────────────────────────

  private onMessage = (ev: MessageEvent): void => {
    if (!this.iframe || ev.source !== this.iframe.contentWindow) return;
    const msg = ev.data as { type?: string } & Record<string, unknown>;
    if (!msg || typeof msg.type !== "string") return;

    switch (msg.type) {
      case "ready":
        this.ready = true;
        this.readyWaiters.splice(0).forEach((fn) => fn());
        return;
      case "loaded":
      case "result": {
        const id = String(msg.id ?? "");
        const p = this.pending.get(id);
        if (!p) return;
        this.pending.delete(id);
        if (p.timer) clearTimeout(p.timer);
        if (msg.type === "loaded") {
          p.resolve({ ok: Boolean(msg.ok), error: msg.error });
        } else {
          p.resolve(msg as Record<string, unknown>);
        }
        return;
      }
      case "llm-request":
        void this.handleLLMRequest(msg);
        return;
      case "state-save": {
        const skillName = String(msg.skillName ?? this.currentSkill ?? "");
        const key = String(msg.key ?? "");
        if (skillName && key) void this.state.save(skillName, key, msg.value ?? null);
        return;
      }
      case "log":
        if (typeof msg.message === "string") {
          const level = String(msg.level ?? "log");
          // eslint-disable-next-line no-console
          (console as unknown as Record<string, (...a: unknown[]) => void>)[level]?.(
            `[skill:${this.currentSkill}] ${msg.message}`,
          );
        }
        return;
    }
  };

  private async handleLLMRequest(msg: Record<string, unknown>): Promise<void> {
    const id = String(msg.id ?? "");
    if (!id) return;
    const prompt = String(msg.prompt ?? "");
    const options = (msg.options ?? {}) as Record<string, unknown>;
    const mode = msg.mode === "json" ? "json" : "text";
    try {
      if (!this.llm) throw new Error("LLM proxy not configured");
      let result: unknown;
      if (mode === "json") {
        result = await this.llm.chatJSON(prompt, msg.schema, options as Parameters<LLMProxy["chatJSON"]>[2]);
      } else {
        result = await this.llm.chat(prompt, options as Parameters<LLMProxy["chat"]>[1]);
      }
      this.post({ type: "llm-response", id, ok: true, content: result });
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      this.post({ type: "llm-response", id, ok: false, error: errMsg });
    }
  }

  private post(msg: unknown): void {
    this.iframe?.contentWindow?.postMessage(msg, "*");
  }

  private async awaitReady(timeoutMs = 5000): Promise<void> {
    if (!this.iframe) throw new Error("skill iframe not attached");
    if (this.ready) return;
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error("skill iframe never signalled ready")),
        timeoutMs,
      );
      this.readyWaiters.push(() => {
        clearTimeout(timer);
        resolve();
      });
    });
  }

  private request<T>(id: string, msg: unknown, timeoutMs: number): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`skill bridge timeout after ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, { resolve: resolve as Pending<unknown>["resolve"], reject, timer });
      this.post(msg);
    });
  }
}

// ────────────────────────────────────────────────────────────────────────

function newId(): string {
  return `msg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function inMemoryStore(): SkillStateStore {
  const m = new Map<string, Record<string, unknown>>();
  return {
    async load(name) {
      return m.get(name) ?? {};
    },
    async save(name, key, value) {
      const cur = m.get(name) ?? {};
      cur[key] = value;
      m.set(name, cur);
    },
  };
}

async function resolveSkillSource(skill: SkillDefinition): Promise<string | undefined> {
  // Prefer scripts/index.js; fall back to extracting inline <script> from index.html.
  if (skill.js_path && skill.js_path.endsWith(".js")) {
    const text = await getFileText(skill.js_path);
    if (text) return text;
  }
  if (skill.script_path) {
    const html = await getFileText(skill.script_path);
    if (html) {
      const inline = /<script[^>]*>([\s\S]*?)<\/script>/i.exec(html);
      if (inline && inline[1].trim()) return inline[1];
      const srcMatch = /<script[^>]*src="([^"]+)"/i.exec(html);
      if (srcMatch) {
        const rel = srcMatch[1];
        const base = skill.script_path.slice(0, skill.script_path.lastIndexOf("/"));
        const path = rel.startsWith("/") ? rel.slice(1) : `${base}/${rel}`;
        const text = await getFileText(path);
        if (text) return text;
      }
    }
  }
  return undefined;
}

export const skillHostBridge = new SkillHostBridge();
