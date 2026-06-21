# Plan #14: INV-4 Category Saturation Diagnostic

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-4 category-level saturation; theoretical sampling protocol

---

## Outcome

Completed 2026-06-21. Added `CategorySaturationDiagnostic` and
`CategorySaturationSummary` domain models plus
`assess_category_saturation()` in `qc_clean/core/pipeline/saturation.py`.
`phase0_scorecard()` now includes `category_saturation`, reporting each
category's property count, dimension count, supporting applications/documents,
status, and gaps. The diagnostic is explicitly separate from the existing
codebook-stability `check_saturation()` path.

This is an adequacy diagnostic only. It does not implement theoretical sampling,
expert GT-fidelity adjudication, or a methodological saturation proof. INV-4
remains PARTIAL.

Verification: `python -m pytest tests/test_category_saturation_inv4.py tests/test_bench_phase0.py tests/test_cross_interview.py -q`
passed (`24 passed`) and Ruff passed on touched files before the implementation
commit. Final plan completion was verified with `make check`.

---

## Gap

**Current:** The repo distinguishes codebook stability from GT category
saturation in prose, and `check_saturation()` explicitly labels its result as
codebook convergence. There is no separate computable category-level diagnostic
for whether GT categories have enough properties, dimensions, and source support
to be treated as developed.

**Target:** Add a deterministic `assess_category_saturation()` diagnostic that
reports category-level adequacy separately from codebook stability. Surface it
in the Phase 0 scorecard as a diagnostic-only section, not a proof of true GT
saturation.

**Why:** INV-4 requires stability and saturation to be separate, separately
labeled outputs. A category diagnostic is the smallest concrete step toward
that invariant and gives future theoretical sampling work a target list of weak
categories.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:257` - INV-4 status: codebook stability exists; category saturation unmet.
- `docs/PROJECT_THEORY_AND_GOALS.md:329` - roadmap: true theoretical sampling + per-category saturation closes INV-4.
- `qc_clean/core/pipeline/saturation.py` - current codebook-stability check.
- `qc_clean/core/pipeline/theoretical_sampling.py` - current uncoded-document suggestion heuristic.
- `qc_clean/core/bench.py` - Phase 0 scorecard surface.
- `qc_clean/schemas/domain.py` - `Code`, `CodeApplication`, and existing saturation result models.
- `tests/test_cross_interview.py` - current saturation and theoretical-sampling tests.
- Memory context: `agent-memory recall 'active decisions category saturation theoretical sampling INV-4 qualitative_coding grounded theory' --project qualitative_coding` — no active blocking decision surfaced.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This slice is a
labeling and diagnostic separation step, not a methodological-saturation model.

---

## Capabilities

This plan modifies internal diagnostics only; it does not create a cross-project
callable capability.

---

## Files Affected

- `qc_clean/schemas/domain.py` (modify)
- `qc_clean/core/pipeline/saturation.py` (modify)
- `qc_clean/core/bench.py` (modify)
- `tests/test_cross_interview.py` or `tests/test_category_saturation_inv4.py` (modify/create)
- `tests/test_bench_phase0.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV4_CATEGORY_SATURATION_DIAGNOSTIC.md` (create, then move to completed)

---

## Plan

### Steps

1. Add Pydantic result models for per-category saturation diagnostics.
2. Implement `assess_category_saturation(state, ...)` using deterministic
   thresholds for properties, dimensions, supporting documents, and applications.
3. Include underdeveloped/developing/adequate categories plus a clear note that
   the result is a diagnostic, not proof of theoretical saturation.
4. Surface the diagnostic in `phase0_scorecard`.
5. Add tests for underdeveloped categories, adequate categories, and scorecard
   metadata.
6. Update docs conservatively: INV-4 improves from only codebook stability to
   separate diagnostic surface, but true theoretical sampling and saturation
   remain unmet/partial.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_category_saturation_inv4.py` | `test_category_saturation_flags_underdeveloped_categories` | Missing properties/dimensions/support are reported separately from codebook stability. |
| `tests/test_category_saturation_inv4.py` | `test_category_saturation_marks_adequate_categories_without_claiming_gt_saturation` | Adequate deterministic thresholds still carry diagnostic-only framing. |
| `tests/test_bench_phase0.py` | `test_scorecard_includes_category_saturation_diagnostic` | Phase 0 scorecard exposes the diagnostic section. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_cross_interview.py` | Existing codebook saturation semantics unchanged. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Codebook stability and category saturation diagnostics remain distinct.
- [ ] Each category reports property count, dimension count, supporting application count, supporting document count, status, and gaps.
- [ ] The overall diagnostic states whether all observed categories meet the deterministic adequacy thresholds.
- [ ] Phase 0 scorecard includes the diagnostic without claiming true GT saturation.
- [ ] Docs keep INV-4 partial unless theoretical sampling and methodological saturation are built.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] What thresholds should public evaluation pre-register? — Status: DEFERRED | Why it matters: this slice uses configurable deterministic defaults; public GT fidelity needs expert-rubric thresholds.
- [ ] Should theoretical sampling consume this diagnostic directly? — Status: DEFERRED | Why it matters: likely yes, but this plan only creates the category-level signal.

---

## Notes

This is not a grounded-theory saturation claim. It is a fail-loud, inspectable
diagnostic that prevents codebook stability from being mistaken for category
adequacy.
