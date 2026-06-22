# Plan #143: D7 Baseline Package Validator

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** safer held-out D7 comparison and `BASELINES=` scoring runs

---

## Gap

**Current:** D7 retrieval and live-baseline exporters write versioned prediction
packages, and D7 comparison preflight validates those packages when a comparison
protocol is supplied. The direct `BASELINES=` scorecard path still accepts any
JSON object with a `disconfirmation_baselines` list, so malformed versioned D7
baseline packages can bypass package-model validation unless the operator also
runs comparison preflight.

**Target:** Add a standalone validator for versioned D7 baseline/prediction
packages that accepts both retrieval and live-baseline package types, expose it
through a Make target/script, reuse it from D7 comparison preflight, and make the
Phase 0 `BASELINES=` loader fail loud for malformed versioned packages while
preserving legacy raw baseline-list compatibility.

**Why:** D7 is a high-priority evidence lane. Baseline files are evidentiary
inputs, so versioned packages should be validated at their own boundary, not
only inside optional protocol preflight. This is package/provenance hardening
only; it does not create held-out D7 results, live-baseline evidence, or
superiority evidence.

---

## References Reviewed

- `agent-memory recall 'qualitative_coding D7 baseline package validation disconfirmation baselines' --project qualitative_coding --limit 5` - 2 broad historical findings; no specific active decision.
- `docs/PROJECT_THEORY_AND_GOALS.md:514-575` - D7 held-out/live-baseline gaps and roadmap priority.
- `docs/EVALUATION_HARNESS.md:55-59` - D7 scoring substrate and remaining held-out/live-baseline gaps.
- `qc_clean/core/d7_retrieval.py` - retrieval package model and comparison helper.
- `qc_clean/core/d7_live_baseline.py` - live-baseline package model.
- `qc_clean/core/d7_comparison_preflight.py` - existing optional prediction-package validation inside protocol preflight.
- `scripts/bench_phase0.py:998-1021` - current shallow D7 `BASELINES=` loader.
- `scripts/compare_d7_retrieval.py` - comparison runner package loading.
- `tests/test_d7_retrieval.py` - retrieval package export and current scorecard loader compatibility.
- `tests/test_d7_live_baseline.py` - live-baseline package export and current scorecard loader compatibility.
- `tests/test_d7_comparison_preflight.py` - current D7 comparison preflight expectations.
- Coordination claims check: `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active claim files at sprint start.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This slice strengthens
deterministic package validation around existing D7 contracts.

---

## Capabilities

This plan creates an internal validation boundary and CLI/Make surface. It does
not create a cross-project callable capability.

---

## Files Affected

- `qc_clean/core/d7_baseline_package.py` (create)
- `qc_clean/core/d7_comparison_preflight.py` (modify)
- `scripts/bench_phase0.py` (modify)
- `scripts/validate_d7_baseline_package.py` (create)
- `tests/test_d7_baseline_package.py` (create)
- `tests/test_d7_retrieval.py` (modify if needed)
- `tests/test_d7_live_baseline.py` (modify if needed)
- `tests/test_d7_comparison_preflight.py` (modify if needed)
- `tests/test_bench_phase0_script.py` (modify if needed)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `qc_clean/core/d7_baseline_package.py` with reusable payload validation
   for retrieval and live-baseline package models, plus a helper that returns
   scorecard-compatible baseline rows.
2. Reuse that validator in D7 comparison preflight instead of duplicating model
   attempts there.
3. Update `scripts/bench_phase0.py` so `BASELINES=` still accepts raw legacy
   lists, but recognized versioned D7 package objects must validate before their
   `disconfirmation_baselines` rows are returned.
4. Add `scripts/validate_d7_baseline_package.py` and
   `make validate-d7-baseline-package PACKAGE=...`.
5. Add focused tests for retrieval/live package acceptance, malformed versioned
   package rejection, CLI JSON output, preflight reuse, and Phase 0 loader
   strictness.
6. Update docs and generated `AGENTS.md` with conservative claim discipline.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_baseline_package.py` | `test_validate_d7_baseline_package_accepts_retrieval_package` | Retrieval prediction packages validate and expose baseline counts. |
| `tests/test_d7_baseline_package.py` | `test_validate_d7_baseline_package_accepts_live_package` | Live candidate-selection baseline packages validate through the same boundary. |
| `tests/test_d7_baseline_package.py` | `test_validate_d7_baseline_package_rejects_malformed_versioned_package` | Versioned packages with missing/invalid required metadata fail loudly. |
| `tests/test_d7_baseline_package.py` | `test_validate_d7_baseline_package_script_outputs_json` | CLI emits machine-readable pass/fail reports and exit codes. |
| `tests/test_d7_baseline_package.py` | `test_phase0_d7_baselines_loader_rejects_invalid_versioned_package` | `BASELINES=` loader validates recognized versioned packages, not just the list field. |
| `tests/test_d7_baseline_package.py` | `test_phase0_d7_baselines_loader_preserves_raw_list_compatibility` | Legacy raw baseline lists remain supported. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d7_retrieval.py` | Retrieval package export and comparison behavior remains stable. |
| `tests/test_d7_live_baseline.py` | Live-baseline package export remains stable. |
| `tests/test_d7_comparison_preflight.py` | Protocol preflight still validates both package types. |
| `tests/test_bench_phase0_script.py` | Existing external-file loader behavior remains compatible. |
| `make docs-check` | Plan/docs/AGENTS sync must pass. |
| `make check` | Full deterministic gate must pass. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Standalone validation accepts both versioned D7 retrieval and live-baseline
      packages and reports package type, baseline count, candidate count, and
      claim-discipline caveat.
- [ ] Standalone validation rejects malformed recognized versioned packages with
      a non-zero CLI exit and JSON error.
- [ ] D7 comparison preflight uses the shared package validator.
- [ ] `BASELINES=` validates recognized versioned packages before scoring while
      preserving raw-list compatibility.
- [ ] Docs state this is package/provenance validation only, not held-out D7
      evidence, live-baseline evidence, or superiority evidence.

> Process criteria:
- [ ] Required new tests pass.
- [ ] Related D7 and bench loader tests pass.
- [ ] `make docs-check` passes.
- [ ] `make check` passes.
- [ ] Plan is completed, committed, and pushed.

---

## Open Questions

None for this slice. Populating held-out D7 gold, running live baselines, and
claiming superiority remain separate evidence-producing lanes.

---

## Notes

The validator deliberately does not require a D7 comparison protocol. Protocol
preflight remains the stronger guard for held-out comparisons; this slice makes
the package boundary itself deterministic and agent-drivable.
