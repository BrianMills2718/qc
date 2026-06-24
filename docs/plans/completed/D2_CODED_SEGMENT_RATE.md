# Plan #73: D2 Coded Segment Rate

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #3 segment universe; Plan #58 D1/D2 structural rate Wilson intervals
**Blocks:** richer D2 prevalence/accounting and future exhaustive-mode default decision

---

## Outcome

Phase 0 D2 coverage scorecards now include `coded_segment_rate` and
`coded_segment_rate_ci`. The rate is computed as `coded_segments /
examined_segments`, and traversal-mode projects with no segment decisions report
an undefined denominator rather than treating untouched text as no-code. This is
local examined-decision accounting only; it does not validate analytic coding or
population prevalence.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_segmentation.py -q` passed (68 tests);
`python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py`
passed; final `make check` passed (781 passed, 1 skipped, 8 deselected;
Ruff/docs-check passed). Type checking is not configured in this repo.

---

## Gap

**Current:** Phase 0 D2 coverage reports traversal coverage, examined segments,
and `coded_segments`, with Wilson intervals for `coverage_rate` and
`examined_rate`. It does not report a point estimate or interval for the rate of
examined segments judged `coded` rather than `no_code`.

**Target:** Add `coded_segment_rate` and `coded_segment_rate_ci` to the D2
coverage scorecard. The denominator must be `examined_segments`, not
`total_segments`, so traversal-mode projects with no decisions report an
undefined denominator instead of a misleading zero coded prevalence.

**Why:** This resolves the deferred question from Plan #58. Coded-vs-no-code
prevalence is useful in exhaustive mode and application-level agreement analysis,
but it must be labeled as local accounting over examined decisions, not analytic
validity or population prevalence.

---

## References Reviewed

- `docs/plans/completed/D1_D2_STRUCTURAL_RATE_WILSON_INTERVALS.md` - deferred
  coded-segment-rate question.
- `qc_clean/core/bench.py` - Phase 0 D1/D2 scorecard and Wilson interval helper.
- `qc_clean/core/segmentation.py` - `CoverageReport` fields and decision counts.
- `tests/test_bench_phase0.py` - D2 coverage scorecard tests.
- `tests/test_segmentation.py` - core coverage decision-count tests.
- `docs/EVALUATION_HARNESS.md` - D2 coverage status and Phase 0 surface.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-8 and D2 claim-discipline language.
- Memory context: `agent-memory recall 'D2 coded segment rate' --project qualitative_coding`
  was not rerun because prior attempts in this sprint failed repeatedly with
  OpenRouter 402/403 and the circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic scorecard accounting enhancement.

---

## Capabilities

This plan modifies a repo-local scorecard surface only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/D2_CODED_SEGMENT_RATE.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `coded_segment_rate` to `coverage_scorecard`, using
   `coded_segments / examined_segments` when at least one segment has a decision
   and `None` otherwise.
2. Add `coded_segment_rate_ci` using the existing Wilson helper with
   `coded_segments` successes and `examined_segments` denominator.
3. Extend D2 scorecard tests for traversal mode and mixed coded/no-code
   exhaustive decisions.
4. Update evaluation-harness and theory docs with the denominator caveat.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_coverage_note_is_conditional_on_exhaustive_mode` | Traversal-mode coded-segment rate is undefined; examined-mode coded rate uses examined decisions as the denominator. |
| `tests/test_bench_phase0.py` | `test_coverage_scorecard_reports_mixed_coded_segment_rate` | Mixed coded/no-code exhaustive decisions report the expected coded rate and Wilson counts. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Protect Phase 0 scorecard shape. |
| `tests/test_segmentation.py` | Protect core decision-count semantics. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D2 coverage scorecard reports `coded_segment_rate` as `None` when no
  segment decisions exist.
- [x] D2 coverage scorecard reports `coded_segment_rate` as
  `coded_segments / examined_segments` when decisions exist.
- [x] D2 coverage scorecard reports a Wilson `coded_segment_rate_ci` with
  successes=`coded_segments` and denominator=`examined_segments`.
- [x] Docs label the metric as local examined-decision accounting, not validity
  or population prevalence.

> Process criteria:
- [x] Required tests pass (`python -m pytest tests/test_bench_phase0.py tests/test_segmentation.py -q`: 68 passed)
- [x] Full test suite passes (`make check`: 781 passed, 1 skipped, 8 deselected; Ruff/docs-check passed)
- [x] Type check status is reported (`make check`: type check not yet configured)
- [x] Docs updated

---

## Open Questions

- [x] Should the coded-segment-rate denominator be total segments or examined
  segments? — Status: RESOLVED | Answer: examined segments. Total-segment
  denominator would imply uncoded prevalence in traversal mode where no segment
  decision was made.

---

## Notes

This is intentionally a Phase 0 local scorecard metric. It does not make
exhaustive mode the default and does not claim that the coded/no-code split is
methodologically valid without human/gold adjudication.
