# Plan #54: D3 System-Gold Agreement Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D3 richer agreement-vs-gold metadata

---

## Outcome

Implemented `application_validity_d3.system_gold_agreement`, a deterministic
exact-key binary agreement diagnostic over the union of D3 gold and predicted
code/source-anchor keys. It reports row count, percent agreement, Cohen's κ,
Gwet's AC1, and prevalence metadata, with notes that prevent interpreting this
as semantic equivalence, Krippendorff's α, full D3 validity, or expert parity.
The human-ceiling chance-corrected metadata note now says that section does not
compare system chance-corrected agreement to the human ceiling.

## Verification

- `python -m pytest tests/test_bench_phase0.py -q` - 47 passed.
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `python scripts/sync_plan_status.py --check` - passed.
- `make check` - 757 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

---

## Gap

**Current:** The D3 application-validity scorecard reports exact code/source
TP/FP/FN, precision, recall, F1, Wilson intervals, F1 bootstrap intervals, span
overlap diagnostics, and human-ceiling metadata. The evaluation harness still
flags system κ/AC1 agreement-vs-gold as future work, and the human-ceiling
metadata note currently says the system scorecard does not compute system
kappa/alpha/AC1.

**Target:** Add a deterministic `system_gold_agreement` section to
`application_validity_d3` when D3 gold is available. It will treat the union of
exact D3 gold keys and exact predicted keys as binary rows, with two raters:
`gold` and `system`. It will report row count, percent agreement, Cohen's κ,
Gwet's AC1, prevalence, and a note that this is exact-key binary agreement
metadata, not full D3 validity or expert parity.

**Why:** This advances the documented D3 agreement-vs-gold gap using the
already-scored exact-key universe, without pretending to compute full
Krippendorff's α, semantic equivalence, multi-label unit agreement, or
methodological validity.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 requires agreement-vs-gold and AC1
  reporting, but warns exact/span scorer is not full D3.
- `docs/PROJECT_THEORY_AND_GOALS.md` - no methodological validity or expert
  parity claims without populated held-out evidence.
- `qc_clean/core/bench.py` - D3 exact key scoring, prevalence tables, and
  human-ceiling comparison metadata.
- `qc_clean/core/pipeline/irr.py` - binary percent agreement, Cohen's κ, and
  Gwet's AC1 helpers.
- `tests/test_bench_phase0.py` - D3 scorecard and human-ceiling coverage.
- Memory context: unavailable. The last three `agent-memory recall` attempts in
  this session failed with the same OpenRouter 402/403 embedding-provider
  errors, so the circuit breaker applies; no local coordination claims were
  present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
adds deterministic binary agreement metadata over exact code/source-anchor keys.
Full D3 agreement with semantic near matches, unit-aware multi-label handling,
and Krippendorff's α remains prompt_eval-backed benchmark work.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D3 exact-key system-gold agreement | D3 gold + exact predicted application keys | Binary agreement metrics/prevalence | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Agreement rows are built from the exact union of gold and predicted D3 keys.
- [x] Metrics include percent agreement, Cohen's κ, and Gwet's AC1.
- [x] Prevalence is reported for interpreting sparse exact-key labels.
- [x] Notes prevent expert-parity/full-validity interpretation.

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

1. Add a helper that builds a binary `gold/system` matrix over the union of D3
   gold and predicted exact keys.
2. Add `system_gold_agreement` to `application_validity_d3_scorecard`.
3. Include prevalence metadata using the existing binary prevalence helper.
4. Add focused tests for mixed TP/FP/FN rows and perfect-match rows.
5. Update docs to say D3 exact-key system-vs-gold κ/AC1 metadata exists while
   full D3 validity, α, semantic equivalence, and expert parity remain future.

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D3 mixed agreement test | Union rows, percent agreement, κ/AC1, and prevalence reflect TP/FP/FN exact keys. |
| `tests/test_bench_phase0.py` | D3 perfect agreement test | Perfect exact D3 match reports agreement metrics at 1.0. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | D3 exact scorecard, span overlap, and human-ceiling behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] `application_validity_d3.system_gold_agreement` exists when D3 gold is
  scored.
- [x] Mixed TP/FP/FN exact-key rows produce deterministic agreement metrics and
  prevalence metadata.
- [x] Perfect exact matches produce 1.0 agreement metrics.
- [x] Docs preserve the caveat that this is exact-key binary agreement metadata,
  not full D3 validity, Krippendorff's α, semantic equivalence, or expert parity.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] When should full D3 Krippendorff's α be implemented? — Status: DEFERRED |
  Why it matters: α needs a pre-registered unit model and missing-boundary
  policy, likely in the prompt_eval-backed suite.
