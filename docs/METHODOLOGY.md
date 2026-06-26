# Qualitative Coding Methodology

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Goal

The project goal is to make LLM-assisted qualitative coding auditable enough
for serious analyst work. The system should not merely produce themes. It
should preserve the evidence chain from transcript to code application to claim
to review decision to exportable report.

The operating theory is:

- programmatic code enforces structure, provenance, coverage accounting, and
  fail-loud validation;
- LLM calls supply semantic and interpretive judgment inside typed schemas;
- humans provide final authority over codebooks, claims, and methodological
  interpretation;
- benchmark and preflight artifacts decide which claims are licensed.

The current repo is stronger at extracting themes, entities, and bounded
relationships than at representing interpretive stance. That means broad theme
labels can still outrun the more methodologically important question of what
participants are asserting, contesting, framing, or evaluating about those
themes. In practice, qualitative usefulness often depends on claim/position
structure, not theme labels alone.

## Methodological Boundary

The repo supports thematic analysis and a grounded-theory-inspired path. The
grounded-theory path is explicitly not "full GT" unless theoretical sampling,
category saturation, memo quality, and expert GT-fidelity evidence are
completed under a protocol.

The system fits codebook-oriented, post-positivist, and audit-heavy qualitative
analysis better than reflexive thematic analysis. Reflexive or constructivist
work can still use the tool as an assistant, but the automated agreement and
coverage metrics should not be treated as the method's quality criterion.

## Design Pattern

The key design pattern is a single typed state object:

- transcripts enter as documents and segments;
- coding stages produce codes and code applications;
- higher-order stages produce relationships, perspectives, synthesis, and
  disconfirmation outputs;
- substantive outputs are mirrored into a first-class claim ledger;
- human review decisions and exports remain attached to the same project state.

This makes the analysis inspectable and portable. It does not by itself prove
the analysis is correct.

It also does not guarantee that the default path centers the most
methodologically important analytic object. Right now the system gives strong
surface prominence to codes/themes and only secondary prominence to claims,
even though contested positions, framings, and scoped assertions are often the
more substantively useful outputs.

## Modality Split

This repo is hybrid.

Deductive / plan-first surfaces:

- Pydantic `ProjectState` and domain schemas;
- pipeline stage contracts;
- export contracts;
- protocol package schemas;
- preflight gates;
- Phase 0 scorecard artifact shape;
- claim-ledger read surfaces.

Exploratory / ladder surfaces:

- whether discovered codes are substantively useful;
- whether disconfirmation recall is good on a real corpus;
- whether interpretive outputs match expert judgment;
- whether GT-inspired stages have methodological fidelity;
- which prompt/model choices hold up on frozen cases.

For exploratory surfaces, the right next step is an instrumented corpus and
readout, not a stronger assertion in documentation.

The current long-running execution spine is
[docs/LONG_TERM_EXECUTION_PLAN.md](LONG_TERM_EXECUTION_PLAN.md). It applies this
modality split to the roadmap by naming the next unambiguous slices, separating
deductive contracts from exploratory readouts, and preserving the concern
register as the steering loop between slices.

## ADR Map

- [docs/adr/0001_qualitative_coding_methodology_spine.md](adr/0001_qualitative_coding_methodology_spine.md)
  records the decision to treat this repo as a governed qualitative-analysis
  instrument with an explicit dossier spine, not a generic labeling demo.

## Evidence Promotion Rule

A capability can be described as implemented when the repo has code, tests, and
operator-facing documentation for it.

A rigor claim can be described as evidenced only when a frozen case set,
protocol, benchmark artifact, or human-adjudicated package exists and the
result has been run.

A public superiority, parity, SOTA, or methodological-validity claim requires a
held-out protocol with appropriate statistical comparison and explicit caveats.

## Main Failure Modes

| Failure mode | Why it matters | Control |
|---|---|---|
| Overclaiming software validation as methodological validity | A passing test suite does not prove qualitative correctness. | Keep claim discipline in `PROJECT.md`, `docs/VALIDATION.md`, and `docs/PROJECT_THEORY_AND_GOALS.md`. |
| Treating example quotes as exhaustive corpus prevalence | LLM-surfaced quotes are not a denominator. | Use segment universe and exhaustive mode when coverage is the claim. |
| Calling the GT path "full grounded theory" | Current stages mimic parts of GT but do not complete GT's epistemic loop. | Use "grounded-theory-inspired" unless D8/GT-fidelity evidence is available. |
| Treating negative-case output as proof of disconfirmation coverage | Prompting for contrary evidence is not a held-out D7 result. | Use D7 gold packages and comparison artifacts before making recall claims. |
| Treating prompt-boundary fixtures as general robustness | Fixture/canary success is not a broad adversarial guarantee. | Keep INV-7 caveats and expand held-out adversarial evaluation. |
| Treating broad themes as sufficient analytic outputs | Topic/theme labels can hide stance, contestation, attribution, evaluation, and rival interpretations. | Promote claim/position-aware extraction and review surfaces rather than treating code graphs alone as the analytic center. |
