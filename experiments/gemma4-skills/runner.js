/**
 * runner.js — Node.js executor for Google AI Edge Gallery JS skills.
 *
 * Replaces the Android WebView execution environment with Node.js polyfills.
 * Invoked as: node runner.js <skill_js_path> <data_json> [secret]
 *
 * The script:
 *  1. Sets up browser-like globals (window, crypto, fetch, localStorage, etc.)
 *  2. Loads persisted localStorage state (Upgrade 1)
 *  3. Injects __skillos.llm helper for Gemma 4 sub-calls (Upgrade 3)
 *  4. Loads and evaluates the skill's index.js
 *  5. Calls ai_edge_gallery_get_result(data, secret)
 *  6. Persists localStorage state to disk
 *  7. Prints the JSON result to stdout
 *
 * Environment variables:
 *   SKILL_STATE_DIR   — directory for persistent localStorage (default: no persistence)
 *   SKILL_NAME        — skill name for state file naming
 *   LLM_API_URL       — Ollama/OpenRouter API base URL (e.g., http://localhost:11434/v1)
 *   LLM_MODEL         — model name (e.g., gemma4:e2b)
 *   LLM_API_KEY       — API key (default: "ollama" for local)
 */

const fs = require('fs');
const path = require('path');
const { webcrypto } = require('crypto');

// ── Arguments ────────────────────────────────────────────────────────
const skillJsPath = process.argv[2];
const dataJson = process.argv[3] || '{}';
const secret = process.argv[4] || '';

if (!skillJsPath) {
  console.error(JSON.stringify({ error: 'Usage: node runner.js <skill_js_path> <data_json> [secret]' }));
  process.exit(1);
}

// ── Upgrade 1: Persistent localStorage ──────────────────────────────

const SKILL_STATE_DIR = process.env.SKILL_STATE_DIR || '';
const SKILL_NAME = process.env.SKILL_NAME || path.basename(path.dirname(path.dirname(skillJsPath)));

// Load persisted state from disk
const _storage = {};
let _stateFile = '';

if (SKILL_STATE_DIR) {
  _stateFile = path.join(SKILL_STATE_DIR, `${SKILL_NAME}.json`);
  try {
    if (fs.existsSync(_stateFile)) {
      const saved = JSON.parse(fs.readFileSync(_stateFile, 'utf-8'));
      Object.assign(_storage, saved);
    }
  } catch (e) {
    // Corrupted state file — start fresh
  }
}

function _persistState() {
  if (!_stateFile || Object.keys(_storage).length === 0) return;
  try {
    fs.mkdirSync(path.dirname(_stateFile), { recursive: true });
    fs.writeFileSync(_stateFile, JSON.stringify(_storage, null, 2));
  } catch (e) {
    // Best effort — don't crash on state save failure
  }
}

// ── Browser-like polyfills ───────────────────────────────────────────

// crypto.subtle (Node 18+ has webcrypto natively)
if (!globalThis.crypto) {
  globalThis.crypto = webcrypto;
}
if (!globalThis.crypto.subtle && webcrypto.subtle) {
  globalThis.crypto.subtle = webcrypto.subtle;
}

// TextEncoder / TextDecoder (usually available in Node, but ensure it)
if (!globalThis.TextEncoder) {
  const { TextEncoder, TextDecoder } = require('util');
  globalThis.TextEncoder = TextEncoder;
  globalThis.TextDecoder = TextDecoder;
}

// btoa / atob polyfills (used by restaurant-roulette for data compression)
if (!globalThis.btoa) {
  globalThis.btoa = (str) => Buffer.from(str, 'binary').toString('base64');
}
if (!globalThis.atob) {
  globalThis.atob = (b64) => Buffer.from(b64, 'base64').toString('binary');
}

// localStorage polyfill (now backed by disk when SKILL_STATE_DIR is set)
const localStoragePoly = {
  getItem(key) { return _storage[key] !== undefined ? _storage[key] : null; },
  setItem(key, value) { _storage[key] = String(value); },
  removeItem(key) { delete _storage[key]; },
  clear() { Object.keys(_storage).forEach(k => delete _storage[k]); },
  get length() { return Object.keys(_storage).length; },
  key(n) { return Object.keys(_storage)[n] || null; },
};

// window / document stubs
const windowStub = {
  crypto: globalThis.crypto,
  localStorage: localStoragePoly,
  location: { href: 'about:blank', origin: 'http://localhost' },
  navigator: { userAgent: 'SkillOS-NodeRunner/1.0' },
  document: {
    createElement: (tag) => ({
      tagName: tag.toUpperCase(),
      style: {},
      setAttribute: () => {},
      appendChild: () => {},
      addEventListener: () => {},
    }),
    body: { appendChild: () => {}, removeChild: () => {} },
    head: { appendChild: () => {} },
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
  },
  addEventListener: () => {},
  setTimeout: setTimeout,
  setInterval: setInterval,
  clearTimeout: clearTimeout,
  clearInterval: clearInterval,
  console: console,
  fetch: globalThis.fetch,
};

// Set globals
globalThis.window = windowStub;
globalThis.document = windowStub.document;
globalThis.localStorage = localStoragePoly;
globalThis.navigator = windowStub.navigator;
globalThis.location = windowStub.location;

// ── Upgrade 3: __skillos LLM helper ─────────────────────────────────

const LLM_API_URL = process.env.LLM_API_URL || '';
const LLM_MODEL = process.env.LLM_MODEL || 'gemma4:e2b';
const LLM_API_KEY = process.env.LLM_API_KEY || 'ollama';

