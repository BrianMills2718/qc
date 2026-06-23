# Plan #207: Review UI Orientation Aids

**Status:** Active
**Type:** implementation
**Priority:** High
**Blocked By:** Reviewer Demo Run Packet
**Blocks:** Brian review usability

---

## Gap

The review UI loads and exposes codes, claims, negative cases, relationships,
and review actions, but the page does not explain what a reviewer is looking
at, what order to inspect things in, or what the buttons/metrics mean. Brian's
review feedback is explicit: "I need tool tips and concise instructions ... I
don't know what I am looking at."

## Target

Add concise, reviewer-facing orientation aids to the existing HTML review UI:

- a short "Start here" instruction strip with the review goal and recommended
  order;
- a compact legend for evidence anchors, support status, confidence, and
  decision buttons;
- per-tab help text that changes for Codes, Claims, Negative Cases, and
  Relationships;
- native `title`/ARIA labels for tab buttons, graph link, global action
  buttons, per-card action buttons, confidence/support/review/status pills,
  application toggles, evidence anchors, and rationale fields.

This slice improves usability only. It must not change review decision
semantics, API payloads, claim meanings, pipeline execution, or evidence claims.

## UI Planning Fallback

The repo asks for `/ui-planning` for non-trivial UI work, but that skill is not
available in this Codex session. Fallback used: read
`~/.claude/UI_PLAN_TEMPLATE.md`, keep the work in the existing static HTML
template, predefine the API contract/acceptance criteria here, and verify with
HTTP plus headless browser checks.

## API Contract Table

| Component / Action | Method | Endpoint | Request | Response type | Notes |
|--------------------|--------|----------|---------|---------------|-------|
| Review page shell | GET | `/review/{project_id}` | none | HTML | Existing page; add static orientation markup. |
| Codes tab data | GET | `/projects/{project_id}/review/codes` | none | existing JSON | No API change. |
| Claims tab data | GET | `/projects/{project_id}/review/claims` | existing query defaults | existing JSON | No API change. |
| Negative cases tab data | GET | `/projects/{project_id}/review/negative-cases` | existing query defaults | existing JSON | No API change. |
| Relationships tab data | GET | `/projects/{project_id}/review/relationships` | existing query defaults | existing JSON | No API change. |
| Save decisions | POST | `/projects/{project_id}/review/decisions` | existing decision payload | existing JSON | No API change. |

## Wireframe

```text
Header: project, status, counts, graph link
Orientation strip: "Start here" + 3 step review checklist
Legend/help row: confidence/support/evidence/decisions definitions
Tabs: Codes | Claims | Negative Cases | Relationships
Per-tab note: what to inspect in this tab
Cards: action buttons with titles, metrics with tooltips, evidence anchors
```

## State Inventory

| State | Type | Lives in | Initial value | Set by | Read by |
|-------|------|----------|---------------|--------|---------|
| `reviewMode` | string | existing JS variable | `"codes"` | tab buttons | data loader, tab help text |
| `projectData` | object | existing JS variable | `null` | GET route | renderer |
| `decisions` | Map | existing JS variable | empty | action buttons | submit/render |
| `expandedCodes` | Set | existing JS variable | empty | application toggles | code cards |

No new persisted state is needed.

## Agent Test Plan

With the demo server running:

```bash
curl -s http://127.0.0.1:8002/review/reviewer-demo | rg "Start here|What to inspect|title=\"Approve"
curl -s http://127.0.0.1:8002/projects/reviewer-demo/review/negative-cases?limit=1 | jq '.returned'
```

Expected: the HTML contains the orientation copy and tooltips; API routes still
return existing data.

## Files Affected

- `qc_clean/plugins/api/review_ui.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/REVIEW_UI_ORIENTATION_AIDS.md` (create, then move to completed)

## Plan

1. Add focused tests proving the rendered review HTML includes the orientation
   strip, per-tab help container, and representative tooltips/ARIA labels.
2. Add CSS/HTML for the orientation strip and tab guidance.
3. Add JS helper functions for active-mode guidance and reusable tooltip/title
   strings.
4. Add tooltips/ARIA labels to tabs, global actions, card actions, confidence
   values, status/support/review pills, application toggles, evidence anchors,
   and rationale inputs.
5. Verify with focused tests, Ruff, docs checks, demo server HTTP checks, and a
   headless browser text check.

## Required Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_review_page_exposes_orientation_aids` | HTML includes Start Here/checklist/tab help and representative tooltips. |
| `tests/test_review_api.py` | existing review UI tests | Existing review UI endpoints/buttons/render functions remain exposed. |

## Acceptance Criteria

- [ ] Review page gives a concise "Start here" instruction strip before cards.
- [ ] Review page gives per-tab "What to inspect" guidance for Codes, Claims,
  Negative Cases, and Relationships.
- [ ] Ambiguous buttons and metrics have native tooltips and accessible labels.
- [ ] The guidance distinguishes software review from methodological validity
  or SOTA evidence.
- [ ] Existing review API routes and decision actions remain unchanged.
- [ ] Focused review UI tests pass.
- [ ] Focused Ruff passes.
- [ ] Demo server serves the updated review page and headless browser confirms
  the orientation text appears.
- [ ] `make docs-check` and `git diff --check` pass.
- [ ] Verified work is committed and pushed.

## Open Questions

- [ ] Should this become a separate reviewer landing page instead of inline
  guidance? — Status: DEFERRED | Reason: the user needs immediate orientation
  on the current HTML page; a dedicated landing page can follow if this is still
  unclear.
