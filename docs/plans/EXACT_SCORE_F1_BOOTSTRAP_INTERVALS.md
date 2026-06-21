# Plan #39: Exact-Score F1 Bootstrap Intervals

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D3/D7 benchmark reporting; future interval-tested baseline deltas

---

## Gap

**Current:** D3/D7 exact-anchor scorecards report point-estimate F1 and Wilson
intervals for recall/precision. The docs still correctly say no F1/bootstrap
interval exists, and D7 baseline deltas remain point estimates.

**Target:** Add deterministic, configurable key-universe bootstrap intervals for
the exact-anchor F1 score emitted by D3/D7 scorecards and D7 baseline scores.
The interval metadata must include method, confidence, sample count, seed, and a
note that this is not a held-out superiority/non-inferiority test.

**Why:** F1 is the headline exact-match summary for D3/D7, but without an
interval it is easier to overread tiny gold sets. A deterministic local bootstrap
does not replace `prompt_eval` or held-out statistical testing, but it is a
useful artifact-level uncertainty signal for exact-anchor scorecards.

---

## References Reviewed

- `qc_clean/core/bench.py` - `_exact_anchor_score`, D3/D7 scorecard construction,
  and D7 baseline scoring.
- `tests/test_bench_phase0.py` - direct exact-score tests.
- `tests/test_bench_phase0_script.py` - external D3/D7 gold package tests.
- `docs/EVALUATION_HARNESS.md` - current D3/D7 metric caveats and missing
  F1/bootstrap interval note.
- Memory context: `agent-memory recall 'active decisions qualitative_coding exact score bootstrap F1 confidence intervals D7 baseline deltas evaluation harness' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This is a deterministic local bootstrap over the exact
gold/prediction key universe. Full held-out statistical testing and baseline
delta intervals remain a later `prompt_eval`-backed lane.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| exact F1 bootstrap interval | exact gold/prediction anchor keys + config | `f1_bootstrap_ci` JSON object | qualitative_coding | Phase 0 scorecard, artifact packages | free |

### Capability Validation

- [ ] D3 scored sections include deterministic `f1_bootstrap_ci`.
- [ ] D7 scored sections include deterministic `f1_bootstrap_ci`.
- [ ] D7 baseline scores include deterministic `f1_bootstrap_ci`.
- [ ] Bootstrap settings are configurable through `ProjectState.config.extra`
  rather than hardcoded only.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_bench_phase0_script.py` (modify if needed)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add an `ExactScoreBootstrapConfig` model and loader from
   `ProjectState.config.extra["phase0_exact_bootstrap"]`.
2. Add deterministic key-universe bootstrap helper(s) for F1.
3. Thread the config through D3, D7, and D7 baseline exact-anchor scoring.
4. Add tests for default output, configurable sample/seed/confidence metadata,
   disabled bootstrap behavior, and D7 baseline inclusion.
5. Update docs conservatively: F1 bootstrap intervals exist for exact-score
   sections, but baseline deltas are still point estimates and no held-out
   superiority/parity claim is licensed.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_scores_d3_application_gold_exact_span_and_code` | D3 exact score includes F1 bootstrap interval. |
| `tests/test_bench_phase0.py` | new configurable bootstrap test | `phase0_exact_bootstrap` controls confidence/samples/seed or disables output. |
| `tests/test_bench_phase0_script.py` | D7 baseline file test | Baseline exact score includes F1 bootstrap interval. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D3/D7 exact score behavior remains stable. |
| `tests/test_bench_phase0_script.py` | CLI scorecard loading remains stable. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] D3 scored sections report `f1_bootstrap_ci` by default.
- [ ] D7 scored sections and D7 baseline sections report `f1_bootstrap_ci` by
  default.
- [ ] Bootstrap settings are configurable from project metadata and can be
  disabled.
- [ ] Docs no longer say no F1/bootstrap interval exists, but still say no
  interval-tested baseline delta or held-out D3/D7 benchmark exists.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should bootstrap units be documents instead of exact keys? — Status:
  DEFERRED | Why it matters: document-level bootstrap needs enough held-out
  documents and document-aware gold packages. This slice uses exact keys because
  Phase 0 currently scores exact anchor keys and often runs on tiny fixtures.

---

## Notes

This plan adds local uncertainty metadata. It does not implement interval-tested
baseline deltas, superiority tests, non-inferiority tests, or prompt_eval-backed
held-out benchmark inference.
