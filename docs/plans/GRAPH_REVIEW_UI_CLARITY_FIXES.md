# Plan #208: Graph and Review UI Clarity Fixes

**Status:** Active
**Type:** implementation
**Priority:** High
**Blocked By:** Review UI Orientation Aids
**Blocks:** Brian review usability

---

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

- [ ] Review UI bulk button reads `Approve All Codes`.
- [ ] Graph UI no longer aborts tab re-render when `loadingMsg` is absent.
- [ ] Code Relationships renders the demo's 2 relationship edges in the browser.
- [ ] Entity Map renders the demo's 1 entity edge in the browser.
- [ ] Code Hierarchy explains that no parent-child links can be a flat codebook,
  not necessarily missing relationship data.
- [ ] Focused tests and Ruff pass.
- [ ] Demo server is restarted and verified in a browser.
- [ ] `make docs-check` and `git diff --check` pass.
- [ ] Verified work is committed and pushed.

## Notes

This is UI clarification and rendering repair only.
