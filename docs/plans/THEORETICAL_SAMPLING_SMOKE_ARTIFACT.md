# Plan #222: Theoretical Sampling Smoke Artifact

**Status:** Active
**Type:** artifact
**Priority:** High
**Blocked By:** None
**Blocks:** stronger INV-4 review evidence and future true sampling-cycle work

---

## Gap

**Current at plan start:** INV-4 has deterministic category adequacy diagnostics,
diagnostic-driven loaded-document suggestions, theoretical-sampling protocol
validation, candidate export, result export, and preflight surfaces. Those
surfaces are tested, and Plan #221 made candidate export portable with
`PROJECTS_DIR` / `--projects-dir`. There is not yet a committed repo-local
artifact that demonstrates the end-to-end protocol -> candidate -> result ->
preflight workflow on a portable project store.

**Target:** Commit a small synthetic smoke artifact under `docs/benchmarks/`
that exercises the existing INV-4 theoretical-sampling package workflow from a
repo-local project store:

1. Store a synthetic GT-inspired project with one coded document and one loaded
   uncoded candidate document.
2. Register a protocol whose hashes match that project/corpus.
3. Validate the protocol.
4. Export loaded-document candidates using explicit `PROJECTS_DIR`.
5. Export selected-candidate results.
6. Preflight candidate/result packages against the protocol and record the
   passing report.
7. Document exact commands, observed status, and claim caveats.

**Why:** This gives Brian and future agents a concrete output surface to inspect
for INV-4 package provenance before attempting real/populated theoretical
sampling cycles.

