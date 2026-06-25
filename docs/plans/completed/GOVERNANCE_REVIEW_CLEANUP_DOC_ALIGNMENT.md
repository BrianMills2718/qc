# Plan #235: Governance Review Cleanup Doc Alignment

**Status:** Completed
**Type:** design
**Priority:** High
**Blocked By:** None
**Blocks:** governance enforcement tightening, docs-check hardening, required-reading default enforcement, plan-validation default enforcement

---

## Outcome

Completed the governance review/cleanup/documentation/planning alignment slice
before any enforcement hardening work. This slice:

- reviewed the governance surface and recorded concrete mismatches between
  policy, tracker state, and default enforcement;
- aligned canonical docs so both `CLAUDE.md` and `docs/plans/CLAUDE.md` now
  state the repo-local governance workflow order
  `review -> cleanup -> documentation updates -> planning updates -> implementation`;
- reconciled `docs/plans/ACTIVE_SPRINT.md` so the active-slice story is no
  longer contradictory;
- clarified the wrapper layer and current soft-coupling policy without changing
  enforcement behavior; and
- carried the unresolved concerns forward into a downstream implementation plan,
  `docs/plans/GOVERNANCE_DEFAULT_ENFORCEMENT_HARDENING.md` (Plan #236), so they
  are tracked in repo artifacts rather than only in chat.

This slice intentionally did not harden default checks. It established the
governed preconditions for doing that next.

## Verification

- `python scripts/meta/validate_plan.py --plan-file docs/plans/completed/GOVERNANCE_REVIEW_CLEANUP_DOC_ALIGNMENT.md`
- `python scripts/meta/validate_plan.py --plan-file docs/plans/GOVERNANCE_DEFAULT_ENFORCEMENT_HARDENING.md`
- `python scripts/check_markdown_links.py`
- `python scripts/check_doc_coupling.py --validate-config`
- `python scripts/sync_plan_status.py --check`
- `python scripts/meta/check_agents_sync.py --check`
- `git diff --check`

---

## Gap

**Current:** The repo has a serious governance surface: canonical authority
docs, claim-discipline rules, a machine-readable relationships graph, plan
tracking, doc-coupling checks, required-reading helpers, and plan validators.
But the workflow ordering the user wants is not clearly codified, and some of
the strongest governance tools are available without being part of the default
`make docs-check` path. The policy surface is therefore stronger than the
default enforcement surface.

**Target:** Review the governance system first, then clean it up, then align
canonical documentation and planning artifacts to the actual workflow ordering:
review -> cleanup -> documentation updates -> planning updates -> implementation.
Only after that alignment should enforcement be tightened.

**Why:** This repo's central risk is false-green governance: documentation,
planning, and implementation drifting apart while checks still pass. Tightening
enforcement before cleaning and documenting the policy would make the process
stricter without making it clearer.

---

## References Reviewed

- `CLAUDE.md` - canonical operational guidance, authority order, and command
  surface.
- `docs/PROJECT_THEORY_AND_GOALS.md` - strategic authority, claim discipline,
  and invariant/status framing.
- `docs/EVALUATION_HARNESS.md` - evaluation/governance caveat model.
- `docs/plans/CLAUDE.md` - plan index, trivial-change rule, and plan lifecycle.
- `docs/plans/TEMPLATE.md` - required plan structure.
- `scripts/relationships.yaml` - required-reading defaults and doc-code
  coupling graph.
- `Makefile` - actual `docs-check` and `check` enforcement path.
- `scripts/check_doc_coupling.py` and `scripts/meta/check_doc_coupling.py` -
  doc-coupling enforcement surface and wrapper structure.
- `scripts/check_required_reading.py` and `scripts/meta/file_context.py` -
  required-reading enforcement surface and repo-local wrapper.
- `scripts/meta/validate_plan.py` and
  `enforced_planning/plan_validation.py` - plan validator requirements and gap
  model.
- `scripts/sync_plan_status.py` and `scripts/meta/sync_plan_status.py` -
  repo-local plan-index consistency model and legacy compatibility wrapper.
- User instruction on 2026-06-25 - governance work must follow the order:
  review, cleanup, documentation updates, planning updates, implementation.

---

## Research Basis For This Slice

No additional research beyond References Reviewed.

---

## Capabilities

No new callable capability is planned in this slice. This plan is governance
review/alignment work over existing repo policy and enforcement surfaces.

---

## Files Affected

- `docs/plans/GOVERNANCE_REVIEW_CLEANUP_DOC_ALIGNMENT.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)
- `CLAUDE.md` (modify)
- `Makefile` (potential modify after review/cleanup/docs alignment)
- `scripts/relationships.yaml` (potential modify after review/cleanup/docs alignment)
- `scripts/check_required_reading.py` (potential modify after review/cleanup/docs alignment)
- `scripts/check_doc_coupling.py` (potential modify after review/cleanup/docs alignment)
- `scripts/meta/validate_plan.py` (potential modify after review/cleanup/docs alignment)
- `scripts/sync_plan_status.py` (potential modify after review/cleanup/docs alignment)

---

## Plan

### Steps

1. Review the governance surface end-to-end:
   authority docs, plan index, relationship graph, plan validator,
   required-reading helper, doc-coupling checker, plan-status checker, and
   `docs-check` wiring.
2. Write down concrete mismatches between:
   documented policy, desired workflow ordering, and default enforcement.
3. Cleanup the governance surface before adding stricter checks:
   identify redundant wrappers, stale instructions, vacuous passes, or
   duplicated authority explanations.
4. Update canonical docs so they explicitly state the required workflow order:
   review -> cleanup -> documentation -> planning -> implementation.
5. Update planning docs/index/sprint tracking so the current governance work is
   recorded honestly and future enforcement work is clearly downstream of this
   alignment slice.
6. Only after steps 1-5, prepare the follow-on implementation plan that
   hardens enforcement (`docs-check`, required reading, plan validation, and
   selected hard couplings).

---

## Required Tests

### New Tests (TDD)

No new automated tests are required for the planning-only slice. If later
cleanup or implementation changes behavior in governance scripts or Make
targets, add tests in that follow-on slice.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python scripts/sync_plan_status.py --check` | Completed-plan ledger must stay internally consistent. |
| `python scripts/meta/validate_plan.py --plan-file docs/plans/GOVERNANCE_REVIEW_CLEANUP_DOC_ALIGNMENT.md` | The new plan must satisfy the repo's plan validator. |
| `make docs-check` | Planning/documentation changes must pass the current docs gate. |
| `git diff --check` | Prevent whitespace/patch hygiene regressions. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] The governance workflow ordering is captured explicitly in canonical docs.
- [x] Review findings distinguish policy, cleanup, docs, planning, and later
  implementation work.
