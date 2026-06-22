# Plan #78: Claim Review API Listing

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #4 first-class claim ledger; Plan #5 claim review decisions
**Blocks:** browser-native claim review workflow; broader INV-10 adjudication surfaces

---

## Gap

**Current:** `ReviewManager` can apply review decisions to
`target_type="claim"`, and `/projects/{id}/claims` exposes a claim-ledger
summary. The browser-oriented review API only has a dedicated code listing at
`/projects/{id}/review/codes`; there is no review-target listing for claims.

**Target:** Add `GET /projects/{project_id}/review/claims` that returns bounded
claim rows for review with adjudication/support state, scope metadata, anchor
counts, revision-history count, and the same review summary used elsewhere.
Also verify claim decisions can be submitted through the existing review
decisions API.

**Why:** INV-10 requires adjudication beyond code labels. A claim-specific
review listing is the API substrate for browser-native claim review without
pretending expert adjudication has happened.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-10 and roadmap review gaps.
- `qc_clean/core/pipeline/review.py` - claim review decision support.
- `qc_clean/plugins/api/api_server.py` - review and claim endpoints.
- `tests/test_review.py` - ReviewManager claim-decision behavior.
- `tests/test_review_api.py` - FastAPI review endpoint tests.
- Memory context: `agent-memory recall 'claim review API listing' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No external research is needed. This is a deterministic API surface for an
existing claim-review state transition.

---

## Capabilities

This plan adds a repo-local API read surface. It does not create a new shared
capability or claim expert adjudication.

---

## Files Affected

- `qc_clean/plugins/api/api_server.py` (modify)
- `tests/test_review_api.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAIM_REVIEW_API_LISTING.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `GET /projects/{project_id}/review/claims`.
2. Return stable claim review rows with IDs, kind, source stage, support status,
   adjudication status, text, origin, scope, supporting/contrary anchor counts,
   and revision-history count.
3. Include project metadata, pipeline status, and `ReviewManager` summary in
   the response.
4. Register the endpoint in the API endpoint list.
5. Update the review-decision request description to include claim targets.
6. Add API tests for claim listing, missing project behavior, and claim decision
   submission through `/review/decisions`.
7. Update docs to mark API claim review listing as built while browser-native
   claim review remains future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review_api.py` | `test_returns_claims_for_review` | Claim review endpoint returns bounded claim rows and summary metadata. |
| `tests/test_review_api.py` | `test_404_for_missing_project` | Claim review endpoint fails loudly for missing projects. |
| `tests/test_review_api.py` | `test_claim_decision_persists` | Existing review decision endpoint applies claim review decisions. |
| `tests/test_project_commands.py` | existing endpoint registration test | Endpoint list includes the claim review route. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_review.py::TestReviewManager::test_claim_review_approve_reject_modify_updates_claim_adjudication` | Core claim review behavior remains intact. |
| `tests/test_review_api.py` | Existing review API behavior remains compatible. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `GET /projects/{project_id}/review/claims` returns claim review rows with
  status, scope, anchor counts, and revision count.
- [ ] Missing projects return HTTP 404.
- [ ] Existing `/projects/{project_id}/review/decisions` can persist claim
  approve/reject/modify decisions through the API.
- [ ] Endpoint list advertises the new route.
- [ ] Docs state this is an API substrate, not completed browser-native expert
  adjudication.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [x] Should this modify the browser HTML UI? — Status: RESOLVED | Answer: No.
  A UI workflow needs a separate UI-planning slice. This plan only creates and
  verifies the API contract it would consume.

---

## Notes

Do not claim INV-10 is complete after this slice. It adds claim listing and
decision submission coverage, but relationship/negative-case review and the
browser workflow remain gaps.
