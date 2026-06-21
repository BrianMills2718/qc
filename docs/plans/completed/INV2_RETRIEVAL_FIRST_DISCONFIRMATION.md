# Plan #7: INV-2 Retrieval-First Disconfirmation

**Status:** Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** INV-2 full disconfirmation hardening; INV-6 stronger final-claim coverage; D7 evaluation-harness disconfirmation metrics

---

## Completion Outcome

Completed 2026-06-21. Negative-case analysis is now retrieval-first over
bounded claim-ledger targets: `qc_clean/core/disconfirmation.py`
deterministically retrieves char-anchored segment candidates, formats them as
untrusted prompt data with `candidate_id`/`claim_id`/span metadata, and
`NegativeCaseStage` asks the LLM to assess those retrieved candidates rather
than dumping the full corpus into the prompt. `NegativeCase` can return a
`candidate_id`; valid IDs attach exact `ClaimAnchor`s directly, and invalid IDs
fail loud. The negative-case memo records how many candidate passages were
retrieved for how many claim targets.

This is an INV-2 first slice, not full hardened disconfirmation. Retrieval is
lexical and deterministic, not semantic/BM25/embedding-based; interpretation is
still same-model unless callers choose another model; no human adjudication or
D7 recall/precision benchmark has run. Absence of retrieved negative cases is
not evidence none exist.

Verification: targeted affected suites passed (`41 passed`), and `make check`
passed with `628 passed, 1 skipped, 8 deselected`; Ruff and docs checks were
green.

---

## Gap

**Current:** `NegativeCaseStage` receives the codebook, cross-interview memo,
bounded claim-ledger targets, and the full transcript text, then asks the same
LLM call to "actively search" and interpret. That is ledger-routed, but still
memory-first and same-prompt-lineage: the model can overlook contrary evidence
or launder confirmation. Contrary anchors are recovered only after the model
returns evidence text, so paraphrases can remain unanchored.

**Target:** Negative-case analysis must retrieve source passages first, before
interpretation. The stage should enumerate claim targets, deterministically
retrieve bounded candidate passages from the char-anchored segment universe,
present only those candidates for disconfirmation interpretation, and let the
LLM cite exact `candidate_id` values. When a returned negative case cites a
valid candidate, the resulting claim receives the known source anchor directly.

**Why:** INV-2 is the difference between "the same model thought about whether
its own analysis has exceptions" and "the system first surfaced candidate
contrary evidence from the corpus, then interpreted it." Retrieval-first
candidate IDs also make contrary anchors more reliable than post-hoc quote
resolution alone.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:255` - INV-2 is UNMET; current disconfirmation is same-model, memory-first, and experimental.
- `docs/PROJECT_THEORY_AND_GOALS.md:259` - INV-6 remains partial because disconfirmation is bounded and not retrieval-first/adversarial.
- `docs/EVALUATION_HARNESS.md:42` - D7 target is disconfirmation recall/precision vs human-identified contrary evidence.
- `docs/plans/completed/INV6_LEDGER_DISCONFIRMATION.md` - prior slice added claim-ledger target routing and deferred retrieval-first design to INV-2.
- `qc_clean/core/pipeline/stages/negative_case.py` - current negative-case prompt/schema and full-corpus prompt path.
- `qc_clean/core/claims.py:355-388` - negative-case claim builder and contrary-anchor resolution.
- `qc_clean/core/claims.py:438-520` - disconfirmation target enumeration and prompt formatting.
- `qc_clean/core/segmentation.py` - char-anchored segment universe for candidate retrieval.
- `qc_clean/schemas/domain.py:260-319` - `ClaimAnchor`, `ClaimScope`, and `AnalyticClaim` fields available for candidate anchors.
- `tests/test_negative_case_inv6.py`, `tests/test_claims.py`, `tests/test_claim_ledger_pipeline.py` - current regression coverage for negative-case routing and claim anchors.
- Coordination context: `~/.claude/coordination/claims/` contained no active claims.
- Memory context: `agent-memory recall 'active decisions retrieval-first disconfirmation negative case INV-2 qualitative_coding' --project qualitative_coding` — no active blocking decision surfaced; only historical completed outcomes were returned.

---

## Research Basis For This Slice

No additional external research is required for this deterministic first slice.
It implements the repo's already-defined invariant using the existing
char-anchored segment universe and claim ledger. Later work should add a
semantic retriever, a different/adversarial model configuration, and D7
gold-set evaluation through `prompt_eval`.

---

## Capabilities

These are internal project capabilities, not cross-project APIs.

| Capability | Input Schema | Output Schema | Producer | Consumer(s) | Cost Tier |
|-----------|-------------|---------------|----------|-------------|-----------|
| `retrieve_disconfirmation_candidates(state, targets, config)` | `ProjectState`, `list[AnalyticClaim]`, retrieval parameters | `list[DisconfirmationCandidate]` | `qc_clean/core/disconfirmation.py` | `NegativeCaseStage`, tests | free |
| `format_disconfirmation_candidates(candidates)` | `list[DisconfirmationCandidate]` | `str` | `qc_clean/core/disconfirmation.py` | `NegativeCaseStage` | free |
| `claims_for_negative_cases(..., candidate_anchors=...)` | `ProjectState`, negative-case objects, optional `candidate_id -> ClaimAnchor` map | `list[AnalyticClaim]` | `qc_clean/core/claims.py` | `NegativeCaseStage`, tests | free |

### Capability Validation

- [ ] Internal Pydantic candidate model has `Field(description=...)` on public fields.
- [ ] Candidate IDs are deterministic within a prompt and map to exact source anchors.
- [ ] Invalid returned `candidate_id` fails loud.
- [ ] Existing claim-ledger/disconfirmation surfaces continue to pass.

---

## Files Affected

- `qc_clean/core/disconfirmation.py` (create)
- `qc_clean/core/pipeline/pipeline_engine.py` (modify retrieval limits/config)
- `qc_clean/core/pipeline/stages/negative_case.py` (modify)
- `qc_clean/core/claims.py` (modify)
- `tests/test_disconfirmation_retrieval_inv2.py` (create)
- `tests/test_negative_case_inv6.py` (modify as needed)
- `tests/test_claims.py` (modify as needed)
- `tests/test_claim_ledger_pipeline.py` (modify as needed)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify at completion)
- `CLAUDE.md` (modify at completion)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV2_RETRIEVAL_FIRST_DISCONFIRMATION.md` (move to completed at finish)

