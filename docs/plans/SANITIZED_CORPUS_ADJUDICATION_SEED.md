# Plan #234: Local Africa Corpus And Adjudication Seed

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** populated D3/D7 evidence lanes, grounded-research legitimacy, mixed-methods workbench evidence bridge, abductive UI/product expansion

---

## Gap

**Current:** QC has protocol, validation, scorecard, package, review, and
handoff surfaces, plus deterministic synthetic reviewer-demo packets. Those
prove software pathways and provenance checks, but they do not provide a
shareable corpus, adjudication seed, populated human labels, grounded-theory
fidelity evidence, or SOTA evidence.

**Target:** Create the first small, local QC evidence instrument: a discovered
Africa transcript subset, explicit provenance/inventory record, explicit scope
record, pipeline output packet, unlabeled adjudication sample, pre-registered
adjudication protocol, and preflighted handoff point for human labeling.
Sanitization/de-identification tooling is deferred and should not block this
local Plan #234 slice. If labels are supplied by Brian or another qualified
reviewer, import them into D3/D7 gold packages and write a strict Phase 0
package manifest. If labels are not supplied, stop at a manual-ready
adjudication packet and do not claim expert evidence.

**Why:** The capability graph says the next risk is not more abductive UI; it
is whether the qualitative evidence engine can produce and govern reviewable
data on a corpus that can be inspected, shared, and later scored. This slice
keeps grounded research and QC foundations ahead of mixed-methods/process-
tracing integration.

---

## References Reviewed

- `docs/CAPABILITY_DEPENDENCY_GRAPH.md` - dependency graph and sequencing
  recommendation for QC, grounded research, and future mixed-methods work.
- `docs/capability_dependency_graph.yaml` - machine-readable capability graph.
- `docs/LOCAL_DATA_INVENTORY.md` - metadata-only inventory of ignored local
  candidate Africa transcript materials.
- `docs/LONG_TERM_EXECUTION_PLAN.md` - execution spine and current-position
  recommendation.
- `docs/EVALUATION_HARNESS.md` - adjudication protocol, sample, response,
  import, D3/D7, and Phase 0 package surfaces.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-3/INV-10 status and claim
  discipline caveats.
- `docs/plans/ACTIVE_SPRINT.md` - current long-running sprint tracker.
- `docs/plans/TEMPLATE.md` - required plan structure.
- User note on 2026-06-25 - Brian confirmed the located Africa-related
  transcripts are the intended starting point and clarified that sanitization
  should be documented as a deferred feature, not handled now.
- `Makefile` - adjudication, D3/D7, Phase 0, and publish-preflight targets.
- `scripts/validate_adjudication_protocol.py` - adjudication protocol
  validator.
- `scripts/preflight_adjudication_protocol_sample.py` - protocol/sample
  preflight.
- `scripts/validate_adjudication_responses.py` - completed-response validator.
- `scripts/preflight_adjudication_responses.py` - response provenance
  preflight.
- `scripts/import_adjudication_responses.py` - D3/D7 package import from
  completed responses.
- `scripts/write_phase0_adjudication_package.py` - strict Phase 0 adjudication
  manifest writer.
- `scripts/bench_phase0.py` and `scripts/run_phase0_benchmark_package.py` -
  canonical Phase 0 scoring/package replay.
- `scripts/build_reviewer_demo.py` - synthetic packet precedent and caveat
  style.
- Memory context:
  `agent-memory recall 'sanitized corpus adjudication seed qualitative coding next slice capability dependency graph' --project qualitative_coding`
  returned two broad historical task summaries and no active decision
  overriding repo docs.

---

## Research Basis For This Slice

No external web research was used to write this plan. Corpus selection itself
is a plan step. If this slice uses an external public corpus instead of
Brian-provided local material or hand-authored software-smoke material, the
implementation pass must research and record the corpus license, provenance,
and fitness before ingestion.

---

