// SkillOS desktop UI — vanilla JS, no bundler.
//
// Two backends:
//   * Tauri invoke() — used when window.__TAURI__ is present.
//   * fetch() against http://127.0.0.1:8765 with a bearer token — used when
//     opened directly in a browser (dev mode, web demo).
//
// The bearer token in web mode is read from ?token=... on the URL.  The
// Tauri path uses the token injected by the Rust host via tauri::command,
// so the frontend never touches the secret.

const TAURI = window.__TAURI__;
const webToken = new URLSearchParams(location.search).get('token') || '';
const webBase  = new URLSearchParams(location.search).get('api')   || 'http://127.0.0.1:8765';

async function call(cmdName, httpPath, { method = 'GET', body, query } = {}) {
  if (TAURI) {
    // Tauri path: single args object, Rust wraps the HTTP call.
    return TAURI.core.invoke(cmdName, body ? { body } : query || {});
  }
  // Web path: direct fetch.
  const q = query ? `?${new URLSearchParams(query).toString()}` : '';
  const res = await fetch(`${webBase}${httpPath}${q}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(webToken ? { 'Authorization': `Bearer ${webToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- nav ------------------------------------------------------------

document.querySelectorAll('header nav button').forEach(btn => {
  btn.addEventListener('click', () => {
    const view = btn.dataset.view;
    document.querySelectorAll('header nav button').forEach(b => b.classList.toggle('active', b === btn));
    document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
  });
});

// --- backend status -------------------------------------------------

async function refreshStatus() {
  const el = document.getElementById('backend-status');
  try {
    const result = await call('get_health', '/health');
    const status = result && (result.status === 'ok' ? 'ok' : '');
    el.textContent = status === 'ok' ? 'backend online' : 'backend degraded';
    el.classList.toggle('ok', status === 'ok');
    el.classList.toggle('err', status !== 'ok');
  } catch (e) {
    el.textContent = `backend unreachable: ${e.message}`;
    el.classList.add('err');
  }
}

// --- route ----------------------------------------------------------

document.getElementById('route-form').addEventListener('submit', async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  const body = {
    goal: data.goal.trim(),
    project: data.project.trim() || undefined,
    cartridge: data.cartridge.trim() || undefined,
    force_forge: !!data.force_forge,
  };
  const out = document.getElementById('route-output');
  out.textContent = 'deciding…';
  try {
    const result = await call('route_goal', '/api/route', { method: 'POST', body });
    out.textContent = JSON.stringify(result, null, 2);
  } catch (e) {
    out.textContent = `error: ${e.message}`;
  }
});

// --- journal --------------------------------------------------------

document.getElementById('journal-form').addEventListener('submit', async e => {
  e.preventDefault();
  const project = new FormData(e.target).get('project').toString().trim();
  const out = document.getElementById('journal-output');
  out.innerHTML = '<p class="lede">loading…</p>';
  try {
    const result = TAURI
      ? await call('get_journal', '/api/journal', { query: { project, tail: 50 } })
      : await call('get_journal', '/api/journal', { query: { project, tail: '50' } });
    if (!result.records || result.records.length === 0) {
      out.innerHTML = '<p class="lede">no entries</p>';
      return;
    }
    out.innerHTML = '';
    for (const r of result.records) {
      const el = document.createElement('article');
      el.className = 'journal-entry';
      el.innerHTML = `
        <div class="meta">${escape(r.started_at)} · <code>${escape(r.job_id)}</code> · ${escape(r.trigger)}</div>
        <p class="goal">${escape(r.goal)}</p>
        <p>outcome: <span class="outcome-${escape(r.outcome)}">${escape(r.outcome)}</span>
           · tokens: ${r.claude_tokens_used}
           · $${(r.claude_usd_used ?? 0).toFixed(4)}
           · ${(r.wall_clock_s ?? 0).toFixed(1)}s</p>
        ${r.artifacts_produced && r.artifacts_produced.length
          ? `<p class="meta">${r.artifacts_produced.length} artifact(s)</p>` : ''}
      `;
      out.appendChild(el);
    }
  } catch (e) {
    out.innerHTML = `<p class="lede">error: ${escape(e.message)}</p>`;
  }
});

// --- budget ---------------------------------------------------------

document.getElementById('budget-form').addEventListener('submit', async e => {
  e.preventDefault();
  const project = new FormData(e.target).get('project').toString().trim();
  const out = document.getElementById('budget-output');
  out.textContent = 'loading…';
  try {
    const result = await call('get_budget', '/api/budget', { query: { project } });
    out.textContent = JSON.stringify(result, null, 2);
  } catch (e) {
    out.textContent = `error: ${e.message}`;
  }
});

// --- audit ----------------------------------------------------------

document.getElementById('audit-form').addEventListener('submit', async e => {
  e.preventDefault();
  const model = new FormData(e.target).get('model').toString().trim();
  const tbody = document.querySelector('#audit-table tbody');
  tbody.innerHTML = '<tr><td colspan="2" class="lede">auditing…</td></tr>';
  try {
    const result = await call('get_audit', '/api/audit', { query: { model } });
    tbody.innerHTML = '';
    const entries = Object.entries(result.status || {});
    if (entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="2" class="lede">no cartridges</td></tr>';
      return;
    }
    for (const [name, verdict] of entries.sort()) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${escape(name)}</td><td class="status-${escape(verdict)}">${escape(verdict)}</td>`;
      tbody.appendChild(tr);
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="2">error: ${escape(e.message)}</td></tr>`;
  }
});

// --- util -----------------------------------------------------------

function escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;',
    '"': '&quot;', "'": '&#39;',
  }[c]));
}

refreshStatus();
setInterval(refreshStatus, 10_000);
