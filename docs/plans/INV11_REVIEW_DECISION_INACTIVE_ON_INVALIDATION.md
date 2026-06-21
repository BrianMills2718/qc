# Plan #23: INV-11 Review Decisions Inactive On Claim Invalidation

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** Plan #22 incremental hard invalidation
**Blocks:** fuller active-vs-historical review audit UX

---

## Gap

**Current:** Incremental recode hard-invalidates stale higher-order claims, but
`HumanReviewDecision` records targeting those claims remain indistinguishable
from decisions that still apply to current state. Deleting them would erase
audit history; leaving them active-looking can mislead downstream review
summaries and exports.

**Target:** Keep review decisions as audit history, but add active/inactive
metadata to `HumanReviewDecision`. During stale-claim invalidation, mark claim
review decisions whose target claims were removed as inactive with an explicit
reason and timestamp. Do not remove decisions, and do not mark decisions for
claims that remain current.

**Why:** This completes the active-vs-historical contract deferred in Plan #22:
claim review decisions survive as audit records without pretending to govern
claims removed from the current analysis state.

---

## References Reviewed

- `qc_clean/schemas/domain.py` - `HumanReviewDecision`, `ReviewSummary`, `AnalyticClaim`.
- `qc_clean/core/pipeline/stages/incremental_coding.py` - stale claim invalidation.
- `qc_clean/core/pipeline/review.py` - claim review decisions and summary.
- `tests/test_incremental_staleness_inv11.py` - invalidation tests.
- `tests/test_domain_model.py` - review-decision model tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-11 remaining review-decision caveat.
- Memory context: `agent-memory recall 'INV-11 review decisions active historical claim invalidation qualitative_coding' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional external research beyond repo-local references was needed. This is
an audit-state contract for an already-defined invariant.

---

## Capabilities

This plan modifies repo-local state models and incremental invalidation only; it
does not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/pipeline/stages/incremental_coding.py` (modify)
- `tests/test_domain_model.py` (modify)
- `tests/test_incremental_staleness_inv11.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify if operational wording changes)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV11_REVIEW_DECISION_INACTIVE_ON_INVALIDATION.md` (create, then move to completed)

---

## Plan

### Steps

1. Add defaulted review-decision activity fields:
   `is_active`, `inactive_reason`, and `inactive_at`.
2. Keep existing review decision creation active by default.
3. During `invalidate_stale_higher_order_outputs`, collect removed claim IDs
   before pruning claims.
4. Mark matching `target_type="claim"` review decisions inactive with a stable
   reason and timestamp.
5. Do not mark non-claim decisions or claim decisions whose target claim remains.
6. Add tests for default active decisions and invalidation-retired decisions.
7. Update docs to remove the remaining INV-11 review-decision caveat.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_domain_model.py` | `test_create` | Review decisions default to active and no inactive metadata. |
| `tests/test_incremental_staleness_inv11.py` | `test_invalidate_marks_review_decisions_for_removed_claims_inactive` | Stale claim decisions become inactive while retained-claim decisions remain active. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_review.py` | Review manager still creates/apply decisions. |
| `tests/test_incremental_staleness_inv11.py` | INV-11 invalidation behavior remains intact. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `HumanReviewDecision` has default-active metadata.
- [ ] Stale claim invalidation marks matching claim review decisions inactive.
- [ ] Review decisions for retained claims remain active.
- [ ] Non-claim review decisions remain active.
- [ ] Docs no longer list active-vs-historical review-decision handling as an open INV-11 gap.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should review summaries count active and inactive decisions separately? —
  Status: DEFERRED | Why it matters: useful for UX, but this slice establishes
  the state contract without changing CLI/API summary behavior.

---

## Notes

This preserves audit history. It intentionally does not delete historical
decisions that targeted now-invalidated claims.