## Capabilities

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Local corpus provenance + inventory | candidate documents + source metadata | metadata-only inventory + corpus manifest | QC implementation slice | QC ingestion, Brian, evaluators | free |
| Local Africa corpus seed package | source documents, scope metadata, corpus policy | corpus manifest + isolated project store | QC implementation slice | Brian, QC evaluators, future workbench | free unless pipeline is run live |
| Adjudication seed packet | project state + sampling policy | schema_version=1 adjudication sample + protocol | QC adjudication surfaces | Brian/human adjudicators, D3/D7 import | free |
| Optional D3/D7 import from labels | completed response package + protocol/sample | D3 gold package, D7 gold package, Phase 0 manifest | QC import/package surfaces | Phase 0 scorecard | free |

### Capability Validation

- [ ] Corpus policy records that this is a local ignored Africa-transcript
  subset unless a later manifest says otherwise.
- [ ] Candidate Africa-related transcripts are inventoried without committing
  raw contents.
- [ ] Long-run sanitizer mechanism is captured as a deferred feature, not a
  current Plan #234 blocker.
- [ ] Scope metadata states what population or phenomenon may and may not be
  inferred from the corpus.
- [ ] Adjudication protocol validates before any labeling.
- [ ] Protocol/sample preflight passes before responses are accepted.
- [ ] Completed responses are imported only after explicit human labeling or
  an explicitly caveated synthetic smoke run.

---

## Files Affected

Planned documentation and artifact paths:

- `docs/plans/SANITIZED_CORPUS_ADJUDICATION_SEED.md` - this plan.
- `docs/plans/CLAUDE.md` - active plan index.
- `docs/plans/ACTIVE_SPRINT.md` - active sprint checkpoint.
- `docs/LONG_TERM_EXECUTION_PLAN.md` - execution-spine current position.
- `docs/benchmarks/` or another repo-local artifact directory - future corpus,
  protocol, sample, response, and package artifacts if implementation proceeds.

Potential implementation paths if gaps are found:

- `qc_cli.py` and `Makefile` only if the existing adjudication surfaces need
  explicit `PROJECTS_DIR` parity for portable corpus packages.
- `tests/` only if a tooling gap requires code changes.

---

## Plan

### Steps

1. Choose corpus policy:
   - use the located local Africa-related transcripts as the starting point;
   - treat the current slice as local evidence/workflow work, not a public
     sanitized or de-identified corpus;
   - defer public/shareable corpus and sanitization decisions;
   - use hand-authored synthetic material only for software-smoke artifacts and
     label it as non-evidentiary.
2. Locate candidate materials without committing raw files. If the old
   Africa-related transcripts are found, inventory only filenames, location,
   document count, rough domain, and git-ignore status in tracked metadata
   docs. Do not commit raw contents.
3. Define the scope record before ingestion: phenomenon, source policy,
   inclusion/exclusion boundaries, population-generalization caveats, and
   license/provenance.
4. Create an isolated repo-local project store for the seed so no default
   project state is mutated.
5. Ingest and run the QC pipeline on the seed with the smallest defensible
   settings for reviewable output. Record trace IDs, model/config metadata, and
   D10 observability if live LLM calls are made.
6. Export the project report and an audit manifest for the output artifacts.
7. Export an unlabeled adjudication sample over applications, claims, negative
   cases, and relationships.
8. Write and validate a pre-registered adjudication protocol for the sample.
9. Run protocol/sample preflight and fix any provenance or sample mismatch.
10. If human labels are supplied, validate completed responses, run response
   preflight, import D3/D7 packages, write a strict Phase 0 adjudication
   package, and run `bench-package`.
11. If labels are not supplied, stop at the manual-ready packet and record that
    no expert evidence exists yet.
12. Add a deferred follow-up plan for an agent-drivable sanitization mechanism.
13. Update claim-discipline docs and active sprint status with exact caveats.

---

## Required Tests

### New Tests (TDD)

