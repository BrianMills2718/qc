# Plan #182: D7 Comparison Package Runner

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** #181
**Blocks:** Reproducible held-out D7 retrieval/live-baseline comparison runs

---

## Gap

**Current:** D7 comparison inputs can be supplied manually through
`scripts/compare_d7_retrieval.py`, `make compare-d7-retrieval`, or
`qc_cli.py compare-d7-retrieval`. Successful runs can write and verify artifact
packages. Unlike Phase 0, the standalone D7 comparison surface still has no
strict run manifest that records the intended project, gold file, ordered
prediction files, optional protocol, optional report output, optional artifact
root, and optional post-run verification switch in one versioned JSON file.

**Target:** Add a strict D7 comparison package runner:

- `scripts/run_d7_comparison_package.py <package.json>` validates a
  `schema_version=1` manifest.
- Relative paths are resolved from the package manifest directory.
- The runner delegates to `scripts/compare_d7_retrieval.py`.
- Manifest fields cover `project_id`, `gold_file`, ordered `prediction_files`,
  optional `protocol_package`, optional `output`, optional `artifact_dir`, and
  optional `verify_artifact`.
- `verify_artifact=true` requires `artifact_dir` and verifies the newest
  artifact directory created by that invocation after the comparison succeeds.
- `make compare-d7-package PACKAGE=...` and
  `qc_cli.py compare-d7-package ...` delegate to the runner.

**Why:** A held-out D7 comparison should be reproducible from one reviewed
manifest rather than a remembered command line. This removes another manual
coordination point before real held-out/live-baseline benchmark runs exist.

**Non-target:** This slice does not create held-out data, run live baselines,
choose retrieval/model policy, add artifact signing, verify original input
files beyond existing comparison preflight/hash metadata, or license held-out
D7 evidence, live-baseline evidence, superiority evidence,
methodological-validity evidence, or SOTA claims.

---

## References Reviewed

- `scripts/run_phase0_benchmark_package.py` - strict manifest runner and
  relative path resolution pattern.
- `tests/test_phase0_benchmark_package.py` - package-runner tests and manifest
  validation expectations.
- `scripts/compare_d7_retrieval.py` - canonical D7 comparison CLI.
- `scripts/verify_d7_comparison_artifact.py` - D7 artifact verification surface.
- `tests/test_d7_comparison_guard.py` - D7 comparison fixtures.
- `Makefile` - package runner and D7 comparison target style.
- `qc_cli.py` - top-level wrapper and dispatch pattern.
- Coordination/memory check: no active claim files under
  `~/.claude/coordination/claims`; `agent-memory recall 'active decisions D7
  comparison package manifest qualitative_coding' --project qualitative_coding`
  returned only low-relevance historical completed-task entries.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is a
deterministic package-runner slice over existing local D7 comparison surfaces.

---

## Capabilities

Internal D7 comparison package execution only; no cross-project boundary is
created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_d7_comparison_package` | strict JSON manifest | canonical D7 comparison report plus optional verified artifact | qualitative_coding | `make compare-d7-package`, `qc_cli.py compare-d7-package`, agents running D7 comparisons | free |

### Capability Validation

- [x] Relative package paths resolve from the manifest directory.
- [x] Ordered prediction files are preserved.
- [x] Invalid manifests fail before comparison runs.
- [x] `verify_artifact=true` verifies the artifact created by that invocation.

---

## Files Affected

- `scripts/run_d7_comparison_package.py`
- `tests/test_d7_comparison_package_runner.py`
- `tests/test_qc_cli_d7_retrieval.py`
- `Makefile`
- `qc_cli.py`
- `docs/EVALUATION_HARNESS.md`
- `docs/PROJECT_THEORY_AND_GOALS.md`
- `CLAUDE.md`
- `AGENTS.md` (regenerate after `CLAUDE.md`)
- `docs/plans/CLAUDE.md`
- `docs/plans/ACTIVE_SPRINT.md`

---

## Plan

### Steps

1. Write failing package-runner tests for relative-path forwarding, manifest
   validation, artifact verification invocation, Make dry-run, and `qc_cli.py`
   forwarding.
2. Add `scripts/run_d7_comparison_package.py` with Pydantic manifest validation
   and canonical argv conversion.
3. Add optional artifact verification after successful comparison runs.
4. Add Make and `qc_cli.py` surfaces.
5. Update docs with package-runner-only claim caveats.
6. Regenerate `AGENTS.md`.
7. Run focused tests, focused Ruff, docs checks, whitespace checks, and full
   `make check`.
8. Commit/push implementation, then close this plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_package_runner.py` | `test_d7_comparison_package_forwards_relative_inputs` | Relative gold/prediction/protocol/output/artifact paths resolve from manifest dir and ordered predictions are preserved. |
| `tests/test_d7_comparison_package_runner.py` | `test_d7_comparison_package_rejects_invalid_manifest` | Bad schema/empty project/missing predictions fail before comparison. |
| `tests/test_d7_comparison_package_runner.py` | `test_d7_comparison_package_verifies_created_artifact_when_requested` | `verify_artifact=true` verifies the newest artifact created by the invocation. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_compare_d7_package_forwards_manifest_path` | `qc_cli.py` delegates package path to canonical runner. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_package_runner.py tests/test_qc_cli_d7_retrieval.py -q` | Package runner behavior and CLI wrapper. |
| `python -m ruff check scripts/run_d7_comparison_package.py tests/test_d7_comparison_package_runner.py tests/test_qc_cli_d7_retrieval.py qc_cli.py` | Focused lint. |
| `make -n compare-d7-package PACKAGE=d7_package.json` | Make target forwards to canonical script. |
| `make docs-check` | Plan index, docs links, and AGENTS sync stay valid. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Valid manifests invoke the canonical D7 comparison script.
- [x] Relative paths resolve from the package manifest directory.
- [x] Prediction file order is preserved.
- [x] `verify_artifact=true` requires `artifact_dir`.
- [x] `verify_artifact=true` verifies the artifact directory created by the
  package run and fails if verification fails.
