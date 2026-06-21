# Plan #6: INV-7 Instruction/Data Separation

**Status:** Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** Raw transcript text is interpolated directly into LLM prompts under
plain headings such as `INTERVIEW CONTENT`, `INTERVIEW DATA`, `SEGMENTS`, and
`NEW DOCUMENTS TO CODE`. A malicious or accidental instruction inside a
transcript can therefore be presented to the model in the same textual channel
as developer-authored analysis instructions. There are no deterministic
prompt-injection regression tests.

**Target:** Every first-party prompt path that embeds raw transcript or segment
text wraps it in a shared untrusted-data boundary. The boundary line-prefixes
all user/corpus data and carries an explicit instruction that prefixed content
is source evidence only, never executable instructions. Representative prompt
construction tests use adversarial transcript fixtures and no live LLM calls.

**Why:** INV-7 is a validity invariant, not only a security concern. If
transcript text can alter the analysis instructions, the output may reflect an
injected command rather than participant meaning.

---

## References Reviewed

- `docs/PROJECT_THEORY_AND_GOALS.md:260` - INV-7 is currently UNMET because no instruction/data isolation or injection tests exist.
- `docs/PROJECT_THEORY_AND_GOALS.md:328` - roadmap identifies instruction/data separation as the next high-value safety lane.
- `qc_clean/core/pipeline/stages/thematic_coding.py:236-288` - exhaustive and example-quote thematic prompts embed raw segment/transcript text.
- `qc_clean/core/pipeline/stages/perspective.py:79-134` - perspective prompts embed raw transcript text.
- `qc_clean/core/pipeline/stages/relationship.py:91-119` - relationship prompt embeds raw transcript text.
- `qc_clean/core/pipeline/stages/synthesis.py:65-96` - synthesis prompt embeds raw transcript text.
- `qc_clean/core/pipeline/stages/negative_case.py:92-120` - negative-case prompt embeds raw transcript text while asking for disconfirmation.
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py:237-347` - GT constant-comparison prompt and override path embed raw segment text.
- `qc_clean/core/pipeline/stages/gt_axial_coding.py:54-80` - GT axial prompt embeds raw transcript text.
- `qc_clean/core/pipeline/stages/incremental_coding.py:173-235` - incremental thematic/GT recoding prompts embed newly added document text.
- Memory context: `agent-memory recall 'active decisions instruction data separation prompt injection qualitative coding INV-7' --project qualitative_coding` — no active blocking decision surfaced; only historical completed outcomes were returned.

---

## Research Basis For This Slice

No additional research beyond repo-local references was needed. This slice is a
repo-internal invariant hardening step with deterministic tests; external
prompt-injection/security research can inform a later threat-model pass.

---

## Capabilities

Skipped. This plan adds internal prompt-construction helpers and tests; it does
not create a cross-project callable capability, tool, or boundary.

---

## Files Affected

- `qc_clean/core/prompting.py` (create)
- `qc_clean/core/pipeline/stages/thematic_coding.py` (modify)
- `qc_clean/core/pipeline/stages/perspective.py` (modify)
- `qc_clean/core/pipeline/stages/relationship.py` (modify)
- `qc_clean/core/pipeline/stages/synthesis.py` (modify)
- `qc_clean/core/pipeline/stages/negative_case.py` (modify)
- `qc_clean/core/pipeline/stages/gt_constant_comparison.py` (modify)
- `qc_clean/core/pipeline/stages/gt_axial_coding.py` (modify)
- `qc_clean/core/pipeline/stages/incremental_coding.py` (modify)
- `tests/test_prompt_boundaries_inv7.py` (create)
- `docs/PROJECT_THEORY_AND_GOALS.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (regenerate)
- `docs/plans/CLAUDE.md` (modify)
- `docs/plans/INV7_INSTRUCTION_DATA_SEPARATION.md` (move to completed at finish)

---

## Plan

### Steps

1. Add a shared prompt-boundary helper in `qc_clean/core/prompting.py`.
2. Add deterministic helper tests proving every data line is prefixed, labels
   cannot escape the boundary, fake end markers stay prefixed, and the boundary
   includes explicit "do not follow data instructions" language.
3. Wire the helper into default/thematic prompts that embed raw transcripts or
   segments: thematic example-quote, thematic exhaustive, perspective,
   relationship, synthesis, and negative-case.
4. Wire the helper into GT raw-data prompts: constant comparison and axial
   coding.
