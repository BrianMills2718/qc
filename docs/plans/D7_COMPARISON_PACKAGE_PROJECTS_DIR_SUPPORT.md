# Plan #215: D7 Comparison Package Projects Dir Support

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** fully portable D7 comparison package replay

---

## Gap

**Current:** D7 retrieval export, live-baseline export, and direct D7 comparison
support explicit repo-local project stores through `PROJECTS_DIR` /
`--projects-dir`. The strict D7 comparison package manifest runner
(`compare-d7-package`) does not. A package can resolve gold/prediction/protocol
paths relative to its manifest, but it cannot encode the project-store path
needed by `compare_d7_retrieval.py`.

**Target:** Add optional `projects_dir` support to schema_version=1 D7
comparison package manifests and forward it from `compare-d7-package` to the
canonical comparison script. Add writer, Make, and `qc_cli.py
write-d7-comparison-package` support so packages can be authored with that
field.

**Why:** A D7 comparison package should be self-contained enough to replay from
repo-local artifact directories without hidden `QC_PROJECTS_DIR` environment
state or mutation of the default user project store.

**Claim boundary:** This is repeatability/provenance plumbing only. It does not
create held-out D7 evidence, live-baseline evidence, semantic disconfirmation
validity, superiority evidence, methodological-validity evidence, or SOTA
evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - D7 held-out comparison remains not
  yet populated.
- `docs/EVALUATION_HARNESS.md` - D7 comparison package workflow and caveats.
- `docs/plans/completed/D7_COMPARISON_PACKAGE_RUNNER.md` - strict package
  runner surface.
- `docs/plans/completed/D7_COMPARISON_PACKAGE_WRITER.md` - strict package writer
  surface.
- `docs/plans/completed/PHASE0_PACKAGE_PROJECTS_DIR_SUPPORT.md` - package-local
  projects_dir precedent.
- `scripts/run_d7_comparison_package.py` - current package schema and argv
  conversion.
- `scripts/write_d7_comparison_package.py` - current writer.
- `Makefile` and `qc_cli.py` - current package writer/runner command surfaces.
- `tests/test_d7_comparison_package_runner.py`,
  `tests/test_d7_comparison_package_writer.py`, and
  `tests/test_qc_cli_d7_retrieval.py` - current package coverage.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is repo-local
execution-surface parity for strict D7 package replay.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 comparison package replay with explicit project store | D7 comparison package manifest with optional projects_dir | Canonical D7 comparison report/artifact | qualitative_coding | D7 benchmark package workflows | free unless prediction packages were live-generated elsewhere |

### Capability Validation

Skipped for cross-project registry purposes: this extends existing project-local
package surfaces.

---

## Files Affected

- `docs/plans/D7_COMPARISON_PACKAGE_PROJECTS_DIR_SUPPORT.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `scripts/run_d7_comparison_package.py` - optional `projects_dir` manifest
  field and `--projects-dir` argv conversion.
- `scripts/write_d7_comparison_package.py` - optional writer parameter and
  report field.
- `Makefile` - optional `PROJECTS_DIR=` forwarding for
  `write-d7-comparison-package`.
- `qc_cli.py` - optional `--projects-dir` parser/forwarding for
  `write-d7-comparison-package`.
- Tests:
  - `tests/test_d7_comparison_package_runner.py`
  - `tests/test_d7_comparison_package_writer.py`
  - `tests/test_qc_cli_d7_retrieval.py`
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add failing tests for package-manifest `projects_dir` resolution and writer
   CLI forwarding.
2. Extend `D7ComparisonPackage` with optional `projects_dir`.
3. Resolve relative `projects_dir` against the package directory and forward it
   as `--projects-dir` before comparison.
4. Extend `write_d7_comparison_package.py` function, CLI, report, and manifest
   writer with optional `projects_dir`.
5. Add `PROJECTS_DIR=` forwarding to Make and `--projects-dir` forwarding to
   `qc_cli.py write-d7-comparison-package`.
6. Update docs conservatively.
7. Run focused tests, touched Ruff, docs checks, and `make check`.
8. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_package_runner.py` | `test_package_projects_dir_forwards_to_compare` | Package `projects_dir` resolves relative to the manifest and forwards `--projects-dir` to `compare_d7_retrieval`. |
| `tests/test_d7_comparison_package_writer.py` | `test_writer_records_projects_dir` | Writer emits package-local `projects_dir` and report metadata. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_write_d7_comparison_package_forwards_projects_dir` | Canonical CLI forwards `--projects-dir` to the writer. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_package_runner.py tests/test_d7_comparison_package_writer.py tests/test_qc_cli_d7_retrieval.py -q` | Focused D7 package runner/writer/CLI coverage. |
| `python -m ruff check scripts/run_d7_comparison_package.py scripts/write_d7_comparison_package.py qc_cli.py tests/test_d7_comparison_package_runner.py tests/test_d7_comparison_package_writer.py tests/test_qc_cli_d7_retrieval.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [ ] D7 comparison package manifests may include optional `projects_dir`.
- [ ] Relative `projects_dir` resolves from the package manifest directory.
- [ ] `compare-d7-package` forwards resolved `projects_dir` to
  `compare_d7_retrieval.py`.
- [ ] `write-d7-comparison-package PROJECTS_DIR=...` and
  `qc_cli.py write-d7-comparison-package --projects-dir ...` write the field.
- [ ] Existing manifests without `projects_dir` remain valid and compatible.
- [ ] Docs preserve claim discipline: this is portability/provenance support,
  not held-out D7 evidence, live-baseline evidence, superiority evidence,
  methodological-validity evidence, or SOTA evidence.

Process criteria:

- [ ] Focused tests pass.
- [ ] Touched Python Ruff gate passes.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Open Questions

- [x] Should package runner itself accept a CLI `--projects-dir` override?
  Status: RESOLVED. No for this slice. The manifest is the replay contract; a
  CLI override would create two competing sources of truth. Add only manifest
  `projects_dir`, writer support, and existing package-relative resolution.

---

## Notes

This mirrors Phase 0 package `projects_dir` support and completes the D7
project-store portability chain for export, live export, direct comparison, and
strict package replay.
