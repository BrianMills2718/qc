# Plan #17: INV-2 Query-Expansion Disconfirmation Retrieval

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 semantic/embedding retrieval; held-out D7 retrieval evaluation

---

## Gap

**Current:** Disconfirmation retrieval is BM25-style lexical retrieval over claim
terms plus contradiction cues. It still misses candidate passages that express a
contrary concept without repeating the claim vocabulary. Example: a claim says
"automation improves service," while a source segment says "the rollout created
delays and slower handoffs." The contrary segment can be invisible if it shares
no target term with the claim.

**Target:** Add a deterministic query-expansion layer to
`retrieve_disconfirmation_candidates()`. Claim terms can expand to configured
contrary/exception terms, and expanded-term matches contribute a configurable
fraction of the BM25 score. Preserve exact source anchors, candidate IDs, prompt
formatting, and D7 scorecard compatibility.

**Why:** This is a bounded retrieval-recall improvement that can be measured by
the existing D7 scorecard once gold exists. It is **not** semantic/embedding
retrieval and does not make disconfirmation credible by itself.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:256` - INV-2 remains partial because retrieval is lexical, bounded, and not D7-validated.
- `docs/PROJECT_THEORY_AND_GOALS.md:328` - roadmap still calls for semantic/embedding/adversarial retrieval and held-out D7 evaluation.
- `docs/plans/completed/INV2_BM25_DISCONFIRMATION_RETRIEVAL.md` - deferred query expansion vs. embeddings as the next retrieval upgrade.
- `qc_clean/core/disconfirmation.py` - current BM25-style retrieval helper and candidate model.
- `qc_clean/core/pipeline/pipeline_engine.py` - `PipelineContext` retrieval knobs.
- `qc_clean/core/pipeline/stages/negative_case.py` - passes retrieval config and formats candidate prompt section.
- `tests/test_disconfirmation_retrieval_inv2.py` - retrieval-first regression suite.

---

## Research Basis For This Slice

This slice is repo-local and deterministic. It intentionally avoids adding an
embedding dependency or model-provider path before there is a held-out D7
benchmark to justify and compare that complexity. The implementation should be
designed so a later embedding retriever can replace or complement the expansion
layer.

---

## Capabilities

This plan modifies internal retrieval configuration only; it does not create a
cross-project callable capability.

---

## Files Affected

- `qc_clean/core/disconfirmation.py` (modify)
- `qc_clean/core/pipeline/pipeline_engine.py` (modify)
- `qc_clean/core/pipeline/stages/negative_case.py` (modify)
- `tests/test_disconfirmation_retrieval_inv2.py` (modify)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV2_QUERY_EXPANSION_DISCONFIRMATION_RETRIEVAL.md` (create, then move to completed)

---

## Plan

### Steps

1. Add default deterministic contrary-term expansions in
   `qc_clean/core/disconfirmation.py`.
2. Add retriever parameters for `query_expansions` and
   `expanded_term_weight`.
3. Score exact claim-term BM25 matches at full weight and expanded-term BM25
   matches at the configured weight.
4. Add `expanded_terms` to `DisconfirmationCandidate` with a default empty
   list and include it in prompt formatting for observability.
5. Add `PipelineContext` fields for `disconfirmation_query_expansions` and
   `disconfirmation_expanded_term_weight`; pass them from `NegativeCaseStage`.
6. Update docs conservatively: query expansion improves deterministic lexical
   recall but still is not semantic/embedding retrieval or D7 validation.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_query_expansion_retrieves_contrary_segment_without_exact_claim_terms` | Expanded contrary terms can retrieve an anchored candidate even when original claim terms do not occur in the segment. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_query_expansion_can_be_disabled_with_zero_weight` | Expansion has an explicit config-off path. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_passes_query_expansion_config` | `PipelineContext` expansion knobs reach the retriever. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_disconfirmation_retrieval_inv2.py` | Protect retrieval-first prompt/candidate/anchor contract. |
| `tests/test_bench_phase0.py` | D7 scorecard still consumes negative-case anchors. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Expanded contrary terms can retrieve source candidates without exact claim-term overlap.
- [ ] `expanded_terms` are recorded and shown in candidate prompt metadata.
- [ ] Existing exact candidate anchors, candidate IDs, quote hashes, and D7 scoring keys remain compatible.
- [ ] Query expansion can be configured or disabled.
- [ ] Docs state this is deterministic lexical query expansion, not semantic/embedding retrieval or validation.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should query expansions be learned from gold failures? — Status: DEFERRED | Why it matters: once D7 gold exists, expansion terms should be justified by measured recall/precision deltas rather than static intuition.
- [ ] Should the next slice introduce embedding retrieval? — Status: DEFERRED | Why it matters: embeddings are likely needed for true semantic recall, but they add provider/model/cost/provenance decisions that should be benchmark-driven.

---

## Notes

Do not describe this as semantic retrieval. It remains lexical, deterministic,
and bounded; the purpose is to expose more candidate passages for adversarial
interpretation while preserving exact source anchors.
