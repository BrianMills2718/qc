# Plan #64: D9 Tie-Rate Wilson Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D9 preference scorecard uncertainty metadata

---

## Gap

**Current:** The D9 interpretive-preference scorecard reports forced-choice
system wins, human wins, ties, tie rate, non-tie system preference rate, and a
Wilson interval for non-tie system preference. Grouped evaluator/criterion
summaries inherit the same system-preference interval. Tie rate is still a point
estimate only.

**Target:** Add Wilson `tie_rate_ci` metadata wherever `_interpretive_preference_summary`
is used: overall D9 summary, by-evaluator summaries, and by-criterion summaries.
The interval uses ties as successes and total cases as denominator.

**Why:** Tie handling is central to D9 parity interpretation. A sparse tie-rate
point estimate can obscure whether raters frequently found outputs equivalent
or whether one or two ties are being overread.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D9 preference target, tie-rate reporting, and parity caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - D9 non-inferiority and claim discipline.
- `qc_clean/core/bench.py` - D9 preference summary and Wilson helper.
- `tests/test_bench_phase0.py` - D9 preference scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This reuses the existing
Phase 0 Wilson interval convention already used for D3/D7, D6, D9 preference
rate, and confidence-calibration scorecards.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D9 tie-rate intervals | forced-choice preference records | Wilson tie-rate intervals in D9 overall/group summaries | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [ ] Overall D9 summary includes `tie_rate_ci`.
- [ ] D9 by-evaluator summaries include `tie_rate_ci`.
- [ ] D9 by-criterion summaries include `tie_rate_ci`.
- [ ] Interval counts match ties and total-case denominators.
- [ ] Existing D9 preference and non-inferiority fields are unchanged.
- [ ] Docs preserve the caveat that this is local uncertainty metadata, not parity evidence.

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

1. Add `tie_rate_ci` to `_interpretive_preference_summary` using ties and total cases.
2. Update D9 focused tests for overall, by-evaluator, and by-criterion interval metadata.
3. Update evaluation/theory docs and sprint tracker without upgrading D9 claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D9 interpretive-preference scorecard test | Overall and grouped `tie_rate_ci` fields. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing D9 scorecard tests | Existing preference rate, Wilson interval, and non-inferiority behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Overall D9 tie rate has Wilson interval metadata.
- [ ] D9 grouped tie rates have Wilson interval metadata.
- [ ] Existing D9 point metrics are unchanged.
- [ ] Existing D9 non-inferiority assessment is unchanged.
- [ ] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future D9 scorecards report separate tie-adjusted preference
  variants? - Status: DEFERRED | Why it matters: public parity claims need a
  pre-registered protocol; this slice only adds local uncertainty metadata for
  the existing tie-rate field.
