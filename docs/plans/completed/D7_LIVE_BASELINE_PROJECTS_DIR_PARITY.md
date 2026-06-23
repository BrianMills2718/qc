# Plan #214: D7 Live Baseline Projects Dir Parity

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** portable D7 live-baseline packages and live-baseline comparisons

---

## Gap

**Current at plan start:** D7 retrieval export and D7 comparison supported
explicit repo-local project stores through `PROJECTS_DIR` / `--projects-dir`,
but `scripts/run_d7_live_baseline.py` still constructed the default
`ProjectStore()`. That blocked a fully explicit portable workflow for opt-in
live D7 candidate-selection baseline packages.

**Target:** Add optional `--projects-dir` / `PROJECTS_DIR=` support to D7 live
baseline export through script, Make, and `qc_cli.py run-d7-live-baseline`,
while preserving default behavior when omitted.

**Why:** Larger D7 benchmark packages need retrieval, live-baseline, and
comparison steps to all be replayable from repo-local project stores without
hidden environment coupling.

**Claim boundary:** This is execution/provenance plumbing only. It does not run
a live baseline, create live-baseline evidence, prove semantic disconfirmation
validity, establish superiority, provide methodological-validity evidence, or
support SOTA claims.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §18 - D7 live-baseline comparison remains
  not yet done.
- `docs/EVALUATION_HARNESS.md` - D7 live baseline package workflow and caveats.
- `docs/plans/completed/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` - retrieval export
  explicit-store pattern.
- `docs/plans/completed/D7_COMPARISON_PROJECTS_DIR_PARITY.md` - comparison
  explicit-store pattern.
- `scripts/run_d7_live_baseline.py` - current default ProjectStore use.
- `Makefile` - current `run-d7-live-baseline` target.
- `qc_cli.py` - current `run-d7-live-baseline` parser and forwarding handler.
- `tests/test_run_d7_live_baseline_script.py` and
  `tests/test_qc_cli_d7_live_baseline.py` - current focused coverage.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is repo-local
execution-surface parity needed before portable live-baseline artifacts.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `run_d7_live_baseline` with explicit project store | project ID + optional projects_dir + live-baseline config | D7 live-baseline prediction package JSON | qualitative_coding | D7 comparison/package workflows | live LLM cost when actually run |

### Capability Validation

Skipped for cross-project registry purposes: this extends an existing
project-local script and CLI surface.

---

## Files Affected

- `docs/plans/D7_LIVE_BASELINE_PROJECTS_DIR_PARITY.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `scripts/run_d7_live_baseline.py` - `--projects-dir` argument and ProjectStore
  construction.
- `Makefile` - optional `PROJECTS_DIR=` forwarding for
  `run-d7-live-baseline`.
- `qc_cli.py` - `--projects-dir` parser/forwarding for
  `run-d7-live-baseline`.
- `tests/test_run_d7_live_baseline_script.py` - script uses explicit project
  store.
- `tests/test_qc_cli_d7_live_baseline.py` - CLI forwards `--projects-dir`.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add failing tests for script `--projects-dir` loading and `qc_cli.py`
   forwarding.
2. Add `--projects-dir` to `scripts/run_d7_live_baseline.py`; construct
   `ProjectStore(projects_dir=args.projects_dir)` only when supplied.
3. Add `PROJECTS_DIR=` forwarding to the Make target.
4. Add `--projects-dir` parser and handler forwarding to `qc_cli.py
   run-d7-live-baseline`.
5. Update command docs conservatively.
6. Run focused tests, touched Ruff, docs checks, and `make check`.
7. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_run_d7_live_baseline_script.py` | `test_run_d7_live_baseline_accepts_projects_dir` | Script loads the project from an explicit repo-local store without monkeypatching default `ProjectStore()`. |
| `tests/test_qc_cli_d7_live_baseline.py` | `test_qc_cli_run_d7_live_baseline_forwards_projects_dir` | Canonical CLI forwards `--projects-dir` to the live-baseline script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q` | Focused D7 live-baseline script/CLI coverage. |
| `python -m ruff check scripts/run_d7_live_baseline.py qc_cli.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] `scripts/run_d7_live_baseline.py --projects-dir path` loads from that
  store.
- [x] `make run-d7-live-baseline PROJECTS_DIR=path ...` forwards the path.
- [x] `qc_cli.py run-d7-live-baseline --projects-dir path ...` forwards the
  path.
- [x] Default behavior without `--projects-dir` remains unchanged.
- [x] Docs preserve claim discipline: this is portability/provenance support,
  not live-baseline evidence, held-out D7 evidence, superiority evidence,
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

Completed in commit `b3ffb0a0`.

Implemented optional explicit project-store loading for D7 live-baseline export:

- `scripts/run_d7_live_baseline.py` accepts `--projects-dir path` and
  constructs `ProjectStore(projects_dir=...)` only when supplied.
- `make run-d7-live-baseline PROJECTS_DIR=path ...` forwards the option.
- `qc_cli.py run-d7-live-baseline --projects-dir path ...` forwards the option
  to the canonical script.
- Tests cover direct script loading from a repo-local project store and
  top-level CLI forwarding without live LLM calls.
- `CLAUDE.md`, generated `AGENTS.md`, and `docs/EVALUATION_HARNESS.md` document
  the portability surface while preserving the non-evidentiary claim caveat.

Verification:

- `python -m pytest tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py -q`
  - 5 passed
- `python -m ruff check scripts/run_d7_live_baseline.py qc_cli.py tests/test_run_d7_live_baseline_script.py tests/test_qc_cli_d7_live_baseline.py`
  - passed
- `make docs-check`
  - passed
- `git diff --check`
  - passed
- `make check`
  - 1299 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this run the live baseline?
  Status: RESOLVED. No. This slice only makes live-baseline export portable.
  A later plan can run a live baseline under a registered protocol.

---

## Notes

This mirrors the explicit-store pattern now present in D7 retrieval export and
D7 retrieval comparison.
