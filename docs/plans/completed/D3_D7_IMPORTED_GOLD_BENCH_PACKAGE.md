# Plan #102: D3/D7 Imported-Gold Benchmark Package

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** INV-3 adjudication response import; Phase 0 benchmark package runner
**Blocks:** repeatable D3/D7 adjudication-package scoring; future held-out expert-evidence runs

---

## Outcome

Implemented a strict Phase 0 manifest writer for imported adjudication gold:

- `scripts/write_phase0_adjudication_package.py` validates supplied D3/D7 files
  as versioned `schema_version=1` gold-set packages.
- The writer requires at least one D3 or D7 package, rejects raw/non-versioned
  gold files, and fails loudly when paired D3/D7 package provenance disagrees.
- Output manifests are validated through the existing `Phase0BenchmarkPackage`
  model and use manifest-relative paths where possible.
- `make write-phase0-adjudication-package` exposes the workflow as an
  agent-drivable target.
- Docs identify the bridge as repeatability/provenance infrastructure, not
  expert evidence or methodological validity evidence.

Implementation commit: `b44bf1b`

## Verification

- TDD red: initial `python -m pytest
  tests/test_phase0_adjudication_package.py -q` failed with
  `ImportError: cannot import name 'write_phase0_adjudication_package'`.
- Focused behavior: `python -m pytest
  tests/test_phase0_adjudication_package.py tests/test_phase0_benchmark_package.py
  tests/test_d3_gold_set.py tests/test_d7_gold_set.py -q` -> 17 passed.
- Focused lint: `python -m ruff check
  scripts/write_phase0_adjudication_package.py
  tests/test_phase0_adjudication_package.py
  scripts/run_phase0_benchmark_package.py tests/test_phase0_benchmark_package.py
  qc_clean/core/d3_gold.py qc_clean/core/d7_gold.py` -> all checks passed.
- Command discoverability: `make help` lists
  `write-phase0-adjudication-package`.
- Documentation governance: `make docs-check` passed.
- Full gate: `make check` -> 890 passed, 1 skipped, 8 deselected; Ruff and
  docs-check passed; type check remains not configured.
- Commit `b44bf1b` was pushed to `main`.

---

## Gap

**Current:** Completed adjudication response packages can be converted into
validated D3 and D7 gold package files. The Phase 0 package runner can execute a
strict manifest. There is no agent-drivable bridge that validates those imported
gold package files together and writes the Phase 0 manifest that `make
bench-package` expects.

**Target:** Add a strict manifest writer for imported adjudication gold outputs:

- Script: `scripts/write_phase0_adjudication_package.py`
- Make target: `make write-phase0-adjudication-package ID=<project_id>
  OUTPUT=phase0_package.json [D3_GOLD=d3_gold.json] [GOLD=d7_gold.json]
  [SCORECARD_OUTPUT=scorecard.json] [ARTIFACT_DIR=benchmark_results]`
- The writer must validate supplied D3/D7 inputs as versioned
  `schema_version=1` gold-set packages, require at least one supplied gold file,
  and fail loudly if both packages are present but disagree on shared provenance
  fields that should match for one adjudication import.
- The output manifest must validate with the existing
  `Phase0BenchmarkPackage` model and resolve gold paths relative to the manifest
  location where possible.

**Why:** This closes the orchestration gap between label import and repeatable
Phase 0 scoring while preserving claim discipline. It makes future expert-label
packages easier to score without treating package assembly as expert evidence.

---

## References Reviewed

- `scripts/run_phase0_benchmark_package.py` - existing strict Phase 0 manifest
  model and relative-path runner.
- `tests/test_phase0_benchmark_package.py` - runner behavior for relative paths,
  output files, artifact dirs, and unknown-key rejection.
- `qc_clean/core/d3_gold.py` - versioned D3 package loader and invariants.
- `qc_clean/core/d7_gold.py` - versioned D7 package loader and invariants.
- `qc_clean/core/adjudication_import.py` - importer that produces D3/D7 package
  outputs from validated adjudication responses.
