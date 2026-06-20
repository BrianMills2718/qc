# Plan — Application-level IRR

*Started: 2026-06-20.*

## Gap

`project irr` measures **codebook-discovery** agreement (do passes surface the
same code *names*?), not **application-level** agreement (do passes assign the
same code to the *same text unit*?). The latter is the real "two coders agree"
number reviewers expect, and it was impossible before because there was no shared
unit. Exhaustive coding (INV-8) now gives one: every pass renders a decision per
segment, and the segment universe is deterministic, so `(doc_id, start_char)`
keys align across passes.

## Design

- Run N **exhaustive** coding passes (thematic). Each pass anchors applications
  directly to segment spans, so per pass we derive `{seg_key: {normalized code
  names}}` from `code_applications` + codebook.
- Unit = `(segment × aligned code)` binary cell: did pass P assign code C to
  segment S? Build a `{seg_key::code: [0/1 per pass]}` matrix and reuse the
  EXISTING `compute_percent_agreement` / `compute_cohens_kappa` /
  `compute_fleiss_kappa`. Report alongside (not replacing) the codebook-discovery
  metrics, clearly labeled.
- Scope: thematic exhaustive only for now. GT app-level (constant comparison
  already segments) is a follow-up.

## Pre-made decisions

- `application_level: bool` param on `run_irr_analysis`; passes set
  `ctx.exhaustive_coding=True`. CLI: `project irr --application-level`.
- New `IRRResult` fields: `application_level`, `application_units`,
  `application_percent_agreement`, `application_cohens_kappa`,
  `application_fleiss_kappa`, `application_interpretation`, `application_matrix`.
- `seg_key = f"{doc_id}#{start_char}"`. Only cells where a code was applied by
  ≥1 pass are included (standard multi-label denominator).

## Phases

| # | Scope | Status |
|---|-------|--------|
| 1 | `build_application_matrix` + IRRResult fields + pure tests | DONE |
| 2 | Wire run_irr_analysis(application_level=True) + e2e test | DONE |
| 3 | CLI `project irr --application-level`; docs (§11, ledger, claim discipline) | PENDING |
