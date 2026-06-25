# Plan #231: Design-Plan Long-Term Execution Spine

## Outcome

Completed 2026-06-25. Added
`docs/LONG_TERM_EXECUTION_PLAN.md` as the design-plan-aligned execution spine
for continued qualitative-coding work. The spine names the frame, authority
order, modality split, risk-ordered roadmap, next two slices, dependency
subplans, concern cadence, and canonical stop conditions. It points Plan #232
at abductive candidate review workflow and Plan #233 at a typed
process-tracing handoff package. Updated methodology, artifact, concern, wiki,
plan-index, and active-sprint docs. This is planning/governance work only, not
methodological-validity evidence, causal proof, process-tracing evidence, or
SOTA evidence.

Verification:

- `make docs-check` — passed.
- `git diff --check` — passed.

**Status:** Complete
**Type:** design
**Priority:** High
**Blocked By:** None
**Blocks:** Plan #232, continued overnight execution

---

## Gap

**Current:** The repo has the design-plan ingredients: goal framing in
`CLAUDE.md` and `docs/PROJECT_THEORY_AND_GOALS.md`, a modality split in
`docs/METHODOLOGY.md`, a concern register in `docs/CONCERNS.md`, and an active
sprint tracker in `docs/plans/ACTIVE_SPRINT.md`. The problem is operational:
the long-term execution spine is scattered across several files, and the next
1-2 slices after the abductive demo packet are not stated in one place.

**Target:** Add a concise, canonical long-term execution spine that maps the
project to the `/design-plan` outputs: frame, modality split, artifact
authority order, risk-ordered slice roadmap, next 1-2 unambiguous slices,
dependency subplans, concern-register cadence, and stop conditions. Update the
artifact register, methodology spine, concern register, active sprint tracker,
and wiki manifest so future agents can proceed without conversation context.

**Why:** Brian wants the repo to run continuously until a real blocker. That
only works if the long-term plan pre-makes the next decisions, preserves claim
discipline, and records the steering loop outside chat.

---

## References Reviewed

- `/home/brian/projects/.agents/skills/design-plan/SKILL.md` - required output:
  frame, modality split, design artifacts, risk-ordered slice roadmap, concern
  register.
- `/home/brian/projects/.agents/skills/design-plan/references/slicing.md` -
  slice spec, plan-hygiene preflight, concern-register cadence.
- `/home/brian/projects/.agents/skills/design-plan/references/exploratory.md` -
  hybrid/exploratory rule: instrument open surfaces and promote stable readouts
  into contracts.
- `CLAUDE.md` - product philosophy and future workbench boundary with
  `process_tracing`.
- `docs/PROJECT_THEORY_AND_GOALS.md` - canonical status ledger, INV-0..11
  roadmap, prior-art caveats, and claim discipline.
- `docs/METHODOLOGY.md` - current methodology spine and modality split.
- `docs/CONCERNS.md` - current concern register.
- `docs/ARTIFACTS.md` - artifact register.
- `docs/plans/ACTIVE_SPRINT.md` - current long-running sprint mission and
  latest completed checkpoint.
- Memory context:
  `agent-memory recall 'active decisions long term qualitative coding design plan abductive process tracing workbench' --project qualitative_coding`
  and
  `agent-memory recall 'abductive process tracing mixed methods workbench qualitative coding' --project qualitative_coding`
  returned two broad historical task-outcome summaries and no concrete active
  architecture decisions that override the repo docs.

---

## Research Basis For This Slice

No additional external research is needed. This is repo-local governance and
planning alignment over already-read project artifacts and the design-plan
skill.

---

## Capabilities

No callable runtime capabilities are created or modified. This is a planning
and documentation slice.

### Capability Validation

Skipped: no runtime boundary or tool contract changes.

---

## Files Affected

- `docs/LONG_TERM_EXECUTION_PLAN.md` - new canonical long-term execution spine.
- `docs/METHODOLOGY.md` - link the execution spine from the methodology
  artifact and clarify how it applies the modality split.
- `docs/ARTIFACTS.md` - add the new plan to the artifact register.
- `docs/CONCERNS.md` - triage stale concerns and add concerns for abductive
  review/handoff.
- `docs/wiki_manifest.yaml` - publish the new governance artifact.
- `docs/plans/ACTIVE_SPRINT.md` - make Plan #231 active, then close it after
  verification.
- `docs/plans/CLAUDE.md` - list Plan #231 as active, then completed.
- `docs/plans/completed/DESIGN_PLAN_LONG_TERM_EXECUTION_SPINE.md` - final
  completed record after verification.

---

## Plan

### Steps

1. Create the active plan and register it in the plan index/sprint tracker.
2. Commit and push the planned slice after docs checks pass.
3. Add `docs/LONG_TERM_EXECUTION_PLAN.md` with the design-plan mapping:
   frame, constraints, authority order, modality split, risk-ordered slices,
   next 1-2 slices, dependency subplans, concern cadence, and stop conditions.
4. Update methodology, artifact, concern, wiki, and active-sprint references.
5. Run docs checks and whitespace checks.
6. Move the plan to completed, update the plan index/sprint tracker, rerun
   docs checks, commit, and push.
7. Continue to the next unambiguous slice from the execution spine unless a
   canonical stop condition is reached.

---

## Required Tests

### New Tests (TDD)

No new code tests are required for a docs-only plan.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `make docs-check` | Verify plan/doc governance and generated mirror checks. |
| `git diff --check` | Whitespace hygiene. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] A canonical long-term execution plan exists and explicitly maps to the
  design-plan outputs.
- [x] The plan names the next 1-2 slices unambiguously with acceptance/audit
  criteria.
- [x] Open exploratory surfaces are framed as instruments/readouts, not fake
  precision.
- [x] Dependency subplans cover unresolved process-tracing/workbench seams.
- [x] The concern register is triaged and includes abductive review/handoff
  risks.
- [x] Artifact register and wiki manifest point to the new execution spine.

> Process criteria:
- [x] `make docs-check` passes.
- [x] `git diff --check` passes.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should Plan #232 implement browser UI review for abductive candidates or
  CLI/API review first? Status: RESOLVED for this planning slice. The next
  unambiguous slice should be CLI/API review first; browser UI is deferred
  until the review semantics are stable and, if needed, a UI-planning slice can
  handle the non-trivial interface.
- [ ] Should the process-tracing handoff contract be implemented inside this
  repo or the future mixed-methods workbench? Status: RESOLVED as a boundary
  decision. This repo should export qualitative patterns, claims, anchors, and
  provisional abductive candidates through typed contracts. Process-tracing
  likelihood/Bayesian support remains outside this repo.

---

## Notes

This slice is about execution reliability, not new methodology evidence. It
must not strengthen the repo's claims about grounded theory, causal proof,
methodological validity, or SOTA.