**Claim boundary:** This is a synthetic workflow/provenance smoke artifact only.
It does not execute real theoretical sampling, collect new data, prove sampling
adequacy, prove category saturation, establish GT-fidelity evidence, provide
methodological-validity evidence, or support SOTA claims.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md` §13/§18 - INV-4 status and remaining
  populated theoretical-sampling work.
- `docs/EVALUATION_HARNESS.md` - theoretical-sampling package surfaces and
  caveats.
- `docs/plans/completed/THEORETICAL_SAMPLING_PROJECTS_DIR_PARITY.md` - explicit
  repo-local project-store support.
- `docs/plans/completed/THEORETICAL_SAMPLING_CANDIDATE_EXPORT.md` and
  `docs/plans/completed/THEORETICAL_SAMPLING_RESULT_EXPORT.md` - candidate and
  result package surfaces.
- `scripts/validate_theoretical_sampling_protocol.py`
- `scripts/export_theoretical_sampling_candidates.py`
- `scripts/export_theoretical_sampling_results.py`
- `scripts/preflight_theoretical_sampling_protocol.py`
- `qc_clean/core/theoretical_sampling_protocol.py`
- `qc_clean/core/theoretical_sampling_candidates.py`
- `qc_clean/core/theoretical_sampling_results.py`
- `qc_clean/core/theoretical_sampling_preflight.py`
- `tests/test_theoretical_sampling_candidate_export.py`
- `tests/test_theoretical_sampling_result_export.py`
- Coordination claims:
  `python scripts/meta/check_coordination_claims.py --check --project qualitative_coding --scope inv4-theoretical-sampling-artifact`
  returned no active claims.
- Memory context:
  `agent-memory recall 'INV-4 theoretical sampling artifact active decisions' --project qualitative_coding`
  returned no relevant active decision.

---

## Research Basis For This Slice

No external research is needed. This is a repo-local artifact/provenance slice
over existing deterministic scripts.

---

## Capabilities

Internal project capability only; no cross-project registry entry is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `theoretical_sampling_smoke_artifact` | repo-local project store + protocol | validated candidates/results/preflight JSON artifacts | qualitative_coding | humans and agents reviewing INV-4 package workflow | free |

### Capability Validation

Skipped for cross-project registry purposes: this is a committed benchmark-style
artifact over existing project-local capabilities.

---

## Files Affected

- `docs/plans/THEORETICAL_SAMPLING_SMOKE_ARTIFACT.md` - active plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - sprint checkpoint.
- `docs/benchmarks/theoretical_sampling_smoke_2026_06_23/`:
  - `README.md`
  - `projects/theoretical_sampling_smoke_project.json`
  - `protocol.json`
  - `validated_protocol.json`
  - `candidates.json`
  - `results.json`
  - `preflight.json`

---

## Plan

### Steps

1. Create and commit this plan before artifact generation.
2. Generate a synthetic repo-local `ProjectState` with one coded document and
   one loaded uncoded candidate document.
3. Generate a matching theoretical-sampling protocol with project and corpus
   hashes computed from the project JSON.
4. Run `qc_cli.py validate-theoretical-sampling-protocol` and save
   `validated_protocol.json`.
5. Run `make export-theoretical-sampling-candidates` with `PROJECTS_DIR=...`
   and save `candidates.json`.
6. Run `qc_cli.py export-theoretical-sampling-results` and save `results.json`.
7. Run `make theoretical-sampling-preflight` and save `preflight.json`.
8. Add `README.md` with commands, summary, and caveats.
9. Verify JSON status/counts, run focused theoretical-sampling tests, docs
   checks, whitespace checks, and `make check`.
10. Commit/push implementation and close the plan.

---

## Required Tests

### Artifact Checks

| Check | What It Verifies |
|-------|------------------|
| `python qc_cli.py validate-theoretical-sampling-protocol docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json > docs/benchmarks/theoretical_sampling_smoke_2026_06_23/validated_protocol.json` | Protocol validates and emits normalized JSON. |
| `make export-theoretical-sampling-candidates ID=theoretical-sampling-smoke PROJECTS_DIR=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/projects PROTOCOL=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json OUTPUT=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json MAX=1` | Candidate export works from explicit repo-local project store. |
| `python qc_cli.py export-theoretical-sampling-results docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json --candidates-file docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json --selected-candidate-id loaded-doc-2 --success-criterion-met "Every targeted gap has an explicit sampling decision." --output docs/benchmarks/theoretical_sampling_smoke_2026_06_23/results.json` | Result package records selected candidate and registered criterion. |
| `make theoretical-sampling-preflight PROTOCOL=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/protocol.json CANDIDATES=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/candidates.json RESULTS=docs/benchmarks/theoretical_sampling_smoke_2026_06_23/results.json > docs/benchmarks/theoretical_sampling_smoke_2026_06_23/preflight.json` | Candidate/result packages pass protocol preflight. |
| JSON inspection command | `preflight.status == "pass"`, candidate count is `1`, selected count is `1`, and all artifact caveats are present. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_theoretical_sampling_candidate_export.py tests/test_theoretical_sampling_result_export.py tests/test_theoretical_sampling_preflight.py tests/test_export_theoretical_sampling_candidates_script.py tests/test_export_theoretical_sampling_results_script.py tests/test_qc_cli_theoretical_sampling_surfaces.py -q` | Focused INV-4 package/script/CLI coverage. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic gate before closeout. |

---

## Acceptance Criteria

Artifact criteria:

- [ ] `docs/benchmarks/theoretical_sampling_smoke_2026_06_23/README.md`
  explains what the artifact is and is not.
- [ ] Repo-local project store is committed under the artifact directory.
- [ ] `protocol.json` validates and is accompanied by `validated_protocol.json`.
- [ ] `candidates.json` was generated from explicit `PROJECTS_DIR`.
- [ ] `results.json` records the selected candidate and registered success
  criterion.
- [ ] `preflight.json` has `status == "pass"`, `candidate_count == 1`, and
  `result_selected_count == 1`.
- [ ] Caveats explicitly say this is workflow/provenance smoke evidence only,
  not theoretical sampling execution, sampling adequacy, saturation,
  GT-fidelity, methodological-validity, or SOTA evidence.

Process criteria:

- [ ] Focused theoretical-sampling tests pass.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified increment is committed and pushed.

---

## Outcome

Pending.

---

## Open Questions

- [ ] Should this artifact use real project data?
  Default: no. Use a synthetic fixture because real theoretical sampling would
  require human data-selection judgment and would change the evidentiary claim.

---

## Notes

This artifact is intentionally analogous to the D7 and INV-7 smoke artifacts:
it proves a portable workflow surface and provenance shape, not methodological
validity.
