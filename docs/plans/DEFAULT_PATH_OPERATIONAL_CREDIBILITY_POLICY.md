# Plan #237: Default-Path Operational Credibility Policy

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** further default-path UI/graph/review surface expansion, continuation of Plan #234 beyond the current local seed packet, misleading completion status for user-facing analytic surfaces

---

## Gap

**Current:** The repo distinguishes software/workflow validation from
methodological validation, but it does not enforce a separate standard for
default-path operational credibility of visible analytic surfaces. A surface
can therefore pass schema/tests/docs gates, appear in the UI, and still be
operationally hollow on the default thematic path. The Plan #234 local seed run
exposed exactly that failure mode: the graph UI showed a `Code Relationships`
tab while the default thematic pipeline did not populate `state.code_relationships`,
and the entity map was structurally populated but too sparse to justify a
"polish-stage" interpretation.

**Target:** Add a repo-wide but scoped governance rule for default-path visible
analytic surfaces: if a user-facing surface is exposed by default and implies
analytic capability, it must have a declared producer on the default path,
documented operational acceptance criteria, and explicit real-run validation
requirements before being treated as complete. Add minimum viable enforcement to
planning/docs gates so this rule is harder to bypass accidentally.

**Why:** The current risk is false completion status. The repo can accumulate
infrastructure, schema, and synthetic-fixture wins while default-path user
surfaces remain operationally weak. That undermines prioritization, hides
product holes, and creates misleading progress signals.

---

## References Reviewed

- `CLAUDE.md` - canonical operational guidance and current state wording.
- `docs/PROJECT_THEORY_AND_GOALS.md` - honest state, invariant framing, and
  claim discipline.
- `docs/VALIDATION.md` - current software/workflow/methodological validation
  distinctions.
- `docs/LONG_TERM_EXECUTION_PLAN.md` - execution spine and current active lane.
- `docs/plans/CLAUDE.md` - plan policy, lifecycle, and current governance
  enforcement notes.
- `docs/plans/ACTIVE_SPRINT.md` - active queue and checkpoint framing.
- `docs/plans/TEMPLATE.md` - required plan structure.
- `scripts/meta/validate_plan.py` - current plan-validation entrypoint.
- `scripts/sync_plan_status.py` - active/completed plan consistency checker.
- `Makefile` - current default docs gate.
- `qc_clean/core/pipeline/stages/relationship.py` - default thematic
  relationship producer.
- `qc_clean/plugins/api/api_server.py` and `qc_clean/plugins/api/graph_ui.py`
  - current visible graph/review surfaces.
- User review on 2026-06-25 - default thematic graph surfaced an empty code
  relationships tab and sparse entity map on a real local seed run.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

No new end-user analytic capability is planned. This slice adds governance and
planning enforcement over how existing or future user-facing capabilities may be
declared complete.

### Capability Validation

- [ ] New governance artifacts are repo-local and machine-readable where
  practical.
- [ ] Default-path visible surfaces have an explicit policy home and validation
  mode.
- [ ] Default docs/planning gates fail loudly on clear policy violations, not on
  subjective quality judgments.

---

## Files Affected

- `docs/plans/DEFAULT_PATH_OPERATIONAL_CREDIBILITY_POLICY.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/plans/TEMPLATE.md` (modify)
- `CLAUDE.md` (modify)
- `docs/VALIDATION.md` (modify)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/governance/default_path_surface_contracts.yaml` (create)
- `scripts/check_default_path_surface_contracts.py` (create)
- `scripts/check_surface_operational_readiness.py` (create or defer if too
  noisy)
- `Makefile` (modify)
- `tests/` (add focused validator tests if new scripts are introduced)

---

## Plan

### Steps

1. Review the current validation/governance language and clean up any ambiguity
   around software vs workflow vs methodological validation before adding new
   enforcement.
2. Define the repo-wide policy statement for default-path visible analytic
   surfaces, including scope limits so the rule does not become ceremony for
   internal-only work.
3. Add a machine-readable default-path surface contract registry for the
   highest-value visible surfaces first: review UI, graph UI tabs, report/export
   surfaces, and other claim-bearing default-path outputs.
4. Add minimum viable enforcement:
   - configuration validation for the new surface-contract registry; and
   - planning/documentation requirements that make operational validation
     explicit for user-facing slices.
5. Update canonical docs and planning docs to distinguish:
   - structural/software completion;
   - operational verification on the default path; and
   - methodological validation/evidence.
6. Re-rank active work so policy/governance enforcement lands before further
   default-path feature expansion continues.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_default_path_surface_contracts.py` | `test_contract_registry_validates_known_surface_fields` | The new registry schema rejects missing or malformed producer-contract entries. |
| `tests/test_default_path_surface_contracts.py` | `test_surface_operational_readiness_flags_missing_default_producer` | The enforcement script fails loudly when a visible default-path surface has no compatible producer. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python scripts/meta/validate_plan.py --plan-file docs/plans/DEFAULT_PATH_OPERATIONAL_CREDIBILITY_POLICY.md` | The governance plan itself must validate. |
| `make docs-check` | The new policy must join the default governance path cleanly. |
| `python -m ruff check .` | New governance scripts must satisfy the lint gate. |
| `git diff --check` | Patch hygiene. |
| `make check` | Required if validator scripts or Make behavior change. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Canonical docs define a repo-wide but scoped default-path operational
  credibility policy.
- [ ] The repo distinguishes structural completion, operational verification,
  and methodological validation in operator-facing docs.
- [ ] A machine-readable registry exists for at least the highest-value
  default-path visible analytic surfaces.
- [ ] The default docs/planning gate checks the new registry configuration.
- [ ] Policy/tracker docs make clear that a visible default-path surface cannot
  be called complete if its producer is absent on that path.

> Process criteria:
- [ ] This plan validates before implementation.
- [ ] `make docs-check` passes after the changes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes if new validator code is added.

---

## Operational Validation

**Classification:** governance_only
**Surface IDs:** None
**Real-Run Requirement:** not_required

---

## Open Questions

- [ ] Should completed plans for user-facing slices be required to reference a
  real-run review artifact immediately, or should that start as warning-only?
  Status: OPEN. Initial rollout should likely validate the contract registry and
  doc requirements first, then add stronger artifact requirements later.
- [ ] Should default-path surface enforcement live entirely in docs/planning
  gates, or partially in runtime/UI assertions? Status: OPEN. Minimum viable
  rollout should start in docs/planning gates; runtime assertions may follow for
  obviously unsupported tabs.

---

## Notes

This policy is intentionally scoped. It is repo-wide as a governance standard,
but enforcement should target default-path visible analytic surfaces and
claim-bearing outputs, not every internal helper or compatibility wrapper.
