# Plan #47: D5 Reliability Bootstrap Intervals

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D5 uncertainty reporting; reliability benchmark artifacts

---

## Outcome

D5 Phase 0 scorecards now report configurable, deterministic local row-bootstrap
intervals for LLM-pass reliability rows when IRR matrices are present. The
scorecard includes intervals for percent agreement and Gwet's AC1 on the
codebook-discovery matrix, application-level positive segment x code matrix, and
categorical segment-decision matrix; `phase0_reliability_bootstrap.enabled=false`
suppresses the D5 CI output without affecting D3/D7 exact-score bootstrap
intervals. Empty matrices return an explicit unavailable CI object. The output is
documented as consistency uncertainty metadata only, not human IRR, validity, or
expert-parity evidence.

**Verification:**
- `python -m pytest tests/test_bench_phase0.py -q` - 32 passed.
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - passed.
- `make check` - 732 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

## Gap

**Current:** D5 reliability scorecards report percent agreement, κ/Fleiss,
Gwet's AC1, and prevalence tables, but do not report confidence intervals. The
evaluation harness requires bootstrap CIs for reliability metrics.

**Target:** Add configurable local row-bootstrap intervals for D5 reliability
metrics in Phase 0. For each available reliability matrix, bootstrap rows with
replacement and report intervals for `percent_agreement` and `gwet_ac1`. Keep
the output labeled as local LLM-pass uncertainty metadata, not human IRR or
validity evidence.

**Why:** This closes the remaining local D5 statistical substrate gap without
requiring human data or `prompt_eval` frozen case sets.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D5 bootstrap CI requirement.
- `docs/PROJECT_THEORY_AND_GOALS.md` - LLM-pass consistency caveat.
- `qc_clean/core/bench.py` - Phase 0 scorecard and existing bootstrap config
  patterns.
- `qc_clean/core/pipeline/irr.py` - percent agreement and AC1 pure functions.
- `tests/test_bench_phase0.py` - D5 reliability scorecard tests.
- Memory context: `agent-memory recall 'qualitative_coding D5 reliability bootstrap confidence intervals AC1 percent agreement scorecard config' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This is a deterministic bootstrap over already stored
IRR matrix rows, matching the local-uncertainty pattern already used by D3/D7
exact-score intervals.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Reliability row-bootstrap CI | IRR matrix + bootstrap config | CI object for percent agreement and AC1 | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Binary reliability matrices get deterministic row-bootstrap intervals for
  percent agreement and AC1.
- [x] Categorical segment-decision matrices get deterministic row-bootstrap
  intervals for percent agreement and AC1.
- [x] `ProjectState.config.extra["phase0_reliability_bootstrap"].enabled=false`
  suppresses reliability CIs without affecting D3/D7 exact-score CIs.
- [x] Empty matrices omit CI output or report an explicit unavailable state.
- [x] Docs preserve the consistency-not-validity caveat.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `ReliabilityBootstrapConfig` under
   `ProjectState.config.extra["phase0_reliability_bootstrap"]`.
2. Add binary/categorical row-bootstrap helpers for percent agreement and AC1.
3. Attach CI objects to D5 scorecard sections when matrices are non-empty and
   bootstrap is enabled.
4. Add deterministic tests for default output and disabled config.
5. Update docs conservatively.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D5 default bootstrap test | Codebook/application/segment sections include deterministic CI objects. |
| `tests/test_bench_phase0.py` | D5 disabled bootstrap test | Disabling reliability bootstrap suppresses D5 CI output only. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Main scorecard shape. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] CI output includes method, confidence level, samples, seed, unit,
  population size, and metric intervals.
- [x] Default config is deterministic.
- [x] Disabled config suppresses D5 reliability CI output.
- [x] No human-IRR, validity, or expert-parity claim is introduced.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should final D5 benchmark CIs eventually come from `prompt_eval` instead
  of local row bootstrap? — Status: DEFERRED | Why it matters: public benchmark
  reporting should use the shared experiment/statistics layer once frozen case
  sets exist.
