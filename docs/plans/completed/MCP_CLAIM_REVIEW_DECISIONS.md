# Plan #79: MCP Claim Review Decisions

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #78 claim review API listing; existing ReviewManager claim decisions
**Blocks:** agent-drivable INV-10 claim adjudication

---

## Gap

**Current:** `ReviewManager` supports `target_type="claim"` decisions, and the
API now exposes a claim review listing. The MCP tool is still named
`qc_review_codes`, documents only code/code-application/codebook targets, and
drops decision rationales before constructing `HumanReviewDecision`.

**Target:** Add a generic MCP review-decision tool that accepts code,
code-application, codebook, and claim targets with rationale/new_value. Keep the
existing `qc_review_codes` tool compatible by delegating to the same helper.

**Why:** INV-10 requires review beyond code labels, and agent-drivable review
needs an MCP surface that honestly advertises claim decisions instead of relying
on an undocumented code-review tool side effect.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-10 claim discipline.
- `qc_mcp_server.py` - `qc_get_claims`, `qc_review_summary`, and
  `qc_review_codes`.
- `tests/test_mcp_server.py` - MCP review tests.
- Memory context: `agent-memory recall 'MCP claim review decisions' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic MCP surface completion
for existing review behavior.

---

## Capabilities

This plan modifies the repo-local MCP agent surface. It does not create a new
shared capability or claim human/expert adjudication.

---

## Files Affected

- `qc_mcp_server.py` (modify)
- `tests/test_mcp_server.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/MCP_CLAIM_REVIEW_DECISIONS.md` (create, then move to completed)

---

## Plan

### Steps

1. Extract shared MCP review-decision application helper.
2. Include `rationale` when constructing `HumanReviewDecision`.
3. Add `qc_review_decisions(project_id, decisions)` as the generic MCP tool.
4. Keep `qc_review_codes` backward compatible by delegating to the helper, while
   updating its docstring to mention the generic replacement.
5. Return claim counts and remaining code counts in the review decision payload.
6. Add MCP tests for claim approval with rationale through the generic tool and
   backward-compatible claim review through `qc_review_codes`.
7. Update docs to state MCP claim review is agent-drivable but does not imply
   expert adjudication.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_mcp_server.py` | `test_review_decisions_claim` | Generic MCP tool persists a claim decision with rationale. |
| `tests/test_mcp_server.py` | `test_review_codes_delegates_claim_decision` | Existing MCP tool remains compatible and can pass claim decisions. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_mcp_server.py::TestReview::test_review_codes` | Existing MCP code review remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `qc_review_decisions` accepts review decisions for claim targets.
- [x] MCP claim decisions preserve `rationale` in claim revision history.
- [x] `qc_review_codes` remains backward compatible.
- [x] Review decision payload includes code and claim counts plus resumability.
- [x] Docs preserve the distinction between agent-drivable adjudication plumbing
  and expert-reviewed validity evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status is reported
- [x] Docs updated

## Verification

- `python -m pytest tests/test_mcp_server.py::TestReview::test_review_codes tests/test_mcp_server.py::TestReview::test_review_decisions_claim tests/test_mcp_server.py::TestReview::test_review_codes_delegates_claim_decision tests/test_mcp_server.py::TestReview::test_review_codes_invalid_action tests/test_mcp_server.py::TestReview::test_review_codes_empty tests/test_mcp_server.py::TestReview::test_review_codes_not_found -q` — 6 passed.
- `make check` — 796 passed, 1 skipped, 8 deselected; lint/docs passed; type check not yet configured.

## Outcome

MCP now exposes `qc_review_decisions` as a generic review-decision tool for code,
code-application, codebook, and claim targets. Decision rationale is preserved in
`HumanReviewDecision` and claim revision history. The existing
`qc_review_codes` tool remains compatible by delegating to the same helper.
This is agent-drivable adjudication plumbing, not expert-reviewed validity
evidence.

---

## Open Questions

- [x] Should `qc_review_codes` be removed or renamed? — Status: RESOLVED |
  Answer: No. Keep it for compatibility and add a better generic tool.

---

## Notes

Do not claim that an MCP-submitted decision is an expert decision. It is a
recorded review decision with whatever provenance the caller actually supplies.
