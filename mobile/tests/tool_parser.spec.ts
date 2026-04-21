import { describe, expect, it } from "vitest";
import {
  TOOL_ALIASES,
  extractJsonObject,
  extractTagContent,
  inferToolFromArgs,
  parseToolCalls,
  repairJsonArgs,
} from "../src/lib/llm/tool_parser";

describe("extractJsonObject", () => {
  it("returns first complete object, ignoring trailing garbage", () => {
    expect(extractJsonObject('{"a":1}<channel|>noise')).toBe('{"a":1}');
    expect(extractJsonObject('prefix {"a":{"b":"}"}} suffix')).toBe('{"a":{"b":"}"}}');
    expect(extractJsonObject('no json here')).toBe('no json here');
  });
  it("respects escapes inside strings", () => {
    expect(extractJsonObject('{"a":"\\"}"}')).toBe('{"a":"\\"}"}');
  });
});

describe("extractTagContent", () => {
  it("returns trimmed tag body", () => {
    expect(extractTagContent("final_answer", "<final_answer>  done  </final_answer>")).toBe(
      "done",
    );
  });
  it("returns null for missing tag", () => {
    expect(extractTagContent("x", "nothing")).toBeNull();
  });
});

describe("inferToolFromArgs", () => {
  it("recognises common tool signatures", () => {
    expect(inferToolFromArgs('{"agent_name":"x","task":"y"}')).toBe("delegate_to_agent");
    expect(inferToolFromArgs('{"path":"f","content":"x"}')).toBe("write_file");
    expect(inferToolFromArgs('{"url":"http://x"}')).toBe("web_fetch");
    expect(inferToolFromArgs('{"prompt":"hi"}')).toBe("call_llm");
    expect(inferToolFromArgs('{"path":"f"}')).toBe("read_file");
    expect(inferToolFromArgs('{"query":"x"}')).toBe("call_llm");
  });
  it("returns null for unknown shape", () => {
    expect(inferToolFromArgs('{"nope":1}')).toBeNull();
    expect(inferToolFromArgs("not json")).toBeNull();
  });
});

describe("parseToolCalls", () => {
  it("format A — named tool_call with JSON body", () => {
    const out = parseToolCalls('<tool_call name="write_file">{"path":"a","content":"x"}</tool_call>');
    expect(out).toEqual([{ name: "write_file", args: '{"path":"a","content":"x"}' }]);
  });

  it("format A2 — unclosed named tool_call terminates at next tag or EOF", () => {
    const text = [
      '<tool_call name="read_file">{"path":"a"}',
      '<final_answer>done</final_answer>',
    ].join("\n");
    const out = parseToolCalls(text);
    expect(out.length).toBe(1);
    expect(out[0].name).toBe("read_file");
    expect(out[0].args).toContain('"path":"a"');
  });

  it("format B — bare tool_call infers name from args", () => {
    const out = parseToolCalls('<tool_call>{"path":"a","content":"x"}</tool_call>');
    expect(out).toEqual([{ name: "write_file", args: '{"path":"a","content":"x"}' }]);
  });

  it("format C — bare tool_call with name on first line", () => {
    const out = parseToolCalls("<tool_call>\nweb_fetch\n{\"url\":\"http://x\"}\n</tool_call>");
    expect(out).toEqual([{ name: "web_fetch", args: '{"url":"http://x"}' }]);
  });

  it("format D — JSON array in ```json fence", () => {
    const text = "```json\n[{\"tool_name\":\"write_file\",\"parameters\":{\"path\":\"p\",\"content\":\"c\"}}]\n```";
    const out = parseToolCalls(text);
    expect(out.length).toBe(1);
    expect(out[0].name).toBe("write_file");
    expect(JSON.parse(out[0].args)).toEqual({ path: "p", content: "c" });
  });

  it("format D — bare array without fence", () => {
    const text = '[{"name":"read_file","params":{"path":"p"}}]';
    const out = parseToolCalls(text);
    expect(out.length).toBe(1);
    expect(out[0].name).toBe("read_file");
  });

  it("format D — infers name from parameters when absent", () => {
    const text = "```json\n[{\"parameters\":{\"url\":\"http://x\"}}]\n```";
    const out = parseToolCalls(text);
    expect(out.length).toBe(1);
    expect(out[0].name).toBe("web_fetch");
  });

  it("multiple calls in format A", () => {
    const text = [
      '<tool_call name="a">{"x":1}</tool_call>',
      '<tool_call name="b">{"y":2}</tool_call>',
    ].join("\n");
    const out = parseToolCalls(text);
    expect(out.map((c) => c.name)).toEqual(["a", "b"]);
  });

  it("empty response returns no calls", () => {
    expect(parseToolCalls("")).toEqual([]);
    expect(parseToolCalls("hello")).toEqual([]);
  });

  it("TOOL_ALIASES maps run_agent → delegate_to_agent", () => {
    expect(TOOL_ALIASES.run_agent).toBe("delegate_to_agent");
  });
});

describe("repairJsonArgs", () => {
  it("recovers args with unescaped inner quotes", () => {
    // Simulates Gemma's classic failure: inner quotes inside `content` are
    // left unescaped, but the outer `"," boundary is well-formed.
    const raw = '{"path": "f.md", "content": "hello "world" end"}';
    const out = repairJsonArgs(raw);
    expect(out).toBeDefined();
    expect(out!.path).toBe("f.md");
    expect(String(out!.content)).toContain('"world"');
    expect(String(out!.content)).toContain("hello");
    expect(String(out!.content)).toContain("end");
  });
  it("returns null for non-object input", () => {
    expect(repairJsonArgs("nope")).toBeNull();
    expect(repairJsonArgs("[1,2]")).toBeNull();
  });
});
