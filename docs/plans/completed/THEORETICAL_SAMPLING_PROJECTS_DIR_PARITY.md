# Plan #221: Theoretical Sampling Projects Dir Parity

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** portable INV-4 theoretical-sampling smoke artifacts

---

## Gap

**Current at plan start:** Theoretical-sampling candidate export is available
through script, Make, and `qc_cli.py`, but `scripts/export_theoretical_sampling_candidates.py`
constructs the default `ProjectStore()`. A caller can indirectly redirect it
with `QC_PROJECTS_DIR`, but there is no explicit `--projects-dir` /
`PROJECTS_DIR=` surface like the newer D7 retrieval, live-baseline, comparison,
and Phase 0 package workflows.

**Target:** Add optional explicit project-store selection to theoretical
sampling candidate export through script, Make, and `qc_cli.py
export-theoretical-sampling-candidates`, while preserving default behavior when
omitted.

**Why:** The next INV-4 artifact should be replayable from a repo-local project
store without hidden dependence on the user's default `~/.qc_projects` store or
ambient environment variables.

**Claim boundary:** This is portability/provenance plumbing only. It does not
execute real theoretical sampling, collect new data, prove sampling adequacy,
prove category saturation, establish GT-fidelity evidence, provide
methodological-validity evidence, or support SOTA claims.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13/§18 - INV-4 status and remaining true
  theoretical-sampling work.
- `docs/EVALUATION_HARNESS.md` - theoretical-sampling protocol/candidate/result
  package surfaces and caveats.
- `docs/plans/completed/THEORETICAL_SAMPLING_CANDIDATE_EXPORT.md` - original
  candidate export surface.
- `docs/plans/completed/QC_CLI_THEORETICAL_SAMPLING_SURFACES.md` - current CLI
  wrappers.
- `docs/plans/completed/D7_RETRIEVAL_PROJECTS_DIR_PARITY.md` and
  `docs/plans/completed/D7_LIVE_BASELINE_PROJECTS_DIR_PARITY.md` - recent
  explicit project-store pattern.
- `scripts/export_theoretical_sampling_candidates.py` - current default
  `ProjectStore()` use.
- `Makefile` - current `export-theoretical-sampling-candidates` target.
- `qc_cli.py` - current parser and forwarding handler.
- `tests/test_export_theoretical_sampling_candidates_script.py` and
  `tests/test_qc_cli_theoretical_sampling_surfaces.py` - current focused
  coverage.
- Coordination claims:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope roadmap-continuation`
  returned no active claims.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` returned
  no relevant active decision.

---

## Research Basis For This Slice

No external research is needed. This is repo-local execution-surface parity
before creating a portable INV-4 artifact.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `export_theoretical_sampling_candidates` with explicit project store | project ID + protocol package + optional projects_dir + candidate filters | theoretical-sampling candidate package JSON | qualitative_coding | theoretical-sampling preflight/result workflows | free |

### Capability Validation

Skipped for cross-project registry purposes: this extends an existing
project-local script and CLI surface.

---

## Files Affected

