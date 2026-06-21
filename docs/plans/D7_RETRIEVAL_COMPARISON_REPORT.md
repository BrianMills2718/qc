# Plan #35: D7 Retrieval Comparison Report

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Held-out D7 retrieval-mode comparison; prompt_eval-backed statistical comparison

---

## Gap

**Current:** `make run-d7-retrieval` exports one retrieval-mode prediction
package, and `make bench GOLD=... BASELINES=...` can score a baseline file.
Comparing multiple retrieval-mode exports still requires manual JSON merging or
manual bench invocations.

**Target:** Add a deterministic comparison report wrapper that loads a project,
one D7 gold file, and one or more exported retrieval prediction packages, then
emits the exact D7 baseline comparison using the existing Phase 0 scorer.

**Why:** The embedding-hybrid path should be evaluated by a repeatable report,
not by ad hoc manual merging. This remains a substrate: it does not create a
held-out result or statistical superiority claim by itself.

---

## References Reviewed

- `qc_clean/core/d7_retrieval.py` - retrieval prediction package shape.
- `scripts/run_d7_retrieval.py` - single-mode prediction export.
- `qc_clean/core/bench.py` - D7 exact scoring and duplicate-baseline fail-loud
  behavior.
- `scripts/bench_phase0.py` - gold/baseline file loading helpers.
- `tests/test_d7_retrieval.py` - current export-package tests.
- `docs/EVALUATION_HARNESS.md` - D7 harness status and caveats.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D7 retrieval comparison report wrapper held-out benchmark' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is deterministic harness
plumbing over existing D7 scoring.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `compare_d7_retrieval_predictions(state, gold, packages)` | `ProjectState` + D7 gold payload + retrieval prediction packages | D7 comparison report dict | qualitative_coding | `scripts/compare_d7_retrieval.py`, agents | free |

### Capability Validation

- [ ] Uses existing D7 gold and baseline Pydantic contracts.
- [ ] Duplicate baseline names fail loudly through the existing scorer.
- [ ] Does not mutate saved project state.

---

## Files Affected

- `qc_clean/core/d7_retrieval.py` (modify)
- `scripts/compare_d7_retrieval.py` (create)
- `Makefile` (modify)
- `tests/test_d7_retrieval.py` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add `compare_d7_retrieval_predictions()` to merge baseline records from one
   or more retrieval prediction packages into a deep-copied state, apply D7 gold
   in memory, call `phase0_scorecard()`, and return a compact report.
2. Add `scripts/compare_d7_retrieval.py` with `project_id`, `--gold-file`,
   repeated `--predictions-file`, and `--output`.
3. Add `make compare-d7-retrieval ID=<project> GOLD=<gold.json> PREDICTIONS="a.json b.json" OUTPUT=report.json`.
4. Add tests for scored comparisons, duplicate-baseline failure, and no mutation
   of the input state.
5. Update docs conservatively: comparison reports are exact-span point estimates
   until a held-out D7 run and interval-tested deltas exist.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_retrieval.py` | `test_compares_retrieval_prediction_packages_against_gold` | Multiple exported retrieval baselines are scored against the same gold in one report. |
| `tests/test_d7_retrieval.py` | `test_comparison_fails_loud_on_duplicate_baseline_names` | Duplicate baseline names are rejected instead of overwritten. |
| `tests/test_d7_retrieval.py` | `test_comparison_does_not_mutate_project_state` | Gold/baseline metadata is applied to a copy only. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_d7_retrieval.py` | Existing export package behavior remains compatible. |
| `tests/test_bench_phase0.py` | D7 scorecard remains the source of truth for scoring. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Agents can run one command to score multiple exported retrieval prediction
  packages against one D7 gold file.
- [ ] Report includes exact D7 baseline scores from the existing scorer, plus
  project ID, package count, and claim-discipline note.
- [ ] Duplicate baseline names fail loudly.
- [ ] State is deep-copied before applying gold/baseline metadata.
- [ ] Docs continue to say this is not a held-out D7 result or superiority claim.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status reported
- [ ] Docs updated
- [ ] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should this report compute interval-tested baseline deltas? — Status:
  DEFERRED | Why it matters: exact point estimates are already available, but
  statistical comparison belongs in the prompt_eval-backed harness.

---

## Notes

This plan intentionally scores already exported predictions. It does not run
retrieval or embeddings itself, keeping generation separate from comparison.
