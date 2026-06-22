# Plan #66: D1/D2 Structural Rate Wilson Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Phase 0 foundational-rate uncertainty metadata

---

## Gap

**Current:** Phase 0 reports D1 grounding rate and D2 coverage/examined rates as
point estimates in the serialized scorecard. These are foundational structural
metrics, but they do not include denominator-aware uncertainty metadata.

**Target:** Add Wilson intervals to the Phase 0 scorecard serialization:
`grounding.grounding_rate_ci`, `coverage.coverage_rate_ci`, and
`coverage.examined_rate_ci`. The underlying `GroundingReport` and
`CoverageReport` dataclasses stay unchanged; interval metadata is scorecard
presentation only.

**Why:** D1/D2 rates are headline structural metrics. Sparse projects or tiny
test corpora should not make point estimates look more certain than they are.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D1/D2 targets and Phase 0 scorecard description.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-1/INV-8 status and claim discipline.
- `qc_clean/core/bench.py` - Phase 0 scorecard serialization and Wilson helper.
- `qc_clean/core/grounding.py` - `GroundingReport` fields.
- `qc_clean/core/segmentation.py` - `CoverageReport` fields.
- `tests/test_bench_phase0.py` - D1/D2 scorecard coverage.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with OpenRouter 402/403 provider errors; circuit
  breaker applies.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This reuses the existing
Phase 0 Wilson interval convention for local binomial-rate metadata.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D1/D2 structural rate intervals | ProjectState grounding/coverage reports | Wilson intervals in Phase 0 grounding and coverage sections | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [ ] Grounding scorecard includes `grounding_rate_ci`.
- [ ] Coverage scorecard includes `coverage_rate_ci`.
- [ ] Coverage scorecard includes `examined_rate_ci`.
- [ ] Interval counts match existing numerator/denominator fields.
- [ ] Empty denominators keep undefined Wilson bounds.
- [ ] Docs preserve the caveat that intervals are local uncertainty metadata, not validity evidence.

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

1. Add small scorecard serialization helpers for D1 grounding and D2 coverage
   that attach Wilson interval metadata.
2. Replace direct `asdict(verify_grounding(...))` / `asdict(compute_coverage(...))`
   calls in `phase0_scorecard` with those helpers.
3. Update focused D1/D2 tests for interval metadata and empty-denominator behavior.
4. Update evaluation/theory docs and sprint tracker without upgrading D1/D2 claim status.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D1 grounding scorecard test | `grounding_rate_ci` numerator/denominator and empty denominator behavior. |
| `tests/test_bench_phase0.py` | D2 coverage test | `coverage_rate_ci` and `examined_rate_ci` numerator/denominator. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing grounding/coverage scorecard tests | Existing rates and coverage-note behavior must not regress. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] D1 grounding rate has Wilson interval metadata.
- [ ] D2 coverage rate has Wilson interval metadata.
- [ ] D2 examined rate has Wilson interval metadata.
- [ ] Existing D1/D2 point metrics are unchanged.
- [ ] Docs preserve the caveat that this is local metadata only.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future Phase 0 scorecards add a coded-segment-rate point estimate
  and interval? - Status: DEFERRED | Why it matters: coded vs no-code prevalence
  may be useful, but this slice only adds intervals to existing public rates.
