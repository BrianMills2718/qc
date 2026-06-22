# Plan #147: D3 Baseline Package Validator

**Status:** In Progress
**Type:** implementation
**Priority:** Medium
**Blocked By:** D3 baseline comparison scorecard
**Blocks:** safer held-out D3 baseline comparison package workflows

---

## Gap

**Current:** D3 baseline predictions can be supplied to Phase 0 as a raw JSON
list or an object with `application_baselines`. That is compatible and useful,
but unlike D7 retrieval/live-baseline predictions, there is no versioned D3
baseline package contract or standalone validator. A malformed versioned object
would currently be treated as a legacy wrapper if it happens to include
`application_baselines`.

**Target:** Add a schema_version=1 D3 application-baseline package contract,
validator, and `make validate-d3-baseline-package PACKAGE=...`. Update the
Phase 0 `D3_BASELINES=` loader so recognized versioned D3 baseline packages
validate before scoring, while legacy raw lists and legacy
`{"application_baselines": [...]}` objects remain supported.

**Why:** D3 baseline comparisons are evidentiary inputs in future held-out
application-validity runs. Package/provenance validation should happen at the
file boundary before those baselines influence scorecards. This does not run a
live baseline or create held-out D3 evidence.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 baseline input surface and remaining held-out evidence gaps.
- `docs/plans/completed/D3_BASELINE_COMPARISON_SCORECARD.md` - existing D3 baseline scorecard substrate and deferred package/export work.
- `qc_clean/core/bench.py` - `ApplicationBaselinePrediction` model and D3 baseline scoring.
- `scripts/bench_phase0.py` - current `load_d3_baselines_file` behavior.
- `qc_clean/core/d7_baseline_package.py` and `scripts/validate_d7_baseline_package.py` - analogous D7 package validator pattern.
- `tests/test_bench_phase0.py`, `tests/test_bench_phase0_script.py`, and `tests/test_phase0_benchmark_package.py` - existing D3 baseline behavior.
- Memory context: `agent-memory recall 'qualitative_coding D3 baseline package validation application_baselines active decisions' --project qualitative_coding --limit 5` - historical broad findings only, no blocking in-flight decision.

---

## Research Basis For This Slice

No external research is needed. This is repo-local package/provenance hardening
for an existing evaluation-harness input.

---

## Capabilities

This plan creates a repo-local D3 baseline package validation boundary and
Make/script surface. It does not create a baseline generator or cross-project
shared capability.

---

## Files Affected

- `qc_clean/core/d3_baseline_package.py` (create)
- `scripts/validate_d3_baseline_package.py` (create)
- `scripts/bench_phase0.py` (modify)
- `tests/test_d3_baseline_package.py` (create)
- `tests/test_bench_phase0_script.py` (modify if needed)
- `Makefile` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/D3_BASELINE_PACKAGE_VALIDATOR.md` (create, then move to completed)

---

## Plan

### Steps

1. Add `qc_clean/core/d3_baseline_package.py` with:
   - `D3BaselinePackage` / run metadata model
   - `validate_d3_baseline_package_payload()`
   - `build_d3_baseline_package_report()`
   - `d3_baselines_payload_for_scorecard()`
2. Preserve legacy D3 baseline raw-list/object compatibility.
3. Make `scripts/bench_phase0.load_d3_baselines_file()` use the shared helper.
4. Add `scripts/validate_d3_baseline_package.py`.
5. Add `make validate-d3-baseline-package PACKAGE=...`.
6. Add focused tests for valid package, malformed package rejection, script JSON
   output/exit codes, Phase 0 loader strictness, and legacy compatibility.
7. Update docs with explicit claim discipline.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d3_baseline_package.py` | `test_validate_d3_baseline_package_accepts_application_package` | Valid schema_version=1 D3 baseline package validates and reports baseline counts. |
| `tests/test_d3_baseline_package.py` | `test_validate_d3_baseline_package_rejects_malformed_versioned_package` | Recognized versioned package with invalid metadata fails loudly. |
| `tests/test_d3_baseline_package.py` | `test_validate_d3_baseline_package_script_outputs_json` | Script emits machine-readable pass/fail reports and exit codes. |
| `tests/test_d3_baseline_package.py` | `test_phase0_d3_baselines_loader_validates_versioned_package` | `D3_BASELINES=` loader validates recognized packages before scoring. |
| `tests/test_d3_baseline_package.py` | `test_phase0_d3_baselines_loader_preserves_legacy_inputs` | Raw list and legacy object inputs remain supported. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Existing D3 baseline scoring stays compatible. |
| `tests/test_bench_phase0_script.py` | External D3 baseline files still load without state mutation. |
| `tests/test_phase0_benchmark_package.py` | Package manifest forwarding still works. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Versioned D3 baseline packages have schema_version=1 and a stable package type.
- [ ] Standalone validation reports package type, project ID, baseline mode, baseline count, baseline names, and claim-discipline caveat.
- [ ] Standalone validation rejects malformed recognized packages with non-zero exit and JSON error.
- [ ] `make validate-d3-baseline-package PACKAGE=...` is available.
- [ ] `D3_BASELINES=` validates recognized versioned packages before scoring while preserving legacy raw-list/object compatibility.
- [ ] Docs say this is package/provenance validation only, not live-baseline or held-out D3 evidence.

> Process criteria (quality gates):
- [ ] Required focused tests pass.
- [ ] Full test suite passes (`make check`).
- [ ] Type check status is reported.
- [ ] Docs updated.

---

## Open Questions

- [ ] Should a future D3 baseline export runner produce this package shape from
  live candidate/application selectors? - Status: DEFERRED | Why it matters:
  generating baseline predictions involves model prompts, budget, and held-out
  benchmark protocol choices outside this validation slice.

---

## Notes

This package validator intentionally does not require D3 gold. It validates the
baseline prediction package boundary; scorecard comparison still requires D3
gold at scoring time.