---

## Plan

### Steps

1. Add `DisconfirmationCandidate` and deterministic retrieval helpers:
   tokenize claim/code text, score char-anchored segments by claim-term overlap
   plus contradiction-cue bonus, and return bounded candidates per claim.
2. Add candidate formatting that includes `candidate_id`, `claim_id`, `doc_id`,
   `segment_id`, offsets, score, and matched terms while wrapping candidate text
   in the INV-7 untrusted-data block.
3. Add `PipelineContext` knobs for retrieval limits (`disconfirmation_max_targets`,
   `disconfirmation_candidates_per_claim`) so hardcoded prompt-size limits are
   configurable.
4. Extend `NegativeCase` with optional `candidate_id`. Wire
   `NegativeCaseStage` to ensure a segment universe exists, retrieve candidate
   passages before the LLM call, pass only the retrieved candidate section
   instead of the full corpus, and instruct the model to copy exact
   `candidate_id`/`claim_id` values.
5. Extend `claims_for_negative_cases` with an optional candidate-anchor map.
   If a negative case cites a valid candidate, attach that anchor directly; if
   it cites an invalid candidate, fail loud; if it cites none, preserve the
   existing quote-resolution fallback.
6. Persist a compact retrieval-first summary in the negative-case memo so
   exported/read surfaces can see how many candidate passages were examined.
7. Update docs conservatively: INV-2 becomes PARTIAL at most unless/until
   semantic/adversarial retrieval and D7 evaluation land.
8. Run targeted tests, `make docs-check`, and `make check`; commit and push.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_retrieves_claim_relevant_segments_with_source_anchors` | Candidate retrieval uses segment offsets and returns exact anchors. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_retrieval_scores_contrary_cues_above_plain_mentions` | Contradiction-cue segments rank ahead of plain topical mentions when overlap is comparable. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_candidate_format_includes_ids_and_untrusted_data_boundaries` | Formatted candidates include exact IDs/offsets and INV-7 data boundaries. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_prompt_uses_retrieved_candidates_not_full_corpus` | Prompt contains candidate passages and excludes irrelevant non-candidate transcript text. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_negative_case_candidate_id_creates_exact_contrary_anchor` | Returned `candidate_id` attaches the known source span without quote re-resolution. |
| `tests/test_disconfirmation_retrieval_inv2.py` | `test_invalid_negative_case_candidate_id_fails_loud` | Invalid returned candidate IDs raise instead of silently falling back. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python -m pytest tests/test_disconfirmation_retrieval_inv2.py` | New INV-2 retrieval-first contract. |
| `python -m pytest tests/test_negative_case_inv6.py tests/test_claims.py tests/test_claim_ledger_pipeline.py tests/test_prompt_boundaries_inv7.py` | Affected negative-case, claim, and prompt-boundary behavior. |
| `make docs-check` | Plan/governance consistency and generated docs sync. |
| `make check` | Full deterministic test, lint, and docs gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [x] Negative-case analysis retrieves candidate passages before LLM interpretation.
- [x] Retrieved candidates are source-anchored to doc/segment offsets.
- [x] Negative-case prompts use retrieved candidate passages instead of dumping the full corpus.
- [x] The LLM schema can return exact `candidate_id` values.
- [x] Valid `candidate_id` values attach contrary anchors directly to negative-case claims.
- [x] Invalid `candidate_id` values fail loud.
- [x] Retrieval limits are configurable through `PipelineContext`.
- [x] Docs state the landed scope without claiming full INV-2, methodological validity, or D7 success.

> Process criteria:
- [x] Required targeted tests pass.
- [x] Full deterministic suite passes through `make check`.
- [x] Lint passes through `make check`.
- [x] Docs checks pass.
- [x] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should this slice use semantic embeddings or BM25 rather than lexical
  overlap? — Status: DEFERRED | Why it matters: semantic recall is important
  for full INV-2, but this first slice needs deterministic anchored retrieval
  with no new service dependency.
- [ ] Should disconfirmation use a different model immediately? — Status:
  DEFERRED | Why it matters: different-model/adversarial interpretation is
  required for full hardening, but retrieval-first evidence flow can land
  independently and reduces prompt-memory laundering first.
- [ ] Should every target claim be forced to have at least one candidate? —
  Status: OPEN | Why it matters: absence of lexical candidates is not evidence
  there is no contrary evidence. This slice should report zero-candidate targets
  honestly rather than fabricating evidence.

---

## Notes

This plan is the first retrieval-first implementation. It should improve INV-2
from UNMET to PARTIAL if implemented, but it does not by itself prove
disconfirmation quality. D7 recall/precision against a human gold set remains
future evaluation work.
