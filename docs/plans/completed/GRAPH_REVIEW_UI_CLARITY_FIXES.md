# Plan #208: Graph and Review UI Clarity Fixes

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Review UI Orientation Aids
**Blocks:** Brian review usability

---

## Outcome

Completed 2026-06-23. The review UI now labels the bulk action as
`Approve All Codes`, with tooltip text clarifying that it does not approve
claims, negative cases, or relationships. The graph UI now survives repeated
tab renders, explains flat code hierarchies, and renders the reviewer demo's
Code Relationships and Entity Map edges.

This is UI clarification and rendering repair only. It does not change API
payloads, project state contracts, review decision semantics, graph endpoint
contracts, claim meanings, methodological-validity claims, or SOTA claims.

## Gap

Brian found two concrete review-surface problems:

- `Approve All` is ambiguous. It currently approves all codes only, not claims,
  negative cases, or relationships.
- The graph page reports relationship/entity counts, but the visual graph tabs
  can look empty after switching tabs.

Investigation found the graph API data is present: reviewer demo graph data has
3 code nodes, 2 code relationship edges, 2 entity nodes, and 1 entity edge. The
rendering bug is in the graph HTML: the first Cytoscape render removes the
`loadingMsg` child node, and later tab switches try to access
`document.getElementById("loadingMsg").style`, throwing before re-render.

## Target

Clarify the review action label and repair graph tab rendering:

- Rename `Approve All` to `Approve All Codes`.
- Keep the button hidden outside the Codes tab.
- Guard missing graph loading placeholder during repeated Cytoscape renders.
- Add concise graph guidance/empty-state language so a flat Code Hierarchy is
  understandable.

No API payloads, project state, review decision semantics, graph endpoint
contracts, or claim meanings should change.

## Required Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_review_page_exposes_orientation_aids` | The review page names the bulk action as code-only. |
| `tests/test_graph_ui.py` | `test_graph_page_handles_repeated_tab_renders` | Graph HTML guards the missing loading placeholder and can show no-edge guidance. |

## Acceptance Criteria

- [x] Review UI bulk button reads `Approve All Codes`.
- [x] Graph UI no longer aborts tab re-render when `loadingMsg` is absent.
- [x] Code Relationships renders the demo's 2 relationship edges in the browser.
- [x] Entity Map renders the demo's 1 entity edge in the browser.
- [x] Code Hierarchy explains that no parent-child links can be a flat codebook,
  not necessarily missing relationship data.
- [x] Focused tests and Ruff pass.
- [x] Demo server is restarted and verified in a browser.
- [x] `make docs-check` and `git diff --check` pass.
- [x] Verified work is committed and pushed.

## Implementation Notes

- Renamed the review UI bulk action from `Approve All` to `Approve All Codes`
  and updated its tooltip to say it does not approve claims, negative cases, or
  relationships.
- Guarded the graph render path when the loading placeholder has already been
  removed after first Cytoscape initialization.
- Moved the graph empty-state note outside the Cytoscape-owned container so it
  survives tab switches.
- Added graph guidance text explaining the difference between Code Hierarchy,
  Code Relationships, and Entity Map.
- Added a flat-codebook note when Code Hierarchy has nodes but no parent-child
  edges.
- Regenerated `test_output/reviewer_demo` to reset accidental code approvals
  recorded during review of the old ambiguous button.

## Verification

- TDD red:
  `python -m pytest tests/test_review_api.py tests/test_graph_ui.py -q`
  initially failed because `Approve All Codes`, the graph render guard, and
  graph guidance text were absent.
- Focused tests:
  `python -m pytest tests/test_review_api.py tests/test_graph_ui.py -q`
  (`62 passed`).
- Focused Ruff:
  `python -m ruff check qc_clean/plugins/api/review_ui.py qc_clean/plugins/api/graph_ui.py tests/test_review_api.py tests/test_graph_ui.py`.
- Demo reset:
  `make reviewer-demo OUTPUT=test_output/reviewer_demo`.
- Browser verification after server restart:
  - Code Hierarchy rendered 3 nodes, 0 edges, and a visible flat-codebook note.
  - Code Relationships rendered 3 nodes and 2 edges with labels
    `tension_with` and `qualifies`.
  - Entity Map rendered 2 nodes and 1 edge labeled `requires_backup`.
  - Review UI rendered `Approve All Codes` with tooltip
    `Approve all visible codes only. This does not approve claims, negative cases, or relationships.`
- Docs gate: `make docs-check`.
- Whitespace gate: `git diff --check`.
- Full gate: `make check` (`1288 passed, 1 skipped, 8 deselected`; Ruff/docs
  passed; type check not configured).

## Notes

This is UI clarification and rendering repair only.