/**
 * __skillos — SkillOS runtime API available to all JS skills.
 *
 * Skills can call Gemma 4 (or any OpenAI-compatible API) for sub-reasoning:
 *
 *   const answer = await __skillos.llm.chat("Summarize this text: ...");
 *   const structured = await __skillos.llm.chatJSON("Extract entities", schema);
 */
const __skillos = {
  /** Runtime metadata */
  runtime: 'node',
  version: '1.0.0',
  skillName: SKILL_NAME,

  /** LLM sub-call interface */
  llm: {
    available: !!LLM_API_URL,
    url: LLM_API_URL,
    model: LLM_MODEL,

    /**
     * Single-turn chat completion. Returns the assistant's text response.
     * @param {string} prompt - User message
     * @param {object} options - Optional: temperature, max_tokens, system
     * @returns {Promise<string>} Assistant response text
     */
    async chat(prompt, options = {}) {
      if (!LLM_API_URL) {
        throw new Error('LLM not available: LLM_API_URL not set');
      }
      const messages = [];
      if (options.system) {
        messages.push({ role: 'system', content: options.system });
      }
      messages.push({ role: 'user', content: prompt });

      const body = {
        model: LLM_MODEL,
        messages,
        temperature: options.temperature ?? 0.7,
      };
      if (options.max_tokens) body.max_tokens = options.max_tokens;

      const resp = await fetch(`${LLM_API_URL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${LLM_API_KEY}`,
        },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const errText = await resp.text().catch(() => resp.statusText);
        throw new Error(`LLM API error (${resp.status}): ${errText}`);
      }

      const data = await resp.json();
      return data.choices[0].message.content;
    },

    /**
     * Chat completion with JSON response. Parses the response as JSON.
     * @param {string} prompt - User message (should ask for JSON output)
     * @param {object} schema - Optional JSON schema hint (included in prompt)
     * @param {object} options - Same as chat()
     * @returns {Promise<object>} Parsed JSON response
     */
    async chatJSON(prompt, schema = null, options = {}) {
      let fullPrompt = prompt;
      if (schema) {
        fullPrompt += `\n\nRespond with valid JSON matching this schema:\n${JSON.stringify(schema, null, 2)}`;
      } else {
        fullPrompt += '\n\nRespond with valid JSON only. No markdown, no explanation.';
      }

      const text = await this.chat(fullPrompt, { ...options, temperature: 0.1 });

      // Extract JSON from response (handle markdown fences)
      const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/) || [null, text];
      const cleaned = (jsonMatch[1] || text).trim();
      return JSON.parse(cleaned);
    },
  },

  /** State persistence */
  state: {
    /** Save arbitrary data to persistent state (separate from localStorage) */
    save(key, value) {
      _storage[`__skillos_state_${key}`] = JSON.stringify(value);
    },
    /** Load data from persistent state */
    load(key, defaultValue = null) {
      const raw = _storage[`__skillos_state_${key}`];
      if (raw === undefined) return defaultValue;
      try { return JSON.parse(raw); } catch { return defaultValue; }
    },
  },
};

globalThis.__skillos = __skillos;
windowStub.__skillos = __skillos;

// ── Load and run skill ──────────────────────────────────────────────

async function run() {
  let resolvedPath = path.resolve(skillJsPath);

  // If the path points to an HTML file, look for a sibling .js file
  if (resolvedPath.endsWith('.html')) {
    const jsCandidate = resolvedPath.replace(/\.html$/, '.js');
    if (fs.existsSync(jsCandidate)) {
      resolvedPath = jsCandidate;
    } else {
      // Extract inline JS from HTML
      const html = fs.readFileSync(resolvedPath, 'utf-8');
      const scriptMatch = html.match(/<script[^>]*src="([^"]+)"[^>]*>/);
      if (scriptMatch) {
        const srcPath = path.resolve(path.dirname(resolvedPath), scriptMatch[1]);
        if (fs.existsSync(srcPath)) {
          resolvedPath = srcPath;
        }
      } else {
        // Try inline <script> content
        const inlineMatch = html.match(/<script[^>]*>([\s\S]*?)<\/script>/);
        if (inlineMatch && inlineMatch[1].trim()) {
          eval(inlineMatch[1]);
        }
      }
    }
  }

  // Load the JS file if we haven't already eval'd inline script
  if (!globalThis.ai_edge_gallery_get_result && !windowStub.ai_edge_gallery_get_result) {
    const code = fs.readFileSync(resolvedPath, 'utf-8');
    eval(code);
  }

  // Resolve the function — it may be on window or globalThis
  const fn = globalThis.ai_edge_gallery_get_result
    || windowStub.ai_edge_gallery_get_result
    || (windowStub['ai_edge_gallery_get_result']);

  if (typeof fn !== 'function') {
    console.log(JSON.stringify({ error: `Function ai_edge_gallery_get_result not found in ${skillJsPath}` }));
    process.exit(0);
  }

  try {
    const result = await fn(dataJson, secret);
    // Persist localStorage state after execution
    _persistState();
    // Result may already be a JSON string or an object
    if (typeof result === 'string') {
      // Validate it's valid JSON, then pass through
      try {
        JSON.parse(result);
        console.log(result);
      } catch {
        console.log(JSON.stringify({ result: result }));
      }
    } else {
      console.log(JSON.stringify(result));
    }
  } catch (e) {
    _persistState(); // Still persist state on error
    console.log(JSON.stringify({ error: `Skill execution failed: ${e.message}` }));
  }
}

run().catch(e => {
  _persistState();
  console.log(JSON.stringify({ error: `Runner error: ${e.message}` }));
  process.exit(0);
});
