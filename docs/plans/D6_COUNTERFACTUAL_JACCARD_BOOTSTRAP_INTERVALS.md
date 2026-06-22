# Plan #68: D6 Counterfactual Jaccard Bootstrap Intervals

**Status:** In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D6 bias-audit scorecard interpretability; future prompt_eval-backed counterfactual suite

---

## Gap

**Current:** The D6 counterfactual-bias scorecard reports invariant-case
code-change rate with Wilson intervals, plus mean code-set Jaccard distance as a
point estimate overall and by attribute.

**Target:** The same scorecard reports configurable deterministic local
bootstrap intervals for mean Jaccard distance overall and by attribute. The
intervals are disabled by explicit config, validated fail-loud when malformed,
and documented as uncertainty metadata over externally supplied records rather
than evidence of bias or bias absence.

**Why:** The evaluation harness bar is confidence-interval-first. D6 already
tracks a continuous distance metric, but leaving it as a point estimate makes
the scorecard weaker than adjacent D4/D8/calibration scorecards and less useful
for benchmark packages.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D6 bias scorecard target and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-5 status and D6 roadmap caveats.
- `docs/plans/completed/D6_COUNTERFACTUAL_BIAS_SCORECARD.md` - original D6
  scorecard scope.
- `docs/plans/completed/D6_COUNTERFACTUAL_CHANGE_RATE_WILSON_INTERVALS.md` -
  prior D6 interval slice and deferred Jaccard uncertainty question.
- `qc_clean/core/bench.py` - current D6 scorecard, bootstrap config patterns,
  and scorecard helpers.
- `tests/test_bench_phase0.py` - direct Phase 0 D6 coverage.
- `tests/test_bench_phase0_script.py` - CLI/script D6 external-file coverage.
- Memory context: unavailable. Prior repeated
  `agent-memory recall ... --project qualitative_coding` calls in this sprint
  failed with OpenRouter 402/403 provider errors; circuit breaker is active.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
measurement-substrate improvement using the existing deterministic bootstrap
pattern.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D6 counterfactual Jaccard interval scorecard | `ProjectState.config.extra["bias_counterfactual_evaluations"]` plus optional `phase0_counterfactual_bootstrap` object | `bias_counterfactual_d6.mean_jaccard_distance_ci` and per-attribute `mean_jaccard_distance_ci` | qualitative_coding | `make bench`, `qc_cli.py bench`, benchmark artifacts | free |

### Capability Validation

- [x] Input records already use `BiasCounterfactualEvaluation` with Pydantic
  field descriptions.
- [x] Bootstrap config defined as a Pydantic model with field descriptions.
- [x] Scorecard output is covered by focused tests and full docs checks.
- [x] No new cross-project callable boundary is introduced.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/D6_COUNTERFACTUAL_JACCARD_BOOTSTRAP_INTERVALS.md` (create, then move to completed at closeout)

---

## Plan

### Steps

1. Add `CounterfactualBootstrapConfig` and
   `phase0_counterfactual_bootstrap` config loading to `bench.py`.
2. Add a deterministic local row-bootstrap helper for mean Jaccard distance
   over invariant counterfactual cases.
3. Surface `mean_jaccard_distance_ci` overall and per attribute when enabled.
4. Add tests for default interval output, disabled config, and malformed config.
5. Update harness/theory docs without weakening existing caveats.
6. Run focused tests, plan sync, docs checks, and full `make check`.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_bias_counterfactual_outcomes` | D6 scored output includes overall and per-attribute Jaccard bootstrap intervals. |
| `tests/test_bench_phase0.py` | `test_scorecard_can_disable_bias_counterfactual_bootstrap_intervals` | `phase0_counterfactual_bootstrap.enabled=false` removes Jaccard interval fields while preserving point metrics. |
| `tests/test_bench_phase0.py` | `test_scorecard_invalid_bias_counterfactual_bootstrap_config_fails_loud` | Malformed D6 bootstrap config raises a clear `ValueError`. |
| `tests/test_bench_phase0_script.py` | `test_bench_phase0_scores_bias_counterfactual_from_file_without_mutating_state` | Script/CLI path surfaces the interval and still avoids persisted state mutation. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `pytest tests/test_bench_phase0.py -k "bias_counterfactual"` | Focused D6 scorecard behavior. |
| `pytest tests/test_bench_phase0_script.py -k "bias_counterfactual"` | External-file D6 path. |
| `python scripts/sync_plan_status.py --check` | Plan registry consistency. |
| `python scripts/check_markdown_links.py` | Docs link integrity. |
| `make check` | Full deterministic project gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Overall D6 score includes `mean_jaccard_distance_ci` by default when
  invariant cases are present.
- [x] Each per-attribute D6 summary includes `mean_jaccard_distance_ci` by
  default when invariant cases are present.
- [x] `phase0_counterfactual_bootstrap.enabled=false` suppresses interval fields
  without changing point metrics or Wilson code-change intervals.
- [x] Invalid `phase0_counterfactual_bootstrap` config fails loudly.
- [x] Existing D6 no-data and external-file behaviors remain unchanged.
- [x] Docs preserve the claim boundary: this is local uncertainty metadata, not
  a populated bias audit or causal proof.

> Process criteria:
- [x] Focused tests pass.
- [x] Plan sync passes.
- [x] Markdown link check passes.
- [x] Full `make check` passes, or any non-codebase failure is recorded.
- [ ] Verified implementation is committed and pushed.

---

## Open Questions

- [ ] Should future D6 packages also report stratified parity-delta bootstrap
  intervals across respondent attributes? - Status: DEFERRED | Why it matters:
  populated bias-audit claims need richer group-comparison uncertainty than this
  local invariant-case distance interval.

---

## Notes

- Bootstrap over externally supplied invariant-case rows is deterministic,
  local, and cheap. It should mirror the existing rubric/calibration patterns.
- This plan intentionally avoids generating counterfactual cases, running live
  models, or claiming bias evidence. Those remain prompt_eval/full-benchmark
  work.
