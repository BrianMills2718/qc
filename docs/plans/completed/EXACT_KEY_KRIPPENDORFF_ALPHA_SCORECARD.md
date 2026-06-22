# Plan #58: Exact-Key Krippendorff Alpha Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Stronger D3/D7 exact-key agreement metadata

---

## Outcome

D3 and D7 exact-key `system_gold_agreement` sections now include
`krippendorff_alpha` beside percent agreement, Cohen's κ, Gwet's AC1, and
prevalence metadata. The implementation adds a tested nominal categorical
Krippendorff's α helper plus a binary wrapper for the existing exact-key
gold/system presence matrices. Docs preserve the caveat that this is exact-key
binary metadata, not full semantic/multi-label D3 α or boundary-aware
reliability evidence.

## Verification

- Focused tests: `python -m pytest tests/test_irr_application_level.py tests/test_bench_phase0.py -q`
  (`63 passed`)
- Focused lint: `python -m ruff check qc_clean/core/pipeline/irr.py qc_clean/core/bench.py tests/test_irr_application_level.py tests/test_bench_phase0.py`
  (`All checks passed!`)
- Docs/link/plan checks:
  - `python scripts/check_markdown_links.py`
  - `python scripts/sync_plan_status.py --check`
- Full gate: `make check` (`769 passed, 1 skipped, 8 deselected`; ruff and
  docs-check passed)
- Type check: not configured by the repo (`make check` reports this explicitly)

## Gap

**Current:** D3 and D7 `system_gold_agreement` sections report exact-key percent
agreement, Cohen's κ, Gwet's AC1, and prevalence. The evaluation docs still
call out Krippendorff's α as a target agreement statistic, but the scorecard has
no system-gold α metadata.

**Target:** Add a deterministic nominal/binary Krippendorff's α helper for
complete exact-key two-rater matrices and surface it in D3 and D7
`system_gold_agreement` as `krippendorff_alpha`. This is exact-key binary
metadata only: gold/system presence over the exact anchor key universe. It does
not implement full D3 semantic/multi-label Krippendorff's α, missing-data
handling, or boundary-disagreement-aware α.

**Why:** α is part of the documented D3 evidence target and is already accepted
as human-human package metadata. Reporting exact-key α beside κ and AC1 makes
the current local agreement substrate more complete while preserving claim
discipline.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - α target and current D3/D7 scorecard caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - claim discipline and honest-state ledger.
- `qc_clean/core/pipeline/irr.py` - current agreement helpers for percent
  agreement, Cohen's κ, and Gwet's AC1.
- `qc_clean/core/bench.py` - exact-key D3/D7 `system_gold_agreement` builder.
- `tests/test_irr_application_level.py` and `tests/test_bench_phase0.py` -
  existing agreement metric tests.
- Memory context: unavailable. Prior `agent-memory recall` attempts in this
  session repeatedly failed with provider errors; circuit breaker applies. No
  active local coordination claims were present.

---

## Research Basis For This Slice

This is a local implementation of nominal Krippendorff's α over complete binary
exact-key matrices. It intentionally avoids broader α variants until the full
D3 semantic/multi-label agreement design is specified.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Exact-key binary Krippendorff's α | `{unit_key: [gold_presence, system_presence]}` | numeric α in system-gold agreement | qualitative_coding | agents, benchmark artifacts | free |

### Capability Validation

- [x] Perfect exact-key agreement returns α = 1.0.
- [x] Mixed exact-key disagreement returns deterministic nominal α.
- [x] D3 `system_gold_agreement` includes `krippendorff_alpha`.
- [x] D7 `system_gold_agreement` includes `krippendorff_alpha`.
- [x] Docs state this is exact-key metadata, not full semantic/multi-label α.

---

## Files Affected

- `qc_clean/core/pipeline/irr.py` (modify)
- `qc_clean/core/bench.py` (modify)
- `tests/test_irr_application_level.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add `compute_krippendorff_alpha_nominal` for complete categorical matrices
   and a binary wrapper if useful for existing exact-key matrices.
2. Add focused metric tests for perfect agreement and the existing mixed
   D3/D7 exact-key matrix.
3. Surface `krippendorff_alpha` in `_exact_key_system_gold_agreement`.
4. Update D3/D7 scorecard tests to assert the new field.
5. Update docs with the caveat that this is exact-key binary α only.

---

## Required Tests

### New/Changed Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_irr_application_level.py` | exact-key alpha perfect | Nominal α returns 1.0 for complete agreement. |
| `tests/test_irr_application_level.py` | exact-key alpha mixed | Nominal α returns the expected deterministic value on a mixed binary matrix. |
| `tests/test_bench_phase0.py` | D3 system-gold agreement | D3 scorecard includes exact-key `krippendorff_alpha`. |
| `tests/test_bench_phase0.py` | D7 system-gold agreement | D7 scorecard includes exact-key `krippendorff_alpha`. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| Existing IRR agreement tests | Existing κ/AC1 behavior must not regress. |
| Existing D3/D7 scorecard tests | Agreement sections must keep their current shape plus the new field. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] A tested Krippendorff's α helper exists for complete nominal matrices.
- [x] D3 and D7 exact-key `system_gold_agreement` include `krippendorff_alpha`.
- [x] Existing κ/AC1/prevalence fields remain unchanged.
- [x] Docs preserve the caveat that full semantic/multi-label α remains future
  benchmark work.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should full D3 semantic/multi-label α use an external reliability package
  or prompt_eval evaluator? - Status: DEFERRED | Why it matters: that design
  needs missing-label and boundary-disagreement semantics; this slice only
  reports exact-key binary metadata.
