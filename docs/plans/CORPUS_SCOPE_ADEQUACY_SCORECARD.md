# Plan #151: Corpus-Scope Adequacy Scorecard

## Mission

Add deterministic Phase 0 accounting for the corpus-boundary record. The repo
can already store `ProjectState.corpus_scope`, surface it in exports, and lint
risky population-generalizing phrasing. The remaining local gap is that
`make bench` does not summarize whether the scope record has enough boundary
detail to support disciplined reporting.

## Scope

- Add a `corpus_scope_adequacy` section to `phase0_scorecard`.
- Reuse the existing `scope_status_for_lint()` classification:
  `missing`, `empty`, `missing_sampling_frame`, or `complete`.
- Report deterministic field-level completeness for phenomenon, population,
  sampling frame, inclusion criteria, exclusion criteria, and notes.
- Report warning codes/messages for missing scope, empty scope, and
  population-without-sampling-frame states.
- Include document and claim counts so downstream reviewers can see whether
  claim-bearing outputs are being interpreted under a recorded boundary.
- State the caveat directly: this is scope-record completeness/accounting only,
  not sampling-frame adequacy, population validity, methodological validity, or
  SOTA evidence.

## Non-Goals

- Do not assess whether the sampling frame is actually representative.
- Do not collect new data, run expert review, or call an LLM.
- Do not change export warnings, scope CLI/API behavior, or phrasing lint rules.
- Do not permit population generalization merely because fields are filled.

## Acceptance Criteria

Passes when:

- `phase0_scorecard(state)["corpus_scope_adequacy"]` is always present.
- Missing, empty, population-without-sampling-frame, and complete scope states
  produce stable statuses and warning codes.
- Field completeness booleans and filled-field counts are deterministic.
- The scorecard includes document and claim counts.
- The note/caveat explicitly says this is not sampling-frame adequacy or
  validity evidence.
- Focused tests cover all four scope states.
- `make docs-check` and `make check` pass before closeout.

Fails when:

- A filled scope record is described as proof of sampling adequacy.
- Population without sampling frame is treated as complete.
- Claim-bearing outputs can appear without an explicit scope status in Phase 0.
- Output ordering is nondeterministic.

## Failure Modes And Diagnostics

| Failure mode | Diagnosis | Response |
|---|---|---|
| Scope status drifts from phrasing lint | Focused tests disagree with `scope_status_for_lint()` | Reuse the existing classifier instead of duplicating policy |
| Empty scope is mistaken for missing scope | Empty `CorpusScope()` fixture fails | Distinguish no record from record with zero detail |
| Filled population is overclaimed | Population-only fixture lacks warning | Require `sampling_frame` when `population` is set |
| Complete record is overclaimed | Docs or note says "adequate sample" | Rewrite to "record completeness" and keep validity caveat |

## Verification

- `python -m pytest tests/test_bench_phase0.py -k "corpus_scope_adequacy"`
- `python -m pytest tests/test_scope_phrasing_lint.py -q`
- `make docs-check`
- `make check`

## Closeout Notes

To be filled after implementation and verification.