- `docs/plans/THEORETICAL_SAMPLING_PROJECTS_DIR_PARITY.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `scripts/export_theoretical_sampling_candidates.py` - `--projects-dir`
  argument and ProjectStore construction.
- `Makefile` - optional `PROJECTS_DIR=` forwarding for candidate export.
- `qc_cli.py` - `--projects-dir` parser/forwarding for candidate export.
- `tests/test_export_theoretical_sampling_candidates_script.py` - script uses
  explicit project store.
- `tests/test_qc_cli_theoretical_sampling_surfaces.py` - CLI forwards
  `--projects-dir`.
- Docs after implementation:
  - `CLAUDE.md` and regenerated `AGENTS.md`
  - `docs/EVALUATION_HARNESS.md`

---

## Plan

### Steps

1. Add failing tests for script `--projects-dir` loading and `qc_cli.py`
   forwarding.
2. Add `--projects-dir` to `scripts/export_theoretical_sampling_candidates.py`;
   construct `ProjectStore(projects_dir=args.projects_dir)` only when supplied.
3. Add `PROJECTS_DIR=` forwarding to the Make target.
4. Add `--projects-dir` parser and handler forwarding to `qc_cli.py
   export-theoretical-sampling-candidates`.
5. Update command docs conservatively.
6. Run focused tests, touched Ruff, docs checks, and `make check`.
7. Commit/push implementation and close the plan.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_export_theoretical_sampling_candidates_script.py` | `test_export_theoretical_sampling_candidates_accepts_projects_dir` | Script loads the project from an explicit repo-local store without monkeypatching default `ProjectStore()`. |
| `tests/test_qc_cli_theoretical_sampling_surfaces.py` | `test_qc_cli_export_theoretical_sampling_candidates_forwards_projects_dir` | Canonical CLI forwards `--projects-dir` to the candidate export script. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_export_theoretical_sampling_candidates_script.py tests/test_qc_cli_theoretical_sampling_surfaces.py -q` | Focused theoretical-sampling script/CLI coverage. |
| `python -m ruff check scripts/export_theoretical_sampling_candidates.py qc_cli.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_qc_cli_theoretical_sampling_surfaces.py` | Touched Python lint gate. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Feature-level criteria:

- [x] `scripts/export_theoretical_sampling_candidates.py --projects-dir path`
  loads from that store.
- [x] `make export-theoretical-sampling-candidates PROJECTS_DIR=path ...`
  forwards the path.
- [x] `qc_cli.py export-theoretical-sampling-candidates --projects-dir path ...`
  forwards the path.
- [x] Default behavior without `--projects-dir` remains unchanged.
- [x] Docs preserve claim discipline: this is portability/provenance support,
  not theoretical sampling execution, sampling adequacy evidence, saturation
  evidence, GT-fidelity evidence, methodological-validity evidence, or SOTA
  evidence.

Process criteria:

- [x] Focused tests pass.
- [x] Touched Python Ruff gate passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified increment is committed and pushed.

---

## Outcome

Completed in commit `51f3aecf`.

Implemented optional explicit project-store loading for theoretical-sampling
candidate export:

- `scripts/export_theoretical_sampling_candidates.py` accepts `--projects-dir
  path` and constructs `ProjectStore(projects_dir=...)` only when supplied.
- `make export-theoretical-sampling-candidates PROJECTS_DIR=path ...` forwards
  the option.
- `qc_cli.py export-theoretical-sampling-candidates --projects-dir path ...`
  forwards the option to the canonical script.
- Tests cover direct script loading from a repo-local project store and
  top-level CLI forwarding.
- `CLAUDE.md`, generated `AGENTS.md`, and `docs/EVALUATION_HARNESS.md` document
  the portability surface while preserving the non-evidentiary claim caveat.

Verification:

- `python -m pytest tests/test_export_theoretical_sampling_candidates_script.py tests/test_qc_cli_theoretical_sampling_surfaces.py -q`
  - 8 passed
- `python -m ruff check scripts/export_theoretical_sampling_candidates.py qc_cli.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_qc_cli_theoretical_sampling_surfaces.py`
  - passed
- `make -n export-theoretical-sampling-candidates ID=project-alpha PROJECTS_DIR=projects PROTOCOL=protocol.json OUTPUT=candidates.json MAX=1`
  - dry-run included `--projects-dir projects`
- `make docs-check`
  - passed
- `git diff --check`
  - passed
- `make check`
  - 1308 passed, 1 skipped, 8 deselected; Ruff passed; docs-check passed;
    type check is not yet configured

---

## Open Questions

- [x] Should this plan also create the committed INV-4 smoke artifact?
  Status: RESOLVED. No. This slice only makes candidate export portable across
  project stores. A later plan can use it to create/replay an INV-4 artifact.

---

## Notes

This mirrors the existing `--projects-dir` pattern in D7 and Phase 0 workflows.
