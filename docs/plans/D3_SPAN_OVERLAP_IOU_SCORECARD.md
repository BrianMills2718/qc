# Plan #41: D3 Span-Overlap IoU Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Full D3 application-validity evaluation; LLMCode-style span alignment

---

## Gap

**Current:** D3 application-validity scoring is exact code/doc/span matching. That
is useful for deterministic TP/FP/FN, but too brittle for span-boundary
evaluation. The evaluation harness still lists IoU / Modified Hausdorff as
future D3 span-alignment metrics.

**Target:** Add a local same-code/same-document char-span IoU diagnostic inside
`application_validity_d3` when D3 gold is present. For each scoreable gold span,
report the best predicted span IoU over system code applications with the same
code ID and document ID, plus aggregate mean best-gold IoU and mean
best-predicted IoU. Segment-only or unanchored records are counted as unscored
for this overlap metric.

**Why:** Exact-span scoring is intentionally strict, but span-alignment metrics
are needed to compare near-boundary matches without treating every offset
difference as a total miss. This is the next deterministic scaffold toward the
LLMCode-style D3 evaluator.

---

## References Reviewed

- `qc_clean/core/bench.py` - D3 exact application scorecard.
- `tests/test_bench_phase0.py` - D3 exact-score tests.
- `docs/EVALUATION_HARNESS.md` - D3 IoU/Hausdorff target and claim discipline.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D3 span overlap IoU Hausdorff application validity scorecard' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. IoU is already named in the harness as an LLMCode-style
span alignment metric to borrow. Modified Hausdorff remains a later lane.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D3 same-code/doc span IoU | D3 gold anchors + system code applications | `application_validity_d3.span_overlap` JSON object | qualitative_coding | Phase 0 scorecard, artifact packages | free |

### Capability Validation

- [ ] D3 scored sections include `span_overlap` when scoreable char-span gold is
  present.
- [ ] Same-code/same-document best IoU is computed for gold→system and
  system→gold directions.
- [ ] Segment-only/unanchored records are counted as unscored for overlap, not
  silently treated as zero-overlap spans.

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

1. Add private span helpers and IoU computation in `qc_clean/core/bench.py`.
2. Add `span_overlap` to scored `application_validity_d3` sections.
3. Add tests for partial-overlap scoring and unscored segment/unanchored records.
4. Update docs conservatively: local IoU overlap exists; Modified Hausdorff,
   κ/α/AC1, human ceiling, and expert parity remain future work.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d3_application_gold_exact_span_and_code` | Existing D3 exact score now also reports overlap metadata. |
| `tests/test_bench_phase0.py` | new partial-overlap test | Same-code/doc best IoU captures near-boundary span overlap. |
| `tests/test_bench_phase0.py` | new unscored-overlap test | Segment-only/unanchored records are counted as unscored for IoU. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D3 exact matching remains stable. |
| `tests/test_bench_phase0_script.py` | External D3 package/file scorecard paths remain stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] D3 scorecard includes a `span_overlap` object for scored D3 sections.
- [ ] The overlap object reports counts, mean best gold IoU, mean best predicted
  IoU, and per-gold/per-predicted best-overlap rows.
- [ ] Unscoreable gold/predicted records are visible in counts.
- [ ] Docs identify this as local IoU span-alignment scaffolding only.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should IoU use a threshold for matched/not-matched? — Status: DEFERRED |
  Why it matters: threshold choice belongs in a future benchmark protocol. This
  slice reports continuous IoU only.
- [ ] Should Modified Hausdorff be added now? — Status: DEFERRED | Why it
  matters: Hausdorff metric design should follow a reviewed LLMCode-compatible
  implementation lane.

---

## Notes

This plan adds a local span-overlap diagnostic. It does not compute κ/α/AC1,
human-human agreement, Modified Hausdorff, or expert-parity evidence.
