# Plan #138: Theoretical Sampling Candidate Export

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #137
**Blocks:** Agent-drivable theoretical-sampling package workflows

---

## Outcome

Implemented across:

- `b578a5e` (`[Plan: THEORETICAL_SAMPLING_CANDIDATE_EXPORT] Add candidate export`)
  for core exporter, script, Make target, and tests.
- `5bd82a8` (`[Plan: THEORETICAL_SAMPLING_CANDIDATE_EXPORT] Document candidate export`)
  for canonical docs.
- `d24d80d` (`[Plan: THEORETICAL_SAMPLING_CANDIDATE_EXPORT] Add candidate export`)
  for generated `AGENTS.md` sync.

The repo now exports schema_version=1 loaded-document theoretical-sampling
candidate packages from existing diagnostic suggestions via
`make export-theoretical-sampling-candidates` /
`scripts/export_theoretical_sampling_candidates.py`. Exported packages include
protocol metadata, project/corpus/state hashes, loaded-document candidates,
target gap codes/types, and the claim-discipline caveat, and they are compatible
with `make theoretical-sampling-preflight`.

This is candidate-package/provenance export only. It is not candidate-selection
execution, new data collection, sampling-frame adequacy evidence,
methodological saturation evidence, full grounded-theory evidence, or SOTA
evidence.

Verification:

- TDD red captured: missing `qc_clean.core.theoretical_sampling_candidates`
  module and missing `scripts.export_theoretical_sampling_candidates` import
  before implementation.
- `python -m pytest tests/test_theoretical_sampling_candidate_export.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_theoretical_sampling_preflight.py -q`
  passed (`10 passed`).
- `python -m ruff check qc_clean/core/theoretical_sampling_candidates.py scripts/export_theoretical_sampling_candidates.py tests/test_theoretical_sampling_candidate_export.py tests/test_export_theoretical_sampling_candidates_script.py`
  passed.
- `make docs-check` passed.
- `make check` passed (`1046 passed, 1 skipped, 8 deselected`); type check is
  not yet configured in this repo.

---

## Gap

**Current:** `suggest_next_documents()` can produce in-memory
diagnostic-driven sampling suggestions over already-loaded uncoded documents,
and Plan #137 can preflight concrete candidate/result packages against a
registered protocol. There is no agent-drivable exporter that writes those
suggestions as a preflight-ready candidate package.

**Target:** Add a deterministic candidate export surface:

- `make export-theoretical-sampling-candidates ID=<project_id> PROTOCOL=protocol.json OUTPUT=candidates.json`
- `scripts/export_theoretical_sampling_candidates.py <project_id> --protocol protocol.json --output candidates.json`

**Why:** This connects existing INV-4 diagnostics/suggestions to the new
protocol preflight without claiming data collection, sampling adequacy, or
saturation.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - INV-4 still lacks populated
  sampling execution/result evidence.
- `docs/plans/completed/THEORETICAL_SAMPLING_PROTOCOL_PREFLIGHT.md` - package
  shape and preflight acceptance.
- `qc_clean/core/pipeline/theoretical_sampling.py` - existing
  `suggest_next_documents()` heuristic.
- `qc_clean/core/theoretical_sampling_preflight.py` - candidate package models.
- `scripts/run_d7_retrieval.py` and `tests/test_run_d7_retrieval_script.py` -
  project-store script boundary pattern.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Scope And Non-Goals

This plan exports a candidate package from already-loaded uncoded documents
only. It does not collect new data, recruit participants, select candidates,
write a sampling result package, prove sampling-frame adequacy, or prove
methodological saturation.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `export_theoretical_sampling_candidates` | `ProjectState` + theoretical-sampling protocol | schema_version=1 candidate package | qualitative_coding | `theoretical-sampling-preflight`, agents/operators | free |

### Capability Validation

- [x] Exported package validates with `TheoreticalSamplingCandidatePackage`.
- [x] Export fails loudly if the protocol requires external-only collection.
- [x] Export records project/corpus/state hashes and does not mutate
  `ProjectState`.
- [x] Script writes identical stdout/file JSON and returns JSON errors.
- [x] Make target exposes the exporter.

---

## Files Affected

- `qc_clean/core/theoretical_sampling_candidates.py` (new)
- `scripts/export_theoretical_sampling_candidates.py` (new)
- `tests/test_theoretical_sampling_candidate_export.py` (new)
- `tests/test_export_theoretical_sampling_candidates_script.py` (new)
- `Makefile` (modify)
- `CLAUDE.md` and `AGENTS.md` (docs/update)
- `docs/PROJECT_THEORY_AND_GOALS.md` and `docs/EVALUATION_HARNESS.md`
  (docs/update)
- `docs/plans/CLAUDE.md` and `docs/plans/ACTIVE_SPRINT.md` (plan tracking)

---

## Plan

### Steps

1. Commit this plan and mark it active.
2. Add TDD tests for core export, external-only protocol rejection, no mutation,
   and script stdout/output/error behavior.
3. Implement candidate package export from `suggest_next_documents()`.
4. Add script and Make target.
5. Update docs with the new export surface and caveats.
6. Run focused tests, focused Ruff, `make docs-check`, and full `make check`.
7. Commit/push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_theoretical_sampling_candidate_export.py` | `test_exports_preflight_ready_candidate_package` | Exported package uses protocol metadata, project hashes, suggestions, and preflight passes. |
| `tests/test_theoretical_sampling_candidate_export.py` | `test_candidate_export_rejects_external_only_protocol` | Loaded-document exporter fails loudly for external-only protocols. |
| `tests/test_theoretical_sampling_candidate_export.py` | `test_candidate_export_does_not_mutate_project_state` | Export is a pure packaging operation. |
| `tests/test_export_theoretical_sampling_candidates_script.py` | `test_export_theoretical_sampling_candidates_writes_output_and_stdout` | Script writes identical JSON to stdout and output. |
| `tests/test_export_theoretical_sampling_candidates_script.py` | `test_export_theoretical_sampling_candidates_missing_project_returns_json_error` | Script returns machine-readable JSON errors. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_theoretical_sampling_candidate_export.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_theoretical_sampling_preflight.py -q` | New exporter plus package preflight compatibility. |
| `python -m ruff check qc_clean/core/theoretical_sampling_candidates.py scripts/export_theoretical_sampling_candidates.py tests/test_theoretical_sampling_candidate_export.py tests/test_export_theoretical_sampling_candidates_script.py` | Focused lint. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Core exporter writes schema_version=1 candidate packages.
- [x] Candidate packages are preflight-compatible with Plan #137.
- [x] Export fails loudly for protocol/source combinations it cannot satisfy.
- [x] Export does not mutate saved or in-memory project state.
- [x] Script and Make target are agent-drivable.
- [x] Docs preserve that this is package export/provenance only, not sampling
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

This exporter is intentionally limited to already-loaded uncoded documents. A
future result-package/export lane can record which candidates were selected or
collected under a registered protocol.