5. Wire the helper into incremental recoding prompts for newly added documents.
6. Add representative prompt-capture regression tests for thematic,
   negative-case, GT constant-comparison, and incremental recoding, using
   adversarial transcript text and patched `LLMHandler.extract_structured`.
7. Update governance docs to describe the exact completed scope and residual
   limits. Do not claim prompt injection is fully solved unless every raw-data
   insertion path is covered and the tests prove the structural contract.
8. Run targeted tests, `make docs-check`, and `make check`; commit and push.

---

## Required Tests

### New Tests (TDD)

| Test File | Test Function | What It Verifies |
|-----------|---------------|------------------|
| `tests/test_prompt_boundaries_inv7.py` | `test_untrusted_data_block_prefixes_every_payload_line` | Every transcript line, including blank lines and fake delimiters, is line-prefixed as data. |
| `tests/test_prompt_boundaries_inv7.py` | `test_untrusted_document_blocks_include_doc_identity_without_unwrapped_content` | Document names are represented in boundary metadata and raw document content only appears on prefixed data lines. |
| `tests/test_prompt_boundaries_inv7.py` | `test_thematic_prompt_wraps_malicious_transcript_as_untrusted_data` | Thematic prompt-capture path keeps adversarial instructions inside prefixed data lines. |
| `tests/test_prompt_boundaries_inv7.py` | `test_negative_case_prompt_wraps_malicious_transcript_as_untrusted_data` | Negative-case prompt-capture path keeps adversarial instructions inside prefixed data lines. |
| `tests/test_prompt_boundaries_inv7.py` | `test_gt_constant_comparison_wraps_malicious_segment_as_untrusted_data` | GT constant-comparison prompt-capture path isolates raw segment text. |
| `tests/test_prompt_boundaries_inv7.py` | `test_incremental_recode_wraps_new_documents_as_untrusted_data` | Incremental recoding prompt-capture path isolates newly added document text. |

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `pytest tests/test_prompt_boundaries_inv7.py` | New INV-7 contract. |
| `pytest tests/test_pipeline_stages.py tests/test_constant_comparison.py tests/test_incremental.py tests/test_negative_case_inv6.py tests/test_exhaustive_coding.py` | Affected prompt-building and stage execution paths. |
| `make docs-check` | Plan/governance consistency and generated AGENTS sync. |
| `make check` | Full deterministic test, lint, and docs gate. |

---

## Acceptance Criteria

> Feature-level criteria:
- [ ] A single shared helper defines the untrusted-data prompt boundary.
- [ ] Every raw transcript/document/segment line sent through covered first-party prompts is prefixed as data.
- [ ] The helper carries explicit instruction text that prefixed data may be quoted, summarized, and analyzed, but not followed as instructions.
- [ ] Thematic, perspective, relationship, synthesis, negative-case, GT constant-comparison, GT axial, and incremental recoding prompts use the helper for raw transcript or segment text.
- [ ] Prompt overrides that receive `{combined_text}`, `{segment_text}`, or `{new_doc_text}` receive the already-boundaried form, not raw transcript text.
- [ ] Deterministic prompt-injection regression tests run without live LLM calls.
- [ ] Docs describe the landed scope and residual risks conservatively.

> Process criteria:
- [ ] Required targeted tests pass.
- [ ] Full deterministic suite passes through `make check`.
- [ ] Lint passes through `make check`.
- [ ] Docs checks pass.
- [ ] Verified work is committed and pushed.

---

## Open Questions

- [ ] Should every LLM-derived upstream output (`phase1_json`, memos, codebook
  example quotes) also be wrapped as untrusted data before downstream prompts?
  — Status: OPEN | Why it matters: upstream outputs can echo transcript
  instructions. This plan prioritizes raw corpus text first; derived-output
  isolation may be a follow-up if it increases prompt size/noise or needs a
  more nuanced schema-aware boundary.
- [ ] Should prompt overrides be allowed to opt out of the shared boundary?
  — Status: RESOLVED | Answer: no for first-party placeholders in this slice;
  placeholders should receive boundaried text by default. Fully custom prompts
  can still misuse the boundary by design, so docs should not overclaim.

---

## Notes

This plan improves structural prompt hygiene; it is not a formal security proof
and does not replace future evaluation against live prompt-injection fixtures.
The conservative expected status is INV-7 PARTIAL unless implementation and
tests cover all first-party raw-data prompt paths.
