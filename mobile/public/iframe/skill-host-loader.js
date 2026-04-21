/**
 * skill-host-loader.js — three-strategy script loader for the sandboxed
 * skill iframe.
 *
 * M19 fallback chain:
 *   1. Blob URL `<script src>` (fastest; default)
 *   2. data URL `<script src>`   (some older WKWebView builds throttle Blob
 *      URLs inside null-origin sandboxes)
 *   3. `srcdoc`-inlined `<script>` tag (slowest; last-ditch for odd iOS
 *      cases where both URL schemes are blocked by CSP nuance)
 *
 * Each attempt has a 3-second handshake timeout; on timeout/error we
 * escalate to the next strategy. The first strategy that succeeds is
 * posted back to the host via `{type:"log", level:"info",
 * message:"loader:<strategy>"}` so we can record device-specific behaviour
 * and prefer that strategy next launch.
 */

(function (global) {
  "use strict";

  var STRATEGY_TIMEOUT_MS = 3000;

  function log(message) {
    try {
      parent.postMessage(
        { type: "log", level: "info", message: "loader:" + message },
        "*",
      );
    } catch (_) {
      /* noop */
    }
  }

  function tryBlobUrl(source) {
    return new Promise(function (resolve, reject) {
      var settled = false;
      var url = null;
      try {
        var blob = new Blob([source], { type: "application/javascript" });
        url = URL.createObjectURL(blob);
        var s = document.createElement("script");
        s.src = url;
        s.onload = function () {
          if (settled) return;
          settled = true;
          URL.revokeObjectURL(url);
          resolve("blob");
        };
        s.onerror = function () {
          if (settled) return;
          settled = true;
          URL.revokeObjectURL(url);
          reject(new Error("blob-url onerror"));
        };
        setTimeout(function () {
          if (settled) return;
          settled = true;
          URL.revokeObjectURL(url);
          reject(new Error("blob-url timeout"));
        }, STRATEGY_TIMEOUT_MS);
        document.head.appendChild(s);
      } catch (err) {
        if (url) URL.revokeObjectURL(url);
        reject(err);
      }
    });
  }

  function tryDataUrl(source) {
    return new Promise(function (resolve, reject) {
      var settled = false;
      try {
        // btoa handles ASCII only; fall back to encodeURIComponent for
        // utf-8 sources. We try btoa first since it's cheaper.
        var encoded;
        try {
          encoded =
            "data:application/javascript;base64," +
            btoa(unescape(encodeURIComponent(source)));
        } catch (_) {
          encoded =
            "data:application/javascript;charset=utf-8," +
            encodeURIComponent(source);
        }
        var s = document.createElement("script");
        s.src = encoded;
        s.onload = function () {
          if (settled) return;
          settled = true;
          resolve("data-url");
        };
        s.onerror = function () {
          if (settled) return;
          settled = true;
          reject(new Error("data-url onerror"));
        };
        setTimeout(function () {
          if (settled) return;
          settled = true;
          reject(new Error("data-url timeout"));
        }, STRATEGY_TIMEOUT_MS);
        document.head.appendChild(s);
      } catch (err) {
        reject(err);
      }
    });
  }

  function tryInlineSrcdoc(source) {
    return new Promise(function (resolve, reject) {
      try {
        // Last resort: append an inline <script> tag with the full source
        // as textContent. Requires CSP to allow 'unsafe-inline' inside the
        // iframe (which skill-host.html enables, scoped to the null origin).
        var s = document.createElement("script");
        s.textContent = source;
        document.head.appendChild(s);
        // No onload event for inline scripts — give the runtime a tick
        // to register the dispatch function.
        setTimeout(function () {
          resolve("inline");
        }, 10);
      } catch (err) {
        reject(err);
      }
    });
  }

  /**
   * injectSkillSource(source) — try strategies in order; resolves with the
   * name of the first one that succeeded, rejects if all three fail.
   */
  global.injectSkillSource = async function (source) {
    var strategies = [
      { name: "blob-url", fn: tryBlobUrl },
      { name: "data-url", fn: tryDataUrl },
      { name: "inline", fn: tryInlineSrcdoc },
    ];
    var lastErr = null;
    for (var i = 0; i < strategies.length; i++) {
      var s = strategies[i];
      try {
        var used = await s.fn(source);
        log(used);
        return used;
      } catch (err) {
        lastErr = err;
        log("fail-" + s.name + ":" + (err && err.message ? err.message : ""));
      }
    }
    throw lastErr || new Error("no script-load strategy succeeded");
  };
})(self);
