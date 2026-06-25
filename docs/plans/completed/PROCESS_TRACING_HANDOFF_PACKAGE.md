# Plan #233: Process-Tracing Handoff Package

## Outcome

Completed 2026-06-25. Added a strict schema_version=1 QC-to-process-tracing
handoff package with Pydantic models, exporter, validator, script wrappers,
top-level `qc_cli.py` commands, Make targets, focused tests, and deterministic
reviewer-demo fixture output. The package contains project/corpus/scope
metadata, document content hashes, observed patterns, abductive candidates,
analytic claims, package-local anchors, provenance hashes, and caveats. It
rejects missing candidate pattern references, missing anchor document
references, and forbidden process-tracing inference fields. It deliberately
excludes likelihood vectors, posterior/comparative-support fields, Bayesian
updates, and process-tracing internal result artifacts. This is a QC-side
boundary artifact for consumer review, not causal proof, process-tracing
results, methodological-validity evidence, or SOTA evidence.

Verification:

- `python -m pytest tests/test_process_tracing_handoff.py -q` — 5 passed.
- `python -m pytest tests/test_process_tracing_handoff.py
  tests/test_reviewer_demo.py -q` — 8 passed.
- `python -m ruff check qc_clean/core/process_tracing_handoff.py
  scripts/export_process_tracing_handoff.py
  scripts/validate_process_tracing_handoff.py qc_cli.py
  scripts/build_reviewer_demo.py tests/test_process_tracing_handoff.py
  tests/test_reviewer_demo.py` — passed.
- `make reviewer-demo OUTPUT=test_output/reviewer_demo` — passed and wrote
  `handoff/process_tracing_handoff.json`.
- `make export-process-tracing-handoff ID=reviewer-demo
  PROJECTS_DIR=test_output/reviewer_demo/projects
  OUTPUT=test_output/reviewer_demo/handoff/make_handoff.json` — passed.
- `make validate-process-tracing-handoff
  PACKAGE=test_output/reviewer_demo/handoff/process_tracing_handoff.json` —
  passed.
- `QC_PROJECTS_DIR=test_output/reviewer_demo/projects python qc_cli.py
  export-process-tracing-handoff reviewer-demo --output
  test_output/reviewer_demo/handoff/qc_cli_handoff.json` — passed.
- `python qc_cli.py validate-process-tracing-handoff
  test_output/reviewer_demo/handoff/qc_cli_handoff.json` — passed.
- `make docs-check` — passed.
- `git diff --check` — passed.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** #231, #232
**Blocks:** future process-tracing consumer review, mixed-methods workbench bridge

---

## Gap

**Current:** QC now has first-class observed patterns, provisional abductive
candidate explanations, and reviewable candidate statuses. The adjacent
`~/projects/process_tracing` repo explicitly says it should consume QC claims,
patterns, anchors, and candidate explanations through typed contracts when the
bridge is ready. No QC-side versioned handoff package exists yet.

**Target:** Add a strict, versioned QC-to-process-tracing handoff package that
exports corpus scope, document metadata, observed patterns, abductive
candidates, analytic claims, anchors, provenance hashes, and caveats. Add a
validator and agent-drivable CLI/Make surfaces. The package must exclude
process-tracing likelihood vectors, Bayesian posterior/support fields, and PT
internal result structures.

**Why:** This is the first stable seam toward the future
`mixed_methods_workbench`: QC supplies qualitative evidence objects; process
tracing supplies causal diagnostic testing.

---

## References Reviewed

- `docs/LONG_TERM_EXECUTION_PLAN.md` - names Plan #233 as the next slice and
  defines acceptance/audit criteria.
- `CLAUDE.md` - QC/process-tracing workbench boundary and QC-owned surfaces.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and status caveats.
- `/home/brian/projects/process_tracing/CLAUDE.md` - process-tracing boundary,
  future adapter surface, and explicit warning not to import internal
  `pt.schemas` or parse `result.json` across the workbench seam.
- `/home/brian/projects/process_tracing/pt/source_packet.py` - source-packet
  contract style and source-scope fields.
- `/home/brian/projects/process_tracing/pt/schemas.py` - evidence/hypothesis
  internals that must stay out of the QC handoff package.
- `qc_clean/schemas/domain.py` - QC source models for documents, scope,
  observed patterns, abductive candidates, claims, and anchors.
- `qc_clean/core/export/data_exporter.py` - existing export style and scope
  warnings.
- `qc_clean/core/pipeline/review.py` - candidate review status semantics.
- `scripts/build_reviewer_demo.py` - deterministic fixture for a handoff smoke
  package.
- Memory context:
  `agent-memory recall 'active decisions process tracing handoff qualitative coding typed package' --project qualitative_coding`
  returned broad historical task summaries and no active decision overriding
  repo docs.

---

## Research Basis For This Slice

