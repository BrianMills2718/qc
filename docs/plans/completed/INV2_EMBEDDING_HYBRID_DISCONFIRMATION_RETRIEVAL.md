# Plan #33: INV-2 Embedding-Hybrid Disconfirmation Retrieval

**Outcome:** Complete. `retrieve_disconfirmation_candidates()` now keeps the
default lexical BM25/query-expansion path while supporting opt-in
`embedding_hybrid` retrieval with embedding cosine similarity, explicit model
configuration, provider-output validation, task/trace/budget pass-through, and
fail-loud invalid modes. `NegativeCaseStage` passes retrieval-mode config from
`PipelineContext`, and candidate prompts/memos expose retrieval mode and semantic
scores without claiming D7 validation.

Verification: `python -m pytest tests/test_disconfirmation_retrieval_inv2.py tests/test_bench_phase0.py -q`
passed with 39 tests; `make check` passed with 703 tests, 1 skipped, 8
deselected, Ruff clean, docs checks clean, and type checking still not
configured.

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 semantic/adversarial retrieval hardening; held-out D7 retrieval evaluation

---

## Gap

**Current:** Disconfirmation retrieval is retrieval-first, source-anchored, and
ranked with BM25-style lexical scoring, contradiction-cue boosts, and
deterministic query expansion. It can find some non-exact contrary terms, but it
is still not embedding/semantic retrieval.

**Target:** Add an opt-in embedding-hybrid retrieval mode that combines the
existing lexical score with cosine similarity from embedding vectors while
preserving exact source anchors, default lexical behavior, and fail-loud
configuration.

**Why:** INV-2 remains partial because lexical/query-expanded retrieval can miss
contrary passages that do not share the claim vocabulary. This slice creates the
first real embedding retrieval surface without claiming validation, a default
provider policy, or D7 performance.

---

## References Reviewed

- `qc_clean/core/disconfirmation.py` - current BM25/query-expansion retriever and
  candidate model.
- `qc_clean/core/pipeline/pipeline_engine.py` - `PipelineContext` retrieval
  knobs and LLM observability fields.
- `qc_clean/core/pipeline/stages/negative_case.py` - negative-case stage calls
  retrieval and formats the prompt/memo summary.
- `tests/test_disconfirmation_retrieval_inv2.py` - current INV-2 retrieval,
  anchoring, prompt-boundary, and config pass-through tests.
- `docs/PROJECT_THEORY_AND_GOALS.md` - INV-2/INV-6 claim discipline and current
  retrieval caveats.
- `docs/EVALUATION_HARNESS.md` - D7 scoring substrate and remaining held-out
  benchmark gaps.
- `/home/brian/projects/llm_client/llm_client/core/client.py` - local
  `llm_client.embed()` API exposes embedding vectors with task/trace logging.
- `/home/brian/projects/llm_client/llm_client/execution/call_contracts.py` -
  `check_budget(trace_id, max_budget)` pre-flight budget check available for
  embedding adapter use.
- Memory context: `agent-memory recall 'active decisions qualitative_coding semantic retrieval disconfirmation embeddings D7 INV-2' --project qualitative_coding` — historical completed outcomes only, no blocking in-flight decision.

---

## Research Basis For This Slice

No additional research beyond References Reviewed. This is a repo-local
implementation slice, not a model-selection or retrieval-quality study.

---

## Capabilities

Internal-only change. This plan modifies an existing project-local retrieval
helper but does not create a cross-project callable boundary or registry entry.

---

## Files Affected

- `qc_clean/core/disconfirmation.py` (modify)
- `qc_clean/core/pipeline/pipeline_engine.py` (modify)
- `qc_clean/core/pipeline/stages/negative_case.py` (modify)
- `tests/test_disconfirmation_retrieval_inv2.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `docs/EVALUATION_HARNESS.md` (modify)
- `docs/plans/CLAUDE.md` (modify)

---

## Plan

### Steps

1. Add retrieval-mode configuration to `PipelineContext`:
   `disconfirmation_retrieval_mode`, `disconfirmation_embedding_model`,
   `disconfirmation_embedding_dimensions`,
   `disconfirmation_semantic_weight`, and
   `disconfirmation_min_semantic_similarity`.
2. Extend `DisconfirmationCandidate` with `retrieval_mode` and optional
   `semantic_score` fields.
3. Refactor `retrieve_disconfirmation_candidates()` so lexical mode preserves
   current behavior and `embedding_hybrid` mode embeds claim queries and segment
   texts once, computes cosine similarity, and ranks by
   `lexical_score + semantic_weight * semantic_score`.
4. Add a default llm_client embedding provider that performs a pre-flight
   `check_budget(trace_id, max_budget)`, calls `llm_client.embed()` with
   task/trace tags, and raises on missing dependency or invalid vector output.
5. Pass retrieval-mode and embedding config from `NegativeCaseStage`; include
   retrieval mode and embedding model in the memo summary.
6. Add tests for embedding-only candidate retrieval, fail-loud invalid
   configuration, default lexical preservation, and pipeline config pass-through.
7. Update docs conservatively: embedding-hybrid is opt-in and unvalidated; it
   does not satisfy D7, human adjudication, or methodological validity.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_embedding_hybrid_retrieves_semantic_candidate_without_lexical_overlap` | Injected embedding vectors can surface a source-anchored candidate with no matched or expanded lexical terms. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_embedding_hybrid_requires_embedding_model` | Opting into embedding retrieval without a model fails loudly. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_unknown_disconfirmation_retrieval_mode_fails_loud` | Unknown retrieval mode raises instead of falling back to lexical search. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_passes_embedding_retrieval_config` | Pipeline context embedding retrieval fields reach the retriever with task/trace/budget tags. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_disconfirmation_retrieval_inv2.py` | Protect existing INV-2 lexical retrieval, anchors, prompt boundaries, and model routing. |
| `tests/test_bench_phase0.py` | Ensure D7 scorecard behavior is unchanged by retrieval-mode additions. |
| `make check` | Full deterministic gate for tests, Ruff, and docs. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [x] Existing default disconfirmation retrieval remains lexical BM25/query
  expansion and existing tests continue to pass.
- [x] `embedding_hybrid` mode can retrieve and anchor a candidate with no lexical
  overlap when embedding similarity is high.
- [x] Embedding mode requires an explicit embedding model and fails loudly on
  unknown mode, invalid weights, missing vectors, or zero-length vectors.
- [x] Negative-case execution passes retrieval mode, embedding model, dimensions,
  semantic weight, similarity threshold, task, trace ID, and max budget to the
  retriever.
- [x] Docs preserve claim discipline: this is opt-in, unvalidated embedding
  retrieval, not D7 evidence or methodological credibility.

> Process criteria (quality gates):
- [x] Required tests pass
- [x] Full test suite passes
- [x] Type check status reported
- [x] Docs updated
- [x] Plan completed, committed, and pushed

---

## Open Questions

- [ ] Which embedding model should be the validated default? — Status: DEFERRED |
  Why it matters: model/provider choice should be benchmark-driven against D7
  gold and cost/latency constraints, not hardcoded in this slice.
- [ ] Should embedding calls move into a shared retrieval/indexing library? —
  Status: DEFERRED | Why it matters: this first slice is project-local, but
  reusable retrieval infrastructure may belong in shared infrastructure if
  multiple projects need it.

---

## Notes

This plan deliberately avoids claiming semantic retrieval is validated. The
mode is opt-in and should be evaluated against held-out D7 before it is used as
credibility evidence.
