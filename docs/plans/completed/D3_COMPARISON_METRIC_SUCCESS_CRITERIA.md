# Plan #178: D3 Comparison Metric Success Criteria

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** D3 baseline comparison score-time guard
**Blocks:** Held-out D3 application-baseline comparisons with pre-registered
machine-checkable pass/fail criteria

---

## Outcome

Implemented and pushed in commit `9ff1b87`.

The D3 comparison protocol module now includes
`evaluate_d3_comparison_metric_criteria()`, report/result models, exact metric
lookups, span-overlap diagnostic lookups, explicit missing-metric accounting,
and the same pass/fail/missing semantics as the completed D7 metric-criteria
lane. Guarded Phase 0 scoring now attaches
`application_validity_d3.metric_criteria_report` after a passing
`D3_PROTOCOL=...` preflight when the protocol includes criteria. Existing D3
scores, baseline deltas, span-overlap diagnostics, preflight behavior, output
writes, artifact writes, and no-criteria/unguarded scoring remain unchanged
except for the additive criteria report when configured.

Verification evidence:

- TDD red:
  `python -m pytest tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py -k "d3_comparison or d3_baseline" -q`
  initially failed during collection because
  `evaluate_d3_comparison_metric_criteria` did not exist.
- Focused D3 selection:
  `python -m pytest tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py -k "d3_comparison or d3_baseline" -q`
  passed: 17 passed, 41 deselected.
- Full touched D3 files:
  `python -m pytest tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py -q`
  passed: 58 passed.
- Focused Ruff:
  `python -m ruff check qc_clean/core/d3_comparison_protocol.py scripts/bench_phase0.py tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py`
  passed.
- Docs gate: `make docs-check` passed.
- Diff whitespace: `git diff --check` passed.
- Full gate: `make check` passed: 1173 passed, 1 skipped, 8 deselected; Ruff
  passed; docs-check passed; type check remains not configured.

This is local protocol/accounting infrastructure only. It is not held-out D3
evidence, live baseline evidence, expert parity, superiority evidence,
methodological-validity evidence, or SOTA evidence.

---

## Gap

**Current:** D3 comparison protocols already accept optional structured
`metric_criteria`, and `make bench D3_PROTOCOL=... D3_GOLD=...
D3_BASELINES=...` now enforces protocol/gold/baseline preflight at score time.
However, those structured D3 criteria are not evaluated against the Phase 0
scorecard, so guarded D3 comparisons still leave pass/fail success accounting
to manual inspection.

**Target:** Evaluate optional D3 comparison protocol metric criteria after a
passing score-time D3 preflight:

- Add a D3 metric-criteria evaluator in `qc_clean/core/d3_comparison_protocol.py`.
- Criteria can target exact D3 baseline metrics (`recall`, `precision`, `f1`)
  and existing local baseline span-overlap diagnostics
  (`mean_best_gold_iou`, `mean_best_predicted_iou`,
  `mean_best_gold_modified_hausdorff_distance`,
  `mean_best_predicted_modified_hausdorff_distance`).
- `scripts/bench_phase0.py` attaches a machine-readable
  `application_validity_d3.metric_criteria_report` only when
  `--d3-comparison-protocol-file` is supplied, preflight passes, and the
  protocol has criteria.
- Missing metrics produce explicit `status="missing"` rows and fail the
  criteria report; they do not silently pass or coerce to zero.
- Existing D3 exact-score, baseline, span-overlap, preflight, output, artifact,
  and unguarded scoring behavior remains unchanged except for the additive
  criteria report.

**Non-target:** This slice does not run or create baselines, collect held-out
labels, choose default D3 success thresholds, add semantic/multi-label D3
agreement, compare to human ceiling beyond existing metadata, or license
held-out D3 evidence, expert parity, superiority, methodological-validity, or
SOTA claims.

**Why:** D3 protocols now carry machine-checkable criteria, but the benchmark
boundary should be able to say whether a guarded comparison met those
pre-registered local thresholds. This is the D3 analogue of the completed D7
metric-criteria lane.

---

## References Reviewed

- `docs/plans/completed/D7_COMPARISON_METRIC_SUCCESS_CRITERIA.md` - completed
  D7 criteria pattern and verification expectations.
- `qc_clean/core/d7_comparison_protocol.py` - evaluator/report model pattern for
  exact and span-overlap criteria.
- `scripts/compare_d7_retrieval.py` - attaches criteria reports only after
  passing guarded comparison preflight.
- `qc_clean/core/d3_comparison_protocol.py` - D3 protocol already validates
  structured `metric_criteria`.
- `scripts/bench_phase0.py` - D3 score-time preflight, scorecard metadata, and
  output/artifact boundary.
- `qc_clean/core/bench.py` - D3 scorecard shape:
  `application_validity_d3.baselines.<name>` exact metrics plus
  `span_overlap` diagnostics.
- `tests/test_d3_comparison_protocol.py`, `tests/test_bench_phase0_script.py` -
  protocol validation and guarded D3 bench regression coverage.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions D3
  metric criteria qualitative_coding' --project qualitative_coding` returned
  only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This implements
the deterministic protocol/accounting layer already implied by the roadmap and
by the completed D7 metric-criteria design.

