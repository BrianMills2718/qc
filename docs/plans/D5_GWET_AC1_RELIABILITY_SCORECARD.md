# Plan #45: D5 Gwet AC1 Reliability Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D5 prevalence-aware reliability reporting

---

## Gap

**Current:** `project irr --application-level` computes codebook-discovery,
positive segment x code, and segment-decision percent agreement plus κ/Fleiss
where applicable. `make bench` surfaces only a small codebook-discovery subset.
The evaluation harness explicitly requires prevalence-aware agreement reporting
with Gwet's AC1 because qualitative code applications are often sparse and κ can
collapse under skewed prevalence.

**Target:** Add Gwet's AC1 for binary code/application matrices and categorical
segment-decision matrices, persist it in `IRRResult`, and surface it in the
Phase 0 D5 reliability scorecard alongside the existing κ/Fleiss values. Keep
all labels clear: these are LLM-pass consistency metrics, not human IRR or
validity evidence.

**Why:** This advances the D5 harness without requiring new human data. It makes
prevalence attenuation visible and prepares the scorecard for later human
agreement lanes.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D5 requirement for bootstrap CIs,
  prevalence, and Gwet AC1 alongside κ.
- `docs/PROJECT_THEORY_AND_GOALS.md` - LLM-pass agreement is consistency, not
  human inter-rater reliability.
- `qc_clean/core/pipeline/irr.py` - existing binary/categorical agreement
  matrices and κ/Fleiss functions.
- `qc_clean/schemas/domain.py` - `IRRResult` persistence schema.
- `qc_clean/core/bench.py` - current Phase 0 D5 scorecard fields.
- `tests/test_irr_application_level.py` and `tests/test_bench_phase0.py` -
  existing reliability coverage.
- Memory context: `agent-memory recall 'qualitative_coding D5 reliability kappa AC1 prevalence bootstrap IRR application-level agreement' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. The harness already records the rationale: AC1 is
reported because κ is prevalence-sensitive under sparse qualitative code
applications. This slice implements the metric substrate only.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Gwet AC1 agreement metric | Binary/categorical IRR matrices | AC1 float + scorecard fields | qualitative_coding | `project irr`, `make bench`, exports | free |

### Capability Validation

- [ ] Binary AC1 computes perfect, partial, and prevalence-skewed examples.
- [ ] Categorical AC1 computes segment-decision agreement.
- [ ] `run_irr_analysis(..., application_level=True)` populates AC1 fields.
- [ ] `make bench` reliability section surfaces AC1 for codebook-discovery,
  positive application cells, and segment decisions when present.
- [ ] Docs preserve the consistency-not-validity caveat.

---

## Files Affected

- `qc_clean/core/pipeline/irr.py` (modify)
- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/bench.py` (modify)
- `tests/test_irr_application_level.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add pure AC1 helpers for binary and categorical agreement matrices.
2. Add optional AC1 fields to `IRRResult` for codebook-discovery,
   application-level positive cells, and segment decisions.
3. Populate AC1 in `run_irr_analysis`.
4. Expand the Phase 0 D5 reliability scorecard to surface application-level and
   segment-decision metrics.
5. Add deterministic tests and docs updates.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_irr_application_level.py` | binary AC1 examples | Perfect and sparse partial agreement return expected AC1. |
| `tests/test_irr_application_level.py` | categorical AC1 examples | Segment decision AC1 is computed for categorical rows. |
| `tests/test_irr_application_level.py` | application-level run | IRRResult stores AC1 for positive cells and segment decisions. |
| `tests/test_bench_phase0.py` | D5 scorecard AC1 | Phase 0 reliability section surfaces AC1 and application-level fields. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_irr_application_level.py` | Agreement matrix contracts remain stable. |
| `tests/test_bench_phase0.py` | Scorecard shape remains stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] AC1 helpers are deterministic pure functions.
- [ ] `IRRResult` carries AC1 fields without breaking existing serialized data.
- [ ] `run_irr_analysis` populates AC1 for available matrices.
- [ ] Phase 0 scorecard surfaces codebook-discovery, application-positive, and
  segment-decision AC1 fields when present.
- [ ] No human-IRR, validity, or expert-parity claim is introduced.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should D5 bootstrap confidence intervals be computed for AC1 in this repo
  or delegated to `prompt_eval`? — Status: DEFERRED | Why it matters: the
  harness calls for bootstrap CIs, but the existing local Phase 0 scorecard only
  has exact-key bootstrap machinery for D3/D7, so AC1 CIs should be a separate
  statistical-design slice.
