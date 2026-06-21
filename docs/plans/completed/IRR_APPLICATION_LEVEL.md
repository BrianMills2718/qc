# Plan — Application-level IRR

*Started: 2026-06-20.*

*Updated: 2026-06-21.* Application-level IRR now reports both the positive
`segment x code` application matrix and a segment-decision matrix over
`coded` / `no_code` / `not_examined`. Shared no-code judgments are counted
explicitly instead of being invisible in the positive-only denominator.

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
- Positive code-application unit = `(segment x aligned code)` binary cell: did
  pass P assign code C to segment S? Build a `{seg_key::code: [0/1 per pass]}`
  matrix and reuse the existing binary agreement metrics.
- Segment-decision unit = one categorical row per segment, with values
  `coded`, `no_code`, or `not_examined`. This is the denominator that counts
  shared null decisions explicitly.
- Report both application-level views alongside (not replacing) the
  codebook-discovery metrics, clearly labeled.
- Scope: thematic exhaustive only for now. GT app-level (constant comparison
  already segments) is a follow-up.

## Pre-made decisions

- `application_level: bool` param on `run_irr_analysis`; passes set
  `ctx.exhaustive_coding=True`. CLI: `project irr --application-level`.
- New `IRRResult` fields: `application_level`, `application_units`,
  `application_percent_agreement`, `application_cohens_kappa`,
  `application_fleiss_kappa`, `application_interpretation`, `application_matrix`.
- New segment-decision fields: `segment_decision_units`,
  `segment_decision_percent_agreement`, `segment_decision_cohens_kappa`,
  `segment_decision_fleiss_kappa`, `segment_decision_interpretation`,
  `segment_decision_matrix`.
- `seg_key = f"{doc_id}#{start_char}"`. In the positive application matrix, only
  cells where a code was applied by >=1 pass are included (standard multi-label
  denominator). The segment-decision matrix includes every segment observed in
  any pass.

## Phases

| # | Scope | Status |
|---|-------|--------|
| 1 | `build_application_matrix` + IRRResult fields + pure tests | DONE |
| 2 | Wire run_irr_analysis(application_level=True) + e2e test | DONE |
| 3 | CLI `--application-level`; docs (§11, ledger, INV-8) | DONE |
| 4 | Segment-decision agreement for `coded` / `no_code` / `not_examined`; CLI/export/MCP/test docs | DONE |
