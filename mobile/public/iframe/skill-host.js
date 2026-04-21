/**
 * skill-host.js — sandbox-side runtime for Gallery JS skills.
 *
 * Adapted from experiments/gemma4-skills/runner.js. The Node polyfill block
 * (runner.js lines 24-139) is intentionally omitted — the browser already
 * supplies Blob, crypto, fetch, TextEncoder, etc. This file keeps the
 * __skillos injection and the ai_edge_gallery_get_result dispatch.
 *
 * Host ↔ iframe protocol is documented in src/lib/skills/skill_host_bridge.ts.
 */

/* eslint-disable no-var */
(function () {
  "use strict";
  var skillName = "";
  var stateCache = Object.create(null); // local per-skill state mirror
  var pendingLLM = new Map();

  function post(msg) {
    parent.postMessage(msg, "*");
  }

  function log(level, message) {
    try {
      post({ type: "log", level: level, message: String(message) });
    } catch (_) {
      /* noop */
    }
  }

  function newId() {
    return "iid_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  // Inject a skill's source into the current document via a Blob URL <script>.
  function injectScript(source) {
    return new Promise(function (resolve, reject) {
      try {
        var blob = new Blob([source], { type: "application/javascript" });
        var url = URL.createObjectURL(blob);
        var s = document.createElement("script");
        s.src = url;
        s.onload = function () {
          URL.revokeObjectURL(url);
          resolve();
        };
        s.onerror = function (e) {
          URL.revokeObjectURL(url);
          reject(e instanceof Error ? e : new Error("script load failed"));
        };
        document.head.appendChild(s);
      } catch (err) {
        reject(err);
      }
    });
  }

  // __skillos — SkillOS runtime API available to all JS skills.
  var __skillos = {
    runtime: "mobile",
    version: "1.0.0",
    get skillName() {
      return skillName;
    },
    llm: {
      available: true,
      chat: function (prompt, options) {
        return new Promise(function (resolve, reject) {
          var id = newId();
          pendingLLM.set(id, { resolve: resolve, reject: reject });
          post({ type: "llm-request", id: id, mode: "text", prompt: String(prompt), options: options || {} });
        });
      },
      chatJSON: function (prompt, schema, options) {
        return new Promise(function (resolve, reject) {
          var id = newId();
          pendingLLM.set(id, { resolve: resolve, reject: reject });
          post({
            type: "llm-request",
            id: id,
            mode: "json",
            prompt: String(prompt),
            schema: schema || null,
            options: options || {},
          });
        });
      },
    },
    state: {
      save: function (key, value) {
        stateCache[key] = value;
        post({ type: "state-save", skillName: skillName, key: String(key), value: value });
      },
      load: function (key, defaultValue) {
        if (Object.prototype.hasOwnProperty.call(stateCache, key)) return stateCache[key];
        return typeof defaultValue === "undefined" ? null : defaultValue;
      },
    },
  };

  // Expose on globals for the skill code to pick up. The skill typically sets
  // globalThis.ai_edge_gallery_get_result on load.
  self.__skillos = __skillos;
  globalThis.__skillos = __skillos;

  function getSkillFn() {
    return (
      globalThis.ai_edge_gallery_get_result ||
      self.ai_edge_gallery_get_result ||
      (typeof window !== "undefined" && window.ai_edge_gallery_get_result)
    );
  }

  async function handleLoadSkill(msg) {
    skillName = String(msg.skillName || "");
    stateCache = Object.assign(Object.create(null), msg.state && typeof msg.state === "object" ? msg.state : {});
    // Clear any prior dispatch function so stale skill code doesn't run.
    try {
      delete globalThis.ai_edge_gallery_get_result;
    } catch (_) {
      globalThis.ai_edge_gallery_get_result = undefined;
    }
    try {
      await injectScript(String(msg.source || ""));
      if (typeof getSkillFn() !== "function") {
        post({
          type: "loaded",
          id: msg.id,
          ok: false,
          error: "skill loaded but ai_edge_gallery_get_result is not defined",
        });
        return;
      }
      post({ type: "loaded", id: msg.id, ok: true });
    } catch (err) {
      post({
        type: "loaded",
        id: msg.id,
        ok: false,
        error: err && err.message ? err.message : "script injection failed",
      });
    }
  }

  async function handleRun(msg) {
    var fn = getSkillFn();
    if (typeof fn !== "function") {
      post({ type: "result", id: msg.id, ok: false, error: "no skill loaded" });
      return;
    }
    try {
      var raw = await fn(String(msg.data || "{}"), String(msg.secret || ""));
      var parsed;
      if (typeof raw === "string") {
        try {
          parsed = JSON.parse(raw);
        } catch (_) {
          parsed = { result: raw };
        }
      } else if (raw && typeof raw === "object") {
        parsed = raw;
      } else {
        parsed = { result: String(raw) };
      }
      post(Object.assign({ type: "result", id: msg.id, ok: !parsed.error }, parsed));
    } catch (err) {
      post({
        type: "result",
        id: msg.id,
        ok: false,
        error: err && err.message ? err.message : "skill threw",
      });
    }
  }

  function handleLLMResponse(msg) {
    var p = pendingLLM.get(msg.id);
    if (!p) return;
    pendingLLM.delete(msg.id);
    if (msg.ok) p.resolve(msg.content);
    else p.reject(new Error(msg.error || "llm error"));
  }

  self.addEventListener("message", function (ev) {
    var msg = ev.data;
    if (!msg || typeof msg.type !== "string") return;
    switch (msg.type) {
      case "load-skill":
        handleLoadSkill(msg);
        break;
      case "run":
        handleRun(msg);
        break;
      case "llm-response":
        handleLLMResponse(msg);
        break;
      default:
        log("warn", "unknown host message type: " + msg.type);
    }
  });

  // Signal readiness.
  post({ type: "ready" });
})();
