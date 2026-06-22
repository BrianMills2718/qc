# Plan #55: D7 System-Gold Agreement Scorecard

**Status:** Planned
**Type:** implementation
**Priority:** Medium
**Blocked By:** None
**Blocks:** D7 richer agreement-vs-gold metadata

---

## Gap

**Current:** The D7 disconfirmation scorecard reports exact target-claim/source
TP/FP/FN, precision, recall, F1, Wilson intervals, F1 bootstrap intervals,
baseline deltas, and human-ceiling metadata. It does not report the same
prevalence-aware binary system-vs-gold agreement metadata now available for D3.

**Target:** Add a deterministic `system_gold_agreement` section to
`disconfirmation_d7` when D7 gold is available. It will treat the union of exact
D7 gold keys and exact predicted contrary-evidence keys as binary rows, with two
raters: `gold` and `system`. It will report row count, percent agreement,
Cohen's κ, Gwet's AC1, prevalence, and a note that this is exact-key binary
agreement metadata, not semantic disconfirmation validity or held-out benchmark
evidence.

**Why:** This makes D7 exact-key agreement diagnostics consistent with D3 while
preserving claim discipline: exact-key κ/AC1 metadata does not establish
disconfirmation quality without populated held-out gold and baselines.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D7 exact disconfirmation scorecard status and
  held-out/baseline caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/INV-6 partial status and no
  credibility claim without held-out evidence.
- `qc_clean/core/bench.py` - D7 exact key scoring, D3 system-gold agreement,
  prevalence tables, and human-ceiling comparison metadata.
- `qc_clean/core/pipeline/irr.py` - binary percent agreement, Cohen's κ, and
  Gwet's AC1 helpers.
- `tests/test_bench_phase0.py` - D7 scorecard and human-ceiling coverage.
- Memory context: unavailable. The last three `agent-memory recall` attempts in
  this session failed with the same OpenRouter 402/403 embedding-provider
  errors, so the circuit breaker applies; no local coordination claims were
  present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic binary agreement metadata over exact target-claim/source
anchor keys. Semantic near-match disconfirmation and held-out live baselines
remain prompt_eval-backed benchmark work.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 exact-key system-gold agreement | D7 gold + exact predicted contrary-evidence keys | Binary agreement metrics/prevalence | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [ ] Agreement rows are built from the exact union of gold and predicted D7 keys.
- [ ] Metrics include percent agreement, Cohen's κ, and Gwet's AC1.
- [ ] Prevalence is reported for interpreting sparse exact-key labels.
- [ ] Notes prevent semantic-validity/held-out-benchmark interpretation.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Generalize the D3 exact-key binary agreement helper so D3 and D7 can share
   it without duplicating metric logic.
2. Add `system_gold_agreement` to `disconfirmation_d7_scorecard`.
3. Add focused tests for mixed TP/FP/FN D7 rows and perfect-match D7 rows.
4. Update docs to say D7 exact-key system-vs-gold κ/AC1 metadata exists while
   held-out semantic disconfirmation validity and live baselines remain future.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D7 mixed agreement test | Union rows, percent agreement, κ/AC1, and prevalence reflect TP/FP/FN exact keys. |
| `tests/test_bench_phase0.py` | D7 perfect agreement test | Perfect exact D7 match reports agreement metrics at 1.0. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D7 exact scorecard, baseline, and human-ceiling behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] `disconfirmation_d7.system_gold_agreement` exists when D7 gold is scored.
- [ ] Mixed TP/FP/FN exact-key rows produce deterministic agreement metrics and
  prevalence metadata.
- [ ] Perfect exact matches produce 1.0 agreement metrics.
- [ ] Docs preserve the caveat that this is exact-key binary agreement metadata,
  not semantic disconfirmation validity or held-out benchmark evidence.

> Process criteria:
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should D7 semantic near-match scoring use retrieval-span overlap or an
  adjudicated entailment rubric? — Status: DEFERRED | Why it matters: exact-key
  agreement is deliberately narrower than the full disconfirmation benchmark.
