# Plan #34: D7 Retrieval-Mode Export

**Outcome:** Complete. Added `qc_clean/core/d7_retrieval.py`,
`scripts/run_d7_retrieval.py`, and `make run-d7-retrieval` to export configured
disconfirmation retrieval candidates as D7 baseline-compatible prediction
packages. The exporter deep-copies state before retrieval, preserves exact
target-claim/source anchors, supports lexical and opt-in embedding-hybrid
retrieval, and composes with the existing `make bench GOLD=... BASELINES=...`
scorecard path without mutating saved project state.

Verification: `python -m pytest tests/test_d7_retrieval.py tests/test_disconfirmation_retrieval_inv2.py tests/test_bench_phase0.py -q`
passed with 43 tests; `make check` passed with 707 tests, 1 skipped, 8
deselected, Ruff clean, docs checks clean, and type checking still not
configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Held-out D7 retrieval-mode comparison; validated embedding retrieval policy

---

## Gap

**Current:** `make bench` can score D7 gold and externally supplied baseline
predictions, and disconfirmation retrieval now supports default
`lexical_bm25` plus opt-in `embedding_hybrid`. There is no agent-drivable way
to export retrieval candidates from a configured mode into the baseline schema
that the D7 scorecard already understands.

**Target:** Add a deterministic exporter that runs a configured retrieval mode
over the current claim ledger and writes a D7 baseline-compatible JSON package
without mutating `ProjectState`.

**Why:** Embedding-hybrid retrieval should not be treated as progress until it
can be compared against gold. This slice makes retrieval-mode comparison
operational with existing Phase 0 scoring: export predictions, then run
`make bench ID=<project> GOLD=<gold.json> BASELINES=<predictions.json>`.

---

## References Reviewed

- `qc_clean/core/disconfirmation.py` - retrieval modes and candidate anchor
  model.
- `qc_clean/core/claims.py` - `disconfirmation_targets()` target selection for
  the final claim ledger.
- `qc_clean/core/bench.py` - D7 exact-anchor scoring and baseline prediction
  schema.
- `qc_clean/core/d7_gold.py` - D7 anchor/package contracts.
- `scripts/bench_phase0.py` - external D7 gold/baseline file loading and Phase 0
  artifact conventions.
- `Makefile` - standard project interface target style.
- `tests/test_disconfirmation_retrieval_inv2.py` and
  `tests/test_bench_phase0.py` - current retrieval and D7 baseline tests.
- Memory context: `agent-memory recall 'active decisions qualitative_coding D7 retrieval-mode comparison embedding hybrid disconfirmation benchmark' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is an evaluation-harness
plumbing slice over existing repository contracts.

---

## Capabilities

Internal project capability only; no cross-project boundary is created.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `export_d7_retrieval_baseline(state, config)` | `ProjectState` + retrieval config kwargs | D7 baseline-compatible JSON dict | qualitative_coding | `scripts/run_d7_retrieval.py`, `make bench BASELINES=...` | free for lexical; embedding cost when `embedding_hybrid` |

### Capability Validation

- [x] Input/output schemas use existing Pydantic `ProjectState` and
  `DisconfirmationGoldAnchor` contracts.
- [x] Exported package can be consumed by existing `load_d7_baselines_file()`.
- [x] No mutation of saved project state.

---

## Files Affected

- `qc_clean/core/d7_retrieval.py` (create)
- `scripts/run_d7_retrieval.py` (create)
- `Makefile` (modify)
- `tests/test_d7_retrieval.py` (create)
- `tests/test_bench_phase0_script.py` or `tests/test_bench_phase0.py` (modify if needed)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add a core exporter that:
   - selects `disconfirmation_targets(state, limit=max_targets)`;
   - calls `retrieve_disconfirmation_candidates()` with explicit retrieval
     config;
   - converts candidates to D7 `contrary_evidence` anchors;
   - returns a JSON-serializable object with `disconfirmation_baselines` plus
     retrieval run metadata.
2. Add a CLI script `scripts/run_d7_retrieval.py` with flags for project ID,
   output path, name/description, target/candidate limits, retrieval mode,
   BM25/query-expansion weights, embedding model/dimensions, semantic weight,
   and minimum semantic similarity.
3. Add `make run-d7-retrieval ID=<project> OUTPUT=<file> [MODE=...]` wrapper.
4. Add tests for lexical export, embedding-hybrid export with an injected
   provider, no-state-mutation behavior, and baseline-loader compatibility.
5. Update docs conservatively: this exports retrieval predictions for scoring;
   it does not run held-out D7, choose a default embedding model, or establish
   superiority.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_d7_retrieval.py` | `test_exports_lexical_retrieval_candidates_as_d7_baseline_package` | Lexical retrieval candidates become baseline-compatible D7 anchors with target claim IDs and exact spans. |
| `tests/test_d7_retrieval.py` | `test_embedding_hybrid_export_can_use_injected_embedding_provider` | Embedding-hybrid export can surface a semantically similar no-lexical-overlap candidate without live embedding calls. |
| `tests/test_d7_retrieval.py` | `test_export_does_not_mutate_project_state` | Exporting predictions works on the in-memory state without writing gold/baseline metadata into `ProjectState.config.extra`. |
| `tests/test_d7_retrieval.py` | `test_export_package_is_accepted_by_phase0_baseline_loader` | Output package shape is compatible with existing `load_d7_baselines_file()` semantics. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_disconfirmation_retrieval_inv2.py` | Retrieval semantics and fail-loud embedding mode remain intact. |
| `tests/test_bench_phase0.py` | Existing D7 gold/baseline scoring remains unchanged. |
| `make check` | Full deterministic gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] Agents can run one command to export D7 retrieval predictions for a
  project and retrieval mode.
- [x] Exported JSON includes a `disconfirmation_baselines` list accepted by the
  current Phase 0 baseline loader.
- [x] Exported anchors preserve `target_claim_id`, `doc_id`, `start_char`,
  `end_char`, `segment_id`, and `quote_text` where available.
- [x] Lexical export makes no embedding calls; embedding-hybrid export remains
  opt-in and fail-loud through the existing retriever.
- [x] Docs make clear this is a comparison substrate, not held-out D7 evidence.

> Process criteria (quality gates):
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Should retrieval-mode comparisons be embedded directly into `make bench`?
  — Status: DEFERRED | Why it matters: this slice composes with the existing
  `BASELINES=` path; direct bench integration can come after the export shape is
  stable.
- [ ] Which embedding model should be used in public D7 comparisons? — Status:
  DEFERRED | Why it matters: model choice should be benchmark-driven and costed,
  not selected by this plumbing slice.

---

## Notes

The output is deliberately baseline-compatible rather than a new scorecard
schema. This reuses the existing D7 scorer and keeps retrieval generation
separate from scoring.
