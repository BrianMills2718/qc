# Plan #171: D7 Baseline Span-Overlap Diagnostics

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** Plan #170: D7 span-overlap diagnostics
**Blocks:** richer D7 retrieval-mode comparison error analysis

---

## Outcome

Each scored D7 baseline row now includes diagnostic-only
`span_overlap` metadata. The diagnostic compares baseline contrary-evidence
anchors against D7 gold using the same same-`target_claim_id`/same-`doc_id`
character-span IoU and Modified Hausdorff logic as the system D7 overlap
section. Segment-only baseline anchors are counted as unscored for overlap
rather than converted into guessed spans.

`compare_d7_retrieval_predictions()` and `make compare-d7-retrieval` surface
the diagnostics through the existing `disconfirmation_d7.baselines.<name>`
payload because the report reuses Phase 0 D7 scoring. Exact D7 baseline
TP/FP/FN, recall, precision, F1, bootstrap intervals, and
system-minus-baseline deltas remain unchanged except for the additive
diagnostic section. This is local error-analysis metadata only; it is not
semantic disconfirmation validity, held-out evidence, expert parity,
superiority evidence, or SOTA evidence.

Implementation commit: `6c2c094` (`Add D7 baseline span-overlap diagnostics`).

Verification:

- Initial focused TDD run failed as expected because baseline rows did not yet
  expose `span_overlap`.
- `python -m pytest tests/test_bench_phase0.py tests/test_d7_retrieval.py -k "d7 or span_overlap or comparison" -q`
  -> 25 passed, 58 deselected.
- `python -m ruff check qc_clean/core/bench.py qc_clean/core/d7_retrieval.py tests/test_bench_phase0.py tests/test_d7_retrieval.py`
  -> passed.
- `make docs-check` -> passed.
- `git diff --check` -> passed.
- `make check` -> 1141 passed, 1 skipped, 8 deselected; Ruff and docs gates
  passed. Type check remains unconfigured by the repo.

---

## Gap

**Current:** `disconfirmation_d7.span_overlap` reports same-target/document
char-span IoU and Modified Hausdorff diagnostics for system negative-case
anchors against D7 gold. D7 baseline records, including retrieval/live-baseline
prediction packages used by `make compare-d7-retrieval`, still expose exact-key
TP/FP/FN/recall/precision/F1 and baseline deltas only. A retrieval baseline can
therefore near-miss the right contrary-evidence span, but the comparison report
only shows one false positive plus one false negative for that baseline.

**Target:** Add diagnostic-only `span_overlap` metadata to each
`disconfirmation_d7.baselines.<name>` row when D7 gold is scored. The diagnostic
will use the same same-`target_claim_id`/same-`doc_id` matching rule as the
system D7 span-overlap section, comparing baseline contrary-evidence anchors to
gold anchors. Exact D7 baseline scores and system-minus-baseline deltas remain
unchanged.

**Why:** D7 retrieval comparisons are where near-boundary retrieval errors are
most useful. Baseline-level overlap diagnostics make exported retrieval/live
candidate packages easier to critique without weakening the exact-anchor
scoring contract or implying held-out/semantic validity evidence.

---

## References Reviewed

- `qc_clean/core/bench.py:2767-2832` - D7 scorecard assembly and baseline
  attachment point.
- `qc_clean/core/bench.py:3133-3168` - D7 baseline exact scoring and delta
  intervals.
- `qc_clean/core/bench.py:3172-3295` - current D7 system span-overlap helpers.
- `qc_clean/core/d7_retrieval.py:196-236` - retrieval comparison reports reuse
  the Phase 0 D7 scorecard and surface `disconfirmation_d7.baselines`.
- `tests/test_bench_phase0.py:2605-2685` - D7 baseline exact-score regression
  tests.
- `tests/test_d7_retrieval.py:120-160` - retrieval comparison report baseline
  tests.
- `docs/EVALUATION_HARNESS.md` and `docs/PROJECT_THEORY_AND_GOALS.md` - D7
  status and claim discipline.
