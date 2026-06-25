# Plan #239: Agent-Drivable Sanitization Workflow

**Status:** Planned
**Type:** design
**Priority:** High
**Blocked By:** None
**Blocks:** any public/shareable corpus package, publication-cleared reviewer packet, sanitizer-backed corpus expansion after Plan #234

---

## Gap

**Current:** Plan #234 proved the local restricted corpus workflow, but the repo
still has no governed mechanism for turning restricted raw interview material
into a reviewed, hashed, de-identification-aware sanitized corpus package. The
current state is explicitly local-only and publication-unsafe by design.

**Target:** Define a repo-governed sanitization workflow that can inventory raw
documents, surface likely identifiers, require reviewed redaction/generalization
decisions, preserve raw-to-sanitized provenance, and emit a sanitized package
with residual-risk caveats.

**Why:** Without a first-class sanitization workflow, every future public corpus
or shareable reviewer packet risks becoming an ad hoc manual process that is
hard to audit and easy to overclaim.

---

## References Reviewed

- `docs/plans/SANITIZED_CORPUS_ADJUDICATION_SEED.md` - completed local-only seed
  slice and deferred sanitizer requirement.
- `docs/LOCAL_DATA_INVENTORY.md` - current metadata-only local corpus inventory.
- `docs/LONG_TERM_EXECUTION_PLAN.md` - execution spine after Plan #234/238.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and current evidence
  boundaries.
- `docs/DEFAULT_PATH_OPERATIONAL_CREDIBILITY_POLICY.md` - user-facing
  operational-credibility doctrine to preserve while adding sanitization
  surfaces.
- `qc_clean/core/export/audit_manifest.py` and export audit tooling - existing
  provenance substrate that a sanitizer workflow should reuse rather than
  bypass.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Operational Validation

**Classification:** claim_bearing_output
**Surface IDs:** `export.markdown_report`
**Real-Run Requirement:** deferred
**Deferred Reason:** This slice is design/governance first. Real-run validation
should occur only after a concrete sanitizer implementation exists and a
restricted test corpus is available for reviewed redaction.

---

## Files Affected

- `docs/plans/AGENT_DRIVABLE_SANITIZATION_WORKFLOW.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `docs/LONG_TERM_EXECUTION_PLAN.md` (modify)
- `docs/plans/SANITIZED_CORPUS_ADJUDICATION_SEED.md` (reference only if needed)

---

## Plan

### Steps

1. Review current corpus/export/provenance surfaces and document what a
   sanitizer must preserve.
2. Define the sanitization workflow boundary: raw inventory, identifier review,
   transformation log, residual-risk record, hashed raw/sanitized linkage.
3. Specify human-review checkpoints and which steps may be agent-assisted
   versus must be explicitly confirmed by a human operator.
4. Define the output contracts for a sanitized corpus package and for a
   de-identification decision log.
5. Queue the implementation slice only after the design is specific enough to
   test on a small restricted corpus.

---

## Required Tests

### New Tests (TDD)

No code tests in this design slice.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `./.venv/bin/python scripts/sync_plan_status.py --check --validate-active` | Planning state must stay coherent. |
| `./.venv/bin/python scripts/check_surface_operational_readiness.py` | New active plan must declare operational-validation posture correctly. |
| `git diff --check` | Patch hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Sanitization scope, boundary, and required human review points are
  explicitly designed.
- [ ] The workflow preserves raw-to-sanitized provenance expectations.
- [ ] The design states what sanitization does and does not license the repo to
  claim.

> Process criteria:
- [ ] Active-plan docs are updated coherently.
- [ ] Governance checks pass.

---

## Notes

This slice should not quietly drift into implementation. The purpose is to
design a workflow that is specific enough to harden later without repeating the
“looks complete, not operationally credible” failure mode.