- `scripts/import_adjudication_responses.py` - command pattern for import
  artifacts.
- `Makefile` - agent-facing target conventions.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - current
  Phase 0 and claim-discipline language.
- Memory context: not retried because `agent-memory recall` has repeatedly
  failed with provider 402/403 in this long-running session; circuit breaker
  remains active.

---

## Research Basis For This Slice

No additional research beyond repo-local references. This slice is deterministic
package assembly over existing validation contracts; it does not design or run a
human adjudication protocol.

---

## Capabilities

Internal orchestration capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `build_phase0_adjudication_package_manifest` | project ID + versioned D3/D7 package paths + optional output/artifact settings | `Phase0BenchmarkPackage` manifest payload | qualitative_coding | agents, `make bench-package` | free |

### Capability Validation

- [x] Input package files validate through the D3/D7 loaders.
- [x] Output manifest validates through `Phase0BenchmarkPackage`.
- [x] Relative path handling is deterministic and covered by tests.

---

## Files Affected

- `scripts/write_phase0_adjudication_package.py` (create)
- `tests/test_phase0_adjudication_package.py` (create)
- `Makefile` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate through existing sync tooling if needed)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify after closeout)

---

## Plan

### Steps

1. Write failing tests for manifest assembly, invalid package rejection, and D3/D7
   provenance mismatch.
2. Add `scripts/write_phase0_adjudication_package.py` with a small Pydantic
   request/report model, package validation, provenance consistency checks, and
   JSON output.
3. Add `make write-phase0-adjudication-package`.
4. Update docs to list the bridge as orchestration/provenance only.
5. Run focused tests, focused Ruff, docs checks, and full `make check`.
6. Commit and push implementation, then close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_phase0_adjudication_package.py` | `test_writes_manifest_for_valid_d3_d7_gold_packages` | Valid D3/D7 package files produce a strict Phase 0 manifest with relative paths. |
| `tests/test_phase0_adjudication_package.py` | `test_rejects_non_versioned_d3_gold_file` | Raw D3 gold inputs are rejected; this bridge requires provenance packages. |
| `tests/test_phase0_adjudication_package.py` | `test_rejects_mismatched_d3_d7_provenance` | D3 and D7 packages from different corpus/project/split metadata fail loudly. |
| `tests/test_phase0_adjudication_package.py` | `test_script_outputs_machine_readable_report` | Script writes the manifest and reports paths/caution as JSON. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_phase0_benchmark_package.py` | Existing package runner contract stays unchanged. |
| `tests/test_d3_gold_set.py tests/test_d7_gold_set.py` | Gold-package validators stay unchanged. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] At least one of `D3_GOLD` or `GOLD`/D7 gold is required.
- [x] Supplied D3/D7 gold files must be versioned package files accepted by
  existing validators.
- [x] If both D3 and D7 packages are supplied, shared provenance fields match or
  the writer fails loudly.
- [x] Written manifest validates through the existing `Phase0BenchmarkPackage`
  model.
- [x] Make target is agent-drivable and discoverable via `make help`.
- [x] Docs say this is package assembly/provenance only, not expert evidence or
  methodological validity evidence.

> Process criteria:
- [x] Required focused tests pass.
- [x] Focused Ruff check passes.
- [x] `make docs-check` passes.
- [x] Full `make check` passes or any failure is documented with evidence.
- [x] Type-check status is reported.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [x] Should the writer support D4/D6/D8/D9/calibration files too? — Status:
  DEFERRED | Why it matters: this slice intentionally bridges imported D3/D7
  adjudication labels only; broader benchmark-package assembly belongs in a
  later general manifest-authoring lane.

---

## Notes

This is an orchestration bridge. A green manifest run can prove the local
scorecard consumed the supplied package files, but it cannot prove the labels
were expert-produced, held out, or methodologically adequate.
