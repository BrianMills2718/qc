# Plan #67: Confidence Calibration Bootstrap Intervals

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #60
**Blocks:** Confidence-calibration uncertainty metadata

---

## Outcome

Confidence-calibration scorecards now include deterministic local bootstrap
intervals for Brier score and fixed-bin ECE when
`phase0_calibration_bootstrap` is enabled. The same metadata appears in overall
and per-surface summaries. `phase0_calibration_bootstrap.enabled=false`
suppresses the interval fields. This remains local uncertainty metadata for
supplied confidence/correctness rows, not proof of calibrated confidence.

## Verification

- `python -m pytest tests/test_bench_phase0.py -q` - 55 passed
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - clean
- `python scripts/check_markdown_links.py` - clean
- `python scripts/sync_plan_status.py --check` - clean
- `make check` - 774 passed, 1 skipped, 8 deselected; lint and docs checks clean; type check not configured

## Gap

**Current:** Confidence-calibration scorecards report accuracy with Wilson
intervals, mean confidence, Brier score, fixed-bin expected calibration error
(ECE), calibration-bin summaries, and per-surface summaries. Brier score and ECE
are still point estimates.

**Target:** Add deterministic local bootstrap intervals for Brier score and ECE
in the overall calibration summary and per-surface summaries. The bootstrap must
be configurable through `ProjectState.config.extra["phase0_calibration_bootstrap"]`
and explicitly disableable.

**Why:** Calibration data is label-dependent and often sparse. Brier/ECE point
estimates without interval metadata are too easy to overread as calibration
evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - confidence-calibration substrate and caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - confidence-calibration claim discipline.
- `qc_clean/core/bench.py` - calibration summary, binning, Wilson helper, and bootstrap patterns.
- `tests/test_bench_phase0.py` - confidence-calibration scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is local descriptive
uncertainty metadata over supplied confidence/correctness rows, not a populated
held-out calibration benchmark.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Calibration metric bootstrap intervals | confidence/correctness records | deterministic bootstrap CIs for Brier score and ECE | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] Overall calibration summary includes `brier_score_ci` when bootstrap is enabled.
- [x] Overall calibration summary includes `expected_calibration_error_ci` when bootstrap is enabled.
- [x] Per-surface calibration summaries include Brier/ECE interval metadata.
- [x] Bootstrap metadata reports method, confidence level, samples, seed, unit, and population size.
- [x] Bootstrap can be disabled through project metadata.
- [x] Docs preserve the caveat that intervals are local uncertainty metadata, not calibration proof.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add `CalibrationBootstrapConfig` with `enabled`, `samples`,
   `confidence_level`, and `seed`.
2. Add deterministic bootstrap helpers that resample calibration rows and
   recompute Brier score and fixed-bin ECE.
3. Thread the config through overall and by-surface calibration summaries.
4. Add focused tests for interval metadata and explicit disable behavior.
5. Update evaluation/theory docs and sprint tracker without upgrading calibration claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | confidence calibration scorecard test | Overall and by-surface Brier/ECE interval metadata. |
| `tests/test_bench_phase0.py` | calibration bootstrap disable test | `phase0_calibration_bootstrap.enabled=false` suppresses interval metadata. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing confidence-calibration scorecard tests | Existing accuracy, Brier, ECE, bin, and per-surface point metrics must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Overall Brier score has deterministic bootstrap CI metadata.
- [x] Overall ECE has deterministic bootstrap CI metadata.
- [x] Per-surface Brier/ECE summaries have deterministic bootstrap CI metadata.
- [x] Explicit bootstrap disable suppresses calibration bootstrap interval fields.
- [x] Existing calibration point metrics are unchanged.
- [x] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should the future prompt_eval-backed calibration benchmark add reliability
  diagrams with confidence bands? - Status: DEFERRED | Why it matters: public
  calibration claims need frozen labels and richer artifacts; this slice only
  adds local bootstrap metadata to existing metrics.
