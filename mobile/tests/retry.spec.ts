import { describe, expect, it, vi } from "vitest";
import { defaultIsRetriable, withRetry } from "../src/lib/llm/retry";

describe("defaultIsRetriable", () => {
  it("retries on 429, 500, 503, 408", () => {
    expect(defaultIsRetriable(new Error("LLM 429: rate limit"))).toBe(true);
    expect(defaultIsRetriable(new Error("LLM 500: upstream"))).toBe(true);
    expect(defaultIsRetriable(new Error("LLM 503: unavailable"))).toBe(true);
    expect(defaultIsRetriable(new Error("LLM 408: timeout"))).toBe(true);
  });

  it("does NOT retry on 400, 401, 403, 404", () => {
    expect(defaultIsRetriable(new Error("LLM 400: bad request"))).toBe(false);
    expect(defaultIsRetriable(new Error("LLM 401: unauth"))).toBe(false);
    expect(defaultIsRetriable(new Error("LLM 403: forbidden"))).toBe(false);
    expect(defaultIsRetriable(new Error("LLM 404: not found"))).toBe(false);
  });

  it("retries generic network errors", () => {
    expect(defaultIsRetriable(new TypeError("fetch failed"))).toBe(true);
    expect(defaultIsRetriable(new Error("ECONNRESET"))).toBe(true);
  });

  it("never retries AbortError", () => {
    expect(defaultIsRetriable(new DOMException("aborted", "AbortError"))).toBe(false);
  });
});

describe("withRetry", () => {
  it("returns the first success immediately", async () => {
    const fn = vi.fn(async () => 42);
    const r = await withRetry(fn);
    expect(r).toBe(42);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("retries a retriable error then succeeds", async () => {
    let n = 0;
    const fn = vi.fn(async () => {
      n++;
      if (n < 3) throw new Error("LLM 503: flaky");
      return "ok";
    });
    const onRetry = vi.fn();
    const r = await withRetry(fn, { minDelayMs: 1, onRetry });
    expect(r).toBe("ok");
    expect(fn).toHaveBeenCalledTimes(3);
    expect(onRetry).toHaveBeenCalledTimes(2);
  });

  it("bails immediately on non-retriable errors", async () => {
    const fn = vi.fn(async () => {
      throw new Error("LLM 401: auth required");
    });
    await expect(withRetry(fn, { minDelayMs: 1 })).rejects.toThrow(/LLM 401/);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("exhausts attempts on persistent retriable failure", async () => {
    const fn = vi.fn(async () => {
      throw new Error("LLM 503: always broken");
    });
    await expect(withRetry(fn, { attempts: 3, minDelayMs: 1 })).rejects.toThrow(/LLM 503/);
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it("respects abort signal between attempts", async () => {
    const ctrl = new AbortController();
    const fn = vi.fn(async () => {
      throw new Error("LLM 503: flaky");
    });
    setTimeout(() => ctrl.abort(), 20);
    await expect(
      withRetry(fn, { minDelayMs: 40, signal: ctrl.signal }),
    ).rejects.toThrow(/abort/i);
  });
});
