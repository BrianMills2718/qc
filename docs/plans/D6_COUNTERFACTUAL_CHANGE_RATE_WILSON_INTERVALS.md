# Plan #61: D6 Counterfactual Change-Rate Wilson Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D6 benchmark uncertainty metadata

---

## Gap

**Current:** The D6 counterfactual-bias scorecard reports invariant-case
code-change rate, changed/unchanged counts, mean code-set Jaccard distance,
changed case IDs, and per-attribute summaries for externally supplied
identity-cue swap outcomes. It does not report uncertainty intervals for the
binary changed-vs-unchanged rate.

**Target:** Add Wilson intervals for invariant-case code-change rate at the
overall D6 summary level and each per-attribute summary. The interval object
must carry successes (`changed_invariant_cases`), denominator
(`invariant_cases`), confidence level, and lower/upper bounds from the existing
Wilson helper.

**Why:** D6 cases will often be sparse and stratified. A point estimate alone is
too easy to overread, especially when a single changed case makes a small
attribute bucket look like a hard finding.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D6 scoring target and local-accounting caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-5 status and claim discipline.
- `qc_clean/core/bench.py` - D6 scorecard implementation and existing Wilson helper.
- `tests/test_bench_phase0.py` - D6 scorecard coverage.
- `tests/test_bench_phase0_script.py` - D6 external-file bench coverage.
- Memory context: unavailable. `agent-memory recall 'D6 counterfactual bias uncertainty intervals' --project qualitative_coding` failed on 2026-06-21 with OpenRouter 402/403 provider errors; prior repeated recall failures in this session triggered the circuit breaker.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This slice reuses the
existing local Wilson interval convention already used for D3/D7, D9, and
confidence-calibration scorecards.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D6 counterfactual change-rate intervals | counterfactual identity-swap records | Wilson intervals in D6 overall and by-attribute summaries | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [ ] Overall D6 summary includes `code_change_rate_ci`.
- [ ] Each per-attribute D6 summary includes `code_change_rate_ci`.
- [ ] Interval counts match changed and invariant-case denominators.
- [ ] Existing D6 code-change and Jaccard metrics are unchanged.
- [ ] Docs preserve the caveat that this is local uncertainty metadata, not bias proof.

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

1. Add `code_change_rate_ci` to `bias_counterfactual_scorecard` using changed
   invariant cases and total invariant cases.
2. Add `code_change_rate_ci` to `_bias_counterfactual_by_attribute` for each
   attribute bucket.
3. Update focused D6 tests for overall and per-attribute interval metadata.
4. Update evaluation and theory docs to mention D6 interval metadata without
   upgrading D6 claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D6 counterfactual scorecard test | Overall and by-attribute `code_change_rate_ci` fields. |
| `tests/test_bench_phase0_script.py` | D6 external file scorecard test | External D6 file path still scores with interval metadata and no mutation. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing D6 scorecard tests | Existing D6 counts, rates, Jaccard distance, and fail-loud behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Overall D6 score includes Wilson `code_change_rate_ci`.
- [ ] Per-attribute D6 summaries include Wilson `code_change_rate_ci`.
- [ ] Existing D6 metrics are unchanged.
- [ ] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should a future prompt_eval-backed D6 benchmark add bootstrap intervals
  for mean Jaccard distance and stratified parity deltas? - Status: DEFERRED |
  Why it matters: populated bias-audit claims require frozen counterfactual
  cases, ethical attribute handling, and richer statistics; this slice only
  adds local binary-rate uncertainty metadata.
