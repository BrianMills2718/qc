# Qualitative Coding Long-Term Execution Plan

Wiki home: http://localhost:8088/index.php/Project_Wiki

**Status:** Active execution spine
**Last updated:** 2026-06-25

This is the design-plan-aligned continuation artifact. It does not replace the
canonical theory/status ledger in `docs/PROJECT_THEORY_AND_GOALS.md` or the
evaluation design in `docs/EVALUATION_HARNESS.md`; it turns them into an
agent-executable sequence.

## Frame

The product goal is a methodology-aware qualitative and mixed-methods research
workbench that can ingest qualitative evidence and produce defensible research
artifacts: codebooks, grounded claims, patterns, negative cases, provisional
abductive explanations, review packets, benchmark packages, and auditable
exports.

The repo's boundary is the qualitative evidence engine. It owns ingestion,
coding, span anchors, segment coverage, code/entity relationships, grounded
claims, descriptive observed patterns, provisional abductive candidates,
negative-case review, adjudication packets, QDA export, and qualitative
evaluation scaffolds. It must not reimplement the process-tracing engine's
likelihood-vector or Bayesian support. Its job is to export traceable
qualitative objects that process-tracing or future mixed-methods workbench
modules can consume.

Success for the software is not a claim of methodological validity. A feature
is implemented when code, tests, and operator-facing docs exist. A rigor claim
is evidenced only by frozen corpora, protocols, benchmark artifacts, or
human-adjudicated packages. SOTA or methodological-validity language remains
blocked by `docs/PROJECT_THEORY_AND_GOALS.md` claim discipline.

## Authority Order

1. `CLAUDE.md` / `AGENTS.md` - operational rules and current commands.
2. `docs/PROJECT_THEORY_AND_GOALS.md` - strategic status, INV-0..11, roadmap,
   and permitted claims.
3. `docs/EVALUATION_HARNESS.md` - benchmark/evaluation proof plan.
4. `docs/LONG_TERM_EXECUTION_PLAN.md` - current long-running execution spine.
5. `docs/plans/ACTIVE_SPRINT.md` - active checkpoint and latest verified
   state.
6. `docs/CONCERNS.md` - live concern register feeding slice selection.

If these conflict on status or claim strength, `docs/PROJECT_THEORY_AND_GOALS.md`
wins.

## Modality Split

This repo is hybrid.

Deductive / plan-first surfaces:

- Pydantic domain schemas and `ProjectState`.
- CLI/API/export contracts.
- Review decision semantics.
- Protocol, package, and preflight validators.
- Benchmark artifact shapes and hash/provenance checks.
- Typed handoff packages to adjacent projects.

Exploratory / ladder surfaces:

- Whether generated codes and patterns are substantively useful.
- Whether abductive candidates help analysts form better explanations.
- Which candidate explanations are worth process tracing.
- Which retrieval/model/prompt settings hold up on frozen corpora.
- Whether GT-inspired outputs satisfy methodologist GT-fidelity rubrics.

For exploratory surfaces, build instruments and readouts first. Do not turn
unknown quality thresholds into fake acceptance criteria. Once a readout
stabilizes, promote it into a typed contract or benchmark gate.

## Risk-Ordered Roadmap

Each slice must finish with verification, adversarial audit, cleanup, concern
triage, commit, and push.

| Order | Slice | Mode | Why it is ordered here | Done when |
|---:|---|---|---|---|
| 1 | Abductive candidate review workflow | Deductive semantics over exploratory content | Provisional explanations now exist but cannot yet be adjudicated as first-class review targets. Without review semantics, downstream handoff would export unchecked hypotheses. | CLI/API/manager review can approve/reject/modify candidates, tests pass, demo packet shows reviewable candidates, and caveats remain provisional. |
| 2 | Process-tracing handoff package | Deductive boundary, exploratory consumer quality | The future workbench boundary needs a typed export before process-tracing agents can align safely. | A versioned package exports patterns, candidate explanations, claims, anchors, scope, and caveats with validation and no Bayesian/process-tracing internals. |
| 3 | Process-tracing consumer review | Exploratory instrument | The QC-side package needs a consumer readout before being treated as a stable seam. | The process-tracing agent can map the deterministic fixture to its own input expectations or returns concrete contract-change requests. |
| 4 | Reviewer-facing abductive UI | Deductive UI contract over stabilized review semantics | Browser UI should follow stable CLI/API semantics, not define them. | UI plan exists first; browser surfaces expose candidate review without changing API semantics; screenshots/manual inspection pass. |
| 5 | Sanitized corpus and adjudication seed | Exploratory evidence instrument | Software surfaces are now visible; next proof requires real or shareable data. | A small corpus, scope record, output packet, and adjudication protocol exist without claiming broad validity. |
| 6 | Populated D3/D7/D8/D9 evaluation lanes | Deductive packages over exploratory quality | Existing protocols need populated results to become evidence. | Frozen inputs, protocols, result packages, scorecards, and caveated reports exist. |

