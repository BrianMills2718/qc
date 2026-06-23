# Plan #205: Review Surface Offset Pagination

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** Claim Ledger CLI/MCP Offset Pagination
**Blocks:** INV-10 agent-drivable review traversal

---

## Gap

**Current:** General claim-ledger read surfaces now support bounded
`limit`/`offset` traversal across API, MCP, and CLI. Review-specific API/MCP
list surfaces remain first-window only:

- API `/projects/{project_id}/review/claims` has a hard-coded 100-row slice and
  no explicit `limit`/`offset` metadata.
- API `/projects/{project_id}/review/negative-cases` and
  `/projects/{project_id}/review/relationships` expose `limit` but not
  `offset`.
- MCP `qc_review_claims`, `qc_review_negative_cases`, and
  `qc_review_relationships` expose `limit` but not `offset`.

**Target:** Add `offset` traversal to review-specific API/MCP list surfaces and
return applied `offset` metadata while preserving existing row shapes and
current per-page limit behavior.

**Why:** Human and agent review workflows need deterministic bounded traversal
of claim, negative-case, and relationship review rows. This is review-surface
pagination/accounting only; it does not add expert adjudication, held-out D3/D7
evidence, relationship validity, disconfirmation validity, or SOTA evidence.

---

## References Reviewed

- `docs/plans/completed/CLAIM_LEDGER_CLI_MCP_OFFSET_PAGINATION.md` - general
  claim-ledger MCP/CLI offset precedent.
- `docs/plans/completed/CLAIM_LEDGER_API_OFFSET_PAGINATION.md` - general API
  offset precedent.
- `qc_clean/plugins/api/api_server.py:465-545` - review API claims,
  negative-case, and relationship list endpoints.
- `qc_mcp_server.py:393-486` - MCP review claims, negative-case, and
  relationship list tools.
- `tests/test_review_api.py:335-455` - review API list tests.
- `tests/test_mcp_server.py:621-865` - MCP review list tests.
- `docs/PROJECT_THEORY_AND_GOALS.md:511` - INV-10 review caveats.
- Memory context:
  `agent-memory recall 'qualitative_coding review claims negative cases relationships offset pagination active decisions' --project qualitative_coding`
  — old completed outcomes only; no active decision.
- Coordination context: `~/.claude/coordination/claims/` contains only an
  unrelated `llm_client` write claim.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic
pagination parity over existing review rows.

---

## Capabilities

This plan modifies project-local API and MCP review list surfaces only. It does
not create a cross-project boundary, registry entry, or new evaluation
capability.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `qc_mcp_server.py` (modify)
- `tests/test_review_api.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/REVIEW_SURFACE_OFFSET_PAGINATION.md` (create)

---

## Plan

### Steps

1. Add TDD tests for API review claims, negative cases, and relationships with
   `limit=1&offset=1`.
2. Add TDD tests for MCP review claims, negative cases, and relationships with
   `limit=1, offset=1`.
3. Implement API offset slicing and response metadata.
4. Implement MCP offset slicing and response metadata.
5. Update docs to describe review pagination as traversal/accounting, not
   adjudication evidence.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and the full
   deterministic gate.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_review_claims_limit_offset` | API claim-review rows page by limit/offset and report offset. |
| `tests/test_review_api.py` | `test_review_negative_cases_limit_offset` | API negative-case review rows page by limit/offset and report offset. |
| `tests/test_review_api.py` | `test_review_relationships_limit_offset` | API relationship-review rows page by limit/offset and report offset. |
| `tests/test_mcp_server.py` | `test_review_claims_limit_offset` | MCP claim-review rows page by limit/offset and report offset. |
| `tests/test_mcp_server.py` | `test_review_negative_cases_limit_offset` | MCP negative-case review rows page by limit/offset and report offset. |
| `tests/test_mcp_server.py` | `test_review_relationships_limit_offset` | MCP relationship-review rows page by limit/offset and report offset. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_review_api.py tests/test_mcp_server.py -q` | Protect API/MCP review surfaces. |
| `python -m ruff check qc_clean/plugins/api/api_server.py qc_mcp_server.py tests/test_review_api.py tests/test_mcp_server.py` | Focused lint for modified files. |
| `make docs-check` | Plan/docs consistency and generated-agent sync. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] API review claims accepts `limit` and `offset`, reports both, and pages
  rows.
- [ ] API review negative cases accepts `offset`, reports it, and pages rows.
- [ ] API review relationships accepts `offset`, reports it, and pages rows.
- [ ] MCP review claims accepts `offset`, reports it, and pages rows.
- [ ] MCP review negative cases accepts `offset`, reports it, and pages rows.
- [ ] MCP review relationships accepts `offset`, reports it, and pages rows.
- [ ] Negative offsets clamp to zero where exercised by existing/new limit
  tests.
- [ ] Existing review row payload fields remain unchanged.

Process criteria:

- [ ] Required focused tests pass.
- [ ] Focused Ruff passes.
- [ ] `make docs-check` passes.
- [ ] `make check` passes or any failure is documented with evidence.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should browser UI add explicit next/previous controls for these review
  list APIs? — Status: DEFERRED | Why it matters: the JSON surfaces can page
  first; browser ergonomics should be a separate UI plan.

---

## Notes

Do not change review decision semantics. This plan only changes list traversal
and metadata.
