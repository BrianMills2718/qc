# Plan #60: Confidence Calibration Wilson Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Calibration benchmark uncertainty metadata

---

## Gap

**Current:** The confidence-calibration scorecard reports accuracy, mean
confidence, Brier score, fixed-bin expected calibration error, bin summaries,
and per-surface summaries. It does not report uncertainty intervals for accuracy
overall, by calibration bin, or by surface.

**Target:** Add Wilson intervals for confidence-calibration accuracy at the
overall summary level, each non-empty calibration bin, and each per-surface
summary. Empty bins keep explicit `None` interval bounds through the existing
Wilson helper. This remains local uncertainty metadata, not proof that
confidence is calibrated.

**Why:** Calibration data is label-dependent and often sparse. Accuracy point
estimates without denominators and intervals are too easy to overread.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - confidence calibration substrate and caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - measured/not-validity claim discipline.
- `qc_clean/core/bench.py` - confidence-calibration scorecard and Wilson helper.
- `tests/test_bench_phase0.py` and `tests/test_bench_phase0_script.py` -
  calibration scorecard/file coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with provider errors; circuit breaker applies. No
  active local coordination claims were present.

---

## Research Basis For This Slice

No external research needed. This reuses the existing Phase 0 Wilson interval
helper already used for D3/D7 and D9 local uncertainty metadata.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Confidence calibration accuracy intervals | confidence/correctness records | Wilson accuracy intervals in calibration summary/bin/surface rows | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [ ] Overall confidence-calibration summary includes `accuracy_ci`.
- [ ] Non-empty calibration bins include Wilson `accuracy_ci` with successes and denominator.
- [ ] Empty calibration bins include Wilson `accuracy_ci` with `None` bounds.
- [ ] Per-surface summaries inherit the same accuracy interval behavior.
- [ ] Docs preserve the caveat that intervals are local uncertainty metadata, not calibration proof.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify if needed)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add `accuracy_ci` to `_confidence_calibration_summary` using correct count
   and total records.
2. Add `accuracy_ci` to each `_calibration_bins` row using correct count and
   bin count, including empty-bin undefined intervals.
3. Update focused tests for overall, bin, and per-surface interval metadata.
4. Update docs to note the new local interval metadata without upgrading the
   evidentiary claim.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | confidence calibration outcomes | Overall, bin, and by-surface `accuracy_ci` fields. |
| `tests/test_bench_phase0_script.py` | confidence calibration file | External file path still scores with interval metadata and no mutation. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing calibration scorecard tests | Existing accuracy/Brier/ECE values must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Overall calibration score includes Wilson `accuracy_ci`.
- [ ] Calibration bins include Wilson `accuracy_ci`.
- [ ] Surface summaries include Wilson `accuracy_ci`.
- [ ] Existing calibration metrics are unchanged.
- [ ] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should the future prompt_eval-backed calibration benchmark add bootstrap
  or reliability-diagram confidence bands? - Status: DEFERRED | Why it matters:
  public calibration claims need frozen labels and richer statistics; this
  slice only adds local Wilson intervals.
