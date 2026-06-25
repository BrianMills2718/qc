# Default-Path Operational Credibility Policy

**Status:** Active governance policy
**Last updated:** 2026-06-25

This policy exists to stop a specific class of failure: a default-path
user-facing analytic surface can look complete in the UI or docs while being
operationally weak, sparsely populated, or unsupported on the default path.

## Policy Statement

If a surface is visible to users by default and implies analytic capability, it
must not be treated as complete from schema/tests/synthetic fixtures alone.

Before that surface is presented as complete, the repo must have:

1. a declared producer contract on the default supported path;
2. explicit operational-validation requirements; and
3. real-run inspection requirements appropriate to the surface class.

This policy is repo-wide as a governance rule, but enforcement is scoped.

## Scope

Default enforcement targets:

- default-path user-facing surfaces;
- graph, review, report, export, and adjudication surfaces;
- claim-bearing outputs or UI elements that imply analytic capability.

Default enforcement does not target with equal force:

- internal refactors;
- compatibility wrappers;
- hidden experimental paths;
- purely synthetic smoke fixtures;
- narrow infrastructure/plumbing slices with no visible analytic surface.

## Completion States

This repo now uses three distinct completion states:

- **structural completion:** code, schemas, commands, tests, and fixtures exist
  and pass their intended gates.
- **operational verification:** the default supported path has a declared
  producer, the visible surface is reviewable on a real local run, and the
  surface is not trivially empty or unsupported relative to its stated scope.
- **methodological validation:** expert- or gold-backed evidence shows that the
  output is substantively valid for a defined task/corpus.

Structural completion is not operational verification. Operational verification
is not methodological validation.

## Enforcement Model

Minimum viable enforcement:

1. `docs/governance/default_path_surface_contracts.yaml` records visible
   default-path surfaces, supported paths, producer contracts, and rollout
   status.
2. `scripts/check_default_path_surface_contracts.py --validate-config`
   validates that registry in the default docs gate.
3. `scripts/check_surface_operational_readiness.py` validates that active plans
   explicitly declare operational-validation classification and real-run
   requirements.

Initial rollout is intentionally scoped:

- registry/config validity is blocking now;
- active-plan operational-validation declarations are blocking now;
- known default-path producer gaps remain visible in the registry and may emit
  warnings, but do not automatically fail the repo until the follow-on
  implementation lane hardens them.

Future stricter rollout may make certain registry violations blocking, such as a
default-visible surface whose default-path producer status remains `missing`.

## Governance Order

This policy follows the repo governance order:

`review -> cleanup -> documentation updates -> planning updates -> implementation`

That means:

- review the visible/default-path failure first;
- clean up policy language and planning structure;
- update canonical docs and templates;
- update active plans and trackers;
- only then harden validators or runtime behavior.

## Current Triggering Example

The immediate motivating case was the default thematic local seed run on
2026-06-25:

- the graph UI exposed a `Code Relationships` tab;
- the default thematic pipeline did not populate `state.code_relationships`;
- the entity map was structurally populated but sparse enough to challenge
  product credibility.

That is the archetypal failure this policy is meant to catch earlier.
