# Plan #10: INV-2 D7 Disconfirmation Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 hardened disconfirmation; D7 evaluation-harness disconfirmation metrics

---

## Outcome

Completed 2026-06-21. `qc_clean/core/bench.py` now includes a deterministic
`disconfirmation_d7` scorecard section. With no adjudicated gold annotations it
reports `status="not_available"`; when
`ProjectState.config.extra["disconfirmation_gold"]` contains anchored
contrary-evidence gold records, it computes exact target-claim/source-anchor
TP/FP/FN, recall, precision, and F1 from negative-case claim ledger anchors.

This is a D7 scoring substrate only. It does not create a held-out gold set,
confidence intervals, baselines, semantic retrieval, or methodological validity
evidence. INV-2/INV-6 remain PARTIAL.

Verification: `python -m pytest tests/test_bench_phase0.py tests/test_disconfirmation_retrieval_inv2.py -q`
passed (`17 passed`) before the implementation commit. Final plan completion was
verified with `make check`.

---

## Gap

**Current:** Negative-case analysis is retrieval-first over bounded, anchored
claim-candidate passages and can attach returned `candidate_id`s as exact
contrary anchors. The Phase 0 scorecard reports grounding, coverage, reliability,
and stability, but it cannot yet quantify whether negative-case analysis found a
known human/adjudicated contrary-evidence set.

**Target:** Add a deterministic D7 scorecard slice that computes
disconfirmation recall, precision, and F1 when a project state carries
gold/adjudicated contrary-evidence annotations. If no gold is present, the
scorecard must explicitly report D7 as unavailable and explain why. This is a
measurement surface, not methodological validity evidence by itself.

**Why:** INV-2/INV-6 cannot become credibility evidence until disconfirmation is
measured against a human-identified contrary-evidence gold set. This plan creates
the smallest agent-drivable scoring contract that future gold datasets and
prompt_eval suites can plug into.

---

## References Reviewed

- `CLAUDE.md` - current operating status, next high-value lanes, and claim discipline.
- `docs/PROJECT_THEORY_AND_GOALS.md:255-260` - INV-2/INV-6/INV-7 statuses and remaining disconfirmation gaps.
- `docs/PROJECT_THEORY_AND_GOALS.md:328-340` - roadmap priority: evaluation harness, then disconfirmation/adjudication.
- `docs/EVALUATION_HARNESS.md:42` - D7 definition: recall/precision vs human-identified disconfirming evidence.
- `docs/EVALUATION_HARNESS.md:111` - Phase 1 calls for D7 computation against a small expert gold set.
- `qc_clean/core/disconfirmation.py` - current retrieval-first candidate model and exact anchor conversion.
- `qc_clean/core/bench.py` - existing deterministic Phase 0 scorecard surface.
- `qc_clean/schemas/domain.py` - `ProjectState`, `AnalyticClaim`, and `ClaimAnchor` models.
- `tests/test_bench_phase0.py` - current scorecard contract tests.
- `tests/test_disconfirmation_retrieval_inv2.py` - current INV-2 retrieval-first contract tests.
- Memory context: `agent-memory recall 'active decisions' --project qualitative_coding` — no active blocking decision surfaced.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. The metric shape
is already specified in `docs/EVALUATION_HARNESS.md`; this plan only creates the
repo-local deterministic scoring substrate.

---

## Capabilities

This plan modifies an internal scorecard function only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV2_D7_DISCONFIRMATION_SCORECARD.md` (create, then move to completed)

---

## Plan

### Steps

1. Add a small D7 scoring contract to the bench layer using `ProjectState.config.extra`
   as the temporary gold-annotation carrier.
2. Normalize gold and predicted contrary evidence to exact comparison keys:
   `(target_claim_id, doc_id, start_char, end_char)` where spans are present,
   falling back only to `segment_id` when span offsets are absent.
3. Compute true positives, false positives, false negatives, recall, precision,
   and F1. Keep results deterministic and LLM-free.
4. Add scorecard metadata that clearly labels D7 as gold-dependent and not a
   SOTA/parity claim.
5. Add tests for no-gold unavailable state, perfect match, and mixed
   precision/recall behavior.
6. Update docs conservatively: D7 scoring substrate exists; no D7 benchmark has
   been run, and INV-2/INV-6 remain partial.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_reports_d7_unavailable_without_gold` | Scorecard does not imply D7 evidence when no gold annotations exist. |
| `tests/test_bench_phase0.py` | `test_scorecard_computes_d7_perfect_match_against_gold` | Exact target/span overlap yields recall=precision=F1=1. |
| `tests/test_bench_phase0.py` | `test_scorecard_computes_d7_false_positive_and_false_negative` | Mixed predictions produce correct TP/FP/FN, recall, precision, and F1. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Scorecard contract and honest metadata. |
| `tests/test_disconfirmation_retrieval_inv2.py` | Negative-case anchors still feed scoring correctly. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Phase 0 scorecard includes a `disconfirmation_d7` section.
- [ ] With no gold annotations, D7 reports `status="not_available"` and does not expose numeric scores.
- [ ] With gold annotations, D7 reports TP/FP/FN, recall, precision, F1, matched gold keys, missed gold keys, and extra predicted keys.
- [ ] D7 comparison uses target-claim identity plus exact source anchors, not free-text similarity.
- [ ] Docs state this is a scoring substrate only; no benchmark result or full INV-2 claim is made.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Where should long-term gold annotations live? — Status: DEFERRED | Why it matters: `ProjectState.config.extra` is adequate for this slice, but a full Phase 1 harness likely needs versioned prompt_eval case files with hashes.
- [ ] Should near-overlap span matches use IoU later? — Status: DEFERRED | Why it matters: D7 may need tolerance for human boundary differences, but this first slice intentionally uses exact anchors to avoid ambiguous scoring.

---

## Notes

This plan intentionally avoids semantic retrieval or live LLM evaluation. It
creates a deterministic measurement surface so future retrieval/model changes
can be scored instead of judged impressionistically.