## Next Slices

### Slice #232: Abductive Candidate Review Workflow

Advances: turns provisional abductive outputs into governed review targets.

Vertical scope: `ReviewManager`, CLI/API review-list and decision surfaces,
tests, docs, and deterministic reviewer-demo packet updates. Browser UI is
deferred unless the review semantics force an unavoidable UI change.

De-risks: exporting or presenting unreviewed hypotheses as if they had analyst
authority.

Acceptance: a candidate can be listed, approved, rejected, and modified through
agent-drivable surfaces; review decisions preserve candidate IDs, status,
revision history, and caveats; existing code/claim/relationship review remains
unchanged.

Audit: try to approve all candidates accidentally, mutate causal status beyond
the allowed enum, review a missing candidate ID, and confuse candidate review
with causal/process-tracing proof. Findings go to `docs/CONCERNS.md` or are
fixed before completion.

Cleanup: keep candidate review helpers near existing review code; remove any
duplicate row serializers; update demo and docs only where they reflect tested
behavior.

### Slice #233: Process-Tracing Handoff Package

Advances: gives `~/projects/process_tracing` and a future
`mixed_methods_workbench` a stable QC export seam.

Vertical scope: versioned package schema, validator, CLI export command,
focused tests, artifact docs, and a small fixture package.

De-risks: cross-repo drift and boundary confusion between qualitative evidence
objects and process-tracing causal inference.

Acceptance: package includes project/corpus/scope metadata, observed patterns,
abductive candidates, referenced claims, anchors, caveats, and provenance
hashes. It excludes process-tracing likelihood vectors and Bayesian updates.

Audit: validate missing anchors, stale candidate references, absent scope,
overclaiming language, and package-version mismatch. Findings are fixed or
registered.

Cleanup: put reusable boundary models in the appropriate contracts/adapters
area, avoid one-off JSON assembly, and document the consumer contract.

## Dependency Subplans

### Dependency Subplan: Process-Tracing Consumer Contract

Blocks: full handoff-package promotion beyond a QC-side exporter.

Known stub: QC can export qualitative evidence objects with IDs, anchors,
scope, provenance, caveats, candidate explanations, rival explanations,
observable implications, and evidence gaps.

Unknowns: exact field names and likelihood-vector expectations in
`~/projects/process_tracing`; whether the consumer wants candidate-level,
claim-level, or event-level rows first.

Instrument: inspect `process_tracing` plans and ask that agent to review the
QC package draft after Slice #233 creates a minimal fixture.

Readout: process-tracing agent can map the fixture to its own input contract
without changing QC evidence semantics.

Promotion: update the handoff schema and this plan after consumer review.

### Dependency Subplan: Quality Thresholds For Abductive Candidates

Blocks: any claim that abductive candidates are high quality.

Known stub: candidates are provisional hypotheses with rivals, implications,
evidence gaps, confidence labels, and review status.

Unknowns: which rubric dimensions predict analyst usefulness and downstream
process-tracing value.

Instrument: reviewer packet plus later small adjudication set; optionally a
D8/D9-style rubric result package.

Readout: reviewers can consistently classify candidates as useful, weak, or
unsafe to pursue, and can explain failures using candidate fields.

Promotion: stable rubric dimensions become protocol/package fields; unstable
dimensions remain exploratory.

## Concern Cadence

At every slice boundary:

1. Read `docs/CONCERNS.md`.
2. Close, mitigate, or defer stale entries.
3. Add any new uncertainty or audit finding before moving on.
4. Let the highest-severity open concern influence the next slice unless the
   active plan gives a stronger reason.

Do not leave concerns only in chat. Do not proceed with a stale active sprint
tracker.

## Stop Conditions

Continue without stopping after green tests, completed commits, tool failures,
or uncertainty that can be logged and safely defaulted.

Stop only for:

- irreversible shared-state actions such as force-pushes, destructive data
  changes, or production mutations;
- a genuine architectural decision not pre-made here and not safely defaultable;
- three failed attempts at the same problem without new information, after
  logging the finding and moving to the next highest-value nonblocked task.

## Current Position

The latest completed implementation slice is Plan #233, process-tracing
handoff package. The next slice is process-tracing consumer review of the
deterministic handoff fixture, unless concern triage changes the risk order.
