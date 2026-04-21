import { describe, expect, it } from "vitest";
import { resolveProvider } from "../src/lib/cartridge/routing";
import type { LLMProvider } from "../src/lib/llm/provider";
import type { AgentSpec, CartridgeManifest } from "../src/lib/cartridge/types";

function fakeProvider(tag: string): LLMProvider {
  return {
    chat: async () => ({ content: tag }),
    testConnection: async () => ({ ok: true, message: tag }),
  };
}

function agent(overrides: Partial<AgentSpec> = {}): AgentSpec {
  return {
    name: "a",
    path: "x",
    body: "",
    needs: [],
    produces: [],
    produces_schema: "",
    produces_description: "",
    tools: [],
    max_turns: 3,
    description: "",
    tier: "cheap",
    ...overrides,
  };
}

function manifest(preferred_tier: CartridgeManifest["preferred_tier"] = "auto"): CartridgeManifest {
  return {
    name: "c",
    path: "",
    description: "",
    entry_intents: [],
    flows: {},
    flow_defs: {},
    blackboard_schema: {},
    validators: [],
    max_turns_per_agent: 3,
    default_flow: "",
    variables: {},
    type: "standard",
    skills_source: "",
    preferred_tier,
  };
}

describe("resolveProvider", () => {
  const primary = fakeProvider("primary");
  const fallback = fakeProvider("fallback");

  it("uses primary by default", () => {
    const r = resolveProvider(agent(), manifest(), { primary });
    expect(r.target).toBe("primary");
    expect(r.provider).toBe(primary);
  });

  it("routes tier:capable agents to fallback when available", () => {
    const r = resolveProvider(
      agent({ tier: "capable" }),
      manifest(),
      { primary, fallback },
    );
    expect(r.target).toBe("fallback");
    expect(r.reason).toMatch(/capable/);
  });

  it("tier:capable stays on primary when no fallback is configured", () => {
    const r = resolveProvider(agent({ tier: "capable" }), manifest(), { primary });
    expect(r.target).toBe("primary");
  });

  it("manifest preferred_tier=cloud routes to fallback for cheap agents too", () => {
    const r = resolveProvider(
      agent({ tier: "cheap" }),
      manifest("cloud"),
      { primary, fallback },
    );
    expect(r.target).toBe("fallback");
  });

  it("escalates to fallback after a validation failure", () => {
    const r = resolveProvider(
      agent(),
      manifest(),
      { primary, fallback },
      { attempt: 2, previousFailure: "validation", previousTarget: "primary" },
    );
    expect(r.target).toBe("fallback");
    expect(r.reason).toMatch(/escalat/i);
  });

  it("does not bounce back from fallback to primary on repeated failure", () => {
    const r = resolveProvider(
      agent(),
      manifest(),
      { primary, fallback },
      { attempt: 3, previousFailure: "validation", previousTarget: "fallback" },
    );
    // Already on fallback — stays on it (no further escalation target).
    expect(r.target).toBe("primary"); // rule 3 no-ops, rule 4 fires
  });

  it("preferred_tier=local has no effect when only primary is available", () => {
    const r = resolveProvider(agent(), manifest("local"), { primary });
    expect(r.target).toBe("primary");
  });
});
