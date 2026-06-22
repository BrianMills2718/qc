# Plan #82: INV-11 Narrow Surface Warnings

**Status:** Implemented
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #22 INV-11 hard invalidation
**Blocks:** safer agent/browser consumption of stale-output warnings

---

## Gap

**Current:** INV-11 `data_warnings` are surfaced in broad human/API/MCP/export
paths, but the theory doc still names narrower surfaces such as MCP
`qc_get_codebook` and graph UI endpoints as not echoing those warnings.

**Target:** Surface `data_warnings` on MCP `qc_get_codebook` and graph data
responses (`/projects/{id}/graph/codes`, `/projects/{id}/graph/entities`) when
warnings are present, without changing existing response shapes when warnings
are absent.

**Why:** Stale/invalidation warnings should travel with narrow codebook/graph
views so agents and browser clients do not silently consume outputs after a
recode invalidated higher-order state.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-11 remaining gap naming
  `qc_get_codebook` and graph UI.
- `qc_mcp_server.py` - `_warn_payload` and `qc_get_codebook`.
- `qc_clean/plugins/api/api_server.py` - graph code/entity endpoints.
- `tests/test_mcp_server.py` - MCP codebook tests.
- `tests/test_graph_ui.py` - graph response shape tests.
- Memory context: `agent-memory recall 'INV-11 narrow surface warnings' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic warning propagation for
existing state metadata.

---

## Capabilities

This plan modifies repo-local API/MCP response metadata. It does not create a
new shared capability.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `tests/test_graph_ui.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/INV11_NARROW_SURFACE_WARNINGS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `_warn_payload(state)` to the `qc_get_codebook` response.
2. Add `data_warnings` to code graph and entity graph responses only when
   warnings are present.
3. Add MCP regression for codebook warnings.
4. Add graph response-shape regressions for code/entity warnings.
5. Update docs to remove the named narrow-surface warning gap while keeping
   INV-11 partial because auto-recompute remains unimplemented.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_get_codebook_surfaces_data_warnings` | MCP codebook output carries state warnings. |
| `tests/test_graph_ui.py` | `test_code_graph_surfaces_data_warnings` | Code graph response carries warnings. |
| `tests/test_graph_ui.py` | `test_entity_graph_surfaces_data_warnings` | Entity graph response carries warnings. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_mcp_server.py::TestInspection` | Existing MCP inspection behavior remains compatible. |
| `tests/test_graph_ui.py` | Existing graph response shape remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] MCP `qc_get_codebook` includes `data_warnings` when the state has warnings.
- [x] Code graph endpoint response includes `data_warnings` when the state has warnings.
- [x] Entity graph endpoint response includes `data_warnings` when the state has warnings.
- [x] Warning-free responses remain unchanged.
- [x] Docs state INV-11 still lacks auto-recompute, but no longer name these
  narrow surfaces as warning gaps.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

## Verification

- `python -m pytest tests/test_mcp_server.py::TestInspection::test_get_codebook tests/test_mcp_server.py::TestInspection::test_get_codebook_surfaces_data_warnings tests/test_graph_ui.py::TestCodeGraphEndpoint::test_code_graph_surfaces_data_warnings tests/test_graph_ui.py::TestEntityGraphEndpoint::test_entity_graph_surfaces_data_warnings tests/test_graph_ui.py -q` — 17 passed.
- `make check` — 804 passed, 1 skipped, 8 deselected; lint/docs passed; type check not yet configured.

---

## Open Questions

- [x] Should graph HTML render a visible warning banner? — Status: DEFERRED |
  Answer: Not in this slice. The immediate gap is machine-readable graph data
  response warnings; a visible UI banner is a separate UI-planning slice.

---

## Notes

Do not claim INV-11 is complete. Auto-recompute after corpus mutation remains
future work.
