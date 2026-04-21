/**
 * withRetry — exponential-backoff retry wrapper for cloud LLM fetch calls.
 *
 * M18 wraps `chatOnce` / `chatStream` in `LLMClient`. Only classifies *network*
 * errors (429, 503, TCP resets, timeouts) as retriable. Auth (401, 403) and
 * user-error (400) never retry — they'd just burn tokens.
 *
 * Respects `AbortSignal` — an abort is propagated immediately, no retry.
 */

export interface RetryOptions {
  attempts?: number;
  minDelayMs?: number;
  maxDelayMs?: number;
  /** Return true to retry; false to bail immediately. Default: `defaultIsRetriable`. */
  isRetriable?: (err: unknown, attempt: number) => boolean;
  signal?: AbortSignal;
  onRetry?: (err: unknown, attempt: number, delayMs: number) => void;
}

const DEFAULT_ATTEMPTS = 5;
const DEFAULT_MIN_DELAY = 250;
const DEFAULT_MAX_DELAY = 8_000;

export function defaultIsRetriable(err: unknown): boolean {
  if (err instanceof DOMException && err.name === "AbortError") return false;
  const msg = err instanceof Error ? err.message : String(err);
  // Status codes from our own `LLMClient` error messages: "LLM <code>: ..."
  const m = /LLM (\d{3}):/.exec(msg);
  if (m) {
    const code = Number(m[1]);
    if (code === 408) return true;
    if (code === 425 || code === 429) return true;
    if (code >= 500 && code < 600) return true;
    return false;
  }
  // Generic network/DNS/reset failures tend to surface as TypeError("fetch failed").
  if (/fetch failed|network|ECONNRESET|ETIMEDOUT|socket hang up/i.test(msg)) return true;
  return false;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = {},
): Promise<T> {
  const attempts = opts.attempts ?? DEFAULT_ATTEMPTS;
  const minDelay = opts.minDelayMs ?? DEFAULT_MIN_DELAY;
  const maxDelay = opts.maxDelayMs ?? DEFAULT_MAX_DELAY;
  const isRetriable = opts.isRetriable ?? defaultIsRetriable;

  let lastErr: unknown = new Error("no attempts");
  for (let i = 1; i <= attempts; i++) {
    if (opts.signal?.aborted) throw new DOMException("aborted", "AbortError");
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i === attempts || !isRetriable(err, i)) throw err;
      const delay = Math.min(maxDelay, minDelay * Math.pow(2, i - 1));
      opts.onRetry?.(err, i, delay);
      await sleep(delay, opts.signal);
    }
  }
  throw lastErr;
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException("aborted", "AbortError"));
    const t = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(t);
      reject(new DOMException("aborted", "AbortError"));
    };
    signal?.addEventListener("abort", onAbort);
  });
}
