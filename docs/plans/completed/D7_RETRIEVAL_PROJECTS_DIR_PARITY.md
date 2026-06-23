# Plan #211: D7 Retrieval Projects Dir Parity

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** repo-local held-out D7 retrieval/export artifacts and package replay

---

## Gap

**Current at plan start:** `scripts/run_d7_retrieval.py` always loaded projects
from the default `ProjectStore()`. `make bench`, Phase 0 package runs,
export-audit surfaces, and reviewer-demo flows already supported explicit
project stores via `PROJECTS_DIR` / `--projects-dir`. D7 retrieval export could
not yet run against a repo-local held-out project shell without monkeypatching
or mutating the user default project store.

**Target:** Add optional `--projects-dir` / `PROJECTS_DIR=` support to D7
retrieval export through script, Make, and `qc_cli.py run-d7-retrieval`, while
preserving default behavior when omitted.

**Why:** Held-out D7 retrieval and comparison artifacts need portable,
repo-local project stores just like Phase 0 benchmark artifacts. This is
execution/provenance plumbing only; it does not create held-out D7 evidence or
change retrieval scoring.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - next high-value D7 lane after INV-7.
- `docs/EVALUATION_HARNESS.md` - D7 retrieval export and comparison workflow.
- `docs/plans/completed/D7_RETRIEVAL_MODE_EXPORT.md` - original D7 retrieval
  package surface.
- `docs/plans/completed/D7_RETRIEVAL_EXPORT_SCRIPT_TESTS.md` - script and CLI
  wrapper coverage.
- `docs/plans/completed/PHASE0_PACKAGE_PROJECTS_DIR_SUPPORT.md` - prior
  project-store portability pattern.
- `scripts/run_d7_retrieval.py` - current hard-coded default ProjectStore use.
- `Makefile` - current `run-d7-retrieval` target.
- `qc_cli.py` - current `run-d7-retrieval` parser and forwarding handler.
- `tests/test_run_d7_retrieval_script.py` and
  `tests/test_qc_cli_d7_retrieval.py` - current focused coverage.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` - no
  relevant in-flight decision found.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
execution-surface parity slice.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_d7_retrieval` with explicit project store | project ID + optional projects_dir + retrieval config | D7 baseline prediction package JSON | qualitative_coding | D7 comparison/package workflows | free unless embedding_hybrid is selected |

### Capability Validation

Skipped for cross-project registry purposes: this extends an existing
project-local script and CLI surface.

---

## Files Affected

- `docs/plans/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `scripts/run_d7_retrieval.py` - `--projects-dir` argument and ProjectStore
  construction.
- `Makefile` - optional `PROJECTS_DIR=` forwarding for `run-d7-retrieval`.
- `qc_cli.py` - `--projects-dir` parser/forwarding for `run-d7-retrieval`.
- `tests/test_run_d7_retrieval_script.py` - script uses explicit project store.
- `tests/test_qc_cli_d7_retrieval.py` - CLI forwards `--projects-dir`.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add failing tests for script `--projects-dir` loading and `qc_cli.py`
   forwarding.
2. Add `--projects-dir` to `scripts/run_d7_retrieval.py`; construct
   `ProjectStore(projects_dir=args.projects_dir)` only when supplied.
3. Add `PROJECTS_DIR=` forwarding to the Make target.
4. Add `--projects-dir` parser and handler forwarding to `qc_cli.py
   run-d7-retrieval`.
5. Update command docs conservatively.
6. Run focused tests, touched Ruff, docs checks, and `make check`.
7. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_run_d7_retrieval_script.py` | `test_run_d7_retrieval_accepts_projects_dir` | Script loads the project from an explicit repo-local store without monkeypatching default `ProjectStore()`. |
| `tests/test_qc_cli_d7_retrieval.py` | `test_qc_cli_run_d7_retrieval_forwards_projects_dir` | Canonical CLI forwards `--projects-dir` to the script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_run_d7_retrieval_script.py tests/test_qc_cli_d7_retrieval.py -q` | Focused D7 retrieval script/CLI coverage. |
| `python -m ruff check scripts/run_d7_retrieval.py qc_cli.py tests/test_run_d7_retrieval_script.py tests/test_qc_cli_d7_retrieval.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] `scripts/run_d7_retrieval.py --projects-dir path` loads from that store.
- [x] `make run-d7-retrieval PROJECTS_DIR=path ...` forwards the path.
- [x] `qc_cli.py run-d7-retrieval --projects-dir path ...` forwards the path.
- [x] Default behavior without `--projects-dir` remains unchanged.
- [x] Docs preserve claim discipline: this is portability/provenance support,
  not held-out D7 evidence, live-baseline evidence, superiority evidence, or
  SOTA evidence.

Process criteria:

- [x] Focused tests pass.
- [x] Touched Python Ruff gate passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Completed in commit `b3900803`.

Implemented optional explicit project-store loading for D7 retrieval export:

- `scripts/run_d7_retrieval.py` accepts `--projects-dir path` and constructs
  `ProjectStore(projects_dir=...)` only when supplied.
- `make run-d7-retrieval PROJECTS_DIR=path ...` forwards the option.
- `qc_cli.py run-d7-retrieval --projects-dir path ...` forwards the option to
  the canonical script.
- Tests cover direct script loading from a repo-local project store and
  top-level CLI forwarding.
- `CLAUDE.md`, generated `AGENTS.md`, and `docs/EVALUATION_HARNESS.md` document
  the portability surface while preserving the non-evidentiary claim caveat.

Verification:

- `python -m pytest tests/test_run_d7_retrieval_script.py tests/test_qc_cli_d7_retrieval.py -q`
  - 14 passed
- `python -m ruff check scripts/run_d7_retrieval.py qc_cli.py tests/test_run_d7_retrieval_script.py tests/test_qc_cli_d7_retrieval.py`
  - passed
- `make docs-check`
  - passed
- `git diff --check`
  - passed
- `make check`
  - 1295 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this run a held-out D7 comparison?
  Status: RESOLVED. No. This slice only makes the D7 retrieval export portable
  across project stores. A later plan can use it to create/replay held-out
  retrieval artifacts.

---

## Notes

This mirrors the existing `--projects-dir` pattern in Phase 0 and export-audit
surfaces.
