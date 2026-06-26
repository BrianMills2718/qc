# Plan #242: Mixed-Methods Workbench Export Fixture

**Status:** Planned
**Type:** design
**Priority:** High
**Blocked By:** #241 - current methodology/pipeline alignment must remain the authority for claim discipline
**Blocks:** `mixed_methods_workbench` Plan 001 QC fixture readiness

---

## Gap

**Current:** The repo has a strict `schema_version=1` process-tracing handoff package that exports corpus scope, document hashes, observed patterns, abductive candidates, analytic claims, anchors, caveats, and provenance. It is suitable as a boundary artifact, but no canonical workbench fixture has been selected, regenerated, and documented for the future mixed-methods workbench.

**Target:** A committed, reproducible, workbench-safe QC export fixture that can be consumed by `mixed_methods_workbench` without importing QC internals or conflating qualitative coding with process tracing.

**Why:** The workbench needs a small real artifact to design against before live engine integration. The fixture should prove the QC side of the contract while keeping causal inference, likelihood vectors, and process-tracing conclusions out of the QC artifact.

---

## References Reviewed

- `CLAUDE.md` - repo conventions and current dirty-worktree context
- `docs/plans/CLAUDE.md` - active/completed plan index
- `docs/plans/TEMPLATE.md` - required plan structure
- `qc_clean/core/process_tracing_handoff.py` - current strict handoff package contract and forbidden PT inference fields
- `docs/plans/completed/PROCESS_TRACING_HANDOFF_PACKAGE.md` - prior completed boundary-artifact record
- Memory context: `agent-memory recall 'process tracing workbench export pt_export_v1 active decisions' --project process_tracing` - no active-decision blocker found for this export planning slice

---

## Research Basis For This Slice

- `/home/brian/projects/investigations/cross-project/2026-06-26-theory-forge-worktrees.md` - cross-project finding that Theory Forge should be treated as an artifact producer for now, not as a live AC15-coupled dependency
- `/home/brian/projects/mixed_methods_workbench/docs/plans/002_engine_stability_and_integration_readiness.md` - integration-readiness plan that marks live workbench buildout as gated by engine stability

---

## Operational Validation

**Classification:** claim_bearing_output
**Surface IDs:** `qualitative_coding.process_tracing_handoff`
**Real-Run Requirement:** required
**Deferred Reason:** Not deferred. The implementation slice must regenerate the selected fixture from an actual QC project state and validate it through the strict handoff package schema before it can be used by the workbench.

---

## Files Affected

- `docs/plans/MIXED_METHODS_WORKBENCH_EXPORT_FIXTURE.md` (this plan)
- `docs/plans/CLAUDE.md` (active plan index)
- Future implementation candidates:
  - `docs/fixtures/mixed_methods_workbench/README.md` (create)
  - `docs/fixtures/mixed_methods_workbench/qc_handoff_v1.json` (create)
  - `docs/fixtures/mixed_methods_workbench/manifest.json` (create)
  - focused tests or validator scripts only if the existing handoff validator is insufficient

---

## Plan

### Steps

1. Confirm the local worktree state and distinguish pre-existing dirty files from this plan's implementation work.
2. Select the smallest existing QC project state that contains corpus scope, at least two documents, observed patterns, analytic claims, anchors, and, if available, abductive candidates.
3. Regenerate the handoff package through the existing `ProcessTracingHandoffPackage` path rather than hand-authoring JSON.
4. Add a package manifest with producer commit, generation command, source project identifier, source-state hash, package hash, and caveats.
5. Add a README that states the fixture is qualitative evidence context only: not causal proof, not process-tracing output, not method validation, and not SOTA evidence.
6. Validate that no process-tracing inference fields appear in the fixture or manifest.
7. Document the consumer contract for `mixed_methods_workbench`: consume the package as data, do not import QC internals, and do not promote QC confidence into causal probability.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| TBD | TBD | Add only if existing handoff package validation cannot be invoked for fixture verification |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| Existing handoff package validator or package import path | Proves the committed fixture conforms to the strict QC export contract |
| Plan/docs gate | Proves the plan and documentation remain indexed and valid |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A single canonical workbench fixture exists under `docs/fixtures/mixed_methods_workbench/`.
- [ ] The fixture validates as `schema_version=1` `qualitative_coding.process_tracing_handoff`.
- [ ] The fixture includes corpus scope or an explicit missing-scope caveat, document hashes, anchors, observed patterns, analytic claims, provenance, and caveats.
- [ ] The fixture contains no process-tracing inference fields such as likelihood vectors, Bayesian updates, posteriors, or comparative support.
- [ ] The fixture README states that abductive candidates are provisional hypotheses for review, not causal conclusions.
- [ ] The fixture manifest records producer commit and package hash.

> Process criteria:
- [ ] Pre-existing dirty files are listed in the implementation note before any commit.
- [ ] Required validation command passes.
- [ ] Docs/index validation passes.
- [ ] No workbench code imports QC internal modules.

---

## Open Questions

- [ ] Which existing QC project state is the least misleading canonical fixture? - Status: OPEN | Why it matters: the fixture will shape workbench contract design and should not overstate methodological maturity.
- [ ] Should abductive candidates be required for the first fixture or allowed to be absent? - Status: OPEN | Why it matters: the workbench needs to plan for QC outputs that may not yet contain reviewed candidate explanations.
- [ ] What is the durable consumer schema name in `mixed_methods_workbench`? - Status: OPEN | Why it matters: the workbench should own its consumer-side permissive model instead of importing producer classes.

---

## Notes

This plan is intentionally documentation/fixture-first. It should not add live mixed-methods integration, process-tracing calls, or Theory Forge coupling.
