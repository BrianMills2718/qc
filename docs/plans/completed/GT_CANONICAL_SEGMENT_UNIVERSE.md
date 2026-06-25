# Plan #225: GT Canonical Segment Universe

## Outcome

Completed 2026-06-25. Grounded-theory constant comparison now traverses the
canonical char-anchored INV-8 `Segment` universe. `segment_documents()` remains
as a compatibility helper, but it delegates to `segment_corpus()` and carries
`segment_id`, `start_char`, and `end_char` through the GT prompt/merge dict
shape. `GTConstantComparisonStage` populates `ProjectState.segments` when
missing and preserves existing canonical segments when present. This unifies the
software evidence denominator for GT traversal, coverage, review/export, and
future abductive evidence bundles; it is not GT saturation, methodological
validity, abductive-synthesis evidence, or SOTA evidence.

Verification:

- `python -m pytest tests/test_constant_comparison.py -q` — 26 passed.
- `python -m pytest tests/test_anchoring_integration.py tests/test_claim_ledger_pipeline.py -q` — 11 passed.
- `python -m pytest tests/test_prompt_boundaries_inv7.py -k gt_constant_comparison -q` — 1 passed, 25 deselected.
- `python -m pytest tests/test_constant_comparison.py tests/test_anchoring_integration.py tests/test_claim_ledger_pipeline.py tests/test_prompt_boundaries_inv7.py -k 'constant_comparison or gt_constant_comparison' -q` — 29 passed, 34 deselected.
- `python -m ruff check qc_clean/core/pipeline/stages/gt_constant_comparison.py qc_clean/core/segmentation.py tests/test_constant_comparison.py` — passed.
- `make docs-check` — passed.
- `git diff --check` — passed.
- `make check` — 1323 passed, 1 skipped, 8 deselected; Ruff/docs passed; type check not configured.

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** Future GT artifact model, observed-pattern layer, abductive synthesis stage, QC-to-workbench evidence bundle

---

## Gap

**Current:** `gt_constant_comparison.py` performs grounded-theory constant
comparison over its own dict-based segmentation path. That path shares the
speaker-turn regex with `qc_clean/core/segmentation.py`, but it strips text,
tracks no `Segment.id`, and carries no char offsets. The canonical INV-8 segment
universe exists in `qc_clean/core/segmentation.py` and `ProjectState.segments`,
but GT does not consume it directly.

**Target:** GT constant comparison uses the canonical char-anchored segment
universe as its traversal substrate. Each GT segment payload retains doc ID,
doc name, speaker, segment index, `segment_id`, `start_char`, and `end_char`.
When the incoming state lacks `segments`, GT populates them with
`segment_corpus()` before traversal. Existing prompt shape and merge behavior
remain compatible.

**Why:** GT, category diagnostics, future abductive pattern finding, and future
workbench exports need one stable evidence denominator. If GT keeps a separate
segmentation path, later claims/patterns cannot reliably step down to the same
source units used by coverage, anchoring, review, and mixed-methods handoff.

---

## References Reviewed

- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` - current GT segmenting, prompt construction, merge logic.
- `qc_clean/core/segmentation.py` - canonical char-anchored `Segment` universe and coverage denominator.
- `qc_clean/schemas/domain.py` - `Segment`, `CodeApplication`, `AnalyticClaim`, and `ProjectState` fields.
- `tests/test_constant_comparison.py` - existing segmentation and GT stage tests.
- `tests/test_anchoring_integration.py` - GT application anchoring expectations.
- `tests/test_claim_ledger_pipeline.py` - GT claim emission expectations.
- `CLAUDE.md` - current GT segmentation refactor candidate and future workbench alignment.
- Memory context: not needed; current repo docs and code are sufficient for this narrow slice.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This is an
internal contract-unification slice, not a methodological novelty slice.

---

## Capabilities

Skipped: this plan modifies internal GT traversal behavior and does not create a
new cross-project callable capability.

---

## Files Affected

- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `tests/test_constant_comparison.py` (modify/add focused tests)
- `tests/test_anchoring_integration.py` or `tests/test_claim_ledger_pipeline.py` (add focused assertion if needed)
- `CLAUDE.md` (update refactor-candidate status if implementation lands)
- `AGENTS.md` (regenerate if `CLAUDE.md` changes)
- `docs/plans/ACTIVE_SPRINT.md` (update checkpoint)
- `docs/plans/CLAUDE.md` (register active/completed plan)

---

## Plan

### Steps

1. Add a small internal conversion from canonical `Segment` objects to the
   segment dict shape currently used by GT prompts/merge logic.
2. Make `segment_documents()` delegate to `segment_corpus()` and preserve its
   public helper name for compatibility with existing tests/imports.
3. Make `GTConstantComparisonStage.execute()` populate `state.segments` when
   missing, then traverse `state.segments` through the compatibility conversion.
4. Include `segment_id`, `start_char`, and `end_char` in the prompt data block
   for traceability without changing required LLM schema fields.
5. Preserve `_merge_segment_results()` behavior for code creation,
   modifications, applications, and best-effort quote anchoring.
6. Add/update tests proving GT uses/preserves canonical segments and prompt
   payloads include offset metadata.
7. Update docs and close the plan after verification.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_constant_comparison.py` | `test_segment_documents_delegates_to_canonical_segments_with_offsets` | GT helper returns segment dicts with canonical text, offsets, and segment IDs. |
| `tests/test_constant_comparison.py` | `test_stage_populates_missing_canonical_segments` | GT stage fills `ProjectState.segments` when absent before traversal. |
| `tests/test_constant_comparison.py` | `test_stage_preserves_existing_canonical_segments` | GT stage uses existing `state.segments` instead of rebuilding a divergent universe. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `pytest tests/test_constant_comparison.py` | Core GT segmentation/stage behavior. |
| `pytest tests/test_anchoring_integration.py tests/test_claim_ledger_pipeline.py` | Anchors and claims still work after segment substrate change. |
| `pytest tests/test_prompt_boundaries_inv7.py -k gt_constant_comparison` | Prompt-boundary protections for GT remain intact. |
| `make docs-check` | Plan registration and generated `AGENTS.md` sync. |
| `git diff --check` | Whitespace hygiene. |
| `make check` | Full deterministic suite and docs/lint gates before closeout. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] GT constant comparison uses canonical `Segment` objects as its traversal substrate.
- [ ] If `ProjectState.segments` is empty, GT populates it using `segment_corpus()`.
- [ ] If `ProjectState.segments` is already populated, GT preserves and uses that existing universe.
- [ ] GT segment prompt data includes segment ID and char offsets for traceability.
- [ ] Existing GT code/application/claim behavior is preserved.
- [ ] This is documented as unifying the software evidence denominator only; it is not claimed as GT saturation, methodological validity, abductive synthesis, or SOTA evidence.

> Process criteria:
- [ ] Required focused tests pass.
- [ ] `make docs-check` passes.
- [ ] `git diff --check` passes.
- [ ] `make check` passes.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should canonical non-speaker paragraph segments later support 500-word
  chunking for very long paragraphs? Status: DEFERRED. This slice preserves the
  canonical segmenter as source of truth; chunk-size policy belongs in
  `segment_corpus()` if needed later.
- [ ] Should `CodeApplication` gain a `segment_id` field? Status: DEFERRED.
  Current `ClaimAnchor` supports `segment_id`, but `CodeApplication` does not.
  Adding it is a schema migration and belongs in a later evidence-bundle slice.

---

## Notes

This plan intentionally keeps the compatibility dict shape inside
`gt_constant_comparison.py` so the first slice is not a broad rewrite. The
important contract change is that those dicts are derived from canonical
`Segment` records rather than a second segmentation implementation.