- Memory context:
  `agent-memory recall 'D7 baseline span overlap diagnostics qualitative_coding active decisions' --project qualitative_coding`
  returned low-relevance historical task outcomes and no active conflicting
  decision.
- Coordination claims:
  `find ~/.claude/coordination/claims -maxdepth 2 -type f` returned no active
  claim files.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a deterministic
repo-local scorecard/reporting extension over existing D7 baseline prediction
contracts.

---

## Capabilities

Internal scorecard/report capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| D7 baseline span-overlap diagnostic | D7 gold anchors + D7 baseline contrary-evidence anchors | `disconfirmation_d7.baselines.<name>.span_overlap` diagnostic metrics | qualitative_coding | `make bench`, `make compare-d7-retrieval`, benchmark artifacts | free |

### Capability Validation

- [x] Baseline overlap rows use the same same-target/document matching rule as
  the system D7 overlap diagnostic.
- [x] Exact baseline metrics and system-minus-baseline deltas are unchanged.
- [x] Segment-only baseline anchors are counted as unscored for overlap
  diagnostics rather than guessed.
- [x] Notes preserve that the section is local diagnostic metadata, not semantic
  disconfirmation validity, held-out evidence, expert parity, or superiority
  evidence.

---

## Files Affected

- `qc_clean/core/bench.py` (modify)
- `tests/test_bench_phase0.py` (modify)
- `tests/test_d7_retrieval.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify if status summary needs updating)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/ACTIVE_SPRINT.md` (modify)

---

## Plan

### Steps

1. Add focused failing tests for D7 baseline span-overlap diagnostics in the
   Phase 0 scorecard and retrieval comparison report.
2. Generalize the D7 overlap helper so it can score system-predicted spans and
   baseline-predicted `DisconfirmationGoldAnchor` spans without duplicating IoU
   logic.
3. Attach `span_overlap` to each D7 baseline score row after exact scoring.
4. Update docs conservatively to say D7 baseline/retrieval comparison rows now
   include local span-overlap diagnostics, while exact-key metrics remain the
   scored comparison contract.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_bench_phase0.py` | `test_scorecard_d7_baseline_span_overlap_scores_near_boundary_match` | A D7 baseline near-boundary span has overlap diagnostics while exact baseline TP/FP/FN remain unchanged. |
| `tests/test_d7_retrieval.py` | `test_comparison_report_includes_baseline_span_overlap` | `compare_d7_retrieval_predictions()` exposes baseline span-overlap diagnostics for retrieval prediction packages. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_bench_phase0.py tests/test_d7_retrieval.py -k "d7 or span_overlap or comparison" -q` | D7 baseline, D7 overlap, and retrieval comparison regressions. |
| `python -m ruff check qc_clean/core/bench.py tests/test_bench_phase0.py tests/test_d7_retrieval.py` | Style/syntax gate for touched code. |
| `make docs-check` | Plan/docs governance and AGENTS sync. |
| `git diff --check` | Whitespace gate. |
| `make check` | Full deterministic suite before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Every scored D7 baseline row includes `span_overlap`.
- [x] Baseline overlap diagnostics compare only same-target/document character
  spans.
- [x] Near-boundary baseline predictions report non-zero IoU/Modified Hausdorff
  diagnostics while exact baseline TP/FP/FN remain unchanged.
- [x] Retrieval comparison reports surface the baseline overlap diagnostics
  through the existing `disconfirmation_d7.baselines` payload.
- [x] Docs preserve the caveat that overlap diagnostics are local error
  analysis only, not semantic disconfirmation validity, held-out evidence,
  expert parity, superiority evidence, or SOTA evidence.

> Process criteria:
- [x] Required tests pass
- [x] Full test suite passes
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should future retrieval comparison reports summarize overlap deltas across
  baselines instead of only nesting per-baseline diagnostics? - Status:
  DEFERRED | Why it matters: this slice preserves existing report shape and
  adds local diagnostics without introducing a new statistical comparison
  contract.
