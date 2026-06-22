# Plan #80: MCP Claim Review Listing

**Status:** Implemented
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #78 claim review API listing; Plan #79 MCP claim review decisions
**Blocks:** agent-drivable INV-10 claim review workflow

---

## Gap

**Current:** MCP `qc_review_decisions` can apply claim decisions with rationale,
and `qc_get_claims` exposes a claim-ledger summary. MCP does not have a
claim-review-target listing with the same status/scope/anchor/revision fields as
the API `GET /projects/{id}/review/claims` endpoint.

**Target:** Add MCP `qc_review_claims(project_id, limit=100)` that returns
bounded claim review rows, project metadata, pipeline status, review summary,
and resumability. Keep `qc_get_claims` unchanged as the ledger-summary surface.

**Why:** Agent-driven claim review needs a direct MCP target list before
submitting decisions. This advances INV-10 plumbing without claiming expert
adjudication.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-10 review-surface caveats.
- `qc_mcp_server.py` - `qc_get_claims`, `qc_review_summary`,
  `qc_review_decisions`.
- `qc_clean/plugins/api/api_server.py` - API claim-review listing response.
- `tests/test_mcp_server.py` - MCP review tests.
- Memory context: `agent-memory recall 'MCP claim review listing' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is deterministic MCP response shaping for
existing claim-review state.

---

## Capabilities

This plan modifies the repo-local MCP agent surface. It does not create a shared
capability or claim expert adjudication.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/MCP_CLAIM_REVIEW_LISTING.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a small helper that serializes claim review rows with stable bounded
   fields.
2. Add MCP `qc_review_claims(project_id, limit=100)`.
3. Include project metadata, pipeline status, `returned`, `total_claims`,
   review summary, `can_resume`, and bounded claim rows.
4. Add tests for populated claim listing, limit handling, and missing project.
5. Update docs to mention MCP claim-review listing as agent-drivable plumbing,
   not expert adjudication.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_review_claims` | MCP returns bounded claim review rows with scope/status counts. |
| `tests/test_mcp_server.py` | `test_review_claims_limit` | MCP respects the requested claim row limit. |
| `tests/test_mcp_server.py` | `test_review_claims_not_found` | Missing project returns an error payload. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_mcp_server.py::TestReview` | Existing MCP review behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] MCP `qc_review_claims` returns claim review rows with status, scope,
  anchor counts, revision counts, and creation metadata.
- [x] Response includes project metadata, review summary, total/returned counts,
  and `can_resume`.
- [x] Limit handling is deterministic and non-negative.
- [x] Missing projects return an error payload.
- [x] Docs preserve the distinction between agent-drivable review plumbing and
  expert-reviewed validity evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

## Verification

- `python -m pytest tests/test_mcp_server.py::TestReview::test_review_claims tests/test_mcp_server.py::TestReview::test_review_claims_limit tests/test_mcp_server.py::TestReview::test_review_claims_not_found tests/test_mcp_server.py::TestReview::test_review_decisions_claim -q` — 4 passed.
- `make check` — 799 passed, 1 skipped, 8 deselected; lint/docs passed; type check not yet configured.

---

## Open Questions

- [x] Should this replace `qc_get_claims`? — Status: RESOLVED | Answer: No.
  Keep `qc_get_claims` as the compact ledger summary and add a review-specific
  surface.

---

## Notes

Do not expose unbounded claim lists through MCP. Keep the default and maximum
path bounded to avoid dumping large project state into agent context.
