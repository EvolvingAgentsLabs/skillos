import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import {
  experiencesForProject,
  listExperiences,
  recordExperience,
  renderExperienceMarkdown,
} from "../src/lib/memory/smart_memory";
import { _resetDBForTests } from "../src/lib/storage/db";

describe("SmartMemory", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("recordExperience appends a new entry", async () => {
    const rec = await recordExperience({
      session_id: "s1",
      project: "cooking-demo",
      goal: "plan weekly menu",
      outcome: "success",
      components_used: ["menu-planner", "shopping-list-builder", "recipe-writer"],
      duration_seconds: 42,
      output_summary: "ok",
    });
    expect(rec.experience_id).toMatch(/^exp_/);
    expect(rec.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    const all = await listExperiences();
    expect(all).toHaveLength(1);
    expect(all[0].goal).toBe("plan weekly menu");
  });

  it("listExperiences sorts newest first", async () => {
    const first = await recordExperience({
      session_id: "a",
      project: "p",
      goal: "g1",
      outcome: "success",
      components_used: [],
      duration_seconds: 1,
    });
    await new Promise((r) => setTimeout(r, 5));
    const second = await recordExperience({
      session_id: "b",
      project: "p",
      goal: "g2",
      outcome: "partial",
      components_used: [],
      duration_seconds: 2,
    });
    const all = await listExperiences();
    expect(all[0].experience_id).toBe(second.experience_id);
    expect(all[1].experience_id).toBe(first.experience_id);
  });

  it("experiencesForProject filters by project name", async () => {
    await recordExperience({
      session_id: "a",
      project: "alpha",
      goal: "g",
      outcome: "success",
      components_used: [],
      duration_seconds: 1,
    });
    await recordExperience({
      session_id: "b",
      project: "beta",
      goal: "g",
      outcome: "success",
      components_used: [],
      duration_seconds: 1,
    });
    const alpha = await experiencesForProject("alpha");
    const beta = await experiencesForProject("beta");
    expect(alpha).toHaveLength(1);
    expect(alpha[0].project).toBe("alpha");
    expect(beta).toHaveLength(1);
    expect(beta[0].project).toBe("beta");
  });

  it("renderExperienceMarkdown round-trips the frontmatter shape", async () => {
    const rec = await recordExperience({
      session_id: "s",
      project: "p",
      goal: "make it work",
      outcome: "success_with_recovery",
      components_used: ["agent-a", "agent-b"],
      quality_score: 8,
      cost_estimate_usd: 0.02,
      duration_seconds: 12,
      output_summary: "done",
      learnings: "schema retry worked",
    });
    const md = renderExperienceMarkdown(rec);
    expect(md.startsWith("---\n")).toBe(true);
    expect(md).toContain("experience_id:");
    expect(md).toContain("outcome: success_with_recovery");
    expect(md).toContain(`components_used: ${JSON.stringify(["agent-a", "agent-b"])}`);
    expect(md).toContain("## Output Summary");
    expect(md).toContain("## Learnings");
    expect(md).toContain("schema retry worked");
  });
});
