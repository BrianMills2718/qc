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

For default-path visible analytic surfaces, there is now a middle bar between
"implemented" and "methodologically validated": operational verification. A
surface can be structurally implemented and still fail operational credibility
if its producer is absent or weak on the default path.

## Authority Order

1. `CLAUDE.md` / `AGENTS.md` - operational rules and current commands.
2. `docs/PROJECT_THEORY_AND_GOALS.md` - strategic status, INV-0..11, roadmap,
   and permitted claims.
3. `docs/EVALUATION_HARNESS.md` - benchmark/evaluation proof plan.
4. `docs/LONG_TERM_EXECUTION_PLAN.md` - current long-running execution spine.
5. `docs/CAPABILITY_DEPENDENCY_GRAPH.md` - capability dependencies and
   success criteria across QC, grounded-research, process tracing, and the
   future mixed-methods workbench.
6. `docs/plans/ACTIVE_SPRINT.md` - active checkpoint and latest verified
   state.
7. `docs/CONCERNS.md` - live concern register feeding slice selection.

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
| 3 | Process-tracing consumer review | Exploratory instrument | The QC-side package needed a consumer readout before being treated as a stable QC fixture. | Complete on 2026-06-25: process-tracing review accepted the deterministic fixture as QC-side adapter input with no QC schema changes, while keeping runnable PT source-packet/research-design fields outside QC. |
| 4 | Reviewer-facing abductive UI | Deductive UI contract over stabilized review semantics | Browser UI should follow stable CLI/API semantics, not define them. | UI plan exists first; browser surfaces expose candidate review without changing API semantics; screenshots/manual inspection pass. |
| 5 | Local Africa corpus and adjudication seed | Exploratory evidence instrument | Software surfaces are now visible; next proof requires real data handled with explicit scope and caveats. | A small local corpus, scope record, output packet, and adjudication protocol exist without claiming broad validity or publication readiness. |
| 6 | Populated D3/D7/D8/D9 evaluation lanes | Deductive packages over exploratory quality | Existing protocols need populated results to become evidence. | Frozen inputs, protocols, result packages, scorecards, and caveated reports exist. |

## Next Slices

### Slice #234: Local Africa Corpus And Adjudication Seed

Advances: turns the existing software/provenance surfaces into a small
reviewable local evidence instrument without claiming expert evidence before
labels exist.

Vertical scope: corpus policy, scope record, isolated project store, pipeline
output packet, audit manifest, unlabeled adjudication sample, pre-registered
adjudication protocol, and protocol/sample preflight. If human labels are
supplied, include response validation, response preflight, D3/D7 import, strict
Phase 0 package writing, and package replay. Prefer explicit isolated-store
flags for project and Make command paths.

De-risks: building more abductive UI or workbench integration on top of
synthetic-only software demos.

Acceptance: a reviewable local corpus seed and manual-ready adjudication packet
exist with explicit caveats. Any imported D3/D7 labels come only from explicit
human review or from an explicitly synthetic smoke run. No methodological-
validity, SOTA, full-GT, or causal/process-tracing claims are made.

Audit: check corpus license/provenance, scope overreach, hidden default project
store mutation, stale sample/protocol hashes, accidental agent-generated labels
presented as expert review, and Phase 0 package replay drift.

Cleanup: keep artifacts in a repo-local benchmark/evidence directory with
hashes and README caveats; update only the active docs needed to describe the
new evidence status.

### Completed Slice #237: Default-Path Operational Credibility Policy

Complete on 2026-06-25. This slice turned the newly exposed graph/review
default-path gap into a repo-enforced governance rule rather than a one-off
chat lesson.

Delivered: canonical docs now distinguish structural completion, operational
verification, and methodological validation; a machine-readable default-path
surface contract registry exists; active plans must declare operational-
validation burden; and the docs gate validates the new policy while making
default-path producer gaps explicit instead of leaving them only in chat.

### Completed Slice #238: Thematic Graph Relationship Hardening

Complete on 2026-06-25. This slice turned the explicit default-path graph
warning into product remediation.

Delivered: the default thematic relationship stage now emits first-class code
relationships; graph API/UI empty states are truthful; linked-only entity
rendering reduces misleading sparsity; long relationship-evidence paraphrases
no longer trigger pathological fuzzy grounding; and real-run replay on the
3-document local seed produced 6 code relationships plus a denser 15-node/8-edge
entity graph.

## Dependency Subplans

### Dependency Subplan: Process-Tracing Consumer Contract

Blocks: full workbench bridge implementation, but no longer blocks treating the current package as an acceptable QC-side fixture.

Known stub: QC can export qualitative evidence objects with IDs, anchors,
scope, provenance, caveats, candidate explanations, rival explanations,
observable implications, and evidence gaps.

Resolved readout on 2026-06-25: process-tracing review found the package
acceptable as a QC-side fixture/adaptor input. It can map `corpus_scope`,
documents, anchors, observed patterns, abductive candidates, and analytic claims
without importing `pt.schemas` into QC and without adding likelihood/posterior
or comparative-support fields.

Remaining unknowns: exact PT/workbench adapter shape and how a separate
research-design/source-packet overlay will be supplied for runnable PT analysis.

Instrument: complete for the QC-side fixture. The next instrument belongs to
the future PT/workbench adapter lane.

Readout: accepted with caveat. The package is not a complete runnable PT input
because it intentionally omits `research_question`, focal window, outcome,
source candidates, known gaps, and pre-specified tests.

Promotion: no QC schema update required now. Future work should define the
PT/workbench adapter or overlay contract outside QC.

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
handoff package. Process-tracing consumer review of the deterministic fixture
completed on 2026-06-25 with no requested QC schema changes.

Plans #234, #237, and #238 are now complete. The repo has:
- a fresh post-fix local restricted corpus packet from Plan #234;
- a repo-enforced default-path operational-credibility policy from Plan #237;
- and a validated thematic graph remediation from Plan #238.

The current nonblocked next slice is the deferred sanitizer/public-corpus work.
Populated D3/D7 evidence remains blocked on explicit human labels. The
recommended order is now: reviewed sanitizer/public-corpus workflow design,
then populated D3/D7 evidence when labels exist, then more abductive
UI/workbench integration.
