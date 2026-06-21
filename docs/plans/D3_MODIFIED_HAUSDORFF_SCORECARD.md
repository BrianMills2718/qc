# Plan #42: D3 Modified Hausdorff Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** LLMCode-style D3 span-alignment evaluation

---

## Gap

**Current:** D3 scorecards now include exact-anchor scores and local
same-code/document span-IoU diagnostics. The harness still lists Modified
Hausdorff as missing for LLMCode-style span alignment.

**Target:** Extend the D3 `span_overlap` object with a local discrete
char-position Modified Hausdorff distance for the same best-overlap pairs already
selected by same-code/document IoU. Report per-row distances plus aggregate mean
best-gold and mean best-predicted distances.

**Metric definition for this slice:** treat each char span as the integer
position set `[start_char, end_char)`. Distance from one position to a span is
zero if the position is inside the other span, otherwise the nearest boundary
distance. Modified Hausdorff distance is
`max(mean(distance from A positions to B), mean(distance from B positions to A))`.
Lower is better; exact span match is zero.

**Why:** IoU captures overlap ratio; Modified Hausdorff captures boundary
distance. Reporting both makes local D3 span diagnostics more informative while
keeping full human-ceiling D3 evaluation out of scope.

---

## References Reviewed

- `qc_clean/core/bench.py` - current D3 `span_overlap` IoU helpers.
- `tests/test_bench_phase0.py` - D3 span-overlap tests.
- `docs/EVALUATION_HARNESS.md` - LLMCode-style IoU/Hausdorff target.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D3 Modified Hausdorff span distance LLMCode metric' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This is a documented local implementation of the
Modified Hausdorff-style span distance named in the evaluation harness. Full
LLMCode compatibility and prompt_eval integration remain future work.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D3 Modified Hausdorff diagnostic | D3 scoreable char spans + selected same-code/doc span pairs | `span_overlap` distance fields | qualitative_coding | Phase 0 scorecard, artifact packages | free |

### Capability Validation

- [ ] Exact span matches report distance zero.
- [ ] Partial-overlap spans report positive deterministic distance.
- [ ] Aggregate mean best-gold and mean best-predicted distances are present.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add private Modified Hausdorff helper(s) over `_ApplicationSpan`.
2. Include `best_modified_hausdorff_distance` in per-gold and per-predicted
   overlap rows.
3. Include aggregate mean best-gold and mean best-predicted distance fields.
4. Add tests for exact match and partial overlap.
5. Update docs conservatively: local Modified Hausdorff diagnostic exists, but
   D3 κ/α/AC1, human ceiling, held-out data, and expert parity remain future
   work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d3_application_gold_exact_span_and_code` | Exact match rows include zero distance where spans match. |
| `tests/test_bench_phase0.py` | `test_scorecard_d3_span_overlap_scores_near_boundary_match` | Partial overlap reports deterministic positive distance. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D3 exact and IoU behavior remain stable. |
| `tests/test_bench_phase0_script.py` | External D3 package/file paths remain stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] `span_overlap` rows include `best_modified_hausdorff_distance`.
- [ ] `span_overlap` includes mean best-gold and mean best-predicted Modified
  Hausdorff distances.
- [ ] Docs identify this as local span-distance scaffolding only.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should this be replaced by a literal upstream LLMCode evaluator? — Status:
  DEFERRED | Why it matters: full compatibility should be a prompt_eval-backed
  evaluator lane. This slice keeps the local scorecard deterministic.

---

## Notes

This plan does not compute D3 human agreement, human ceiling, or expert parity.
It adds a local distance diagnostic for already-supplied adjudicated gold.