- [x] Invalid manifests return a JSON error and do not run comparison.
- [x] Make and `qc_cli.py` surfaces delegate to the canonical runner.
- [x] Docs state this package runner is reproducibility/provenance
  infrastructure only, not held-out D7 evidence, live-baseline evidence,
  superiority evidence, methodological-validity evidence, or SOTA.

> Process criteria:
- [x] TDD red state observed before implementation.
- [x] Focused tests pass.
- [x] Focused Ruff check passes.
- [x] Make dry-run passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Plan is moved to completed with verification evidence.
- [x] Verified implementation is committed and pushed.

---

## Outcome

Implemented and pushed in commit `97956856`
(`[Plan: D7_COMPARISON_PACKAGE_RUNNER] Add D7 comparison package runner`).

The slice adds `scripts/run_d7_comparison_package.py`, a strict
`schema_version=1` manifest runner over the canonical D7 comparison CLI.
Manifest-relative paths are resolved from the package file directory, ordered
prediction files are preserved, invalid manifests fail before comparison, and
`verify_artifact=true` requires `artifact_dir` then verifies the one new
artifact directory created by that invocation. `make compare-d7-package
PACKAGE=...` and `qc_cli.py compare-d7-package ...` delegate to the runner.

Verification evidence:

- TDD red: initial focused run failed with import errors because
  `scripts.run_d7_comparison_package` did not yet exist.
- Focused package/CLI tests:
  `python -m pytest tests/test_d7_comparison_package_runner.py tests/test_qc_cli_d7_retrieval.py -q`
  -> `11 passed`.
- Focused lint:
  `python -m ruff check scripts/run_d7_comparison_package.py tests/test_d7_comparison_package_runner.py tests/test_qc_cli_d7_retrieval.py qc_cli.py`
  -> passed.
- Make dry-run:
  `make -n compare-d7-package PACKAGE=d7_comparison_package.json`
  -> `python scripts/run_d7_comparison_package.py d7_comparison_package.json`.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- Full gate: `make check` -> `1186 passed, 1 skipped, 8 deselected`; Ruff
  passed; docs-check passed; type check remains not configured.

This remains reproducibility/provenance infrastructure only. It does not create
held-out D7 data, run live baselines, validate retrieval/model policy, prove
semantic disconfirmation validity, establish superiority, or support SOTA
claims.

---

## Failure Modes and Diagnostics

| Failure | Diagnosis | Response |
|---------|-----------|----------|
| Prediction order changes | Manifest conversion sorts paths | Preserve list order exactly. |
| Paths resolve from cwd | Runner ignores manifest directory | Resolve non-absolute paths relative to `package_file.parent`. |
| Verification checks an older artifact | Runner cannot identify created artifact | Capture artifact root directory listing before and after comparison and require exactly one new run directory for verification. |
| Verification requested without artifact root | Manifest ambiguous | Reject manifest before comparison. |
| Docs imply evidence | Caveat omitted | State package execution is reproducibility/provenance only. |
