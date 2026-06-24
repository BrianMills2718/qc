# Plan #153: Boundary Invalid Project ID Tests

**Status:** Complete
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** `ProjectStore` rejects traversal-like project IDs at the
persistence boundary, and many API/MCP surfaces catch missing projects, but the
documented maintenance backlog calls out missing API/MCP regression coverage for
invalid project IDs.

**Target:** Representative API and MCP project-ID boundaries have regression
tests proving invalid/traversal-style IDs produce explicit not-found/invalid
responses and do not resolve to existing project files.

**Why:** Project IDs are user- and agent-supplied boundary inputs. The store
already avoids ID rewriting, but API/MCP tests should lock that behavior at the
surfaces agents actually call.

---

## References Reviewed

- `CLAUDE.md` - maintenance follow-up listing invalid project-ID boundary tests.
- `qc_clean/core/persistence/project_store.py` - project ID regex,
  `InvalidProjectID`, and `ProjectStore.load/exists/delete` behavior.
- `tests/test_project_store.py` - existing persistence-boundary invalid-ID
  tests.
- `qc_clean/plugins/api/api_server.py` - API surfaces that call
  `ProjectStore.load` / `exists`.
- `tests/test_review_api.py` - existing FastAPI boundary fixture and missing
  project tests.
- `qc_mcp_server.py` - MCP tools that call `store.load` / `delete`.
- `tests/test_mcp_server.py` - MCP fixture with temp `ProjectStore`.
- Memory context:
  `agent-memory recall 'active decisions invalid project id boundary tests qualitative_coding' --project qualitative_coding`
  - 2 low-relevance historical findings, no active conflicting decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

Skipped: this plan adds/adjusts boundary regression coverage and does not create
a new callable capability.

---

## Files Affected

- `tests/test_review_api.py` - add API invalid project-ID regression tests.
- `tests/test_mcp_server.py` - add MCP invalid project-ID regression tests.
- `qc_clean/plugins/api/api_server.py` - modify only if tests expose an
  unhandled/ambiguous API boundary response.
- `qc_mcp_server.py` - modify only if tests expose an unhandled/ambiguous MCP
  boundary response.
- `CLAUDE.md` - remove the maintenance follow-up after completion.
- `AGENTS.md` - regenerated only if `CLAUDE.md` changes.

---

## Plan

### Steps

1. Add API tests for traversal-like project IDs against representative read,
   review, and mutation endpoints.
2. Add MCP tests for traversal-like project IDs against representative read,
   export/review, and delete tools.
3. Run focused tests and inspect failures.
4. If any boundary leaks an unsafe or ambiguous response, add the smallest
   production fix at that boundary.
5. Update maintenance docs and run docs sync/checks.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_invalid_project_ids_return_404_without_aliasing_existing_project` | API surfaces reject traversal/punctuation IDs and do not alias an existing project |
| `tests/test_mcp_server.py` | `test_invalid_project_ids_return_error_without_aliasing_existing_project` | MCP tools reject traversal/punctuation IDs and do not alias an existing project |
| `tests/test_mcp_server.py` | `test_delete_invalid_project_id_does_not_delete_existing_project` | MCP delete treats invalid IDs as not found and leaves existing project files intact |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_project_store.py -q` | Persistence boundary remains unchanged |
| `python -m pytest tests/test_review_api.py -q` | API review/scope/project boundaries remain unchanged |
| `python -m pytest tests/test_mcp_server.py -q` | MCP project/review/export boundaries remain unchanged |
| `make docs-check` | Plan/doc status and AGENTS sync remain valid |
| `make check` | Full deterministic gate remains green |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] Invalid/traversal-style API project IDs return explicit 404 responses.
- [ ] Invalid/traversal-style MCP project IDs return JSON error payloads.
- [ ] Invalid MCP delete IDs do not delete valid existing projects.
- [ ] Tests prove invalid IDs do not sanitize or alias to an existing project.

Process criteria:

- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [ ] None.

---

## Notes

This slice is coverage-first. It should not change project-ID syntax unless a
surface test demonstrates a real boundary leak.

## Closeout Notes

Completed 2026-06-22.

Outcome: Representative API and MCP project-ID boundaries now have regression
tests proving invalid/traversal-like IDs return explicit 404/error responses
and do not sanitize into existing project files. MCP delete coverage proves
invalid IDs do not delete valid saved projects. The existing persistence and
surface behavior already satisfied the tests, so no production boundary changes
were required.

Checkpoints:

- Plan checkpoint: `f441d90`
- Implementation checkpoint: `aa68b7a`

Verification:

- `python -m pytest tests/test_review_api.py -q` (`35 passed`)
- `python -m pytest tests/test_mcp_server.py -q` (`72 passed`)
- `python -m pytest tests/test_project_store.py -q` (`12 passed`)
- `make docs-check`
- `make check` (`1103 passed, 1 skipped, 8 deselected`)

Caveat: this is regression coverage for representative API/MCP project-ID
boundaries. It does not expand the project-ID syntax or implement a central
FastAPI path-parameter validator.