---

## Design Decisions

- Reuse the existing D3 `metric_criteria` schema shape; no schema-version bump.
- Add D3 report models mirroring D7:
  - `D3MetricCriterionResult`
  - `D3MetricCriteriaReport`
  - `D3MetricCriteriaStatus`
- Add `evaluate_d3_comparison_metric_criteria(protocol_payload, scorecard)`.
  It validates the supplied protocol payload, returns `None` when no criteria
  are configured, and otherwise reads the full Phase 0 scorecard at
  `application_validity_d3.baselines`.
- Attach the report at
  `application_validity_d3.metric_criteria_report`, not under `_meta`, because
  it evaluates D3 metrics rather than only recording preflight provenance.
- Missing `application_validity_d3`, missing `baselines`, missing baseline
  names, missing `span_overlap`, non-finite values, or non-numeric values all
  become explicit missing rows.
- Overall report `status` is `pass` only when every criterion passes; `fail`
  covers threshold failures and missing metrics.

---

## Capabilities

Internal D3 protocol/accounting capability only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `evaluate_d3_comparison_metric_criteria` | D3 comparison protocol JSON + Phase 0 scorecard JSON | D3 metric criteria report JSON or null | qualitative_coding | guarded `make bench`, `qc_cli.py bench`, benchmark package manifests, agents reviewing D3 reports | free |

### Capability Validation

- [x] Criteria can target exact D3 baseline metrics and span-overlap diagnostics.
- [x] Criteria cannot silently pass when metrics are absent or malformed.
- [x] Guarded Phase 0 output includes criteria result status when criteria are
  present.
- [x] Unguarded or no-criteria D3 scoring remains compatible.

---

## Files Affected

- `qc_clean/core/d3_comparison_protocol.py`
- `scripts/bench_phase0.py`
- `tests/test_d3_comparison_protocol.py`
- `tests/test_bench_phase0_script.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing tests for the D3 criteria evaluator and guarded Phase 0 report
   attachment.
2. Add D3 metric-criteria report models and evaluator helpers.
3. Attach the D3 criteria report in `scripts/bench_phase0.py` after a passing
   D3 preflight and scorecard generation.
4. Update docs with the criteria/accounting caveat and remaining evidence gap.
5. Regenerate `AGENTS.md`.
6. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
7. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d3_comparison_protocol.py` | `test_evaluate_d3_comparison_metric_criteria_returns_pass_fail_rows` | Evaluator returns pass/fail rows, counts, observed values, and overall fail when one criterion misses its threshold. |
| `tests/test_d3_comparison_protocol.py` | `test_evaluate_d3_comparison_metric_criteria_reports_missing_metrics` | Missing span-overlap diagnostics become explicit missing rows and fail the report. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d3_comparison_protocol_guard_includes_metric_criteria_results` | Guarded Phase 0 output includes `application_validity_d3.metric_criteria_report` when the protocol has criteria. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_d3_comparison_protocol_guard_reports_missing_metric_criteria` | Guarded Phase 0 output reports missing criteria rows when a configured diagnostic metric is unavailable. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py -k "d3_comparison or d3_baseline" -q` | New D3 protocol/bench behavior plus adjacent D3 guard regressions. |
| `python -m ruff check qc_clean/core/d3_comparison_protocol.py scripts/bench_phase0.py tests/test_d3_comparison_protocol.py tests/test_bench_phase0_script.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D3 metric criteria are evaluated deterministically against guarded Phase
  0 scorecards.
- [x] Criteria results include overall status, per-criterion pass/fail/missing
  status, observed values when available, and the pre-registered threshold.
- [x] Missing metrics fail explicitly.
- [x] Exact D3 TP/FP/FN, baseline deltas, span-overlap diagnostics, and
  preflight pass/fail behavior remain unchanged except for the additive
  criteria section.
- [x] Guarded D3 scorecards with no structured criteria remain compatible and
  omit the additive criteria report.
- [x] Docs state structured criteria are local protocol/accounting only, not
  held-out D3 evidence, live baseline evidence, expert parity, superiority,
  methodological-validity evidence, or SOTA.

> Process criteria:
- [x] TDD red state observed for at least one new protocol/bench test before
  implementation.
- [x] Focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Plan is moved to completed with verification evidence.
- [x] Verified implementation is committed and pushed.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Criteria report appears for unguarded scoring | Integration ignores protocol/preflight boundary | Only evaluate when `--d3-comparison-protocol-file` was supplied and preflight passed. |
| Criteria pass when metric is absent | Missing lookup coerced to `0.0` or falsey success | Return `observed_value=null`, `status="missing"`, and fail overall report. |
| Criteria change D3 exact scores | Evaluator mutates scorecard data before/while reading | Keep evaluator read-only over the completed scorecard and attach only an additive report. |
| Span-overlap criteria are overclaimed | Docs imply diagnostic metrics prove application validity | Keep report caution and docs explicit that these are local diagnostics. |
| Existing no-criteria protocols emit noisy reports | Evaluator does not return `None` for empty criteria | Preserve no-report behavior when `metric_criteria=[]`. |
| Full gate fails outside touched files | Inspect failing output; fix related regressions only, otherwise record proven unrelated state before proceeding. |
