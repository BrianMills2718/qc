# ADR 0001: Treat Qualitative Coding As A Governed Methodology Instrument

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Status

Accepted.

## Context

The repo has many implementation plans and evaluation substrates. Without a
single dossier spine, a portfolio reviewer sees a large tool surface but not
the methodological argument: the project is about making qualitative analysis
auditable, not about producing labels faster.

The repo also has a real overclaiming risk. It includes grounded-theory-inspired
stages, prompt-boundary fixtures, disconfirmation scoring substrates, and
evaluation preflights, but those do not yet license full-GT, prompt-injection
robustness, methodological-validity, expert-parity, or SOTA claims.

## Decision

Maintain a wiki-visible project dossier spine:

- `PROJECT.md` as the project entrypoint;
- `docs/METHODOLOGY.md` as the methodology spine;
- `docs/ARTIFACTS.md` as the artifact register;
- `docs/VALIDATION.md` as the validation register;
- `docs/CONCERNS.md` as the concern register;
- this ADR as the durable framing decision.

The dossier will frame the repo as a governed qualitative-analysis instrument
for analyst work. It will preserve explicit claim discipline and point to the
existing evidence bundle, theory document, evaluation harness, plans, and
benchmark/canary artifacts.

## Consequences

Positive:

- Reviewers get a short path through a large repo.
- Wiki generation can classify the repo as `portfolio-ready`.
- Future agents have a stable place to update methodology, artifacts,
  validation, and concerns.
- The portfolio story emphasizes analyst-methods engineering rather than
  generic infrastructure.

Negative:

- The dossier may look more polished than the evidence justifies unless
  validation caveats remain prominent.
- Existing implementation plans continue to move quickly, so generated wiki
  surfaces need periodic refresh.

## Non-Decisions

This ADR does not validate the methodology, change pipeline behavior, move any
repos, replace existing plan tracking, or claim the system is ready for public
SOTA positioning.

