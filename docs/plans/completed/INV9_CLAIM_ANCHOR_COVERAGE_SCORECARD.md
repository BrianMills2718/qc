# Plan #150: INV-9 Claim-Anchor Coverage Scorecard

## Mission

Expose deterministic Phase 0 accounting for whether first-class analytic claims
are actually source-anchored. This closes a blind spot in the INV-9 object layer:
the ledger already records `support_status`, `supporting_anchors`, and
`contrary_anchors`, but the evaluation harness does not summarize how many
claims are anchored versus still `needs_anchor`.

## Scope

- Add an LLM-free scorecard section to `qc_clean/core/bench.py`.
- Include total claim counts, anchor counts, anchored/unanchored claim counts,
  anchored rate with Wilson interval metadata, and deterministic breakdowns by
  claim kind, source stage, and support status.
- Treat either supporting or contrary anchors as source-anchor coverage.
- Keep no-claims events visible in totals and breakdowns instead of filtering
  them out; they are explicit ledger artifacts and should not disappear.
- Document that the scorecard is structural accounting only. Anchor presence is
  not truth, human adjudication, full disconfirmation, or methodological
  validity evidence.

## Non-Goals

- Do not change claim creation, disconfirmation retrieval, or human review
  workflows.
- Do not add LLM calls, new external files, prompt_eval integration, or held-out
  evidence.
- Do not assert that claims are valid, retained, or fully supported.

## Acceptance Criteria

Passes when:

- `phase0_scorecard(state)` includes a stable `claim_anchor_coverage` section.
- Empty claim ledgers return deterministic zero-count output without errors.
- Mixed claim fixtures report correct supporting/contrary anchor totals,
  anchored/unanchored counts, `needs_anchor` counts, anchored rate, and
  breakdowns by kind/stage/status.
- The scorecard note states the caveat: structural source-anchor accounting only,
  not validity/adjudication/disconfirmation evidence.
- Focused tests cover empty and mixed-ledger cases.
- `make docs-check` and `make check` pass before closeout.

Fails when:

- The scorecard omits claims with only contrary anchors.
- The scorecard hides `needs_anchor` claims or no-claims events.
- The output order is nondeterministic.
- Documentation implies that source-anchor coverage proves claim truth,
  methodological validity, SOTA, or human adjudication.

## Failure Modes And Diagnostics

| Failure mode | Diagnosis | Response |
|---|---|---|
| `needs_anchor` claims are undercounted | Fixture with explicit `ClaimSupportStatus.NEEDS_ANCHOR` fails | Count support status directly from claim objects |
| Contrary evidence claims look unanchored | Negative-case fixture with only `contrary_anchors` fails | Define anchored as supporting or contrary anchor count > 0 |
| Output order churns in JSON | Test compares exact nested dicts | Sort all breakdown keys before returning |
| Documentation overclaims | `docs-check` or review finds claim-discipline drift | Add caveat text and remove validity language |

## Verification

- `pytest tests/test_bench_phase0.py -k "claim_anchor_coverage"`
- `make docs-check`
- `make check`

## Closeout Notes

Completed in commits:

- Plan checkpoint: `f1ae2fa`
- Implementation checkpoint: `a96d823`

Implemented `claim_anchor_coverage` in `phase0_scorecard` with total claim
counts, supporting/contrary anchor counts, anchored/unanchored claim counts,
anchored-rate Wilson interval metadata, and deterministic breakdowns by claim
kind, source stage, and support status. The scorecard treats supporting or
contrary anchors as source-anchor coverage and keeps no-claims events visible
as ledger rows.

Verification:

- `python -m pytest tests/test_bench_phase0.py -k claim_anchor_coverage -v`
- `python -m pytest tests/test_claims.py -q`
- `python -m pytest tests/test_bench_phase0.py -q`
- `ruff check qc_clean/core/bench.py tests/test_bench_phase0.py`
- `make docs-check`
- `make check` (`1086 passed, 1 skipped, 8 deselected`)

Claim discipline: this is deterministic structural accounting only. It does not
prove claim truth, human adjudication, full disconfirmation coverage,
methodological validity, or SOTA evidence.