- [x] Cleanup targets are identified before any enforcement-tightening change is
  proposed as active implementation work.
- [x] Planning artifacts reflect that governance alignment is a prerequisite to
  enforcement hardening.

> Process criteria:
- [x] `python scripts/meta/validate_plan.py --plan-file docs/plans/GOVERNANCE_REVIEW_CLEANUP_DOC_ALIGNMENT.md` passes.
- [x] `python scripts/sync_plan_status.py --check` passes.
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.

---

## Review Findings

### Policy / tracker mismatches found

1. `docs/plans/ACTIVE_SPRINT.md` previously told two different stories about
   the active slice: the top section centered Plan #234 while an appended note
   introduced Plan #235 as the governance-alignment slice. This was a genuine
   tracker contradiction and created ambiguity about what "active" meant.
2. `docs/plans/CLAUDE.md` explained plan creation/completion and the trivial
   exemption, but did not codify the repo-local governance workflow order
   `review -> cleanup -> documentation updates -> planning updates ->
   implementation`.
3. The canonical planning doc also lacked a practical inverse of the trivial
   exemption: there was no explicit note that governance checks, pipeline
   behavior, export/audit behavior, CLI/API/MCP surfaces, and claim-bearing
   doc/status changes should assume a plan is required.
4. `Makefile` `docs-check` enforced markdown links, doc-coupling config,
   completed-plan-table consistency, and AGENTS sync, but did not run the
   available required-reading or full plan-validation checks by default. This
   confirmed the central review hypothesis: policy surface > default enforced
   surface.

### Documentation/planning alignment completed in the review slice

1. `CLAUDE.md` now states the governance workflow order.
2. `docs/plans/CLAUDE.md` now states the same order, clarifies the narrow
   trivial exemption, and documents what `make docs-check` currently enforces
   versus which governance tools remain opt-in.
3. `docs/plans/ACTIVE_SPRINT.md` now treats Plan #235 as the active governance
   slice and Plan #234 as the next execution-roadmap slice, removing the prior
   active-slice contradiction.

### Cleanup targets identified for the next phase

1. Review the compatibility-wrapper layer
   (`scripts/check_doc_coupling.py`, `scripts/check_required_reading.py`,
   `scripts/meta/sync_plan_status.py`) and decide which wrappers are still
   justified versus redundant.
2. Decide whether any current soft couplings in `scripts/relationships.yaml`
   should remain intentionally soft after cleanup, or should later become
   candidate hard checks.
3. Decide how to introduce required-reading enforcement and full plan
   validation into the default path without creating noisy or misleading
   failures.

### Remaining concerns carried forward explicitly

1. The wrapper layer is now better explained, but still increases governance
   indirection. This is acceptable only if the repo deliberately values stable
   legacy entrypoints more than a smaller surface area.
2. The largest live governance gap remains default enforcement scope:
   required-reading enforcement and full plan validation exist, but are not yet
   part of `make docs-check`.
3. Soft couplings are now documented as intentional for the current phase, but
   the repo still needs an explicit later decision about which of them should
   stay advisory and which should become candidate hard checks.

---

## Open Questions

- [x] Should workflow ordering live only in `CLAUDE.md`, or also in
  `docs/plans/CLAUDE.md`? — Status: RESOLVED | Answer: both. The rule now lives
  in operational and planning entrypoints so it is visible in both
  implementation and planning contexts.
- [ ] Which current soft couplings are intentionally soft versus merely not yet
  hardened? — Status: OPEN | Why it matters: later enforcement tightening
  should reflect deliberate policy, not inertia.
- [ ] Is the wrapper layer a permanent compatibility surface or transitional
  cleanup debt? — Status: OPEN | Why it matters: this determines whether later
  governance work should simplify entrypoints or merely document them better.

---

## Notes

This plan intentionally sequenced work rather than hardening enforcement in the
same slice. That matched the repo-specific governance requirement from the
user: review, cleanup, documentation, and planning updates came before any
implementation change to the checks themselves.
