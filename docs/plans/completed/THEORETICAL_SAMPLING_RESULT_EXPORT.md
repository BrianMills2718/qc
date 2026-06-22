# Plan #139: Theoretical Sampling Result Export

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #138
**Blocks:** Auditable theoretical-sampling selection/result packages

---

## Outcome

Implemented across:

- `e41a64d` (`[Plan: THEORETICAL_SAMPLING_RESULT_EXPORT] Add result export`)
  for core exporter, script, Make target, and tests.
- `5ca66e6` (`[Plan: THEORETICAL_SAMPLING_RESULT_EXPORT] Add result export`)
  for canonical docs and generated `AGENTS.md` sync.

The repo now exports schema_version=1 theoretical-sampling result packages from
explicit selected candidate IDs via `make export-theoretical-sampling-results`
/ `scripts/export_theoretical_sampling_results.py`. Result packages derive
addressed gap codes/types from selected candidates, require success criteria
from the registered protocol, and are compatible with
`make theoretical-sampling-preflight`.

This is result-package/provenance export only. It is not candidate-selection
judgment, new data collection, sampling-frame adequacy evidence,
methodological saturation evidence, full grounded-theory evidence, or SOTA
evidence.

Verification:

- TDD red captured: missing `qc_clean.core.theoretical_sampling_results`
  module and missing `scripts.export_theoretical_sampling_results` import before
  implementation.
- `python -m pytest tests/test_theoretical_sampling_result_export.py tests/test_export_theoretical_sampling_results_script.py tests/test_theoretical_sampling_preflight.py -q`
  passed (`10 passed`).
- `python -m ruff check qc_clean/core/theoretical_sampling_results.py scripts/export_theoretical_sampling_results.py tests/test_theoretical_sampling_result_export.py tests/test_export_theoretical_sampling_results_script.py`
  passed.
- `make docs-check` passed.
- `make check` passed (`1051 passed, 1 skipped, 8 deselected`); type check is
  not yet configured in this repo.

---

## Gap

**Current:** The repo can validate theoretical-sampling protocols, export
loaded-document candidate packages, and preflight candidate/result packages.
There is no agent-drivable exporter that records which candidate IDs were
selected under a protocol as a schema_version=1 result package.

**Target:** Add a deterministic result export surface:

- `make export-theoretical-sampling-results PROTOCOL=protocol.json CANDIDATES=candidates.json SELECTED=loaded-doc-1 SUCCESS_CRITERION="..." OUTPUT=results.json`
- `scripts/export_theoretical_sampling_results.py protocol.json --candidates-file candidates.json --selected-candidate-id loaded-doc-1 --success-criterion-met "..." --output results.json`

**Why:** Plan #137 already defines result-package preflight. This slice gives
agents/operators a governed way to write those result packages without claiming
sampling adequacy or methodological saturation.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - INV-4 still lacks populated
  sampling-result evidence and true saturation evidence.
- `docs/plans/completed/THEORETICAL_SAMPLING_PROTOCOL_PREFLIGHT.md` - result
  package shape and preflight checks.
- `docs/plans/completed/THEORETICAL_SAMPLING_CANDIDATE_EXPORT.md` - candidate
  package exporter and caveats.
- `qc_clean/core/theoretical_sampling_preflight.py` - candidate/result package
  models and preflight report.
- `scripts/export_theoretical_sampling_candidates.py` and tests - script/store
  boundary style.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Scope And Non-Goals

This plan records selected candidate IDs as a result package. It does not decide
which candidates should be selected, collect new data, import new documents,
prove sampling-frame adequacy, prove methodological saturation, or score
GT-fidelity.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `export_theoretical_sampling_results` | protocol JSON + candidate package JSON + selected IDs + success criteria | schema_version=1 result package | qualitative_coding | `theoretical-sampling-preflight`, agents/operators | free |

### Capability Validation

- [x] Result package validates with `TheoreticalSamplingResultPackage`.
- [x] Export fails loudly when selected IDs are not in the candidate package.
- [x] Export derives addressed gap codes/types from selected candidates.
- [x] Script writes identical stdout/file JSON and returns JSON errors.
- [x] Make target exposes the exporter.

---

## Files Affected

- `qc_clean/core/theoretical_sampling_results.py` (new)
- `scripts/export_theoretical_sampling_results.py` (new)
- `tests/test_theoretical_sampling_result_export.py` (new)
- `tests/test_export_theoretical_sampling_results_script.py` (new)
- `Makefile` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/PROJECT_THEORY_AND_GOALS.md` and `docs/EVALUATION_HARNESS.md`
  (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for core result export, unknown selected IDs, unregistered
   success criteria, and script stdout/output/error behavior.
3. Implement result package export from protocol + candidate package.
4. Add script and Make target.
5. Update docs with the new result surface and caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_theoretical_sampling_result_export.py` | `test_exports_preflight_ready_result_package` | Result package derives addressed gaps from selected candidates and preflight passes. |
| `tests/test_theoretical_sampling_result_export.py` | `test_result_export_rejects_unknown_selected_candidate` | Selected IDs must exist in the candidate package. |
| `tests/test_theoretical_sampling_result_export.py` | `test_result_export_rejects_unregistered_success_criterion` | Success criteria must come from the protocol. |
| `tests/test_export_theoretical_sampling_results_script.py` | `test_export_theoretical_sampling_results_writes_output_and_stdout` | Script writes identical JSON to stdout and output. |
| `tests/test_export_theoretical_sampling_results_script.py` | `test_export_theoretical_sampling_results_returns_json_error` | Script returns machine-readable JSON errors. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_theoretical_sampling_result_export.py tests/test_export_theoretical_sampling_results_script.py tests/test_theoretical_sampling_preflight.py -q` | New result exporter plus existing preflight compatibility. |
| `python -m ruff check qc_clean/core/theoretical_sampling_results.py scripts/export_theoretical_sampling_results.py tests/test_theoretical_sampling_result_export.py tests/test_export_theoretical_sampling_results_script.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Core exporter writes schema_version=1 result packages.
- [x] Result packages are preflight-compatible with Plan #137.
- [x] Export fails loudly for unknown selected IDs and unregistered success
  criteria.
- [x] Script and Make target are agent-drivable.
- [x] Docs preserve that this is result-package/provenance only, not sampling
  execution, sampling adequacy, or saturation evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Notes

This creates the governed result artifact for selected IDs. A later lane can
import genuinely new data collected under a protocol or connect result packages
to GT-fidelity evaluation artifacts.
