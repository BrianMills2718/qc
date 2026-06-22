# Plan #88: MCP Relationship Review

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Relationship review API decisions
**Blocks:** INV-10 agent-driven relationship adjudication; browser relationship review

---

## Outcome

Completed 2026-06-21. MCP now exposes `qc_review_relationships(project_id,
limit=100)` for bounded code/entity relationship review targets backed by
`ReviewManager.get_pending_relationships()`. The shared MCP review-decision
response now returns `relationships_count`, and MCP decision docstrings name the
`code_relationship` and `entity_relationship` target types.

This closes the MCP/agent first slice for relationship adjudication. It does not
add browser relationship review, negative-case-specific review UX, or expert
adjudication evidence.

Verification: initial TDD run failed as expected (`4 failed, 56 passed`) because
`qc_review_relationships` and `relationships_count` were missing. After
implementation, focused MCP tests passed (`60 passed`), Ruff passed on touched
files, docs/plan/AGENTS checks passed, and final `make check` passed (`828
passed, 1 skipped, 8 deselected`; type check not yet configured).

---

## Gap

**Current:** `ReviewManager` and the HTTP API can list and adjudicate
code/entity relationships, but MCP only exposes `qc_review_claims`,
`qc_review_decisions`, and the legacy `qc_review_codes` compatibility tool. MCP
agent clients cannot list relationship targets before submitting
`code_relationship` / `entity_relationship` decisions, and MCP decision results
do not return `relationships_count`.

**Target:** Add `qc_review_relationships(project_id, limit=100)` as a bounded
MCP listing tool backed by `ReviewManager.get_pending_relationships()`. Extend
the shared MCP review-decision response with `relationships_count`, and update
MCP docstrings to include relationship target types.

**Why:** This closes the MCP/agent first slice for relationship adjudication
after the API/manager semantics landed. It remains operational review plumbing,
not browser-native UX or expert adjudication evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:363` - INV-10 current status and remaining
  MCP/browser relationship review gap.
- `docs/plans/completed/RELATIONSHIP_REVIEW_API_DECISIONS.md` - completed
  API/manager relationship-review semantics.
- `qc_mcp_server.py` - existing `qc_review_claims`, `qc_review_decisions`, and
  `_apply_mcp_review_decisions` surfaces.
- `qc_clean/core/pipeline/review.py` - `get_pending_relationships()` and shared
  relationship decision handlers.
- `tests/test_mcp_server.py` - MCP review tests.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is an
agent-facing wrapper around already-implemented relationship review semantics.

---

## Capabilities

This modifies an existing MCP tool surface for this project. It does not create
a cross-project callable boundary.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/MCP_RELATIONSHIP_REVIEW.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `qc_review_relationships(project_id, limit=100)` returning bounded
   normalized relationship review rows, total count, summary, and `can_resume`.
2. Cap the MCP limit to `0..100`, matching `qc_review_claims`.
3. Add `relationships_count` to `_apply_mcp_review_decisions()` responses.
4. Update `qc_review_decisions` and `qc_review_codes` docstrings so relationship
   target types are discoverable.
5. Add MCP tests for listing, limit behavior, not-found behavior, and persisted
   relationship decisions.
6. Update docs conservatively: MCP relationship review is now available, but
   browser relationship review and expert adjudication remain future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_review_relationships` | MCP lists code/entity relationship review targets with explicit target types. |
| `tests/test_mcp_server.py` | `test_review_relationships_limit` | MCP relationship listing honors capped non-negative limits. |
| `tests/test_mcp_server.py` | `test_review_relationships_not_found` | Missing projects fail loud with an error payload. |
| `tests/test_mcp_server.py` | `test_review_decisions_relationship` | MCP review decisions persist code/entity relationship modifications/removals and return `relationships_count`. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_mcp_server.py -q` | MCP review tools remain compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_review_relationships` exists and returns bounded review rows.
- [x] Rows distinguish `code_relationship` and `entity_relationship`.
- [x] Limit handling matches `qc_review_claims` (`0..100`).
- [x] MCP review-decision results include `relationships_count`.
- [x] MCP can apply relationship decisions through the shared review manager.
- [x] Docs state this narrows INV-10 but does not add browser/expert review.

> Process criteria:
- [x] Required focused tests pass.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Verification

- Initial TDD run: `python -m pytest tests/test_mcp_server.py -q` - failed as
  expected because `qc_review_relationships` and `relationships_count` did not
  exist (`4 failed, 56 passed`).
- `python -m pytest tests/test_mcp_server.py -q` - passed (`60 passed`).
- `python -m ruff check qc_mcp_server.py tests/test_mcp_server.py` - passed.
- `python scripts/check_markdown_links.py && python scripts/sync_plan_status.py --check && python scripts/meta/check_agents_sync.py --check`
  - passed.
- `make check` - passed (`828 passed, 1 skipped, 8 deselected`); Ruff and docs
  gates passed; type check is not yet configured.

---

## Open Questions

- [ ] Should the browser review page get a Relationships mode next?
  - Status: DEFERRED | Why it matters: this plan closes agent/MCP access; human
  browser UX remains separate.
- [ ] Should negative-case review get a dedicated MCP listing separate from
  claim review?
  - Status: DEFERRED | Why it matters: negative cases are currently reachable as
  `ClaimKind.NEGATIVE_CASE` claim rows, but a specialized UX could surface
  candidate/disconfirmation context better.

---

## Notes

This plan intentionally reuses `ReviewManager.get_pending_relationships()` so
API and MCP relationship rows stay aligned.
