# Plan #24: Review Summary Active Inactive Counts

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** Plan #23 review-decision inactive metadata
**Blocks:** review audit UX

---

## Gap

**Current:** `HumanReviewDecision` now distinguishes active decisions from
historical-only inactive decisions, but `ReviewSummary` reports only
`existing_decisions`. CLI users and agents cannot see from the summary whether
some decisions no longer apply to current targets.

**Target:** Add `active_decisions` and `inactive_decisions` to `ReviewSummary`,
populate them in `ReviewManager.get_review_summary()`, and print them in the
review CLI while preserving `existing_decisions` as the total count.

**Why:** The state contract from Plan #23 is only useful if routine review
surfaces show when historical review decisions exist separately from active
decisions.

---

## References Reviewed

- `qc_clean/schemas/domain.py` - `ReviewSummary`, `HumanReviewDecision`.
- `qc_clean/core/pipeline/review.py` - summary construction.
- `qc_clean/core/cli/commands/review.py` - review summary display.
- `tests/test_review.py` - review summary tests.
- `tests/test_domain_model.py` - model defaults.
- Memory context: `agent-memory recall 'review summary active inactive decisions qualitative_coding INV-11 INV-10' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional external research beyond repo-local references was needed. This is
a local summary-surface follow-up to Plan #23.

---

## Capabilities

This plan modifies repo-local review summary surfaces only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/pipeline/review.py` (modify)
- `qc_clean/core/cli/commands/review.py` (modify)
- `tests/test_review.py` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/REVIEW_SUMMARY_ACTIVE_INACTIVE_COUNTS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `active_decisions` and `inactive_decisions` default counters to
   `ReviewSummary`.
2. Populate counters from `state.review_decisions` using `decision.is_active`.
3. Keep `existing_decisions` as total decisions for backward compatibility.
4. Print active/inactive counts in review CLI summary.
5. Add tests for mixed active/inactive decisions.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_review.py` | `test_review_summary_counts_active_and_inactive_decisions` | Total, active, and inactive review-decision counters are correct. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_review.py tests/test_domain_model.py` | Review model and manager behavior. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `ReviewSummary` includes active and inactive decision counters.
- [ ] `existing_decisions` remains the total decision count.
- [ ] `ReviewManager.get_review_summary()` computes all three counts.
- [ ] Review CLI prints active and inactive counts.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should API review summary expose the counters explicitly? — Status:
  RESOLVED | Answer: yes automatically, because FastAPI serializes the expanded
  `ReviewSummary` model.

---

## Notes

This does not change how decisions are applied. It only exposes the existing
active/inactive state in summary surfaces.
