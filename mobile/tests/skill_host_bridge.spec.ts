/**
 * Unit tests for SkillHostBridge protocol handling.
 *
 * We don't spin up a real sandboxed iframe in happy-dom (its iframe has a
 * shared script context, so the end-to-end test would not exercise anything
 * sandbox-specific). Instead we exercise the bridge by attaching a fake
 * iframe whose `contentWindow.postMessage` is intercepted, and simulating
 * replies via `window.dispatchEvent(new MessageEvent(...))`.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { skillHostBridge } from "../src/lib/skills/skill_host_bridge";
import type { SkillDefinition } from "../src/lib/skills/skill_loader";
import { putFile, _resetDBForTests } from "../src/lib/storage/db";
import { IDBFactory } from "fake-indexeddb";

interface RecordedMessage {
  type: string;
  id?: string;
  [k: string]: unknown;
}

function makeFakeIframe(onPost: (m: RecordedMessage) => void): HTMLIFrameElement {
  const cw = {
    postMessage: (m: RecordedMessage) => {
      onPost(m);
    },
  } as unknown as Window;
  const el = {
    contentWindow: cw,
    setAttribute: () => {},
  } as unknown as HTMLIFrameElement;
  return el;
}

function emitFromIframe(iframe: HTMLIFrameElement, data: unknown): void {
  const ev = new MessageEvent("message", {
    data,
    source: iframe.contentWindow as Window,
  });
  window.dispatchEvent(ev);
}

const CALCULATE_HASH_SOURCE = `
  globalThis.ai_edge_gallery_get_result = async function (dataJson) {
    const d = JSON.parse(dataJson);
    return { result: 'HASH_OF_' + d.text };
  };
`;

describe("SkillHostBridge", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    skillHostBridge.detach();
    skillHostBridge.setLLMProxy(null);
    await putFile(
      "cartridges/demo/skills/mock-hash/SKILL.md",
      "---\nname: mock-hash\ndescription: mock\n---\nbody",
    );
    await putFile(
      "cartridges/demo/skills/mock-hash/scripts/index.js",
      CALCULATE_HASH_SOURCE,
    );
  });

  it("completes ready → load → run round-trip", async () => {
    const posted: RecordedMessage[] = [];
    let iframe: HTMLIFrameElement | null = null;
    iframe = makeFakeIframe((m) => {
      posted.push(m);
      // Drive the iframe's replies inline so the bridge's awaits resolve.
      if (m.type === "load-skill") {
        queueMicrotask(() =>
          emitFromIframe(iframe as HTMLIFrameElement, {
            type: "loaded",
            id: m.id,
            ok: true,
          }),
        );
      } else if (m.type === "run") {
        queueMicrotask(() =>
          emitFromIframe(iframe as HTMLIFrameElement, {
            type: "result",
            id: m.id,
            result: "HASH_OF_hello",
          }),
        );
      }
    });
    skillHostBridge.attachIframe(iframe);
    emitFromIframe(iframe, { type: "ready" });
    expect(skillHostBridge.isReady()).toBe(true);

    const skill: SkillDefinition = {
      name: "mock-hash",
      description: "",
      instructions: "",
      require_secret: false,
      require_secret_description: "",
      homepage: "",
      skill_dir: "cartridges/demo/skills/mock-hash",
      script_path: "",
      js_path: "cartridges/demo/skills/mock-hash/scripts/index.js",
      runtime: "node",
    };

    const res = await skillHostBridge.runSkill(skill, { data: { text: "hello" } });

    const loadMsg = posted.find((m) => m.type === "load-skill");
    expect(loadMsg).toBeDefined();
    expect(loadMsg!.skillName).toBe("mock-hash");
    expect(String(loadMsg!.source)).toContain("ai_edge_gallery_get_result");

    const runMsg = posted.find((m) => m.type === "run");
    expect(runMsg).toBeDefined();
    expect(JSON.parse(String(runMsg!.data))).toEqual({ text: "hello" });

    expect(res.ok).toBe(true);
    expect(res.result).toBe("HASH_OF_hello");
  });

  it("proxies an llm-request from iframe to the configured LLMProxy", async () => {
    const posted: RecordedMessage[] = [];
    const iframe = makeFakeIframe((m) => posted.push(m));
    skillHostBridge.attachIframe(iframe);
    emitFromIframe(iframe, { type: "ready" });

    const proxy = {
      chat: vi.fn(async (prompt: string) => `echo:${prompt}`),
      chatJSON: vi.fn(async () => ({})),
    };
    skillHostBridge.setLLMProxy(proxy);

    const requestId = "llm_1";
    emitFromIframe(iframe, {
      type: "llm-request",
      id: requestId,
      mode: "text",
      prompt: "what is 2+2?",
      options: {},
    });
    // Yield twice to let async handler complete.
    await new Promise((r) => setTimeout(r, 0));
    await new Promise((r) => setTimeout(r, 0));

    const response = posted.find((m) => m.type === "llm-response");
    expect(response).toBeDefined();
    expect(response!.id).toBe(requestId);
    expect(response!.ok).toBe(true);
    expect(response!.content).toBe("echo:what is 2+2?");
    expect(proxy.chat).toHaveBeenCalledTimes(1);
  });

  it("returns llm-response with error when proxy is not configured", async () => {
    const posted: RecordedMessage[] = [];
    const iframe = makeFakeIframe((m) => posted.push(m));
    skillHostBridge.attachIframe(iframe);
    emitFromIframe(iframe, { type: "ready" });

    skillHostBridge.setLLMProxy(null);
    emitFromIframe(iframe, {
      type: "llm-request",
      id: "x",
      mode: "text",
      prompt: "hi",
      options: {},
    });
    await new Promise((r) => setTimeout(r, 0));
    const response = posted.find((m) => m.type === "llm-response" && m.id === "x");
    expect(response).toBeDefined();
    expect(response!.ok).toBe(false);
    expect(String(response!.error)).toContain("not configured");
  });

  it("records state-save messages via the configured store", async () => {
    const iframe = makeFakeIframe(() => {});
    skillHostBridge.attachIframe(iframe);
    emitFromIframe(iframe, { type: "ready" });

    const store: Record<string, Record<string, unknown>> = {};
    skillHostBridge.setStateStore({
      async load(name) {
        return store[name] ?? {};
      },
      async save(name, key, value) {
        (store[name] ??= {})[key] = value;
      },
    });

    emitFromIframe(iframe, { type: "state-save", skillName: "s1", key: "k", value: 42 });
    await new Promise((r) => setTimeout(r, 0));
    expect(store.s1).toEqual({ k: 42 });
  });
});
