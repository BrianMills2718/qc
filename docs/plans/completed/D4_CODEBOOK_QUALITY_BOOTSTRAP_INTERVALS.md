# Plan #62: D4 Codebook-Quality Bootstrap Intervals

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D4 benchmark uncertainty metadata

---

## Outcome

D4 codebook-quality scorecards now include deterministic local rubric-mean
bootstrap intervals when `phase0_rubric_bootstrap` is enabled. The scorecard
reports `overall_mean_ci`, per-metric `mean_ci`, and per-evaluator-type
overall/metric intervals. `phase0_rubric_bootstrap.enabled=false` suppresses
the interval fields. This remains local uncertainty metadata for supplied rubric
rows, not blind expert-panel evidence or proof of codebook validity.

## Verification

- `python -m pytest tests/test_bench_phase0.py -q` - 53 passed
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - clean
- `python scripts/check_markdown_links.py` - clean
- `python scripts/sync_plan_status.py --check` - clean
- `make check` - 772 passed, 1 skipped, 8 deselected; lint and docs checks clean; type check not configured

## Gap

**Current:** The D4 codebook-quality scorecard reports externally supplied
rubric outcomes as metric summaries, overall mean, evaluator-type counts, and
per-evaluator-type summaries. It does not report uncertainty intervals for
those rubric means.

**Target:** Add deterministic local bootstrap intervals for D4 mean rubric
scores: `overall_mean_ci`, per-metric `mean_ci`, and per-evaluator-type
`overall_mean_ci` / metric `mean_ci`. The bootstrap must be configurable through
project metadata and disabled explicitly when needed.

**Why:** D4 rubric datasets may mix LLM judges and human experts, often with
small sample sizes. Mean scores without interval metadata invite overclaiming
about codebook quality and evaluator-type differences.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D4 target and full benchmark caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - measured/not-validity claim discipline.
- `qc_clean/core/bench.py` - D4 scorecard, numeric summary, and existing bootstrap patterns.
- `tests/test_bench_phase0.py` - D4 scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is local descriptive
uncertainty metadata for supplied rubric rows, not a substitute for the planned
blind expert-panel protocol.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D4 rubric mean bootstrap intervals | codebook-quality rubric records | deterministic bootstrap CIs for D4 rubric means | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] D4 overall summary includes `overall_mean_ci` when bootstrap is enabled.
- [x] D4 metric summaries include `mean_ci` when bootstrap is enabled.
- [x] D4 per-evaluator-type summaries include overall and metric mean intervals.
- [x] Bootstrap metadata reports method, confidence level, samples, seed, unit, and population size.
- [x] Bootstrap can be disabled through project metadata.
- [x] Docs preserve the caveat that intervals are local uncertainty metadata, not expert-panel evidence.

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

1. Add a D4/rubric bootstrap config model with `enabled`, `samples`,
   `confidence_level`, and `seed`, loaded from `ProjectState.config.extra`.
2. Add a deterministic mean-bootstrap helper over numeric rubric rows using the
   existing percentile utility.
3. Wire `overall_mean_ci` and metric `mean_ci` into D4 overall and
   per-evaluator-type summaries when enabled.
4. Add focused tests for default interval metadata and explicit disable behavior.
5. Update evaluation/theory docs and sprint tracker without upgrading D4 claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D4 codebook-quality scorecard test | Overall, metric, and per-evaluator-type bootstrap interval metadata. |
| `tests/test_bench_phase0.py` | D4 bootstrap disable test | `phase0_rubric_bootstrap.enabled=false` suppresses D4 interval metadata. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing D4 scorecard tests | Existing metric summaries and fail-loud behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D4 overall mean has deterministic bootstrap CI metadata.
- [x] D4 per-metric means have deterministic bootstrap CI metadata.
- [x] D4 per-evaluator-type summaries have deterministic bootstrap CI metadata.
- [x] Explicit bootstrap disable suppresses D4 interval fields.
- [x] Existing D4 point metrics are unchanged.
- [x] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should the same rubric bootstrap helper be applied to D8 GT-fidelity
  rubric outcomes next? - Status: DEFERRED | Why it matters: D8 has a similar
  rubric scorecard, but this slice proves the helper on D4 first.
