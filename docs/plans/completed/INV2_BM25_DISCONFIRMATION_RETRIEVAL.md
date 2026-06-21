# Plan #11: INV-2 BM25 Disconfirmation Retrieval

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 hardened disconfirmation; held-out D7 retrieval evaluation

---

## Outcome

Completed 2026-06-21. `retrieve_disconfirmation_candidates()` now ranks source
segments with BM25-style term weighting plus configurable contradiction-cue
boosts. `PipelineContext` exposes `disconfirmation_bm25_k1`,
`disconfirmation_bm25_b`, and `disconfirmation_contrary_cue_weight`, and
`NegativeCaseStage` passes those values into retrieval. Candidate IDs, exact
anchors, quote hashes, prompt formatting, and D7 scorecard consumption remain
compatible.

This is a retrieval-quality slice only. It does not provide semantic/embedding
retrieval, human adjudication, validated reviewer model policy, or held-out D7
evidence. INV-2/INV-6 remain PARTIAL.

Verification: `python -m pytest tests/test_disconfirmation_retrieval_inv2.py tests/test_bench_phase0.py -q`
passed (`19 passed`) and Ruff passed on touched files before the implementation
commit. Final plan completion was verified with `make check`.

---

## Gap

**Current:** Retrieval-first disconfirmation ranks candidate passages by raw
claim-term overlap plus contradiction-cue count. This is deterministic and
anchored, but it treats common terms too strongly and cannot distinguish a
segment that repeats generic claim vocabulary from one containing a rarer,
more diagnostic claim term.

**Target:** Replace raw overlap scoring with a deterministic BM25-style lexical
retrieval score over the segment universe, while preserving contradiction-cue
boosting, exact anchors, existing candidate IDs, and prompt formatting. Make the
BM25 and cue-weight parameters configurable through `PipelineContext` and direct
retriever kwargs.

**Why:** INV-2 remains partial partly because retrieval quality is weak. BM25 is
not semantic search and does not prove disconfirmation quality, but it is a
standard, transparent first retrieval upgrade that can later be evaluated by the
D7 scorecard.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:255` - INV-2 remains partial because retrieval is lexical overlap, not semantic/BM25/embedding search.
- `docs/PROJECT_THEORY_AND_GOALS.md:327` - roadmap lists semantic/adversarial retrieval and D7 gold-set evaluation as remaining disconfirmation work.
- `docs/EVALUATION_HARNESS.md:57` - D7 score is recall/precision against human contrary evidence.
- `qc_clean/core/disconfirmation.py` - current retrieval-first candidate scorer.
- `qc_clean/core/pipeline/pipeline_engine.py` - `PipelineContext` owns disconfirmation limits/config.
- `tests/test_disconfirmation_retrieval_inv2.py` - current INV-2 retrieval contract tests.
- `requirements.txt` - no existing BM25/search dependency; keep this slice dependency-free.
- Memory context: `agent-memory recall 'active decisions BM25 semantic retrieval disconfirmation qualitative_coding INV-2' --project qualitative_coding` — no active blocking decision surfaced.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. BM25 is a
well-established lexical ranking formula; this slice uses it as a transparent
deterministic upgrade, not as a SOTA retrieval claim.

---

## Capabilities

This plan modifies an internal retrieval helper only; it does not create a
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
- `docs/plans/INV2_BM25_DISCONFIRMATION_RETRIEVAL.md` (create, then move to completed)

---

## Plan

### Steps

1. Add BM25-style corpus statistics over `state.segments` inside
   `qc_clean/core/disconfirmation.py`.
2. Replace raw `len(matched) + cue_weight * cues` scoring with
   `bm25_score + cue_weight * cues`, preserving deterministic sort order.
3. Add `PipelineContext` fields for BM25 `k1`, `b`, and contradiction cue weight.
4. Pass those knobs from `NegativeCaseStage` into
   `retrieve_disconfirmation_candidates`.
5. Add tests proving rare diagnostic claim terms outrank repeated generic terms,
   existing cue ranking remains, and pipeline config is propagated.
6. Update docs conservatively: retrieval is BM25-style lexical, not semantic;
   no held-out D7 benchmark has run.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_bm25_ranks_rare_specific_terms_above_repeated_generic_terms` | A rare diagnostic claim term outranks repeated generic overlap. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_passes_bm25_retrieval_config` | `PipelineContext` BM25/cue knobs reach the retriever. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `tests/test_disconfirmation_retrieval_inv2.py` | Protect retrieval-first prompt/candidate/anchor contract. |
| `tests/test_bench_phase0.py` | D7 scorecard still consumes negative-case anchors. |
| `make check` | Full deterministic repo gate. |

---

## Acceptance Criteria

> Feature-level criteria (what the plan accomplishes):
- [ ] Retrieval score uses BM25-style term weighting plus configurable contrary-cue boost.
- [ ] Existing candidate IDs, source anchors, quote hashes, matched terms, and prompt formatting remain compatible.
- [ ] Pipeline context exposes configurable `disconfirmation_bm25_k1`, `disconfirmation_bm25_b`, and `disconfirmation_contrary_cue_weight`.
- [ ] Tests prove BM25 ranking changes the known raw-overlap failure mode.
- [ ] Docs state BM25-style lexical retrieval is still not semantic retrieval or D7 validation.

> Process criteria (quality gates):
- [ ] Required tests pass
- [ ] Full test suite passes
- [ ] Type check status is reported
- [ ] Docs updated

---

## Open Questions

- [ ] Should the next retrieval upgrade use embeddings or query expansion? — Status: DEFERRED | Why it matters: BM25 improves lexical ranking but does not find semantic contradictions without shared vocabulary.
- [ ] Should BM25 parameters live in persisted project config? — Status: DEFERRED | Why it matters: `PipelineContext` is enough for execution-time tuning; persisted eval provenance can be added with the full prompt_eval suite.

---

## Notes

This plan intentionally avoids adding a dependency for a small deterministic
formula. If retrieval grows beyond BM25, move the abstraction toward a dedicated
retrieval module or shared infra rather than expanding this helper indefinitely.
