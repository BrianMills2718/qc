# Plan #212: D7 Comparison Projects Dir Parity

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** portable D7 held-out retrieval/comparison artifact packages

---

## Gap

**Current at plan start:** `scripts/run_d7_retrieval.py` accepted
`--projects-dir`, but `scripts/compare_d7_retrieval.py` still constructed the
default `ProjectStore()`. That meant a portable D7 retrieval package could be
exported from a repo-local store, but the comparison/artifact step could not
load that same store through an explicit argument. Operators had to rely on
`QC_PROJECTS_DIR` or mutate the default user project store.

**Target:** Add optional `--projects-dir` / `PROJECTS_DIR=` support to D7
retrieval comparison through script, Make, and `qc_cli.py compare-d7-retrieval`,
while preserving default behavior when omitted.

**Why:** D7 comparison artifacts should be reproducible from repo-local project
stores without hidden environment coupling. This is execution/provenance
plumbing only; it does not create held-out D7 evidence, live-baseline evidence,
superiority evidence, methodological-validity evidence, or SOTA evidence.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - D7 held-out comparison remains a
  high-priority gap.
- `docs/EVALUATION_HARNESS.md` - D7 comparison workflow and claim caveats.
- `docs/plans/completed/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` - immediately prior
  retrieval-export parity pattern.
- `docs/plans/completed/D7_COMPARISON_ARTIFACT_PACKAGE.md` - comparison artifact
  package surface.
- `scripts/compare_d7_retrieval.py` - current hard-coded default ProjectStore
  use.
- `Makefile` - current `compare-d7-retrieval` target.
- `qc_cli.py` - current `compare-d7-retrieval` parser and forwarding handler.
- `tests/test_d7_comparison_guard.py` and `tests/test_qc_cli_d7_retrieval.py` -
  current comparison and CLI coverage.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is repo-local
execution-surface parity needed before committing portable D7 comparison
artifacts.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `compare_d7_retrieval` with explicit project store | project ID + optional projects_dir + gold/prediction/protocol files | D7 comparison report / optional artifact package | qualitative_coding | D7 comparison/package workflows | free |

### Capability Validation

Skipped for cross-project registry purposes: this extends an existing
project-local script and CLI surface.

---

## Files Affected

- `docs/plans/D7_COMPARISON_PROJECTS_DIR_PARITY.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `scripts/compare_d7_retrieval.py` - `--projects-dir` argument and
  ProjectStore construction.
- `Makefile` - optional `PROJECTS_DIR=` forwarding for `compare-d7-retrieval`.
- `qc_cli.py` - `--projects-dir` parser/forwarding for
  `compare-d7-retrieval`.
- `tests/test_d7_comparison_guard.py` - script loads explicit project store.
- `tests/test_qc_cli_d7_retrieval.py` - CLI forwards `--projects-dir`.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add failing tests for comparison script `--projects-dir` loading and
   `qc_cli.py compare-d7-retrieval` forwarding.
2. Add `--projects-dir` to `scripts/compare_d7_retrieval.py`; construct
   `ProjectStore(projects_dir=args.projects_dir)` only when supplied.
3. Add `PROJECTS_DIR=` forwarding to the Make target.
4. Add `--projects-dir` parser and handler forwarding to `qc_cli.py
   compare-d7-retrieval`.
5. Update command docs conservatively.
6. Run focused tests, touched Ruff, docs checks, and `make check`.
7. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_comparison_guard.py` | `test_compare_d7_retrieval_accepts_projects_dir` | Script loads the comparison project from an explicit repo-local store without monkeypatching default `ProjectStore()`. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_compare_d7_retrieval_forwards_projects_dir` | Canonical CLI forwards `--projects-dir` to the comparison script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py -q` | Focused D7 comparison script/CLI coverage. |
| `python -m ruff check scripts/compare_d7_retrieval.py qc_cli.py tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] `scripts/compare_d7_retrieval.py --projects-dir path` loads from that
  store.
- [x] `make compare-d7-retrieval PROJECTS_DIR=path ...` forwards the path.
- [x] `qc_cli.py compare-d7-retrieval --projects-dir path ...` forwards the
  path.
- [x] Default behavior without `--projects-dir` remains unchanged.
- [x] Docs preserve claim discipline: this is portability/provenance support,
  not held-out D7 evidence, live-baseline evidence, superiority evidence,
  methodological-validity evidence, or SOTA evidence.

Process criteria:

- [x] Focused tests pass.
- [x] Touched Python Ruff gate passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Completed in commit `f3f0bdfa`.

Implemented optional explicit project-store loading for D7 retrieval
comparison:

- `scripts/compare_d7_retrieval.py` accepts `--projects-dir path` and
  constructs `ProjectStore(projects_dir=...)` only when supplied.
- `make compare-d7-retrieval PROJECTS_DIR=path ...` forwards the option.
- `qc_cli.py compare-d7-retrieval --projects-dir path ...` forwards the option
  to the canonical script.
- Tests cover direct comparison-script loading from a repo-local project store
  and top-level CLI forwarding.
- `CLAUDE.md`, generated `AGENTS.md`, and `docs/EVALUATION_HARNESS.md` document
  the portability surface while preserving the non-evidentiary claim caveat.

Verification:

- `python -m pytest tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py -q`
  - 21 passed
- `python -m ruff check scripts/compare_d7_retrieval.py qc_cli.py tests/test_d7_comparison_guard.py tests/test_qc_cli_d7_retrieval.py`
  - passed
- `make docs-check`
  - passed
- `git diff --check`
  - passed
- `make check`
  - 1297 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this plan create the D7 artifact itself?
  Status: RESOLVED. No. This plan removes the comparison-store portability
  blocker. The next plan can create/replay a portable D7 retrieval-comparison
  artifact using both explicit project-store surfaces.

---

## Notes

This mirrors the existing `--projects-dir` pattern in Phase 0 and D7 retrieval
export surfaces.
