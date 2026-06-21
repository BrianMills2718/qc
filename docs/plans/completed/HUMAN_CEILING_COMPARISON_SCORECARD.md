# Plan #44: Human-Ceiling Comparison Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D3/D7 expert-parity reporting; SOTA-gate audit trail

---

## Outcome

Implemented first-class `human_ceiling_comparison` sections for scored D3 and
D7 Phase 0 scorecards. When a versioned gold-set package includes numeric
human-human `recall`, `precision`, or `f1`, the scorecard reports system value,
human value, system-minus-human delta, and whether the system meets or exceeds
that metric. Missing or non-comparable human metrics produce explicit
`not_available` states. Documentation preserves the caveat that this is a
comparison substrate, not expert-parity evidence without populated held-out
human-adjudicated gold.

**Verification:** `python -m pytest tests/test_bench_phase0.py
tests/test_d3_gold_set.py tests/test_d7_gold_set.py -q` (39 passed); `python -m
ruff check qc_clean/core/bench.py tests/test_bench_phase0.py`; `make check` (729
passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet
configured).

---

## Gap

**Current:** Versioned D3/D7 gold-set packages can carry adjudication metadata
with optional `human_human_agreement`, and Phase 0 scorecards surface that
metadata inside `gold_provenance`. The scorecard does not provide a first-class
system-vs-human-ceiling comparison, so downstream benchmark artifacts cannot
programmatically distinguish "human ceiling absent" from "human ceiling present
and system below/equal/above it."

**Target:** Add conservative `human_ceiling_comparison` sections to D3 and D7
scorecards. When a versioned gold-set package supplies numeric
`human_human_agreement` metrics that overlap with system exact-score metrics
(`recall`, `precision`, `f1`), report system value, human value, delta, and
whether the system meets or exceeds that metric. When no comparable metrics are
available, report `not_available` with a clear reason.

**Why:** The evaluation harness says expert parity requires comparison against
the measured human-human ceiling on the same corpus. This slice does not create
expert data, but it makes the scorecard ready to consume and audit that data
once supplied.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3/D7 human-ceiling and expert-parity criteria.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline for SOTA/expert parity.
- `qc_clean/core/d3_gold.py` - D3 package `human_human_agreement` metadata.
- `qc_clean/core/d7_gold.py` - D7 package `human_human_agreement` metadata.
- `qc_clean/core/bench.py` - D3/D7 exact-score scorecard construction.
- `tests/test_bench_phase0.py` - current D3/D7 scorecard coverage.
- Memory context: `agent-memory recall 'active decisions qualitative_coding next roadmap D3 agreement kappa alpha AC1 bias prompt injection live benchmark confidence calibration' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No new external research. This implements the already documented harness
requirement that human-ceiling comparison must be explicit before expert-parity
claims.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D3/D7 human-ceiling comparison | Versioned gold package with `adjudication.human_human_agreement` | `human_ceiling_comparison` scorecard section | qualitative_coding | benchmark artifacts, claim-discipline review | free |

### Capability Validation

- [x] D3 scorecard reports comparable recall/precision/F1 deltas when a package
  supplies numeric human metrics.
- [x] D7 scorecard reports comparable recall/precision/F1 deltas when a package
  supplies numeric human metrics.
- [x] Scorecards report `not_available` when human metrics are absent or have no
  comparable exact-score keys.
- [x] Docs state this is a comparison substrate, not expert-parity evidence
  unless populated from held-out adjudicated gold.

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

1. Add a helper that extracts `human_human_agreement` from D3/D7 versioned
   package provenance and compares numeric `recall`, `precision`, and `f1`
   against the system scorecard.
2. Attach `human_ceiling_comparison` to D3 and D7 scorecards after exact-score
   metrics are computed.
3. Add deterministic tests for available, absent, and non-comparable human
   metrics.
4. Update harness/theory docs conservatively.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D3 human-ceiling comparison test | Versioned D3 package with human F1/precision/recall produces metric deltas. |
| `tests/test_bench_phase0.py` | D7 human-ceiling comparison test | Versioned D7 package with human F1/precision/recall produces metric deltas. |
| `tests/test_bench_phase0.py` | unavailable comparison test | Missing/non-comparable human metrics report `not_available`, not a false pass/fail. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Main scorecard contract. |
| `tests/test_d3_gold_set.py` / `tests/test_d7_gold_set.py` | Package validation remains compatible. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D3 and D7 scorecards include `human_ceiling_comparison`.
- [x] Comparable metrics include `system_value`, `human_value`,
  `system_minus_human`, and `meets_or_exceeds_human`.
- [x] Non-comparable or missing human metrics are explicit `not_available`
  states.
- [x] No SOTA, expert-parity, or methodological-validity claim is introduced.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [x] Should κ/α/AC1 become first-class computed metrics in this repo? — Status:
  DEFERRED | Why it matters: those require agreement-unit modeling beyond this
  exact-anchor scorer and should be a separate D5/D3 agreement plan.
