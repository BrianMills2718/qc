# Plan #49: Human Agreement Metadata Scorecard

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** D3/D7 human-ceiling agreement transparency

---

## Outcome

D3/D7 `human_ceiling_comparison` sections now include
`chance_corrected_agreement` when versioned gold-package
`adjudication.human_human_agreement` metadata supplies numeric Cohen's κ,
Fleiss κ, Krippendorff's α, or Gwet's AC1 values. Exact system-vs-human
comparison remains limited to recall/precision/F1; packages with only
chance-corrected human metrics return `metadata_only`, not a scored exact parity
comparison. Non-numeric chance metrics remain explicit under
`non_numeric_metrics`. Docs preserve that no populated κ/α/AC1 human-ceiling
benchmark or system agreement-vs-gold evidence exists yet.

**Verification:**
- `python -m pytest tests/test_bench_phase0.py -q` - 35 passed.
- `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py` - passed.
- `python scripts/check_markdown_links.py` - passed.
- `make check` - 737 passed, 1 skipped, 8 deselected; Ruff and docs checks passed; type check not yet configured.

## Gap

**Current:** Versioned D3/D7 gold-set packages accept
`adjudication.human_human_agreement`, but `human_ceiling_comparison` only scores
exact recall/precision/F1. Chance-corrected human-human metrics such as
`cohens_kappa`, `krippendorff_alpha`, and `gwet_ac1` are currently treated as
non-comparable leftovers instead of being explicitly surfaced.

**Target:** Add a `chance_corrected_agreement` subsection to D3/D7
`human_ceiling_comparison` when versioned package metadata supplies numeric
human-human κ/α/AC1-style metrics. Keep exact system-vs-human comparison limited
to recall/precision/F1 and label chance-corrected values as human metadata only.

**Why:** This makes the scorecard more honest and complete: it records the
human-ceiling agreement metadata the harness asks for without pretending the
system has κ/α/AC1 agreement-vs-gold or expert parity.

---

## References Reviewed

- `docs/EVALUATION_HARNESS.md` - D3 requirement for κ/α/AC1 reporting and
  human-ceiling caveats.
- `docs/PROJECT_THEORY_AND_GOALS.md` - no κ/α/AC1 human-ceiling agreement has
  been populated/run.
- `qc_clean/core/bench.py` - `_human_ceiling_comparison`, D3/D7 provenance
  helpers, and exact-score comparison output.
- `qc_clean/core/d3_gold.py`, `qc_clean/core/d7_gold.py` - versioned gold-set
  package adjudication metadata contracts.
- `tests/test_bench_phase0.py` - current exact human-ceiling comparison tests.
- Memory context: `agent-memory recall 'qualitative_coding human_human_agreement kappa alpha AC1 human ceiling scorecard' --project qualitative_coding` failed because the embedding provider returned OpenRouter 402/403 errors; no local coordination claims were present.

---

## Research Basis For This Slice

No additional external research beyond repo-local references. This slice only
surfaces already-supplied package metadata and does not define or compute new
agreement statistics.

---

## Capabilities

Internal scorecard capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| Human agreement metadata scorecard | Versioned gold package `human_human_agreement` | Reported chance-corrected agreement metadata | qualitative_coding | `make bench`, benchmark artifacts | free |

### Capability Validation

- [x] Numeric κ/α/AC1-style metrics are surfaced under `chance_corrected_agreement`.
- [x] Exact system-vs-human comparison remains limited to recall/precision/F1.
- [x] A package with only chance-corrected metrics reports `metadata_only`, not exact-score parity.
- [x] Non-numeric or unknown human metrics remain explicit and do not silently disappear.

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

1. Add canonical chance-corrected human agreement metric keys and aliases in
   `qc_clean/core/bench.py`.
2. Extend `_human_ceiling_comparison` to include
   `chance_corrected_agreement` when numeric κ/α/AC1-style metrics are present.
3. Return `metadata_only` when a versioned package supplies chance-corrected
   metrics but no comparable exact recall/precision/F1 metrics.
4. Update D3/D7 tests for exact+chance metadata and metadata-only packages.
5. Update docs so the current status is "metadata surfaced when supplied," not
   "populated human agreement evidence exists."

---

## Required Tests

### New Tests

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | D3 exact+chance metadata test | Exact metrics still compare, κ/AC1 metadata is reported separately. |
| `tests/test_bench_phase0.py` | D3 metadata-only test | Chance metrics without recall/precision/F1 produce `metadata_only`. |
| `tests/test_bench_phase0.py` | D7 chance metadata test | D7 packages surface chance-corrected human agreement metadata. |

### Existing Tests

| Test Pattern | Why |
|--------------|-----|
| `tests/test_bench_phase0.py` | Human-ceiling scorecard behavior. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] D3/D7 human-ceiling sections surface numeric Cohen's κ, Krippendorff's α,
  Fleiss κ, and Gwet's AC1 metadata when supplied.
- [x] Exact comparison status remains `scored` only when recall/precision/F1 are
  comparable to system exact scores.
- [x] Metadata-only packages do not claim system parity or validity.
- [x] Docs preserve the caveat that no populated κ/α/AC1 human-ceiling benchmark
  has been run.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future system κ/α/AC1 agreement-vs-gold be computed locally or via
  `prompt_eval`? — Status: DEFERRED | Why it matters: public benchmark
  agreement statistics should likely live in the frozen experiment layer.