No external web research is needed. This is a local cross-repo contract slice
based on the explicit QC and process-tracing repo boundary docs.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Export process-tracing handoff | `ProjectState`, optional output path | `ProcessTracingHandoffPackageV1` JSON | QC | process_tracing, mixed_methods_workbench | free / no LLM calls |
| Validate process-tracing handoff | package JSON path | validation success or fail-loud errors | QC | agents, CI, process_tracing reviewer | free / no LLM calls |

### Capability Validation

- [x] Package model uses Pydantic fields with descriptions.
- [x] Validator enforces schema version, candidate source-pattern references,
  anchor document references, and absence of PT inference fields.
- [x] CLI/Make surfaces are agent-drivable.
- [x] Reviewer demo can generate a deterministic handoff fixture.

---

## Files Affected

- `qc_clean/core/process_tracing_handoff.py` - package models, exporter,
  validator.
- `scripts/export_process_tracing_handoff.py` - script wrapper.
- `scripts/validate_process_tracing_handoff.py` - validator wrapper.
- `qc_cli.py` - top-level CLI wrappers.
- `Makefile` - export/validate targets.
- `scripts/build_reviewer_demo.py` - optional handoff fixture in demo packet.
- `tests/test_process_tracing_handoff.py` - package/export/validator tests.
- `tests/test_reviewer_demo.py` - demo packet fixture assertion if updated.
- `docs/plans/ACTIVE_SPRINT.md`, `docs/plans/CLAUDE.md`, and status docs -
  plan tracking and caveats.

---

## Plan

### Steps

1. Register Plan #233 as active and commit the planned state.
2. Add tests for package export shape, reference validation, PT-field
   rejection, CLI/script wrappers, and reviewer-demo fixture output.
3. Implement strict Pydantic package models and exporter.
4. Implement validator/load function that fails loud on reference drift.
5. Add script, CLI, and Make surfaces.
6. Add demo packet handoff fixture if it stays deterministic and small.
7. Run focused tests, Ruff, demo generation, docs checks, `git diff --check`,
   and `make check`.
8. Close the plan, update the execution spine/concerns, commit, push, and
   continue.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_process_tracing_handoff.py` | `test_export_process_tracing_handoff_package_shape` | Export includes scope, docs, patterns, candidates, claims, anchors, caveats, and hashes. |
| `tests/test_process_tracing_handoff.py` | `test_validate_rejects_missing_candidate_pattern_reference` | Candidate source-pattern drift fails loud. |
| `tests/test_process_tracing_handoff.py` | `test_validate_rejects_process_tracing_inference_fields` | Package cannot carry likelihood/posterior/Bayesian internals. |
| `tests/test_process_tracing_handoff.py` | `test_cli_exports_and_validates_handoff_package` | CLI/script path is agent-drivable. |
| `tests/test_reviewer_demo.py` | update packet test | Demo packet includes a deterministic handoff package if added. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_process_tracing_handoff.py tests/test_reviewer_demo.py -q` | Focused contract/demo coverage. |
| `python -m ruff check qc_clean/core/process_tracing_handoff.py scripts/export_process_tracing_handoff.py scripts/validate_process_tracing_handoff.py qc_cli.py tests/test_process_tracing_handoff.py scripts/build_reviewer_demo.py tests/test_reviewer_demo.py` | Touched-file lint. |
| `make reviewer-demo OUTPUT=test_output/reviewer_demo` | Prove deterministic fixture output. |
| `make docs-check` | Plan/docs governance. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Package schema version is explicit and strict.
- [x] Package contains project/corpus/scope metadata, document hashes,
  observed patterns, abductive candidates, analytic claims, anchors,
  provenance, and caveats.
- [x] Package excludes PT likelihood vectors, posterior/support fields,
  Bayesian update fields, and PT internal result artifacts.
- [x] Validator fails loud on bad schema version, missing candidate
  source-pattern IDs, missing anchor document IDs, and forbidden PT fields.
- [x] CLI and Make surfaces can export and validate a package from an explicit
  or environment-provided project store.
- [x] Demo packet includes a deterministic handoff fixture if added.

> Process criteria:
- [x] Focused tests pass.
- [x] Ruff passes for touched files.
- [x] `make reviewer-demo OUTPUT=test_output/reviewer_demo` passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] `make check` passes.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should this package import process-tracing schemas? Status: RESOLVED no.
  PT docs explicitly warn against cross-engine imports of internal schemas.
- [ ] Should this package include comparative support or posterior fields?
  Status: RESOLVED no. Those are process-tracing outputs, not QC handoff
  inputs.
- [ ] Should process-tracing consumer changes happen in this slice? Status:
  RESOLVED no. This slice creates the QC-side fixture and validator; consumer
  review follows.

---

## Notes

This is an adapter seam, not a causal inference result. The package should make
qualitative evidence usable by a process-tracing engine without pretending that
QC itself has completed process tracing.