No new tests are required for a docs/artifact-only first pass. Add tests if
implementation uncovers a missing CLI/Make/project-store capability.

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `make validate-adjudication-protocol PROTOCOL=<protocol.json>` | Protocol is structurally valid before labeling. |
| `make adjudication-protocol-preflight PROTOCOL=<protocol.json> SAMPLE=<sample.json>` | Protocol and sample hashes/IDs match before labeling. |
| `make validate-adjudication-responses PACKAGE=<responses.json>` | Required only if completed responses are supplied. |
| `make adjudication-response-preflight PROTOCOL=<protocol.json> SAMPLE=<sample.json> RESPONSES=<responses.json>` | Required before importing completed labels. |
| `make import-adjudication-responses ...` | Required only for real or explicitly synthetic completed responses. |
| `make write-phase0-adjudication-package ...` | Required once D3/D7 package files exist. |
| `make bench-package PACKAGE=<phase0_package.json>` | Required once a strict Phase 0 package exists. |
| `make docs-check` | Required for plan/docs updates. |
| `git diff --check` | Required before commit. |
| `make check` | Required if code changes are made. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] Corpus policy is chosen and recorded with provenance/license caveats.
- [ ] Candidate Africa-related transcripts are inventoried before ingestion;
  raw files are not committed.
- [ ] Sanitization/de-identification tooling is explicitly deferred.
- [ ] Scope record exists before output claims are written.
- [ ] Seed project runs in an isolated project store.
- [ ] Project output packet and audit manifest exist.
- [ ] Unlabeled adjudication sample is exported.
- [ ] Pre-registered adjudication protocol validates.
- [ ] Protocol/sample preflight passes.
- [ ] Any imported D3/D7 labels come only from explicit human labeling or from
  a clearly marked synthetic smoke package.
- [ ] If D3/D7 packages exist, strict Phase 0 package replay passes.
- [ ] Documentation states what evidence this slice does and does not support.

> Process criteria:
- [ ] Required gates pass.
- [ ] Full deterministic `make check` passes if code changes are made.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Which corpus source should be used? Status: RESOLVED for this slice. Use
  the located local Africa-related transcripts as the Plan #234 starting point.
  A public/shareable corpus remains future work.
- [ ] Can the old Africa-related transcripts be located?
  Status: PARTIALLY RESOLVED / DEFERRED. Candidate materials were located in
  ignored local `data/interviews/` and `data/samples/temp_test_interviews/`
  paths and recorded in `docs/LOCAL_DATA_INVENTORY.md`. Sanitization is
  deferred and is not required before local Plan #234 work.
- [ ] Who labels the adjudication responses? Status: OPEN. Human or qualified
  reviewer labels are required before claiming D3/D7 adjudication evidence.
  Agent-generated responses can exercise tooling only and must be caveated as
  synthetic.
- [ ] Should `make adjudication-sample` gain `PROJECTS_DIR` parity? Status:
  OPEN. The current target does not expose `PROJECTS_DIR`; implementation must
  verify whether `QC_PROJECTS_DIR` is sufficient or whether a code change is
  needed for package portability.
- [ ] What should the long-run sanitizer mechanism do? Status: DEFERRED. Initial
  target: CLI/Make flow that inventories raw docs, detects likely identifiers,
  supports reviewed redaction/generalization, writes a de-identification log,
  hashes raw/sanitized versions, and blocks ingestion unless the manifest
  records residual-risk caveats.

---

## Notes

Do not use this slice to claim methodological validity, full grounded theory,
human adjudication, SOTA evidence, causal/process-tracing proof, or abductive
quality. The first valid outcome is a reviewable, shareable instrument. Evidence
claims start only after real labels and scorecards exist.

Longer term, sanitization should become an agent-drivable capability with
review checkpoints, not an informal manual pre-step. That work is deferred and
should be planned separately after the local corpus/adjudication seed proves the
core workflow.
