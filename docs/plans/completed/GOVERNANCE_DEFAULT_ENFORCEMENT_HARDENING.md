# Plan #236: Governance Default Enforcement Hardening

**Status:** Completed
**Type:** implementation
**Priority:** High
**Blocked By:** #235
**Blocks:** required-reading default enforcement, plan-validation default enforcement, selective hard-coupling adoption

---

## Outcome

Completed a scoped default-governance hardening slice without broadening the
gate into noisy or misleading failures.

Implemented:

- default `docs-check` now validates active plan files by routing
  `scripts/sync_plan_status.py --check --validate-active` through the canonical
  plan validator;
- the repo-local planning docs now describe that default gate behavior exactly;
  and
- required-reading enforcement remains opt-in/session-based for now, with that
  decision documented explicitly instead of being left ambiguous.

Did not implement:

- blanket required-reading enforcement in the default path; and
- hard-coupling promotion.

Those remain separate concerns because they depend on per-session read logs or
additional signal/noise decisions that were not necessary for this slice.

## Verification

- `python scripts/check_markdown_links.py`
- `python scripts/check_doc_coupling.py --validate-config`
- `python scripts/sync_plan_status.py --check --validate-active`
- `python scripts/meta/check_agents_sync.py --check`
- `python -m pytest tests/ -m "not live_llm" -x -q`
- `python -m ruff check .`
- `git diff --check`

---

## Gap

**Current:** The repo now documents the intended governance workflow and has a
cleaner explanation of canonical versus compatibility entrypoints, but the
default `make docs-check` path still enforces only a subset of the available
governance tools. Required-reading enforcement and full plan validation remain
opt-in.

**Target:** Harden the default governance path in a scoped, non-noisy way:
introduce required-reading enforcement and plan validation where they add real
signal, preserve truthful greens, and selectively evaluate whether any soft
couplings should become hard checks.

**Why:** The current live risk is still false-green governance: default checks
can pass while skipping some of the repo's highest-value discipline
mechanisms. After Plan #235 review/cleanup/doc/planning work, the next step is
to tighten enforcement deliberately rather than implicitly.

---

## References Reviewed

- `CLAUDE.md` - operational authority and now-explicit governance workflow
  order.
- `docs/plans/CLAUDE.md` - plan policy, trivial exemption, and enforcement
  notes.
- `docs/plans/completed/GOVERNANCE_REVIEW_CLEANUP_DOC_ALIGNMENT.md` - reviewed cleanup
  findings, carried-forward concerns, and prerequisite sequencing.
- `Makefile` - current `docs-check` and `check` path.
- `scripts/check_required_reading.py` and `scripts/meta/file_context.py` -
  required-reading enforcement surface.
- `scripts/meta/validate_plan.py` and
  `enforced_planning/plan_validation.py` - plan validation requirements.
- `scripts/check_doc_coupling.py`,
  `scripts/meta/check_doc_coupling.py`, and `scripts/relationships.yaml` -
  coupling behavior, current soft policy, and hardening candidates.
- `scripts/sync_plan_status.py` - completed-plan ledger enforcement already in
  the default path.
- User instruction on 2026-06-25 - governance work must document concerns in
  plans rather than leaving them only in chat.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

No new end-user capability is planned. This slice changes default governance
enforcement behavior in local developer workflows and CI-equivalent gates.

---

## Files Affected

- `docs/plans/GOVERNANCE_DEFAULT_ENFORCEMENT_HARDENING.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `Makefile` (modify)
- `scripts/relationships.yaml` (potential modify)
- `scripts/check_required_reading.py` (potential modify if CLI behavior needs clarification)
- `scripts/meta/file_context.py` (potential modify if gate scoping needs support)
- `scripts/meta/validate_plan.py` (potential modify if gate scoping needs support)
- `tests/` (potential add/modify if governance gate behavior changes)

---

## Plan

### Steps

1. Decide the minimum-signal default enforcement set to add to `docs-check`.
2. Scope required-reading enforcement so it applies to governance-sensitive or
   plan-bearing changes without becoming a noisy blanket requirement.
3. Scope plan validation so active/changed plan files are checked by default.
4. Revisit current soft couplings and nominate only a very small number for
   candidate hardening if they are high-value and low-noise.
5. Update docs to reflect the new default gate behavior exactly.
6. Add or update tests for any modified governance-script behavior.

---

## Required Tests

### New Tests (TDD)

Add focused tests only if new behavior is introduced in governance helpers or
Make-path wrappers.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python scripts/meta/validate_plan.py --plan-file docs/plans/GOVERNANCE_DEFAULT_ENFORCEMENT_HARDENING.md` | The follow-on plan itself must validate. |
| `make docs-check` | The hardened governance path must stay green once updated. |
| `git diff --check` | Patch hygiene. |
| `make check` | Required if behavior changes in scripts or enforcement paths. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Default governance enforcement is stricter in a documented, scoped way.
- [x] Required-reading and/or plan-validation default behavior is introduced
  only where it adds signal.
- [x] In this slice, active-plan validation is added to the default path while
  required-reading remains opt-in because it depends on per-session read logs
  rather than a repo-stable CI artifact.
- [x] Any hard-coupling promotion is explicit, minimal, and justified.
  Answer: none were promoted in this slice.
- [x] Canonical docs describe the new default gate behavior exactly.

> Process criteria:
- [x] This plan validates before implementation.
- [x] `make docs-check` passes after the changes.
- [x] `git diff --check` passes.
- [x] `make check` passes if script behavior changes.

---

## Open Questions

- [x] Which specific paths should trigger required-reading by default? —
  Status: RESOLVED FOR THIS SLICE | Answer: none in the default path yet.
  Required-reading remains opt-in until a repo-stable, low-noise artifact
  replaces per-session read logs.
- [x] Should any current soft couplings be hardened in the same slice, or
  deferred? — Status: RESOLVED FOR THIS SLICE | Answer: deferred. Plan
  validation added enough signal for one increment without coupling hardening.

---

## Notes

This slice deliberately chose the lowest-noise hardening path. It improved the
truthfulness of the default green check without making session-local read
tracking or hard-coupling policy a hidden prerequisite for passing docs gates.
