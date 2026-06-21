# Plan #18: D7 Wilson Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** held-out D7 evaluation; prompt_eval-backed benchmark suite

---

## Gap

**Current:** `disconfirmation_d7_scorecard()` computes exact TP/FP/FN, recall,
precision, and F1 when adjudicated contrary-evidence gold is supplied. It does
not report uncertainty, so a future held-out D7 run would only show point
estimates.

**Target:** Add deterministic 95% Wilson score intervals for D7 recall and
precision. Keep the scorecard LLM-free and dependency-free. Do not add F1
bootstrap or baseline deltas in this slice; those belong in the later
`prompt_eval` benchmark suite.

**Why:** The evaluation harness requires confidence intervals before any public
claim. Wilson intervals are a small, deterministic improvement over raw point
scores and can be computed from the existing exact count substrate.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md:56` - D7 is recall/precision vs human-identified disconfirming evidence.
- `docs/EVALUATION_HARNESS.md:89` - benchmark protocol requires CIs alongside scored metrics.
- `docs/PROJECT_THEORY_AND_GOALS.md:324-328` - roadmap still lists held-out D7 runs with CIs/baselines as remaining work.
- `qc_clean/core/bench.py` - current D7 scorecard implementation.
- `tests/test_bench_phase0.py` - current D7 scoring contract tests.
- `docs/plans/completed/INV2_D7_DISCONFIRMATION_SCORECARD.md` - first D7 scorecard slice explicitly deferred confidence intervals.

---

## Research Basis For This Slice

Wilson score intervals are standard binomial proportion intervals and are
appropriate for recall and precision because both are proportions over finite
denominators. This is not the final statistical harness; it is a deterministic
Phase 0 interval substrate.

---

## Capabilities

This plan modifies an internal scorecard function only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D7_WILSON_INTERVALS.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a small `_wilson_interval(successes, total, confidence=0.95)` helper.
2. Add `recall_ci` using denominator `TP + FN`.
3. Add `precision_ci` using denominator `TP + FP`.
4. Represent undefined intervals explicitly when the denominator is zero.
5. Add tests for perfect match and mixed TP/FP/FN cases.
6. Update docs conservatively: D7 now has recall/precision interval estimates
   when gold is supplied, but no held-out benchmark, baseline comparison, F1
   bootstrap interval, or SOTA/parity claim exists.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_reports_d7_wilson_intervals_for_perfect_match` | D7 scorecard includes Wilson interval metadata for recall and precision. |
| `tests/test_bench_phase0.py` | `test_scorecard_reports_d7_wilson_intervals_for_mixed_counts` | Mixed TP/FP/FN intervals use the correct denominators and bound the point estimates. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Protect scorecard contract and D7 exact scoring. |
| `tests/test_bench_phase0_script.py` | External gold-file path still returns D7 scorecard. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Scored D7 output includes `recall_ci` and `precision_ci`.
- [ ] Intervals include method, confidence level, denominator, lower, and upper.
- [ ] Undefined denominators are explicit and do not crash.
- [ ] Existing TP/FP/FN, recall, precision, F1, and key lists remain compatible.
- [ ] Docs state these are Phase 0 interval estimates only, not held-out D7 validation or baseline comparison.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should F1 get a bootstrap interval now? — Status: DEFERRED | Why it matters: F1 depends jointly on precision and recall; deterministic Wilson intervals are enough for this slice, while full bootstrap belongs in `prompt_eval`.
- [ ] Should intervals be configurable beyond 95%? — Status: DEFERRED | Why it matters: future benchmark reports may support multiple levels, but a fixed 95% keeps Phase 0 simple and reviewable.

---

## Notes

This plan does not create a held-out D7 dataset. It only improves the scorecard
shape for the day a real adjudicated gold set is supplied.
