/**
 * runner.js — Node.js executor for Google AI Edge Gallery JS skills.
 *
 * Replaces the Android WebView execution environment with Node.js polyfills.
 * Invoked as: node runner.js <skill_js_path> <data_json> [secret]
 *
 * The script:
 *  1. Sets up browser-like globals (window, crypto, fetch, localStorage, etc.)
 *  2. Loads and evaluates the skill's index.js
 *  3. Calls ai_edge_gallery_get_result(data, secret)
 *  4. Prints the JSON result to stdout
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

// localStorage polyfill (in-memory, per-execution)
const _storage = {};
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
    console.log(JSON.stringify({ error: `Skill execution failed: ${e.message}` }));
  }
}

run().catch(e => {
  console.log(JSON.stringify({ error: `Runner error: ${e.message}` }));
  process.exit(0);
});
