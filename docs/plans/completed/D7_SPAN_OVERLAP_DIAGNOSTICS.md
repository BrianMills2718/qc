# Plan #170: D7 Span-Overlap Diagnostics

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** D7 exact-anchor scorecard substrate
**Blocks:** richer D7 near-boundary retrieval/error analysis

---

## Outcome

D7 scorecards now include a diagnostic-only `disconfirmation_d7.span_overlap`
section whenever D7 gold is scored. The diagnostic compares character-offset
contrary-evidence anchors only when they share the same `target_claim_id` and
`doc_id`, reporting best IoU and Modified Hausdorff distance in both
gold-to-system and system-to-gold directions. Segment-only or missing-offset
anchors are counted as unscored for this diagnostic and are not converted into
guessed character spans.

Exact D7 TP/FP/FN, recall, precision, F1, Wilson/bootstrap intervals,
system-gold agreement metadata, and baseline scoring remain unchanged except
for the additive diagnostic section. This is local error-analysis metadata
only; it is not semantic disconfirmation validity, held-out benchmark evidence,
expert parity, or SOTA evidence.

Implementation commit: `7935ca4` (`Add D7 span-overlap diagnostics`).

Verification:

- Initial focused TDD run failed as expected because `disconfirmation_d7` did
  not yet expose `span_overlap`.
- `python -m pytest tests/test_bench_phase0.py -k "d7_span_overlap or d3_span_overlap" -q`
  -> 5 passed, 67 deselected.
- `python -m pytest tests/test_bench_phase0.py tests/test_bench_phase0_script.py -k "d7 or span_overlap or disconfirmation" -q`
  -> 18 passed, 95 deselected.
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> 1138 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed. Type check remains unconfigured by the repo.

---

## Gap

**Current:** D7 disconfirmation scoring reports exact target-claim/source-anchor
recall, precision, F1, Wilson intervals, F1 bootstrap intervals, exact-key
agreement metadata, baseline deltas, and human-ceiling exact-metric metadata
when gold is supplied. D3 application-validity scoring also reports local
same-code/document span-IoU and Modified Hausdorff diagnostics for near-boundary
span matches. D7 does not yet expose an equivalent diagnostic, so a predicted
contrary anchor that overlaps the right gold evidence span but misses exact
offsets is only visible as one false positive plus one false negative.

**Target:** Add a diagnostic-only `disconfirmation_d7.span_overlap` section when
D7 gold is scored. It will compare character-offset anchors over the same
`target_claim_id` and `doc_id`, reporting best IoU and Modified Hausdorff
distance in both gold-to-system and system-to-gold directions. Exact D7
TP/FP/FN/recall/precision/F1 remain unchanged and remain the primary scored
metrics.

**Why:** Public D7 work needs to distinguish exact-key failures from near-boundary
span disagreements without weakening the exact-score contract. This improves
local error analysis and retrieval diagnostics while preserving claim discipline:
overlap diagnostics are not semantic disconfirmation validity, held-out evidence,
or baseline superiority evidence.

---

## References Reviewed

- `qc_clean/core/bench.py:2767-2832` - current D7 scorecard assembly.
- `qc_clean/core/bench.py:2834-3168` - exact-anchor score, bootstrap, and D7
  baseline scoring helpers.
- `qc_clean/core/bench.py:3609-3776` - existing D3 span-overlap, IoU, and
  Modified Hausdorff diagnostics.
- `qc_clean/core/bench.py:3852-3919` - predicted D7 exact-key extraction and
  unscored contrary-anchor handling.
- `qc_clean/core/d7_gold.py:16-43` - D7 gold anchor validation contract.
- `tests/test_bench_phase0.py:1539-1636` - D3 span-overlap regression tests.
- `tests/test_bench_phase0.py:2333-2685` - D7 exact-score, interval, agreement,
  and baseline regression tests.
- `docs/EVALUATION_HARNESS.md` - Phase 0 D3/D7 scorecard status and claim
  caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/INV-6 partial status and
  evaluation-claim discipline.
- Memory context:
  `agent-memory recall 'active decisions' --project qualitative_coding` returned
  low-relevance historical task outcomes and no active conflicting decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a deterministic
repo-local scorecard diagnostic that generalizes the existing D3 local
span-overlap machinery to D7's target-claim/document anchor surface.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 span-overlap diagnostic | D7 gold anchors + system contrary anchors with character offsets | `disconfirmation_d7.span_overlap` diagnostic metrics | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] D7 exact metrics remain unchanged by overlap diagnostics.
- [x] D7 overlap rows only compare anchors with the same target claim and
  document.
- [x] Segment-only or otherwise unscoreable anchors are counted separately
  rather than guessed.
- [x] Notes state that the section is local diagnostic metadata, not semantic
  disconfirmation validity or held-out benchmark evidence.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify if status summary needs updating)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add focused failing tests for D7 near-boundary span overlap and unscored
   segment-only anchors while asserting exact D7 TP/FP/FN are unchanged.
2. Generalize the internal span dataclass/helper naming so D3 and D7 can share
   IoU and Modified Hausdorff logic without changing D3 output keys.
3. Add D7 span extraction from gold anchors and system negative-case
   contrary anchors; compare only same `target_claim_id` plus same `doc_id`.
4. Attach `span_overlap` to `disconfirmation_d7_scorecard` after exact scoring.
5. Update evaluation/theory docs conservatively: D7 now has local span-overlap
   diagnostics, but exact scores remain primary and no held-out/semantic claim is
   licensed by the diagnostic.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_d7_span_overlap_scores_near_boundary_match` | A same-target/document partial span overlap is reported with best IoU and Modified Hausdorff distance while exact D7 still records FP/FN. |
| `tests/test_bench_phase0.py` | `test_scorecard_d7_span_overlap_counts_unscored_records` | Segment-only gold/system anchors are counted as unscored for overlap diagnostics without guessed offsets. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0.py -k "d7 or span_overlap" -q` | Focused D7 and existing D3 span-overlap regressions. |
| `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` | Style/syntax gate for touched code. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `disconfirmation_d7.span_overlap` appears when D7 gold is scored.
- [x] Same-target/document near-boundary D7 spans report best IoU and Modified
  Hausdorff distance in gold-to-system and system-to-gold directions.
- [x] Exact D7 counts, keys, intervals, agreement metadata, and baseline scoring
  remain unchanged except for the additive diagnostic section.
- [x] Segment-only or missing-offset anchors are counted as unscored for the
  diagnostic and are not converted into fabricated character spans.
- [x] Docs preserve the caveat that D7 overlap diagnostics are local error
  analysis only, not semantic disconfirmation validity, held-out evidence,
  expert parity, or SOTA evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future D7 semantic near-match scoring combine span overlap with an
  adjudicated entailment/contradiction rubric? - Status: DEFERRED | Why it
  matters: this slice deliberately measures local source-span agreement, not
  whether the evidence semantically disconfirms the target claim.
