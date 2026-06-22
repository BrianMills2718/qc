# Plan #46: D5 Reliability Prevalence Tables

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D5 reliability interpretation; future reliability bootstrap CIs

---

## Gap

**Current:** D5 reliability now reports Gwet's AC1 alongside κ/Fleiss, but the
Phase 0 scorecard does not expose the underlying rating prevalence that explains
why κ may attenuate under sparse qualitative code applications.

**Target:** Add deterministic prevalence summaries to the Phase 0 reliability
scorecard for codebook-discovery binary matrices, positive segment x code
application matrices, and segment-decision categorical matrices when those
matrices are present in `IRRResult`.

**Why:** The evaluation harness requires prevalence to be reported alongside
κ/AC1. This slice makes base rates visible without claiming human IRR or
validity.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D5 requirement to report prevalence alongside
  κ/AC1.
- `docs/PROJECT_THEORY_AND_GOALS.md` - LLM-pass consistency caveat.
- `qc_clean/core/bench.py` - Phase 0 reliability scorecard section.
- `qc_clean/core/pipeline/irr.py` - stored binary and categorical agreement
  matrices.
- `tests/test_bench_phase0.py` - D5 scorecard coverage.
- Memory context: `agent-memory recall 'qualitative_coding D5 reliability prevalence tables kappa AC1 bootstrap scorecard' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This implements the documented D5 reporting
requirement that prevalence/base rates accompany agreement coefficients.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Reliability prevalence summary | IRR binary/categorical matrices | Category count/rate tables | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [ ] Binary prevalence summaries report rating counts/rates for absent/present.
- [ ] Categorical prevalence summaries report rating counts/rates for segment
  decisions.
- [ ] Empty matrices report explicit zero-row summaries, not errors.
- [ ] D5 scorecard includes prevalence tables where corresponding matrices are
  present.
- [ ] Docs preserve the consistency-not-validity caveat.

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

1. Add helper functions to summarize binary and categorical agreement-matrix
   prevalence.
2. Attach prevalence summaries to codebook-discovery, positive application-cell,
   and segment-decision reliability scorecard sections.
3. Add deterministic tests for populated and empty matrices.
4. Update docs conservatively.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | binary prevalence scorecard test | Codebook and application binary matrices report absent/present counts and rates. |
| `tests/test_bench_phase0.py` | categorical prevalence scorecard test | Segment-decision matrix reports coded/no_code/not_examined counts and rates. |
| `tests/test_bench_phase0.py` | empty prevalence test | Empty matrices produce explicit zero-row summaries. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Reliability scorecard shape. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Prevalence summaries include `row_count`, `rating_count`,
  `ratings_per_row`, category counts, and rates.
- [ ] Codebook-discovery prevalence is surfaced when `coding_matrix` exists.
- [ ] Application-positive and segment-decision prevalence are surfaced when
  `application_level=True`.
- [ ] No human-IRR, validity, or expert-parity claim is introduced.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should prevalence tables be exported by `project irr` directly? — Status:
  DEFERRED | Why it matters: the immediate D5 scorecard/artifact path needs
  prevalence first; CLI/export display can be expanded in a later UX-focused
  slice if the tables are too verbose for default output.
