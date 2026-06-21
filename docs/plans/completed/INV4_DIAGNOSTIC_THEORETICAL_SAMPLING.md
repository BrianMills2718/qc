# Plan #15: INV-4 Diagnostic-Driven Theoretical Sampling

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-4 theoretical sampling protocol

---

## Outcome

Completed 2026-06-21. `suggest_next_documents()` now calls
`assess_category_saturation()` and uses non-adequate category IDs as primary
`SamplingSuggestion.gap_codes`, falling back to the previous low-coverage
heuristic when no category-development gaps are present. Suggestion reasons now
distinguish category-development gaps from generic under-represented-code
coverage.

This remains sampling guidance among already-loaded uncoded documents. It does
not implement a full GT theoretical sampling protocol, persist sampling
decisions, select/collect new external data, or prove category saturation.
INV-4 remains PARTIAL.

Verification: `python -m pytest tests/test_cross_interview.py tests/test_category_saturation_inv4.py -q`
passed (`17 passed`) and Ruff passed on touched files before the implementation
commit. Final plan completion was verified with `make check`.

---

## Gap

**Current:** `suggest_next_documents()` recommends uncoded documents using a
simple low-coverage heuristic: code IDs with one or fewer applications become
gap codes. Plan #14 added category adequacy diagnostics, but theoretical
sampling does not consume them yet.

**Target:** Use `assess_category_saturation()` inside theoretical sampling so
underdeveloped/developing categories remain sampling targets even when they have
multiple applications but lack properties, dimensions, or document support.

**Why:** Theoretical sampling should develop weak categories, not merely add
more applications to rare codes. This is a small INV-4 step from generic
coverage toward category-development guidance.

---

## References Reviewed

- `qc_clean/core/pipeline/theoretical_sampling.py` - current low-coverage sampling heuristic.
- `qc_clean/core/pipeline/saturation.py` - new category adequacy diagnostic.
- `qc_clean/schemas/domain.py` - `SamplingSuggestion` and category diagnostic models.
- `tests/test_cross_interview.py` - current theoretical sampling tests.
- `docs/PROJECT_THEORY_AND_GOALS.md:257` - INV-4 partial status.
- `docs/plans/completed/INV4_CATEGORY_SATURATION_DIAGNOSTIC.md` - previous slice and remaining work.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic wiring step from the category diagnostic into the existing
sampling heuristic.

---

## Capabilities

This plan modifies an internal pipeline helper only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/pipeline/theoretical_sampling.py` (modify)
- `tests/test_cross_interview.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV4_DIAGNOSTIC_THEORETICAL_SAMPLING.md` (create, then move to completed)

---

## Plan

### Steps

1. Call `assess_category_saturation()` from `suggest_next_documents()`.
2. Use non-adequate category IDs as the primary gap-code list.
3. Preserve the existing low-coverage fallback for projects without diagnostic
   gaps.
4. Update suggestion reasons to distinguish category-development gaps from
   generic low coverage.
5. Add a regression where a code has multiple applications but remains a gap
   because it lacks properties/dimensions.
6. Update docs conservatively: this improves theoretical-sampling guidance but
   is not a full GT sampling protocol.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_cross_interview.py` | `test_sampling_uses_category_diagnostics_over_application_count` | Diagnostic gaps drive sampling even when application count is not low. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_cross_interview.py` | Existing sampling behavior remains compatible. |
| `tests/test_category_saturation_inv4.py` | Diagnostic contract unchanged. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Non-adequate category diagnostics feed `SamplingSuggestion.gap_codes`.
- [ ] Existing low-coverage behavior remains as fallback.
- [ ] Suggestion reason identifies category-development gaps when diagnostics are driving the result.
- [ ] Docs state this is sampling guidance, not true theoretical sampling/saturation proof.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should candidate document text be semantically matched to gap categories? — Status: DEFERRED | Why it matters: current candidate docs are uncoded, so content matching would need a retrieval design and possibly embeddings.
- [ ] Should suggestions persist as project state? — Status: DEFERRED | Why it matters: current function is read-only; a full protocol likely needs persistent sampling decisions and rationale.

---

## Notes

This plan still suggests among already-loaded uncoded documents. True GT
theoretical sampling often means collecting new data outside the current corpus;
that remains future work.
