# Plan #63: D8 GT-Fidelity Bootstrap Intervals

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #62
**Blocks:** D8 benchmark uncertainty metadata

---

## Outcome

D8 GT-fidelity scorecards now include deterministic local rubric-mean bootstrap
intervals when `phase0_rubric_bootstrap` is enabled. The scorecard reports
`overall_mean_ci`, per-metric `mean_ci`, per-evaluator-type overall/metric
intervals, and per-scope overall/metric intervals. The shared
`phase0_rubric_bootstrap.enabled=false` setting suppresses the interval fields.
This remains local uncertainty metadata for supplied rubric rows, not
expert-rubric acceptance, methodological saturation proof, or full grounded
theory evidence.

## Verification

- `python -m pytest tests/test_bench_phase0.py -q` - 54 passed
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - clean
- `python scripts/check_markdown_links.py` - clean
- `python scripts/sync_plan_status.py --check` - clean
- `make check` - 773 passed, 1 skipped, 8 deselected; lint and docs checks clean; type check not configured

## Gap

**Current:** The D8 GT-fidelity scorecard reports externally supplied rubric
outcomes as metric summaries, overall mean, evaluator-type summaries, and scope
summaries. It does not report uncertainty intervals for those rubric means.

**Target:** Reuse the existing `phase0_rubric_bootstrap` helper to add
deterministic local bootstrap intervals for D8 mean rubric scores:
`overall_mean_ci`, per-metric `mean_ci`, per-evaluator-type overall/metric
intervals, and per-scope overall/metric intervals. The existing
`phase0_rubric_bootstrap.enabled=false` setting must suppress D8 interval fields.

**Why:** D8 is a high-risk methodological-validity surface. Sparse rubric means
without interval metadata are too easy to overread as GT-fidelity evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D8 target and full benchmark caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - GT-fidelity and methodological-validity claim discipline.
- `qc_clean/core/bench.py` - D8 scorecard and reusable rubric bootstrap helper from Plan #62.
- `tests/test_bench_phase0.py` - D8 scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is local descriptive
uncertainty metadata for supplied rubric rows, not expert-rubric acceptance or
proof of full grounded theory.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D8 rubric mean bootstrap intervals | GT-fidelity rubric records | deterministic bootstrap CIs for D8 rubric means | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] D8 overall summary includes `overall_mean_ci` when bootstrap is enabled.
- [x] D8 metric summaries include `mean_ci` when bootstrap is enabled.
- [x] D8 per-evaluator-type summaries include overall and metric mean intervals.
- [x] D8 per-scope summaries include overall and metric mean intervals.
- [x] Existing `phase0_rubric_bootstrap.enabled=false` suppresses D8 interval fields.
- [x] Docs preserve the caveat that intervals are local uncertainty metadata, not GT-fidelity proof.

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

1. Thread `RubricBootstrapConfig` through D8 overall, metric, evaluator-type,
   and scope summary builders.
2. Add `overall_mean_ci` and metric `mean_ci` fields when rubric bootstrap is
   enabled.
3. Add focused tests for default D8 interval metadata and explicit disable behavior.
4. Update evaluation/theory docs and sprint tracker without upgrading D8 claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D8 GT-fidelity scorecard test | Overall, metric, evaluator-type, and scope bootstrap interval metadata. |
| `tests/test_bench_phase0.py` | D8 bootstrap disable test | `phase0_rubric_bootstrap.enabled=false` suppresses D8 interval metadata. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing D8 scorecard tests | Existing metric summaries, grouping, and fail-loud behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D8 overall mean has deterministic bootstrap CI metadata.
- [x] D8 per-metric means have deterministic bootstrap CI metadata.
- [x] D8 per-evaluator-type summaries have deterministic bootstrap CI metadata.
- [x] D8 per-scope summaries have deterministic bootstrap CI metadata.
- [x] Explicit bootstrap disable suppresses D8 interval fields.
- [x] Existing D8 point metrics are unchanged.
- [x] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should D8 eventually report agreement among expert raters separately from
  rubric-score intervals? - Status: DEFERRED | Why it matters: a populated D8
  benchmark needs an expert protocol and agreement statistics; this slice only
  adds local interval metadata for supplied rows.
