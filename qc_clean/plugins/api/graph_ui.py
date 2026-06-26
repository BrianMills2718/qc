"""
Self-contained HTML graph visualization UI served by the FastAPI server.

Uses string.Template so that CSS/JS curly braces don't need escaping.
The single substitution variable is $project_id.
Loads Cytoscape.js from CDN for interactive graph rendering.
"""

from string import Template


_GRAPH_HTML = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analysis Graph</title>
<script src="https://unpkg.com/cytoscape@3.30.4/dist/cytoscape.min.js"></script>
<script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
<script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f5f5f5; color: #1a1a1a; line-height: 1.5; display: flex; flex-direction: column; height: 100vh; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

/* Header */
.header { background: #fff; border-bottom: 1px solid #e0e0e0; padding: 12px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.header h1 { font-size: 18px; font-weight: 600; }
.nav-links { margin-left: auto; display: flex; gap: 16px; font-size: 13px; }

/* Tabs */
.tabs { background: #fff; border-bottom: 1px solid #e0e0e0; padding: 0 24px; display: flex; gap: 0; }
.tab { padding: 10px 20px; font-size: 14px; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; color: #666; transition: all 0.15s; }
.tab:hover { color: #1a1a1a; background: #f9fafb; }
.tab.active { color: #2563eb; border-bottom-color: #2563eb; }

/* Toolbar */
.toolbar { background: #fff; border-bottom: 1px solid #e0e0e0; padding: 8px 24px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.toolbar input[type="text"] { padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; width: 200px; }
.btn { padding: 6px 14px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; background: #fff; transition: all 0.15s; }
.btn:hover { background: #f3f4f6; }
.btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn-primary:hover { background: #1d4ed8; }
.stats-bar { margin-left: auto; font-size: 12px; color: #888; }
.graph-help { background: #eff6ff; border-bottom: 1px solid #bfdbfe; padding: 8px 24px; font-size: 13px; color: #1f2937; }
.graph-help strong { margin-right: 6px; }
.empty-note { position: absolute; left: 24px; top: 158px; z-index: 10; max-width: 360px; background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px 12px; font-size: 13px; color: #374151; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: none; }

/* Graph container */
#cy { flex: 1; background: #fafafa; position: relative; }

/* Detail panel */
.detail-panel { position: fixed; right: 20px; top: 140px; width: 320px; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: none; z-index: 50; max-height: 60vh; overflow-y: auto; }
.detail-panel h3 { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.detail-panel .close-btn { position: absolute; top: 8px; right: 12px; font-size: 18px; cursor: pointer; color: #888; background: none; border: none; }
.detail-panel .field { margin-bottom: 8px; }
.detail-panel .field-label { font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; }
.detail-panel .field-value { font-size: 13px; color: #333; }
.detail-panel .quotes { font-size: 12px; color: #555; font-style: italic; }
.detail-panel .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #e5e7eb; color: #374151; margin-right: 4px; }

/* Loading / empty */
.loading { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 16px; color: #888; }
</style>
</head>
<body>

<div class="header">
  <h1 id="projectName">Analysis Graph</h1>
  <div class="nav-links">
    <a href="/review/$project_id">Code Review</a>
    <a href="/projects/$project_id">Project</a>
  </div>
</div>

<div class="tabs">
  <div class="tab active" data-view="hierarchy" onclick="switchView('hierarchy')">Code Hierarchy</div>
  <div class="tab" data-view="relationships" onclick="switchView('relationships')">Code Relationships</div>
  <div class="tab" data-view="entities" onclick="switchView('entities')">Entity Map</div>
  <div class="tab" data-view="claims" onclick="switchView('claims')">Claim Graph</div>
</div>

<div class="toolbar">
  <input type="text" id="searchInput" placeholder="Search nodes..." oninput="searchNodes(this.value)">
  <button class="btn" onclick="fitGraph()">Fit to View</button>
  <button class="btn" onclick="downloadPNG()">Download PNG</button>
  <span class="stats-bar" id="statsBar"></span>
</div>

<div class="graph-help" id="graphHelp">
  <strong>What this graph shows:</strong>
  Code Hierarchy shows parent-child codebook links. Code Relationships shows non-hierarchy analytic links. Entity Map shows extracted entities and entity links.
</div>

<div id="cy">
  <div class="loading" id="loadingMsg">Loading graph data...</div>
</div>
<div class="empty-note" id="emptyNote"></div>

<div class="detail-panel" id="detailPanel">
  <button class="close-btn" onclick="closeDetail()">&times;</button>
  <div id="detailContent"></div>
</div>

<script>
const PROJECT_ID = "$project_id";
const API_BASE = "";

let cy = null;
let currentView = "hierarchy";
let codeData = null;
let entityData = null;
let claimData = null;

// -------------------------------------------------------------------
// Color palettes
// -------------------------------------------------------------------
const LEVEL_COLORS = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626"];
const REL_COLORS = {
  "related_to": "#6b7280",
  "causes": "#dc2626",
  "influences": "#d97706",
  "part_of": "#2563eb",
  "leads_to": "#059669",
  "contradicts": "#7c3aed",
};

// -------------------------------------------------------------------
// Data loading
// -------------------------------------------------------------------
async function loadCodeData() {
  try {
    const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/graph/codes");
    if (!resp.ok) throw new Error("Failed to load code data");
    codeData = await resp.json();
    document.getElementById("projectName").textContent = (codeData.project_name || "Project") + " — Graph";
  } catch (e) {
    document.getElementById("loadingMsg").textContent = "Error: " + e.message;
  }
}

async function loadEntityData() {
  try {
    const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/graph/entities");
    if (!resp.ok) throw new Error("Failed to load entity data");
    entityData = await resp.json();
  } catch (e) {
    console.error("Entity load error:", e);
  }
}

async function loadClaimData() {
  try {
    const resp = await fetch(API_BASE + "/projects/" + PROJECT_ID + "/graph/claims");
    if (!resp.ok) throw new Error("Failed to load claim data");
    claimData = await resp.json();
  } catch (e) {
    console.error("Claim load error:", e);
  }
}

// -------------------------------------------------------------------
// Graph rendering
// -------------------------------------------------------------------
function initCytoscape(elements, layout) {
  if (cy) cy.destroy();
  const loading = document.getElementById("loadingMsg");
  if (loading) loading.style.display = "none";
  setEmptyNote("");

  cy = cytoscape({
    container: document.getElementById("cy"),
    elements: elements,
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "text-wrap": "wrap",
          "text-max-width": "120px",
          "font-size": "12px",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "data(color)",
          "width": "data(size)",
          "height": "data(size)",
          "border-width": 2,
          "border-color": "#fff",
          "color": "#1a1a1a",
        }
      },
      {
        selector: "node.highlighted",
        style: {
          "border-color": "#dc2626",
          "border-width": 4,
        }
      },
      {
        selector: "node.dimmed",
        style: {
          "opacity": 0.3,
        }
      },
      {
        selector: "edge",
        style: {
          "width": "data(width)",
          "line-color": "data(color)",
          "target-arrow-color": "data(color)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "opacity": 0.7,
          "label": "data(label)",
          "font-size": "10px",
          "text-rotation": "autorotate",
          "color": "#888",
        }
      },
      {
        selector: "edge.dimmed",
        style: {
          "opacity": 0.1,
        }
      },
    ],
    layout: layout,
    minZoom: 0.2,
    maxZoom: 3,
  });

  cy.on("tap", "node", function(evt) {
    showDetail(evt.target.data());
  });

  cy.on("tap", "edge", function(evt) {
    showDetail(evt.target.data());
  });

  cy.on("tap", function(evt) {
    if (evt.target === cy) closeDetail();
  });
}

function renderHierarchy() {
  if (!codeData) return;
  var elements = [];

  for (var node of codeData.nodes) {
    var size = Math.max(30, Math.min(80, 30 + (node.mention_count || 0) * 3));
    var color = LEVEL_COLORS[node.level % LEVEL_COLORS.length];
    elements.push({
      data: {
        id: node.id,
        label: node.name,
        color: color,
        size: size,
        // Store full data for detail panel
        description: node.description || "",
        level: node.level,
        mention_count: node.mention_count || 0,
        confidence: node.confidence || 0,
        example_quotes: node.example_quotes || [],
        nodeType: "code",
      }
    });
  }

  for (var edge of (codeData.hierarchy_edges || [])) {
    elements.push({
      data: {
        id: "hierarchy:" + edge.source + ":" + edge.target,
        source: edge.source,
        target: edge.target,
        label: "",
        color: "#94a3b8",
        width: 2,
        edgeType: "hierarchy",
        rationale: "Parent-child codebook hierarchy link.",
      }
    });
  }

  var stats = codeData.nodes.length + " codes";
  if (codeData.hierarchy_edges) stats += ", " + codeData.hierarchy_edges.length + " parent-child links";
  document.getElementById("statsBar").textContent = stats;
  document.getElementById("graphHelp").innerHTML =
    "<strong>What this graph shows:</strong> Code Hierarchy shows parent-child codebook links. A flat codebook can have nodes but no parent-child edges.";

  initCytoscape(elements, {
    name: "dagre",
    rankDir: "TB",
    nodeSep: 60,
    rankSep: 80,
    padding: 30,
  });
  if ((codeData.hierarchy_edges || []).length === 0) {
    setEmptyNote("No parent-child hierarchy links in this view. This can be normal for a flat codebook; use Code Relationships for analytic links between codes.");
  }
}

function renderRelationships() {
  if (!codeData) return;
  var elements = [];

  // Only include codes that have relationships
  var relatedIds = new Set();
  for (var edge of (codeData.relationship_edges || [])) {
    relatedIds.add(edge.source);
    relatedIds.add(edge.target);
  }

  // If no relationships, show all codes
  var showAll = relatedIds.size === 0;

  for (var node of codeData.nodes) {
    if (!showAll && !relatedIds.has(node.id)) continue;
    var size = Math.max(30, Math.min(80, 30 + (node.mention_count || 0) * 3));
    elements.push({
      data: {
        id: node.id,
        label: node.name,
        color: LEVEL_COLORS[node.level % LEVEL_COLORS.length],
        size: size,
        description: node.description || "",
        level: node.level,
        mention_count: node.mention_count || 0,
        confidence: node.confidence || 0,
        example_quotes: node.example_quotes || [],
        nodeType: "code",
      }
    });
  }

  for (var edge of (codeData.relationship_edges || [])) {
    var relColor = REL_COLORS[edge.type] || "#6b7280";
    var w = Math.max(1, Math.min(6, (edge.strength || 0.5) * 6));
    elements.push({
      data: {
        id: "code-rel:" + edge.source + ":" + edge.target + ":" + (edge.type || ""),
        source: edge.source,
        target: edge.target,
        label: edge.type || "",
        color: relColor,
        width: w,
        edgeType: "code_relationship",
        relationshipType: edge.type || "",
        strength: edge.strength || 0,
      }
    });
  }

  var stats = elements.filter(function(e) { return !e.data.source; }).length + " codes, " +
              (codeData.relationship_edges || []).length + " relationships";
  document.getElementById("statsBar").textContent = stats;
  document.getElementById("graphHelp").innerHTML =
    "<strong>What this graph shows:</strong> Code Relationships shows analytic links between codes, such as tension, influence, or qualification.";

  initCytoscape(elements, {
    name: "cose",
    idealEdgeLength: 150,
    nodeOverlap: 20,
    padding: 30,
    animate: false,
  });
  if ((codeData.relationship_edges || []).length === 0) {
    setEmptyNote(codeData.empty_reason || "No code relationship edges are available for this project.");
  }
}

function renderEntities() {
  if (!entityData) return;
  var elements = [];

  var TYPE_COLORS = {
    "concept": "#2563eb",
    "person": "#059669",
    "organization": "#d97706",
    "tool": "#7c3aed",
    "technology": "#dc2626",
  };

  var relatedIds = new Set();
  for (var edge of (entityData.edges || [])) {
    relatedIds.add(edge.source);
    relatedIds.add(edge.target);
  }

  var showAll = relatedIds.size === 0;

  for (var node of entityData.nodes) {
    if (!showAll && !relatedIds.has(node.id)) continue;
    var color = TYPE_COLORS[node.type] || "#6b7280";
    elements.push({
      data: {
        id: node.id,
        label: node.name,
        color: color,
        size: 40,
        description: node.description || "",
        entityType: node.type || "concept",
        nodeType: "entity",
      }
    });
  }

  for (var edge of (entityData.edges || [])) {
    var w = Math.max(1, Math.min(6, (edge.strength || 0.5) * 6));
    elements.push({
      data: {
        id: "entity-rel:" + edge.source + ":" + edge.target + ":" + (edge.type || ""),
        source: edge.source,
        target: edge.target,
        label: edge.type || "",
        color: "#94a3b8",
        width: w,
        edgeType: "entity_relationship",
        relationshipType: edge.type || "",
        strength: edge.strength || 0,
      }
    });
  }

  var shownEntities = elements.filter(function(e) { return !e.data.source; }).length;
  var hiddenIsolated = Math.max(0, entityData.nodes.length - shownEntities);
  var stats = shownEntities + " linked entities, " + (entityData.edges || []).length + " relationships";
  if (hiddenIsolated > 0) stats += ", " + hiddenIsolated + " isolated hidden";
  document.getElementById("statsBar").textContent = stats;
  document.getElementById("graphHelp").innerHTML =
    "<strong>What this graph shows:</strong> Entity Map shows extracted entities and links between them. Isolated entities are hidden when linked structure exists.";

  initCytoscape(elements, {
    name: "cose",
    idealEdgeLength: 150,
    nodeOverlap: 20,
    padding: 30,
    animate: false,
  });
  if ((entityData.edges || []).length === 0) {
    setEmptyNote(entityData.empty_reason || "No entity relationship edges are available for this project.");
  }
}

function renderClaims() {
  if (!claimData) return;
  var elements = [];

  const CLAIM_KIND_COLORS = {
    "perspective": "#2563eb",
    "cross_case": "#d97706",
    "synthesis_finding": "#059669",
    "relationship": "#7c3aed",
    "negative_case": "#dc2626",
    "code": "#6b7280",
    "code_application": "#64748b",
  };
  const CLAIM_REL_COLORS = {
    "elaborates": "#2563eb",
    "synthesizes": "#059669",
    "contrasts": "#dc2626",
  };

  for (var node of (claimData.nodes || [])) {
    elements.push({
      data: {
        id: node.id,
        label: node.label,
        color: CLAIM_KIND_COLORS[node.kind] || "#6b7280",
        size: 46,
        claimText: node.claim_text || "",
        claimKind: node.kind || "claim",
        sourceStage: node.source_stage || "",
        supportStatus: node.support_status || "",
        participantNames: node.participant_names || [],
        originObjectType: node.origin_object_type || "",
        nodeType: "claim",
      }
    });
  }

  for (var edge of (claimData.edges || [])) {
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.type || "",
        color: CLAIM_REL_COLORS[edge.type] || "#6b7280",
        width: 3,
        edgeType: "claim_relationship",
        relationshipType: edge.type || "",
        rationale: edge.rationale || "",
      }
    });
  }

  var stats = (claimData.nodes || []).length + " claims, " + (claimData.edges || []).length + " relationships";
  document.getElementById("statsBar").textContent = stats;
  document.getElementById("graphHelp").innerHTML =
    "<strong>What this graph shows:</strong> Claim Graph shows first-class claim nodes and deterministic links such as elaborates, synthesizes, and contrasts.";

  initCytoscape(elements, {
    name: "cose",
    idealEdgeLength: 180,
    nodeOverlap: 20,
    padding: 30,
    animate: false,
  });
  if ((claimData.edges || []).length === 0) {
    setEmptyNote(claimData.empty_reason || "No claim relationship edges are available for this project.");
  }
}

function setEmptyNote(message) {
  const note = document.getElementById("emptyNote");
  if (!note) return;
  if (!message) {
    note.textContent = "";
    note.style.display = "none";
    return;
  }
  note.textContent = message;
  note.style.display = "block";
}

// -------------------------------------------------------------------
// View switching
// -------------------------------------------------------------------
function switchView(view) {
  currentView = view;
  document.querySelectorAll(".tab").forEach(function(t) {
    t.classList.toggle("active", t.dataset.view === view);
  });
  closeDetail();
  if (view === "hierarchy") renderHierarchy();
  else if (view === "relationships") renderRelationships();
  else if (view === "entities") renderEntities();
  else if (view === "claims") renderClaims();
}

// -------------------------------------------------------------------
// Search
// -------------------------------------------------------------------
function searchNodes(query) {
  if (!cy) return;
  if (!query) {
    cy.elements().removeClass("highlighted dimmed");
    return;
  }
  var q = query.toLowerCase();
  cy.nodes().forEach(function(node) {
    var label = (node.data("label") || "").toLowerCase();
    if (label.includes(q)) {
      node.addClass("highlighted").removeClass("dimmed");
    } else {
      node.addClass("dimmed").removeClass("highlighted");
    }
  });
  cy.edges().forEach(function(edge) {
    var src = edge.source();
    var tgt = edge.target();
    if (src.hasClass("highlighted") || tgt.hasClass("highlighted")) {
      edge.removeClass("dimmed");
    } else {
      edge.addClass("dimmed");
    }
  });
}

// -------------------------------------------------------------------
// Detail panel
// -------------------------------------------------------------------
function showDetail(data) {
  var html = "<h3>" + escapeHtml(data.label) + "</h3>";

  if (data.nodeType === "code") {
    html += '<div class="field"><span class="field-label">Level</span>';
    html += '<div class="field-value">' + data.level + '</div></div>';
    html += '<div class="field"><span class="field-label">Mentions</span>';
    html += '<div class="field-value">' + data.mention_count + '</div></div>';
    html += '<div class="field"><span class="field-label">Confidence</span>';
    html += '<div class="field-value">' + (data.confidence || 0).toFixed(2) + '</div></div>';
    if (data.description) {
      html += '<div class="field"><span class="field-label">Description</span>';
      html += '<div class="field-value">' + escapeHtml(data.description) + '</div></div>';
    }
    if (data.example_quotes && data.example_quotes.length > 0) {
      html += '<div class="field"><span class="field-label">Example Quotes</span>';
      html += '<div class="quotes">';
      data.example_quotes.slice(0, 3).forEach(function(q) {
        html += '<p>"' + escapeHtml(q.substring(0, 150)) + '"</p>';
      });
      html += '</div></div>';
    }
  } else if (data.nodeType === "entity") {
    html += '<div class="field"><span class="badge">' + escapeHtml(data.entityType || "concept") + '</span></div>';
    if (data.description) {
      html += '<div class="field"><span class="field-label">Description</span>';
      html += '<div class="field-value">' + escapeHtml(data.description) + '</div></div>';
    }
  } else if (data.nodeType === "claim") {
    html += '<div class="field"><span class="badge">' + escapeHtml(data.claimKind || "claim") + '</span></div>';
    html += '<div class="field"><span class="field-label">Stage</span>';
    html += '<div class="field-value">' + escapeHtml(data.sourceStage || "") + '</div></div>';
    html += '<div class="field"><span class="field-label">Support</span>';
    html += '<div class="field-value">' + escapeHtml(data.supportStatus || "") + '</div></div>';
    if (data.participantNames && data.participantNames.length > 0) {
      html += '<div class="field"><span class="field-label">Participants</span>';
      html += '<div class="field-value">' + escapeHtml(data.participantNames.join(", ")) + '</div></div>';
    }
    if (data.originObjectType) {
      html += '<div class="field"><span class="field-label">Origin</span>';
      html += '<div class="field-value">' + escapeHtml(data.originObjectType) + '</div></div>';
    }
    if (data.claimText) {
      html += '<div class="field"><span class="field-label">Claim text</span>';
      html += '<div class="field-value">' + escapeHtml(data.claimText) + '</div></div>';
    }
  } else if (data.edgeType) {
    html += '<div class="field"><span class="badge">' + escapeHtml(data.edgeType) + '</span></div>';
    html += '<div class="field"><span class="field-label">Source</span>';
    html += '<div class="field-value">' + escapeHtml(data.source || "") + '</div></div>';
    html += '<div class="field"><span class="field-label">Target</span>';
    html += '<div class="field-value">' + escapeHtml(data.target || "") + '</div></div>';
    if (data.relationshipType) {
      html += '<div class="field"><span class="field-label">Relationship</span>';
      html += '<div class="field-value">' + escapeHtml(data.relationshipType) + '</div></div>';
    }
    if (data.strength !== undefined) {
      html += '<div class="field"><span class="field-label">Strength</span>';
      html += '<div class="field-value">' + escapeHtml(String(data.strength)) + '</div></div>';
    }
    if (data.rationale) {
      html += '<div class="field"><span class="field-label">Rationale</span>';
      html += '<div class="field-value">' + escapeHtml(data.rationale) + '</div></div>';
    }
  }

  document.getElementById("detailContent").innerHTML = html;
  document.getElementById("detailPanel").style.display = "block";
}

function closeDetail() {
  document.getElementById("detailPanel").style.display = "none";
}

// -------------------------------------------------------------------
// Controls
// -------------------------------------------------------------------
function fitGraph() {
  if (cy) cy.fit(null, 30);
}

function downloadPNG() {
  if (!cy) return;
  var png = cy.png({ scale: 2, full: true, bg: "#fafafa" });
  var link = document.createElement("a");
  link.href = png;
  link.download = "graph-" + currentView + ".png";
  link.click();
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------
function escapeHtml(s) {
  if (!s) return "";
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// -------------------------------------------------------------------
// Init
// -------------------------------------------------------------------
async function init() {
  await Promise.all([loadCodeData(), loadEntityData(), loadClaimData()]);
  renderHierarchy();
}

init();
</script>
</body>
</html>
""")


def render_graph_page(project_id: str) -> str:
    """Return the graph HTML page with the project_id substituted in."""
    return _GRAPH_HTML.substitute(project_id=project_id)
