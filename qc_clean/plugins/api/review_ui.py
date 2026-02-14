"""
Self-contained HTML review UI served by the FastAPI server.

Uses string.Template so that CSS/JS curly braces don't need escaping.
The single substitution variable is $project_id.
"""

from string import Template


_REVIEW_HTML = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Review</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f5f5f5; color: #1a1a1a; line-height: 1.5; }
a { color: #2563eb; }

/* Header */
.header { position: sticky; top: 0; z-index: 100; background: #fff; border-bottom: 1px solid #e0e0e0; padding: 12px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.header h1 { font-size: 18px; font-weight: 600; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.badge-review { background: #fef3c7; color: #92400e; }
.badge-running { background: #dbeafe; color: #1e40af; }
.badge-completed { background: #d1fae5; color: #065f46; }
.badge-pending { background: #e5e7eb; color: #374151; }
.stats { margin-left: auto; font-size: 13px; color: #666; display: flex; gap: 16px; }

/* Action bar */
.action-bar { background: #fff; border-bottom: 1px solid #e0e0e0; padding: 10px 24px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; position: sticky; top: 55px; z-index: 99; }
.btn { padding: 7px 16px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; background: #fff; transition: all 0.15s; }
.btn:hover { background: #f3f4f6; }
.btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn-primary:hover { background: #1d4ed8; }
.btn-success { background: #059669; color: #fff; border-color: #059669; }
.btn-success:hover { background: #047857; }
.btn-danger { background: #dc2626; color: #fff; border-color: #dc2626; }
.btn-danger:hover { background: #b91c1c; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.decision-count { font-size: 13px; color: #666; margin-left: auto; }

/* Toast */
.toast { position: fixed; top: 20px; right: 20px; z-index: 200; padding: 12px 20px; border-radius: 8px; font-size: 14px; color: #fff; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.toast-success { background: #059669; }
.toast-error { background: #dc2626; }

/* Card list */
.cards { padding: 16px 24px; display: flex; flex-direction: column; gap: 12px; max-width: 900px; margin: 0 auto; }

/* Code card */
.card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; border-left: 4px solid #d1d5db; overflow: hidden; }
.card.decision-approve { border-left-color: #059669; }
.card.decision-reject { border-left-color: #dc2626; }
.card.decision-modify { border-left-color: #d97706; }
.card.decision-merge { border-left-color: #7c3aed; }
.card.decision-split { border-left-color: #ea580c; }
.card.decision-reject .card-name { text-decoration: line-through; opacity: 0.6; }

.card-top { padding: 12px 16px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.card-actions { display: flex; gap: 4px; }
.card-actions .btn { padding: 4px 10px; font-size: 12px; }
.card-actions .btn.active { outline: 2px solid #2563eb; outline-offset: -2px; }
.card-name { font-weight: 600; font-size: 15px; }
.card-mentions { font-size: 12px; color: #888; }
.card-confidence { margin-left: auto; font-size: 13px; font-weight: 600; color: #666; }
.card-provenance { font-size: 11px; padding: 1px 6px; border-radius: 4px; background: #f3f4f6; color: #666; }

.card-body { padding: 0 16px 12px; }
.card-desc { font-size: 13px; color: #555; margin-bottom: 6px; }
.card-quotes { font-size: 12px; color: #777; }
.card-quotes q { font-style: italic; }

/* Modify fields */
.modify-fields { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.modify-fields label { font-size: 12px; font-weight: 600; color: #555; }
.modify-fields input, .modify-fields textarea { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; font-family: inherit; }
.modify-fields textarea { resize: vertical; min-height: 60px; }

/* Merge fields */
.merge-fields { margin-top: 8px; }
.merge-fields select { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; min-width: 200px; }

/* Split fields */
.split-fields { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.split-row { display: flex; gap: 8px; align-items: center; }
.split-row input { flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
.split-add { font-size: 12px; color: #2563eb; cursor: pointer; background: none; border: none; }

/* Applications accordion */
.app-toggle { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 8px 16px; border-top: 1px solid #f0f0f0; font-size: 13px; font-weight: 500; color: #555; user-select: none; }
.app-toggle:hover { background: #fafafa; }
.app-toggle .arrow { transition: transform 0.15s; }
.app-toggle.open .arrow { transform: rotate(90deg); }
.app-list { display: none; padding: 0 16px 12px; }
.app-list.open { display: block; }
.app-item { border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 13px; }
.app-item.app-decision-approve { border-left: 3px solid #059669; }
.app-item.app-decision-reject { border-left: 3px solid #dc2626; text-decoration: line-through; opacity: 0.6; }
.app-quote { font-style: italic; color: #555; }
.app-meta { display: flex; gap: 12px; font-size: 12px; color: #888; margin-top: 4px; }
.app-actions { margin-top: 4px; display: flex; gap: 4px; }
.app-actions .btn { padding: 2px 8px; font-size: 11px; }
.app-actions .btn.active { outline: 2px solid #2563eb; outline-offset: -2px; }

/* Rationale */
.rationale-row { padding: 0 16px 12px; }
.rationale-row input { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }
.rationale-row label { font-size: 11px; color: #888; }

/* Loading */
.loading { text-align: center; padding: 60px; font-size: 16px; color: #888; }

/* Empty state */
.empty { text-align: center; padding: 60px; color: #888; }
</style>
</head>
<body>

<div class="header" id="header">
  <h1 id="projectName">Loading...</h1>
  <span class="badge badge-pending" id="statusBadge">...</span>
  <div class="stats" id="stats"></div>
  <a href="/graph/$project_id" style="font-size:13px;margin-left:8px;">View Graph</a>
</div>

<div class="action-bar">
  <button class="btn btn-success" id="approveAllBtn" onclick="approveAll()">Approve All</button>
  <button class="btn btn-primary" id="saveBtn" onclick="submitDecisions(false)">Save Decisions</button>
  <button class="btn btn-primary" id="saveResumeBtn" onclick="submitDecisions(true)">Save &amp; Resume Pipeline</button>
  <span class="decision-count" id="decisionCount"></span>
</div>

<div class="toast" id="toast"></div>

<div id="content">
  <div class="loading">Loading project data...</div>
</div>

<script>
const PROJECT_ID = "$project_id";
const API_BASE = "";

let projectData = null;
let decisions = new Map();  // targetId -> {target_type, target_id, action, rationale, new_value}
let expandedCodes = new Set();

// -------------------------------------------------------------------
// Data loading
// -------------------------------------------------------------------

async function loadProject() {
  try {
    const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/review/codes");
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    projectData = await resp.json();
    decisions = new Map();
    render();
  } catch (e) {
    document.getElementById("content").innerHTML =
      '<div class="empty">Failed to load project: ' + escapeHtml(e.message) + '</div>';
  }
}

// -------------------------------------------------------------------
// Rendering
// -------------------------------------------------------------------

function render() {
  if (!projectData) return;

  // Header
  document.getElementById("projectName").textContent = projectData.project_name || "Project";
  const badge = document.getElementById("statusBadge");
  const status = projectData.pipeline_status || "unknown";
  badge.textContent = status.replace(/_/g, " ");
  badge.className = "badge badge-" + (
    status === "paused_for_review" ? "review" :
    status === "running" ? "running" :
    status === "completed" ? "completed" : "pending"
  );

  const summary = projectData.summary || {};
  document.getElementById("stats").innerHTML =
    "<span>" + (summary.codes_count || 0) + " codes</span>" +
    "<span>" + (summary.applications_count || 0) + " applications</span>";

  updateDecisionCount();

  // Cards
  const codes = projectData.codes || [];
  if (codes.length === 0) {
    document.getElementById("content").innerHTML =
      '<div class="empty">No codes to review.</div>';
    return;
  }

  let html = '<div class="cards">';
  for (const code of codes) {
    html += renderCodeCard(code);
  }
  html += '</div>';
  document.getElementById("content").innerHTML = html;
}

function renderCodeCard(code) {
  const d = decisions.get(code.id);
  const action = d ? d.action : null;
  const cardClass = action ? "card decision-" + action : "card";

  const apps = code.applications || [];
  const isExpanded = expandedCodes.has(code.id);

  let html = '<div class="' + cardClass + '" id="card-' + code.id + '">';

  // Top bar: actions, name, stats
  html += '<div class="card-top">';
  html += '<div class="card-actions">';
  for (const act of ["approve", "reject", "modify", "merge", "split"]) {
    const activeClass = action === act ? " active" : "";
    html += '<button class="btn' + activeClass + '" onclick="setDecision(\'' +
            code.id + '\',\'' + act + '\')">' + capitalize(act) + '</button>';
  }
  html += '</div>';
  html += '<span class="card-confidence">' + (code.confidence != null ? code.confidence.toFixed(2) : "") + '</span>';
  html += '</div>';

  // Name row
  html += '<div class="card-body">';
  html += '<div class="card-name">' + escapeHtml(code.name) +
          ' <span class="card-mentions">(' + (code.mention_count || 0) + ' mentions)</span>' +
          ' <span class="card-provenance">' + escapeHtml(code.provenance || "llm") + '</span></div>';
  html += '<div class="card-desc">' + escapeHtml(code.description || "") + '</div>';

  // Example quotes
  if (code.example_quotes && code.example_quotes.length > 0) {
    html += '<div class="card-quotes">Quotes: ';
    html += code.example_quotes.slice(0, 3).map(function(q) {
      return '<q>' + escapeHtml(truncate(q, 120)) + '</q>';
    }).join(", ");
    html += '</div>';
  }

  // Modify fields
  if (action === "modify") {
    const nv = d.new_value || {};
    html += '<div class="modify-fields">';
    html += '<label>New Name</label>';
    html += '<input type="text" value="' + escapeAttr(nv.name || code.name) +
            '" onchange="updateModify(\'' + code.id + '\',\'name\',this.value)">';
    html += '<label>New Description</label>';
    html += '<textarea onchange="updateModify(\'' + code.id + '\',\'description\',this.value)">' +
            escapeHtml(nv.description || code.description || "") + '</textarea>';
    html += '</div>';
  }

  // Merge fields
  if (action === "merge") {
    const nv = d.new_value || {};
    const otherCodes = (projectData.codes || []).filter(function(c) { return c.id !== code.id; });
    html += '<div class="merge-fields">';
    html += '<label style="font-size:12px;font-weight:600;color:#555">Merge into: </label>';
    html += '<select onchange="updateMerge(\'' + code.id + '\',this.value)">';
    html += '<option value="">-- Select target code --</option>';
    for (const oc of otherCodes) {
      const sel = nv.merge_into === oc.id ? " selected" : "";
      html += '<option value="' + oc.id + '"' + sel + '>' + escapeHtml(oc.name) + '</option>';
    }
    html += '</select></div>';
  }

  // Split fields
  if (action === "split") {
    const nv = d.new_value || {};
    const newCodes = nv.new_codes || [{ name: "" }, { name: "" }];
    html += '<div class="split-fields">';
    html += '<label style="font-size:12px;font-weight:600;color:#555">Split into:</label>';
    for (let i = 0; i < newCodes.length; i++) {
      html += '<div class="split-row">';
      html += '<input type="text" placeholder="New code name ' + (i + 1) + '" value="' +
              escapeAttr(newCodes[i].name || "") +
              '" onchange="updateSplit(\'' + code.id + '\',' + i + ',this.value)">';
      html += '</div>';
    }
    html += '<button class="split-add" onclick="addSplitRow(\'' + code.id + '\')">+ Add another</button>';
    html += '</div>';
  }

  html += '</div>';  // card-body

  // Applications accordion
  if (apps.length > 0) {
    html += '<div class="app-toggle' + (isExpanded ? " open" : "") +
            '" onclick="toggleApps(\'' + code.id + '\')">';
    html += '<span class="arrow">&#9654;</span> Applications (' + apps.length + ')';
    html += '</div>';
    html += '<div class="app-list' + (isExpanded ? " open" : "") + '">';
    for (const app of apps) {
      html += renderAppItem(app, code.id);
    }
    html += '</div>';
  }

  // Rationale
  html += '<div class="rationale-row">';
  html += '<label>Rationale</label>';
  html += '<input type="text" placeholder="Optional rationale for this decision" value="' +
          escapeAttr(d ? d.rationale || "" : "") +
          '" onchange="updateRationale(\'' + code.id + '\',this.value)">';
  html += '</div>';

  html += '</div>';  // card
  return html;
}

function renderAppItem(app, codeId) {
  const d = decisions.get(app.id);
  const action = d ? d.action : null;
  const cls = action ? "app-item app-decision-" + action : "app-item";

  let html = '<div class="' + cls + '">';
  html += '<div class="app-quote">"' + escapeHtml(truncate(app.quote_text || "", 200)) + '"</div>';
  html += '<div class="app-meta">';
  if (app.speaker) html += '<span>Speaker: ' + escapeHtml(app.speaker) + '</span>';
  html += '<span>Doc: ' + escapeHtml(app.doc_name || "") + '</span>';
  if (app.confidence != null) html += '<span>' + app.confidence.toFixed(2) + '</span>';
  html += '</div>';
  html += '<div class="app-actions">';
  for (const act of ["approve", "reject"]) {
    const activeClass = action === act ? " active" : "";
    html += '<button class="btn' + activeClass + '" onclick="setAppDecision(\'' +
            app.id + '\',\'' + act + '\',event)">' + capitalize(act) + '</button>';
  }
  html += '</div>';
  html += '</div>';
  return html;
}

// -------------------------------------------------------------------
// Decision management
// -------------------------------------------------------------------

function setDecision(codeId, action) {
  const existing = decisions.get(codeId);
  if (existing && existing.action === action) {
    // Toggle off
    decisions.delete(codeId);
  } else {
    const d = { target_type: "code", target_id: codeId, action: action, rationale: "" };
    if (action === "modify") d.new_value = {};
    if (action === "merge") d.new_value = {};
    if (action === "split") d.new_value = { new_codes: [{ name: "" }, { name: "" }] };
    decisions.set(codeId, d);
  }
  rerenderCard(codeId);
  updateDecisionCount();
}

function setAppDecision(appId, action, event) {
  if (event) event.stopPropagation();
  const existing = decisions.get(appId);
  if (existing && existing.action === action) {
    decisions.delete(appId);
  } else {
    decisions.set(appId, { target_type: "code_application", target_id: appId, action: action, rationale: "" });
  }
  // Re-render the parent code card
  const code = findCodeForApp(appId);
  if (code) rerenderCard(code.id);
  updateDecisionCount();
}

function updateRationale(codeId, value) {
  const d = decisions.get(codeId);
  if (d) d.rationale = value;
}

function updateModify(codeId, field, value) {
  const d = decisions.get(codeId);
  if (d && d.action === "modify") {
    if (!d.new_value) d.new_value = {};
    d.new_value[field] = value;
  }
}

function updateMerge(codeId, targetId) {
  const d = decisions.get(codeId);
  if (d && d.action === "merge") {
    d.new_value = { merge_into: targetId };
  }
}

function updateSplit(codeId, index, value) {
  const d = decisions.get(codeId);
  if (d && d.action === "split") {
    if (!d.new_value) d.new_value = { new_codes: [] };
    while (d.new_value.new_codes.length <= index) d.new_value.new_codes.push({ name: "" });
    d.new_value.new_codes[index].name = value;
  }
}

function addSplitRow(codeId) {
  const d = decisions.get(codeId);
  if (d && d.action === "split") {
    if (!d.new_value) d.new_value = { new_codes: [] };
    d.new_value.new_codes.push({ name: "" });
    rerenderCard(codeId);
  }
}

function toggleApps(codeId) {
  if (expandedCodes.has(codeId)) expandedCodes.delete(codeId);
  else expandedCodes.add(codeId);
  rerenderCard(codeId);
}

function rerenderCard(codeId) {
  const code = (projectData.codes || []).find(function(c) { return c.id === codeId; });
  if (!code) return;
  const el = document.getElementById("card-" + codeId);
  if (!el) return;
  const tmp = document.createElement("div");
  tmp.innerHTML = renderCodeCard(code);
  el.replaceWith(tmp.firstElementChild);
}

function updateDecisionCount() {
  const n = decisions.size;
  document.getElementById("decisionCount").textContent =
    n > 0 ? n + " decision" + (n !== 1 ? "s" : "") + " pending" : "";
}

function findCodeForApp(appId) {
  for (const code of (projectData.codes || [])) {
    for (const app of (code.applications || [])) {
      if (app.id === appId) return code;
    }
  }
  return null;
}

// -------------------------------------------------------------------
// Submit
// -------------------------------------------------------------------

async function submitDecisions(andResume) {
  const decisionList = Array.from(decisions.values());
  if (decisionList.length === 0 && !andResume) {
    showToast("No decisions to save.", "error");
    return;
  }

  try {
    if (decisionList.length > 0) {
      const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/review/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decisions: decisionList }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to save decisions");
      }
      const result = await resp.json();
      showToast("Saved " + result.applied + " decisions.", "success");
    }

    if (andResume) {
      const resp2 = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!resp2.ok) {
        const err = await resp2.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to resume pipeline");
      }
      showToast("Pipeline resumed! Remaining stages running in background.", "success");
    }

    // Refresh data
    await loadProject();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function approveAll() {
  try {
    const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/review/approve-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to approve all");
    }
    const result = await resp.json();
    showToast("Approved all " + result.applied + " codes.", "success");
    await loadProject();
  } catch (e) {
    showToast(e.message, "error");
  }
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

function showToast(msg, type) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast toast-" + type;
  el.style.display = "block";
  setTimeout(function() { el.style.display = "none"; }, 4000);
}

function escapeHtml(s) {
  if (!s) return "";
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  if (!s) return "";
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function truncate(s, n) {
  if (!s || s.length <= n) return s;
  return s.slice(0, n) + "...";
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// -------------------------------------------------------------------
// Init
// -------------------------------------------------------------------
loadProject();
</script>
</body>
</html>
""")


def render_review_page(project_id: str) -> str:
    """Return the review HTML page with the project_id substituted in."""
    return _REVIEW_HTML.substitute(project_id=project_id)
