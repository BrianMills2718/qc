# Plan #40: D7 Baseline Delta Bootstrap Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D7 retrieval-mode comparison reporting; future held-out baseline testing

---

## Gap

**Current:** D7 baseline scores include exact TP/FP/FN, recall, precision, F1,
Wilson intervals for recall/precision, local F1 bootstrap intervals, and
`system_minus_baseline` point deltas. The deltas themselves still have no local
interval metadata, so readers can overinterpret small exact-key fixtures.

**Target:** Add a deterministic paired exact-key bootstrap interval for
`system_minus_baseline` recall, precision, and F1 deltas in D7 baseline sections.
The output must be visibly local/exact-key bootstrap metadata, not a held-out
superiority claim.

**Why:** D7 retrieval-mode reports now compare multiple prediction packages
against one gold file. Paired local delta intervals make those reports more
honest about uncertainty while preserving claim discipline: held-out data,
frozen baselines, and `prompt_eval`-backed tests are still required before any
superiority claim.

---

## References Reviewed

- `qc_clean/core/bench.py` - D7 system score, baseline scoring, exact-key
  bootstrap helpers.
- `qc_clean/core/d7_retrieval.py` - retrieval comparison report consuming the D7
  scorecard.
- `tests/test_bench_phase0.py` - D7 baseline exact-score coverage.
- `docs/EVALUATION_HARNESS.md` - current baseline-delta caveats.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D7 baseline delta bootstrap interval exact score prompt_eval' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This is a deterministic paired bootstrap over exact
gold/system/baseline key membership. Full held-out statistical testing remains a
later `prompt_eval`-backed lane.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 baseline delta bootstrap interval | D7 gold keys + system predictions + one baseline prediction set + bootstrap config | `system_minus_baseline_ci` JSON object | qualitative_coding | Phase 0 scorecard, D7 retrieval comparison reports | free |

### Capability Validation

- [ ] D7 baseline sections include `system_minus_baseline_ci` when bootstrap is
  enabled.
- [ ] Delta CI covers recall, precision, and F1.
- [ ] Disabling `phase0_exact_bootstrap.enabled` suppresses both F1 and delta
  bootstrap outputs.

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

1. Thread system predicted keys and unscored system predictions into D7 baseline
   scoring.
2. Add paired exact-key bootstrap helpers for recall/precision/F1 deltas.
3. Add `system_minus_baseline_ci` beside `system_minus_baseline` when bootstrap
   is enabled.
4. Add tests for default delta CI output and disabled bootstrap behavior.
5. Update docs conservatively: local paired delta intervals exist, but held-out
   live-baseline superiority testing remains unmet.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d7_baselines_against_same_gold` | Baseline score includes recall/precision/F1 delta CI metadata. |
| `tests/test_bench_phase0.py` | new disabled bootstrap baseline test | Disabling bootstrap suppresses baseline delta CI. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D7 system and baseline exact scores remain stable. |
| `tests/test_d7_retrieval.py` | Retrieval comparison reports remain compatible. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] D7 baseline sections report `system_minus_baseline_ci` by default.
- [ ] Delta CI metadata includes method, confidence, samples, seed, population
  size, and per-metric lower/upper bounds.
- [ ] Bootstrap disabled mode suppresses F1 and delta bootstrap outputs.
- [ ] Docs distinguish local paired bootstrap intervals from held-out
  superiority/non-inferiority testing.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should delta intervals use document-level pairing in the future? — Status:
  DEFERRED | Why it matters: document-level pairing needs enough held-out
  documents and document-aware baseline packages. This slice remains exact-key
  local Phase 0 metadata.

---

## Notes

This plan does not run a live baseline, populate a held-out D7 gold set, or
license superiority. It makes local exact-key comparison reports less brittle.
